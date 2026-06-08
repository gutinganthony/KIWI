#!/usr/bin/env python3
"""
real_backtest.py — TSI 真實數據回測引擎

使用真實歷史數據（jacksoncrow Kaggle 1993-2020 + CBOE VIX/VVIX 1990-2025）
逐日計算 TSI，客觀評估：
  1. 各歷史崩盤事件，TSI 是否提前發出警示？提前幾天？
  2. 假警報率（TSI 高但後續沒崩盤的比例）
  3. 各別指標的預測力排名（哪些指標真的有領先效果）

資料來源（已下載至 data/backtest/）：
  ETF/股票: Date,Open,High,Low,Close,Adj Close,Volume
  VIX:      DATE,OPEN,HIGH,LOW,CLOSE  (M/D/YYYY)
  VVIX:     DATE,VVIX                 (M/D/YYYY)

用法：
  python scripts/real_backtest.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from src.tsi import TechStressIndex

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "backtest")

# ─── 資料載入 ────────────────────────────────────────────────────────────────

def load_ohlc(ticker):
    """載入 ETF/股票 收盤價序列。"""
    df = pd.read_csv(os.path.join(DATA, f"{ticker}.csv"))
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()
    # 用 Adj Close（已調整股息/分割）較準確；若無則用 Close
    col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
    return df[col].dropna()

def load_vix():
    df = pd.read_csv(os.path.join(DATA, "VIX.csv"))
    df['DATE'] = pd.to_datetime(df['DATE'], format='%m/%d/%Y')
    df = df.set_index('DATE').sort_index()
    return df['CLOSE'].dropna()

def load_vvix():
    df = pd.read_csv(os.path.join(DATA, "VVIX.csv"))
    df['DATE'] = pd.to_datetime(df['DATE'], format='%m/%d/%Y')
    df = df.set_index('DATE').sort_index()
    return df['VVIX'].dropna()

print("載入真實歷史數據中...")
data = {
    'SPY':  load_ohlc('SPY'),
    'QQQ':  load_ohlc('QQQ'),
    'HYG':  load_ohlc('HYG'),
    'SOXX': load_ohlc('SOXX'),
    'SMH':  load_ohlc('SMH'),
    'MU':   load_ohlc('MU'),
    'VIX':  load_vix(),
    'VVIX': load_vvix(),
}
for k, v in data.items():
    print(f"  {k:5}: {len(v):5} 筆  {v.index[0].date()} → {v.index[-1].date()}")

# 共同交易日（以 SPY 為基準，因為所有崩盤都看 SPY/QQQ）
spy = data['SPY']
qqq = data['QQQ']

# ─── 崩盤事件定義 ─────────────────────────────────────────────────────────────

def find_crash_events(price, fwd_window=5, threshold=-0.06, min_gap=15):
    """找出崩盤事件的「起始日」。

    崩盤起始日 = 該日之後 fwd_window 天內累積跌幅超過 threshold，
    且為該段下跌的第一天（與前一個崩盤起始日間隔 >= min_gap 交易日）。

    回傳：崩盤起始日列表
    """
    fwd_ret = price.shift(-fwd_window) / price - 1
    crash_days = fwd_ret[fwd_ret <= threshold].index.tolist()

    # 聚類：相近的崩盤日只取第一天
    events = []
    last = None
    for d in crash_days:
        if last is None or (price.index.get_loc(d) - price.index.get_loc(last)) >= min_gap:
            events.append(d)
            last = d
    return events

# 主要崩盤：SPY 未來 5 日跌幅 > 6%（突發型）
spy_crashes = find_crash_events(spy, fwd_window=5, threshold=-0.06, min_gap=20)
# 科技崩盤：QQQ 未來 5 日跌幅 > 8%
qqq_crashes = find_crash_events(qqq, fwd_window=5, threshold=-0.08, min_gap=20)

print(f"\n偵測到 SPY 突發崩盤事件：{len(spy_crashes)} 次")
print(f"偵測到 QQQ 科技崩盤事件：{len(qqq_crashes)} 次")

# ─── TSI 逐日計算（全期間）──────────────────────────────────────────────────

def get_window(series, end_date, n=260):
    """取得 end_date（含）之前最多 n 個交易日的資料。"""
    s = series[series.index <= end_date]
    return s.tail(n)

def compute_tsi_on(date):
    """在指定日期計算 TSI（用該日之前的資料）。"""
    tsi = TechStressIndex()
    try:
        vix_w = get_window(data['VIX'], date, 260)
        if len(vix_w) < 30:
            return None
        # VVIX/HYG 可能在早期不存在 → 傳 None，引擎會用替代
        vvix_w = get_window(data['VVIX'], date, 260)
        hyg_w  = get_window(data['HYG'], date, 260)
        vvix_arg = vvix_w if len(vvix_w) >= 20 else None
        hyg_arg  = hyg_w if len(hyg_w) >= 10 else None

        # SOXX 早期不存在 → 用 SMH 或 QQQ
        soxx_w = get_window(data['SOXX'], date, 260)
        if len(soxx_w) < 20:
            soxx_w = get_window(data['SMH'], date, 260)
        if len(soxx_w) < 20:
            soxx_w = get_window(data['QQQ'], date, 260)

        # 10Y 殖利率沒有歷史檔 → 用常數（殖利率類指標在此回測中停用）
        vix_idx = vix_w.index
        t10y = pd.Series(0.03, index=vix_idx)

        result = tsi.compute(
            sox_daily    = soxx_w,
            qqq_daily    = get_window(data['QQQ'], date, 260),
            mu_daily     = get_window(data['MU'], date, 260),
            smh_daily    = get_window(data['SMH'], date, 260),
            spy_daily    = get_window(data['SPY'], date, 260),
            treasury_10y = t10y,
            vix_daily    = vix_w,
            vvix_daily   = vvix_arg,
            hyg_daily    = hyg_arg,
        )
        return result
    except Exception as e:
        return None

# 為效率：只在 1996 之後計算（早期 ETF 資料不全）
# 計算全期間每日 TSI，存成 DataFrame
print("\n逐日計算 TSI（這會花一點時間）...")
eval_dates = spy.index[(spy.index >= '2006-01-01')]  # VVIX 從 2006 起才完整

records = []
for i, d in enumerate(eval_dates):
    if i % 500 == 0:
        print(f"  進度 {i}/{len(eval_dates)} ({d.date()})")
    r = compute_tsi_on(d)
    if r is None:
        continue
    m = {ind.name: ind.signal for ind in r.indicators}
    records.append({
        'date': d, 'score': r.score, 'bias': r.bias, 'flash': r.flash_alert,
        **{k: m.get(k, 0) for k in [
            'vvix_lead', 'credit_divergence', 'sox_momentum_decel',
            'tech_crash_day', 'vix_tech_correlation', 'sox_qqq_divergence',
            'memory_momentum', 'tech_breadth',
        ]}
    })

tsi_df = pd.DataFrame(records).set_index('date')
print(f"完成：{len(tsi_df)} 個交易日的 TSI 數值")

# 存檔供後續分析
tsi_df.to_csv(os.path.join(DATA, 'tsi_history.csv'))
print(f"已存：data/backtest/tsi_history.csv")

# ─── 評估 1：崩盤前 TSI 領先分析 ────────────────────────────────────────────

def analyze_lead(crashes, label, score_threshold=45, lookback=10):
    """對每個崩盤事件，計算 TSI 在崩盤前幾天首次超過閾值。"""
    print(f"\n{'='*72}")
    print(f"  {label}（TSI 分數 >= {score_threshold} 視為警示）")
    print(f"{'='*72}")
    print(f"  {'崩盤起始日':<12}  {'前5日SPY':>8}  {'崩盤日TSI':>9}  {'首次警示':>9}  {'領先天數':>8}")
    print(f"  {'-'*60}")

    lead_times = []
    detected = 0
    for cd in crashes:
        if cd not in tsi_df.index:
            continue
        loc = tsi_df.index.get_loc(cd)
        if loc < lookback:
            continue
        window = tsi_df.iloc[loc-lookback:loc+1]
        score_at_crash = tsi_df.iloc[loc]['score']

        # 崩盤前的跌幅參考
        sloc = spy.index.get_loc(cd)
        fwd5 = (spy.iloc[min(sloc+5, len(spy)-1)] / spy.iloc[sloc] - 1) * 100

        # 找崩盤日（含）之前，首次超過閾值的日子
        above = window[window['score'] >= score_threshold]
        if len(above) > 0:
            first_warn = above.index[0]
            lead = (tsi_df.index.get_loc(cd) - tsi_df.index.get_loc(first_warn))
            lead_times.append(lead)
            detected += 1
            warn_str = first_warn.date().isoformat()
            lead_str = f"{lead}d 前" if lead > 0 else "當日"
        else:
            warn_str = "未觸發"
            lead_str = "—"

        print(f"  {cd.date()}  {fwd5:>7.1f}%  {score_at_crash:>8.1f}  {warn_str:>11}  {lead_str:>10}")

    n = len([c for c in crashes if c in tsi_df.index])
    print(f"  {'-'*60}")
    print(f"  偵測率：{detected}/{n} ({detected/max(n,1)*100:.0f}%)")
    if lead_times:
        adv = [l for l in lead_times if l > 0]
        print(f"  平均領先天數：{np.mean(lead_times):.1f} 天")
        print(f"  提前 >=1 天的比例：{len(adv)}/{len(lead_times)} ({len(adv)/len(lead_times)*100:.0f}%)")
    return lead_times

spy_leads = analyze_lead(spy_crashes, "SPY 突發崩盤事件", score_threshold=45, lookback=10)
qqq_leads = analyze_lead(qqq_crashes, "QQQ 科技崩盤事件", score_threshold=45, lookback=10)

# ─── 評估 2：假警報率 ────────────────────────────────────────────────────────

print(f"\n{'='*72}")
print(f"  假警報率分析（TSI 高警示後，是否真的崩盤）")
print(f"{'='*72}")

for thr in [45, 55, 60]:
    warn_days = tsi_df[tsi_df['score'] >= thr].index
    # 對每個警示日，檢查未來 10 日 SPY 是否跌 > 4%
    hits = 0
    for wd in warn_days:
        sloc = spy.index.get_loc(spy.index[spy.index <= wd][-1])
        if sloc + 10 >= len(spy):
            continue
        fwd10_min = (spy.iloc[sloc+1:sloc+11].min() / spy.iloc[sloc] - 1) * 100
        if fwd10_min <= -4:
            hits += 1
    n = len(warn_days)
    if n > 0:
        print(f"  TSI>={thr}: 警示 {n:4} 天，其中 {hits:4} 天後續10日內跌>4% "
              f"(命中率 {hits/n*100:.0f}%, 佔全期 {n/len(tsi_df)*100:.0f}%的時間在警示)")

# ─── 評估 3：各指標預測力排名 ────────────────────────────────────────────────

print(f"\n{'='*72}")
print(f"  各別指標預測力排名（崩盤前 1-3 天平均訊號強度）")
print(f"{'='*72}")

all_crashes = sorted(set(spy_crashes + qqq_crashes))
indicators = ['vvix_lead', 'credit_divergence', 'sox_momentum_decel',
              'tech_crash_day', 'vix_tech_correlation', 'sox_qqq_divergence',
              'memory_momentum', 'tech_breadth']

ind_stats = {}
for ind in indicators:
    pre_crash_vals = []   # 崩盤前 1-3 天的訊號
    baseline_vals = tsi_df[ind].mean()  # 全期平均（基準）
    for cd in all_crashes:
        if cd not in tsi_df.index:
            continue
        loc = tsi_df.index.get_loc(cd)
        if loc < 3:
            continue
        pre = tsi_df.iloc[loc-3:loc][ind].mean()  # D-3~D-1 平均
        pre_crash_vals.append(pre)
    if pre_crash_vals:
        avg_pre = np.mean(pre_crash_vals)
        # 預測力 = 崩盤前訊號 / 全期基準（越高代表越能區分崩盤）
        lift = avg_pre / max(baseline_vals, 1)
        ind_stats[ind] = (avg_pre, baseline_vals, lift)

print(f"  {'指標':<24}  {'崩盤前D-3~D-1':>12}  {'全期基準':>9}  {'提升倍數':>8}")
print(f"  {'-'*60}")
for ind, (pre, base, lift) in sorted(ind_stats.items(), key=lambda x: -x[1][2]):
    leading = "⏩" if ind in ('vvix_lead','credit_divergence','sox_momentum_decel') else "  "
    print(f"  {leading} {ind:<22}  {pre:>11.1f}  {base:>8.1f}  {lift:>7.2f}x")

print(f"\n{'='*72}")
print("  說明：提升倍數 > 1.5x 代表該指標在崩盤前確實顯著升高（有預測力）")
print("       提升倍數 ≈ 1.0x 代表該指標崩盤前後沒差別（無預測力）")
print(f"{'='*72}")
