#!/usr/bin/env python3
"""BTC＋ETH 趨勢跟隨回測（研究報告：topics/business/2026-10-28-crypto-trend-following-research.md）。

規則（日線，台北 08:00 收盤後計算，隔天執行；現貨、不加槓桿、不做空）：
  1. 每個幣 7 個趨勢訊號取平均（0～1）：收盤 > 100/150/200 日均線、60/90/180 日漲跌 > 0、唐奇安 20 日突破／10 日跌破。
  2. 每個幣的部位 ＝ 50% × 訊號 × min(1, 目標波動 ÷ 該幣 60 日年化波動)。預設目標 40%：BTC 波動 60% 時、訊號全滿，部位約 33%。
  3. 任何一個幣的目標權重和現在差 > 5 個百分點才調整；成本每單位換手 0.1%。
  注意：不要改成「用組合過去 60 天的實際波動去縮放到 15%」——空手一段時間後估出來的波動接近 0，
  重新進場會直接滿倉，實際承擔的風險遠高於標稱；真的壓在組合波動 15% 時樣本外只剩年化 ~10%（見研究報告 §3）。

用法：python3 projects/crypto-f3/trend_backtest.py [--target 0.40] [--chart out.png] [--csv dir]
資料：Yahoo Finance 日線（BTC-USD、ETH-USD）。只用 Python 標準庫＋pandas／numpy（畫圖才需要 matplotlib）。
"""
import argparse, json, time, urllib.request
import numpy as np
import pandas as pd

COINS = ("BTC", "ETH")


def fetch(sym, csv_dir=None):
    if csv_dir:
        return pd.read_csv(f"{csv_dir}/{sym}.csv", parse_dates=["t"]).set_index("t").close
    u = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}-USD"
         f"?period1=1410000000&period2={int(time.time())}&interval=1d")
    r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}),
                                          timeout=30).read())["chart"]["result"][0]
    s = pd.Series(r["indicators"]["quote"][0]["close"],
                  index=pd.to_datetime(r["timestamp"], unit="s").normalize()).dropna()
    return s[~s.index.duplicated(keep="last")]


def ensemble(c):
    """7 個趨勢訊號的平均，0＝全部看空、1＝全部看多；不滿 200 天的資料不給訊號。"""
    sigs = [(c > c.rolling(n).mean()).astype(float) for n in (100, 150, 200)]
    sigs += [(c / c.shift(n) > 1).astype(float) for n in (60, 90, 180)]
    hi, lo = c.rolling(20).max().shift(1), c.rolling(10).min().shift(1)
    d = pd.Series(np.nan, index=c.index)
    d[c > hi], d[c < lo] = 1, 0
    sigs.append(d.ffill().fillna(0))
    s = sum(sigs) / len(sigs)
    s[c.rolling(200).count() < 200] = np.nan
    return s


def weights(P, target=0.40, cap=0.5, lb=60, band=0.05):
    R = P.pct_change()
    S = pd.DataFrame({t: ensemble(P[t]) for t in P})
    vol = R.rolling(lb).std() * np.sqrt(365)
    w = (cap * S * np.minimum(1, target / vol)).fillna(0)
    cur, out = w.iloc[0].copy(), []
    for _, row in w.iterrows():          # 權重變動 > band 才調整
        if (row - cur).abs().max() > band:
            cur = row.copy()
        out.append(cur.values)
    return pd.DataFrame(out, index=w.index, columns=w.columns), S


def backtest(P, w, start="2015-06-01", cost=0.001):
    R = P.pct_change().loc[start:].fillna(0)
    w = w.loc[start:]
    held = w.shift(1).fillna(0)          # 今天收盤決定，明天的報酬才算
    turn = (w - w.shift(1).fillna(0)).abs().sum(axis=1)
    return (1 + (held * R).sum(axis=1) - turn * cost).cumprod()


def stats(e):
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    return (e.iloc[-1] ** (1 / yrs) - 1) * 100, ((e / e.cummax()) - 1).min() * 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=float, default=0.40, help="單幣年化波動目標（0.40＝40%%）")
    ap.add_argument("--chart", help="輸出淨值圖 PNG")
    ap.add_argument("--csv", help="改用本機 CSV（欄位 t,close；檔名 BTC.csv、ETH.csv）")
    a = ap.parse_args()
    raw = {t: fetch(t, a.csv) for t in COINS}
    days = pd.date_range(min(s.index[0] for s in raw.values()), max(s.index[-1] for s in raw.values()), freq="D")
    P = pd.DataFrame({t: s.reindex(days).ffill() for t, s in raw.items()})
    w, S = weights(P, a.target)
    e = backtest(P, w)
    print(f"BTC＋ETH 趨勢跟隨，單幣波動目標 {a.target:.0%}（年化／最大回撤）")
    for lab, s0, s1 in (("全期 2015-06 起", "2015-06-01", None), ("樣本內 2015-06～2020", "2015-06-01", "2020-12-31"),
                        ("樣本外 2021 起", "2021-01-01", None), ("2022 起", "2022-01-01", None)):
        x = e.loc[s0:s1]
        c, d = stats(x / x.iloc[0])
        print(f"  {lab:<20} {c:6.1f}% / {d:6.1f}%")
    yr = {y: (e[e.index.year == y].iloc[-1] / e[e.index < e[e.index.year == y].index[0]].iloc[-1] - 1) * 100
          for y in range(2016, e.index[-1].year + 1)}
    print("  各年：" + "  ".join(f"{y} {v:+.0f}%" for y, v in yr.items()))
    print(f"  平均曝險 {w.loc['2015-06-01':].sum(axis=1).mean():.0%}；"
          f"最新（{w.index[-1].date()}）訊號 " + "、".join(f"{t} {S[t].iloc[-1]:.2f}" for t in COINS)
          + "；目標權重 " + "、".join(f"{t} {w[t].iloc[-1]:.1%}" for t in COINS))
    if a.chart:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        x = e.loc["2021-01-01":]
        b = P["BTC"].loc[x.index]
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(x / x.iloc[0], label=f"趨勢跟隨（單幣波動目標 {a.target:.0%}）", color="#2a6fdb", lw=1.8)
        ax.plot(b / b.iloc[0], label="BTC 買進持有", color="#999", lw=1)
        ax.set_yscale("log")
        ax.set_title("樣本外 2021 起（對數座標，起點＝1）")
        ax.legend()
        ax.grid(alpha=.3)
        fig.tight_layout()
        fig.savefig(a.chart, dpi=130)
        print("圖：", a.chart)


if __name__ == "__main__":
    main()
