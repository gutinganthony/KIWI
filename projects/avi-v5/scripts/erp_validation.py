#!/usr/bin/env python3
"""
erp_validation.py — MRI 估值層（ECY / 隱含 ERP）的完整驗證

背景：MRI 設計綱要原本提案用「成長調整後的隱含 ERP」取代 Shiller 的
Excess CAPE Yield：

    高登模型  P/E = 1/(r−g)  ⟹  r = E/P + g
    隱含 ERP = 1/CAPE + g − 實質10Y殖利率

理論上這比 ECY（= 1/CAPE − 實質10Y，完全沒有 g 項）更完整，也正好處理
「不同時代成長率不同」的問題。本腳本用 Shiller 1871-2026 完整資料集實測
這個提案是否成立。

【結論：提案被推翻】
  - 前提成立：g 確實隨時代大幅變動（跨時代中位數落差 4.98pp）
  - 但 ECY + g 反而變差（相關 0.460 vs 純 ECY 0.594）
  - 根因：盈餘成長強烈均值回歸（過去30年 g → 未來10年 g 相關 −0.49），
    用 trailing g 代表未來 g，方向是反的 —— 典型的外推謬誤
  - 且加 g 的窗口越短越糟，呈單調關係，要到 g50 才勉強打平純 ECY

【另一個關鍵發現：ECY 不能做短期預警】
  1年 0.227 / 3年 0.351 / 5年 0.441 / 10年 0.582
  → 它量測的是「摔下去會多痛」，不是「什麼時候摔」。
    但尾端風險差異是真的：最貴 20% 未來一年跌超過 10% 的機率 25.9%，
    最便宜 20% 只有 7.9%（3.3 倍差距），對決定部位大小有實用價值。

用法：python scripts/erp_validation.py
"""
import os
import urllib.request
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(BASE, "data", "ext")
SHILLER = os.path.join(EXT, "shiller_sp500.csv")
SRC = "https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv"


def load_shiller():
    """Shiller 1871- 完整資料集。本地沒有就抓一次並快取。"""
    if not os.path.exists(SHILLER):
        os.makedirs(EXT, exist_ok=True)
        print(f"下載 Shiller 資料集 → {SHILLER}")
        urllib.request.urlretrieve(SRC, SHILLER)
    df = pd.read_csv(SHILLER)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index().rename(columns={
        "Consumer Price Index": "cpi", "Long Interest Rate": "nom10y",
        "Real Price": "rp", "Real Dividend": "rd", "Real Earnings": "re", "PE10": "cape",
    })
    # 最新幾列的衍生欄位為 0（尚未填），視為缺值
    for c in ["cpi", "nom10y", "rp", "rd", "re", "cape"]:
        df[c] = df[c].replace(0.0, np.nan)
    return df


def build(df):
    """建立實質總報酬指數與各項組件。"""
    tr = pd.Series(index=df.index, dtype=float)
    tr.iloc[0] = 100.0
    rp, rd = df["rp"], df["rd"]
    for i in range(1, len(df)):
        p0, p1, d1 = rp.iloc[i-1], rp.iloc[i], rd.iloc[i]
        if np.isnan(p0) or np.isnan(p1) or p0 <= 0:
            tr.iloc[i] = tr.iloc[i-1]
            continue
        tr.iloc[i] = tr.iloc[i-1] * (p1 + ((d1/12.0) if not np.isnan(d1) else 0.0)) / p0
    df["tr"] = tr
    infl10 = (df["cpi"] / df["cpi"].shift(120)) ** (1/10) - 1
    df["real10y"] = df["nom10y"]/100.0 - infl10
    df["ey"] = 1.0 / df["cape"]
    df["ecy"] = df["ey"] - df["real10y"]
    return df


def fwd_ann_real(df, years):
    n = years * 12
    return (df["tr"].shift(-n) / df["tr"]) ** (1.0/years) - 1.0


def g_trailing(df, years):
    return (df["re"] / df["re"].shift(years*12)) ** (1/years) - 1


def corr(a, b):
    both = pd.concat([a, b], axis=1).dropna()
    return (both.iloc[:, 0].corr(both.iloc[:, 1]), len(both)) if len(both) > 120 else (np.nan, len(both))


