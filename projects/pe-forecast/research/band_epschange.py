#!/usr/bin/env python3
"""README §22.4：EPS 變化越大，區間要不要越寬？（走動式樣本外）

    python3 research/band_epschange.py > results/band_epschange.txt
    python3 research/band_epschange.py --fit     # 正式版：全部資料挑 δ、重新校準分位數 → results/band_epschange.json（pef/orbit.load_model 會併入）

起因（§22.1）：MU 兩年 EPS ×110，股價的 80% 區間完全沒涵蓋實際。全樣本看，|ln(EPS_a ÷ 今天 EPS)| 越大，股價偏離預測越多：
24 個月 80% 區間的涵蓋率從 82%（|g| < 0.25）掉到 75%（|g| > 1）。
做法：正式版區間 ＝ 預測 × exp(波動^0.7 × 分位數)；多乘 exp(δ × min(|g|, 2))（|g|＝你給的 EPS 和今天差多少，ln）。
走動式：每年 Y 只用目標日在 Y 年以前的誤差校準分位數、挑 δ（區間分數最低），再看 Y 年起點的涵蓋率（依 |g| 分組）與區間分數。
資料：results/orbit_predictions.csv.gz（S&P 500，走動式「原始成長a」：EPS＝實際），兩端 EPS 都 > 0 的列。
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from pef import cond, orbit                              # noqa: E402

RES = os.path.join(HERE, "results")
A = 0.2
DELTAS = (0.0, 0.05, 0.1, 0.15, 0.2)
BINS = [0, 0.25, 0.5, 1.0, 5]
LABS = ["|g|<0.25", "0.25–0.5", "0.5–1", "|g|>1"]


def iscore(y, lo, hi):
    return (hi - lo) + (2 / A) * np.maximum(lo - y, 0) + (2 / A) * np.maximum(y - hi, 0)


Q = (0.1, 0.25, 0.75, 0.9)
LEVELS = (50, 60, 70, 80, 90)       # §27：可選的涵蓋水準
CUTOFF = pd.Timestamp("2025-09-30")


def fit():
    """正式版：2015 起、目標日 ≤ 2025-09-30 的走動式誤差（和 orbit_fit.py 同一批），用「原始成長a」挑 δ（區間分數最低），
    再對每個用到 EPS 的寫法重新校準 10／25／75／90% 分位數（除以 波動^α × exp(δ × min(|g|, 2))、置中）。"""
    m = json.load(open(os.path.join(RES, "orbit_model.json")))
    p = pd.read_csv(os.path.join(RES, "orbit_predictions.csv.gz"), parse_dates=["month"])
    out = dict(note="README §22.4：EPS 變化越大區間越寬；sc ×＝ exp(δ × min(|ln(EPS_a ÷ 今天 EPS)|, 2))，只用在有 EPS 的寫法",
               delta={}, q={}, check={})
    for h in (6, 12, 24):
        a_ = m["h"][str(h)]["pair"][0]
        z = p[(p["month"] >= "2015-01-01") & p[f"y{h}"].notna() & (p["month"] + pd.DateOffset(months=h) <= CUTOFF)].copy()
        vmed = float(z["vol36"].median())
        base = np.clip(z["vol36"].where(np.isfinite(z["vol36"]), vmed), *cond.VOL_CLIP) ** m["alpha"]
        g = np.log(z[f"eps_f{a_}"] / z["eps0"]).where((z[f"eps_f{a_}"] > 0) & (z["eps0"] > 0)).abs().clip(upper=2)
        e = z[f"y{h}"] - z[f"p{h}_原始成長a"]
        ok = e.notna() & g.notna()
        best = None
        for d_ in DELTAS:
            sc = base[ok] * np.exp(d_ * g[ok])
            u = e[ok] / sc
            u = u - u.median()
            q = np.quantile(u, [A / 2, 1 - A / 2])
            isc = float(np.mean(iscore(u.to_numpy(), q[0], q[1]) * sc.to_numpy()))
            best = (isc, d_) if best is None or isc < best[0] else best
        dl = best[1]
        out["delta"][str(h)] = dl
        out["q"][str(h)] = {}
        out.setdefault("levels", {})[str(h)] = {}
        for spec in m["h"][str(h)]["bands"]:
            if spec == "軌道":                             # 軌道（沒有 EPS，不放寬）：只補各水準的分位數，q 保留 orbit_fit.py 的
                ee = z[f"y{h}"].where(z[f"eps_f{a_}"] > 0)
                k = ee.notna()
                u = ee[k] / base[k]
                u = u - u.median()
                out["levels"][str(h)][spec] = {str(L): [float(v) for v in np.quantile(u, [(1 - L / 100) / 2, 1 - (1 - L / 100) / 2])] for L in LEVELS}
                continue
            if f"p{h}_{spec}" not in z:
                continue
            ee = z[f"y{h}"] - z[f"p{h}_{spec}"]
            k = ee.notna() & g.notna()
            u = ee[k] / (base[k] * np.exp(dl * g[k]))
            u = u - u.median()
            out["q"][str(h)][spec] = [float(v) for v in np.quantile(u, Q)]
            # §27：50／60／70／80／90% 的等尾區間（同一批 u；80 ＝ q 的 [10, 90]、50 ＝ [25, 75]）
            out["levels"][str(h)][spec] = {str(L): [float(v) for v in np.quantile(u, [(1 - L / 100) / 2, 1 - (1 - L / 100) / 2])] for L in LEVELS}
        print(f"{h} 個月：δ＝{dl:g}（區間分數 {best[0]:.4f}）；重新校準 {len(out['q'][str(h)])} 個寫法（各水準 {len(out['levels'][str(h)])} 個）")
    json.dump(out, open(os.path.join(RES, "band_epschange.json"), "w"), ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", action="store_true")
    if ap.parse_args().fit:
        return fit()
    m = orbit.load_model()
    p = pd.read_csv(os.path.join(RES, "orbit_predictions.csv.gz"), parse_dates=["month"])
    rows, picks_all = [], {}
    for h in (6, 12, 24):
        z = p[p[f"y{h}"].notna() & p[f"p{h}_原始成長a"].notna() & (p["month"] + pd.DateOffset(months=h) <= pd.Timestamp("2025-09-30"))].copy()
        g = np.log(z[f"eps_f{h}"] / z["eps0"]).where((z[f"eps_f{h}"] > 0) & (z["eps0"] > 0))
        z = z[g.notna()]
        z["ag"] = g[g.notna()].abs().clip(upper=2)
        e = z[f"y{h}"] - z[f"p{h}_原始成長a"]
        base = np.clip(z["vol36"].fillna(z["vol36"].median()), *cond.VOL_CLIP) ** m["alpha"]
        z["bin"] = pd.cut(z["ag"], BINS, labels=LABS, include_lowest=True)
        for dl in DELTAS + ("走動式挑 δ",):
            res, picks = [], []
            for Y in sorted({mm.year for mm in z["month"]}):
                cal = (z["month"] + pd.DateOffset(months=h)) < pd.Timestamp(f"{Y}-01-01")
                tst = z["month"].dt.year == Y
                if cal.sum() < 3000 or tst.sum() < 300:
                    continue
                best = None
                for d_ in (DELTAS if dl == "走動式挑 δ" else (dl,)):
                    sc = base[cal] * np.exp(d_ * z.loc[cal, "ag"])
                    u = e[cal] / sc
                    u = u - u.median()
                    q = np.quantile(u, [A / 2, 1 - A / 2])
                    isc = float(np.mean(iscore(u.to_numpy(), q[0], q[1]) * sc.to_numpy()))
                    if best is None or isc < best[0]:
                        best = (isc, d_, q)
                _, d_, q = best
                picks.append(d_)
                st = base[tst] * np.exp(d_ * z.loc[tst, "ag"])
                lo, hi = q[0] * st, q[1] * st
                res.append(pd.DataFrame({"in": (e[tst] >= lo) & (e[tst] <= hi), "is": iscore(e[tst].to_numpy(), lo.to_numpy(), hi.to_numpy()),
                                         "bin": z.loc[tst, "bin"], "late": z.loc[tst, "month"] >= "2022-01-01"}))
            rr = pd.concat(res)
            cb = rr.groupby("bin", observed=True)["in"].mean()
            r = dict(h=h, δ=dl, n=len(rr), 涵蓋=float(rr["in"].mean()), 區間分數=float(rr["is"].mean()),
                     **{f"涵蓋 {k}": float(cb.get(k, np.nan)) for k in LABS},
                     各組和80差平均=float(np.mean(np.abs(cb - 0.8))), 區間分數_2022後=float(rr.loc[rr["late"], "is"].mean()))
            if dl == "走動式挑 δ":
                r["挑到的δ"] = "、".join(f"{v:g}" for v in picks)
                picks_all[h] = picks
            rows.append(r)
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print("== 走動式 80% 區間（δ＝0 是正式版）：依 |g| 分組的涵蓋率、區間分數（越低越好）")
    print(t.round(4).to_string(index=False))
    t.to_csv(os.path.join(RES, "band_epschange_scores.csv"), index=False, float_format="%.6f")


if __name__ == "__main__":
    main()
