#!/usr/bin/env python3
"""CPI Dashboard — visual HTML dashboard + browser auto-open."""

import json
import os
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


def run_dashboard(date=None, verbose=False):
    from src.cpi.data import CPIDataCollector
    from src.cpi import CrashProbabilityIndex

    print("Collecting market data...")
    collector = CPIDataCollector()
    data = collector.collect_all(start="2024-01-01")

    print("Computing CPI...")
    cpi = CrashProbabilityIndex()
    result = cpi.compute(
        sp500_daily=data["sp500"],
        vix_daily=data["vix"],
        vix3m_daily=data.get("vix3m"),
        baa_daily=data["baa"],
        aaa_daily=data["aaa"],
        treasury_10y=data["treasury_10y"],
        treasury_2y=data["treasury_2y"],
        as_of=date,
    )

    # Build indicator data for template
    indicators_json = json.dumps([
        {"name": ind.name.replace("_", " ").title(), "signal": round(ind.signal), "status": ind.status}
        for ind in sorted(result.indicators, key=lambda x: -x.weighted_signal)
    ])

    flash_triggers = result.flash_alert.triggers if result.flash_alert.triggered else []

    # Read template
    template_path = PROJECT_ROOT / "dashboard" / "template.html"
    html = template_path.read_text()

    # Inject data
    html = html.replace("{{CPI_SCORE}}", f"{result.score:.0f}")
    html = html.replace("{{CPI_LEVEL}}", result.level)
    html = html.replace("{{CPI_DATE}}", result.date.strftime("%Y-%m-%d"))
    html = html.replace("{{INDICATORS_JSON}}", indicators_json)
    html = html.replace("{{FLASH_TRIGGERED}}", "true" if result.flash_alert.triggered else "false")
    html = html.replace("{{FLASH_TRIGGERS}}", json.dumps(flash_triggers))

    # Color mapping
    colors = {"LOW": "#00c853", "MODERATE": "#ffd600", "ELEVATED": "#ff9100", "HIGH": "#ff3d00", "CRITICAL": "#d50000"}
    html = html.replace("{{CPI_COLOR}}", colors.get(result.level, "#00c853"))

    # Action guidance
    actions = {
        "LOW": "Normal conditions. Standard risk management.",
        "MODERATE": "Stay aware. Monitor market dynamics.",
        "ELEVATED": "Review positions. Prepare hedging strategies.",
        "HIGH": "Reduce risk exposure. Tighten stop-losses.",
        "CRITICAL": "Immediate risk reduction. Raise cash levels.",
    }
    html = html.replace("{{ACTION_TEXT}}", actions.get(result.level, ""))

    # Write output
    output_path = PROJECT_ROOT / "dashboard" / "cpi_report.html"
    output_path.write_text(html)

    print(f"\nCPI Score: {result.score:.0f}/100 ({result.level})")
    if result.flash_alert.triggered:
        print(f"⚡ FLASH ALERT: {', '.join(flash_triggers)}")
    print(f"\nDashboard saved: {output_path}")
    print("Opening in browser...")

    webbrowser.open(f"file://{output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CPI Visual Dashboard")
    parser.add_argument("--date", help="Date to compute (YYYY-MM-DD)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    run_dashboard(args.date, args.verbose)


if __name__ == "__main__":
    main()
