"""Backtest performance metrics for AVI signal evaluation.

Computes crisis detection quality (early warning capability) and
portfolio performance statistics.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Default threshold for a "warning" signal
_WARNING_THRESHOLD = 6.0
# Months before peak to look for signal
_LOOKBACK_MONTHS = 24
# Forward window and drop threshold for false-positive analysis
_FP_FORWARD_MONTHS = 18
_FP_DROP_THRESHOLD = 0.10  # 10 % drop


@dataclass
class CrisisDetail:
    """Per-crisis detection detail."""

    name: str
    max_avi: float          # max AVI in lookback window before peak
    detected: bool          # max_avi >= threshold
    lead_time_months: int   # months AVI first >= threshold before peak (0 if not detected)


@dataclass
class BacktestMetrics:
    """Aggregate backtest metrics for one AVI version."""

    # Crisis detection
    detection_rate: float              # fraction of crises detected (max AVI >= 6.0 in 24mo)
    avg_lead_time_months: float        # average months signal fires before peak
    max_avi_before_peak: list[float]   # max AVI in window before each crisis peak
    crisis_details: list[CrisisDetail] = field(default_factory=list)

    # False positives
    false_positive_rate: float = 0.0   # fraction of months AVI >= 6.0 NOT followed by 10 % drop
    months_above_threshold: int = 0    # total months with AVI >= 6.0
    false_positive_months: int = 0     # months above threshold that were false positives

    # Portfolio performance
    sharpe_ratio: float = 0.0          # annualized Sharpe (rf = 0)
    max_drawdown: float = 0.0          # maximum portfolio drawdown
    total_return: float = 0.0          # cumulative return (e.g. 2.50 = +150 %)
    calmar_ratio: float = 0.0          # total annualized return / |max_drawdown|


def _find_crisis_signal(
    avi_series: pd.Series,
    peak_date: str,
    lookback_months: int = _LOOKBACK_MONTHS,
    threshold: float = _WARNING_THRESHOLD,
) -> CrisisDetail:
    """Analyze AVI signal in the window before a crisis peak.

    Parameters
    ----------
    avi_series : pd.Series
        Monthly AVI scores.
    peak_date : str
        Date of market peak (YYYY-MM-DD).
    lookback_months : int
        Number of months before peak to search.
    threshold : float
        AVI level considered a warning.

    Returns
    -------
    CrisisDetail
    """
    peak_ts = pd.Timestamp(peak_date)
    window_start = peak_ts - pd.DateOffset(months=lookback_months)

    window = avi_series[
        (avi_series.index >= window_start) & (avi_series.index <= peak_ts)
    ]

    if window.empty:
        return CrisisDetail(name="", max_avi=0.0, detected=False, lead_time_months=0)

    max_avi = float(window.max())
    detected = max_avi >= threshold

    # Lead time: months from first signal >= threshold to peak
    lead_time = 0
    if detected:
        above = window[window >= threshold]
        if not above.empty:
            first_signal = above.index[0]
            # Approximate lead time in months
            lead_time = max(
                0,
                int(round((peak_ts - first_signal).days / 30.44))
            )

    return CrisisDetail(
        name="",  # filled by caller
        max_avi=max_avi,
        detected=detected,
        lead_time_months=lead_time,
    )


def _compute_false_positive_rate(
    avi_series: pd.Series,
    sp500_monthly_returns: pd.Series,
    threshold: float = _WARNING_THRESHOLD,
    forward_months: int = _FP_FORWARD_MONTHS,
    drop_threshold: float = _FP_DROP_THRESHOLD,
) -> tuple[float, int, int]:
    """Compute the false-positive rate.

    A month is a "positive" if AVI >= threshold.  It is a "false
    positive" if the S&P 500 does NOT drop by ``drop_threshold`` or
    more within the next ``forward_months``.

    Returns
    -------
    tuple
        (false_positive_rate, months_above, false_positive_count)
    """
    above_months = avi_series[avi_series >= threshold].index
    if len(above_months) == 0:
        return 0.0, 0, 0

    fp_count = 0
    total_above = len(above_months)

    for m in above_months:
        # Look at cumulative return over the next forward_months
        future_start = m
        future_end = m + pd.DateOffset(months=forward_months)
        future_returns = sp500_monthly_returns[
            (sp500_monthly_returns.index > future_start) &
            (sp500_monthly_returns.index <= future_end)
        ]

        if future_returns.empty:
            # No future data available — cannot confirm or deny; count as FP
            fp_count += 1
            continue

        # Compute cumulative return path and check for a drop
        cum = (1.0 + future_returns).cumprod()
        max_drawdown_in_window = (cum / cum.cummax() - 1.0).min()

        if max_drawdown_in_window > -drop_threshold:
            # Did not drop enough -> false positive
            fp_count += 1

    fp_rate = fp_count / total_above if total_above > 0 else 0.0
    return fp_rate, total_above, fp_count


def _compute_portfolio_stats(
    portfolio_df: pd.DataFrame,
) -> dict:
    """Compute Sharpe, max drawdown, total return, and Calmar ratio.

    Parameters
    ----------
    portfolio_df : pd.DataFrame
        Output from ``AVISignalPortfolio.run()``.

    Returns
    -------
    dict with keys: sharpe_ratio, max_drawdown, total_return, calmar_ratio
    """
    if portfolio_df.empty or "portfolio_return" not in portfolio_df.columns:
        return {
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_return": 0.0,
            "calmar_ratio": 0.0,
        }

    returns = portfolio_df["portfolio_return"]
    cum_ret = portfolio_df["cumulative_return"]

    # Total return (cumulative series is already a growth factor)
    total_return = cum_ret.iloc[-1] if not cum_ret.empty else 1.0

    # Annualized return
    n_months = len(returns)
    n_years = n_months / 12.0
    ann_return = total_return ** (1.0 / n_years) - 1.0 if n_years > 0 else 0.0

    # Annualized Sharpe (rf = 0)
    monthly_mean = returns.mean()
    monthly_std = returns.std()
    sharpe = (monthly_mean / monthly_std * np.sqrt(12)) if monthly_std > 0 else 0.0

    # Max drawdown from cumulative return series
    running_max = cum_ret.cummax()
    drawdowns = (cum_ret - running_max) / running_max
    max_dd = float(drawdowns.min()) if not drawdowns.empty else 0.0

    # Calmar ratio
    calmar = ann_return / abs(max_dd) if max_dd != 0 else 0.0

    return {
        "sharpe_ratio": float(sharpe),
        "max_drawdown": max_dd,
        "total_return": total_return,
        "calmar_ratio": float(calmar),
    }


def compute_metrics(
    avi_series: pd.Series,
    sp500_monthly_returns: pd.Series,
    crises: list[dict],
    portfolio_df: Optional[pd.DataFrame] = None,
) -> BacktestMetrics:
    """Compute full backtest metrics for one AVI version.

    Parameters
    ----------
    avi_series : pd.Series
        Monthly AVI scores.
    sp500_monthly_returns : pd.Series
        Monthly S&P 500 simple returns.
    crises : list[dict]
        Crisis definitions (from ``crises.py``).
    portfolio_df : pd.DataFrame or None
        If provided, portfolio stats are computed from it.
        If None, portfolio metrics are left at defaults.

    Returns
    -------
    BacktestMetrics
    """
    # --- Crisis detection ---
    crisis_details: list[CrisisDetail] = []
    max_avis: list[float] = []

    for crisis in crises:
        detail = _find_crisis_signal(avi_series, crisis["peak"])
        detail.name = crisis["name"]
        crisis_details.append(detail)
        max_avis.append(detail.max_avi)

    detected_count = sum(1 for d in crisis_details if d.detected)
    detection_rate = detected_count / len(crises) if crises else 0.0

    lead_times = [d.lead_time_months for d in crisis_details if d.detected]
    avg_lead = np.mean(lead_times) if lead_times else 0.0

    # --- False positives ---
    fp_rate, months_above, fp_count = _compute_false_positive_rate(
        avi_series, sp500_monthly_returns
    )

    # --- Portfolio performance ---
    if portfolio_df is not None and not portfolio_df.empty:
        port_stats = _compute_portfolio_stats(portfolio_df)
    else:
        port_stats = {
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_return": 0.0,
            "calmar_ratio": 0.0,
        }

    return BacktestMetrics(
        detection_rate=detection_rate,
        avg_lead_time_months=float(avg_lead),
        max_avi_before_peak=max_avis,
        crisis_details=crisis_details,
        false_positive_rate=fp_rate,
        months_above_threshold=months_above,
        false_positive_months=fp_count,
        **port_stats,
    )
