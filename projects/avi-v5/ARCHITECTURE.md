# AVI V5 Architecture Plan
> Claude × TradingView MCP + Markov Regime Engine + GARCH Volatility

## Overview

AVI V5 is the next evolution of the Adjusted Valuation Index, integrating:
- **AVI V4 base**: 14 indicators × 6 dimensions → 0-10 score (unchanged)
- **Markov Regime Engine**: 4-state HMM classifier (calm_trend, volatile_trend, chop, risk_off) that dynamically adjusts AVI interpretation
- **GARCH(1,1) Volatility Forecasting**: Forward-looking vol signal that supplements static VIX
- **TradingView MCP Server**: Claude Code directly controls TradingView via Playwright automation
- **Backtest Framework**: V4 vs V4.1 (+ Regime) vs V4.2 (+ Regime + GARCH) comparison across 5 crises

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    DATA SOURCES                           │
│  FRED API ─┐                                             │
│  multpl ───┤──► collector.py ──► cache                   │
│  yfinance ─┘                                             │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│                   CORE ENGINES                            │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  AVI V4     │  │ Regime (HMM) │  │ GARCH(1,1)     │  │
│  │  14 指標    │  │ 4 states     │  │ vol forecast   │  │
│  │  20Y pctile │  │ transitions  │  │ VIX comparison │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘  │
│         └────────────────┼──────────────────┘            │
│                          ▼                                │
│              ┌──────────────────┐                         │
│              │  V5 Pipeline     │                         │
│              │  composite score │                         │
│              └────────┬─────────┘                         │
└───────────────────────┼──────────────────────────────────┘
                        │
          ┌─────────────┼────────────┐
          ▼             ▼            ▼
    ┌──────────┐  ┌──────────┐  ┌──────────────┐
    │ Backtest │  │ Reports  │  │ TradingView  │
    │ V4/V41/42│  │ HTML/PDF │  │ MCP + Pine   │
    └──────────┘  └──────────┘  └──────────────┘
```

## File Structure

```
projects/avi-v5/
├── ARCHITECTURE.md
├── requirements.txt
├── .env.example                    # FRED_API_KEY, TV credentials
├── config/
│   ├── avi_weights.yaml            # 14 indicator weights
│   ├── indicators.yaml             # FRED IDs, sources, directions
│   ├── regime_params.yaml          # HMM hyperparameters
│   └── garch_params.yaml          # GARCH config
├── mcp-tradingview/                # MCP Server
│   ├── server.py                   # MCP protocol handler (stdio)
│   ├── tradingview_bridge.py       # Playwright automation
│   └── tools/
│       ├── chart_tools.py          # switch_symbol, draw_level
│       ├── pine_tools.py           # create/modify Pine Script
│       ├── data_tools.py           # get_ohlcv, market_state
│       └── backtest_tools.py       # run_backtest
├── src/
│   ├── data/
│   │   ├── collector.py            # Pull all 14 indicators
│   │   ├── sources/
│   │   │   ├── fred.py             # FRED API (10 indicators)
│   │   │   ├── multpl.py           # CAPE, P/S, Earnings Yield
│   │   │   └── yfinance_source.py  # S&P 500 (200MA, Drawdown)
│   │   └── cache.py                # Local cache
│   ├── engine/
│   │   ├── avi_core.py             # V4 base computation
│   │   ├── percentile.py           # 20Y rolling percentile
│   │   └── weights.py              # Weight manager
│   ├── regime/
│   │   ├── regime_engine.py        # 4-state HMM classifier
│   │   ├── feature_builder.py      # 6 features for regime detection
│   │   ├── transitions.py          # Transition probability matrix
│   │   └── regime_adjustment.py    # Regime → AVI multiplier
│   ├── garch/
│   │   ├── garch_model.py          # GARCH(1,1) with arch library
│   │   ├── forecast.py             # Multi-step vol forecast
│   │   ├── persistence.py          # α+β stickiness metric
│   │   └── vix_comparison.py       # GARCH vs VIX accuracy
│   └── pipeline/
│       ├── avi_v5_pipeline.py       # Orchestrator
│       └── monthly_update.py        # Scheduled computation
├── backtest/
│   ├── framework.py                # Event-loop backtest engine
│   ├── signals.py                  # V4, V4.1, V4.2 signal generators
│   ├── portfolio.py                # AVI-signal allocation
│   ├── metrics.py                  # Detection rate, FP, Sharpe, etc.
│   ├── crises.py                   # 5 crisis definitions
│   └── compare.py                  # Cross-version comparison
├── pine/
│   ├── avi_v5_indicator.pine       # Main indicator for TradingView
│   └── regime_overlay.pine         # Regime visualization
└── scripts/
    ├── run_monthly.py              # CLI: monthly AVI update
    ├── run_backtest.py             # CLI: comparison backtest
    └── export_to_pine.py           # CLI: generate Pine Script
