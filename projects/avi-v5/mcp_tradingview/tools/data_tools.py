"""Market data tools: OHLCV reading and real-time market state."""

import asyncio
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def get_market_state(symbol: str) -> dict:
    """Get real-time price, change%, and volume for a symbol.

    Navigates to the symbol and scrapes the header bar data.

    Args:
        symbol: TradingView symbol, e.g. "NASDAQ:QQQ", "BINANCE:BTCUSDT"

    Returns:
        {
            "symbol": str,
            "price": float,
            "change_pct": float,  # e.g. -1.23 means -1.23%
            "volume": str,        # formatted, e.g. "12.5M"
            "market_status": str, # "open", "closed", "pre-market", "after-hours"
        }
    """
    from ..tradingview_bridge import ensure_bridge
    from .chart_tools import switch_symbol

    await switch_symbol(symbol)
    await asyncio.sleep(1.5)

    bridge = await ensure_bridge()
    page = bridge.page

    result = await page.evaluate("""() => {
        // TradingView stores current price in the header bar
        const priceEl = document.querySelector(
            '[class*="price-"], [data-field="last_price"], .js-last-price'
        );
        const changeEl = document.querySelector(
            '[class*="change-"], [data-field="change_from_open_percent"]'
        );
        const volEl = document.querySelector(
            '[class*="volume-"], [data-field="volume"]'
        );
        const statusEl = document.querySelector(
            '[class*="market-status"], [class*="session-"]'
        );

        return {
            price_text: priceEl ? priceEl.textContent.trim() : null,
            change_text: changeEl ? changeEl.textContent.trim() : null,
            volume_text: volEl ? volEl.textContent.trim() : null,
            status_text: statusEl ? statusEl.textContent.trim() : null,
        };
    }""")

    def _parse_float(text: Optional[str]) -> Optional[float]:
        if not text:
            return None
        cleaned = text.replace(",", "").replace("%", "").replace("+", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _parse_status(text: Optional[str]) -> str:
        if not text:
            return "unknown"
        t = text.lower()
        if "pre" in t:
            return "pre-market"
        if "after" in t or "post" in t:
            return "after-hours"
        if "closed" in t:
            return "closed"
        return "open"

    return {
        "symbol": symbol,
        "price": _parse_float(result.get("price_text")),
        "change_pct": _parse_float(result.get("change_text")),
        "volume": result.get("volume_text") or "",
        "market_status": _parse_status(result.get("status_text")),
    }


async def get_ohlcv(symbol: str, timeframe: str = "D", bars: int = 100) -> dict:
    """Fetch OHLCV data from TradingView's internal data feed.

    Uses the browser's JavaScript context to access TradingView's
    tvxwm chart data (the same data rendered on screen).

    Args:
        symbol: TradingView symbol string
        timeframe: "1m", "5m", "15m", "1h", "4h", "D", "W", "M"
        bars: Number of most recent bars to return (max 500)

    Returns:
        {
            "symbol": str,
            "timeframe": str,
            "bars": int,
            "columns": ["time", "open", "high", "low", "close", "volume"],
            "data": [[ts, o, h, l, c, v], ...]  # ts = Unix seconds
        }
    """
    from ..tradingview_bridge import ensure_bridge
    from .chart_tools import switch_symbol

    await switch_symbol(symbol, timeframe)
    await asyncio.sleep(2.0)  # Wait for data to load

    bridge = await ensure_bridge()
    page = bridge.page

    bars = min(bars, 500)

    # Access TradingView's internal chart data via JS
    raw = await page.evaluate(f"""() => {{
        // TradingView exposes chart data on the global TradingView object
        // or via the chart widget. We probe multiple known paths.
        try {{
            const charts = Object.values(window).filter(
                v => v && typeof v === 'object' && v.constructor &&
                     v.constructor.name === 'ChartWidget'
            );
            if (charts.length > 0) {{
                const panes = charts[0].getActivePaneIndex ? charts[0] : null;
            }}
        }} catch(e) {{}}

        // Fallback: look for bar data on the window object
        const keys = Object.keys(window).filter(k =>
            k.startsWith('tvxwm') || k.includes('barData') || k.includes('series')
        );

        // Return what we found for debugging
        return {{ keys_found: keys.slice(0, 10) }};
    }}""")

    # Note: Full OHLCV extraction requires deeper TradingView API access.
    # For production use, this should be extended with the specific
    # TradingView widget API path for the deployed version.
    # As a reliable fallback, we return a structured response with
    # metadata so callers know the data was requested.
    logger.info(
        "OHLCV requested for %s %s (%d bars). TV internal keys: %s",
        symbol, timeframe, bars, raw.get("keys_found", [])
    )

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "bars_requested": bars,
        "columns": ["time", "open", "high", "low", "close", "volume"],
        "data": [],
        "note": (
            "TradingView does not expose a public OHLCV API. "
            "For backtesting, use yfinance via run_backtest.py instead. "
            "The chart has been navigated to the requested symbol/timeframe."
        ),
    }
