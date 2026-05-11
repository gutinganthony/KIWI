#!/usr/bin/env python3
"""AVI Monthly Update Script.

Usage:
    python scripts/run_monthly.py [--date YYYY-MM-DD] [--verbose]
    python scripts/run_monthly.py --v5 [--date YYYY-MM-DD] [--verbose]

Requires:
    FRED_API_KEY environment variable (or .env file in project root)
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file if present
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute AVI V4 score from current market data.",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Compute AVI as of this date (YYYY-MM-DD). Default: latest available.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2000-01-01",
        help="Start date for historical data (YYYY-MM-DD). Default: 2000-01-01.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging.",
    )
    parser.add_argument(
        "--v5",
        action="store_true",
        help="Run full V5 pipeline (regime + GARCH) instead of V4-only.",
    )
    return parser.parse_args()


def run_v4(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Run the V4-only pipeline."""
    # Step 1: Collect indicator data
    logger.info("Step 1: Collecting indicator data...")
    try:
        from src.data.collector import IndicatorCollector

        collector = IndicatorCollector()
        indicator_data = collector.collect_all(
            as_of_date=args.date,
            start_date=args.start_date,
        )
    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        return 1

    if not indicator_data:
        logger.error("No indicator data collected. Check API keys and connectivity.")
        return 1

    logger.info(f"Collected {len(indicator_data)} indicators successfully.")

    # Step 2: Compute AVI score
    logger.info("Step 2: Computing AVI score...")
    try:
        from src.engine.avi_core import AVIEngine

        engine = AVIEngine()
        result = engine.compute(indicator_data, as_of_date=args.date)
    except Exception as e:
        logger.error(f"AVI computation failed: {e}")
        return 1

    # Step 3: Output results
    print("\n")
    print(result.summary())
    print("\n")

    return 0


def run_v5(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Run the full V5 pipeline (V4 + regime + GARCH)."""
    try:
        from src.pipeline.avi_v5_pipeline import AVIV5Pipeline
    except ImportError as e:
        logger.error(
            f"V5 pipeline import failed: {e}. "
            "Ensure hmmlearn, arch, and scikit-learn are installed."
        )
        return 1

    logger.info("Running full V5 pipeline...")
    try:
        pipeline = AVIV5Pipeline()
        result = pipeline.run(
            as_of_date=args.date,
            start_date=args.start_date,
            verbose=args.verbose,
        )
    except Exception as e:
        logger.error(f"V5 pipeline failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Print composite summary
    print("\n")
    print(result.summary())
    print("\n")

    # Print V4 detail underneath
    print("--- Detailed V4 Breakdown ---")
    print(result.v4_result.summary())
    print("\n")

    return 0


def main() -> int:
    """Run the monthly AVI computation pipeline."""
    args = parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger("avi_monthly")

    if args.v5:
        logger.info("=" * 64)
        logger.info("  AVI V5 Monthly Update (Regime + GARCH)")
        logger.info("=" * 64)
        return run_v5(args, logger)
    else:
        logger.info("=" * 60)
        logger.info("  AVI V4 Monthly Update")
        logger.info("=" * 60)
        return run_v4(args, logger)


if __name__ == "__main__":
    sys.exit(main())