```

## Data Flow

### Monthly Update Pipeline

1. **Data Collection**: Pull 14 indicators from FRED (10), multpl.com (3), yfinance (1)
2. **Rolling Percentile**: Each indicator → 20-year (240 month) rolling percentile
3. **AVI V4 Base**: percentile × direction → score × weight → sum = AVI V4 (0-10)
4. **Regime Classification**: HMM on [rolling_return, realized_vol, drawdown, rolling_sharpe, VIX, credit_spread] → 1 of 4 regimes
5. **GARCH Forecast**: GARCH(1,1) on daily S&P returns → vol forecast + persistence + VIX gap
6. **Composite V5**: `AVI_V5 = AVI_V4 × regime_multiplier + garch_adjustment + transition_premium`

### Regime Multipliers

| Regime | Multiplier | Rationale |
|--------|-----------|-----------|
| calm_trend | 1.00 | Neutral — no adjustment |
| volatile_trend | 1.08 | +8% — whipsaw risk, tail events more likely |
| chop | 1.04 | +4% — range-bound, signals noisy |
| risk_off | 1.15 | +15% — active drawdown, risk elevated |

### GARCH Integration Points

| Integration | Mechanism | Impact |
|-------------|-----------|--------|
| VIX supplement | `max(VIX_percentile, GARCH_forecast_percentile)` | More forward-looking |
| Regime stickiness | `persistence = α+β`; if > 0.97 → regime is "sticky" | Adds to transition premium |
| Vol gap signal | `(GARCH_forecast - VIX) / VIX`; clip to ±0.5 | Direct AVI adjustment |

### V5 Composite Formula

```python
regime_multiplier = {calm_trend: 1.00, volatile_trend: 1.08, chop: 1.04, risk_off: 1.15}
garch_adjustment = clip((garch_vol - vix) / vix * 0.3, -0.5, +0.5)
transition_premium = P(risk_off | current_state) * 0.5

