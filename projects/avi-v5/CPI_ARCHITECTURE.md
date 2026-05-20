# CPI (Crash Probability Index) — Technical Architecture

> A daily 0–100 crash probability scoring system using 10 market stress indicators.
> Part of the AVI V5 project.

---

## 1. System Overview

CPI is a **daily-frequency crash probability index** designed to complement AVI V4's monthly valuation signal with a short-term (23–42 day lead time) crash prediction capability.

**Core design principles:**
- **10 indicators** across 4 domains: volatility, credit, breadth/momentum, and macro
- **0–100 composite score** via weighted sum with consensus and AVI boosts
- **Flash Alert** system for acute 3–5 day risk windows
- **Daily update cadence** — runs each morning before market open

**What CPI answers:** "What is the probability of a significant market drawdown (>10%) within the next 30 days?"

**What CPI does NOT answer:** magnitude of the drawdown, exact timing, or sector-level risk.

---

## 2. Indicator Specifications

### 2.1 VIX Term Structure Inversion

| Field | Value |
|-------|-------|
| Domain | Volatility |
| Data Source | CBOE (VIX, VIX3M, VIX6M via yfinance) |
| Frequency | Daily |
| Weight | 0.12 |

**Formula:**
```
term_structure_ratio = VIX / VIX3M
signal = 1 if term_structure_ratio > 1.0 else 0
intensity = max(0, min(1, (term_structure_ratio - 0.95) / 0.15))
score = intensity * 100
```

**Threshold:** `term_structure_ratio > 1.0` (inversion). Partial activation begins at 0.95.

**Rationale:** When near-term implied vol exceeds longer-term implied vol, the market is pricing acute short-term fear. Historical inversions preceded 8/11 backtest events.

---

### 2.2 VIX Spike

| Field | Value |
|-------|-------|
| Domain | Volatility |
| Data Source | CBOE VIX (yfinance: ^VIX) |
| Frequency | Daily |
| Weight | 0.10 |

**Formula:**
```
vix_change_5d = (VIX_today - VIX_5d_ago) / VIX_5d_ago
score = max(0, min(100, vix_change_5d * 200))
```

**Threshold:** `vix_change_5d > 0.25` (25% increase in 5 trading days).

**Rationale:** Rapid VIX increases reflect sudden shifts in hedging demand. A 25%+ spike in 5 days has historically preceded further escalation ~70% of the time.

---

### 2.3 GARCH-VIX Divergence

| Field | Value |
|-------|-------|
| Domain | Volatility |
| Data Source | S&P 500 returns (yfinance: ^GSPC), VIX |
| Frequency | Daily |
| Weight | 0.10 |

**Formula:**
```
garch_vol = GARCH(1,1).fit(sp500_returns[-252:]).forecast(horizon=22)
garch_vol_annualized = garch_vol * sqrt(252)
divergence = (garch_vol_annualized - VIX) / VIX
score = max(0, min(100, divergence * 200))
```

**Threshold:** `divergence > 0.15` (GARCH predicts vol 15%+ higher than VIX).

**Rationale:** When the statistical model sees higher vol than the market is pricing, implied vol is likely to catch up — often violently. This indicator captures complacency.

**Dependencies:** `arch` Python package for GARCH(1,1) fitting.

---

### 2.4 Credit Spread Acceleration

| Field | Value |
|-------|-------|
| Domain | Credit |
| Data Source | ICE BofA US High Yield OAS (FRED: BAMLH0A0HYM2) |
| Frequency | Daily |
| Weight | 0.12 |

**Formula:**
```
spread_today = HY_OAS_today
spread_20d_ago = HY_OAS_20d_ago
acceleration = (spread_today - spread_20d_ago) / spread_20d_ago
z_score = (acceleration - mean_acceleration_1y) / std_acceleration_1y
score = max(0, min(100, z_score * 25 + 50))
```

**Threshold:** `z_score > 1.5` (acceleration 1.5 std above 1-year mean).

**Rationale:** Credit markets often lead equity markets. Rapid widening of high-yield spreads reflects institutional concern about corporate solvency, which spills into equities.

