#!/usr/bin/env python3
"""README §25.2：用使用者提供的 Bloomberg 共識（2019-01～2026-09 每月，未來 12 個月／第 13–24 個月／第 25–36 個月 EPS）
回測「每個月當起點」預估 12、24 個月後的本益比；測「分析師的第二年預估」能不能當成長定價的「目標日成長預期」。

    python3 research/bbg_consensus_test.py --xlsx <Bloomberg 匯出檔> --cache <orbit_x2.pkl 目錄> --build <pk pickle> --raw <Yahoo JSON 目錄> > results/bbg_consensus.txt

本益比的分母一律是最近四季 GAAP 稀釋 EPS（面板；目標日 2026-09 用 research/case_broad 抓的 Yahoo 最近四季 EPS），分子是月底收盤價。
Bloomberg 的 EPS 是調整後（BEst）口徑，和 I/B/E/S 一樣乘上共識校正係數（同一家、同一個月的走動式校正；沒有的月份沿用最近 12 個月內的一筆）。
起點：每個月（2019-01～），12 個月目標日到 2025-09（面板）＋ 2026-09；24 個月同理。只評面板裡的公司（S&P 500）；起點或目標日虧損、前後 4 個月有分割的不評。
方法（ln 預測本益比 − ln 實際）：
  事前：本益比不變｜軌道（EPS_a＝未來 12 個月 × 係數；EPS_b 延一年）｜軌道（EPS_b＝第 13–24 個月）｜成長定價（回歸）｜成長定價（第二年＝分析師預估）
        24 個月：軌道 EPS_a＝第 13–24 個月（分析師）vs 延一年 vs 不外推；成長定價 EPS_a、EPS_b＝第 13–24、25–36 個月
  猜對：軌道（EPS_a＝實際）｜成長定價（EPS_a＝實際、目標日的成長預期＝目標日的 Bloomberg 未來 12 個月 × 係數）
係數：走動式（起點那一年的版本，只用目標日在那年以前的 I/B/E/S 配對）。
"""
import argparse
import io
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "research"))
from pef import orbit, growth_price as GP               # noqa: E402
import bbg_load as BL                                    # noqa: E402

