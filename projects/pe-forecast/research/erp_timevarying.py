#!/usr/bin/env python3
"""README §20.4：股權風險溢酬要不要隨估值水位變？（固定 5% vs 依估值調整，走動式樣本外）

    python3 research/erp_timevarying.py > results/erp_timevarying.txt

邏輯：軌道＝10 年期＋風險溢酬。如果市場很貴（盈餘殖利率低），未來報酬通常較低；很便宜時較高（Campbell & Shiller 1988；
但 Goyal & Welch 2008 發現多數預測變數在樣本外輸給歷史平均）。這裡用最長的資料直接檢驗。
資料：Shiller S&P 500（projects/avi-v5/data/ext/shiller_sp500.csv：月均價、12 個月盈餘與股利、CPI、10 年期；盈餘到 2023-06）。
目標：未來 h 個月（12、24）S&P 500 的總報酬（含股利）減去起點的 10 年期殖利率（年化）＝實際的風險溢酬。
候選（起點當月就知道的）：
  固定 5%（正式版）｜歷史平均（只用當時以前的資料，擴張視窗）｜
  盈餘殖利率 E/P｜CAPE 殖利率 1/PE10｜E/P − 實質利率（10 年期 − 過去 12 個月 CPI 年增）｜1/PE10 − 實質利率｜股利殖利率
  每個候選：ERP_t ＝ a ＋ b × 訊號_t，每年 1 月只用「目標日已到」的資料重估（擴張視窗，1900 年起）。
評分：樣本外中位 |誤差| 與 R²（相對於固定 5%），期間 1950–2023、1990–2023、2010–2023。
注意：12 個月重疊的月資料高度相關，有效樣本約「年數」而不是「月數」。
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = os.path.join(os.path.dirname(os.path.dirname(HERE)), "projects", "avi-v5", "data", "ext", "shiller_sp500.csv")

d = pd.read_csv(SH, parse_dates=["Date"]).set_index("Date")
d = d.replace(0.0, np.nan)
d = d[d.index >= "1880-01-01"]
P, D, E, CPI, Y = d["SP500"], d["Dividend"], d["Earnings"], d["Consumer Price Index"], d["Long Interest Rate"] / 100
infl = np.log(CPI / CPI.shift(12))
sig = pd.DataFrame({
    "盈餘殖利率 E/P": E / P,
    "CAPE 殖利率 1/PE10": 1 / d["PE10"],
    "E/P − 實質利率": E / P - (Y - infl),
    "1/PE10 − 實質利率": 1 / d["PE10"] - (Y - infl),
    "股利殖利率": D / P,
})


def target(h):
    """未來 h 個月的年化總報酬（價格＋股利，月均價近似）減起點 10 年期。"""
    tot = np.log(P.shift(-h) / P) + (D / P).rolling(h).mean().shift(-h) * h / 12
    return (tot * 12 / h - Y).rename("ex")


def walk(h, start_eval=1950):
    y = target(h)
    rows = []
    for Y0 in range(start_eval, 2024):
        cut = pd.Timestamp(f"{Y0}-01-01")
        tr_mask = (y.index + pd.DateOffset(months=h) < cut) & (y.index >= "1900-01-01")
        te = y[(y.index >= cut) & (y.index < cut + pd.DateOffset(years=1))].dropna()
        if te.empty:
            continue
        r = pd.DataFrame({"ex": te})
        r["固定 5%"] = 0.05
        r["歷史平均"] = float(y[tr_mask].mean())
        for c in sig:
            s = sig[c]
            z = pd.concat([y[tr_mask], s[tr_mask]], axis=1).dropna()
            if len(z) < 240:
                continue
            b = np.polyfit(z.iloc[:, 1], z.iloc[:, 0], 1)
            r[c] = b[1] + b[0] * s.reindex(te.index)
            r[c + "_b"] = b[0]
        rows.append(r)
    return pd.concat(rows)


def score(r, lo, hi):
    z = r[(r.index >= lo) & (r.index <= hi)]
    base = z["ex"] - z["固定 5%"]
    out = {}
    for c in ["固定 5%", "歷史平均"] + list(sig):
        if c not in z:
            continue
        e = (z["ex"] - z[c]).dropna()
        out[c] = dict(中位誤差=float(np.median(np.abs(e))), R2對固定5=float(1 - (e ** 2).sum() / (base.loc[e.index] ** 2).sum()), n=len(e))
    return out


print(__doc__.strip().splitlines()[0])
print(f"資料：{d.index.min():%Y-%m}～{d.index.max():%Y-%m}；盈餘到 {E.dropna().index.max():%Y-%m}；10 年期到 {Y.dropna().index.max():%Y-%m}")
for h in (12, 24):
    y = target(h)
    print(f"\n== {h} 個月：實際風險溢酬（年化）1900–2023 平均 {y['1900':'2023'].mean():+.1%}、中位 {y['1900':'2023'].median():+.1%}；"
          f"1950–2023 平均 {y['1950':'2023'].mean():+.1%}；1990–2023 平均 {y['1990':'2023'].mean():+.1%}")
    r = walk(h)
    for per, lo, hi in (("1950–2023", "1950-01-01", "2023-12-31"), ("1990–2023", "1990-01-01", "2023-12-31"), ("2010–2023", "2010-01-01", "2023-12-31")):
        sc = score(r, lo, hi)
        print(f"  樣本外 {per}（{list(sc.values())[0]['n']} 個月）：" + "；".join(f"{k} {v['中位誤差']:.3f}（R² {v['R2對固定5']:+.2f}）" for k, v in sc.items()))
    last = r.index.max()
    print("  最後一年的斜率（ERP 每變 1 單位訊號）：" + "；".join(f"{c} {r.loc[last, c + '_b'].iloc[-1] if isinstance(r.loc[last, c + '_b'], pd.Series) else r.loc[last, c + '_b']:+.2f}"
                                                 for c in sig if c + "_b" in r))
cur = sig.dropna().iloc[-1]
print(f"\n訊號最後一個有值的月份（{sig.dropna().index.max():%Y-%m}）：" + "；".join(f"{k} {v:.2%}" for k, v in cur.items()))
