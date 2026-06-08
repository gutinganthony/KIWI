#!/usr/bin/env python3
"""
tsi_optimize.py — 用真實回測數據找出最有效的 TSI 指標結構（嚴謹版）

讀取 real_backtest.py 產生的 tsi_history.csv，做：
  1. 多個預測時間窗（1/3/5/10日）下各指標的 ROC-AUC
  2. 邏輯回歸找最佳權重組合
  3. 與現行 TSI score 比較
  4. 輸出建議的新權重結構
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "backtest")

tsi_df = pd.read_csv(os.path.join(DATA, 'tsi_history.csv'), index_col=0, parse_dates=True)
spy = pd.read_csv(os.path.join(DATA, 'SPY.csv'))
spy['Date'] = pd.to_datetime(spy['Date'])
spy = spy.set_index('Date').sort_index()['Adj Close']

indicators = ['vvix_lead', 'credit_divergence', 'sox_momentum_decel',
              'tech_crash_day', 'vix_tech_correlation', 'sox_qqq_divergence',
              'memory_momentum', 'tech_breadth']

def roc_auc(scores, labels):
    scores = np.asarray(scores, float); labels = np.asarray(labels)
    n_pos = labels.sum(); n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0: return 0.5
    ranks = np.argsort(np.argsort(scores)) + 1
    return (ranks[labels == 1].sum() - n_pos*(n_pos+1)/2) / (n_pos*n_neg)

def fwd_min_return(window):
    """未來 window 日 SPY 最大跌幅(%)。"""
    out = pd.Series(index=tsi_df.index, dtype=float)
    for d in tsi_df.index:
        prior = spy.index[spy.index <= d]
        if len(prior) == 0: continue
        loc = spy.index.get_loc(prior[-1])
        if loc + window >= len(spy): continue
        out[d] = (spy.iloc[loc+1:loc+1+window].min() / spy.iloc[loc] - 1) * 100
    return out

# ─── 評估 1：多時間窗 × 各指標 AUC ──────────────────────────────────────────

print("="*78)
print("  各指標在不同預測時間窗的 ROC-AUC（崩盤定義：未來N日跌幅>5%）")
print("  AUC: 0.5=亂猜  0.55=微弱  0.60=有用  0.65+=強")
print("="*78)

horizons = [1, 3, 5, 10]
auc_table = {}  # (ind, h) -> auc
labels_by_h = {}
for h in horizons:
    fwd = fwd_min_return(h)
    lab = (fwd <= -5.0).astype(int)
    lab = lab[fwd.notna()]
    labels_by_h[h] = lab

# 用 5日窗為主要最佳化目標
main_h = 5
common_idx = labels_by_h[main_h].index
X = tsi_df.loc[common_idx, indicators]
y = labels_by_h[main_h].values

print(f"\n  {'指標':<24} " + "".join(f"{'D'+str(h):>8}" for h in horizons))
print(f"  {'-'*56}")
for ind in indicators:
    row = []
    for h in horizons:
        lab = labels_by_h[h]
        vals = tsi_df.loc[lab.index, ind].values
        a = roc_auc(vals, lab.values)
        auc_table[(ind, h)] = a
        row.append(a)
    leading = "⏩" if ind in ('vvix_lead','credit_divergence','sox_momentum_decel') else "  "
    cells = "".join(f"{a:>8.3f}" for a in row)
    best = max(row)
    mark = " ✅" if best >= 0.58 else (" 🟡" if best >= 0.54 else " ❌")
    print(f"  {leading} {ind:<22}{cells}{mark}")

# 現行整體 score
print(f"  {'-'*56}")
row = []
for h in horizons:
    lab = labels_by_h[h]
    a = roc_auc(tsi_df.loc[lab.index, 'score'].values, lab.values)
    row.append(a)
print(f"     {'【現行 TSI score】':<20}" + "".join(f"{a:>8.3f}" for a in row))

# ─── 評估 2：邏輯回歸找最佳權重 ─────────────────────────────────────────────

print(f"\n{'='*78}")
print(f"  邏輯回歸最佳化（目標：未來{main_h}日跌幅>5%）")
print(f"{'='*78}")

# 標準化
Xz = (X - X.mean()) / (X.std() + 1e-9)
Xmat = Xz.values
n, p = Xmat.shape

# 加截距
Xb = np.hstack([np.ones((n, 1)), Xmat])
w = np.zeros(p + 1)

# 梯度下降（L2 正則）
lr = 0.1; lam = 0.5
for it in range(3000):
    z = Xb @ w
    pred = 1 / (1 + np.exp(-z))
    grad = Xb.T @ (pred - y) / n + lam * np.r_[0, w[1:]] / n
    w -= lr * grad

# 訓練集 AUC（注意：這是樣本內，會略樂觀）
logit_score = Xb @ w
logit_auc = roc_auc(logit_score, y)

# 5-fold 交叉驗證 AUC（樣本外，較誠實）
def cv_auc(Xmat, y, folds=5):
    idx = np.arange(len(y))
    np.random.seed(0); np.random.shuffle(idx)
    chunks = np.array_split(idx, folds)
    aucs = []
    for f in range(folds):
        test = chunks[f]; train = np.concatenate([chunks[i] for i in range(folds) if i != f])
        Xtr = np.hstack([np.ones((len(train),1)), Xmat[train]])
        Xte = np.hstack([np.ones((len(test),1)), Xmat[test]])
        ww = np.zeros(Xtr.shape[1])
        for it in range(2000):
            pr = 1/(1+np.exp(-(Xtr@ww)))
            g = Xtr.T@(pr - y[train])/len(train) + lam*np.r_[0, ww[1:]]/len(train)
            ww -= lr*g
        aucs.append(roc_auc(Xte@ww, y[test]))
    return np.mean(aucs), np.std(aucs)

cv_mean, cv_std = cv_auc(Xmat, y)

print(f"  邏輯回歸係數（標準化後，正=升高時崩盤機率增加）：")
print(f"  {'指標':<24}  {'係數':>8}  {'重要性':>8}")
print(f"  {'-'*48}")
coefs = {indicators[i]: w[i+1] for i in range(p)}
abs_total = sum(abs(c) for c in coefs.values())
for ind, c in sorted(coefs.items(), key=lambda x: -abs(x[1])):
    imp = abs(c) / abs_total * 100
    leading = "⏩" if ind in ('vvix_lead','credit_divergence','sox_momentum_decel') else "  "
    sign = "✅" if c > 0.05 else ("⚠️反向" if c < -0.05 else "·中性")
    print(f"  {leading} {ind:<22}  {c:>8.3f}  {imp:>6.1f}%  {sign}")

print(f"\n  樣本內 AUC：{logit_auc:.3f}")
print(f"  交叉驗證 AUC（樣本外，誠實值）：{cv_mean:.3f} ± {cv_std:.3f}")
score_auc_main = roc_auc(tsi_df.loc[common_idx, 'score'].values, y)
print(f"  現行 TSI score AUC：{score_auc_main:.3f}")
print(f"  改善：{(cv_mean - score_auc_main)*100:+.1f} AUC 點")

# ─── 評估 3：實用警示性能（精確度/召回率）──────────────────────────────────

print(f"\n{'='*78}")
print(f"  實用警示性能：把分數最高的 X% 時間設為警示")
print(f"{'='*78}")

def perf_at_rate(scores, labels, rate):
    n_alert = max(int(len(scores)*rate), 1)
    thr = np.sort(scores)[-n_alert]
    alerts = scores >= thr
    tp = ((alerts) & (labels==1)).sum()
    prec = tp/max(alerts.sum(),1); rec = tp/max(labels.sum(),1)
    return prec, rec

base_rate = y.mean()
print(f"  崩盤基準率：{base_rate*100:.1f}%（隨機警示的精確度）")
print(f"\n  {'警報率':>6}  {'最佳化模型':>20}  {'現行score':>18}")
print(f"  {'':>6}  {'精確度/召回':>20}  {'精確度/召回':>18}")
print(f"  {'-'*50}")
for rate in [0.05, 0.10, 0.15, 0.20]:
    p1, r1 = perf_at_rate(logit_score, y, rate)
    p2, r2 = perf_at_rate(tsi_df.loc[common_idx,'score'].values, y, rate)
    lift1 = p1/base_rate
    print(f"  {rate*100:>5.0f}%  {p1*100:>6.0f}%/{r1*100:<3.0f}% ({lift1:.1f}x基準)  {p2*100:>6.0f}%/{r2*100:<3.0f}%")

# ─── 輸出建議權重（給 TSI v4）──────────────────────────────────────────────

print(f"\n{'='*78}")
print(f"  ⭐ TSI v4 建議結構（只保留正係數指標，按重要性配權）")
print(f"{'='*78}")
positive = {ind: c for ind, c in coefs.items() if c > 0.03}
ptotal = sum(positive.values())
print(f"  {'指標':<24}  {'建議權重':>8}")
print(f"  {'-'*36}")
for ind, c in sorted(positive.items(), key=lambda x: -x[1]):
    leading = "⏩" if ind in ('vvix_lead','credit_divergence','sox_momentum_decel') else "  "
    print(f"  {leading} {ind:<22}  {c/ptotal*100:>6.1f}%")
dropped = [ind for ind in indicators if coefs[ind] <= 0.03]
print(f"\n  建議剔除（係數≤0.03，對預測崩盤無正貢獻）：")
for ind in dropped:
    print(f"    ✗ {ind}  (係數={coefs[ind]:+.3f})")
