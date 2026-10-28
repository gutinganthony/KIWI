#!/usr/bin/env python3
"""BTC＋ETH 趨勢跟隨回測（研究報告：topics/business/2026-10-28-crypto-trend-following-research.md）。

規則（日線，UTC 00:00＝台北 08:00 收盤後計算，用收盤價成交；現貨、不加槓桿、不做空）：
  1. 每個幣 7 個趨勢訊號取平均（0～1）：收盤 > 100/150/200 日均線、60/90/180 日漲跌 > 0、唐奇安 20 日突破／10 日跌破。
  2. 每個幣的目標部位 ＝ 50% × 訊號 × min(1, 目標波動 ÷ 該幣 60 日年化波動)。預設目標 40%：BTC 波動 60% 時、訊號全滿，部位約 33%。
  3. 實際持倉會隨價格漂移；任何一個幣的「目標部位」和「現在實際部位」差 > 5 個百分點才調整，調整時兩個幣一起調回目標。
     成本每單位換手 0.1%。紙上交易機器人 trend_paper.py 用的是同一個 step()，所以重播結果和回測一致。
  注意：不要改成「用組合過去 60 天的實際波動去縮放到 15%」——空手一段時間後估出來的波動接近 0，
  重新進場會直接滿倉，實際承擔的風險遠高於標稱；真的壓在組合波動 15% 時樣本外只剩年化 ~10%（見研究報告 §3）。

用法：python3 projects/crypto-f3/trend_backtest.py [--targets 0.40,0.45,0.50] [--source yahoo|okx] [--csv dir] [--chart out.png]
資料：Yahoo 日線（2014 起，預設）或 OKX 1Dutc 日線（2018 起，和紙上交易機器人同源）。
"""
import argparse, json, sys, time, urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

COINS = ("BTC", "ETH")
CAP, LB, BAND, COST = 0.5, 60, 0.05, 0.001


def fetch(sym, csv_dir=None, source="yahoo"):
    """收盤價序列（索引＝UTC 日期）。"""
    if csv_dir:
        return pd.read_csv(f"{csv_dir}/{sym}.csv", parse_dates=["t"]).set_index("t").close
    if source == "okx":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import f3_backtest as bt
        rows = bt.fetch_okx(sym, "1d", int(pd.Timestamp("2017-01-01").timestamp() * 1000))
        s = pd.Series({pd.Timestamp(k, unit="ms"): v[3] for k, v in rows.items()}).sort_index()
        return s
    u = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}-USD"
         f"?period1=1410000000&period2={int(time.time())}&interval=1d")
    r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}),
                                          timeout=30).read())["chart"]["result"][0]
    s = pd.Series(r["indicators"]["quote"][0]["close"],
                  index=pd.to_datetime(r["timestamp"], unit="s").normalize()).dropna()
    return s[~s.index.duplicated(keep="last")]


def prices(csv_dir=None, source="yahoo"):
    raw = {t: fetch(t, csv_dir, source) for t in COINS}
    days = pd.date_range(min(s.index[0] for s in raw.values()), max(s.index[-1] for s in raw.values()), freq="D")
    return pd.DataFrame({t: s.reindex(days).ffill() for t, s in raw.items()})


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


def targets(P, target=0.40, cap=CAP, lb=LB):
    """每天收盤後的目標部位（佔總資金比例）與訊號分數。"""
    S = pd.DataFrame({t: ensemble(P[t]) for t in P})
    vol = P.pct_change().rolling(lb).std() * np.sqrt(365)
    return (cap * S * np.minimum(1, target / vol)).fillna(0), S, vol


def step(units, cash, px, tgt, band=BAND, cost=COST):
    """一天一次：用收盤價 px 估值；任一幣實際部位和目標差 > band 就全部調回目標。
    units／px／tgt 是 {幣: 數字}。回傳 (units, cash, 換手金額)。"""
    value = cash + sum(units[c] * px[c] for c in units)
    if value <= 0:
        return units, cash, 0.0
    cur = {c: units[c] * px[c] / value for c in units}
    if max(abs(tgt[c] - cur[c]) for c in units) <= band:
        return units, cash, 0.0
    turn = sum(abs(tgt[c] - cur[c]) for c in units) * value
    fee = turn * cost
    new = {c: tgt[c] * (value - fee) / px[c] if px[c] > 0 else 0.0 for c in units}
    cash = value - fee - sum(new[c] * px[c] for c in units)
    return new, cash, turn


