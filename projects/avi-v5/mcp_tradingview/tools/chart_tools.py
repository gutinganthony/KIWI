"""Chart manipulation tools: symbol switching, drawing levels."""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TIMEFRAME_MAP = {
    "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
    "1h": "60", "2h": "120", "4h": "240",
    "D": "D", "1D": "D", "W": "W", "1W": "W", "M": "M", "1M": "M",
}

COLOR_MAP = {
    "red": "#FF4444", "green": "#00AA88", "blue": "#2962FF",
    "orange": "#FF9800", "yellow": "#FFEB3B", "white": "#FFFFFF",
    "gray": "#888888", "purple": "#9C27B0",
}


async def switch_symbol(symbol: str, timeframe: str = "D") -> dict:
    """Navigate TradingView chart to a new symbol and timeframe.

    Args:
        symbol: TradingView symbol string, e.g. "NASDAQ:QQQ", "BINANCE:BTCUSDT"
        timeframe: "1m", "5m", "15m", "1h", "4h", "D", "W", "M"

    Returns:
        {"ok": True, "symbol": ..., "timeframe": ...}
    """
    from ..tradingview_bridge import ensure_bridge

    bridge = await ensure_bridge()
    page = bridge.page

    # Use TradingView keyboard shortcut to open symbol search
    await page.keyboard.press("Escape")
    await asyncio.sleep(0.2)

    # Press / to open symbol search
    await page.keyboard.press("/")
    await asyncio.sleep(0.5)

    # Type symbol
    search_input = page.locator('[data-name="search-market-input"]')
    await search_input.wait_for(timeout=3000)
    await search_input.fill(symbol)
    await asyncio.sleep(0.8)

    # Select first result
    first_result = page.locator('[data-name="market-item"]').first
    await first_result.click()
    await asyncio.sleep(0.5)

    # Switch timeframe
    tv_tf = TIMEFRAME_MAP.get(timeframe, timeframe)
    await _set_timeframe(page, tv_tf)

    logger.info("Switched to %s %s", symbol, timeframe)
    return {"ok": True, "symbol": symbol, "timeframe": timeframe}


async def _set_timeframe(page, tv_tf: str) -> None:
    """Click the timeframe button matching tv_tf."""
    try:
        # Try clicking the timeframe selector directly
        tf_btn = page.locator(f'[data-value="{tv_tf}"]').first
        if await tf_btn.is_visible(timeout=2000):
            await tf_btn.click()
            await asyncio.sleep(0.3)
            return
    except Exception:
        pass

    # Fallback: keyboard shortcut for common timeframes
    shortcuts = {"D": "D", "W": "W", "M": "M"}
    if tv_tf in shortcuts:
        await page.keyboard.press(shortcuts[tv_tf])


async def draw_level(
    price: float,
    label: str = "",
    color: str = "red",
    style: str = "solid",
    extend: bool = True,
) -> dict:
    """Draw a horizontal price level on the active TradingView chart.

    Uses TradingView's Pine Script object model via the drawing toolbar.
    Injects a tiny Pine indicator to render the line persistently.

    Args:
        price: Price level to draw
        label: Text label for the line
        color: "red", "green", "blue", "orange", "yellow", "gray", or hex
        style: "solid", "dashed", "dotted"
        extend: Extend line to the right edge

    Returns:
        {"ok": True, "price": ..., "label": ...}
    """
    hex_color = COLOR_MAP.get(color, color)
    line_style = {
        "solid": "line.style_solid",
        "dashed": "line.style_dashed",
        "dotted": "line.style_dotted",
    }.get(style, "line.style_solid")

    extend_opt = "extend.right" if extend else "extend.none"
    label_text = label or f"{price:.4f}"

    pine_code = f"""//@version=5
indicator("Level {price:.4f}", overlay=true)
var line lvl = na
var label lbl = na
if barstate.isfirst
    lvl := line.new(bar_index, {price}, bar_index + 1, {price},
                    color=color.new(color.fromHex("{hex_color}"), 0),
                    style={line_style}, width=1, extend={extend_opt})
    lbl := label.new(bar_index, {price}, "{label_text}",
                     color=color.new(color.fromHex("{hex_color}"), 20),
                     textcolor=color.white, style=label.style_label_right,
                     size=size.small)
"""
    from .pine_tools import create_pine_indicator
    result = await create_pine_indicator(
        name=f"Level_{price:.4f}",
        source_code=pine_code,
    )
    return {"ok": result.get("ok", False), "price": price, "label": label_text}


async def take_screenshot(filepath: str) -> dict:
    """Save a screenshot of the current TradingView chart.

    Args:
        filepath: Absolute path where the PNG will be saved.

    Returns:
        {"ok": True, "path": filepath}
    """
    from ..tradingview_bridge import ensure_bridge

    bridge = await ensure_bridge()
    page = bridge.page

    # Hide UI chrome for a clean chart screenshot
    await page.evaluate("""
        document.querySelectorAll(
            '.header-chart-panel, .chart-toolbar, .tv-side-toolbar'
        ).forEach(el => el.style.opacity = '0');
    """)
    await asyncio.sleep(0.3)

    await page.screenshot(path=filepath, full_page=False)

    # Restore UI
    await page.evaluate("""
        document.querySelectorAll(
            '.header-chart-panel, .chart-toolbar, .tv-side-toolbar'
        ).forEach(el => el.style.opacity = '1');
    """)

    logger.info("Screenshot saved: %s", filepath)
    return {"ok": True, "path": filepath}
