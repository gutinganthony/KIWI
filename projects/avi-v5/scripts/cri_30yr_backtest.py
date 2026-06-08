#!/usr/bin/env python3
"""
cri_30yr_backtest.py — CRI v2 近 30 年崩盤預警有效性回測

用真實 SPY(1993-)+VIX(1990-) 數據，逐日計算 CRI v2 分數，並針對
1994-2020 每一次重大市場崩盤，檢視 CRI 是否「在崩盤前」就升高警示。

對每個崩盤事件輸出：
  - 崩盤前 D-10 / D-5 / D-3 / D-1 / D-0 的 CRI 分數與等級
  - 第一次觸發 ELEVATED(≥35) 的日期與提前天數（領先預警時間）
  - 崩盤窗內 CRI 峰值

並計算整體：偵測率、平均提前天數、假警報率。

CRI 等級門檻：LOW<20  MODERATE 20  ELEVATED 35  HIGH 50  CRITICAL≥70
回測停用需債券/利率的 3 指標（credit_acceleration / yield_*），與既有
cri_backtest.py 一致；可測的 9 個 SPY+VIX 指標即 CRI v2 主力。

用法：python scripts/cri_30yr_backtest.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from src.cpi import CrashProbabilityIndex

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "backtest")
ELEVATED, HIGH, CRITICAL = 35.0, 50.0, 70.0

# ─── 載入真實數據 ────────────────────────────────────────────────────────────

def load_sp500():
    df = pd.read_csv(os.path.join(DATA, "SPY.csv"))
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()
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
spy_close = sp500['close']
print(f"  SPY: {len(sp500)} 筆  {sp500.index[0].date()} → {sp500.index[-1].date()}")
print(f"  VIX: {len(vix)} 筆  {vix.index[0].date()} → {vix.index[-1].date()}")

# ─── 逐日計算 CRI v2 ─────────────────────────────────────────────────────────

cri = CrashProbabilityIndex()

def get_win(series, end, n=300):
    s = series[series.index <= end]
    return s.tail(n)

def compute_cri_on(date):
    try:
        sp_w = sp500[sp500.index <= date].tail(300)
        if len(sp_w) < 210:
            return None
        vix_w = get_win(vix, date, 300)
        if len(vix_w) < 70:
            return None
        return cri.compute(
            sp500_daily=sp_w, vix_daily=vix_w, vix3m_daily=None,
            baa_daily=empty, aaa_daily=empty,
            treasury_10y=empty, treasury_2y=empty,
        )
    except Exception:
        return None

CACHE = os.path.join(DATA, "cri_history_30yr.csv")
if os.path.exists(CACHE):
    print(f"\n讀取既有快取 {os.path.basename(CACHE)}")
    cri_df = pd.read_csv(CACHE, parse_dates=['date']).set_index('date')
else:
    print("\n逐日計算 CRI v2（1994-2020，約需 1-2 分鐘）...")
    eval_dates = spy_close.index[(spy_close.index >= '1994-01-01') & (spy_close.index <= '2020-04-01')]
    records = []
    for i, d in enumerate(eval_dates):
        if i % 1000 == 0:
            print(f"  進度 {i}/{len(eval_dates)} ({d.date()})")
        r = compute_cri_on(d)
        if r is None:
            continue
        records.append({'date': d, 'score': r.score})
    cri_df = pd.DataFrame(records).set_index('date')
    cri_df.to_csv(CACHE)
    print(f"完成：{len(cri_df)} 個交易日 → 已存 {os.path.basename(CACHE)}")

print(f"  CRI 涵蓋：{cri_df.index[0].date()} → {cri_df.index[-1].date()}  ({len(cri_df)} 日)")

# ─── 重大崩盤事件清單（1994-2020）────────────────────────────────────────────
# 日期 = 崩盤「主跌段起點」（D-0），以該日之後的急跌定義。

CRASHES = [
    ("1997-10-27", "1997 亞洲金融風暴（道指單日-7.2%）"),
    ("1998-08-31", "1998 LTCM/俄債危機"),
    ("2000-04-14", "2000 網路泡沫首波重挫"),
    ("2001-09-17", "2001 911 復市崩跌"),
    ("2002-07-19", "2002 企業醜聞熊市急跌"),
    ("2008-09-15", "2008 雷曼倒閉金融海嘯"),
    ("2010-05-06", "2010 閃電崩盤 Flash Crash"),
    ("2011-08-04", "2011 美債降評/歐債危機"),
    ("2015-08-21", "2015 人民幣貶值閃崩"),
    ("2018-02-05", "2018 Volmageddon 波動率末日"),
    ("2018-12-14", "2018 聖誕節崩跌"),
    ("2020-02-24", "2020 COVID-19 全球股災"),
]

def level_name(s):
    if s >= CRITICAL: return "CRITICAL"
    if s >= HIGH:     return "HIGH"
    if s >= ELEVATED: return "ELEVATED"
    if s >= 20:       return "MODERATE"
    return "LOW"

def nearest_score(target_date):
    """回傳該日期（或之前最近交易日）的 CRI 分數。"""
    idx = cri_df.index[cri_df.index <= target_date]
    if len(idx) == 0:
        return None, None
    d = idx[-1]
    return float(cri_df.loc[d, 'score']), d

def score_at_offset(crash_date, offset_days):
    """崩盤前第 offset 個『交易日』的 CRI（offset 為正=之前）。"""
    if crash_date not in cri_df.index:
        # 對齊到 <= crash_date 的最近交易日
        prior = cri_df.index[cri_df.index <= crash_date]
        if len(prior) == 0:
            return None
        base_loc = cri_df.index.get_loc(prior[-1])
    else:
        base_loc = cri_df.index.get_loc(crash_date)
    loc = base_loc - offset_days
    if loc < 0 or loc >= len(cri_df):
        return None
    return float(cri_df.iloc[loc]['score'])

def first_warning(crash_date, lookback=20, thr=ELEVATED):
    """崩盤前 lookback 交易日內，第一次 CRI≥thr 的日期與提前天數。"""
    prior = cri_df.index[cri_df.index <= crash_date]
    if len(prior) == 0:
        return None, None
    base_loc = cri_df.index.get_loc(prior[-1])
    start = max(0, base_loc - lookback)
    window = cri_df.iloc[start:base_loc + 1]
    hits = window[window['score'] >= thr]
    if len(hits) == 0:
        return None, None
    first_day = hits.index[0]
    lead = base_loc - cri_df.index.get_loc(first_day)
    return first_day, lead

# ─── 逐事件報表 ──────────────────────────────────────────────────────────────

print(f"\n{'='*86}")
print(f"  CRI v2 近 30 年崩盤前預警明細（1994-2020，共 {len(CRASHES)} 次重大崩盤）")
print(f"  等級：LOW<20  MODERATE≥20  ELEVATED≥35  HIGH≥50  CRITICAL≥70")
print(f"{'='*86}")
hdr = f"  {'崩盤事件':<30}{'D-10':>7}{'D-5':>7}{'D-3':>7}{'D-1':>7}{'D0':>7}{'峰值':>7}  {'首次預警':>10}"
print(hdr)
print(f"  {'-'*82}")

summary_rows = []
for cdate_s, name in CRASHES:
    cdate = pd.Timestamp(cdate_s)
    offs = {o: score_at_offset(cdate, o) for o in (10, 5, 3, 1, 0)}
    # 崩盤窗 [D-0, D+5] 峰值
    prior = cri_df.index[cri_df.index <= cdate]
    peak = None
    if len(prior) > 0:
        base_loc = cri_df.index.get_loc(prior[-1])
        win = cri_df.iloc[base_loc:base_loc + 6]
        if len(win):
            peak = float(win['score'].max())
    fw_day, lead = first_warning(cdate, lookback=20, thr=ELEVATED)

    def fmt(v):
        return f"{v:>6.0f}" if v is not None else "   -- "
    if fw_day is not None:
        warn_str = f"D-{lead}({level_name(score_at_offset(cdate, lead) or 0)[:4]})"
    else:
        warn_str = "(無預警)"
    print(f"  {name:<30}{fmt(offs[10])} {fmt(offs[5])} {fmt(offs[3])} {fmt(offs[1])} {fmt(offs[0])} {fmt(peak)}  {warn_str:>10}")
    summary_rows.append({
        'event': name, 'date': cdate_s,
        'd1': offs[1], 'd0': offs[0], 'peak': peak, 'lead': lead,
    })

# ─── 整體統計 ────────────────────────────────────────────────────────────────

detected = [r for r in summary_rows if r['lead'] is not None]
leads = [r['lead'] for r in detected]
print(f"\n  {'-'*82}")
print(f"  偵測率（崩盤前 20 日內 CRI≥ELEVATED）：{len(detected)}/{len(CRASHES)} = {len(detected)/len(CRASHES)*100:.0f}%")
if leads:
    print(f"  平均提前預警天數：{np.mean(leads):.1f} 個交易日（中位數 {np.median(leads):.0f}，最長 {max(leads)}）")
    print(f"  其中提前 ≥3 個交易日預警：{sum(1 for l in leads if l>=3)}/{len(detected)} 次")

# ─── 假警報分析 ──────────────────────────────────────────────────────────────
# 把每日標記為「是否其後5日內 SPY 最大跌幅>5%」，再看 CRI≥門檻時的命中率。

def fwd_min_return(window=5):
    out = pd.Series(index=cri_df.index, dtype=float)
    sc = spy_close
    for d in cri_df.index:
        prior = sc.index[sc.index <= d]
        if len(prior) == 0:
            continue
        loc = sc.index.get_loc(prior[-1])
        if loc + window >= len(sc):
            continue
        out[d] = (sc.iloc[loc+1:loc+1+window].min() / sc.iloc[loc] - 1) * 100
    return out

fwd = fwd_min_return(5)
valid = fwd.notna()
labels = (fwd[valid] <= -5.0).astype(int)
scores = cri_df.loc[labels.index, 'score']
base_rate = labels.mean()

print(f"\n{'='*86}")
print(f"  假警報 / 精確率分析（事件：未來5日 SPY 最大跌幅>5%，基準率 {base_rate*100:.1f}%）")
print(f"{'='*86}")
print(f"  {'警示門檻':<14}{'觸發天數':>10}{'其中真崩盤':>12}{'精確率':>10}{'相對基準':>10}{'召回率':>10}")
print(f"  {'-'*66}")
for thr, nm in [(ELEVATED, "ELEVATED≥35"), (HIGH, "HIGH≥50"), (CRITICAL, "CRITICAL≥70")]:
    al = scores >= thr
    n_al = int(al.sum())
    tp = int(((al) & (labels == 1)).sum())
    prec = tp / max(n_al, 1)
    recall = tp / max(int(labels.sum()), 1)
    lift = prec / base_rate if base_rate > 0 else 0
    print(f"  {nm:<14}{n_al:>10}{tp:>12}{prec*100:>9.0f}%{lift:>8.1f}x{recall*100:>9.0f}%")

print(f"\n  說明：精確率 = 警示時真的在5日內崩盤的比例；相對基準 = 比隨機猜測強幾倍。")
print(f"        '召回率' 低屬正常——CRI 只在最危險時刻警示，寧可錯過小回檔也不亂報。")
print(f"\n完成。每日 CRI 分數已存：data/backtest/{os.path.basename(CACHE)}")
