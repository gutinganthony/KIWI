#!/usr/bin/env python3
"""本益比軌道模型的正式版：用 2025-09-30 以前已揭曉的全部配對估 β、校準區間，寫成 results/orbit_model.json（README §16）。

    python3 orbit_fit.py --cache <lab_orbit.py 用的暫存目錄>      # 先跑過 lab_orbit.py（要它的快取與 orbit_predictions.csv.gz）

β：每個預測距離（6、12、24 個月）× 寫法 × 公司類型，用 lab_orbit.py 同一個估法（同月份去平均、Huber、沒有截距）。
區間：lab_orbit.py 走動式回測的樣本外誤差（每年 1 月只用當時已揭曉的資料估 β 再預測），除以 波動^0.7、置中、取分位數。
  另外用「2021 年底以前的誤差」校準、2022 以後檢查涵蓋率，看區間是否誠實。
虧損：目標日 EPS ≤ 0 的列，軌道誤差比獲利的列寬多少倍（loss_widen），pef/orbit.py 用它放寬區間。
輸出：results/orbit_model.json、results/orbit_fit.txt
"""
import argparse
import io
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab_orbit as lo                                   # noqa: E402
from pef import cond                                     # noqa: E402

RES = lo.RES
CUTOFF = pd.Timestamp("2025-09-30")
ALPHA = cond.BAND_ALPHA
Q = (0.1, 0.25, 0.75, 0.9)
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def scale(vol, vmed):
    return np.clip(np.where(np.isfinite(vol), vol, vmed), *cond.VOL_CLIP) ** ALPHA