RES = os.path.join(HERE, "results")
GNAME = orbit.GNAME
T_LAST = pd.Timestamp("2026-09-01")
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def now_eps(raw):
    """2026-09 月底的最近四季 EPS（今天的股數口徑）：網頁資料的今天 EPS（2026-10-12；Q3 財報多半在 10/12 以後才公布，和 9/30 相同）。"""
    import make_orbit_page as MP                         # noqa: E402
    tk, _ = MP.tickers()
    return {d["t"]: float(d["e"]) for d in tk if d.get("e")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--build", required=True)
    ap.add_argument("--raw", default=None)
    ap.add_argument("--rows", default=None, help="逐列結果寫到哪（不進版控；預設不寫）")
    a = ap.parse_args()
    D, info = BL.load(a.xlsx)
    x = pd.read_pickle(os.path.join(a.cache, "orbit_x2.pkl"))
    b = pd.read_pickle(a.build)
    model = orbit.load_model()
    gm = GP.load()
    wb = pd.read_csv(os.path.join(RES, "orbit_beta.csv")).set_index(["h", "年", "方法", "組別"])
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 40)

    x = x[x["month"] >= "2018-01-01"].copy()
    tick = sorted(set(x["ticker"]) & set(D["px"].columns))
    x = x[x["ticker"].isin(tick)]
    # 分割事件（面板股數口徑改變的月份）
    xs = x.sort_values(["ticker", "month"])
    chg = xs.groupby("ticker")["split_fac"].diff().fillna(0) != 0
    evd = {t: g["month"].tolist() for t, g in xs.loc[chg, ["ticker", "month"]].groupby("ticker")}
    # 共識校正：同一家、同一個月；沒有就用最近 12 個月內最後一筆
    pk = b[["ticker", "month", "pk"]].dropna().sort_values("month")
    pkd = {t: g.set_index("month")["pk"] for t, g in pk.groupby("ticker")}

    def kfac(t, m):
        s = pkd.get(t)
        if s is None:
            return 0.0
        s = s[(s.index <= m) & (s.index > m - pd.DateOffset(months=12))]
        return float(s.iloc[-1]) if len(s) else 0.0

    long = {k: D[k].stack().rename(k) for k in ("px", "f1", "f2", "f3")}
    bb = pd.concat(long, axis=1).reset_index().rename(columns={"level_0": "month", "level_1": "ticker", "px": "P"})
    x = x.merge(bb, on=["ticker", "month"], how="left")
    # 口徑：Bloomberg 是分割還原到 2026-09、面板到 2025-09 → 每檔一個固定倍數（之間有分割才 ≠ 1）。取中位數、對到乾淨的分割比例；
    # 對不上（差 > 5%，例：Bloomberg 也還原了分拆）的整檔不評。
    clean = [1.0] + [c for c in (1.5, 2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 30, 40, 50, 100)] + [1 / c for c in (1.5, 2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 30, 40, 50, 100)]
    rr = (x["P"] / x["px"]).groupby(x["ticker"]).median()
    bas = {}
    for t, v in rr.items():
        if not (np.isfinite(v) and v > 0):
            continue
        c = min(clean, key=lambda c_: abs(np.log(v / c_)))
        if abs(np.log(v / c)) <= 0.05:
            bas[t] = c
    say(f"Bloomberg × 面板：{len(tick)} 家重疊；口徑對得上 {len(bas)} 家（其中有分割倍數 ≠ 1 的 {sum(1 for v in bas.values() if v != 1)} 家）")
    x["basis"] = x["ticker"].map(bas)
    x = x[x["basis"].notna()]
    eT = now_eps(a.raw)
    # 目標日 2026-09 的列（只有收盤價與最近四季 EPS）
    last = D["px"].loc[T_LAST]
    rows = []
    for h in (12, 24):
        st = x[(x["month"] >= "2019-01-01") & (x["eps0"] > 0) & (x["f1"] > 0) & x["P"].notna()].copy()
        st["T"] = st["month"] + pd.DateOffset(months=h)
        tg = x[["ticker", "month", "px", "eps0", "P", "f1"]].rename(columns={"month": "T", "px": "pxT", "eps0": "eT", "P": "PT", "f1": "f1T"})
        d = st.merge(tg, on=["ticker", "T"], how="left")
        # 2026-09 目標日：收盤價（Bloomberg）÷ 今天口徑的最近四季 EPS；起點換到今天口徑
        m26 = d["T"] == T_LAST
        d.loc[m26, "PT"] = d.loc[m26, "ticker"].map(last)
        d.loc[m26, "eT_now"] = d.loc[m26, "ticker"].map(eT)
        d["peT"] = np.where(m26, d["PT"] / d["eT_now"], d["pxT"] / d["eT"])
        d = d[np.isfinite(d["peT"]) & (d["peT"] > 0)]
        near = [any(T_ - pd.DateOffset(months=4) < e <= T_ + pd.DateOffset(months=1) for e in evd.get(t, [])) or
                any(m_ - pd.DateOffset(months=4) < e <= m_ + pd.DateOffset(months=1) for e in evd.get(t, []))
                for t, T_, m_ in zip(d["ticker"], d["T"], d["month"])]
        d = d[~np.array(near)]
        for r in d.itertuples(index=False):
            Y = r.month.year
            grp = r.grp if r.grp in GNAME else "other"
            gn = GNAME[grp]
            if (h, Y, "預期b＋修正ab", gn) not in wb.index or str(Y) not in gm["by_year"][str(h)]:
                continue
            bs = float(r.basis)
            p0, e0 = float(r.px), float(r.eps0)               # 面板口徑
            F1, F2, F3 = (float(v) / bs if np.isfinite(v) else np.nan for v in (r.f1, r.f2, r.f3))
            k = float(np.exp(kfac(r.ticker, r.month)))
            pe1 = float(r.peT)
            if r.T == T_LAST:
                e1 = float(r.eT_now) / bs                         # 今天口徑 → 起點的面板口徑（近似：起點到今天的分割倍數）
            else:
                e1 = float(r.eT)
            if not (e1 > 0):
                continue
            dy0 = float(r.dy) if np.isfinite(r.dy) else 0.0
            orb = (float(r.y10) + model["erp"] - dy0) * h / 12
            b_exp = float(wb.loc[(h, Y, "預期b＋修正ab", gn), "b0"])
            b_raw = float(wb.loc[(h, Y, "原始成長a", gn), "b0"])
            g = float(np.clip(F1 / e0, 0.7, 1.5))
            vol0 = float(r.vol36) if np.isfinite(r.vol36) else np.nan
            ret0 = float(r.ret12) if np.isfinite(r.ret12) else None
            row = dict(px=p0, eps0=e0, y10=float(r.y10), dy=dy0, vol36=vol0, grp=grp)
            gp_ = lambda ea_, eb_: GP.predict(row, h, ea_, eb_, F1 * k, ret0, model=model, gm=gm, year=Y) if (ea_ and eb_ and ea_ > 0 and eb_ > 0) else None  # noqa: E731
            lg = lambda o: np.log(o["pe"] / pe1) if o else np.nan                                      # noqa: E731
            orbit_pe = lambda ea_, eb_: np.log(p0 * np.exp(orb + b_exp * np.log(eb_ / e0)) / ea_ / pe1) if (ea_ > 0 and eb_ > 0) else np.nan  # noqa: E731
            G0_ = float(np.clip(np.log(F1 * k / e0), -1.5, 1.5))
            gt12 = gm["by_year"]["12"][str(Y)]["gt_hat"]
            if h == 12:
                ea = F1 * k
                ea_r = ea
                ea2, eb2 = ea, (F2 * k if F2 > 0 else np.nan)
            else:
                ea = F1 * k * g
                ea_r = F1 * k * np.exp(gt12[0] + gt12[1] * G0_)
                ea2, eb2 = (F2 * k if F2 > 0 else np.nan), (F3 * k if F3 > 0 else np.nan)
            ft = float(r.f1T) / bs if (np.isfinite(r.f1T) and r.T != T_LAST) else (float(D["f1"].at[T_LAST, r.ticker]) / bs if r.ticker in D["f1"] else np.nan)
            kT = float(np.exp(kfac(r.ticker, r.T)))
            out = dict(ticker=r.ticker, month=r.month, T=r.T, year=Y, h=h, grp=gn, sector=r.sector,
                       U=np.log(p0 / e0 / pe1),
                       O=orbit_pe(ea, ea * g),
                       O_2=orbit_pe(ea2, eb2) if np.isfinite(ea2) and np.isfinite(eb2) else np.nan,
                       O_n=orbit_pe(F1 * k, F1 * k) if h == 24 else np.nan,
                       Gr=lg(gp_(ea_r, GP.eps_b_hat(gm, h, ea_r, e0, F1 * k, year=Y))),
                       G2=lg(gp_(ea2, eb2)) if np.isfinite(ea2) and np.isfinite(eb2) else np.nan,
                       O_or=np.log(p0 * np.exp(orb + b_raw * float(np.clip(np.log(e1 / e0), -2, 2))) / e1 / pe1),
                       G_or=lg(gp_(e1, ft * kT)) if np.isfinite(ft) and ft > 0 else np.nan,
                       eps_err1=np.log(ea / e1), eps_err2=np.log(ea2 / e1) if np.isfinite(ea2) else np.nan,
                       epsg=np.log(e1 / e0), T26=bool(r.T == T_LAST))
            rows.append(out)
    o = pd.DataFrame(rows)
    tech = o["grp"] != "非科技"
    o["H"] = o["Gr"].where(tech, o["O"])
    o["H2"] = o["G2"].where(tech, o["O_2"])
    o["組"] = np.where(tech, "科技", "非科技")
    if a.rows:
        o.to_csv(a.rows, index=False, float_format="%.5g")
    cols = [("U", "本益比不變"), ("O", "軌道（延一年）"), ("O_2", "軌道（第二年＝分析師）"), ("O_n", "軌道不外推"), ("Gr", "成長定價（回歸）"),
            ("G2", "成長定價（第二年＝分析師）"), ("H", "分組"), ("H2", "分組（分析師第二年）"), ("O_or", "猜對：軌道"), ("G_or", "猜對：成長定價")]

    def tab(df, by):
        rr = []
        for k_, g_ in df.groupby(by, observed=True):
            r_ = dict(zip(by, k_ if isinstance(k_, tuple) else [k_]))
            r_["n"] = len(g_)
            r_["家數"] = g_["ticker"].nunique()
            for c, nm in cols:
                e_ = g_[c].dropna()
                r_[nm] = float(np.median(np.abs(e_))) if len(e_) >= 20 else np.nan
            rr.append(r_)
        return pd.DataFrame(rr)
    for h in (12, 24):
        g = o[o["h"] == h]
        say(f"\n==================== {h} 個月：{len(g):,} 組（{g['ticker'].nunique()} 家；起點 {g['month'].min():%Y-%m}～{g['month'].max():%Y-%m}，每個月一個起點）")
        say(f"  分析師 EPS 誤差（中位 |ln(預估 ÷ 實際)|）：未來 12 個月 × 係數（{'延一年' if h == 24 else '原樣'}）{np.median(np.abs(g['eps_err1'].dropna())):.3f}"
            + (f"；第 13–24 個月 × 係數 {np.median(np.abs(g['eps_err2'].dropna())):.3f}" if h == 24 else ""))
        say("-- 依起點年份")
        say(tab(g, ["year"]).round(3).to_string(index=False))
        say("-- 依組別")
        say(tab(g, ["組"]).round(3).to_string(index=False))
        say(tab(g, ["year", "組"]).round(3).to_string(index=False))
        w = tab(g, ["year", "組"])
        for grp_lab in ("科技", "非科技"):
            t = w[w["組"] == grp_lab]
            say(f"  {grp_lab}：成長定價（第二年）勝成長定價（回歸）{int((t['成長定價（第二年＝分析師）'] < t['成長定價（回歸）']).sum())}／{len(t)} 年；"
                f"成長定價（回歸）勝軌道 {int((t['成長定價（回歸）'] < t['軌道（延一年）']).sum())}；軌道（第二年）勝軌道（延一年）{int((t['軌道（第二年＝分析師）'] < t['軌道（延一年）']).sum())}；"
                f"猜對時成長定價勝軌道 {int((t['猜對：成長定價'] < t['猜對：軌道']).sum())}")
        say("  ±20%：" + "、".join(f"{nm} {np.mean(np.abs(np.exp(g[c].dropna()) - 1) <= 0.2):.0%}" for c, nm in cols if g[c].notna().any()))
    open(os.path.join(RES, "bbg_consensus.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
