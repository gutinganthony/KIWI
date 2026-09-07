#!/usr/bin/env python3
"""
factor_audit.py — KIWI 三指數因子有效性總檢討

目的：回答「哪些因子有效、哪些無效、哪些是領先、哪些只是同步」。

方法論：
  1. 無條件 AUC（多時間窗 D1/D3/D5/D10）— 基本預測力
  2. 【關鍵】平靜期條件 AUC — 只在「過去5日沒跌超過2%」的日子評估。
     這排除了「崩盤已經開始才亮燈」的作弊效果，是真正的早期預警測試。
  3. 觸發率 — 一個 AUC 高但幾乎不亮燈的因子，實用價值不同
  4. 冗餘度 — 因子間相關係數，找出重複計算的因子
  5. 邊際貢獻 — 逐一移除因子看總分 AUC 變化（drop-one-out）

用法：python scripts/factor_audit.py
"""
import os
import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "backtest")

# ─── 工具 ────────────────────────────────────────────────────────────────────

def roc_auc(scores, labels):
    """Mann-Whitney U 版 ROC-AUC，含 tie 處理。"""
    scores = np.asarray(scores, float)
    labels = np.asarray(labels, int)
    ok = ~np.isnan(scores)
    scores, labels = scores[ok], labels[ok]
    n_pos, n_neg = labels.sum(), len(labels) - labels.sum()
    if n_pos == 0 or n_neg == 0:
        return np.nan
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), float)
    sorted_s = scores[order]
    i = 0
    while i < len(sorted_s):                     # average ranks for ties
        j = i
        while j + 1 < len(sorted_s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
        i = j + 1
    return (ranks[labels == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def fwd_min_return(price, dates, window):
    """未來 window 個交易日內的最大跌幅 (%)。"""
    out = pd.Series(index=dates, dtype=float)
    pidx = price.index
    for d in dates:
        prior = pidx[pidx <= d]
        if len(prior) == 0:
            continue
        loc = pidx.get_loc(prior[-1])
        if loc + window >= len(price):
            continue
        out[d] = (price.iloc[loc + 1:loc + 1 + window].min() / price.iloc[loc] - 1) * 100
    return out


def past_return(price, dates, window=5):
    """過去 window 個交易日的報酬 (%)，用來定義「平靜期」。"""
    out = pd.Series(index=dates, dtype=float)
    pidx = price.index
    for d in dates:
        prior = pidx[pidx <= d]
        if len(prior) == 0:
            continue
        loc = pidx.get_loc(prior[-1])
        if loc - window < 0:
            continue
        out[d] = (price.iloc[loc] / price.iloc[loc - window] - 1) * 100
    return out


def load_price(fname, date_col="Date", px_col=None):
    df = pd.read_csv(os.path.join(DATA, fname))
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()
    if px_col is None:
        px_col = "Adj Close" if "Adj Close" in df.columns else "Close"
    return df[px_col].dropna()


# ─── 主分析 ──────────────────────────────────────────────────────────────────

def audit(index_name, hist_file, factor_cols, weights, price, drop_thresh=-5.0):
    print("\n" + "=" * 96)
    print(f"  {index_name} 因子有效性總檢討")
    print("=" * 96)

    hist = pd.read_csv(os.path.join(DATA, hist_file), parse_dates=["date"]).set_index("date")
    hist = hist.sort_index()
    dates = hist.index
    print(f"  樣本：{len(hist)} 個交易日  {dates[0].date()} → {dates[-1].date()}")

    # ── 標籤：未來 N 日跌幅 > threshold ──
    horizons = [1, 3, 5, 10]
    labels = {}
    for h in horizons:
        fwd = fwd_min_return(price, dates, h)
        labels[h] = (fwd <= drop_thresh).astype(int)[fwd.notna()]
    base = labels[5].mean()
    print(f"  崩盤定義：未來N日最大跌幅 ≤ {drop_thresh}%  |  D5 基準率 {base*100:.1f}%")

    # ── 平靜期遮罩：過去5日跌幅未超過 2% ──
    past5 = past_return(price, dates, 5)
    calm = past5 > -2.0
    n_calm = int(calm.sum())
    print(f"  平靜期樣本（過去5日未跌超過2%）：{n_calm} 日 ({n_calm/len(dates)*100:.0f}%)")

    # ── 逐因子分析 ──
    print(f"\n  {'因子':<24}{'權重':>6}{'觸發率':>8}{'D1':>7}{'D3':>7}{'D5':>7}{'D10':>7}"
          f"{'平靜D5':>9}  判定")
    print("  " + "-" * 92)

    rows = []
    for f in factor_cols:
        if f not in hist.columns:
            print(f"  {f:<24}  （此回測未啟用，資料全為 0）")
            continue
        vals = hist[f]
        fire = float((vals > 1).mean())          # 觸發率：訊號 > 1 視為有發聲

        aucs = {}
        for h in horizons:
            lab = labels[h]
            aucs[h] = roc_auc(vals.loc[lab.index].values, lab.values)

        # 平靜期 D5 AUC —— 真正的早期預警能力
        lab5 = labels[5]
        calm_idx = lab5.index[calm.reindex(lab5.index).fillna(False).values]
        auc_calm = (roc_auc(vals.loc[calm_idx].values, lab5.loc[calm_idx].values)
                    if len(calm_idx) > 50 else np.nan)

        best = max(v for v in aucs.values() if not np.isnan(v))
        if fire < 0.02:
            verdict = "💤 幾乎不觸發"
        elif best < 0.50:
            verdict = "❌ 反向/無效"
        elif best < 0.55:
            verdict = "❌ 無預測力"
        elif not np.isnan(auc_calm) and auc_calm >= 0.60:
            verdict = "⭐ 真領先"
        elif best >= 0.70:
            verdict = "✅ 強（偏同步）"
        elif best >= 0.60:
            verdict = "🟡 中等"
        else:
            verdict = "🟠 偏弱"

        cells = "".join(f"{aucs[h]:>7.3f}" if not np.isnan(aucs[h]) else "    n/a"
                        for h in horizons)
        calm_s = f"{auc_calm:>9.3f}" if not np.isnan(auc_calm) else "      n/a"
        w = weights.get(f, 0.0)
        print(f"  {f:<24}{w*100:>5.0f}%{fire*100:>7.0f}%{cells}{calm_s}  {verdict}")
        rows.append(dict(factor=f, weight=w, fire=fire, auc_calm=auc_calm,
                         best=best, **{f"d{h}": aucs[h] for h in horizons}))

    # ── 總分 AUC ──
    print("  " + "-" * 92)
    sc = hist["score"]
    cells = "".join(f"{roc_auc(sc.loc[labels[h].index].values, labels[h].values):>7.3f}"
                    for h in horizons)
    lab5 = labels[5]
    calm_idx = lab5.index[calm.reindex(lab5.index).fillna(False).values]
    sc_calm = roc_auc(sc.loc[calm_idx].values, lab5.loc[calm_idx].values)
    print(f"  {'【總分 score】':<22}{'':>6}{'':>8}{cells}{sc_calm:>9.3f}")

    df = pd.DataFrame(rows)

    # ── 冗餘度：因子間相關 ──
    active = [r["factor"] for r in rows if r["fire"] >= 0.02]
    if len(active) > 1:
        corr = hist[active].corr()
        pairs = []
        for i in range(len(active)):
            for j in range(i + 1, len(active)):
                c = corr.iloc[i, j]
                if abs(c) >= 0.5:
                    pairs.append((active[i], active[j], c))
        if pairs:
            print(f"\n  ⚠️  高度重複的因子對（|相關| ≥ 0.5，代表資訊冗餘）：")
            for a, b, c in sorted(pairs, key=lambda x: -abs(x[2])):
                print(f"      {a:<24} ↔ {b:<24} r = {c:+.2f}")
        else:
            print(f"\n  ✅ 因子間無高度重複（所有 |相關| < 0.5），資訊互補性良好")

    # ── 邊際貢獻：drop-one-out ──
    print(f"\n  邊際貢獻（移除該因子後，重算加權總分的 D5 AUC 變化）：")
    lab = labels[5]
    wsum_all = sum(weights.get(f, 0) for f in active)
    full = sum(hist[f].loc[lab.index] * weights.get(f, 0) for f in active) / max(wsum_all, 1e-9)
    auc_full = roc_auc(full.values, lab.values)
    print(f"      完整模型 D5 AUC = {auc_full:.4f}")
    deltas = []
    for f in active:
        rest = [x for x in active if x != f]
        ws = sum(weights.get(x, 0) for x in rest)
        if ws <= 0:
            continue
        sub = sum(hist[x].loc[lab.index] * weights.get(x, 0) for x in rest) / ws
        a = roc_auc(sub.values, lab.values)
        deltas.append((f, auc_full - a))
    for f, d in sorted(deltas, key=lambda x: -x[1]):
        bar = "▓" * min(int(abs(d) * 800), 30)
        sign = "貢獻" if d > 0.0005 else ("拖累" if d < -0.0005 else "無影響")
        print(f"      {f:<24} {d:+.4f}  {bar} {sign}")

    return df, hist, labels, calm


def event_study(index_name, hist, price, events, thresholds):
    """重大跌幅事件研究：崩盤前指數的實際讀數。"""
    print(f"\n  {index_name} 重大事件前的讀數（D-10 / D-5 / D-3 / D-1 / D0 / 事件中峰值）")
    print("  " + "-" * 92)
    lo, mid, hi = thresholds
    sc = hist["score"]

    def at_off(cdate, off):
        prior = sc.index[sc.index <= cdate]
        if len(prior) == 0:
            return None
        loc = sc.index.get_loc(prior[-1]) - off
        return float(sc.iloc[loc]) if 0 <= loc < len(sc) else None

    hdr = f"  {'事件':<30}{'D-10':>7}{'D-5':>7}{'D-3':>7}{'D-1':>7}{'D0':>7}{'峰值':>7}  首次預警"
    print(hdr)
    results = []
    for cdate_s, name in events:
        cdate = pd.Timestamp(cdate_s)
        offs = {o: at_off(cdate, o) for o in (10, 5, 3, 1, 0)}
        prior = sc.index[sc.index <= cdate]
        peak = None
        if len(prior):
            loc = sc.index.get_loc(prior[-1])
            win = sc.iloc[loc:loc + 8]
            peak = float(win.max()) if len(win) else None
        # 首次達 mid 門檻（崩盤前 20 日內）
        lead = None
        if len(prior):
            loc = sc.index.get_loc(prior[-1])
            w = sc.iloc[max(0, loc - 20):loc + 1]
            hits = w[w >= mid]
            if len(hits):
                lead = loc - sc.index.get_loc(hits.index[0])
        f = lambda v: f"{v:>7.0f}" if v is not None else "     --"
        warn = f"D-{lead}" if lead is not None else "(無)"
        print(f"  {name:<30}{f(offs[10])}{f(offs[5])}{f(offs[3])}{f(offs[1])}{f(offs[0])}{f(peak)}  {warn:>8}")
        results.append((name, lead))
    det = [l for _, l in results if l is not None]
    print(f"\n  偵測率（崩盤前20日內達門檻 {mid}）：{len(det)}/{len(results)}"
          f" = {len(det)/max(len(results),1)*100:.0f}%"
          + (f"  平均提前 {np.mean(det):.1f} 個交易日" if det else ""))


# ═══════════════════════════════════════════════════════════════════════════

CRI_WEIGHTS = {
    "vix_spike": 0.22, "vix_term_structure": 0.20, "momentum_collapse": 0.13,
    "distribution_days": 0.10, "intraday_selloff": 0.08, "garch_vix_gap": 0.03,
    "breadth_divergence": 0.02, "rsi_divergence": 0.01, "ma_distance_reversal": 0.01,
    "credit_acceleration": 0.10, "yield_surge": 0.06, "yield_curve_steepening": 0.04,
}
CRI_FACTORS = list(CRI_WEIGHTS.keys())

TSI_WEIGHTS = {
    "tech_breadth": 0.18, "vvix_lead": 0.14, "credit_divergence": 0.12,
    "tech_crash_day": 0.10, "vix_tech_correlation": 0.08, "sox_qqq_divergence": 0.07,
    "memory_momentum": 0.05, "sox_momentum_decel": 0.05, "yield_shock": 0.09,
    "yield_30y_stress": 0.05, "ai_infra_rs": 0.04, "yield_curve_bear_steep": 0.03,
}
TSI_FACTORS = list(TSI_WEIGHTS.keys())

if __name__ == "__main__":
    spy = load_price("SPY.csv")
    qqq = load_price("QQQ.csv")
    print(f"載入 SPY {len(spy)} 筆 ({spy.index[0].date()}→{spy.index[-1].date()})，"
          f"QQQ {len(qqq)} 筆")

    cri_df, cri_hist, cri_lab, cri_calm = audit(
        "CRI（大盤崩盤風險）", "cri_history.csv", CRI_FACTORS, CRI_WEIGHTS, spy)

    CRASHES = [
        ("1997-10-27", "1997 亞洲金融風暴"),
        ("1998-08-31", "1998 LTCM/俄債危機"),
        ("2000-04-14", "2000 網路泡沫首波"),
        ("2001-09-17", "2001 911 復市"),
        ("2002-07-19", "2002 企業醜聞熊市"),
        ("2008-09-15", "2008 雷曼倒閉"),
        ("2010-05-06", "2010 閃電崩盤"),
        ("2011-08-04", "2011 美債降評/歐債"),
        ("2015-08-21", "2015 人民幣閃崩"),
        ("2018-02-05", "2018 Volmageddon"),
        ("2018-12-14", "2018 聖誕崩跌"),
        ("2020-02-24", "2020 COVID 股災"),
    ]
    event_study("CRI", cri_hist, spy, CRASHES, (20, 35, 50))

    tsi_df, tsi_hist, tsi_lab, tsi_calm = audit(
        "TSI（科技板塊壓力）", "tsi_history.csv", TSI_FACTORS, TSI_WEIGHTS, qqq)

    TECH_CRASHES = [
        ("2008-09-15", "2008 雷曼倒閉"),
        ("2010-05-06", "2010 閃電崩盤"),
        ("2011-08-04", "2011 美債降評"),
        ("2015-08-21", "2015 人民幣閃崩"),
        ("2018-02-05", "2018 Volmageddon"),
        ("2018-10-10", "2018 科技股10月修正"),
        ("2018-12-14", "2018 聖誕崩跌"),
        ("2020-02-24", "2020 COVID 股災"),
    ]
    event_study("TSI", tsi_hist, qqq, TECH_CRASHES, (22, 40, 60))