def simulate(P, T, start="2015-06-01", band=BAND, cost=COST):
    """回傳每日淨值（起點 1）、每日實際部位、調整次數。"""
    idx = P.loc[start:].index
    units, cash = {c: 0.0 for c in P}, 1.0
    eq, wt, n = [], [], 0
    for d in idx:
        px = P.loc[d].fillna(0).to_dict()          # 還沒上市的幣：價格 0、目標 0
        units, cash, turn = step(units, cash, px, T.loc[d].to_dict(), band, cost)
        n += turn > 0
        v = cash + sum(units[c] * px[c] for c in units)
        eq.append(v)
        wt.append([units[c] * px[c] / v for c in P])
    return pd.Series(eq, index=idx), pd.DataFrame(wt, index=idx, columns=P.columns), n


def stats(e):
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    return (e.iloc[-1] ** (1 / yrs) - 1) * 100, ((e / e.cummax()) - 1).min() * 100


def period(e, s0, s1=None):
    x = e.loc[s0:s1]
    return stats(x / x.iloc[0])


def yearly(e):
    out = {}
    for y in range(e.index[0].year + 1, e.index[-1].year + 1):
        cur, prev = e[e.index.year == y], e[e.index.year < y]
        out[y] = (cur.iloc[-1] / prev.iloc[-1] - 1) * 100
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="0.40", help="單幣年化波動目標，逗號分隔（0.40＝40%%）")
    ap.add_argument("--source", default="yahoo", choices=("yahoo", "okx"))
    ap.add_argument("--start", default=None, help="回測起點（預設 Yahoo 2015-06-01、OKX 資料第 260 天）")
    ap.add_argument("--chart", help="輸出淨值圖 PNG")
    ap.add_argument("--csv", help="改用本機 CSV（欄位 t,close；檔名 BTC.csv、ETH.csv）")
    a = ap.parse_args()
    P = prices(a.csv, a.source)
    start = a.start or ("2015-06-01" if a.source == "yahoo" and not a.csv else str(P.index[260].date()))
    curves = {}
    for tg in (float(x) for x in a.targets.split(",")):
        T, S, _ = targets(P, tg)
        e, w, n = simulate(P, T, start)
        curves[tg] = e
        yrs = (e.index[-1] - e.index[0]).days / 365.25
        print(f"\nBTC＋ETH 趨勢跟隨，單幣波動目標 {tg:.0%}（{a.source}，{start} 起；年化／最大回撤）")
        for lab, s0, s1 in (("全期", start, None), ("樣本內 ～2020", start, "2020-12-31"),
                            ("樣本外 2021 起", "2021-01-01", None), ("2022 起", "2022-01-01", None)):
            if e.loc[s0:s1].size > 30:
                c, d = period(e, s0, s1)
                print(f"  {lab:<14} {c:6.1f}% / {d:6.1f}%")
        print("  各年：" + "  ".join(f"{y} {v:+.0f}%" for y, v in yearly(e).items()))
        print(f"  平均曝險 {w.sum(axis=1).mean():.0%}、最大 {w.sum(axis=1).max():.0%}；一年調整約 {n / yrs:.0f} 次；"
              f"最新（{P.index[-1].date()}）訊號 " + "、".join(f"{t} {S[t].iloc[-1]:.2f}" for t in COINS)
              + "；目標部位 " + "、".join(f"{t} {T[t].iloc[-1]:.1%}" for t in COINS))
    if a.chart:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for f in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",):      # 中文字型（有就用）
            if Path(f).exists():
                font_manager.fontManager.addfont(f)
                plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
        fig, ax = plt.subplots(figsize=(10, 4.5))
        for tg, e in curves.items():
            x = e.loc["2021-01-01":]
            ax.plot(x / x.iloc[0], label=f"波動目標 {tg:.0%}", lw=1.4)
        b = P["BTC"].loc["2021-01-01":]
        ax.plot(b / b.iloc[0], label="BTC 買進持有", color="#999", lw=1)
        ax.set_yscale("log")
        ax.legend()
        ax.grid(alpha=.3)
        fig.tight_layout()
        fig.savefig(a.chart, dpi=130)
        print("圖：", a.chart)


if __name__ == "__main__":
    main()
