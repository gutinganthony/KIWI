#!/usr/bin/env python3
"""
reweight_lab.py — 因子重配權重 + 新增因子的實測

factor_audit.py 發現 CRI 有結構性問題：
  - 20% 權重壓在回測中從未觸發的利率/信用因子（credit_acceleration/yield_surge/
    yield_curve_steepening），因為它們需要 FRED 資料，回測時傳空序列
  - ~4% 壓在 AUC < 0.5 的無效因子（breadth_divergence / rsi_divergence /
    ma_distance_reversal），三者即使全部滿分也只值 4 分
  - momentum_collapse(13%) 與 vix_spike(22%) 相關 0.71，邊際貢獻 -0.0002

本腳本實測：
  1. 各種重配權重方案，看 AUC 上限在哪
  2. 新增一個「HYG 日頻信用因子」——CRI 目前的信用因子用 FRED BAA/AAA（月頻、
     常缺資料），但 HYG 是日頻且已在抓。TSI 用了 HYG，CRI 沒用，這是明顯的缺口。
  3. 誠實對照：改良幅度到底有多少，值不值得動

用法：python scripts/reweight_lab.py
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BT = os.path.join(BASE, "data", "backtest")


def roc_auc(scores, labels):
    scores = np.asarray(scores, float)
    labels = np.asarray(labels, int)
    ok = ~np.isnan(scores)
    scores, labels = scores[ok], labels[ok]
    n_pos, n_neg = labels.sum(), len(labels) - labels.sum()
    if n_pos == 0 or n_neg == 0:
        return np.nan
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), float)
    ss = scores[order]
    i = 0
    while i < len(ss):
        j = i
        while j + 1 < len(ss) and ss[j + 1] == ss[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
        i = j + 1
    return (ranks[labels == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def precision_at(scores, labels, rate=0.10):
    s = np.asarray(scores, float); l = np.asarray(labels, int)
    ok = ~np.isnan(s); s, l = s[ok], l[ok]
    n = max(int(len(s) * rate), 1)
    thr = np.sort(s)[-n]
    a = s >= thr
    return l[a].sum() / max(a.sum(), 1)


# ─── 資料 ───────────────────────────────────────────────────────────────────
hist = pd.read_csv(os.path.join(BT, "cri_history.csv"), parse_dates=["date"]).set_index("date").sort_index()
spy = pd.read_csv(os.path.join(BT, "SPY.csv")); spy["Date"] = pd.to_datetime(spy["Date"])
spy = spy.set_index("Date").sort_index()
spy_px = (spy["Adj Close"] if "Adj Close" in spy.columns else spy["Close"]).dropna()
hyg = pd.read_csv(os.path.join(BT, "HYG.csv")); hyg["Date"] = pd.to_datetime(hyg["Date"])
hyg = hyg.set_index("Date").sort_index()
hyg_px = (hyg["Adj Close"] if "Adj Close" in hyg.columns else hyg["Close"]).dropna()

# 標籤：未來10日跌 >4%
fwd = {}
for d in hist.index:
    prior = spy_px.index[spy_px.index <= d]
    if len(prior) == 0:
        continue
    loc = spy_px.index.get_loc(prior[-1])
    if loc + 10 >= len(spy_px):
        continue
    fwd[d] = (spy_px.iloc[loc + 1:loc + 11].min() / spy_px.iloc[loc] - 1) * 100
fwd = pd.Series(fwd)
lab = (fwd <= -4.0).astype(int)
base = lab.mean()
print(f"樣本 {len(lab)} 日（{lab.index[0].date()}→{lab.index[-1].date()}），"
      f"事件基準率 {base*100:.1f}%")

ACTIVE = ["vix_spike", "vix_term_structure", "momentum_collapse", "distribution_days",
          "intraday_selloff", "breadth_divergence", "rsi_divergence", "ma_distance_reversal"]

CURRENT = {"vix_spike": .22, "vix_term_structure": .20, "momentum_collapse": .13,
           "distribution_days": .10, "intraday_selloff": .08, "garch_vix_gap": .03,
           "breadth_divergence": .02, "rsi_divergence": .01, "ma_distance_reversal": .01,
           "credit_acceleration": .10, "yield_surge": .06, "yield_curve_steepening": .04}


def composite(weights, df=None):
    d = hist if df is None else df
    tot = sum(w for k, w in weights.items() if k in d.columns)
    if tot <= 0:
        return None
    return sum(d[k] * w for k, w in weights.items() if k in d.columns) / tot


SCENARIOS = {
    "現況（12因子原始權重）": CURRENT,
    "① 剔除3個無效因子（breadth/rsi/ma）": {k: v for k, v in CURRENT.items()
                                    if k not in ("breadth_divergence", "rsi_divergence",
                                                 "ma_distance_reversal")},
    "② 再剔除冗餘的 momentum_collapse": {k: v for k, v in CURRENT.items()
                                  if k not in ("breadth_divergence", "rsi_divergence",
                                               "ma_distance_reversal", "momentum_collapse")},
    "③ 只留4支有效因子": {"vix_spike": .35, "vix_term_structure": .35,
                    "distribution_days": .18, "intraday_selloff": .12},
    "④ 純領先組合（期限結構為主）": {"vix_term_structure": .70, "distribution_days": .30},
    "⑤ 領先加重（term_structure 提到35%）": {"vix_term_structure": .35, "vix_spike": .30,
                                    "distribution_days": .20, "intraday_selloff": .15},
}

print("\n" + "=" * 92)
print("  CRI 重配權重實測（標籤：未來10日 SPY 跌 >4%）")
print("=" * 92)
print(f"  {'方案':<38}{'AUC':>8}{'精確@10%':>11}{'相對基準':>10}   評價")
print("  " + "-" * 88)
res = {}
for name, w in SCENARIOS.items():
    c = composite(w)
    if c is None:
        continue
    s = c.loc[lab.index]
    a = roc_auc(s.values, lab.values)
    p = precision_at(s.values, lab.values, 0.10)
    res[name] = a
    delta = a - res.get("現況（12因子原始權重）", a)
    tag = "（基準）" if "現況" in name else (f"{delta:+.3f}")
    print(f"  {name:<38}{a:>8.3f}{p*100:>10.0f}%{p/base:>9.1f}x   {tag}")

# ── 新增 HYG 日頻信用因子 ──
print("\n" + "=" * 92)
print("  新增因子測試：HYG 日頻信用背離（CRI 目前缺這一塊）")
print("=" * 92)
print("  設計：credit_hyg = clip((SPY 5日報酬 − HYG 5日報酬) / 3 × 100, 0, 100)")
print("        含義：股市撐住但高收益債先走弱 = 信用市場提前示警\n")

common = hist.index.intersection(hyg_px.index)
spy_5d = (spy_px / spy_px.shift(5) - 1) * 100
hyg_5d = (hyg_px / hyg_px.shift(5) - 1) * 100
div = (spy_5d.reindex(common) - hyg_5d.reindex(common))
credit_hyg = div.clip(lower=0).div(3).mul(100).clip(0, 100)

sub = hist.loc[common].copy()
sub["credit_hyg"] = credit_hyg
lab_h = lab.loc[lab.index.intersection(common)]
print(f"  可測期間：{common[0].date()} → {common[-1].date()}（{len(lab_h)} 日，"
      f"事件基準率 {lab_h.mean()*100:.1f}%）")

solo = roc_auc(sub["credit_hyg"].loc[lab_h.index].values, lab_h.values)
print(f"\n  單獨 AUC：{solo:.3f}  " +
      ("✅ 有預測力" if solo >= 0.55 else "❌ 無預測力"))

BEST = {"vix_spike": .35, "vix_term_structure": .35, "distribution_days": .18,
        "intraday_selloff": .12}
print(f"\n  {'組合':<44}{'AUC':>8}{'精確@10%':>11}   變化")
print("  " + "-" * 76)
for nm, w in [("方案③（4因子，不含 HYG）", BEST),
              ("方案③ + HYG信用 10%", {**{k: v * .9 for k, v in BEST.items()}, "credit_hyg": .10}),
              ("方案③ + HYG信用 20%", {**{k: v * .8 for k, v in BEST.items()}, "credit_hyg": .20}),
              ("現況12因子 + HYG信用 10%", {**{k: v * .9 for k, v in CURRENT.items()}, "credit_hyg": .10})]:
    c = composite(w, sub)
    s = c.loc[lab_h.index]
    a = roc_auc(s.values, lab_h.values)
    p = precision_at(s.values, lab_h.values, 0.10)
    print(f"  {nm:<44}{a:>8.3f}{p*100:>10.0f}%")

# ── 平滑 + 最佳權重的疊加效果 ──
print("\n" + "=" * 92)
print("  最終疊加：最佳權重 + 平滑讀法（兩個改良能否相加）")
print("=" * 92)
cur = composite(CURRENT).loc[lab.index]
bestw = composite(BEST).loc[lab.index]
print(f"  {'組合':<44}{'AUC':>8}{'精確@10%':>11}{'相對基準':>10}")
print("  " + "-" * 76)
for nm, s in [("現況權重 + 原始每日讀數（今天的做法）", cur),
              ("現況權重 + 10日平滑", cur.rolling(10, min_periods=1).mean()),
              ("最佳權重 + 原始每日讀數", bestw),
              ("最佳權重 + 10日平滑", bestw.rolling(10, min_periods=1).mean())]:
    a = roc_auc(s.values, lab.values)
    p = precision_at(s.values, lab.values, 0.10)
    print(f"  {nm:<44}{a:>8.3f}{p*100:>10.0f}%{p/base:>9.1f}x")
