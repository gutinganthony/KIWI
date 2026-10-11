#!/usr/bin/env python3
"""README §19.3：利率情境的係數從哪來、能不能用（驗算）。

    python3 research/rate_sensitivity_check.py [--gspc <^GSPC 月線 JSON>] > results/rate_sensitivity.txt
另存 results/rate_sensitivity.json：利率情境用的係數（pef/orbit.py 的 rate_slope、網頁試算器）。

問題 1：每升 1 個百分點，股價相對軌道變多少？和預測距離（6／12／24 個月）有沒有關係？
  個股：results/orbit_predictions.csv.gz 的模型誤差（實際偏離軌道 − 模型用 EPS 成長算的偏離，原始成長a）每月取中位數，
  對「同一段期間 10 年期殖利率的變化」回歸；分 2012–2021、2022 以後。
  指數：^GSPC，股利殖利率用 2% 近似（只影響截距）。
問題 2：折現率邏輯說本益比高（存續期間長）的股票對利率更敏感——資料是否如此？
  每月把股票依本益比分三組，看「高本益比組 − 低本益比組」的模型誤差中位數差，對 10 年期變化回歸。
問題 3（驗算）：理論上的折現率效果有多大？戈登模型 P＝D÷(r−g)：g 不變時 ∂lnP/∂r ＝ −1÷(r−g) ＝ −本益比÷配息率。
  拿實測斜率和它比，看看「利率上升時成長率／風險溢酬一起變」抵銷了多少。
"""
import argparse
import json
import os
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--gspc", default=None)
a = ap.parse_args()

rt = pd.read_csv(os.path.join(HERE, "data", "rates_monthly.csv"), parse_dates=["month_end"]).set_index("month_end")["DGS10"]
p = pd.read_csv(os.path.join(HERE, "results", "orbit_predictions.csv.gz"), parse_dates=["month"])
p["month_end"] = p["month"] + pd.offsets.MonthEnd(0)
p["lpe"] = np.where(p["eps0"] > 0, np.log(p["px"] / p["eps0"]), np.nan)
PER = (("2012–2021", "2012-01-01", "2021-12-31"), ("2022 以後", "2022-01-01", "2030-12-31"))


