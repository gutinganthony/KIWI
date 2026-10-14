#!/usr/bin/env python3
"""README §24.3：成長定價模型（pef/growth_price.py）的正式版係數與區間 → results/growth_price.json

    python3 research/growth_price_fit.py --build <lab_eps_correction.py 的 L.build pickle> > results/growth_price_fit.txt

配對和 research/rerating_lab.py 一樣（起點距離年報 10.5–12 個月、目標日 T＝起點＋h、T 時剛換到下一個財年）；
共識換成預期的 GAAP（走動式共識校正）。目標：本益比的變化扣掉軌道
  y ＝ ln(T 的股價 ÷ EPS_a) − ln(今天本益比) − 軌道 × h/12
  線索：ga＝ln(EPS_a ÷ 今天 EPS)、GT＝ln(T 時的共識 ÷ EPS_a)、G0＝ln(今天的共識 ÷ 今天 EPS)、ret12c＝過去 12 個月 ln 報酬（截在 ±1）
係數（Huber）：非科技自己估、科技三組共用全部一起估（科技樣本太小）。
  正式版：目標日 ≤ 2025-09-30 的全部配對；走動式（by_year）：每個年份 Y 只用目標日在 Y 年以前的配對（回測、回頭驗證用）。
區間：走動式預測誤差 ÷ (波動^α × exp(δ × min(|ga|, 2)))（α 和軌道模型一樣，δ 用區間分數挑）、置中後的 10／25／75／90% 分位數；同時報告「只用前幾年校準」的樣本外涵蓋率。
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
from pef import cond, growth_price as GP                 # noqa: E402
from pef.stats import huber_ols                          # noqa: E402
import rerating_lab as RL                                # noqa: E402
import usage_backtest as UB                              # noqa: E402

RES = os.path.join(HERE, "results")
CUTOFF = pd.Timestamp("2025-09-30")
Q = (0.1, 0.25, 0.75, 0.9)
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def prep(b, h):
    d = RL.pairs(b, h)
    d["lpe0"] = np.log(d["px"] / d["eps0"])
    x = pd.DataFrame([GP.features(e0, ea, ft, f0, r) or {k: np.nan for k in GP.FEATS}
                      for e0, ea, ft, f0, r in zip(d["eps0"], d["EA"], d["FTk"], d["F0k"], d["ret12"])], index=d.index)
    d = d.drop(columns=["G0", "GT"]).join(x)              # 同定義（pef/growth_price.features），以正式版的函式為準
    d["y"] = d["act"] - d["lpe0"] - d["orbit_lr"] * h / 12
    return d.dropna(subset=GP.FEATS + ["y"])


def fit(tr):
    out = {}
    for key, sub in (("all", tr), ("other", tr[tr["grp"] == "other"])):
        if len(sub) < 150:
            continue
        X = np.column_stack([np.ones(len(sub))] + [sub[c].to_numpy(float) for c in GP.FEATS])
        out[key] = [float(v) for v in huber_ols(X, sub["y"].to_numpy(float))]
    return out


def apply(d, co):
    c = np.array([co["other"] if (g == "other" and "other" in co) else co["all"] for g in d["grp"]])
    X = np.column_stack([np.ones(len(d))] + [d[k].to_numpy(float) for k in GP.FEATS])
    return (c * X).sum(axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    a = ap.parse_args()
    b = pd.read_pickle(a.build)
    b["pk"] = UB.correction_wf(b)
    model = json.load(open(os.path.join(RES, "orbit_model.json")))
    out = dict(version="2026-10-14", note="README §24：成長定價。y＝本益比變化扣掉軌道 ＝ a ＋ c·[ga, GT, G0, ret12c]；係數順序 [a, c_a, c_T, c_0, c_r]",
               feats=GP.FEATS, fit_cutoff=str(CUTOFF.date()), h={}, by_year={})
    for h in (12, 24):
        d = prep(b, h)
        prod = d[d["T"] <= CUTOFF]
        co = fit(prod)
        by = {}
        pred = pd.Series(np.nan, index=d.index)
        for Y in range(2015, 2027):
            tr = d[d["T"] < pd.Timestamp(f"{Y}-01-01")]
            if len(tr) < 300:
                continue
            by[str(Y)] = fit(tr)
            te = d["year"] == Y
            if te.any():
                pred.loc[te] = apply(d[te], by[str(Y)])
        e = (pred - d["y"]).dropna()
        vmed = float(d["vol36"].median())
        base = np.clip(d["vol36"].where(np.isfinite(d["vol36"]), vmed), *cond.VOL_CLIP) ** model["alpha"]
        # EPS 變化越大區間越寬（同 §22.4）：sc ×＝ exp(δ × min(|ga|, 2))，δ 用區間分數挑
        aga = d.loc[e.index, "ga"].abs().clip(upper=2)
        best = None
        for dl in (0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0):
            sc_ = base.loc[e.index] * np.exp(dl * aga)
            uu = e / sc_
            uu = uu - uu.median()
            lo_, hi_ = np.quantile(uu, [0.1, 0.9])
            isc = float(np.mean(((hi_ - lo_) + 10 * np.maximum(lo_ - uu, 0) + 10 * np.maximum(uu - hi_, 0)) * sc_))
            best = (isc, dl) if best is None or isc < best[0] else best
        delta = best[1]
        base = base * np.exp(delta * d["ga"].abs().clip(upper=2))
        u = (e / base.loc[e.index])
        u = u - u.median()
        q = [float(v) for v in np.quantile(u, Q)]
        # 樣本外涵蓋：每年只用前幾年的誤差校準 10／90%
        cov = []
        for Y in sorted(d.loc[e.index, "year"].unique()):
            prev = u[d.loc[u.index, "year"] < Y]
            cur = e[d.loc[e.index, "year"] == Y]
            if len(prev) < 200 or cur.empty:
                continue
            lo, hi = np.quantile(prev - prev.median(), [0.1, 0.9])
            s = base.loc[cur.index]
            cov.append(dict(年=int(Y), n=len(cur), 涵蓋=float(((cur >= lo * s) & (cur <= hi * s)).mean())))
        cov = pd.DataFrame(cov)
        ga_bin = pd.cut(d.loc[e.index, "ga"].abs(), [0, 0.25, 0.5, 1, 5], labels=["|ga|<0.25", "0.25–0.5", "0.5–1", ">1"], include_lowest=True)
        inside = (e >= q[0] * base.loc[e.index]) & (e <= q[3] * base.loc[e.index])
        out["h"][str(h)] = dict(coef=co, q=q, delta=delta, vol_median=vmed, n=int(len(prod)), firms=int(prod["ticker"].nunique()),
                                months=[str(prod["month"].min().date()), str(prod["month"].max().date())],
                                wf_median_abs=float(np.median(np.abs(e))), wf_cover80=float(cov["涵蓋"].mean()) if len(cov) else None)
        out["by_year"][str(h)] = by
        say(f"\n== {h} 個月：正式版用 {len(prod):,} 組配對（{prod['ticker'].nunique()} 家，起點 {prod['month'].min():%Y-%m}～{prod['month'].max():%Y-%m}）")
        names = ["截距"] + GP.FEATS
        say("  正式版係數：" + "；".join(f"{k}：" + "、".join(f"{n_} {v:+.3f}" for n_, v in zip(names, c)) for k, c in co.items()))
        say(f"  走動式（{len(e):,} 筆）中位 |本益比誤差| {np.median(np.abs(e)):.3f}；δ＝{delta:g}；區間分位數（÷ 波動^α × exp(δ|ga|)）{', '.join(f'{v:+.3f}' for v in q)}")
        say(f"  樣本外 80% 涵蓋（每年只用前幾年校準）：平均 {cov['涵蓋'].mean():.0%}；逐年 " + "、".join(f"{r.年} {r.涵蓋:.0%}" for r in cov.itertuples()))
        say("  依 |交出的成長| 分組的涵蓋（全樣本分位數）：" + "、".join(f"{k} {v:.0%}" for k, v in inside.groupby(ga_bin, observed=True).mean().items()))
        say("  依組別：" + "、".join(f"{RL.GNAME[k]} {v:.0%}" for k, v in inside.groupby(d.loc[e.index, "grp"]).mean().items()))
        for Y in sorted(by):
            say(f"  走動式 {Y}：" + "；".join(f"{k} " + "、".join(f"{v:+.2f}" for v in c) for k, c in by[Y].items()))
    json.dump(out, open(os.path.join(RES, "growth_price.json"), "w"), ensure_ascii=False, indent=1)
    open(os.path.join(RES, "growth_price_fit.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
