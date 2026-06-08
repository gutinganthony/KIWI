#!/usr/bin/env python3
"""
TSI v3 回測腳本 — 驗證領先指標是否能在已知崩盤事件前 1-2 天發出預警

測試場景（依歷史實際走勢建構合成資料）：
  1. 2000-03 網路泡沫頂點崩盤
  2. 2008-09 雷曼兄弟倒閉週（9/12→9/15）
  3. 2020-02 COVID 初始崩跌
  4. 2022-01 升息恐慌（Fed 鷹派轉向）
  5. 2018-12 聖誕前暴跌

評估指標：
  - 領先指標（vvix_lead, credit_divergence, sox_momentum_decel）首次觸發日
  - 反應指標（tech_crash_day, vix_tech_correlation）首次觸發日
  - 領先天數 = 領先指標觸發 - 反應指標觸發（正數代表提前）
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from src.tsi import TechStressIndex

np.random.seed(42)

# ─── 輔助函數 ────────────────────────────────────────────────────────────────

def make_crash_scenario(
    n_days=60,
    crash_day=45,          # 主崩盤日（0-indexed）
    crash_size=-0.035,     # 主崩盤當天跌幅（-3.5% → QQQ）
    lead_days=2,           # 領先指標提前幾天出現徵兆
    daily_vol=0.012,
    seed=None,
):
    """建構包含崩盤動態的合成價格序列。

    t-lead_days: VVIX 開始急升，HYG 開始乖離，SOX 動能開始衰減
    t-2:        市場仍撐住，但壓力累積中
    t-1:        小跌（-0.8%），VIX 微升
    t=crash:    主崩跌（-3.5%），VIX 爆衝
    t+1:        繼續下跌或反彈
    """
    if seed:
        np.random.seed(seed)

    dates = pd.date_range('2020-01-01', periods=n_days, freq='B')
    rng = np.random.randn(n_days) * daily_vol

    # 主體走勢：溫和上漲直到崩盤
    returns = rng.copy()
    returns[crash_day-1] += -0.008    # 前1天小跌
    returns[crash_day]   += crash_size  # 主崩盤
    if crash_day + 1 < n_days:
        returns[crash_day+1] += crash_size * 0.4  # 餘震

    def price_series(base, extra_vol=0):
        r = returns + np.random.randn(n_days) * extra_vol
        return pd.Series(base * np.cumprod(1 + r), index=dates)

    # QQQ：主跌指標
    qqq = price_series(420, 0.002)

    # SOX：領先 QQQ（提前 lead_days+1 天開始弱化）
    sox_returns = returns.copy()
    if crash_day - lead_days - 1 >= 0:
        sox_returns[crash_day - lead_days - 1] += -0.005  # SOX 先軟化
    sox_returns[crash_day - 1] += -0.006  # 前1天比 QQQ 更弱
    sox_returns[crash_day]     += crash_size * 1.1  # 崩盤更猛
    sox = pd.Series(180 * np.cumprod(1 + sox_returns + np.random.randn(n_days)*0.003), index=dates)

    # SPY：跌幅比 QQQ 小 30%
    spy_returns = returns * 0.7 + np.random.randn(n_days) * 0.005
    spy = pd.Series(450 * np.cumprod(1 + spy_returns), index=dates)

    # SMH / MU：類似 SOX
    smh = pd.Series(200 * np.cumprod(1 + sox_returns + np.random.randn(n_days)*0.005), index=dates)
    mu  = pd.Series(80  * np.cumprod(1 + sox_returns * 1.2 + np.random.randn(n_days)*0.015), index=dates)

    # VIX：平靜 → 前1天微升 → 崩盤日爆衝
    vix = pd.Series(18 + np.random.randn(n_days) * 1.5, index=dates)
    vix_vals = vix.values.copy()
    vix_vals[crash_day - 1] += 2.5
    vix_vals[crash_day]     += 10.0   # VIX +10 點
    if crash_day + 1 < n_days:
        vix_vals[crash_day + 1] += 6.0
    vix = pd.Series(np.clip(vix_vals, 10, 80), index=dates)

    # VVIX：在崩盤前 lead_days 天開始急升（領先指標核心）
    vvix = pd.Series(95 + np.random.randn(n_days) * 5, index=dates)
    vvix_vals = vvix.values.copy()
    for d in range(lead_days + 1):
        i = crash_day - lead_days + d
        if 0 <= i < n_days:
            vvix_vals[i] += (d + 1) * 8  # 逐日攀升
    vvix_vals[crash_day] += 25  # 崩盤當天最高
    vvix = pd.Series(np.clip(vvix_vals, 80, 200), index=dates)

    # HYG：在崩盤前 lead_days 天開始比 SPY 弱（信用市場領先）
    hyg_returns = spy_returns * 0.3 + np.random.randn(n_days) * 0.002
    for d in range(lead_days + 1):
        i = crash_day - lead_days + d
        if 0 <= i < n_days:
            hyg_returns[i] += -0.004  # HYG 先跌
    hyg = pd.Series(78 * np.cumprod(1 + hyg_returns), index=dates)

    # 10Y 殖利率：穩定
    t10y = pd.Series(0.045 + np.random.randn(n_days) * 0.001, index=dates)

    return dict(qqq=qqq, sox=sox, spy=spy, smh=smh, mu=mu, vix=vix,
                vvix=vvix, hyg=hyg, t10y=t10y, dates=dates, crash_day=crash_day)


def run_tsi_daily(scenario, window=30):
    """對每個交易日計算 TSI（使用該日之前 window 天的資料）。"""
    tsi_engine = TechStressIndex()
    crash_day = scenario['crash_day']
    results = []

    for i in range(window, len(scenario['dates'])):
        day = scenario['dates'][i]
        sl = slice(0, i + 1)

        try:
            result = tsi_engine.compute(
                sox_daily     = scenario['sox'].iloc[sl],
                qqq_daily     = scenario['qqq'].iloc[sl],
                mu_daily      = scenario['mu'].iloc[sl],
                smh_daily     = scenario['smh'].iloc[sl],
                spy_daily     = scenario['spy'].iloc[sl],
                treasury_10y  = scenario['t10y'].iloc[sl],
                vix_daily     = scenario['vix'].iloc[sl],
                vvix_daily    = scenario['vvix'].iloc[sl],
                hyg_daily     = scenario['hyg'].iloc[sl],
            )
        except Exception as e:
            continue

        ind_map = {ind.name: ind.signal for ind in result.indicators}
        results.append({
            'day_idx':  i,
            'rel_day':  i - crash_day,   # 相對崩盤日（負=崩盤前）
            'date':     day,
            'tsi_score': result.score,
            'bias':     result.bias,
            'flash':    result.flash_alert,
            # 領先指標
            'vvix_lead':          ind_map.get('vvix_lead', 0),
            'credit_divergence':  ind_map.get('credit_divergence', 0),
            'sox_momentum_decel': ind_map.get('sox_momentum_decel', 0),
            # 反應指標
            'tech_crash_day':     ind_map.get('tech_crash_day', 0),
            'vix_tech_corr':      ind_map.get('vix_tech_correlation', 0),
            'sox_qqq_div':        ind_map.get('sox_qqq_divergence', 0),
        })

    return pd.DataFrame(results)


def analyze_lead_time(df, crash_day_idx, threshold=30, label=""):
    """計算領先指標 vs 反應指標的觸發時間差。"""
    # 找各指標首次 >= threshold 的相對日
    leading   = ['vvix_lead', 'credit_divergence', 'sox_momentum_decel']
    reactive  = ['tech_crash_day', 'vix_tech_corr', 'sox_qqq_div']

    lead_first = {}
    for col in leading + reactive:
        fired = df[df[col] >= threshold]['rel_day']
        if len(fired) > 0:
            lead_first[col] = fired.iloc[0]
        else:
            lead_first[col] = None

    lead_days_all = []
    for lc in leading:
        for rc in reactive:
            if lead_first[lc] is not None and lead_first[rc] is not None:
                diff = lead_first[rc] - lead_first[lc]
                lead_days_all.append(diff)

    avg_lead = np.mean(lead_days_all) if lead_days_all else 0

    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    print(f"  閾值: {threshold}/100  |  參考崩盤日: rel_day=0")
    print()
    print(f"  ⏩ 領先指標首次觸發日：")
    for c in leading:
        d = lead_first[c]
        arrow = "✅" if (d is not None and d < 0) else ("⚠️" if d == 0 else "❌")
        print(f"    {arrow} {c:<28}: rel_day={d if d is not None else 'N/A'}")
    print()
    print(f"     反應指標首次觸發日：")
    for c in reactive:
        d = lead_first[c]
        print(f"       {c:<28}: rel_day={d if d is not None else 'N/A'}")
    print()
    print(f"  平均領先天數（正數=提前）: {avg_lead:.1f} 天")

    # 印出崩盤前 5 天到崩盤後 2 天的 TSI 數值
    window_df = df[(df['rel_day'] >= -5) & (df['rel_day'] <= 2)]
    if len(window_df):
        print()
        print(f"  日期          TSI分數  偏向       Flash  VVIX  CreditDiv  SOXDecel  CrashDay  VIXCorr")
        print(f"  {'─'*100}")
        for _, row in window_df.iterrows():
            flash_mark = "⚡" if row['flash'] else "  "
            print(f"  rel={int(row['rel_day']):+2d}   "
                  f"{row['tsi_score']:5.1f}   {row['bias']:<9} {flash_mark}   "
                  f"{row['vvix_lead']:4.0f}  {row['credit_divergence']:5.0f}     "
                  f"{row['sox_momentum_decel']:5.0f}    {row['tech_crash_day']:5.0f}    "
                  f"{row['vix_tech_corr']:5.0f}")

    return avg_lead


# ─── 場景定義（依歷史事件特性調整參數）────────────────────────────────────

scenarios = [
    dict(
        label    = "2000-03 網路泡沫崩盤（QQQ -7.3%/day）",
        n_days   = 70, crash_day=50, crash_size=-0.073,
        lead_days=2, daily_vol=0.020, seed=1,
    ),
    dict(
        label    = "2008-09 雷曼週（金融海嘯 -4.7%/day）",
        n_days   = 70, crash_day=50, crash_size=-0.047,
        lead_days=3, daily_vol=0.015, seed=2,
    ),
    dict(
        label    = "2020-02 COVID 初始崩跌（-3.9%/day）",
        n_days   = 70, crash_day=50, crash_size=-0.039,
        lead_days=2, daily_vol=0.012, seed=3,
    ),
    dict(
        label    = "2022-01 Fed 升息恐慌（-3.0%/day）",
        n_days   = 70, crash_day=50, crash_size=-0.030,
        lead_days=2, daily_vol=0.010, seed=4,
    ),
    dict(
        label    = "2018-12 聖誕前暴跌（-2.7%/day）",
        n_days   = 70, crash_day=50, crash_size=-0.027,
        lead_days=1, daily_vol=0.010, seed=5,
    ),
]

# ─── 執行回測 ─────────────────────────────────────────────────────────────────

print("=" * 60)
print("  TSI v3 回測 — 領先指標有效性驗證")
print("  閾值 >= 30/100 算作觸發（中等警示水準）")
print("=" * 60)

all_lead_days = []
for sc in scenarios:
    data = make_crash_scenario(**{k: v for k, v in sc.items() if k != 'label'})
    df = run_tsi_daily(data, window=30)
    avg = analyze_lead_time(df, sc['crash_day'], threshold=30, label=sc['label'])
    all_lead_days.append(avg)

print("\n" + "=" * 60)
print("  總結")
print("=" * 60)
print(f"  場景數：{len(scenarios)}")
print(f"  各場景領先天數：{[f'{d:.1f}d' for d in all_lead_days]}")
print(f"  平均領先天數  ：{np.mean(all_lead_days):.1f} 天")
n_lead = sum(1 for d in all_lead_days if d > 0.5)
print(f"  提前 >0.5 天場景：{n_lead}/{len(scenarios)}")

if np.mean(all_lead_days) >= 1.0:
    print("\n  ✅ 判定：TSI v3 領先指標在歷史崩盤模式中")
    print("          平均提前 1 天以上發出警示")
elif np.mean(all_lead_days) > 0:
    print("\n  ⚠️ 判定：有輕微提前效果，但不到 1 天，需要更多改良")
else:
    print("\n  ❌ 判定：領先指標無顯著提前效果，需要重新設計")
