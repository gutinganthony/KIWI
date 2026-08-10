#!/usr/bin/env python3
"""美銀牛熊指標(BBI)賣訊後的 SPY 前瞻報酬檢定。

BBI 是 BofA 專有指標、無公開序列；訊號日取自媒體報導（見
topics/business/2026-08-06-bofa-bull-bear-9-7-signal-verification.md §4 的版本矛盾）。
本腳本計算「已報導訊號日之後 SPY 的實際走勢」並對照無條件基準。
拿到新訊號日就加進 sigs 清單重跑。用法：python3 scripts/bbi_signal_check.py
"""
import pandas as pd, numpy as np
def load(p):
    d=pd.read_csv(p); c=[x for x in d.columns if x.lower()=='date'][0]
    d[c]=pd.to_datetime(d[c]); d=d.set_index(c).sort_index()
    return (d['Adj Close'] if 'Adj Close' in d else d['Close']).astype(float)
a=load('data/backtest/SPY.csv'); b=load('data/ext/SPY.csv')
spy=pd.concat([a[a.index<b.index[0]],b]).sort_index()
print(f"SPY {spy.index[0].date()} → {spy.index[-1].date()}  n={len(spy)}\n")

# 已報導的 BBI 賣訊日期（媒體轉述，非 BofA 一手序列）
sigs=[("2025-10-01","~8.9 峰"),("2025-12-19","7.9→8.5 觸發"),
      ("2026-01-15","9.2–9.4"),("2026-02-20","9.6 高點"),("2026-06-15","連三週賣訊")]
def fwd(d0,wk):
    i=spy.index.searchsorted(pd.Timestamp(d0))
    j=i+wk*5
    if i>=len(spy) or j>=len(spy): return None,None
    seg=spy.iloc[i:j+1]
    return spy.iloc[j]/spy.iloc[i]-1, seg.min()/spy.iloc[i]-1
print(f"{'訊號日':<12}{'備註':<14}{'2週':>16}{'4週':>16}{'8週':>16}{'12週':>16}")
print(f"{'':<26}{'報酬/最大回落':>16}"*4)
print("-"*90)
for d,note in sigs:
    row=f"{d:<12}{note:<14}"
    for wk in (2,4,8,12):
        r,dd=fwd(d,wk)
        row += f"{'  n/a':>16}" if r is None else f"{r*100:>+8.1f}%/{dd*100:>+6.1f}%"
    print(row)

# 無條件基準（同期間所有交易日）
print("\n無條件基準（2006 起全樣本，隨機日）：")
s=spy[spy.index>='2006-01-01']
for wk in (2,4,8,12):
    h=wk*5; r=(s.shift(-h)/s-1).dropna()
    dds=[]
    for i in range(0,len(s)-h,5):
        seg=s.iloc[i:i+h+1]; dds.append(seg.min()/s.iloc[i]-1)
    print(f"  {wk:>2}週：平均報酬 {r.mean()*100:+.1f}%　中位 {r.median()*100:+.1f}%　"
          f"下跌機率 {(r<0).mean()*100:.0f}%　平均最大回落 {np.mean(dds)*100:+.1f}%")

# 2025-12-19 起至今（賣訊持續期間）市場走勢
i=spy.index.searchsorted(pd.Timestamp("2025-12-19"))
print(f"\n★ 賣訊持續期檢定：2025-12-19（{spy.iloc[i]:.2f}）→ {spy.index[-1].date()}（{spy.iloc[-1]:.2f}）"
      f" = {(spy.iloc[-1]/spy.iloc[i]-1)*100:+.1f}%")
seg=spy.iloc[i:]
print(f"  期間最大回落 {(seg.min()/spy.iloc[i]-1)*100:+.1f}%（{seg.idxmin().date()}）"
      f"、期間高點 {(seg.max()/spy.iloc[i]-1)*100:+.1f}%（{seg.idxmax().date()}）")
