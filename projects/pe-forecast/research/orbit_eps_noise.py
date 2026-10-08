#!/usr/bin/env python3
"""README §16.3「實際用起來多準」：你的 EPS 有誤差時，h 個月後本益比的誤差有多大（預測起點 2022 以後）。

    python3 research/orbit_eps_noise.py > results/orbit_eps_noise.txt

本益比誤差 ＝ ln(預測本益比 ÷ 實際本益比) ＝ 股價誤差 − EPS_a 誤差（股價對 EPS 的反應 β 很小，所以 EPS 錯多少、本益比大約就錯多少）。
EPS 誤差兩種：①實際 EPS × exp(N(0, σ))（a、b 各自獨立）②用 lab_orbit.py 的「市場預期代理」（樹模型的 EPS 成長預測）當你的 EPS。
對照：本益比不變（今天的本益比，不需要 EPS）。β 用 results/orbit_model.json 的「原始成長ab」。
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = pd.read_csv(os.path.join(HERE, "results", "orbit_predictions.csv.gz"), parse_dates=["month"])
m = json.load(open(os.path.join(HERE, "results", "orbit_model.json")))
rng = np.random.default_rng(0)
print(__doc__.strip().splitlines()[0])
print("中位 |ln 本益比誤差|（0.10 ≈ 差 10%）")
for h, (a, b) in {6: (6, 18), 12: (12, 24), 24: (24, 36)}.items():
    d = p[(p["month"] >= "2022-01-01") & p[f"y{h}"].notna() & p[f"p{h}_原始成長ab"].notna() & p[f"e{a}"].notna() & p[f"e{b}"].notna()]
    bt = m["h"][str(h)]["beta"]["原始成長ab"]
    ba, bb = d["grp"].map({g: v[0] for g, v in bt.items()}), d["grp"].map({g: v[1] for g, v in bt.items()})
    base = d[f"p{h}_原始成長ab"] - d[f"y{h}"]
    unch = d[f"g{a}"] - (d[f"y{h}"] + d["orbit_lr"] * h / 12)
    for gl, mask in (("全部", d["grp"].notna()), ("科技", d["grp"] != "other")):
        row = [f"{h:>2} 個月 {gl}（n={int(mask.sum()):,}）：本益比不變 {np.median(np.abs(unch[mask])):.3f}"]
        for sig in (0.0, 0.1, 0.2, 0.3):
            na, nb = rng.normal(0, sig, len(d)), rng.normal(0, sig, len(d))
            row.append(f"EPS 誤差 σ={sig:.1f} → {np.median(np.abs((base + ba * na + bb * nb - na)[mask])):.3f}")
        na, nb = d[f"e{a}"] - d[f"g{a}"], d[f"e{b}"] - d[f"g{b}"]
        row.append(f"代理預測當 EPS（EPS 誤差中位 {np.median(np.abs(na[mask])):.2f}）→ "
                   f"{np.median(np.abs((base + ba * na + bb * nb - na)[mask])):.3f}")
        print("  " + "；".join(row))
