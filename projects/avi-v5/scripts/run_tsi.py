#!/usr/bin/env python3
"""Tech Stress Index (TSI) — daily tech sector crash/rally predictor.

Usage:
    python3 scripts/run_tsi.py              # Current TSI score
    python3 scripts/run_tsi.py --history 30 # Show 30-day trend
"""

import argparse
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    if not verbose:
        for name in ["yfinance", "urllib3", "peewee"]:
            logging.getLogger(name).setLevel(logging.WARNING)


def main():
    parser = argparse.ArgumentParser(description="Tech Stress Index (TSI)")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--history", type=int, default=0, help="Show N-day historical TSI")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger("tsi")

    logger.info("=" * 60)
    logger.info("  Tech Stress Index (TSI)")
    logger.info("=" * 60)

    start_time = time.time()

    from src.tsi.data import TSIDataCollector
    from src.tsi import TechStressIndex

    logger.info("Collecting data...")
    collector = TSIDataCollector()
    data = collector.collect_all()

    tsi = TechStressIndex()

    if args.history > 0:
        # Show historical trend
        dates = data["sox"].index[-args.history:]
        print(f"\n{'Date':<12} {'TSI':>5} {'Bias':<10} {'Bar'}")
        print("-" * 50)
        for dt in dates:
            try:
                result = tsi.compute(
                    sox_daily=data["sox"], qqq_daily=data["qqq"],
                    mu_daily=data["mu"], smh_daily=data["smh"],
                    spy_daily=data["spy"], treasury_10y=data["t10y"],
                    vix_daily=data["vix"], as_of=dt.strftime("%Y-%m-%d"),
                )
                bar = "█" * int(result.score / 5)
                flash = " ⚡" if result.flash_alert else ""
                print(f"{dt.strftime('%Y-%m-%d'):<12} {result.score:>5.0f} {result.bias:<10} {bar}{flash}")
            except Exception:
                pass
        print()
    else:
        result = tsi.compute(
            sox_daily=data["sox"], qqq_daily=data["qqq"],
            mu_daily=data["mu"], smh_daily=data["smh"],
            spy_daily=data["spy"], treasury_10y=data["t10y"],
            vix_daily=data["vix"], as_of=args.date,
        )
        print(result.summary())

    elapsed = time.time() - start_time
    logger.info(f"Elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
