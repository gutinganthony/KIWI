"""Cross-version backtest comparison runner.

Orchestrates the full V4 / V4.1 / V4.2 backtest pipeline:
  1. Collect all historical indicator + daily data
  2. Generate monthly AVI signals for each version
  3. Run portfolio simulation for each
  4. Compute metrics for each
  5. Format a comparison report
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.data.collector import IndicatorCollector
from src.engine.avi_core import AVIEngine

from backtest.crises import CRISES
from backtest.metrics import BacktestMetrics, compute_metrics
from backtest.portfolio import AVISignalPortfolio
from backtest.signals import generate_v4_signal, generate_v41_signal, generate_v42_signal

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Data collection helpers
# ─────────────────────────────────────────────────────────────────────

def _collect_all_data(
    fred_api_key: Optional[str],
    start: str,
    end: str,
) -> tuple[dict[str, pd.Series], pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Fetch everything needed for the backtest.

    Returns
    -------
    indicator_data : dict[str, pd.Series]
        Monthly indicator histories.
    sp500_daily : pd.DataFrame
        Daily S&P 500 with ``close`` column.
    vix_daily : pd.Series
        Daily VIX.
    credit_daily : pd.Series
        Daily BAA-10Y credit spread.
    sp500_monthly_returns : pd.Series
        Monthly simple returns for S&P 500.
    """
    import yfinance as yf

    logger.info("Collecting indicator histories...")
    collector = IndicatorCollector(fred_api_key=fred_api_key)
    indicator_data = collector.collect_all(as_of_date=end, start_date=start)

    logger.info("Downloading S&P 500 daily data...")
    sp_raw = yf.download("^GSPC", start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(sp_raw.columns, pd.MultiIndex):
        sp_raw.columns = sp_raw.columns.get_level_values(0)
    sp500_daily = pd.DataFrame({"close": sp_raw["Close"]})

    # Monthly returns for portfolio simulation
    sp_monthly_close = sp500_daily["close"].resample("ME").last()
    sp500_monthly_returns = sp_monthly_close.pct_change().dropna()
    sp500_monthly_returns.name = "sp500_return"

    logger.info("Fetching daily VIX...")
    vix_daily = collector.fred.fetch_series("VIXCLS", start, end).dropna()

    logger.info("Fetching daily BAA-10Y credit spread...")
    credit_daily = collector.fred.fetch_series("BAA10YM", start, end).dropna()

    logger.info(
        f"Data collection complete: {len(indicator_data)} indicators, "
        f"{len(sp500_daily)} daily S&P obs, "
        f"{len(sp500_monthly_returns)} monthly returns"
    )

    return indicator_data, sp500_daily, vix_daily, credit_daily, sp500_monthly_returns


# ─────────────────────────────────────────────────────────────────────
# Buy-and-hold benchmark
# ─────────────────────────────────────────────────────────────────────

def _buy_and_hold_metrics(sp500_monthly_returns: pd.Series) -> dict:
    """Compute buy-and-hold (100 % SPY) portfolio stats."""
    if sp500_monthly_returns.empty:
        return {"total_return": 1.0, "sharpe_ratio": 0.0,
                "max_drawdown": 0.0, "calmar_ratio": 0.0}

    cum = (1.0 + sp500_monthly_returns).cumprod()
    total_return = float(cum.iloc[-1])

    n_years = len(sp500_monthly_returns) / 12.0
    ann_return = total_return ** (1.0 / n_years) - 1.0 if n_years > 0 else 0.0

    monthly_mean = sp500_monthly_returns.mean()
    monthly_std = sp500_monthly_returns.std()
    sharpe = (monthly_mean / monthly_std * np.sqrt(12)) if monthly_std > 0 else 0.0

    running_max = cum.cummax()
    dd = (cum - running_max) / running_max
    max_dd = float(dd.min())

    calmar = ann_return / abs(max_dd) if max_dd != 0 else 0.0

    return {
        "total_return": total_return,
        "sharpe_ratio": float(sharpe),
        "max_drawdown": max_dd,
        "calmar_ratio": float(calmar),
    }


# ─────────────────────────────────────────────────────────────────────
# Report formatting
# ─────────────────────────────────────────────────────────────────────

def _format_comparison_table(
    metrics: dict[str, BacktestMetrics],
    bh: dict,
) -> str:
    """Build the main comparison ASCII table."""
    v4 = metrics["v4"]
    v41 = metrics["v41"]
    v42 = metrics["v42"]

    sep = "=" * 69
    thin = "-" * 65

    lines = [
        sep,
        "  AVI BACKTEST COMPARISON: V4 vs V4.1 (+ Regime) vs V4.2 (+ GARCH)",
        sep,
        "",
        "  CRISIS DETECTION",
        f"  {thin}",
        f"  {'Metric':<30} {'V4':>10} {'V4.1':>10} {'V4.2':>10}",
        f"  {thin}",
    ]

    # Detection rate
    def _det_str(m: BacktestMetrics) -> str:
        detected = sum(1 for d in m.crisis_details if d.detected)
        total = len(m.crisis_details)
        return f"{detected}/{total}"

    lines.append(
        f"  {'Detection Rate (>=6.0)':<30} {_det_str(v4):>10} "
        f"{_det_str(v41):>10} {_det_str(v42):>10}"
    )

    lines.append(
        f"  {'Avg Lead Time (months)':<30} {v4.avg_lead_time_months:>10.1f} "
        f"{v41.avg_lead_time_months:>10.1f} {v42.avg_lead_time_months:>10.1f}"
    )

    def _avg_max(m: BacktestMetrics) -> float:
        return np.mean(m.max_avi_before_peak) if m.max_avi_before_peak else 0.0

    lines.append(
        f"  {'Avg Max AVI Before Peak':<30} {_avg_max(v4):>10.2f} "
        f"{_avg_max(v41):>10.2f} {_avg_max(v42):>10.2f}"
    )

    lines.append("")
    return "\n".join(lines)


def _format_crisis_detail(metrics: dict[str, BacktestMetrics]) -> str:
    """Per-crisis breakdown table."""
    v4 = metrics["v4"]
    v41 = metrics["v41"]
    v42 = metrics["v42"]

    thin = "-" * 90

    lines = [
        "  PER-CRISIS DETAIL",
        f"  {thin}",
        f"  {'Crisis':<22} {'V4 Max':>8} {'V4.1 Max':>9} {'V4.2 Max':>9}"
        f"  {'V4 Lead':>8} {'V4.1 Lead':>10} {'V4.2 Lead':>10}",
        f"  {thin}",
    ]

    for i in range(len(CRISES)):
        d4 = v4.crisis_details[i] if i < len(v4.crisis_details) else None
        d41 = v41.crisis_details[i] if i < len(v41.crisis_details) else None
        d42 = v42.crisis_details[i] if i < len(v42.crisis_details) else None

        name = CRISES[i]["name"]
        max4 = f"{d4.max_avi:.2f}" if d4 else "N/A"
        max41 = f"{d41.max_avi:.2f}" if d41 else "N/A"
        max42 = f"{d42.max_avi:.2f}" if d42 else "N/A"
        lead4 = f"{d4.lead_time_months}mo" if d4 and d4.detected else "--"
        lead41 = f"{d41.lead_time_months}mo" if d41 and d41.detected else "--"
        lead42 = f"{d42.lead_time_months}mo" if d42 and d42.detected else "--"

        lines.append(
            f"  {name:<22} {max4:>8} {max41:>9} {max42:>9}"
            f"  {lead4:>8} {lead41:>10} {lead42:>10}"
        )

    lines.append("")
    return "\n".join(lines)


def _format_portfolio_table(
    metrics: dict[str, BacktestMetrics],
    bh: dict,
) -> str:
    """Portfolio performance table."""
    v4 = metrics["v4"]
    v41 = metrics["v41"]
    v42 = metrics["v42"]

    thin = "-" * 65

    lines = [
        "  PORTFOLIO PERFORMANCE",
        f"  {thin}",
        f"  {'Metric':<30} {'V4':>8} {'V4.1':>8} {'V4.2':>8} {'Buy&Hold':>9}",
        f"  {thin}",
    ]

    # Total return
    def _ret_str(tr: float) -> str:
        return f"{(tr - 1.0) * 100:.0f}%"

    lines.append(
        f"  {'Total Return':<30} "
        f"{_ret_str(v4.total_return):>8} "
        f"{_ret_str(v41.total_return):>8} "
        f"{_ret_str(v42.total_return):>8} "
        f"{_ret_str(bh['total_return']):>9}"
    )

    lines.append(
        f"  {'Sharpe Ratio':<30} "
        f"{v4.sharpe_ratio:>8.2f} "
        f"{v41.sharpe_ratio:>8.2f} "
        f"{v42.sharpe_ratio:>8.2f} "
        f"{bh['sharpe_ratio']:>9.2f}"
    )

    def _dd_str(dd: float) -> str:
        return f"{dd * 100:.0f}%"

    lines.append(
        f"  {'Max Drawdown':<30} "
        f"{_dd_str(v4.max_drawdown):>8} "
        f"{_dd_str(v41.max_drawdown):>8} "
        f"{_dd_str(v42.max_drawdown):>8} "
        f"{_dd_str(bh['max_drawdown']):>9}"
    )

    lines.append(
        f"  {'Calmar Ratio':<30} "
        f"{v4.calmar_ratio:>8.2f} "
        f"{v41.calmar_ratio:>8.2f} "
        f"{v42.calmar_ratio:>8.2f} "
        f"{bh['calmar_ratio']:>9.2f}"
    )

    lines.append("")
    return "\n".join(lines)


def _format_fp_table(metrics: dict[str, BacktestMetrics]) -> str:
    """False-positive analysis table."""
    v4 = metrics["v4"]
    v41 = metrics["v41"]
    v42 = metrics["v42"]

    thin = "-" * 65

    lines = [
        "  FALSE POSITIVE ANALYSIS",
        f"  {thin}",
        f"  {'Metric':<30} {'V4':>10} {'V4.1':>10} {'V4.2':>10}",
        f"  {thin}",
    ]

    lines.append(
        f"  {'Months >=6.0 total':<30} "
        f"{v4.months_above_threshold:>10} "
        f"{v41.months_above_threshold:>10} "
        f"{v42.months_above_threshold:>10}"
    )

    lines.append(
        f"  {'False Positive Rate':<30} "
        f"{v4.false_positive_rate * 100:>9.0f}% "
        f"{v41.false_positive_rate * 100:>9.0f}% "
        f"{v42.false_positive_rate * 100:>9.0f}%"
    )

    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# Main comparison entry point
# ─────────────────────────────────────────────────────────────────────

def run_comparison(
    fred_api_key: Optional[str] = None,
    start: str = "1996-01-01",
    end: str = "2026-04-01",
) -> dict:
    """Run full backtest for V4, V4.1, and V4.2.

    Parameters
    ----------
    fred_api_key : str or None
        FRED API key.  Reads from ``FRED_API_KEY`` env var if None.
    start : str
        Backtest start date (data collection starts here).
    end : str
        Backtest end date.

    Returns
    -------
    dict
        ``"v4"``              -- BacktestMetrics for V4
        ``"v41"``             -- BacktestMetrics for V4.1
        ``"v42"``             -- BacktestMetrics for V4.2
        ``"buy_hold"``        -- dict with buy-and-hold stats
        ``"comparison_table"``-- formatted ASCII table
        ``"crisis_detail"``   -- per-crisis breakdown string
    """
    # ── Step 1: Collect data ────────────────────────────────────────
    logger.info("=" * 64)
    logger.info("  AVI BACKTEST: Collecting historical data")
    logger.info("=" * 64)

    indicator_data, sp500_daily, vix_daily, credit_daily, sp500_monthly_returns = (
        _collect_all_data(fred_api_key, start, end)
    )

    # ── Step 2: Generate signals ────────────────────────────────────
    logger.info("=" * 64)
    logger.info("  AVI BACKTEST: Generating signals")
    logger.info("=" * 64)

    engine = AVIEngine()

    v4_signal = generate_v4_signal(indicator_data, engine, start, end)
    logger.info(f"V4 signal: {len(v4_signal)} months")

    v41_signal = generate_v41_signal(
        indicator_data, engine, sp500_daily, vix_daily, credit_daily, start, end,
    )
    logger.info(f"V4.1 signal: {len(v41_signal)} months")

    v42_signal = generate_v42_signal(
        indicator_data, engine, sp500_daily, vix_daily, credit_daily, start, end,
    )
    logger.info(f"V4.2 signal: {len(v42_signal)} months")

    # ── Step 3: Portfolio simulation ────────────────────────────────
    logger.info("=" * 64)
    logger.info("  AVI BACKTEST: Running portfolio simulations")
    logger.info("=" * 64)

    portfolio = AVISignalPortfolio()
    port_v4 = portfolio.run(v4_signal, sp500_monthly_returns)
    port_v41 = portfolio.run(v41_signal, sp500_monthly_returns)
    port_v42 = portfolio.run(v42_signal, sp500_monthly_returns)

    # Buy-and-hold benchmark
    bh_stats = _buy_and_hold_metrics(sp500_monthly_returns)

    # ── Step 4: Compute metrics ─────────────────────────────────────
    logger.info("=" * 64)
    logger.info("  AVI BACKTEST: Computing metrics")
    logger.info("=" * 64)

    metrics_v4 = compute_metrics(v4_signal, sp500_monthly_returns, CRISES, port_v4)
    metrics_v41 = compute_metrics(v41_signal, sp500_monthly_returns, CRISES, port_v41)
    metrics_v42 = compute_metrics(v42_signal, sp500_monthly_returns, CRISES, port_v42)

    all_metrics = {"v4": metrics_v4, "v41": metrics_v41, "v42": metrics_v42}

    # ── Step 5: Format reports ──────────────────────────────────────
    comparison_table = (
        _format_comparison_table(all_metrics, bh_stats)
        + _format_crisis_detail(all_metrics)
        + _format_portfolio_table(all_metrics, bh_stats)
        + _format_fp_table(all_metrics)
    )

    logger.info("Backtest comparison complete.")

    return {
        "v4": metrics_v4,
        "v41": metrics_v41,
        "v42": metrics_v42,
        "buy_hold": bh_stats,
        "comparison_table": comparison_table,
        "crisis_detail": _format_crisis_detail(all_metrics),
        "v4_signal": v4_signal,
        "v41_signal": v41_signal,
        "v42_signal": v42_signal,
    }
