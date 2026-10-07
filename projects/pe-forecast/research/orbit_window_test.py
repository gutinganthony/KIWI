#!/usr/bin/env python3
"""README §16.3 第 4 點：β 只用最近幾年（3／5／8 年滾動窗）估，會不會比 2012 起全部（擴張窗）準？評 2022 以後的起點。

    python3 research/orbit_window_test.py <lab_orbit.py 暫存目錄>/orbit_x2.pkl > results/orbit_window.txt
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
import lab_orbit as lo
x = pd.read_pickle(sys.argv[1])
for k in lo.EPS_H:
    x[f"s{k}"] = (x[f"g{k}"] - x[f"e{k}"]).clip(-2, 2)
x = x[x["month"] >= "2012-01-01"].copy()
rows = []
for h in (6, 12, 24):
    specs = lo.specs_for(h)
    for win in (None, 8, 5, 3):
        for name in ("原始成長ab", "預期b＋修正ab"):
            cols, mat = specs[name]
            pred = pd.Series(np.nan, index=x.index)
            for Y in range(2022, 2026):
                cutoff = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
                te = x[(x["month_end"] > cutoff) & (x["month_end"] <= cutoff + pd.DateOffset(months=12))]
                tr = x[lo.tgt_end(x, max(h, mat)) <= cutoff]
                if win:
                    tr = tr[tr["month"] >= cutoff - pd.DateOffset(years=win)]
                for g in lo.GNAME:
                    b = lo.beta_fit(tr[tr["grp"] == g], f"y{h}", cols)
                    t = te[te["grp"] == g]
                    if np.all(np.isfinite(b)):
                        pred.loc[t.index] = np.column_stack([t[c] for c in cols]) @ b
            e = (pred - x[f"y{h}"])
            d = x.assign(e=e)[x["month"] >= "2022-01-01"].dropna(subset=["e", f"y{h}"])
            for gl, dd in (("全部", d), ("科技", d[d["grp"] != "other"]), ("半導體類", d[d["grp"] == "cyclical"]), ("軟體網路", d[d["grp"] == "growth"])):
                rows.append(dict(h=h, 窗=("擴張(2012起)" if not win else f"最近{win}年"), 寫法=name, 組別=gl, n=len(dd),
                                 誤差=float(np.median(np.abs(dd["e"]))), 軌道=float(np.median(np.abs(dd[f"y{h}"])))))
r = pd.DataFrame(rows)
print(r.pivot_table(index=["h", "寫法", "組別"], columns="窗", values="誤差").round(4).to_string())
print(r.groupby(["h","寫法","組別"])[["n","軌道"]].first().round(4).to_string())
