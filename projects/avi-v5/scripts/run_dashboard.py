#!/usr/bin/env python3
"""CPI Visual Dashboard — generate and open an HTML dashboard for CPI results.

Usage:
    # Generate dashboard and open in browser
    python3 scripts/run_dashboard.py

    # Also generate updated Pine Script for TradingView
    python3 scripts/run_dashboard.py --pine

    # Compute for a specific date
    python3 scripts/run_dashboard.py --date 2024-12-15

    # Custom output path
    python3 scripts/run_dashboard.py --output /tmp/cpi.html
"""

import argparse
import logging
import sys
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if not verbose:
        logging.getLogger("yfinance").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("peewee").setLevel(logging.WARNING)
        logging.getLogger("src.garch").setLevel(logging.WARNING)


def collect_data(start: str = "2024-01-01") -> Dict:
    """Collect all CPI data sources."""
    from src.cpi.data import CPIDataCollector

    collector = CPIDataCollector()
    return collector.collect_all(start=start)


def compute_cpi(data: Dict, date: Optional[str] = None):
    """Compute CPI score and return the CPIResult."""
    import pandas as pd
    from src.cpi import CrashProbabilityIndex

    cpi = CrashProbabilityIndex()
    return cpi.compute(
        sp500_daily=data["sp500"],
        vix_daily=data.get("vix", pd.Series(dtype=float)),
        vix3m_daily=data.get("vix3m"),
        baa_daily=data.get("baa", pd.Series(dtype=float)),
        aaa_daily=data.get("aaa", pd.Series(dtype=float)),
        treasury_10y=data.get("t10y", pd.Series(dtype=float)),
        treasury_2y=data.get("t2y", pd.Series(dtype=float)),
        as_of=date,
    )


def build_history(
    data: Dict, days: int = 30
) -> List[Tuple[str, float]]:
    """Compute CPI for last N trading days to build a history chart.

    Returns list of (date_str, score) tuples.
    """
    from src.cpi import CrashProbabilityIndex

    logger = logging.getLogger("dashboard.history")
    cpi = CrashProbabilityIndex()

    # Get the last N trading dates from sp500
    sp500 = data["sp500"]
    dates = sp500.index[-days:]

    history = []  # type: List[Tuple[str, float]]
    for dt in dates:
        try:
            result = cpi.compute(
                sp500_daily=sp500,
                vix_daily=data["vix"],
                vix3m_daily=data.get("vix3m"),
                baa_daily=data["baa"],
                aaa_daily=data["aaa"],
                treasury_10y=data["t10y"],
                treasury_2y=data["t2y"],
                as_of=dt.strftime("%Y-%m-%d"),
            )
            history.append((dt.strftime("%Y-%m-%d"), round(result.score, 1)))
        except Exception as e:
            logger.debug("Skipping %s: %s", dt.strftime("%Y-%m-%d"), e)
            continue

    return history


