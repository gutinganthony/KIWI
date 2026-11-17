"""Run TauricResearch/TradingAgents on one ticker and save the reports into this repo.

Called by .github/workflows/tradingagents.yml. Configuration comes from env:
  TA_TICKER     e.g. BE, 2303.TW, 8271.TWO (required)
  TA_DATE       YYYY-MM-DD analysis date (default: today, Asia/Taipei)
  TA_ANALYSTS   comma list of market,social,news,fundamentals
  TRADINGAGENTS_* overrides are applied by the package itself (provider, models, rounds).
"""
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from tradingagents.default_config import build_default_config
from tradingagents.graph.trading_graph import TradingAgentsGraph

HERE = Path(__file__).resolve().parent
VALID_ANALYSTS = {"market", "social", "news", "fundamentals"}


def main() -> int:
    ticker = os.environ.get("TA_TICKER", "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.\-=^]{0,14}", ticker):
        print(f"invalid ticker: {ticker!r}", file=sys.stderr)
        return 2

    date = os.environ.get("TA_DATE", "").strip() or datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d")
    datetime.strptime(date, "%Y-%m-%d")  # fail loudly on a malformed date

    analysts = [a.strip() for a in os.environ.get("TA_ANALYSTS", "market,news,fundamentals").split(",") if a.strip()]
    unknown = set(analysts) - VALID_ANALYSTS
    if not analysts or unknown:
        print(f"invalid analysts: {sorted(unknown) or 'empty'}", file=sys.stderr)
        return 2

    config = build_default_config()
    # The memory log lives in the repo so decisions settle and reflect across runs.
    config["memory_log_path"] = str(HERE / "memory" / "trading_memory.md")
    config["results_dir"] = str(HERE / ".runlogs")

    ta = TradingAgentsGraph(selected_analysts=tuple(analysts), config=config)
    ta.settle_all_pending()
    final_state, decision = ta.propagate(ticker, date)

    out = HERE / "reports" / ticker / date
    ta.save_reports(final_state, ticker, save_path=out)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"## {ticker} {date}: **{decision}**\n\n")
            f.write(f"Report: `projects/tradingagents/reports/{ticker}/{date}/complete_report.md`\n")
    print(f"{ticker} {date}: {decision}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