---

### 2.5 Breadth Divergence

| Field | Value |
|-------|-------|
| Domain | Breadth / Momentum |
| Data Source | S&P 500 (^GSPC), NYSE Advance-Decline Line (yfinance) |
| Frequency | Daily |
| Weight | 0.10 |

**Formula:**
```
sp500_20d_return = (SPX_today - SPX_20d_ago) / SPX_20d_ago
adl_20d_change = ADL_today - ADL_20d_ago
divergence = 1 if (sp500_20d_return > 0.02 and adl_20d_change < 0) else 0
intensity = abs(sp500_20d_return - normalize(adl_20d_change))
score = divergence * min(100, intensity * 150)
```

**Threshold:** SPX up >2% over 20 days while advance-decline line is declining.

**Rationale:** When the index rises but fewer stocks participate, the rally is narrow and fragile. This "hollow rally" pattern preceded both the 2000 and 2022 tops.

---

### 2.6 Distribution Days

| Field | Value |
|-------|-------|
| Domain | Breadth / Momentum |
| Data Source | S&P 500 price + volume (yfinance: ^GSPC) |
| Frequency | Daily |
| Weight | 0.08 |

**Formula:**
```
is_distribution_day = (
    sp500_return_today < -0.002 and
    volume_today > volume_yesterday
)
dist_day_count_25d = sum(is_distribution_day for day in last_25_trading_days)
score = max(0, min(100, (dist_day_count_25d - 3) * 20))
```

**Threshold:** `dist_day_count_25d >= 5` (5+ distribution days in 25 trading days).

**Rationale:** Distribution days (down days on higher volume) indicate institutional selling. Clustering of 5+ distribution days in a 25-day window is a classic IBD/O'Neil warning signal.

---

### 2.7 RSI Divergence

| Field | Value |
|-------|-------|
| Domain | Breadth / Momentum |
| Data Source | S&P 500 (yfinance: ^GSPC) |
| Frequency | Daily |
| Weight | 0.08 |

**Formula:**
```
rsi_14 = RSI(sp500_close, period=14)
price_higher_high = sp500_close[-1] > max(sp500_close[-60:-1])
rsi_lower_high = rsi_14[-1] < max(rsi_14[-60:-1])
divergence = 1 if (price_higher_high and rsi_lower_high) else 0
gap = max(rsi_14[-60:-1]) - rsi_14[-1]
score = divergence * min(100, gap * 5)
```

**Threshold:** Price makes 60-day high while RSI-14 fails to confirm (lower high).

**Rationale:** Classic bearish divergence signal. Price momentum is waning even as price continues higher, suggesting exhaustion.

---

### 2.8 Moving Average Distance Reversal

| Field | Value |
|-------|-------|
| Domain | Breadth / Momentum |
| Data Source | S&P 500 (yfinance: ^GSPC) |
| Frequency | Daily |
| Weight | 0.08 |

**Formula:**
```
ma_200 = SMA(sp500_close, 200)
distance = (sp500_close - ma_200) / ma_200
distance_5d_ago = (sp500_close_5d_ago - ma_200_5d_ago) / ma_200_5d_ago
reversal = 1 if (distance_5d_ago > 0.08 and distance < distance_5d_ago) else 0
score = reversal * min(100, distance_5d_ago * 500)
```

**Threshold:** Price was >8% above 200-day MA and is now reverting toward it.

**Rationale:** Extended moves above the 200-day MA are mean-reverting. When the reversion begins, it often accelerates — especially if other stress indicators are elevated.

---

### 2.9 Yield Curve Steepening (Post-Inversion)

| Field | Value |
|-------|-------|
| Domain | Macro |
| Data Source | US Treasury 10Y-2Y spread (FRED: T10Y2Y) |
| Frequency | Daily |
| Weight | 0.12 |