def generate_pine_script(result) -> str:
    """Generate an updated Pine Script with current CPI values filled in.

    Reads the template pine file and replaces placeholder values between
    the PINE_VALUES_START and PINE_VALUES_END markers.

    Returns the path to the generated Pine Script.
    """
    template_path = PROJECT_ROOT / "pine" / "cpi_indicator.pine"
    output_path = PROJECT_ROOT / "pine" / "cpi_indicator_current.pine"

    template = template_path.read_text(encoding="utf-8")

    # Build indicator signal lookup
    sig_map = {}  # type: Dict[str, float]
    for ind in result.indicators:
        sig_map[ind.name] = round(ind.signal, 1)

    # Values to substitute
    avi_ctx = result.avi_context
    replacements = {
        "{{CPI_SCORE}}": "{:.1f}".format(result.score),
        "{{CPI_DATE}}": result.date.strftime("%Y-%m-%d"),
        "{{FLASH_ALERT}}": "true" if result.flash_alert.triggered else "false",
        "{{FLASH_SEVERITY}}": result.flash_alert.severity,
        "{{AVI_CONTEXT}}": "{:.1f}".format(avi_ctx) if avi_ctx is not None else "0.0",
        "{{SIG_VIX_TERM}}": str(sig_map.get("vix_term_structure", 0.0)),
        "{{SIG_VIX_SPIKE}}": str(sig_map.get("vix_spike", 0.0)),
        "{{SIG_GARCH}}": str(sig_map.get("garch_vix_gap", 0.0)),
        "{{SIG_CREDIT}}": str(sig_map.get("credit_acceleration", 0.0)),
        "{{SIG_BREADTH}}": str(sig_map.get("breadth_divergence", 0.0)),
        "{{SIG_DISTRIB}}": str(sig_map.get("distribution_days", 0.0)),
        "{{SIG_RSI}}": str(sig_map.get("rsi_divergence", 0.0)),
        "{{SIG_MA_DIST}}": str(sig_map.get("ma_distance_reversal", 0.0)),
        "{{SIG_YIELD}}": str(sig_map.get("yield_curve_steepening", 0.0)),
        "{{SIG_MOMENTUM}}": str(sig_map.get("momentum_collapse", 0.0)),
    }

    output = template
    for placeholder, value in replacements.items():
        output = output.replace(placeholder, value)

    output_path.write_text(output, encoding="utf-8")
    return str(output_path.resolve())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CPI Visual Dashboard — generate HTML + optional Pine Script"
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="Compute CPI for a specific date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--pine", action="store_true",
        help="Also generate updated Pine Script for TradingView"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Custom output path for the HTML dashboard"
    )
    parser.add_argument(
        "--history", type=int, default=252,
        help="Number of historical trading days to chart (default: 252 = ~1 year)"
    )
    parser.add_argument(
        "--guide", action="store_true",
        help="Open the CPI User Guide instead of the dashboard"
    )
    parser.add_argument(
        "--no-open", action="store_true",
        help="Do not auto-open the dashboard in a browser"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger("dashboard")

    if args.guide:
        guide_path = str((PROJECT_ROOT / "dashboard" / "guide.html").resolve())
        webbrowser.open("file://" + guide_path)
        return

    logger.info("=" * 65)
    logger.info("  CPI Visual Dashboard")
    logger.info("=" * 65)

    # Step 1: Collect data
    logger.info("Collecting market data...")
    data = collect_data()

    # Step 2: Compute AVI V5 score
    avi_score = None
    try:
        logger.info("Computing AVI V5 score...")
        from src.pipeline.avi_v5_pipeline import AVIV5Pipeline
        import os
        fred_key = os.environ.get("FRED_API_KEY", "")
        if fred_key:
            pipeline = AVIV5Pipeline(fred_api_key=fred_key)
            v5_result = pipeline.run(verbose=False)
            avi_score = v5_result.avi_v4_score
            logger.info("AVI V5: %.2f/10", avi_score)
        else:
            logger.warning("No FRED_API_KEY, skipping AVI")
    except Exception as e:
        logger.warning("AVI computation failed (non-fatal): %s", e)

    # Step 3: Compute current CPI
    logger.info("Computing CPI score...")
    result = compute_cpi(data, date=args.date)
    result.avi_context = avi_score
    logger.info(
        "CPI Score: %.0f/100 (%s)", result.score, result.level
    )

    # Step 3: Build history (for chart)
    history = None  # type: Optional[List[Tuple[str, float]]]
    if args.history > 0:
        logger.info("Computing %d-day history for chart...", args.history)
        history = build_history(data, days=args.history)
        logger.info("  History: %d data points", len(history) if history else 0)

    # Step 4: Generate HTML dashboard
    from dashboard.cpi_dashboard import generate_dashboard

    html_path = generate_dashboard(
        result=result,
        history=history,
        output_path=args.output,
    )
    logger.info("Dashboard generated: %s", html_path)

    # Step 5: Open in browser
    if not args.no_open:
        url = "file://" + html_path
        logger.info("Opening in browser...")
        webbrowser.open(url)

    # Step 6: Generate Pine Script (optional)
    pine_path = None
    if args.pine:
        logger.info("Generating Pine Script with current values...")
        pine_path = generate_pine_script(result)
        logger.info("Pine Script generated: %s", pine_path)
        logger.info(
            "  Copy contents of %s into TradingView Pine Editor",
            pine_path,
        )

    # Print summary to terminal as well
    print()
    print(result.summary())
    print()
    print("Dashboard: file://" + html_path)
    if pine_path:
        print("Pine Script: " + pine_path)


if __name__ == "__main__":
    main()
