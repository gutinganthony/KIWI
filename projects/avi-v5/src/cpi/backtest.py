"""Backtest CPI against historical crash events."""

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import CrashProbabilityIndex

logger = logging.getLogger(__name__)

CRASH_EVENTS = [
    {"name": "Dot-com Crash 2000", "peak": "2000-03-24", "trough": "2002-10-09", "drawdown": -0.49, "type": "major"},
    {"name": "GFC 2007-09", "peak": "2007-10-09", "trough": "2009-03-09", "drawdown": -0.57, "type": "major"},
    {"name": "2018 Feb Volmageddon", "peak": "2018-01-26", "trough": "2018-02-08", "drawdown": -0.10, "type": "flash_crash"},
    {"name": "2018 Q4 Selloff", "peak": "2018-10-03", "trough": "2018-12-24", "drawdown": -0.20, "type": "major"},
    {"name": "2019 May Selloff", "peak": "2019-05-01", "trough": "2019-06-03", "drawdown": -0.07, "type": "correction"},
    {"name": "COVID Crash 2020", "peak": "2020-02-19", "trough": "2020-03-23", "drawdown": -0.34, "type": "major"},
    {"name": "2020 Sep Tech Corr", "peak": "2020-09-02", "trough": "2020-09-23", "drawdown": -0.10, "type": "correction"},
    {"name": "2022 Rate Hike", "peak": "2022-01-03", "trough": "2022-10-12", "drawdown": -0.25, "type": "major"},
    {"name": "2023 Jul-Oct Pullback", "peak": "2023-07-31", "trough": "2023-10-27", "drawdown": -0.10, "type": "correction"},
    {"name": "2024 Aug Japan Carry", "peak": "2024-07-16", "trough": "2024-08-05", "drawdown": -0.08, "type": "correction"},
    {"name": "2025 Q1 Tariff", "peak": "2025-02-19", "trough": "2025-04-08", "drawdown": -0.19, "type": "major"},
]


@dataclass
class CrashDetectionResult:
    name: str
    peak_date: str
    max_cpi_30d_before: float
    max_cpi_7d_before: float
    cpi_at_peak: float
    flash_alert_before: bool
    days_first_alert: int  # Days before peak that CPI first exceeded 60
    detected_30d: bool  # CPI >= 35 within 30 days before peak
    detected_7d: bool  # CPI >= 35 within 7 days before peak


