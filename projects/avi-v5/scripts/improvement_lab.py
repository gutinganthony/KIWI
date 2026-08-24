#!/usr/bin/env python3
"""
improvement_lab.py — 「怎麼讀 / 加什麼參數能提高預判效果」實測台

背景觀察：CRI/TSI 是「跳動式尖峰」而非持續升高。這造成兩個問題：
  (a) 「20日內曾達門檻」這種偵測率指標會被雜訊灌水，看起來 100% 但沒有實用價值
  (b) 使用者看到單日尖峰無法分辨是真警訊還是雜訊

本腳本實測五組改良方案，全部用同一套評分標準比較：
  A. 原始每日分數（基準）
  B. 平滑：N 日移動平均
  C. 持續性：最近 N 日中有 M 日 ≥ 門檻
  D. 斜率：指數本身的變化率（方向比水位重要？）
  E. 組合：平滑水位 + 上升斜率

評分標準（避免只看 AUC 的盲點）：
  - AUC：整體排序能力
  - 精確率 @ 固定警報率：實務上「亮燈時有多少真的跌」
  - 事件覆蓋率：重大回檔前是否真的有「持續」警訊（非單日尖峰）

用法：python scripts/improvement_lab.py
"""
import os
import json
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(BASE, "data", "ext")
BT = os.path.join(BASE, "data", "backtest")
HISTORY = os.path.abspath(os.path.join(BASE, "..", "..", "docs", "history.json"))


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


def precision_at_rate(scores, labels, rate):
    """在「只允許亮燈 rate 比例的日子」的前提下，亮燈時的命中率。"""
    s = np.asarray(scores, float)
    ok = ~np.isnan(s)
    s, l = s[ok], np.asarray(labels, int)[ok]
    n = max(int(len(s) * rate), 1)
    thr = np.sort(s)[-n]
    alert = s >= thr
    if alert.sum() == 0:
        return np.nan, np.nan
    return (l[alert].sum() / alert.sum(), alert.sum() / len(s))


def load_ext(name):
    df = pd.read_csv(os.path.join(EXT, f"{name}.csv"))
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    return df[col].dropna()


def make_labels(score_index, price, horizon=10, thresh=-4.0):
    fwd = {}
    pidx = price.index
    for d in score_index:
        prior = pidx[pidx <= d]
        if len(prior) == 0:
            continue
        loc = pidx.get_loc(prior[-1])
        if loc + horizon >= len(price):
            continue
        fwd[d] = (price.iloc[loc + 1:loc + 1 + horizon].min() / price.iloc[loc] - 1) * 100
    fwd = pd.Series(fwd)
    return (fwd <= thresh).astype(int), fwd


def variants(sc):
    """產生所有候選讀法。全部只用「當下與過去」的資訊，無未來洩漏。"""
    v = {"A. 原始每日分數（現況）": sc}
    for n in (3, 5, 10):
        v[f"B. {n}日移動平均"] = sc.rolling(n, min_periods=1).mean()
    # C. 持續性：最近 N 日中 ≥ 門檻的天數比例 × 100
    for n, thr in ((5, 35), (5, 50), (10, 35)):
        v[f"C. 近{n}日達{thr}的比例"] = (sc >= thr).rolling(n, min_periods=1).mean() * 100
    # D. 斜率：5 日變化
    v["D. 5日變化量（純方向）"] = sc.diff(5)
    # E. 組合：3日均 + 上升動能加權
    ma3 = sc.rolling(3, min_periods=1).mean()
    slope5 = sc.diff(5).clip(lower=0)
    v["E. 3日均 + 上升動能"] = ma3 + slope5 * 0.5
    v["E2. 3日均 ×(1+上升動能/50)"] = ma3 * (1 + slope5.clip(0, 50) / 50)
    return v


def sustained_event_check(sc, price, events, thr, need_days=2, window=20):
    """事件覆蓋：崩盤前 window 日內，是否有「連續/多日」達門檻（而非單日尖峰）。"""
    hits_any, hits_sustained = 0, 0
    for e in events:
        pk = e["peak_date"]
        prior = sc.index[sc.index <= pk]
        if len(prior) == 0:
            continue
        loc = sc.index.get_loc(prior[-1])
        w = sc.iloc[max(0, loc - window):loc + 1]
        above = (w >= thr)
        if above.any():
            hits_any += 1
        # 是否有 need_days 天(不必連續)達標
        if above.sum() >= need_days:
            hits_sustained += 1
    return hits_any, hits_sustained, len(events)