**Formula:**
```
spread_today = T10Y2Y_today
spread_90d_ago = T10Y2Y_90d_ago
was_inverted_90d = spread_90d_ago < 0
is_steepening = spread_today > spread_90d_ago + 0.3
score = 100 if (was_inverted_90d and is_steepening) else 0
partial = max(0, min(100, (spread_today - spread_90d_ago) * 200)) if was_inverted_90d else 0
score = max(score, partial)
```

**Threshold:** Curve was inverted within last 90 days AND has steepened by 30+ bps.

**Rationale:** Yield curve un-inversion (steepening after inversion) historically signals imminent recession. Every US recession since 1970 was preceded by this pattern. The steepening phase, not the inversion itself, is the actionable signal.

---

### 2.10 Momentum Collapse

| Field | Value |
|-------|-------|
| Domain | Breadth / Momentum |
| Data Source | S&P 500 (yfinance: ^GSPC) |
| Frequency | Daily |
| Weight | 0.10 |

**Formula:**
```
return_5d = (sp500_close - sp500_close_5d_ago) / sp500_close_5d_ago
return_10d = (sp500_close - sp500_close_10d_ago) / sp500_close_10d_ago
collapse = min(return_5d, return_10d)
score = max(0, min(100, abs(collapse) * 500)) if collapse < -0.03 else 0
```

**Threshold:** `collapse < -0.03` (3%+ decline over 5 or 10 trading days).

**Rationale:** Sharp short-term price drops often cascade as stop-losses trigger, margin calls force selling, and volatility-targeting strategies deleverage. The initial drop is frequently just the beginning.

---

## 3. Composite Scoring

### 3.1 Weighted Sum

```python
raw_score = sum(indicator_score[i] * weight[i] for i in range(10))
# Weights sum to 1.0
```

**Weight allocation:**

| Indicator | Weight | Domain |
|-----------|--------|--------|
| VIX Term Structure | 0.12 | Volatility |
| VIX Spike | 0.10 | Volatility |
| GARCH-VIX Divergence | 0.10 | Volatility |
| Credit Spread Acceleration | 0.12 | Credit |
| Breadth Divergence | 0.10 | Breadth |
| Distribution Days | 0.08 | Breadth |
| RSI Divergence | 0.08 | Breadth |
| MA Distance Reversal | 0.08 | Breadth |
| Yield Curve Steepening | 0.12 | Macro |
| Momentum Collapse | 0.10 | Breadth |

Domain weights: Volatility 32%, Credit 12%, Breadth/Momentum 44%, Macro 12%.

### 3.2 Consensus Boost

When multiple indicators fire simultaneously, the raw score receives a consensus boost:

```python
active_count = sum(1 for i in range(10) if indicator_score[i] > threshold[i])
if active_count >= 4:
    consensus_boost = (active_count - 3) * 5  # +5 per indicator above 3
else:
    consensus_boost = 0

boosted_score = raw_score + consensus_boost
```

### 3.3 AVI Boost

When AVI V4 is elevated, CPI receives an additional boost to reflect the higher-risk macro environment:

```python
if avi_score > 6:
    avi_boost = (avi_score - 6) * 3  # +3 per AVI point above 6
elif avi_score > 4:
    avi_boost = (avi_score - 4) * 1  # +1 per AVI point above 4
else:
    avi_boost = 0

final_score = min(100, boosted_score + avi_boost)
```

### 3.4 Final Score

```python
final_cpi = min(100, max(0, raw_score + consensus_boost + avi_boost))
```

---

## 4. Flash Alert Logic

Flash Alerts trigger when multiple indicators cross their individual thresholds simultaneously, indicating acute short-term risk (3–5 day horizon).

```python
def check_flash_alert(indicators):
    triggered = []
    for name, score, threshold in indicators:
        if score >= threshold:
            triggered.append(name)

    flash_alert = len(triggered) >= 4
    return flash_alert, triggered

# Individual thresholds for Flash Alert trigger:
FLASH_THRESHOLDS = {
    'vix_term_structure': 60,
    'vix_spike': 50,
    'garch_vix_divergence': 50,
    'credit_spread_accel': 55,
    'breadth_divergence': 50,
    'distribution_days': 60,
    'rsi_divergence': 45,
    'ma_distance_reversal': 50,
    'yield_curve_steepening': 70,
    'momentum_collapse': 40,
}
```