ERAS = [
    ("1900s 鐵路/工業",   "1900-01-01", "1929-12-31"),
    ("1930-45 大蕭條戰時", "1930-01-01", "1945-12-31"),
    ("1946-72 戰後嬰兒潮", "1946-01-01", "1972-12-31"),
    ("1973-89 停滯性通膨", "1973-01-01", "1989-12-31"),
    ("1990-99 網路時代",   "1990-01-01", "1999-12-31"),
    ("2000-09 兩次泡沫",   "2000-01-01", "2009-12-31"),
    ("2010-2025 QE/科技",  "2010-01-01", "2025-12-31"),
]


def main():
    df = build(load_shiller())
    ok = df.dropna(subset=["cape", "rp", "re", "nom10y", "cpi"])
    print(f"資料 {df.index[0].date()} → {df.index[-1].date()}；"
          f"完整可用至 {ok.index[-1].date()}\n")
    f10 = fwd_ann_real(df, 10)
    for N in (10, 20, 30, 40, 50):
        df[f"g{N}"] = g_trailing(df, N)

    # ── Q1 前提檢驗 ──
    print("="*78)
    print("Q1. 前提：實質盈餘成長率 g 是否隨時代大幅變動？")
    print("="*78)
    print(f"  {'時代':<22}{'g20 中位數':>12}{'CAPE 中位數':>13}")
    print("  " + "-"*47)
    meds = []
    for nm, a, b in ERAS:
        s, c = df.loc[a:b, "g20"].dropna(), df.loc[a:b, "cape"].dropna()
        if len(s) < 12:
            continue
        meds.append(s.median())
        print(f"  {nm:<22}{s.median()*100:>11.2f}%{c.median():>12.1f}")
    g_all = df["g20"].dropna()
    print("  " + "-"*47)
    print(f"  跨時代中位數落差 {(max(meds)-min(meds))*100:.2f}pp；"
          f"g 標準差 {g_all.std()*100:.2f}pp "
          f"= ECY 標準差的 {g_all.std()/df['ecy'].dropna().std()*100:.0f}%")
    print("  → 前提成立：g 的變異不可忽略\n")

    # ── Q2 加 g 是否有幫助 ──
    print("="*78)
    print("Q2. ECY + g 是否優於純 ECY？（對未來10年實質總報酬）")
    print("="*78)
    print(f"  {'公式':<26}{'相關':>9}{'同段純ECY':>11}   判定")
    print("  " + "-"*56)
    for N in (5, 10, 20, 30, 40, 50):
        s = df["ecy"] + df[f"g{N}"] if f"g{N}" in df else None
        if s is None:
            continue
        both = pd.concat([s, f10], axis=1).dropna()
        if len(both) < 120:
            continue
        r = both.iloc[:, 0].corr(both.iloc[:, 1])
        r0 = df["ecy"].loc[both.index].corr(f10.loc[both.index])
        print(f"  {'ECY + g'+str(N):<26}{r:>9.3f}{r0:>11.3f}   "
              + ("✅ 勝出" if r > r0 else "❌ 不如純 ECY"))
    print("\n  對照（證明只有『會變動的 g』才可能有影響）：")
    both = pd.concat([df["ecy"] + 0.02, f10], axis=1).dropna()
    print(f"    ECY + 固定2%  相關 {both.iloc[:,0].corr(both.iloc[:,1]):.3f}"
          f"  ← 與純 ECY 相同，符合預期")

    # ── Q3 為什麼失敗：均值回歸 ──
    print("\n" + "="*78)
    print("Q3. 失敗根因：trailing g 能不能預測未來的 g？")
    print("="*78)
    g_fut = (df["re"].shift(-120) / df["re"]) ** (1/10) - 1
    for N in (10, 20, 30):
        r, _ = corr(df[f"g{N}"], g_fut)
        print(f"  過去{N}年 g → 未來10年 g   相關 {r:>7.3f}   "
              + ("（負相關＝均值回歸，用它是外推謬誤）" if r < 0 else "（正相關）"))
    print("\n  分組驗證（按過去20年成長分組，看未來10年實質報酬）：")
    d = pd.concat([df["g20"].rename("g"), f10.rename("f")], axis=1).dropna()
    q = d["g"].quantile([1/3, 2/3])
    for nm, sub in [("成長最低 1/3", d[d["g"] <= q[1/3]]),
                    ("中間 1/3", d[(d["g"] > q[1/3]) & (d["g"] < q[2/3])]),
                    ("成長最高 1/3", d[d["g"] >= q[2/3]])]:
        print(f"    {nm:<14} 過去 g 中位 {sub['g'].median()*100:>5.2f}%"
              f"  →  未來10年報酬 {sub['f'].mean()*100:>6.2f}%")
    print("\n  既然是負相關，改成『減去 g』會不會比較好？")
    common = pd.concat([df["ecy"], df["g20"], f10], axis=1).dropna().index
    for nm, s in [("純 ECY", df["ecy"]), ("ECY + g20", df["ecy"]+df["g20"]),
                  ("ECY − 0.5×g20", df["ecy"]-0.5*df["g20"]),
                  ("ECY − 1.0×g20", df["ecy"]-df["g20"])]:
        print(f"    {nm:<16}{s.loc[common].corr(f10.loc[common]):>8.3f}")

    # ── Q4 能不能預警 ──
    print("\n" + "="*78)
    print("Q4.【關鍵】ECY 在不同時間視野的預測力 —— 能不能做預警？")
    print("="*78)
    print(f"  {'視野':<8}{'1/CAPE':>9}{'ECY':>9}{'ECY+g20':>10}   解讀")
    print("  " + "-"*52)
    for yrs in (1, 2, 3, 5, 10):
        f = fwd_ann_real(df, yrs)
        row = [corr(s, f)[0] for s in (df["ey"], df["ecy"], df["ecy"]+df["g20"])]
        note = ("幾乎無用" if abs(row[1]) < .25 else "微弱" if abs(row[1]) < .40
                else "中等" if abs(row[1]) < .55 else "強")
        print(f"  {str(yrs)+'年':<8}{row[0]:>9.3f}{row[1]:>9.3f}{row[2]:>10.3f}   {note}")

    print("\n  但尾端風險的差異是真的（未來1年）：")
    f1 = fwd_ann_real(df, 1)
    d = pd.concat([df["ecy"], f1.rename("f1")], axis=1).dropna()
    q = d["ecy"].quantile([0.2, 0.8])
    print(f"  {'ECY 分組':<20}{'平均報酬':>10}{'跌超過10%的機率':>16}")
    for nm, sub in [("最貴 20%", d[d["ecy"] <= q[0.2]]),
                    ("中間 60%", d[(d["ecy"] > q[0.2]) & (d["ecy"] < q[0.8])]),
                    ("最便宜 20%", d[d["ecy"] >= q[0.8]])]:
        print(f"  {nm:<20}{sub['f1'].mean()*100:>9.1f}%{(sub['f1']<=-0.10).mean()*100:>15.1f}%")
    print(f"\n  → ECY 做不到『擇時預警』，但做得到『量測曝險』：最貴與最便宜之間，")
    print(f"    一年內大跌的機率差 "
          f"{(d[d['ecy']<=q[0.2]]['f1']<=-0.10).mean()/(d[d['ecy']>=q[0.8]]['f1']<=-0.10).mean():.1f} 倍。")

    # ── 現在的位置 ──
    print("\n" + "="*78)
    print("現在的位置")
    print("="*78)
    last = ok.index[-1]
    for nm, v, ser in [("CAPE", df.loc[last, "cape"], df["cape"]),
                       ("ECY", df.loc[last, "ecy"]*100, df["ecy"]*100),
                       ("g20（實質盈餘成長）", df.loc[last, "g20"]*100, df["g20"]*100)]:
        pct = (ser.dropna() < v).mean()*100
        print(f"  {nm:<22}{v:>8.2f}   歷史百分位 {pct:>3.0f}%")
    print(f"  （最新完整資料月份：{last.date()}）")
    print("\n  註：g20 若落在高百分位，按 Q3 的均值回歸結果，那是脆弱訊號而非利多。")


if __name__ == "__main__":
    main()
