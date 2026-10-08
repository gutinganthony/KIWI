#!/usr/bin/env python3
"""
cri_exit_rule_backtest.py — 出場規則 3（CRI≥50 組合總開關）的成本/效益回測

問題：「CRI 突破 50 → 股票盡量出清、尤其降槓桿」這條規則，實際代價是什麼？
資料：SPY(Adj Close) + 既有快取 data/backtest/cri_history_30yr.csv（CRI v2，1994-2020，
      9 個 SPY/VIX 指標；live CRI 另含信用/利率 3 指標，讀數可能不同）。
假設：訊號以當日收盤判定、次一交易日起換倉；現金年化 3%；2× 槓桿以每日 2× SPY
      扣借款成本模擬（未扣槓桿 ETF 管理費，實際更差）。in-sample，無 1987。

用法：python scripts/cri_exit_rule_backtest.py
對應文件：skills/serenity/exit-playbook.md §0 規則 3
"""

import os
import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "backtest")
CASH = 0.03 / 252
CRASHES = ["1997-10-27", "1998-08-31", "2000-04-14", "2001-09-17", "2002-07-19", "2008-09-15",
           "2010-05-06", "2011-08-04", "2015-08-21", "2018-02-05", "2018-12-14", "2020-02-24"]

spy = pd.read_csv(os.path.join(DATA, "SPY.csv"), parse_dates=["Date"]).set_index("Date")["Adj Close"]
cri = pd.read_csv(os.path.join(DATA, "cri_history_30yr.csv"), parse_dates=["date"]).set_index("date")["score"]
df = pd.DataFrame({"p": spy}).join(cri.rename("c"), how="inner").dropna()
df["r"] = df.p.pct_change().fillna(0)
df["ma"] = spy.rolling(200).mean().reindex(df.index)
c, p, m = df.c.values, df.p.values, df.ma.values
calm10 = pd.Series(c < 35).rolling(10).sum().values == 10   # 連續 10 日 CRI<35


def stats(eq):
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    return eq.iloc[-1] ** (1 / yrs) - 1, (eq / eq.cummax() - 1).min()


def sim(exit_fn, reenter_fn, on_w, off_w):
    st, w, trips = True, [], 0
    for i in range(len(df)):
        w.append(on_w if st else off_w)
        if st and exit_fn(i):
            st, trips = False, trips + 1
        elif not st and reenter_fn(i):
            st = True
    w = pd.Series(w, index=df.index).shift(1).fillna(on_w)
    rr = w * df.r - np.clip(w - 1, 0, None) * CASH + np.clip(1 - w, 0, None) * CASH
    cg, dd = stats((1 + rr).cumprod())
    return cg, dd, (w < on_w).mean(), trips


def report(name, res):
    cg, dd, out, trips = res
    print(f"{name:44s} CAGR {cg:6.2%}  MDD {dd:6.1%}  防守時間 {out:4.0%}  觸發 {trips:3d} 次")


print(f"期間 {df.index[0].date()} → {df.index[-1].date()}；CRI≥50 天數占比 {(df.c >= 50).mean():.1%}\n")
report("買進持有 1×", sim(lambda i: False, lambda i: True, 1, 1))
report("買進持有 2×", sim(lambda i: False, lambda i: True, 2, 2))

raw50 = lambda i: c[i] >= 50
gated = lambda i: c[i] >= 50 and p[i] < m[i]
re_raw = lambda i: calm10[i]
re_gated = lambda i: calm10[i] and p[i] > m[i]

print("\n— 原始版：CRI≥50 單獨觸發 —")
report("1× → 全出清", sim(raw50, re_raw, 1, 0))
report("2× → 全出清", sim(raw50, re_raw, 2, 0))
report("2× → 降回 1×（只砍槓桿）", sim(raw50, re_raw, 2, 1))

print("\n— 確認版：CRI≥50 且 S&P<200 日線 —")
report("1× → 全出清", sim(gated, re_gated, 1, 0))
report("2× → 全出清", sim(gated, re_gated, 2, 0))

print("\n— 對照組 —")
report("1× 只看 200 日線", sim(lambda i: p[i] < m[i], lambda i: p[i] > m[i], 1, 0))

first = (df.c >= 50) & (df.c.shift(1) < 50)
fwd = pd.DataFrame({h: (df.p.shift(-h) / df.p - 1)[first] for h in (5, 21, 63)})
print(f"\nCRI 首次上穿 50 共 {first.sum()} 次；之後 SPY 報酬中位數："
      f"1 週 {fwd[5].median():+.1%}／1 月 {fwd[21].median():+.1%}／3 月 {fwd[63].median():+.1%}")
print("（中位數為正＝單用 CRI≥50 常賣在急跌低點，這是加 200 日線確認的理由）\n")

trig = pd.Series([gated(i) for i in range(len(df))], index=df.index)
print("各次重大崩盤 D-0 前後，確認版首次觸發日（±60 交易日窗）：")
for d in CRASHES:
    d0 = df.index[df.index <= pd.Timestamp(d)][-1]
    k = df.index.get_loc(d0)
    win = trig.iloc[max(0, k - 60): k + 61]
    hit = win[win]
    if len(hit):
        lag = df.index.get_loc(hit.index[0]) - k
        print(f"  {d}: 首次觸發 {hit.index[0].date()}（{lag:+d} 交易日）")
    else:
        print(f"  {d}: 窗內未觸發")

# ─── 規則 3 實際採用的兩段式：CRI≥50 先砍槓桿 → 再加 200 日線確認才全出清 ─────────
def two_stage(lev):
    st, w, n1, n2 = 2, [], 0, 0          # 2=正常, 1=已砍槓桿, 0=全出清
    for i in range(len(df)):
        w.append({2: lev, 1: 1.0, 0: 0.0}[st])
        if st > 0 and gated(i):
            n2 += st == 2 or st == 1; st = 0
        elif st == 2 and raw50(i):
            n1 += 1; st = 1
        elif st == 1 and calm10[i]:
            st = 2
        elif st == 0 and re_gated(i):
            st = 2
    w = pd.Series(w, index=df.index).shift(1).fillna(lev)
    rr = w * df.r - np.clip(w - 1, 0, None) * CASH + np.clip(1 - w, 0, None) * CASH
    cg, dd = stats((1 + rr).cumprod())
    return cg, dd, (w < lev).mean(), n1 + n2

print("\n— 規則 3 兩段式（槓桿部位：CRI≥50 降回 1×；確認後全出清）—")
report("2× 兩段式", two_stage(2.0))
