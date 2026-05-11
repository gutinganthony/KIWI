#!/usr/bin/env python3
"""AVI Backtest Comparison Script.

Runs the full V4 vs V4.1 vs V4.2 backtest across 5 historical crises
and prints a formatted comparison report.

Usage:
    python scripts/run_backtest.py [--start 1996-01-01] [--end 2026-04-01] [--verbose]

Requires:
    FRED_API_KEY environment variable (or .env file in project root)
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file if present
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE)
    except ImportError:
        pass


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("fredapi").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("hmmlearn").setLevel(logging.WARNING)
    logging.getLogger("arch").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Run AVI backtest comparison across V4, V4.1, and V4.2 "
            "over 5 historical crises."
        ),
    )
    parser.add_argument(
        "--start",
        type=str,
        default="1996-01-01",
        help="Backtest start date (YYYY-MM-DD). Default: 1996-01-01.",
    )
    parser.add_argument(
        "--end",
        type=str,
        default="2026-04-01",
        help="Backtest end date (YYYY-MM-DD). Default: 2026-04-01.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging.",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point for the backtest comparison."""
    args = parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger("avi_backtest")

    logger.info("=" * 69)
    logger.info("  AVI BACKTEST COMPARISON")
    logger.info(f"  Period: {args.start} -> {args.end}")
    logger.info("=" * 69)

    t0 = time.time()

    from backtest.compare import run_comparison

    try:
        results = run_comparison(
            fred_api_key=None,  # reads from env
            start=args.start,
            end=args.end,
        )
    except Exception as exc:
        logger.error(f"Backtest failed: {exc}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    elapsed = time.time() - t0

    # Print the comparison report
    print("\n")
    print(results["comparison_table"])
    print(f"\n  Elapsed time: {elapsed / 60:.1f} minutes")
    print("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
