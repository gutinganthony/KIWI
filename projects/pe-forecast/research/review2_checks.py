#!/usr/bin/env python3
"""REVIEW_2026-10-14.md 的數字：第二次審閱（整套本益比模型）的檢查（2026-10-14）。

    python3 research/review2_checks.py --build <pk pickle> --cache <orbit_x2.pkl 目錄> > results/review2.txt

讀 results/long_backtest_rows.csv.gz（§25.1 的逐列結果）、共識配對（rerating_lab.pairs）、面板。六個檢查：
  1 市場層級：誤差裡有多少是「大盤本益比變了」（知道大盤變化、或只看相對誤差時剩多少）
  2 配對 bootstrap：軌道 vs 成長定價（回歸）的差距在不在雜訊內（依起點年份整年重抽）
  3 混合：w × 成長定價 ＋ (1 − w) × 軌道，固定 w 與走動式挑 w
  4 相對估值線索：在成長定價的事前迴歸加「相對產業／大盤／自己歷史的本益比」，走動式有沒有更準
  5 拆解：成長定價事前的預測，和「軌道 β＝0」「＋走動式截距」「＋過去 12 個月報酬反轉」差多少（事前時三個成長項代數上互相抵銷）
  6 區間：固定分位數（正式版，用 EPS 猜對的誤差校準）vs 走動式 conformal（只用起點前已到期配對的共識模式誤差）
另附：面板每年實際的 12 個月股價中位變化 vs 軌道假設（10 年期 ＋ 5% − 股利殖利率）。
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "research"))
from pef.stats import huber_ols                          # noqa: E402
import rerating_lab as RL                                # noqa: E402

RES = os.path.join(HERE, "results")
W = (0, 0.25, 0.5, 0.75, 1.0)


def med(e):
    e = np.asarray(e, float)
    e = e[np.isfinite(e)]
    return float(np.median(np.abs(e))) if len(e) else np.nan


def check1_market(o):
    print("== 1. 市場層級誤差（全期係數列）：|e| ｜ 知道大盤本益比變化時 |e ＋ 大盤變化| ｜ 相對誤差（扣掉同一起點月全體的中位誤差）")
    for h in (12, 24):
        P = o[(o["h"] == h) & (o["mode"] == "prod")]
        oc = "O" if h == 12 else "O_n"
        for c, nm in ((oc, "軌道"), ("Gr", "成長定價（回歸）"), ("U", "本益比不變"), ("O_or", "猜對：軌道"), ("GA", "猜對：成長定價")):
            rel = P[c] - P.groupby("month")[c].transform("median")
            print(f"  {h} 個月 {nm:10s} {med(P[c]):.3f} ｜ {med(P[c] + P['mkt_dpe']):.3f} ｜ {med(rel):.3f}")


def check2_bootstrap(o, n_boot=2000):
    rng = np.random.default_rng(0)
    print("\n== 2. 配對 bootstrap（依起點年份整年重抽 2,000 次）：成長定價（回歸）− 軌道 的中位 |e| 差，負＝成長定價較準")
    for h in (12, 24):
        oc = "O" if h == 12 else "O_n"
        for mode in ("wf", "prod"):
            D = o[(o["h"] == h) & (o["mode"] == mode)]
            for grp, m in (("科技", D["grp"] != "非科技"), ("非科技", D["grp"] == "非科技")):
                g = D[m]
                yrs = sorted(g["year"].unique())
                by = {y: g[g["year"] == y] for y in yrs}
                d = np.array([(lambda s: med(s["Gr"]) - med(s[oc]))(pd.concat([by[y] for y in rng.choice(yrs, len(yrs), replace=True)])) for _ in range(n_boot)])
                obs = med(g["Gr"]) - med(g[oc])
                print(f"  {h} 個月 {'走動式' if mode == 'wf' else '全期':3s} {grp:3s} n={len(g):5,d} 年數 {len(yrs):2d}  觀察差 {obs:+.4f}  90% 區間 [{np.quantile(d, .05):+.4f}, {np.quantile(d, .95):+.4f}]  P(成長定價較準) {np.mean(d < 0):.2f}")


def check3_blend(o):
    print("\n== 3. 混合 w × 成長定價（回歸）＋ (1 − w) × 軌道（ln 空間；全期係數列）：中位 |e|")
    for h in (12, 24):
        oc = "O" if h == 12 else "O_n"
        P = o[(o["h"] == h) & (o["mode"] == "prod")]
        for grp, m in (("科技", P["grp"] != "非科技"), ("非科技", P["grp"] == "非科技"), ("全部", P["grp"].notna())):
            g = P[m]
            yrs = sorted(g["year"].unique())
            errs = []
            for i, y in enumerate(yrs):
                if i < 3:
                    continue
                prev, cur = g[g["year"] < y], g[g["year"] == y]
                wb = min(W, key=lambda w: med(w * prev["Gr"] + (1 - w) * prev[oc]))
                errs.append(wb * cur["Gr"] + (1 - wb) * cur[oc])
            same = g[g["year"] >= yrs[3]]
            print(f"  {h} 個月 {grp:3s} " + "  ".join(f"w={w}: {med(w * g['Gr'] + (1 - w) * g[oc]):.3f}" for w in W)
                  + f"  ｜ {yrs[3]} 起走動式挑 w {med(pd.concat(errs)):.3f}、固定 0.5 {med(0.5 * same['Gr'] + 0.5 * same[oc]):.3f}、軌道 {med(same[oc]):.3f}、成長定價 {med(same['Gr']):.3f}")


def check45_features(b):
    b = b.copy()
    b["lpe"] = np.log(b["px"] / b["eps0"]).where(b["eps0"] > 0)
    b["lpe_sec"] = b.groupby(["month", "sector"])["lpe"].transform("median")
    b["lpe_mkt"] = b.groupby("month")["lpe"].transform("median")
    b["lfpe"] = np.log(b["px"] / b["feps"]).where(b["feps"] > 0)
    b["lfpe_sec"] = b.groupby(["month", "sector"])["lfpe"].transform("median")
    b = b.sort_values(["ticker", "month"])
    b["lpe_own36"] = b.groupby("ticker")["lpe"].transform(lambda s: s.rolling(36, min_periods=12).median().shift(1))
    specs = {"基準 ga, GT, G0, ret12": ["ga", "GT", "G0", "ret12c"],
             "＋相對產業（trailing）": ["ga", "GT", "G0", "ret12c", "prem_sec"],
             "＋相對產業（forward）": ["ga", "GT", "G0", "ret12c", "prem_fsec"],
             "＋相對大盤": ["ga", "GT", "G0", "ret12c", "prem_mkt"],
             "＋相對自己 36 個月": ["ga", "GT", "G0", "ret12c", "prem_own"],
             "＋產業＋自己": ["ga", "GT", "G0", "ret12c", "prem_sec", "prem_own"],
             "＋產業＋自己＋波動": ["ga", "GT", "G0", "ret12c", "prem_sec", "prem_own", "lvol"]}
    print("\n== 4. 成長定價的事前迴歸加「相對估值」線索（走動式 2017 起；事前 C 模式 ｜ 猜對 A 模式）：中位 |e|")
    for h in (12, 24):
        d = RL.pairs(b, h)
        d = d[d["year"] <= 2024].copy()
        d["lpe0"] = np.log(d["px"] / d["eps0"])
        d["orb"] = d["orbit_lr"] * h / 12
        d["yo"] = d["act"] - d["lpe0"] - d["orb"]
        d["ga"] = np.log(d["EA"] / d["eps0"]).clip(-2, 2)
        d["ret12c"] = d["ret12"].fillna(0).clip(-1, 1)
        d["prem_sec"] = (d["lpe0"] - d["lpe_sec"]).clip(-1.5, 1.5)
        d["prem_fsec"] = (d["lfpe0"] - d["lfpe_sec"]).clip(-1.5, 1.5)
        d["prem_mkt"] = (d["lpe0"] - d["lpe_mkt"]).clip(-1.5, 1.5)
        d["prem_own"] = (d["lpe0"] - d["lpe_own36"]).clip(-1.5, 1.5)
        d["lvol"] = np.log(d["vol36"].clip(0.1, 1.5))
        g = (d["F0k"] / d["eps0"]).clip(0.7, 1.5)
        EAc = d["F0k"] if h == 12 else d["F0k"] * g
        d["ga_c"] = np.log(EAc / d["eps0"]).clip(-2, 2)
        res = {k: pd.Series(np.nan, index=d.index) for k in specs}
        res_or = {k: pd.Series(np.nan, index=d.index) for k in specs}
        yb = d["act"] - d["lpe0"] - d["orb"] + d["ga_c"]                 # 扣掉「EPS 一比一稀釋」後剩下的本益比變化
        r0, r1, r2 = (pd.Series(np.nan, index=d.index) for _ in range(3))
        k = co = None
        for Y in range(2017, 2025):
            tr, te = d[d["T"] < pd.Timestamp(f"{Y}-01-01")], d[d["year"] == Y]
            if len(tr) < 300 or te.empty:
                continue
            z = tr.dropna(subset=["GT", "G0"])
            ab = huber_ols(np.column_stack([np.ones(len(z)), z["G0"]]), z["GT"].to_numpy(float))
            for kk, cols in specs.items():
                trc = tr.dropna(subset=cols + ["yo"])
                cf = huber_ols(np.column_stack([np.ones(len(trc))] + [trc[c].to_numpy(float) for c in cols]), trc["yo"].to_numpy(float))
                xe = te.copy()
                xe["ga"] = xe["ga_c"]
                xe["GT"] = (ab[0] + ab[1] * xe["G0"]).clip(-1.5, 1.5)
                okm = xe[cols].notna().all(axis=1)
                Xe = np.column_stack([np.ones(int(okm.sum()))] + [xe.loc[okm, c].to_numpy(float) for c in cols])
                res[kk].loc[xe.index[okm]] = xe.loc[okm, "lpe0"] + xe.loc[okm, "orb"] + Xe @ cf - xe.loc[okm, "act"]
                oko = te[cols].notna().all(axis=1)
                Xo = np.column_stack([np.ones(int(oko.sum()))] + [te.loc[oko, c].to_numpy(float) for c in cols])
                res_or[kk].loc[te.index[oko]] = te.loc[oko, "lpe0"] + te.loc[oko, "orb"] + Xo @ cf - te.loc[oko, "act"]
            k = float(np.median(yb.loc[tr.index]))
            co = huber_ols(np.column_stack([np.ones(len(tr)), tr["ret12c"]]), yb.loc[tr.index].to_numpy(float))
            base_pe = te["lpe0"] + te["orb"] - te["ga_c"]
            r0.loc[te.index] = base_pe - te["act"]
            r1.loc[te.index] = base_pe + k - te["act"]
            r2.loc[te.index] = base_pe + co[0] + co[1] * te["ret12c"] - te["act"]
        ok = pd.concat(res, axis=1).notna().all(axis=1)
        tech = (d["grp"] != "other")[ok]
        print(f"-- {h} 個月，{int(ok.sum()):,} 組同一批列")
        for kk in specs:
            e, eo = res[kk][ok], res_or[kk][ok]
            print(f"  {kk:20s} 事前 全部 {med(e):.3f} 科技 {med(e[tech]):.3f} 非科技 {med(e[~tech]):.3f} ｜ 猜對 全部 {med(eo):.3f} 科技 {med(eo[tech]):.3f} 非科技 {med(eo[~tech]):.3f}")
        base = res["基準 ga, GT, G0, ret12"][ok]
        print(f"  5. 拆解（同一批列）：軌道 β＝0 {med(r0[ok]):.3f} → ＋走動式截距 {med(r1[ok]):.3f} → ＋ret12 反轉 {med(r2[ok]):.3f} ｜ 成長定價事前 {med(base):.3f}"
              f"（最後一年：截距 {k:+.3f}、ret12 斜率 {co[1]:+.3f}；偏差中位：軌道 β＝0 {float(np.median(r0[ok])):+.3f}、成長定價 {float(np.median(base)):+.3f}）")


def check6_conformal(o, b):
    o = o.merge(b[["ticker", "month", "vol36"]], on=["ticker", "month"], how="left")
    print("\n== 6. 80% 區間涵蓋：固定分位數（正式版）vs 走動式 conformal（只用起點前已到期配對的共識模式誤差 ÷ 波動^0.7 的 10／90% 分位數）；軌道、全期係數列")
    for h in (12, 24):
        P = o[(o["h"] == h) & (o["mode"] == "prod")].copy()
        oc = "O" if h == 12 else "O_n"
        P["u"] = P[oc] / np.clip(P["vol36"].fillna(P["vol36"].median()), 0.1, 1.5) ** 0.7
        rows = []
        for Y in sorted(P["year"].unique()):
            cur = P[P["year"] == Y]
            mat = P[P["T"] < cur["month"].min()]
            r = dict(年=Y, n=len(cur), 固定=float(cur["bO"].astype(float).mean()))
            if len(mat) >= 200:
                lo, hi = np.quantile(mat["u"], [0.1, 0.9])
                r["conformal"] = float(((cur["u"] >= lo) & (cur["u"] <= hi)).mean())
                r["寬度（u）"] = float(hi - lo)
            rows.append(r)
        t = pd.DataFrame(rows)
        print(f"-- {h} 個月\n" + t.round(2).to_string(index=False))
        print("   " + "；".join(f"{c}：平均 {t[c].mean():.2f}、最低 {t[c].min():.2f}" for c in ("固定", "conformal") if c in t))


def drift(x):
    x = x.sort_values(["ticker", "month"])
    x["lp12"] = np.log(x.groupby("ticker")["px"].shift(-12) / x["px"])
    g = x.groupby(x["month"].dt.year).agg(實際=("lp12", "median"), 軌道=("orbit_lr", "median")).dropna()
    print("\n== 附：面板每年（起點年份）12 個月 ln 股價變化的中位數 vs 軌道假設（10 年期 ＋ 5% − 股利殖利率）")
    print(g.T.round(3).to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    pd.set_option("display.width", 220)
    o = pd.read_csv(os.path.join(RES, "long_backtest_rows.csv.gz"), parse_dates=["month", "T"])
    b = pd.read_pickle(a.build)
    x = pd.read_pickle(os.path.join(a.cache, "orbit_x2.pkl"))
    check1_market(o)
    check2_bootstrap(o)
    check3_blend(o)
    check45_features(b)
    check6_conformal(o, b)
    drift(x)


if __name__ == "__main__":
    main()
