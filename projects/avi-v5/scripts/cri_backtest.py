#!/usr/bin/env python3
"""
cri_backtest.py — CRI 真實數據回測引擎（與 TSI 同方法論）

CRI 衡量 S&P 500 大盤崩盤風險。用真實 SPY(1993-)+VIX(1990-) 數據回測，
評估：各指標預測力、提前天數、假警報率，並找出最佳權重結構。

CRI 12 指標中，9 個只需 SPY+VIX（可回測），3 個需債券/利率（本回測停用）：
  可測：vix_term_structure, garch_vix_gap, breadth_divergence, distribution_days,
        rsi_divergence, ma_distance_reversal, vix_spike, momentum_collapse,
        intraday_selloff
  停用：credit_acceleration, yield_curve_steepening, yield_surge（傳空序列→回傳0）

用法：python scripts/cri_backtest.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from src.cpi import CrashProbabilityIndex

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "backtest")

# ─── 載入真實數據 ────────────────────────────────────────────────────────────

def load_sp500():
    df = pd.read_csv(os.path.join(DATA, "SPY.csv"))
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()
    # CRI 函數需要小寫 'close','volume'
    return pd.DataFrame({
        'close': df['Adj Close'] if 'Adj Close' in df.columns else df['Close'],
        'volume': df['Volume'],
    }).dropna()

def load_vix():
    df = pd.read_csv(os.path.join(DATA, "VIX.csv"))
    df['DATE'] = pd.to_datetime(df['DATE'], format='%m/%d/%Y')
    df = df.set_index('DATE').sort_index()
    return df['CLOSE'].dropna()

print("載入真實歷史數據中...")
sp500 = load_sp500()
vix = load_vix()
empty = pd.Series(dtype=float)
print(f"  SPY: {len(sp500)} 筆  {sp500.index[0].date()} → {sp500.index[-1].date()}")
print(f"  VIX: {len(vix)} 筆  {vix.index[0].date()} → {vix.index[-1].date()}")

spy_close = sp500['close']

# ─── 崩盤事件定義（與 TSI 一致）─────────────────────────────────────────────

def find_crash_events(price, fwd_window=5, threshold=-0.06, min_gap=20):
    fwd_ret = price.shift(-fwd_window) / price - 1
    crash_days = fwd_ret[fwd_ret <= threshold].index.tolist()
    events, last = [], None
    for d in crash_days:
        if last is None or (price.index.get_loc(d) - price.index.get_loc(last)) >= min_gap:
            events.append(d); last = d
    return events

spy_crashes = find_crash_events(spy_close, 5, -0.06, 20)
print(f"\n偵測到 SPY 大盤崩盤事件：{len(spy_crashes)} 次（未來5日跌>6%）")

# ─── 逐日計算 CRI ────────────────────────────────────────────────────────────

def get_win(series, end, n=300):
    s = series[series.index <= end]
    return s.tail(n)

cri = CrashProbabilityIndex()

def compute_cri_on(date):
    try:
        sp_w = sp500[sp500.index <= date].tail(300)
        if len(sp_w) < 210:
            return None
        vix_w = get_win(vix, date, 300)
        if len(vix_w) < 70:
            return None
        result = cri.compute(
            sp500_daily  = sp_w,
            vix_daily    = vix_w,
            vix3m_daily  = None,      # 用 63日MA proxy
            baa_daily    = empty,     # 無 → credit_acceleration 回傳 0
            aaa_daily    = empty,
            treasury_10y = empty,     # 無 → yield 指標回傳 0
            treasury_2y  = empty,
        )
        return result
    except Exception:
        return None

print("\n逐日計算 CRI（1996-2020，這會花一點時間）...")
eval_dates = spy_close.index[(spy_close.index >= '1996-01-01') & (spy_close.index <= '2020-04-01')]

cri_indicators = [
    'vix_term_structure', 'garch_vix_gap', 'breadth_divergence', 'distribution_days',
    'rsi_divergence', 'ma_distance_reversal', 'vix_spike', 'momentum_collapse',
    'intraday_selloff',
    # 停用（恆為0，列出以對照）：
    'credit_acceleration', 'yield_curve_steepening', 'yield_surge',
]

records = []
for i, d in enumerate(eval_dates):
    if i % 800 == 0:
        print(f"  進度 {i}/{len(eval_dates)} ({d.date()})")
    r = compute_cri_on(d)
    if r is None:
        continue
    m = {ind.name: ind.signal for ind in r.indicators}
    records.append({
        'date': d, 'score': r.score,
        **{k: m.get(k, 0) for k in cri_indicators}
    })

cri_df = pd.DataFrame(records).set_index('date')
cri_df.to_csv(os.path.join(DATA, 'cri_history.csv'))
print(f"完成：{len(cri_df)} 個交易日，已存 data/backtest/cri_history.csv")

# ─── ROC-AUC 評估 ────────────────────────────────────────────────────────────

def roc_auc(scores, labels):
    scores = np.asarray(scores, float); labels = np.asarray(labels)
    n_pos = labels.sum(); n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0: return 0.5
    ranks = np.argsort(np.argsort(scores)) + 1
    return (ranks[labels == 1].sum() - n_pos*(n_pos+1)/2) / (n_pos*n_neg)

def fwd_min_return(window):
    out = pd.Series(index=cri_df.index, dtype=float)
    for d in cri_df.index:
        prior = spy_close.index[spy_close.index <= d]
        if len(prior) == 0: continue
        loc = spy_close.index.get_loc(prior[-1])
        if loc + window >= len(spy_close): continue
        out[d] = (spy_close.iloc[loc+1:loc+1+window].min() / spy_close.iloc[loc] - 1) * 100
    return out

horizons = [1, 3, 5, 10]
labels_by_h = {}
for h in horizons:
    fwd = fwd_min_return(h)
    labels_by_h[h] = (fwd <= -5.0).astype(int)[fwd.notna()]

# 只評估「可測」的 9 個指標
testable = cri_indicators[:9]

print(f"\n{'='*78}")
print(f"  各 CRI 指標預測力（ROC-AUC：0.5=亂猜 0.6=有用 0.65+=強）")
print(f"{'='*78}")
print(f"  {'指標':<24} " + "".join(f"{'D'+str(h):>8}" for h in horizons))
print(f"  {'-'*56}")
auc_best = {}
for ind in testable:
    row = []
    for h in horizons:
        lab = labels_by_h[h]
        a = roc_auc(cri_df.loc[lab.index, ind].values, lab.values)
        row.append(a)
    auc_best[ind] = max(row)
    cells = "".join(f"{a:>8.3f}" for a in row)
    mark = " ✅" if max(row) >= 0.60 else (" 🟡" if max(row) >= 0.55 else " ❌")
    print(f"  {ind:<24}{cells}{mark}")

# 現行 CRI score（含 boost）
print(f"  {'-'*56}")
row = []
for h in horizons:
    lab = labels_by_h[h]
    row.append(roc_auc(cri_df.loc[lab.index, 'score'].values, lab.values))
print(f"  {'【現行 CRI score(含boost)】':<24}" + "".join(f"{a:>8.3f}" for a in row))

# ─── 邏輯回歸最佳化（5日窗）────────────────────────────────────────────────

main_h = 5
lab = labels_by_h[main_h]
common = lab.index
X = cri_df.loc[common, testable]
y = lab.values
Xz = (X - X.mean()) / (X.std() + 1e-9)
Xmat = Xz.values; n, p = Xmat.shape
Xb = np.hstack([np.ones((n,1)), Xmat]); w = np.zeros(p+1)
lr, lam = 0.1, 0.5
for it in range(3000):
    pr = 1/(1+np.exp(-(Xb@w)))
    w -= lr*(Xb.T@(pr-y)/n + lam*np.r_[0,w[1:]]/n)

def cv_auc(Xmat, y, folds=5):
    idx = np.arange(len(y)); np.random.seed(0); np.random.shuffle(idx)
    chunks = np.array_split(idx, folds); aucs=[]
    for f in range(folds):
        te = chunks[f]; tr = np.concatenate([chunks[i] for i in range(folds) if i!=f])
        Xtr = np.hstack([np.ones((len(tr),1)), Xmat[tr]]); Xte = np.hstack([np.ones((len(te),1)), Xmat[te]])
        ww = np.zeros(Xtr.shape[1])
        for it in range(2000):
            pr = 1/(1+np.exp(-(Xtr@ww)))
            ww -= lr*(Xtr.T@(pr-y[tr])/len(tr) + lam*np.r_[0,ww[1:]]/len(tr))
        aucs.append(roc_auc(Xte@ww, y[te]))
    return np.mean(aucs), np.std(aucs)

cvm, cvs = cv_auc(Xmat, y)
coefs = {testable[i]: w[i+1] for i in range(p)}

print(f"\n{'='*78}")
print(f"  邏輯回歸最佳化（目標：未來{main_h}日跌幅>5%）")
print(f"{'='*78}")
print(f"  {'指標':<24}  {'係數':>8}  {'重要性':>8}")
print(f"  {'-'*46}")
abst = sum(abs(c) for c in coefs.values())
for ind, c in sorted(coefs.items(), key=lambda x:-abs(x[1])):
    sign = "✅" if c>0.05 else ("⚠️反向" if c<-0.05 else "·中性")
    print(f"  {ind:<24}  {c:>8.3f}  {abs(c)/abst*100:>6.1f}%  {sign}")

score_auc = roc_auc(cri_df.loc[common,'score'].values, y)
print(f"\n  交叉驗證 AUC（樣本外）：{cvm:.3f} ± {cvs:.3f}")
print(f"  現行 CRI score(含boost) AUC：{score_auc:.3f}")
print(f"  改善空間：{(cvm-score_auc)*100:+.1f} AUC 點")

# ─── 實用警示性能 ───────────────────────────────────────────────────────────

def perf(scores, labels, rate):
    na = max(int(len(scores)*rate),1); thr=np.sort(scores)[-na]
    al = scores>=thr; tp=((al)&(labels==1)).sum()
    return tp/max(al.sum(),1), tp/max(labels.sum(),1)

logit_score = Xb@w
base = y.mean()
print(f"\n{'='*78}")
print(f"  實用警示性能（崩盤基準率 {base*100:.1f}%）")
print(f"{'='*78}")
print(f"  {'警報率':>6}  {'最佳化模型(精/召)':>22}  {'現行score(精/召)':>20}")
print(f"  {'-'*52}")
for rate in [0.05, 0.10, 0.15]:
    p1,r1 = perf(logit_score, y, rate)
    p2,r2 = perf(cri_df.loc[common,'score'].values, y, rate)
    print(f"  {rate*100:>5.0f}%  {p1*100:>6.0f}%/{r1*100:<3.0f}% ({p1/base:.1f}x)      {p2*100:>6.0f}%/{r2*100:<3.0f}%")

# ─── 建議權重 ───────────────────────────────────────────────────────────────

print(f"\n{'='*78}")
print(f"  ⭐ CRI v2 建議結構（9個可測指標，按係數正規化）")
print(f"{'='*78}")
pos = {ind:c for ind,c in coefs.items() if c>0.03}
pt = sum(pos.values())
for ind,c in sorted(pos.items(), key=lambda x:-x[1]):
    print(f"    {ind:<24}  {c/pt*100:>6.1f}%")
dropped = [ind for ind in testable if coefs[ind]<=0.03]
print(f"\n  建議剔除/低配（係數≤0.03）：{', '.join(dropped) if dropped else '無'}")
