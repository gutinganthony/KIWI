#!/usr/bin/env python3
"""示範「從今天股價反推市場隱含的長期成長」（研究用，不是投資建議）。

    python3 research/reverse_demo.py

1. 週期股 vs 其他：12 個月股價（相對軌道）對 EPS 變化的反應（results/aeg_lab_rows.csv.gz，S&P 500 2012–2022）。
2. 反推：今天股價（results/now_all.csv，2026-09-24）＋「假設的」近年 EPS 成長 → 市場隱含高成長要再維持幾年
   （兩階段：前 n 年 EPS 以 g 成長、派發 1 − g/ROE；之後 4% 成長、ROE 20%）。成長率是假設的情境，不是共識預估。
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "results")

x = pd.read_csv(os.path.join(RES, "aeg_lab_rows.csv.gz"))
x["y"] = np.log(x["px_f12"] / x["orbit"].where(x["orbit"] > 0))
x["g1"] = np.log(x["eps1"] / x["eps0"])
x["g2"] = np.log(x["eps2"].where(x["eps2"] > 0) / x["eps1"])
print("== 1. ln(實際 ÷ 軌道) ＝ a ＋ b1·ln(EPS₁₂/EPS₀) ＋ b2·ln(EPS₂₄/EPS₁₂)：EPS 多 10% → 股價多約 b×10%")
for g, y in x.dropna(subset=["y", "g1", "g2"]).groupby("grp"):
    y = y[(y["g1"].abs() < 2) & (y["g2"].abs() < 2)]
    X = np.column_stack([np.ones(len(y)), y["g1"], y["g2"]])
    b = np.linalg.lstsq(X, y["y"], rcond=None)[0]
    print(f"  {g:18s} n={len(y):6,}  這一年 EPS b1 {b[1]:+.3f}  再下一年 EPS b2 {b[2]:+.3f}")

R_ERP, GN, ROE_N = 0.05, 0.04, 0.20


def fwd_pe(g, n, roe, r, horizon=400):
    T = n + horizon
    gg = np.where(np.arange(T) < n, g, GN)
    eps = np.cumprod(np.r_[1.0, 1 + gg[:-1]])
    pay = np.where(np.arange(T) < n, max(0.0, 1 - g / roe), 1 - GN / ROE_N)
    return float(np.sum(pay * eps * (1 + r) ** -np.arange(1, T + 1)))      # 價格 ÷ 下一年 EPS


def implied_n(pe_fwd, g, roe, r):
    pes = [fwd_pe(g, n, roe, r) for n in range(0, 31)]
    if pe_fwd < pes[0]:
        return "<0（比成熟期還便宜）"
    if pe_fwd > pes[-1]:
        return ">30"
    k = int(np.searchsorted(pes, pe_fwd))
    lo, hi = pes[k - 1], pes[k]
    return f"{k - 1 + (pe_fwd - lo) / (hi - lo):.1f}"


d = pd.read_csv(os.path.join(RES, "now_all.csv"))
print("\n== 2. 今天股價隱含：若 EPS 每年成長 g，這種高成長要再維持幾年才說得通（成熟期 4% 成長、ROE 20%）")
for t, roe in (("MSFT", 0.35), ("AAPL", 0.60), ("NVDA", 0.60), ("AVGO", 0.35), ("MU", 0.25), ("AMD", 0.20)):
    row = d[d["ticker"] == t]
    if row.empty:
        continue
    row = row.iloc[0]
    r = float(row["y10"]) + R_ERP
    cells = []
    for g in (0.10, 0.20, 0.30):
        pe_fwd = row["px"] / (row["eps0"] * (1 + g))           # 假設下一年 EPS＝目前最近四季 ×（1＋g）
        cells.append(f"g={g:.0%}：forward 本益比 {pe_fwd:5.1f} → {implied_n(pe_fwd, g, roe, r)} 年")
    print(f"  {t:5s} 股價 {row['px']:8.2f}  最近四季 EPS {row['eps0']:6.2f}（trailing 本益比 {row['px'] / row['eps0']:5.1f}）  " + "；".join(cells))
