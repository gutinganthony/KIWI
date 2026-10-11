#!/usr/bin/env python3
"""README §19.3：股價對利率的反應會不會隨通膨環境變號？（S&P 500 指數，1990 起）

    python3 research/rate_regime_check.py > results/rate_regime.txt

市場偏離軌道 M_t ＝ ln(S&P 500_{t+12} ÷ S&P 500_t) − (10 年期_t + 5% − 2%)（股利殖利率用 2% 近似：只影響水準、不影響相關與斜率）。
看 M_t 和「未來 12 個月 10 年期殖利率變化」（完全預知的利率看法）的關係，依 CPI 年增率是否 > 3% 分組；
再看事前可知的線索（預期升降息＝2 年期 − 聯邦基金利率、期限利差、過去 12 個月 10 年期變化）在兩種環境下的相關。
股價：Yahoo ^GSPC 月線；利率：data/rates_monthly.csv（FRED）；CPI：data/cpi_us_monthly.csv。
"""
import json
import os
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = json.load(urllib.request.urlopen(urllib.request.Request(
    "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=40y&interval=1mo", headers={"User-Agent": "Mozilla/5.0"}), timeout=60))
r = raw["chart"]["result"][0]
px = pd.Series(r["indicators"]["quote"][0]["close"], index=pd.to_datetime(r["timestamp"], unit="s")).dropna()
px.index = px.index.normalize() + pd.offsets.MonthEnd(0)
px = px.groupby(level=0).last()
rt = pd.read_csv(os.path.join(HERE, "data", "rates_monthly.csv"), parse_dates=["month_end"]).set_index("month_end")
cpi = pd.read_csv(os.path.join(HERE, "data", "cpi_us_monthly.csv"), parse_dates=["Date"]).set_index("Date")["Index"]
cpi.index = cpi.index + pd.offsets.MonthEnd(0)
d = pd.DataFrame({"px": px}).join(rt, how="inner")
d["cpi_yoy"] = (cpi / cpi.shift(12) - 1).reindex(d.index) * 100
d["M"] = np.log(d["px"].shift(-12) / d["px"]) - (d["DGS10"] / 100 + 0.05 - 0.02)
d["d10_fwd"] = d["DGS10"].shift(-12) - d["DGS10"]
d["d10_past"] = d["DGS10"] - d["DGS10"].shift(12)
d = d[d.index >= "1990-01-01"].dropna(subset=["M", "d10_fwd", "cpi_yoy"])
print(__doc__.strip().splitlines()[0])
print(f"樣本：{d.index.min():%Y-%m}～{d.index.max():%Y-%m}，{len(d)} 個月（12 個月重疊，獨立的大約 {len(d) // 12} 段）")
print("\n1. 完全預知利率時：M ~ 未來 12 個月 10 年期變化（百分點）")
for lab, m in (("全部", d.index == d.index), ("CPI 年增 ≤ 3%", d["cpi_yoy"] <= 3), ("CPI 年增 > 3%", d["cpi_yoy"] > 3)):
    q = d[m]
    b = np.polyfit(q["d10_fwd"], q["M"], 1)
    print(f"  {lab:<12} n={len(q):3d}  斜率 {b[0]:+.3f}（升 1 個百分點 → 股價相對軌道 {np.exp(b[0]) - 1:+.1%}）  相關 {q['M'].corr(q['d10_fwd']):+.3f}")
print("\n   依年代：")
for a, b_ in (("1990", "1999"), ("2000", "2009"), ("2010", "2019"), ("2020", "2026")):
    q = d[(d.index >= f"{a}-01-01") & (d.index <= f"{b_}-12-31")]
    bb = np.polyfit(q["d10_fwd"], q["M"], 1)
    print(f"  {a}s n={len(q):3d}  斜率 {bb[0]:+.3f}  相關 {q['M'].corr(q['d10_fwd']):+.3f}  CPI 年增中位 {q['cpi_yoy'].median():.1f}%")
print("\n2. 事前可知的利率線索 vs M 的相關（預期升降息從 1990 起；聯邦基金利率是月平均）")
for c in ("exp_cut_2y", "slope", "d10_past", "DFII10"):
    row = []
    for lab, m in (("全部", d.index == d.index), ("CPI≤3%", d["cpi_yoy"] <= 3), ("CPI>3%", d["cpi_yoy"] > 3)):
        q = d[m].dropna(subset=[c])
        row.append(f"{lab} {q['M'].corr(q[c]):+.3f}（n={len(q)}）")
    print(f"  {c:<11} " + "；".join(row))
last = d.dropna(subset=["cpi_yoy"]).iloc[-1] if len(d) else None
cur = pd.DataFrame({"cpi": (cpi / cpi.shift(12) - 1) * 100}).dropna().iloc[-1]
print(f"\n目前（{cur.name:%Y-%m}）CPI 年增 {cur['cpi']:.1f}%；最新 10 年期 {rt['DGS10'].dropna().iloc[-1]:.2f}%")