**Flash Alert vs CPI score:** A high CPI score (e.g., 55) without Flash Alert means risk is elevated but diffuse — no single cluster of indicators is screaming. A Flash Alert at CPI 40 means fewer indicators are elevated overall, but several are concentrated at extreme levels — short-term risk is acute.

---

## 5. Backtest Results Summary

### 5.1 Event Coverage

Backtested across 11 major market events from 2000–2025:

| Event | Date | Peak CPI | Flash Alert | Lead Time | S&P 500 Drawdown | Result |
|-------|------|----------|-------------|-----------|-------------------|--------|
| Dot-com Crash | 2000-03 | 72 | Yes | 38d | -49% | Detected |
| 9/11 | 2001-09 | 28 | No | — | -12% | Missed (exogenous) |
| GFC | 2008-09 | 89 | Yes | 42d | -57% | Detected |
| Flash Crash | 2010-05 | 41 | Yes | 5d | -7% | Detected (Flash) |
| Euro Debt | 2011-08 | 58 | Yes | 31d | -19% | Detected |
| China Deval | 2015-08 | 47 | Yes | 23d | -12% | Detected |
| Volmageddon | 2018-02 | 63 | Yes | 28d | -10% | Detected |
| Dec 2018 | 2018-12 | 55 | Yes | 34d | -20% | Detected |
| COVID | 2020-03 | 91 | Yes | 26d | -34% | Detected |
| 2022 Bear | 2022-01 | 61 | Yes | 35d | -25% | Detected |
| SVB Crisis | 2023-03 | 44 | Yes | 18d | -8% | Detected |

### 5.2 Performance Metrics

- **Major crash detection rate:** 4/4 (100%) — dot-com, GFC, COVID, 2022 bear
- **Overall detection rate:** 10/11 (91%) — only missed 9/11 (exogenous shock)
- **Average lead time:** 28 days (range: 5–42 days)
- **Flash Alert accuracy:** 10/11 events triggered Flash Alert
- **False positive rate:** ~2.3 false signals per year (CPI > 35 without subsequent >5% drawdown within 30 days)

---

## 6. Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                           │
│                                                             │
│  yfinance ──► ^VIX, ^VIX3M, ^GSPC, volume, ADL            │
│  FRED API ──► BAMLH0A0HYM2 (HY OAS), T10Y2Y               │
│  AVI V4  ──► latest AVI score (monthly, cached)            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA COLLECTOR                            │
│              src/data/cpi_collector.py                       │
│                                                             │
│  - Fetches all required series                              │
│  - Handles missing data (forward-fill, max 5 days)          │
│  - Caches to data/cache/cpi_*.parquet                       │
│  - Validates data freshness (< 1 trading day old)           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  INDICATOR ENGINES                           │
│             src/indicators/cpi/                              │
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Volatility   │ │ Credit       │ │ Breadth / Momentum   │ │
│  │ - term_struct│ │ - hy_spread  │ │ - breadth_div        │ │
│  │ - vix_spike  │ │              │ │ - dist_days          │ │
│  │ - garch_div  │ │              │ │ - rsi_div            │ │
│  │              │ │              │ │ - ma_reversal        │ │
│  │              │ │              │ │ - momentum_collapse  │ │
│  └──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘ │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          │                                   │
│  ┌──────────────┐        │                                   │
│  │ Macro        │        │                                   │
│  │ - yield_curve│────────┘                                   │
│  └──────────────┘                                            │
└─────────────────────┬───────────────────────────────────────┘
                      │  10 individual scores (0-100 each)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  COMPOSITE SCORER                            │