def find_drawdowns(price, min_decline=5.0):
    p, idx = price.values, price.index
    events, peak_i, i = [], 0, 1
    while i < len(p):
        if p[i] > p[peak_i]:
            peak_i = i; i += 1; continue
        if (p[i] / p[peak_i] - 1) * 100 <= -min_decline:
            j = i; trough_i = i
            while j < len(p) and p[j] < p[peak_i]:
                if p[j] < p[trough_i]:
                    trough_i = j
                j += 1
            events.append({"peak_date": idx[peak_i], "trough_date": idx[trough_i],
                           "decline_pct": (p[trough_i] / p[peak_i] - 1) * 100})
            peak_i = j if j < len(p) else len(p) - 1
            i = j
        else:
            i += 1
    return events


def run(sc, price, name, sample_name, base_thr):
    print("\n" + "=" * 100)
    print(f"  {name}  —  {sample_name}")
    print("=" * 100)
    lab, fwd = make_labels(sc.index, price, horizon=10, thresh=-4.0)
    sc_al = sc.loc[lab.index]
    base = lab.mean()
    print(f"  樣本 {len(lab)} 日 | 事件（未來10日跌>4%）基準率 {base*100:.1f}%")
    print(f"\n  {'讀法':<26}{'AUC':>8}{'精確@5%':>10}{'精確@10%':>10}{'精確@20%':>10}   相對基準")
    print("  " + "-" * 90)

    results = {}
    for vname, series in variants(sc).items():
        s = series.loc[lab.index]
        a = roc_auc(s.values, lab.values)
        p5, _ = precision_at_rate(s.values, lab.values, 0.05)
        p10, _ = precision_at_rate(s.values, lab.values, 0.10)
        p20, _ = precision_at_rate(s.values, lab.values, 0.20)
        lift = p10 / base if base > 0 else np.nan
        star = " ⭐" if a >= 0.70 else (" ✅" if a >= 0.65 else "")
        print(f"  {vname:<26}{a:>8.3f}{p5*100:>9.0f}%{p10*100:>9.0f}%{p20*100:>9.0f}%"
              f"{lift:>9.1f}x{star}")
        results[vname] = (a, p10)

    # 最佳 vs 原始
    baseline = results["A. 原始每日分數（現況）"]
    best_name = max(results, key=lambda k: results[k][0])
    best = results[best_name]
    print("  " + "-" * 90)
    print(f"  最佳讀法：{best_name}")
    print(f"     AUC {baseline[0]:.3f} → {best[0]:.3f} ({(best[0]-baseline[0])*100:+.1f} 點)"
          f" | 精確率@10% {baseline[1]*100:.0f}% → {best[1]*100:.0f}%")

    # 事件層級：單日尖峰 vs 持續警訊
    events = find_drawdowns(price[(price.index >= sc.index[0]) & (price.index <= sc.index[-1])], 5.0)
    print(f"\n  【關鍵檢驗】事件前20日的警訊品質（共 {len(events)} 次回檔）")
    print(f"  {'門檻':>8}{'曾單日達標':>12}{'≥2日達標':>12}{'≥4日達標':>12}   解讀")
    for thr in (base_thr, base_thr + 15):
        a1, s2, n = sustained_event_check(sc, price, events, thr, 2)
        _, s4, _ = sustained_event_check(sc, price, events, thr, 4)
        note = "單日尖峰灌水嚴重" if a1 > s2 + 1 else "警訊品質穩定"
        print(f"  {thr:>8}{a1:>10}/{n}{s2:>10}/{n}{s4:>10}/{n}   {note}")
    return results


if __name__ == "__main__":
    h = json.load(open(HISTORY))
    hist = pd.DataFrame({"cri": h["c"], "tsi": h["t"]},
                        index=pd.to_datetime(h["d"])).sort_index()
    spy_m = load_ext("SPY")
    qqq_m = load_ext("QQQ")
    ov_end = min(hist.index[-1], spy_m.index[-1])
    hm = hist[(hist.index >= hist.index[0]) & (hist.index <= ov_end)]

    run(hm["cri"], spy_m, "CRI 讀法改良實測", "現代樣本 2021-2026", 35)
    run(hm["tsi"], qqq_m, "TSI 讀法改良實測", "現代樣本 2021-2026", 40)

    # 舊樣本交叉驗證（1996-2020），確認改良不是過度配適現代資料
    print("\n\n" + "#" * 100)
    print("#  交叉驗證：同樣的改良套用到 1996-2020 舊樣本（確認不是過度配適）")
    print("#" * 100)
    cri_old = pd.read_csv(os.path.join(BT, "cri_history.csv"),
                          parse_dates=["date"]).set_index("date")["score"].sort_index()
    spy_old = pd.read_csv(os.path.join(BT, "SPY.csv"))
    spy_old["Date"] = pd.to_datetime(spy_old["Date"])
    spy_old = spy_old.set_index("Date").sort_index()
    spy_old = (spy_old["Adj Close"] if "Adj Close" in spy_old.columns
               else spy_old["Close"]).dropna()
    run(cri_old, spy_old, "CRI 讀法改良實測", "舊樣本 1996-2020", 35)