def band(e, vol, vmed):
    u = e / scale(vol, vmed)
    u = u - np.median(u)
    return [float(v) for v in np.quantile(u, Q)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    x = pd.read_pickle(os.path.join(a.cache, "orbit_x2.pkl"))
    for k in lo.EPS_H:
        x[f"s{k}"] = (x[f"g{k}"] - x[f"e{k}"]).clip(-2, 2)
    x = x[x["month"] >= "2012-01-01"].copy()
    p = pd.read_csv(os.path.join(RES, "orbit_predictions.csv.gz"), parse_dates=["month"])
    model = dict(version="orbit-1", fit_cutoff=str(CUTOFF.date()), erp=cond.ERP, alpha=ALPHA, vol_clip=list(cond.VOL_CLIP),
                 quantiles=list(Q), groups=lo.GROUPS, h={}, backtest={}, loss_widen={})
    say(f"正式版 β：用目標日 ≤ {CUTOFF.date()} 的全部配對（S&P 500，起點 2012 起）")
    rows = []
    for h in lo.HS:
        hm = dict(pair=list(lo.PAIR[h]), beta={}, cols={}, n={}, bands={})
        for name, (cols, mat) in lo.specs_for(h).items():
            tr = x[lo.tgt_end(x, max(h, mat)) <= CUTOFF]
            hm["cols"][name] = cols
            hm["beta"][name], hm["n"][name] = {}, {}
            for g in lo.GNAME:
                d = tr[tr["grp"] == g]
                b = lo.beta_fit(d, f"y{h}", cols)
                hm["beta"][name][g] = [float(v) for v in b]
                hm["n"][name][g] = int(d.dropna(subset=[f"y{h}"] + cols).shape[0])
                rows.append(dict(h=h, 寫法=name, 組別=lo.GNAME[g], 線索="、".join(cols), β="、".join(f"{v:+.3f}" for v in b),
                                 n=hm["n"][name][g]))

        # 區間：走動式樣本外誤差（實際 − 預測，ln）
        z = p[(p["month"] >= "2015-01-01") & p[f"y{h}"].notna()].copy()
        z = z[lo.tgt_end(z, h) <= CUTOFF]
        vmed = float(z["vol36"].median())
        a_ = lo.PAIR[h][0]
        prof = z[f"eps_f{a_}"] > 0
        errs = {"軌道": z[f"y{h}"].where(prof)}
        for name in lo.specs_for(h):
            errs[name] = z[f"y{h}"] - z[f"p{h}_{name}"]
        cov = []
        for name, e in errs.items():
            ok = e.notna().to_numpy()
            if ok.sum() < 500:
                continue
            ev, vv, mm = e.to_numpy(float)[ok], z["vol36"].to_numpy(float)[ok], z["month"].to_numpy()[ok]
            hm["bands"][name] = dict(q=band(ev, vv, vmed), vol_median=vmed, n=int(ok.sum()))
            early = lo.tgt_end(pd.DataFrame({"month": mm}), h) <= pd.Timestamp("2021-12-31")
            late = pd.Series(mm) >= pd.Timestamp("2022-01-01")
            if early.sum() > 300 and late.sum() > 300:
                qe = band(ev[early.to_numpy()], vv[early.to_numpy()], vmed)
                u = ev[late.to_numpy()] / scale(vv[late.to_numpy()], vmed)
                u = u - np.median(u)                    # 只檢查寬度：檢查期用自己的中位數置中（大盤偏差另外報，見「檢查期偏差中位」）
                cov.append(dict(寫法=name, n_校準=int(early.sum()), n_檢查=int(late.sum()),
                                涵蓋50=float(np.mean((u >= qe[1]) & (u <= qe[2]))),
                                涵蓋80=float(np.mean((u >= qe[0]) & (u <= qe[3]))),
                                檢查期偏差中位=float(np.median(ev[late.to_numpy()]))))
        # 虧損放寬：目標日 EPS ≤ 0 的軌道誤差寬度 ÷ 獲利的寬度（10–90% 分位距）
        ee = z[f"y{h}"].to_numpy(float) / scale(z["vol36"].to_numpy(float), vmed)
        lossm = (z[f"eps_f{a_}"] <= 0).to_numpy()
        w = lambda v: np.quantile(v, 0.9) - np.quantile(v, 0.1)
        model["loss_widen"][str(h)] = float(w(ee[lossm]) / w(ee[prof.to_numpy()])) if lossm.sum() > 100 else 1.6
        hm["band_coverage"] = cov
        model["h"][str(h)] = hm
        say(f"\n== {h} 個月：區間（2021 以前校準 → 2022 以後檢查；目標 50%／80%）；目標日虧損放寬 ×{model['loss_widen'][str(h)]:.2f}"
            f"（虧損 {int(lossm.sum()):,} 列）")
        say(pd.DataFrame(cov).round(3).to_string(index=False))

    say("\n== 落在實際 ±10%／±20% 內的比例（預測起點 2022 以後；同一批列：a、b 時點 EPS 都有）")
    hit = []
    for h in lo.HS:
        a_ = lo.PAIR[h][0]
        d = p[(p["month"] >= "2022-01-01") & p[f"y{h}"].notna() & p[f"p{h}_原始成長ab"].notna() & p[f"p{h}_預期b＋修正ab"].notna()]
        for gl, dd in (("全部", d), ("科技", d[d["grp"] != "other"])):
            r = dict(h=h, 組別=gl, n=len(dd))
            errs = {"本益比不變": dd[f"g{a_}"] - (dd[f"y{h}"] + dd["orbit_lr"] * h / 12), "軌道": -dd[f"y{h}"],
                    "＋你的EPS(ab)": dd[f"p{h}_原始成長ab"] - dd[f"y{h}"], "＋預期代理＋你的EPS": dd[f"p{h}_預期b＋修正ab"] - dd[f"y{h}"]}
            for k, e in errs.items():
                r[f"{k}_±10%"] = float(np.mean(np.abs(np.exp(e) - 1) <= 0.1))
                r[f"{k}_±20%"] = float(np.mean(np.abs(np.exp(e) - 1) <= 0.2))
            hit.append(r)
    say(pd.DataFrame(hit).round(3).to_string(index=False))
    model["hit_rates"] = hit

    say("\n== 正式版 β（EPS 多 10% → 股價約 β×10%；順序同「線索」）")
    say(pd.DataFrame(rows).to_string(index=False))

    sc = pd.read_csv(os.path.join(RES, "orbit_scores.csv"))
    for h in lo.HS:
        s = sc[(sc["h"] == h) & sc["期間"].str.startswith("保留期") & (sc["樣本"] == "也有 b 時點 EPS")].set_index("組別")
        bt = {}
        for g in ("全部", "科技"):
            if g in s.index:
                bt[f"軌道（{g}）"] = float(s.loc[g, "orbit"])
                bt[f"＋你的 EPS（{g}）"] = float(s.loc[g, "原始成長ab"])
                bt[f"＋預期（代理）＋你的 EPS（{g}）"] = float(s.loc[g, "預期b＋修正ab"])
        model["backtest"][str(h)] = bt
    rp = os.path.join(RES, "orbit_recent_scores.csv")
    if os.path.exists(rp):
        r = pd.read_csv(rp)
        model["recent"] = {str(h): {g: dict(n=int(d["n"].iloc[0]), 軌道=float(d["軌道"].iloc[0]),
                                            加你的EPS=float(d["軌道＋原始成長a"].iloc[0]),
                                            市場偏離軌道中位=float(d["市場偏離軌道中位"].iloc[0]))
                                    for g, d in r[r["h"] == h].groupby("組別")} for h in sorted(r["h"].unique())}
    json.dump(model, open(os.path.join(RES, "orbit_model.json"), "w"), ensure_ascii=False, indent=1)
    open(os.path.join(RES, "orbit_fit.txt"), "w").write(buf.getvalue())
    say(f"\n寫入 results/orbit_model.json")


if __name__ == "__main__":
    main()
