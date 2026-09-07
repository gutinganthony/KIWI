#!/usr/bin/env python3
"""
credit_lead_test.py — MRI 信用觸發層的核心假設驗證

要驗證的主張：「信用市場的壓力領先股市回檔」。
這是整個 MRI 設計裡唯一宣稱能「預警」的一層，若不成立，兩軸架構就只剩半邊。

方法上最重要的一件事——**必須控制「兩者一起跌」的假象**：
  HYG 和 SPY 在崩盤時本來就會一起跌。若只做無條件 AUC，會把「同步下跌」
  誤讀成「信用領先」。因此本腳本的主結果是【平靜期條件 AUC】：
  只在「SPY 過去 10 日沒跌超過 2%」的日子評估，這時股市看起來還好，
  若信用指標此時仍能預測未來的股市回檔，才是真正的領先性。

同時放入對照組（SPY 自身的回撤），檢驗信用是否真的提供了額外資訊，
還是只是把股市已知的下跌換個方式講一遍。

資料：HYG/SPY 2007-2026（合併 data/backtest 與 data/ext），涵蓋
      2008 金融海嘯、2011 歐債、2015、2018×2、2020 COVID、2022 熊市、2025。

註：HYG 價格同時含「信用利差」與「利率久期」兩種成分。待 LQD/IEF 由
    GitHub Actions 抓回後（已加入 fetch_backtest_ext.py），可用
    HYG − IEF 分離出純信用利差，本測試會再跑一次升級版。

用法：python scripts/credit_lead_test.py
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BT = os.path.join(BASE, "data", "backtest")
EXT = os.path.join(BASE, "data", "ext")


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


def load_merged(name):
    """合併 data/backtest（歷史）與 data/ext（現代）的同名價格序列。"""
    parts = []
    for d in (BT, EXT):
        p = os.path.join(d, f"{name}.csv")
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        dcol = "Date" if "Date" in df.columns else "DATE"
        df[dcol] = pd.to_datetime(df[dcol])
        df = df.set_index(dcol).sort_index()
        col = "Adj Close" if "Adj Close" in df.columns else "Close"
        parts.append(df[col].dropna().rename(name))
    if not parts:
        raise FileNotFoundError(name)
    s = pd.concat(parts)
    # 重疊區間以後者（ext，較新）為準
    return s[~s.index.duplicated(keep="last")].sort_index()


hyg = load_merged("HYG")
spy = load_merged("SPY")
common = hyg.index.intersection(spy.index)
hyg, spy = hyg.loc[common], spy.loc[common]
print(f"樣本：{common[0].date()} → {common[-1].date()}（{len(common)} 個交易日）")

# ── 候選信用壓力指標（全部只用當下與過去）──
signals = {
    "HYG 自身回撤（距60日高點）":  -(hyg / hyg.rolling(60).max() - 1) * 100,
    "HYG 5日跌幅":                -(hyg / hyg.shift(5) - 1) * 100,
    "HYG 20日跌幅":               -(hyg / hyg.shift(20) - 1) * 100,
    "HYG 相對 SPY（20日）":       -((hyg / hyg.shift(20)) - (spy / spy.shift(20))) * 100,
    "HYG 波動率（20日年化）":      hyg.pct_change().rolling(20).std() * np.sqrt(252) * 100,
}
# 對照組：股市自己的回撤（若信用指標贏不過它，代表沒有提供額外資訊）
control = {
    "【對照】SPY 自身回撤":        -(spy / spy.rolling(60).max() - 1) * 100,
    "【對照】SPY 20日跌幅":        -(spy / spy.shift(20) - 1) * 100,
}

# ── 標籤：未來 N 日 SPY 最大跌幅 ≤ -5% ──
def fwd_label(window, thresh=-5.0):
    fwd = pd.Series(index=spy.index, dtype=float)
    v = spy.values
    for i in range(len(v) - window):
        fwd.iloc[i] = (v[i + 1:i + 1 + window].min() / v[i] - 1) * 100
    return (fwd <= thresh).astype(int)[fwd.notna()]


# ── 平靜期遮罩 ──
past10 = (spy / spy.shift(10) - 1) * 100
calm = past10 > -2.0
print(f"平靜期（SPY 過去10日未跌超過2%）：{int(calm.sum())} 日 "
      f"({calm.sum()/len(calm)*100:.0f}%)\n")

horizons = [5, 10, 20, 40]
print("=" * 94)
print("  信用壓力指標對『未來 N 日 SPY 跌 >5%』的預測力")
print("=" * 94)
print(f"  {'指標':<28}" + "".join(f"{'D'+str(h):>8}" for h in horizons)
      + f"{'平靜D20':>10}   判定")
print("  " + "-" * 90)

results = {}
for nm, s in {**signals, **control}.items():
    row, calm_auc = [], np.nan
    for h in horizons:
        lab = fwd_label(h)
        idx = lab.index.intersection(s.dropna().index)
        row.append(roc_auc(s.loc[idx].values, lab.loc[idx].values) if len(idx) > 200 else np.nan)
    lab20 = fwd_label(20)
    cidx = lab20.index.intersection(s.dropna().index)
    cidx = cidx[calm.reindex(cidx).fillna(False).values]
    if len(cidx) > 200:
        calm_auc = roc_auc(s.loc[cidx].values, lab20.loc[cidx].values)
    results[nm] = (row, calm_auc)
    cells = "".join(f"{v:>8.3f}" if not np.isnan(v) else "     n/a" for v in row)
    if np.isnan(calm_auc):
        verdict = "樣本不足"
    elif calm_auc >= 0.65:
        verdict = "⭐ 強領先"
    elif calm_auc >= 0.58:
        verdict = "✅ 有領先性"
    elif calm_auc >= 0.53:
        verdict = "🟡 微弱"
    else:
        verdict = "❌ 無領先性"
    print(f"  {nm:<28}{cells}{calm_auc:>10.3f}   {verdict}")

# ── 關鍵對照：信用是否勝過「股市自己已經在跌」──
print("\n" + "=" * 94)
print("  關鍵問題：信用指標有沒有提供『股市自身回撤』之外的資訊？")
print("=" * 94)
best_credit = max((v[1], k) for k, v in results.items() if not k.startswith("【對照】"))
best_ctrl = max((v[1], k) for k, v in results.items() if k.startswith("【對照】"))
print(f"  最佳信用指標   {best_credit[1]:<30} 平靜期 AUC {best_credit[0]:.3f}")
print(f"  最佳對照指標   {best_ctrl[1]:<30} 平靜期 AUC {best_ctrl[0]:.3f}")
diff = best_credit[0] - best_ctrl[0]
print(f"  差距 {diff:+.3f}  → " + (
    "信用確實提供額外資訊 ✅" if diff > 0.02 else
    "信用與股市自身回撤幾乎等價，額外資訊有限 ⚠️" if diff > -0.02 else
    "信用不如直接看股市自身 ❌"))

# ── 領先天數：信用壓力高峰 vs 股市回檔起點 ──
print("\n" + "=" * 94)
print("  事件層級：每次 SPY 重大回檔前，信用壓力何時開始升高")
print("=" * 94)


def find_drawdowns(price, min_decline=7.0):
    p, idx = price.values, price.index
    ev, peak_i, i = [], 0, 1
    while i < len(p):
        if p[i] > p[peak_i]:
            peak_i = i; i += 1; continue
        if (p[i] / p[peak_i] - 1) * 100 <= -min_decline:
            j = i; tr = i
            while j < len(p) and p[j] < p[peak_i]:
                if p[j] < p[tr]:
                    tr = j
                j += 1
            ev.append({"peak": idx[peak_i], "trough": idx[tr],
                       "dd": (p[tr] / p[peak_i] - 1) * 100})
            peak_i = j if j < len(p) else len(p) - 1
            i = j
        else:
            i += 1
    return ev


cs = signals["HYG 自身回撤（距60日高點）"]
cs_thresh = cs.dropna().quantile(0.80)   # 信用壓力進入歷史前 20% 視為「亮燈」
events = find_drawdowns(spy, 7.0)
print(f"  信用亮燈門檻：HYG 回撤 ≥ {cs_thresh:.2f}%（歷史 80 百分位）\n")
print(f"  {'SPY 回檔（峰→谷）':<28}{'跌幅':>8}   信用何時亮燈")
print("  " + "-" * 66)
leads = []
for e in events:
    pk = e["peak"]
    w = cs[(cs.index <= pk) & (cs.index >= pk - pd.Timedelta(days=90))].dropna()
    hit = w[w >= cs_thresh]
    if len(hit):
        lead_days = len(cs[(cs.index > hit.index[0]) & (cs.index <= pk)])
        leads.append(lead_days)
        msg = f"回檔前 {lead_days} 個交易日"
    else:
        msg = "❌ 回檔前未亮燈"
    # 注意：date 物件的 __format__ 會把 ":<14" 當 strftime 格式，必須先轉字串
    span = f"{pk.date()}→{e['trough'].date()}"
    print(f"  {span:<28}{e['dd']:>7.1f}%   {msg}")
print("  " + "-" * 66)
if leads:
    print(f"  事前亮燈 {len(leads)}/{len(events)} 次 = {len(leads)/len(events)*100:.0f}%"
          f"，中位數提前 {int(np.median(leads))} 個交易日")
else:
    print("  沒有任何一次事前亮燈")

print("\n註：HYG 含利率久期成分，本測試為近似版。LQD/IEF 抓回後可分離純信用利差再驗一次。")
