"""Backtest tools: run Pine Strategy Tester and parse results."""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def run_backtest(
    strategy_code: str,
    symbol: str,
    timeframe: str = "D",
    period: str = "5Y",
) -> dict:
    """Upload a Pine Strategy to TradingView and extract backtest results.

    Args:
        strategy_code: Complete Pine Script v5 strategy() source code
        symbol: Symbol to test on, e.g. "NASDAQ:QQQ"
        timeframe: Chart timeframe for the backtest
        period: Lookback period: "1Y", "2Y", "5Y", "10Y", "MAX"

    Returns:
        {
            "ok": bool,
            "symbol": str,
            "net_profit_pct": float,
            "max_drawdown_pct": float,
            "total_trades": int,
            "win_rate_pct": float,
            "profit_factor": float,
            "sharpe_ratio": float,  # if available
        }
    """
    from ..tradingview_bridge import ensure_bridge
    from .chart_tools import switch_symbol
    from .pine_tools import create_pine_indicator

    # Navigate to symbol
    await switch_symbol(symbol, timeframe)
    await asyncio.sleep(1.0)

    # Upload strategy
    await create_pine_indicator(name="AVI_Backtest_Strategy", source_code=strategy_code)
    await asyncio.sleep(2.0)

    bridge = await ensure_bridge()
    page = bridge.page

    # Open Strategy Tester tab
    try:
        st_tab = page.locator(
            '[data-name="strategy-tester"], button:has-text("Strategy Tester")'
        ).first
        if await st_tab.is_visible(timeout=3000):
            await st_tab.click()
            await asyncio.sleep(1.5)
    except Exception:
        logger.warning("Could not find Strategy Tester tab")

    # Set date range
    await _set_backtest_period(page, period)
    await asyncio.sleep(1.0)

    # Extract results
    results = await _parse_strategy_results(page)
    results.update({"symbol": symbol, "timeframe": timeframe, "period": period})
    return results


async def _set_backtest_period(page, period: str) -> None:
    """Set the date range in Strategy Tester."""
    period_map = {
        "1Y": "1 year", "2Y": "2 years", "5Y": "5 years",
        "10Y": "10 years", "MAX": "All time",
    }
    label = period_map.get(period.upper(), period)
    try:
        period_btn = page.locator(
            f'button:has-text("{label}"), [aria-label*="{label}"]'
        ).first
        if await period_btn.is_visible(timeout=2000):
            await period_btn.click()
            await asyncio.sleep(0.5)
    except Exception:
        logger.debug("Period selector not found for: %s", period)


async def _parse_strategy_results(page) -> dict:
    """Scrape Strategy Tester performance summary table."""
    raw = await page.evaluate("""() => {
        const result = {};

        const findMetric = (labels) => {
            for (const label of labels) {
                const els = document.querySelectorAll(
                    '[class*="performance"], [class*="report"], [class*="strategy-report"]'
                );
                for (const el of els) {
                    const text = el.textContent;
                    if (text.includes(label)) {
                        // Try to extract the number next to it
                        const match = text.match(new RegExp(label + '[\\s\\S]*?([\\-+]?[\\d,]+\\.?\\d*%?)'));
                        if (match) return match[1];
                    }
                }
            }
            return null;
        };

        result.net_profit = findMetric(['Net Profit', 'Net profit']);
        result.max_drawdown = findMetric(['Max Drawdown', 'Max. Drawdown']);
        result.total_trades = findMetric(['Total Closed Trades', 'Total trades']);
        result.win_rate = findMetric(['Percent Profitable', 'Win rate', 'Win Rate']);
        result.profit_factor = findMetric(['Profit Factor', 'Profit factor']);

        return result;
    }""")

    def _pct(val: Optional[str]) -> Optional[float]:
        if not val:
            return None
        return float(val.replace("%", "").replace(",", "").strip())

    def _float(val: Optional[str]) -> Optional[float]:
        if not val:
            return None
        try:
            return float(val.replace(",", "").strip())
        except ValueError:
            return None

    return {
        "ok": True,
        "net_profit_pct": _pct(raw.get("net_profit")),
        "max_drawdown_pct": _pct(raw.get("max_drawdown")),
        "total_trades": int(_float(raw.get("total_trades")) or 0),
        "win_rate_pct": _pct(raw.get("win_rate")),
        "profit_factor": _float(raw.get("profit_factor")),
    }