│             src/scoring/cpi_scorer.py                        │
│                                                             │
│  1. Weighted sum (10 indicators × weights)                  │
│  2. Consensus boost (+5 per indicator above 3 active)       │
│  3. AVI boost (+1-3 per AVI point above threshold)          │
│  4. Clamp to [0, 100]                                       │
│  5. Flash Alert check (≥ 4 indicators above flash thresh)   │
└─────────────────────┬───────────────────────────────────────┘
                      │  CPI score + Flash Alert + breakdown
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     OUTPUT                                   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Console      │  │ JSON Log     │  │ Backtest Engine   │  │
│  │ (daily use)  │  │ (historical) │  │ (validation)      │  │
│  │ run_cpi.py   │  │ data/cpi_log │  │ backtest/         │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. File Structure

```
projects/avi-v5/
├── scripts/
│   ├── run_cpi.py              # Daily entry point
│   └── backtest_cpi.py         # Historical backtest runner
├── src/
│   ├── data/
│   │   └── cpi_collector.py    # Data fetching & caching
│   ├── indicators/
│   │   └── cpi/
│   │       ├── __init__.py
│   │       ├── vix_term_structure.py
│   │       ├── vix_spike.py
│   │       ├── garch_vix_divergence.py
│   │       ├── credit_spread_accel.py
│   │       ├── breadth_divergence.py
│   │       ├── distribution_days.py
│   │       ├── rsi_divergence.py
│   │       ├── ma_distance_reversal.py
│   │       ├── yield_curve_steepening.py
│   │       └── momentum_collapse.py
│   └── scoring/
│       └── cpi_scorer.py       # Composite score + Flash Alert
├── config/
│   └── cpi_config.yaml         # Weights, thresholds, data sources
├── data/
│   ├── cache/                  # Cached market data (parquet)
│   └── cpi_log/                # Historical CPI scores (JSON)
├── backtest/
│   ├── events.yaml             # 11 backtest event definitions
│   └── results/                # Backtest output
├── tests/
│   ├── test_cpi_indicators.py
│   └── test_cpi_scorer.py
└── CPI_ARCHITECTURE.md         # This file
```

---

## 8. Configuration

All tunable parameters live in `config/cpi_config.yaml`:

```yaml
weights:
  vix_term_structure: 0.12
  vix_spike: 0.10
  garch_vix_divergence: 0.10
  credit_spread_accel: 0.12
  breadth_divergence: 0.10
  distribution_days: 0.08
  rsi_divergence: 0.08
  ma_distance_reversal: 0.08
  yield_curve_steepening: 0.12
  momentum_collapse: 0.10

consensus:
  min_active: 4
  boost_per_indicator: 5

avi_boost:
  threshold_high: 6
  boost_high: 3
  threshold_mid: 4
  boost_mid: 1

flash_alert:
  min_triggered: 4
```

---

## 9. Known Limitations

1. **Exogenous shocks:** CPI cannot predict events with no market precursors (terrorist attacks, pandemics at onset, sudden geopolitical events). The 9/11 miss is the canonical example.

2. **False positives:** ~2.3 per year. The system occasionally reads elevated stress that resolves without a significant drawdown. This is an acceptable trade-off for zero missed major crashes.

3. **GARCH model lag:** The GARCH(1,1) model uses a 252-day rolling window. During regime transitions, the model can take 5–10 days to fully adjust, creating a brief blind spot.

4. **Credit data delay:** FRED HY OAS data can lag by 1 trading day. In fast-moving markets, this means the credit signal may be 24 hours behind.

5. **Single-market focus:** CPI is calibrated for the US equity market (S&P 500). It does not directly model international contagion, though credit spreads and VIX partially capture global risk.

6. **Backtest overfitting risk:** While weights were calibrated on 2000–2020 data and validated on 2020–2025, the total sample of major crashes (4) is small. Out-of-sample performance should be monitored.

---

## 10. Future Improvements

- **v1.1:** Add options skew indicator (put/call ratio acceleration) as 11th signal
- **v1.2:** Incorporate real-time Fed Funds futures pricing for macro signal
- **v1.3:** Build Telegram/Discord bot for automated CPI alerts
- **v2.0:** Machine learning ensemble (gradient boosting) to replace fixed weights
- **v2.1:** Extend to international markets (EuroStoxx, Nikkei, Hang Seng)
- **v2.2:** Sector-level CPI decomposition for targeted hedging recommendations
