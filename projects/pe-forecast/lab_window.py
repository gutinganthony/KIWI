#!/usr/bin/env python3
"""近期樣本外測試：模型在 S&P 500 以外（Nasdaq-100、S&P 400、S&P 600、Russell 2000）還準不準？

    python3 lab_window.py --lg <loosygoosie data/companies> --oz <代號對上 CIK 的表> --ozm <月底股價表> \
                          --stooq <S&P 500 Stooq 目錄> --idx <indexkit 成分股 parquet 目錄>

期間：2025-12 → 2026-09（全美股月股價只有這段）。站在 2025-12～2026-06 的每個月底，只用當時已公告的財報（季報季末 +45 天、
年報 +75 天才算公告），預測 3／6／9 個月後的本益比，和 2026-03～2026-09 的實際值比。模型只用 2025-09 以前的 S&P 500 歷史訓練，
所以這段期間對它完全是樣本外。
限制：只有一段 9 個月的行情；財報是重述後的最後申報值；成分股用 2026-09 的名單（倖存者）。
輸出：results/window.txt、results/window_scores.csv
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import lab, now                                 # noqa: E402
from pef.data import load_macro                          # noqa: E402
from pef.ensemble import EnsembleForecaster              # noqa: E402
from pef.features import monthly_panel, quarterly_features   # noqa: E402
from pef.forecast import PEForecaster                    # noqa: E402
from pef.load import panel_sp500                         # noqa: E402

DATA = os.path.join(HERE, "data")
RES = os.path.join(HERE, "results")
ASOF = pd.Timestamp("2026-09-30")
H = (3, 6, 9)
GROUPS = ["S&P 500", "Nasdaq-100", "S&P 400 中型股", "S&P 600 小型股", "Russell 2000", "其他"]
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def norm(t):
    return str(t).upper().replace(".", "-").replace("/", "-")


def membership(idx_dir, sp500_tickers):
    m = {"S&P 500": {norm(t) for t in sp500_tickers}}
    for g, f in (("Nasdaq-100", "ndx"), ("S&P 400 中型股", "sp400"), ("S&P 600 小型股", "sp600"), ("Russell 2000", "rut")):
        d = pd.read_parquet(os.path.join(idx_dir, f"{f}-2026-09.parquet"))
        m[g] = {norm(t) for t in d["ticker"].dropna()}
    return m


def window_panel(Q, prices, meta, macro):
    """每家公司的月面板（2024-06 起；S&P 500 以外從 2025-12 起），市值＝月底股價 × 當時最新一季的股數。"""
    rows = []
    for t, (h, _) in prices.items():
        full = pd.date_range(h.index.min(), h.index.max(), freq="ME")
        h = h.reindex(full)
        q = Q[Q["ticker"] == t][["avail", "sh_now"]].dropna().sort_values("avail")
        if q.empty:
            continue
        px = pd.DataFrame({"month_end": h.index, "px": h.values})
        px = pd.merge_asof(px, q, left_on="month_end", right_on="avail", direction="backward")
        px["mc"] = px["px"] * px["sh_now"]
        px["ticker"] = t
        px["month"] = px["month_end"] - pd.offsets.MonthBegin(1)
        rows.append(px[["ticker", "month", "mc", "px"]])
    p = pd.concat(rows, ignore_index=True)
    qf = quarterly_features(Q)
    df = monthly_panel(qf, p, macro)
    df = df[df["mc"].notna() & ((df["month_end"] - df["period_end"]).dt.days <= 240)].reset_index(drop=True)
    df = df.merge(meta[["ticker", "sector", "in_sp500"]], on="ticker", how="left")
    df["train"] = False
    return df, qf


def main():
    ap = argparse.ArgumentParser()
    for k in ("lg", "oz", "ozm", "stooq", "idx"):
        ap.add_argument(f"--{k}", required=True)
    a = ap.parse_args()
    sp = pd.read_csv(os.path.join(DATA, "universe_sp500.csv"), keep_default_na=False)
    tech = pd.read_csv(os.path.join(DATA, "universe.csv"), keep_default_na=False)
    Q, prices, meta = now.build(a.lg, pd.read_csv(a.oz), pd.read_csv(a.ozm), a.stooq, sp, tech, "2026-09-24")
    macro = load_macro(DATA)
    df, qf = window_panel(Q, prices, meta, macro)
    d = lab.build(df, qf)
    mem = membership(a.idx, pd.read_csv(os.path.join(DATA, "universe_sp500.csv"))["ticker"])
    alias = {r.ticker: {norm(r.ticker)} | {norm(x) for x in str(r.aliases).split() if x and x != "nan"} for r in meta.itertuples()}
    def groups_of(t):
        keys = alias.get(t, {norm(t)})
        gs = [g for g in GROUPS[:-1] if keys & mem[g]]
        return gs or ["其他"]
    say(f"樣本外期間 2025-12 → 2026-09；有財報＋股價的公司 {d['ticker'].nunique()} 家")
    say("各指數涵蓋（2026-09 成分股中，有資料的家數）：" + "、".join(
        f"{g} {sum(1 for t in d['ticker'].unique() if g in groups_of(t))}/{len(mem[g])}" for g in GROUPS[:-1]))

    tr_df, tr_qf = panel_sp500()
    fc = PEForecaster().fit(tr_df, ASOF)
    ens = EnsembleForecaster(horizons=H).fit(tr_df, tr_qf, ASOF, old=fc)
    te = d[(d["month"] >= "2025-12-01") & (d["month"] <= "2026-06-01") & d["sigma"].notna() & d["m_bar"].notna() & (d["mc"] > 0)]
    te = te.reset_index(drop=True)
    e = ens.predict(te)
    out = []
    for h in H:
        x = te[["ticker", "month", "ln_pe", f"ln_pe_f{h}", "mc"]].copy()
        x["h"], x["ens"] = h, e[f"ens_{h}"].to_numpy()
        x = x.rename(columns={f"ln_pe_f{h}": "actual"})
        out.append(x)
    p = pd.concat(out, ignore_index=True)
    p = p[p["actual"].notna() & p["ln_pe"].notna() & p["ens"].notna()]
    rows = []
    p["groups"] = p["ticker"].map({t: groups_of(t) for t in p["ticker"].unique()})
    for g in GROUPS:
        x = p[p["groups"].apply(lambda gs: g in gs)]
        for h in H:
            y = x[x["h"] == h]
            if len(y) < 30:
                continue
            em, er = y["ens"] - y["actual"], y["ln_pe"] - y["actual"]
            pc = y.assign(em=em.abs(), er=er.abs()).groupby("ticker")[["em", "er"]].median()
            rows.append({"群組": g, "h": h, "公司數": y["ticker"].nunique(), "n": len(y),
                         "本益比不變": float(er.abs().median()), "模型": float(em.abs().median()),
                         "改善": float(em.abs().median() / er.abs().median() - 1),
                         "OOS_R2": float(1 - np.sum(np.minimum(em ** 2, 4)) / np.sum(np.minimum(er ** 2, 4))),
                         "方向命中": float(np.mean(np.sign(y["ens"] - y["ln_pe"]) == np.sign(y["actual"] - y["ln_pe"]))),
                         "模型較準的公司": float((pc["em"] < pc["er"]).mean()),
                         "市值中位_億美元": float(y["mc"].median() / 1e8)})
    s = pd.DataFrame(rows)
    say("\n== 樣本外（2025-12 → 2026-09）× 指數 × 預測距離")
    say(s.set_index(["群組", "h"]).round(3).to_string())
    s.to_csv(os.path.join(RES, "window_scores.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "window.txt"), "w").write(buf.getvalue())
    return p


if __name__ == "__main__":
    main()
