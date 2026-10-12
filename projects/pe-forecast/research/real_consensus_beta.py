#!/usr/bin/env python3
"""README §20.6：用真正的歷史共識（I/B/E/S，OSAP）重估「市場已預期的成長」與「和共識的差距」的 β，和正式版（代理預期估的）比樣本外準度。

    python3 research/real_consensus_beta.py --cache <lab_orbit 暫存目錄> > results/real_consensus_beta.txt

用 consensus_monthly.py 的對答案程式（--selftest 同一份模擬面板：S&P 500 每月、本財年共識、12 個月後的 GAAP 最近四季與股價），
寫法＝「預期＋修正a」：調整＝β_預期 × ln(共識_a ÷ 今天 EPS) ＋ β_差距 × ln(實際_a ÷ 共識_a)（實際＝目標日已公布的最近四季，上限）。
比較（走動式，每年 1 月只用目標日已到的列重估，2016–2024）：
  代理預期 β（正式版的估法，每年 1 月重估：results/orbit_beta.csv，公平的樣本外）｜正式版 β（全期估的，對它有利，僅供參考）｜
  真共識 β（每年重估）｜不調整（只用軌道）
評分：中位 |實際偏離軌道 − 預測的調整|（含大盤）與扣掉每月中位後（只看個股）。
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import consensus_monthly as CM                          # noqa: E402
import lab_eps_correction as L                          # noqa: E402
from pef import orbit                                   # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cache", required=True)
a = ap.parse_args()
d = L.build(a.cache)
d = d[(d["month"] >= "2012-01-01") & ~d["near_split"]]
p = pd.DataFrame({"symbol": d["ticker"], "asof": d["month"] + pd.offsets.MonthEnd(0), "px": d["px"], "ttm": d["eps0"],
                  "mrq": d["period_end"], "fy0_end": d["fy1"], "c0": d["feps"], "c1": np.nan, "fy1_end": pd.NaT, "cf": np.nan, "y10": d["y10"]})
p["ym"] = p["asof"].dt.strftime("%Y-%m")
sector = d.drop_duplicates("ticker").set_index("ticker")["sector"].to_dict()
bc = CM.beta_check(p, sector=sector)
bc["x_exp"], bc["x_gap"] = bc["x_exp"].clip(-2, 2), bc["x_gap"].clip(-2, 2)
model = orbit.load_model()
prod = model["h"]["12"]["beta"]["預期＋修正a"]
bc["p_prod"] = [prod[g][0] * xe + prod[g][1] * xg for g, xe, xg in zip(bc["grp"], bc["x_exp"], bc["x_gap"])]
wb = pd.read_csv(os.path.join(HERE, "results", "orbit_beta.csv"))
wb = wb[(wb["h"] == 12) & (wb["方法"] == "預期＋修正a")].set_index(["年", "組別"])[["b0", "b1"]]
bc["p_walk"] = [wb.loc[(m.year, orbit.GNAME[g]), "b0"] * xe + wb.loc[(m.year, orbit.GNAME[g]), "b1"] * xg
                if (m.year, orbit.GNAME[g]) in wb.index else np.nan for m, g, xe, xg in zip(bc["month"], bc["grp"], bc["x_exp"], bc["x_gap"])]
bc["p_real"] = np.nan
yrs = []
for Y in range(2016, 2025):
    cut = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
    tr = bc[bc["month"] + pd.DateOffset(months=12) <= cut]
    te = bc[(bc["month"] > cut) & (bc["month"] <= cut + pd.DateOffset(months=12))]
    fb = CM.fit_beta(tr)
    for g, gg in te.groupby("grp"):
        b = fb.get(g, (None, 0))[0]
        b = b if b is not None else fb["全部"][0]
        if b is not None:
            bc.loc[gg.index, "p_real"] = gg["x_exp"] * b[0] + gg["x_gap"] * b[1]
            yrs.append(dict(年=Y, 組別=orbit.GNAME[g], β_預期=b[0], β_差距=b[1], n_train=len(tr[tr["grp"] == g])))
ev = bc[bc["p_real"].notna() & bc["p_walk"].notna()].copy()
print(f"模擬面板 {len(bc):,} 組（12 個月後有答案），樣本外評分 {len(ev):,} 組（起點 2016–2024）")
rows = []
for per, lo, hi in (("2016–2021", "2016-01-01", "2021-12-31"), ("2022 以後", "2022-01-01", "2026-12-31"), ("全期", "2016-01-01", "2026-12-31")):
    for gn in ["全部"] + list(orbit.GNAME):
        g = ev[(ev["month"] >= lo) & (ev["month"] <= hi)]
        if gn != "全部":
            g = g[g["grp"] == gn]
        if len(g) < 100:
            continue
        r = dict(期間=per, 組別=orbit.GNAME.get(gn, gn), n=len(g))
        for nm, col in (("只用軌道", None), ("代理 β（走動式）", "p_walk"), ("真共識 β", "p_real"), ("正式版 β（參考）", "p_prod")):
            pr = 0.0 if col is None else g[col]
            e = g["y"] - pr
            r[nm] = float(np.median(np.abs(e)))
            r[nm + "｜扣大盤"] = float(np.median(np.abs(e - e.groupby(g["month"]).transform("median"))))
        rows.append(r)
t = pd.DataFrame(rows)
print("\n== 中位 |誤差|（EPS_a＝實際，上限；扣大盤＝扣掉每月中位，只看個股）")
print(t.round(4).to_string(index=False))
print("\n== 真共識 β（每年重估，最後兩年）vs 正式版（代理預期）")
yt = pd.DataFrame(yrs)
print(yt[yt["年"] >= 2023].round(3).to_string(index=False))
print("正式版：" + "；".join(f"{orbit.GNAME[g]} {v[0]:+.3f}、{v[1]:+.3f}" for g, v in prod.items()))
