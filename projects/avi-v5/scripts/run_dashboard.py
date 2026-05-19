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
    """Generate updated CPI Pine Script with current values. Delegates to src.pine_export."""
    from src.pine_export import generate_cpi_pine
    return generate_cpi_pine(result)




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

    # Step 6: Generate Pine Scripts (optional)
    pine_paths = []
    if args.pine:
        logger.info("Generating Pine Scripts with current values...")

        # CPI Pine
        cpi_pine_path = generate_pine_script(result)
        pine_paths.append(("CPI", cpi_pine_path))
        logger.info("CPI Pine generated: %s", cpi_pine_path)

        # TSI Pine
        try:
            from src.tsi.data import TSIDataCollector
            from src.tsi import TechStressIndex
            from src.pine_export import generate_tsi_pine, generate_composite_pine

            logger.info("Computing TSI for Pine Script...")
            tsi_data = TSIDataCollector().collect_all()
            tsi_result = TechStressIndex().compute(
                sox_daily=tsi_data["sox"], qqq_daily=tsi_data["qqq"],
                mu_daily=tsi_data["mu"], smh_daily=tsi_data["smh"],
                spy_daily=tsi_data["spy"], treasury_10y=tsi_data["t10y"],
                vix_daily=tsi_data["vix"], treasury_30y=tsi_data.get("t30y"),
                as_of=args.date,
            )
            tsi_pine_path = generate_tsi_pine(tsi_result)
            pine_paths.append(("TSI", tsi_pine_path))
            logger.info("TSI Pine generated: %s", tsi_pine_path)
            logger.info("TSI Score: %.0f/100 (%s)", tsi_result.score, tsi_result.bias)

            # Composite (CPI + TSI + AVI)
            composite_path = generate_composite_pine(result, tsi_result, avi_score)
            pine_paths.append(("Composite", composite_path))
            logger.info("Composite Pine generated: %s", composite_path)

        except ImportError:
            logger.warning("mcp-tradingview not available for TSI Pine — skipping")
        except Exception as e:
            logger.warning("TSI Pine generation failed (non-fatal): %s", e)

    # Print summary to terminal as well
    print()
    print(result.summary())
    print()
    print("Dashboard: file://" + html_path)
    if pine_paths:
        print()
        print("Pine Scripts generated:")
        for name, path in pine_paths:
            print(f"  [{name}] {path}")
        print()
        print("→ Paste each file into TradingView Pine Editor and click 'Add to chart'")


if __name__ == "__main__":
    main()
