#!/usr/bin/env python3
"""
modern_validation.py — 現代樣本（2021-2026）實戰驗證

回答：「過去幾次市場比較大的跌幅，KIWI 到底有沒有預判效果？」

與 factor_audit.py 的差別：
  - factor_audit 用 1996-2020 的因子級歷史做「因子有效性」檢討
  - 本腳本用 docs/history.json（2021-2026 的實際 CRI/TSI 分數）
    對照 data/ext/ 的真實 SPY/QQQ 價格，做「近年實戰」驗證

重點分析：
  1. 自動辨識所有重大回檔事件（峰→谷 ≥5%），不靠人工挑事件避免選擇偏誤
  2. 每次事件：下跌開始前 CRI/TSI 的實際讀數與首次預警時點
  3. 現代樣本 AUC vs 舊樣本 AUC —— 檢查指數是否隨時間退化
  4. 假警報分析：亮燈但沒跌的次數

用法：python scripts/modern_validation.py
"""
import os
import json
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(BASE, "data", "ext")
HISTORY = os.path.abspath(os.path.join(BASE, "..", "..", "docs", "history.json"))

CRI_LEVELS = [(20, "MODERATE"), (35, "ELEVATED"), (50, "HIGH"), (70, "CRITICAL")]
TSI_LEVELS = [(22, "NEUTRAL"), (40, "CAUTIOUS"), (60, "BEARISH")]


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
    s_sorted = scores[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
        i = j + 1
    return (ranks[labels == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def load_ext(name):
    df = pd.read_csv(os.path.join(EXT, f"{name}.csv"))
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    return df[col].dropna()


def find_drawdowns(price, min_decline=5.0, min_gap_days=10):
    """自動辨識峰→谷回檔事件（不人工挑選，避免選擇偏誤）。

    做法：走訪價格序列，記錄執行中的高點；當自高點回落 ≥ min_decline%
    即認定為一次事件，記錄「高點日」（= 下跌開始前最後一個好日子）與谷底。
    """
    p = price.values
    idx = price.index
    events = []
    peak_i = 0
    i = 1
    while i < len(p):
        if p[i] > p[peak_i]:
            peak_i = i
            i += 1
            continue
        dd = (p[i] / p[peak_i] - 1) * 100
        if dd <= -min_decline:
            # 找這波的谷底：往後走到創新高之前的最低點
            j = i
            trough_i = i
            while j < len(p) and p[j] < p[peak_i]:
                if p[j] < p[trough_i]:
                    trough_i = j
                j += 1
            events.append({
                "peak_date": idx[peak_i], "peak_px": p[peak_i],
                "trough_date": idx[trough_i], "trough_px": p[trough_i],
                "decline_pct": (p[trough_i] / p[peak_i] - 1) * 100,
                "days": trough_i - peak_i,
            })
            peak_i = j if j < len(p) else len(p) - 1
            i = j
        else:
            i += 1
    # 合併間隔太近的事件
    merged = []
    for e in events:
        if merged and (e["peak_date"] - merged[-1]["trough_date"]).days < min_gap_days:
            if e["decline_pct"] < merged[-1]["decline_pct"]:
                merged[-1] = e
        else:
            merged.append(e)
    return merged


def level_of(score, levels, base="LOW"):
    name = base
    for thr, nm in levels:
        if score >= thr:
            name = nm
    return name


def analyse(index_key, index_name, hist_df, price, events, levels, warn_thr):
    print("\n" + "=" * 100)
    print(f"  {index_name} — 近年重大回檔實戰驗證（預警門檻 = {warn_thr}）")
    print("=" * 100)

    sc = hist_df[index_key].dropna()

    def at_offset(peak_date, off):
        """峰值日往前 off 個『有分數的交易日』的讀數。"""
        prior = sc.index[sc.index <= peak_date]
        if len(prior) == 0:
            return None
        loc = sc.index.get_loc(prior[-1]) - off
        return float(sc.iloc[loc]) if 0 <= loc < len(sc) else None

    print(f"\n  {'事件（峰→谷）':<26}{'跌幅':>7}{'天':>4} │{'D-10':>6}{'D-5':>6}{'D-3':>6}{'D-1':>6}{'D0':>6}"
          f" │{'谷底前峰值':>9}  首次預警")
    print("  " + "-" * 96)

    rows = []
    for e in events:
        pk, tr = e["peak_date"], e["trough_date"]
        offs = {o: at_offset(pk, o) for o in (10, 5, 3, 1, 0)}

        # 下跌途中（峰→谷）的最高分
        during = sc[(sc.index >= pk) & (sc.index <= tr)]
        peak_score = float(during.max()) if len(during) else None

        # 首次預警：峰值日前 20 個交易日內首次 ≥ warn_thr
        lead = None
        prior = sc.index[sc.index <= pk]
        if len(prior):
            loc = sc.index.get_loc(prior[-1])
            w = sc.iloc[max(0, loc - 20):loc + 1]
            hits = w[w >= warn_thr]
            if len(hits):
                lead = loc - sc.index.get_loc(hits.index[0])

        f = lambda v: f"{v:>6.0f}" if v is not None else "    --"
        label = f"{pk.date()}→{tr.date()}"
        warn = f"D-{lead}" if lead is not None else "❌ 無"
        print(f"  {label:<26}{e['decline_pct']:>6.1f}%{e['days']:>4} │"
              f"{f(offs[10])}{f(offs[5])}{f(offs[3])}{f(offs[1])}{f(offs[0])} │"
              f"{f(peak_score):>9}  {warn:>8}")
        rows.append(dict(peak=pk, trough=tr, decline=e["decline_pct"],
                         lead=lead, peak_score=peak_score, d0=offs[0], d1=offs[1]))

    det = [r for r in rows if r["lead"] is not None]
    big = [r for r in rows if r["decline"] <= -8]
    big_det = [r for r in big if r["lead"] is not None]
    print("  " + "-" * 96)
    print(f"  事前預警率（峰值前20日內達 {warn_thr}）：{len(det)}/{len(rows)} = "
          f"{len(det)/max(len(rows),1)*100:.0f}%"
          + (f"   平均提前 {np.mean([r['lead'] for r in det]):.1f} 個交易日" if det else ""))
    if big:
        print(f"  其中【跌幅 ≥8% 的大跌】：{len(big_det)}/{len(big)} = "
              f"{len(big_det)/len(big)*100:.0f}% 有事前預警")
    # 下跌途中是否至少亮燈（同步偵測，非預警）
    during_hit = [r for r in rows if r["peak_score"] is not None and r["peak_score"] >= warn_thr]
    print(f"  下跌途中曾達門檻（同步偵測，不算預警）：{len(during_hit)}/{len(rows)} = "
          f"{len(during_hit)/max(len(rows),1)*100:.0f}%")
    return rows


def auc_by_era(hist_df, key, price, label_thr=-5.0, horizon=5):
    """分期 AUC：檢查指數是否隨時間退化。"""
    sc = hist_df[key].dropna()
    dates = sc.index
    fwd = pd.Series(index=dates, dtype=float)
    pidx = price.index
    for d in dates:
        prior = pidx[pidx <= d]
        if len(prior) == 0:
            continue
        loc = pidx.get_loc(prior[-1])
        if loc + horizon >= len(price):
            continue
        fwd[d] = (price.iloc[loc + 1:loc + 1 + horizon].min() / price.iloc[loc] - 1) * 100
    lab = (fwd <= label_thr).astype(int)[fwd.notna()]
    out = {}
    for name, (a, b) in {
        "2021下-2022 (熊市)": ("2021-06-01", "2022-12-31"),
        "2023 (SVB/升息)":    ("2023-01-01", "2023-12-31"),
        "2024 (日圓套利)":    ("2024-01-01", "2024-12-31"),
        "2025":               ("2025-01-01", "2025-12-31"),
        "2026 迄今":          ("2026-01-01", "2026-12-31"),
    }.items():
        m = (lab.index >= a) & (lab.index <= b)
        sub_lab, sub_sc = lab[m], sc.loc[lab.index[m]]
        if sub_lab.sum() >= 3 and len(sub_lab) > 30:
            out[name] = (roc_auc(sub_sc.values, sub_lab.values),
                         int(sub_lab.sum()), len(sub_lab))
        else:
            out[name] = (np.nan, int(sub_lab.sum()), len(sub_lab))
    overall = roc_auc(sc.loc[lab.index].values, lab.values)
    return out, overall, lab.mean()


if __name__ == "__main__":
    spy = load_ext("SPY")
    qqq = load_ext("QQQ")
    h = json.load(open(HISTORY))
    hist = pd.DataFrame({"cri": h["c"], "tsi": h["t"], "avi": h["a"]},
                        index=pd.to_datetime(h["d"])).sort_index()
    print(f"指數歷史：{hist.index[0].date()} → {hist.index[-1].date()} ({len(hist)} 筆)")
    print(f"SPY 價格：{spy.index[0].date()} → {spy.index[-1].date()}")
    ov = hist.index.intersection(spy.index)
    print(f"重疊可驗證區間：{ov[0].date()} → {ov[-1].date()} ({len(ov)} 個交易日)")

    print("\n" + "=" * 100)
    print("  自動辨識的重大回檔事件（SPY 峰→谷 ≥5%，程式自動掃描，非人工挑選）")
    print("=" * 100)
    spy_win = spy[(spy.index >= hist.index[0]) & (spy.index <= min(hist.index[-1], spy.index[-1]))]
    events = find_drawdowns(spy_win, 5.0)
    for e in events:
        print(f"  {e['peak_date'].date()} → {e['trough_date'].date()}  "
              f"{e['decline_pct']:>6.1f}%  歷時 {e['days']:>3} 交易日")
    print(f"  共 {len(events)} 次；其中 ≥8% 者 {sum(1 for e in events if e['decline_pct'] <= -8)} 次")

    cri_rows = analyse("cri", "CRI（大盤崩盤風險）", hist, spy, events, CRI_LEVELS, 35)
    cri_rows_h = analyse("cri", "CRI — 改用 HIGH(50) 作為門檻", hist, spy, events, CRI_LEVELS, 50)

    qqq_win = qqq[(qqq.index >= hist.index[0]) & (qqq.index <= min(hist.index[-1], qqq.index[-1]))]
    tech_events = find_drawdowns(qqq_win, 6.0)
    print("\n" + "=" * 100)
    print(f"  QQQ 科技股回檔事件（≥6%）：{len(tech_events)} 次")
    print("=" * 100)
    for e in tech_events:
        print(f"  {e['peak_date'].date()} → {e['trough_date'].date()}  "
              f"{e['decline_pct']:>6.1f}%  歷時 {e['days']:>3} 交易日")
    tsi_rows = analyse("tsi", "TSI（科技板塊壓力）", hist, qqq, tech_events, TSI_LEVELS, 40)

    # ── 分期 AUC：退化檢查 ──
    print("\n" + "=" * 100)
    print("  分期預測力 AUC（未來5日跌幅>5%）— 檢查指數是否隨時間退化")
    print("=" * 100)
    for key, nm, px in (("cri", "CRI", spy), ("tsi", "TSI", qqq)):
        eras, overall, base = auc_by_era(hist, key, px)
        print(f"\n  【{nm}】現代樣本整體 AUC = {overall:.3f}（事件基準率 {base*100:.1f}%）")
        for era, (a, npos, n) in eras.items():
            s = f"{a:.3f}" if not np.isnan(a) else "樣本不足"
            flag = ""
            if not np.isnan(a):
                flag = " ⭐" if a >= 0.70 else (" ✅" if a >= 0.60 else
                                               (" 🟡" if a >= 0.55 else " ❌"))
            print(f"      {era:<22} AUC {s:>9}   (事件 {npos:>2}/{n:>3} 日){flag}")

    # ── 假警報 ──
    print("\n" + "=" * 100)
    print("  假警報分析（現代樣本）")
    print("=" * 100)
    for key, nm, px, thrs in (("cri", "CRI", spy, [35, 50, 70]),
                              ("tsi", "TSI", qqq, [40, 60])):
        sc = hist[key].dropna()
        pidx = px.index
        fwd = {}
        for d in sc.index:
            prior = pidx[pidx <= d]
            if len(prior) == 0:
                continue
            loc = pidx.get_loc(prior[-1])
            if loc + 10 >= len(px):
                continue
            fwd[d] = (px.iloc[loc + 1:loc + 11].min() / px.iloc[loc] - 1) * 100
        fwd = pd.Series(fwd)
        print(f"\n  【{nm}】")
        print(f"      {'門檻':>8}{'亮燈日數':>10}{'佔比':>8}{'後10日真跌>4%':>15}{'精確率':>9}{'空包彈率':>10}")
        for t in thrs:
            hit = sc.loc[fwd.index] >= t
            n_hit = int(hit.sum())
            if n_hit == 0:
                print(f"      {t:>8}{0:>10}{'0%':>8}{'—':>15}{'—':>9}{'—':>10}")
                continue
            real = int((fwd[hit.values] <= -4.0).sum())
            prec = real / n_hit
            print(f"      {t:>8}{n_hit:>10}{n_hit/len(sc)*100:>7.0f}%{real:>15}"
                  f"{prec*100:>8.0f}%{(1-prec)*100:>9.0f}%")