avi_v5 = clip(avi_v4 * regime_multiplier[regime] + garch_adjustment + transition_premium, 0, 10)
```

## TradingView MCP Server

### Approach: Playwright Browser Automation

TradingView has no public REST API for chart manipulation. The MCP server uses Playwright to automate the web terminal.

### MCP Configuration (settings.json)

```json
{
  "mcpServers": {
    "tradingview": {
      "command": "python",
      "args": ["-m", "projects.avi-v5.mcp-tradingview.server"],
      "env": {
        "TV_SESSION_COOKIE": "${TV_SESSION_COOKIE}"
      }
    }
  }
}
```

### MCP Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `tv_switch_symbol` | symbol, timeframe | Navigate to symbol |
| `tv_draw_level` | price, label, color | Draw horizontal line |
| `tv_get_ohlcv` | symbol, timeframe, bars | Read OHLCV data |
| `tv_get_market_state` | symbol | Price, change%, volume |
| `tv_create_pine_indicator` | name, source_code | Upload Pine indicator |
| `tv_run_backtest` | strategy_code, symbol, period | Execute Pine backtest |
| `tv_screenshot` | filepath | Capture chart state |

## Backtest Framework

### 5 Historical Crises

| Crisis | Peak | Trough | S&P Drawdown |
|--------|------|--------|-------------|
| Asian/LTCM 1997-98 | 1998-07-17 | 1998-10-08 | -19% |
| Dot-com 2000 | 2000-03-24 | 2002-10-09 | -49% |
| GFC 2007-09 | 2007-10-09 | 2009-03-09 | -57% |
| COVID 2020 | 2020-02-19 | 2020-03-23 | -34% |
| Rate Hike 2022 | 2022-01-03 | 2022-10-12 | -25% |

### Metrics

- **Detection rate**: % of crises where AVI ≥ 6.0 before peak
- **Avg lead time**: Months AVI ≥ 6.0 before peak
- **False positive rate**: % of months AVI ≥ 6.0 NOT followed by 10%+ drop in 18mo
- **Sharpe ratio**: AVI-signal portfolio vs buy-and-hold
- **Max drawdown**: AVI-signal portfolio

### Signal-Based Portfolio Rules

| AVI Level | Allocation |
|-----------|-----------|
| < 4.0 | 100% SPY |
| 4.0-5.0 | 80% SPY, 20% Cash |
| 5.0-6.0 | 60% SPY, 40% Cash |
| 6.0-7.0 | 40% SPY, 60% Cash |
| 7.0-8.0 | 20% SPY, 80% Cash |
| > 8.0 | 100% Cash |

## 14 Indicator Data Dictionary

| # | Indicator | Source | FRED ID | Direction | Dimension | Weight |
|---|-----------|--------|---------|-----------|-----------|--------|
| 1 | CAPE | multpl.com | — | ↑=↑risk | Valuation | 12% |
| 2 | P/S Ratio | multpl.com | — | ↑=↑risk | Valuation | 8% |
| 3 | FCF Yield | multpl.com | — | ↑=↓risk | Valuation | 9% |
| 4 | Buffett Indicator | FRED | GDP + WILL5000PRFC | ↑=↑risk | Valuation | 9% |
| 5 | ROIC | FRED | A446RC1Q027SBEA / TNWMVBSNNCB | ↑=↓risk | Profitability | 8% |
| 6 | Yield Spread 10Y-2Y | FRED | T10Y2Y | ↑=↑risk | Macro | 4% |
| 7 | VIX | FRED | VIXCLS | ↑=↑risk | Macro | 5% |
| 8 | STLFSI4 | FRED | STLFSI4 | ↑=↑risk | Macro | 5% |
| 9 | CPI YoY | FRED | CPIAUCSL | ↑=↑risk | Rates | 7% |
| 10 | 10Y Real Yield | FRED | DGS10 - CPI | ↑=↑risk | Rates | 7% |
| 11 | BAA-10Y Spread | FRED | BAA10YM | ↑=↑risk | Credit | 6% |
| 12 | BAA-AAA Diff | FRED | BAA - AAA | ↑=↑risk | Credit | 6% |
| 13 | S&P/200MA Ratio | yfinance | ^GSPC | ↑=↑risk | Momentum | 7% |
| 14 | S&P Drawdown | yfinance | ^GSPC | ↑=↓risk | Momentum | 7% |

## Implementation Phases

| Phase | Scope | Timeline | Deliverable |
|-------|-------|----------|-------------|
| 1 | AVI V4 reproduction in new structure | Week 1-2 | `run_monthly.py` outputs correct score |
| 2 | Regime Engine (4-state HMM) | Week 3-4 | Regime classification with visual validation |
| 3 | GARCH Integration | Week 5-6 | Full V5 pipeline with composite score |
| 4 | Backtesting (V4 vs V4.1 vs V4.2) | Week 7-8 | Comparison table + report |
| 5 | TradingView MCP Server | Week 9-10 | Claude controls TradingView |
| 6 | Reports + Polish | Week 11-12 | Production-ready monthly automation |

## Dependencies

```
numpy>=1.24.0, pandas>=2.0.0, pydantic>=2.0.0, pyyaml>=6.0
fredapi>=0.5.0, yfinance>=0.2.18, requests>=2.28.0, beautifulsoup4>=4.12.0
hmmlearn>=0.3.0, scikit-learn>=1.2.0, arch>=6.0.0, scipy>=1.10.0
matplotlib>=3.7.0, jinja2>=3.1.0
mcp>=1.0.0, playwright>=1.40.0
pytest>=7.0.0
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| YAML config for weights | Decouples parameters from code; enables A/B testing |
| 4 regimes (not 3) | Separates "chop" from "calm" — different risk profiles |
| Multiplicative regime adjustment | Scales naturally with AVI level (7.0 × 1.08 = 7.56) |
| GARCH(1,1) with Student-t | Fat-tail capture; `arch` library is the Python standard |
| Playwright for TradingView | No public API exists; Playwright > Selenium for async MCP |
| Pine Script output (not scraping) | Pine is persistent, shareable, runs independently |
| Monthly frequency | AVI designed for monthly; FRED data is monthly |