def fit(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 12:
        return np.nan, np.nan, int(m.sum())
    b = np.polyfit(x[m], y[m], 1)
    return b[0], float(np.corrcoef(x[m], y[m])[0, 1]), int(m.sum())


print(__doc__.strip().splitlines()[0])
print("\n== 1. 每升 1 個百分點（10 年期，h 個月內的變化），股價相對軌道的變化（斜率；個股＝每月模型誤差的中位數）")
rows = []
for h in (6, 12, 24):
    d10 = (rt.shift(-h) - rt).rename("d10")
    q = p[p[f"y{h}"].notna() & p[f"p{h}_原始成長a"].notna()].copy()
    q["res"] = q[f"y{h}"] - q[f"p{h}_原始成長a"]
    q["tech"] = q["grp"].isin(["cyclical", "growth", "tech_other"])
    q["pe_t"] = q.groupby("month")["lpe"].transform(lambda s: pd.qcut(s, 3, labels=False, duplicates="drop") if s.notna().sum() > 30 else np.nan)
    mk = q.groupby("month_end").agg(all=("res", "median")).join(q[q["tech"]].groupby("month_end")["res"].median().rename("tech"))
    hi, lo = q[q["pe_t"] == 2].groupby("month_end")["res"].median(), q[q["pe_t"] == 0].groupby("month_end")["res"].median()
    mk["hi_lo"] = hi - lo
    mk = mk.join(d10)
    for per, s, e in PER:
        z = mk[(mk.index >= s) & (mk.index <= e)]
        for col, lab in (("all", "全部（中位股票）"), ("tech", "科技"), ("hi_lo", "高本益比 − 低本益比")):
            b, c, n = fit(z["d10"].to_numpy(float), z[col].to_numpy(float))
            rows.append(dict(h=h, 期間=per, 對象=lab, 月數=n, 斜率=b, 相關=c))
gs = None
try:
    raw = json.load(open(a.gspc)) if a.gspc else json.load(urllib.request.urlopen(urllib.request.Request(
        "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=40y&interval=1mo", headers={"User-Agent": "Mozilla/5.0"}), timeout=60))
    r = raw["chart"]["result"][0]
    gs = pd.Series(r["indicators"]["quote"][0]["close"], index=pd.to_datetime(r["timestamp"], unit="s")).dropna()
    gs.index = gs.index.normalize() + pd.offsets.MonthEnd(0)
    gs = gs.groupby(level=0).last()
except Exception as ex:                                   # noqa: BLE001
    print(f"（^GSPC 抓不到：{ex}）")
if gs is not None:
    g = pd.DataFrame({"px": gs}).join(rt, how="inner")
    for h in (6, 12, 24):
        M = np.log(g["px"].shift(-h) / g["px"]) - (g["DGS10"] / 100 + 0.05 - 0.02) * h / 12
        d10 = g["DGS10"].shift(-h) - g["DGS10"]
        for per, s, e in PER + (("1990–2011", "1990-01-01", "2011-12-31"),):
            m = (g.index >= s) & (g.index <= e)
            b, c, n = fit(d10[m].to_numpy(float), M[m].to_numpy(float))
            rows.append(dict(h=h, 期間=per, 對象="S&P 500 指數", 月數=n, 斜率=b, 相關=c))
t = pd.DataFrame(rows)
print(t.pivot_table(index=["對象", "期間"], columns="h", values="斜率").round(3).to_string())
print("\n相關係數：")
print(t.pivot_table(index=["對象", "期間"], columns="h", values="相關").round(2).to_string())
print("\n讀法：同一列 6／12／24 個月的斜率接近 → 「每個百分點的影響」和預測距離無關，情境用 斜率 × 你預期的變化，不乘 h/12。")

sens = {}
for key, per, lab in (("2022", "2022 以後", "2022 以後（通膨期：利率上升＝風險溢酬上升，股價跌）"),
                      ("2012", "2012–2021", "2012–2021（低通膨期：利率上升常伴隨景氣變好，大盤幾乎不受影響）")):
    pick = lambda who, h: float(t[(t["對象"] == who) & (t["期間"] == per) & (t["h"] == h)]["斜率"].iloc[0])
    sens[key] = dict(label=lab, h={str(h): dict(mkt=round(pick("全部（中位股票）", h), 4), dur=round(pick("高本益比 − 低本益比", h), 4))
                                   for h in (6, 12, 24)})
json.dump(dict(note="每升 1 個百分點（10 年期，到目標日的變化）股價相對軌道的 ln 變化：中位股票 mkt ＋ 本益比位置的傾斜 dur×(百分位−0.5)÷(2/3)"
                    "（百分位截在 1/6～5/6；dur＝高本益比三分之一 − 低本益比三分之一）。來源：research/rate_sensitivity_check.py",
               regimes=sens), open(os.path.join(HERE, "results", "rate_sensitivity.json"), "w"), ensure_ascii=False, indent=1)

print("\n== 2. 本益比高的股票對利率比較敏感嗎？（上表「高本益比 − 低本益比」列：負＝利率升時高本益比股票相對跌更多）")
print(t[t["對象"] == "高本益比 − 低本益比"][["h", "期間", "月數", "斜率", "相關"]].round(3).to_string(index=False))

print("\n== 3. 驗算：理論上的折現率效果 vs 實測")
last = p[p["month"] == p["month"].max()]
pe_med = float(np.exp(last["lpe"].median()))
dy_med = float(last["dy"].median())
payout = dy_med * pe_med
print(f"  最新月份 S&P 500 中位本益比 {pe_med:.1f}、股利殖利率 {dy_med:.2%} → 配息率約 {payout:.0%}")
print(f"  戈登模型（g 不變）：∂lnP/∂r ＝ −1/(r−g) ＝ −本益比 ÷ 配息率 ≈ −{pe_med / max(payout, 0.05):.0f}（每升 1 個百分點跌 {pe_med / max(payout, 0.05):.0f}%）")
print(f"  連配息率都不看、只用本益比當存續期間：每升 1 個百分點跌約 {pe_med:.0f}%")
for per, s, e in PER:
    v = t[(t["對象"] == "全部（中位股票）") & (t["期間"] == per) & (t["h"] == 12)]["斜率"]
    if len(v):
        print(f"  實測 {per}（12 個月）：每升 1 個百分點 {np.exp(float(v.iloc[0])) - 1:+.1%}")
print("  → 實測只有理論值的一小部分、而且會變號：利率上升常伴隨經濟變好（g 上升，2012–2021）或通膨（風險溢酬上升，2022 以後），"
      "\n    把折現率效果抵銷或放大。只改折現率（r）不改成長（g）的寫法會嚴重高估利率的影響。")
