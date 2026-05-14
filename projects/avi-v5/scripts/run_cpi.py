#!/usr/bin/env python3
"""CLI for Crash Probability Index (CPI).

Usage:
    # Current CPI score
    python3 scripts/run_cpi.py

    # Backtest against historical crashes
    python3 scripts/run_cpi.py --backtest

    # Specific date
    python3 scripts/run_cpi.py --date 2020-02-15
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")


def setup_logging(verbose: bool = False):
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


def run_current(date: str = None, verbose: bool = False):
    from src.cpi import CrashProbabilityIndex
    from src.cpi.data import CPIDataCollector

    logger = logging.getLogger("cpi_current")
    logger.info("=" * 65)
    logger.info("  Crash Probability Index (CPI) — Current Reading")
    logger.info("=" * 65)

    collector = CPIDataCollector()
    data = collector.collect_all(start="2020-01-01")

    cpi = CrashProbabilityIndex()
    result = cpi.compute(
        sp500_daily=data["sp500"],
        vix_daily=data["vix"],
        vix3m_daily=data.get("vix3m"),
        baa_daily=data["baa"],
        aaa_daily=data["aaa"],
        treasury_10y=data["t10y"],
        treasury_2y=data["t2y"],
        as_of=date,
    )

    print(result.summary())


def run_backtest(verbose: bool = False):
    from src.cpi.backtest import run_cpi_backtest
    from src.cpi.data import CPIDataCollector

    logger = logging.getLogger("cpi_backtest")
    logger.info("=" * 65)
    logger.info("  CPI BACKTEST — Short-Term Crash Detection")
    logger.info("=" * 65)

    start_time = time.time()

    collector = CPIDataCollector()
    data = collector.collect_all(start="2016-01-01")

    result = run_cpi_backtest(data)
    print(result)

    elapsed = time.time() - start_time
    print(f"\n  Elapsed time: {elapsed / 60:.1f} minutes")


def main():
    parser = argparse.ArgumentParser(description="Crash Probability Index (CPI)")
    parser.add_argument("--backtest", action="store_true", help="Run historical backtest")
    parser.add_argument("--date", type=str, default=None, help="Compute CPI for specific date")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.backtest:
        run_backtest(args.verbose)
    else:
        run_current(args.date, args.verbose)


if __name__ == "__main__":
    main()