def run_cpi_backtest(
    data: dict,
    events: list[dict] = None,
) -> str:
    """Run CPI backtest against historical crash events.

    Args:
        data: Dict from CPIDataCollector.collect_all()
        events: List of crash events (default: CRASH_EVENTS)

    Returns:
        Formatted results string.
    """
    if events is None:
        events = CRASH_EVENTS

    cpi = CrashProbabilityIndex()
    sp500 = data["sp500"]
    vix = data.get("vix", pd.Series(dtype=float))
    vix3m = data.get("vix3m")
    baa = data.get("baa", pd.Series(dtype=float))
    aaa = data.get("aaa", pd.Series(dtype=float))
    t10y = data.get("t10y", pd.Series(dtype=float))
    t2y = data.get("t2y", pd.Series(dtype=float))

    # Compute daily CPI for the full history
    logger.info("Computing daily CPI scores...")
    trading_days = sp500.index
    daily_scores = {}
    daily_flash = {}

    for i, day in enumerate(trading_days):
        if i < 252:  # Need at least 1 year of history
            continue
        try:
            result = cpi.compute(
                sp500_daily=sp500,
                vix_daily=vix,
                vix3m_daily=vix3m,
                baa_daily=baa,
                aaa_daily=aaa,
                treasury_10y=t10y,
                treasury_2y=t2y,
                as_of=day.strftime("%Y-%m-%d"),
            )
            daily_scores[day] = result.score
            daily_flash[day] = result.flash_alert.triggered
        except Exception as e:
            if i % 500 == 0:
                logger.debug(f"  CPI failed at {day.date()}: {e}")

        if (i + 1) % 500 == 0:
            logger.info(f"  CPI progress: {i + 1}/{len(trading_days)} days")

    cpi_series = pd.Series(daily_scores)
    flash_series = pd.Series(daily_flash)
    logger.info(f"Computed CPI for {len(cpi_series)} trading days")

    # Evaluate each crash event
    results = []
    for event in events:
        peak = pd.Timestamp(event["peak"])

        # Get CPI scores in windows before peak
        mask_30d = (cpi_series.index >= peak - pd.Timedelta(days=45)) & (cpi_series.index <= peak)
        mask_7d = (cpi_series.index >= peak - pd.Timedelta(days=10)) & (cpi_series.index <= peak)

        scores_30d = cpi_series[mask_30d]
        scores_7d = cpi_series[mask_7d]
        flash_30d = flash_series[mask_30d]

        if scores_30d.empty:
            results.append(CrashDetectionResult(
                name=event["name"], peak_date=event["peak"],
                max_cpi_30d_before=0, max_cpi_7d_before=0, cpi_at_peak=0,
                flash_alert_before=False, days_first_alert=-1,
                detected_30d=False, detected_7d=False,
            ))
            continue

        max_30d = scores_30d.max()
        max_7d = scores_7d.max() if not scores_7d.empty else 0
        at_peak = cpi_series.get(peak, scores_30d.iloc[-1])

        # First day CPI >= 35
        alerts_60 = scores_30d[scores_30d >= 35]
        if not alerts_60.empty:
            first_alert = alerts_60.index[0]
            days_before = (peak - first_alert).days
        else:
            days_before = -1

        results.append(CrashDetectionResult(
            name=event["name"],
            peak_date=event["peak"],
            max_cpi_30d_before=max_30d,
            max_cpi_7d_before=max_7d,
            cpi_at_peak=at_peak,
            flash_alert_before=flash_30d.any() if not flash_30d.empty else False,
            days_first_alert=days_before,
            detected_30d=max_30d >= 35,
            detected_7d=max_7d >= 35,
        ))

    # Also compute false positive rate
    # Define: CPI >= 35 on a day NOT within 30 days before any crash peak
    crash_windows = set()
    for event in events:
        peak = pd.Timestamp(event["peak"])
        for d in range(45):
            crash_windows.add(peak - pd.Timedelta(days=d))

    total_alert_days = (cpi_series >= 35).sum()
    true_positive_days = sum(
        1 for d in cpi_series.index if cpi_series[d] >= 35 and d in crash_windows
    )
    false_positive_days = total_alert_days - true_positive_days
    total_non_crash_days = len(cpi_series) - len(crash_windows.intersection(set(cpi_series.index)))
    fp_rate = false_positive_days / max(total_non_crash_days, 1)

    # Format output
    lines = [
        "=" * 70,
        "  CPI BACKTEST: Crash Probability Index vs Historical Events",
        "=" * 70,
        "",
        "  CRASH DETECTION (threshold: CPI >= 35)",
        "  " + "-" * 66,
    ]

    detected_30d_count = sum(1 for r in results if r.detected_30d)
    detected_7d_count = sum(1 for r in results if r.detected_7d)
    flash_count = sum(1 for r in results if r.flash_alert_before)

    lines.append(f"  Detection Rate (30d window):  {detected_30d_count}/{len(results)}")
    lines.append(f"  Detection Rate (7d window):   {detected_7d_count}/{len(results)}")
    lines.append(f"  Flash Alerts Before Crash:     {flash_count}/{len(results)}")
    lines.append(f"  False Positive Rate:           {fp_rate:.1%}")
    lines.append("")

    lines.append("  PER-EVENT DETAIL")
    lines.append("  " + "-" * 66)
    lines.append(f"  {'Event':<25} {'Max30d':>7} {'Max7d':>7} {'Flash':>6} {'Lead':>6} {'DD':>6}")
    lines.append("  " + "-" * 66)

    for r, event in zip(results, events):
        lead = f"{r.days_first_alert}d" if r.days_first_alert >= 0 else "--"
        flash = "YES" if r.flash_alert_before else "no"
        dd = f"{event['drawdown']:.0%}"
        lines.append(
            f"  {r.name:<25} {r.max_cpi_30d_before:>7.0f} {r.max_cpi_7d_before:>7.0f} "
            f"{flash:>6} {lead:>6} {dd:>6}"
        )

    lines.append("")
    lines.append(f"  ALERT STATISTICS")
    lines.append("  " + "-" * 66)
    lines.append(f"  Total days CPI >= 35:         {total_alert_days}")
    lines.append(f"  True positive days:           {true_positive_days}")
    lines.append(f"  False positive days:          {false_positive_days}")
    lines.append(f"  False positive rate:          {fp_rate:.1%}")
    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)
