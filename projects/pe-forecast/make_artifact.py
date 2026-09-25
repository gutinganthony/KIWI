#!/usr/bin/env python3
"""把模型、回測、現在的預測打包成一頁互動網頁（artifact/page.html 樣板 ＋ 資料）。

    python3 make_artifact.py <輸出.html>

只讀 results/ 與 data/（lab_run.py、snapshot_run.py 的產出），約 30 秒。資料都是公開公司的財報與股價衍生數字。
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import ensemble as en   # noqa: E402
from pef import lab              # noqa: E402
from pef.load import panel       # noqa: E402

RES = os.path.join(HERE, "results")
ASOF = pd.Timestamp("2026-09-30")
Y10_NOW = 0.046                   # 快照用的 10 年期（2026-07 的值，見 results/snapshot_2026-09.md）
HIST_H = (6, 12, 36)
CASES = [   # (ticker, 預測月份, 標題, 類型)
    ("NVDA", "2021-07-01", "盈餘快速成長，本益比自然下降", "盈餘成長"),
    ("AMD", "2023-11-01", "帳面盈餘被攤銷壓低，本益比虛高", "一次性項目"),
    ("HPQ", "2022-11-01", "本益比 5 倍不是便宜，是盈餘在高點", "週期高點"),
    ("MU", "2025-09-01", "站在一年前，預測今天的美光", "推到現在"),
    ("NVDA", "2022-07-01", "模型沒看到 AI 行情", "失敗案例"),
]


def r(x, k=3):
    return None if x is None or not np.isfinite(x) else round(float(x), k)


def horizon_block():
    hz = pd.read_csv(os.path.join(RES, "lab_horizons_all.csv"))
    hz = hz[hz["口徑"] == "GAAP"]
    hits = pd.read_csv(os.path.join(RES, "lab_hits.csv")).set_index("h")
    nn = pd.read_csv(os.path.join(RES, "lab_near_now.csv"))
    nn = nn[nn["窗口"] == "最後12個月"].set_index("h")
    cov = pd.read_csv(os.path.join(RES, "lab_horizon.csv")).set_index("h")
    allh = pd.read_csv(os.path.join(RES, "lab_horizons_all.csv"))
    core = allh[(allh["口徑"] == "核心") & (allh["期間"] == "全期")].set_index("h")
    out = []
    for h in lab.HORIZONS:
        a = hz[(hz["h"] == h) & (hz["期間"] == "全期")].iloc[0]
        s = hz[(hz["h"] == h) & (hz["期間"] == "選模期")].iloc[0]
        o = hz[(hz["h"] == h) & (hz["期間"] == "保留期")].iloc[0]
        hi = hits.loc[h]
        out.append(dict(
            h=h, n=int(a["n"]), rw=r(a["隨機漫步_誤差"]), ens=r(a["組合_誤差"]), oracle=r(a["盈餘全知_誤差"]),
            imp=r(a["改善"]), r2_sel=r(s["OOS_R2"]), r2_hold=r(o["OOS_R2"]), n_hold=int(o["n"]),
            dir=r(hi["方向命中"]), big_dir=r(hi["大變動時方向命中"]), big_share=r(hi["大變動占比"]),
            in20=r(hi["組合_±20%內"]), in20_rw=r(hi["不變_±20%內"]), in30=r(hi["組合_±30%內"]),
            in30_rw=r(hi["不變_±30%內"]), beat=r(hi["組合比不變準的比例"]),
            cover=r(cov.loc[h, "實測涵蓋率"]), sc_cover=r(hi["情境區間_實測涵蓋率"]),
            now_imp=r(nn.loc[h, "改善"]) if h in nn.index else None,
            now_win=r(nn.loc[h, "組合贏的公司比例"]) if h in nn.index else None,
            now_n=int(nn.loc[h, "公司數"]) if h in nn.index else None,
            core_rw=r(core.loc[h, "隨機漫步_誤差"]), core_ens=r(core.loc[h, "組合_誤差"])))
    return out


def methods_block():
    s = pd.read_csv(os.path.join(RES, "lab_scores.csv"))
    s = s[s["h"] == 12]
    out = {}
    for per in ("選模期", "保留期"):
        g = s[(s["期間"] == per) & (s["比較"] == "各方法")].set_index("方法")
        o = s[(s["期間"] == per) & (s["比較"] == "舊模型")].set_index("方法")
        hh = s[(s["期間"] == per) & (s["比較"] == "歷史本益比特徵")].set_index("方法")
        out[per] = {m: dict(r2=r(g.loc[m, "OOS_R2"]), err=r(g.loc[m, "中位絕對誤差"])) for m in g.index}
        out[per]["old_vs"] = {m: r(o.loc[m, "OOS_R2"]) for m in o.index}
        out[per]["hist_vs"] = {m: r(hh.loc[m, "OOS_R2"]) for m in hh.index}
    return out


def history_block(p):
    out = {}
    for h in HIST_H:
        g = p[(p["h"] == h) & p["ens"].notna()].copy()
        g["tgt"] = (g["month"] + pd.DateOffset(months=h)).dt.strftime("%Y-%m")
        per = {}
        for t, x in g.groupby("ticker"):
            x = x.sort_values("tgt")
            months = pd.period_range(x["tgt"].iloc[0], x["tgt"].iloc[-1], freq="M").strftime("%Y-%m")
            x = x.set_index("tgt").reindex(months)
            f = lambda c: [None if not np.isfinite(v) else round(float(np.exp(v)), 1) for v in x[c].to_numpy(float)]
            per[t] = dict(s=months[0], pred=f("ens"), act=f("actual"), rw=f("ln_pe"))
        out[str(h)] = per
    return out


def sector_block(p):
    g = p[(p["h"] == 12) & p["actual"].notna() & p["ln_pe"].notna() & p["ens"].notna() & (p["month"] >= "2015-01-01")]
    g = g.assign(em=(g["ens"] - g["actual"]).abs(), er=(g["ln_pe"] - g["actual"]).abs())
    s = g.groupby("sector").agg(n=("em", "size"), rw=("er", "median"), ens=("em", "median"))
    return [dict(sector=k, n=int(v.n), rw=r(v.rw), ens=r(v.ens)) for k, v in s.iterrows()]


def cases_block(p, d):
    out = []
    for t, m, title, kind in CASES:
        m = pd.Timestamp(m)
        x = p[(p["h"] == 12) & (p["ticker"] == t) & (p["month"] == m)].iloc[0]
        row = d[(d["ticker"] == t) & (d["month"] == m)].iloc[0]
        coe = (row["y10"] + lab.ERP)
        impl = np.exp(np.log(row["mc"]) + coe - x["ens"])
        mem = {k: r(np.exp(x[k]), 1) if np.isfinite(x[k]) else None for k in ("old", "huber", "gbm", "gbm_z")}
        out.append(dict(
            ticker=t, month=m.strftime("%Y-%m"), target=(m + pd.DateOffset(months=12)).strftime("%Y-%m"),
            title=title, kind=kind, sector=x["sector"],
            pe0=r(np.exp(x["ln_pe"]), 1), pred=r(np.exp(x["ens"]), 1), act=r(np.exp(x["actual"]), 1),
            mc0=r(row["mc"] / 1e9, 1), mc1=r(row["mc_f12"] / 1e9, 1), ni0=r(row["ni_ttm"] / 1e9, 2),
            ni1=r(row["ni_ttm_f12"] / 1e9, 2), ni_impl=r(impl / 1e9, 2), coe=r(coe, 4), members=mem))
    return out


def current_block(d_bands):
    s = pd.read_csv(os.path.join(RES, "snapshot_2026-09.csv"), parse_dates=["month_end", "period_end"])
    order = ["四大CSP", "記憶體", "光通訊", "半導體設備", "能源", "電力", "軍工", "那斯達克其他"]
    s["g"] = s["group"].map({g: i for i, g in enumerate(order)})
    s = s.sort_values(["g", "ticker"])
    coe = Y10_NOW + lab.ERP
    out = []
    for x in s.itertuples():
        o = dict(ticker=x.ticker, group=x.group, anchor=x.month_end.strftime("%Y-%m"),
                 fin=x.period_end.strftime("%Y-%m-%d"), mc=r(x.mc / 1e9, 2), ni=r(x.ni_ttm / 1e9, 3),
                 pe=r(x.pe_now, 1) if x.ni_ttm > 0 else None, stale=bool(x.stale), adj=bool(x.adj),
                 tech=x.group not in ("能源", "電力", "軍工") and x.ticker != "TSLA",
                 old12=r(np.exp(x.lnpe_hat_12), 1) if x.ni_hat_12 > 0 else None,
                 core_pe=r(x.core_pe_now, 1) if np.isfinite(x.core_pe_now) and x.core_pe_now > 0 else None,
                 core12=r(np.exp(x.core_ens_12), 1) if np.isfinite(x.core_ens_12) else None, ens={}, impl={})
        for h in lab.HORIZONS:
            v = getattr(x, f"ens_{h}")
            o["ens"][h] = r(np.exp(v), 1) if np.isfinite(v) else None
            if np.isfinite(v):
                ni_h = np.exp(np.log(x.mc) + coe * h / 12 - v)
                o["impl"][h] = r(ni_h / x.ni_ttm - 1, 3) if x.ni_ttm > 0 else None
        out.append(o)
    return out


def main():
    out_path = sys.argv[1]
    df, qf = panel()
    d = lab.build(df, qf)
    p = pd.read_csv(os.path.join(RES, "lab_predictions.csv.gz"), parse_dates=["month"])
    ens_b = en.bands(ASOF)
    ret_b = en.return_bands(d, ASOF)
    data = dict(
        asof=ASOF.strftime("%Y-%m-%d"), y10=Y10_NOW, erp=lab.ERP,
        n_firms=int(d["ticker"].nunique()),
        bands={h: [r(a, 4), r(b, 4)] for h, (a, b) in ens_b.items()},
        ret_bands={h: [r(a, 4), r(b, 4)] for h, (a, b) in ret_b.items()},
        horizons=horizon_block(), methods=methods_block(), sectors=sector_block(p),
        cases=cases_block(p, d), current=current_block(ens_b), history=history_block(p),
        sector_of=p.groupby("ticker")["sector"].first().to_dict())
    tpl = open(os.path.join(HERE, "artifact", "page.html"), encoding="utf-8").read()
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = tpl.replace("/*__DATA__*/null", blob)
    open(out_path, "w", encoding="utf-8").write(html)
    print(f"寫入 {out_path}（{len(html) / 1e3:,.0f} KB）")


if __name__ == "__main__":
    main()
