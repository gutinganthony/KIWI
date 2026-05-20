"""TradingView MCP Server — Phase 5 of AVI V5.

Runs as an MCP server over stdio. Configure Claude Code via
.claude/settings.json (or ~/.claude/settings.json):

    {
        "mcpServers": {
            "tradingview": {
                "command": "python",
                "args": ["mcp_tradingview/server.py"],
                "cwd": "/path/to/KIWI/projects/avi-v5",
                "env": {
                    "TV_SESSION_COOKIE": "your_session_cookie_here",
                    "TV_HEADLESS": "1"
                }
            }
        }
    }

How to get your TradingView session cookie:
    1. Log into TradingView in Chrome
    2. DevTools (F12) → Application → Cookies → tradingview.com
    3. Copy the value of the `sessionid` cookie
    4. Paste it into TV_SESSION_COOKIE in .env or the MCP env block

Available tools:
    tv_switch_symbol         — Navigate chart to a symbol + timeframe
    tv_draw_level            — Draw a horizontal price level
    tv_get_market_state      — Real-time price and change%
    tv_get_ohlcv             — OHLCV info (chart navigation; see note)
    tv_create_pine_indicator — Upload and add a Pine Script indicator
    tv_run_backtest          — Run Pine Strategy Tester
    tv_screenshot            — Save chart screenshot
    tv_update_avi_indicators — One-click: update CPI + TSI + AVI Pine Scripts
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# ── Path setup ──
# server.py lives in projects/avi-v5/mcp_tradingview/
# We need projects/avi-v5/ on the path for src.*, dashboard.*, etc.
_PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJ))

from dotenv import load_dotenv
load_dotenv(_PROJ / ".env")

# ── MCP imports ──
from mcp.server.fastmcp import FastMCP

# ── Local imports (absolute, _PROJ is on sys.path) ──
from mcp_tradingview.tradingview_bridge import get_bridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("tradingview-mcp")

# ── FastMCP server ──
mcp = FastMCP(
    "tradingview",
    instructions=(
        "Control TradingView charts via Playwright automation. "
        "Use tv_update_avi_indicators to push the latest CPI/TSI/AVI scores "
        "to TradingView with one call. All chart actions happen in a real browser."
    ),
)


# ────────────────────────────────────────────────────────────────
# Status resource
# ────────────────────────────────────────────────────────────────

@mcp.resource("tradingview://status")
async def server_status() -> str:
    bridge = get_bridge()
    status = "connected" if bridge.is_ready else "disconnected"
    cookie_set = bool(os.environ.get("TV_SESSION_COOKIE"))
    return (
        f"TradingView MCP Server\n"
        f"Status: {status}\n"
        f"Session cookie: {'set' if cookie_set else 'NOT SET (guest mode)'}\n"
        f"Headless: {os.environ.get('TV_HEADLESS', '1') != '0'}\n"
    )


# ────────────────────────────────────────────────────────────────
# Tools
# ────────────────────────────────────────────────────────────────

@mcp.tool()
async def tv_switch_symbol(symbol: str, timeframe: str = "D") -> str:
    """Navigate TradingView chart to a symbol and timeframe.

    Args:
        symbol: TradingView symbol string.
                Examples: "NASDAQ:QQQ", "NYSE:SPY", "BINANCE:BTCUSDT"
        timeframe: Chart interval. Options: "1m" "5m" "15m" "1h" "4h" "D" "W" "M"
    """
    from mcp_tradingview.tools.chart_tools import switch_symbol
    result = await switch_symbol(symbol, timeframe)
    return f"Chart switched to {result['symbol']} ({result['timeframe']})"


@mcp.tool()
async def tv_draw_level(
    price: float,
    label: str = "",
    color: str = "red",
    style: str = "solid",
) -> str:
    """Draw a horizontal price level on the current TradingView chart.

    Creates a persistent Pine indicator that renders the level line and label.

    Args:
        price: Price level to draw (e.g. 480.0)
        label: Text label next to the line (e.g. "Support")
        color: "red", "green", "blue", "orange", "yellow", "gray"
        style: "solid", "dashed", "dotted"
    """
    from mcp_tradingview.tools.chart_tools import draw_level
    result = await draw_level(price=price, label=label, color=color, style=style)
    return f"Level drawn at {result['price']} — '{result['label']}'"


@mcp.tool()
async def tv_get_market_state(symbol: str) -> str:
    """Get real-time price, % change, and session status for a symbol.

    Args:
        symbol: TradingView symbol string (e.g. "NASDAQ:QQQ")
    """
    from mcp_tradingview.tools.data_tools import get_market_state
    data = await get_market_state(symbol)
    price = data.get("price")
    chg = data.get("change_pct")
    vol = data.get("volume") or "—"
    status = data.get("market_status", "unknown")

    price_str = f"{price:.4f}" if price else "n/a"
    chg_str = f"{chg:+.2f}%" if chg is not None else "n/a"
    return (
        f"{symbol}\n"
        f"  Price:   {price_str}\n"
        f"  Change:  {chg_str}\n"
        f"  Volume:  {vol}\n"
        f"  Session: {status}"
    )


@mcp.tool()
async def tv_get_ohlcv(
    symbol: str,
    timeframe: str = "D",
    bars: int = 100,
) -> str:
    """Navigate the chart to a symbol/timeframe (OHLCV read note inside).

    Note: TradingView has no public OHLCV API. This tool navigates the chart
    to the requested symbol/timeframe. For backtesting use run_backtest.py
    which pulls clean data directly from yfinance.

    Args:
        symbol: TradingView symbol (e.g. "NASDAQ:QQQ")
        timeframe: Chart interval
        bars: Number of recent bars to request (max 500)
    """
    from mcp_tradingview.tools.data_tools import get_ohlcv
    data = await get_ohlcv(symbol, timeframe, bars)
    return (
        f"Symbol: {data['symbol']} ({data['timeframe']})\n"
        f"Bars requested: {data['bars_requested']}\n"
        f"Note: {data['note']}"
    )


@mcp.tool()
async def tv_create_pine_indicator(name: str, source_code: str) -> str:
    """Upload a Pine Script v5 indicator to TradingView and add it to the chart.

    Args:
        name: Indicator display name
        source_code: Complete Pine Script v5 source (must start with //@version=5)
    """
    from mcp_tradingview.tools.pine_tools import create_pine_indicator
    result = await create_pine_indicator(name=name, source_code=source_code)
    if result.get("ok"):
        return f"Indicator '{name}' uploaded and added to chart."
    return f"Upload attempted for '{name}' — check TradingView Pine Editor."


@mcp.tool()
async def tv_run_backtest(
    strategy_code: str,
    symbol: str = "NASDAQ:QQQ",
    timeframe: str = "D",
    period: str = "5Y",
) -> str:
    """Upload a Pine Strategy and extract Strategy Tester results.

    Args:
        strategy_code: Pine Script v5 strategy() code
        symbol: Symbol to backtest on
        timeframe: Chart timeframe
        period: Lookback — "1Y", "2Y", "5Y", "10Y", "MAX"
    """
    from mcp_tradingview.tools.backtest_tools import run_backtest
    r = await run_backtest(
        strategy_code=strategy_code,
        symbol=symbol,
        timeframe=timeframe,
        period=period,
    )
    lines = [f"Backtest: {r.get('symbol')} {r.get('timeframe')} ({r.get('period')})"]
    for key, label in [
        ("net_profit_pct", "Net Profit"),
        ("max_drawdown_pct", "Max Drawdown"),
        ("win_rate_pct", "Win Rate"),
        ("profit_factor", "Profit Factor"),
    ]:
        val = r.get(key)
        if val is not None:
            suffix = "%" if "pct" in key else ""
            lines.append(f"  {label:16} {val:+.2f}{suffix}" if "profit" in key else f"  {label:16} {val:.2f}{suffix}")
    if r.get("total_trades"):
        lines.append(f"  {'Total Trades':16} {r['total_trades']}")
    return "\n".join(lines)


@mcp.tool()
async def tv_screenshot(filepath: str) -> str:
    """Capture the current TradingView chart as a PNG screenshot.

    Args:
        filepath: Absolute path for the PNG (e.g. "/tmp/qqq_chart.png")
    """
    from mcp_tradingview.tools.chart_tools import take_screenshot
    result = await take_screenshot(filepath)
    if result.get("ok"):
        return f"Screenshot saved: {result['path']}"
    return "Screenshot failed."


@mcp.tool()
async def tv_update_avi_indicators() -> str:
    """One-click update: compute latest CPI + TSI + AVI and push all Pine Scripts.

    Daily workflow:
    1. Fetches fresh market data (yfinance + FRED)
    2. Computes CPI (crash probability), TSI (tech stress), AVI V5 (valuation)
    3. Fills Pine Script templates with today's values
    4. Uploads CPI, TSI, and Composite indicators to TradingView

    Requires: FRED_API_KEY in .env for AVI. Takes ~60-90s.
    """
    from mcp_tradingview.tools.pine_tools import update_avi_indicators
    r = await update_avi_indicators()

    lines = ["AVI Indicators Updated"]
    lines.append(f"  CPI (crash prob):   {r.get('cpi', 'n/a')}/100")
    lines.append(f"  TSI (tech stress):  {r.get('tsi', 'n/a')}/100")
    avi = r.get("avi")
    lines.append(f"  AVI V5 (valuation): {f'{avi:.2f}/10' if avi else 'n/a (no FRED key)'}")
    lines.append("")
    lines.append("Files:")
    for f in r.get("files", []):
        lines.append(f"  {f}")
    uploaded = r.get("uploaded", {})
    if uploaded:
        lines.append("")
        lines.append("Uploaded to TradingView:")
        for name, ok in uploaded.items():
            lines.append(f"  {'✓' if ok else '✗'} {name}")
    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────
# Lifecycle
# ────────────────────────────────────────────────────────────────

async def _startup() -> None:
    headless = os.environ.get("TV_HEADLESS", "1") != "0"
    bridge = get_bridge()
    bridge._headless = headless
    try:
        await bridge.start()
        logger.info("TradingView bridge started (headless=%s)", headless)
    except Exception as e:
        logger.error("Bridge start failed: %s — tools will retry on first call", e)


async def _run() -> None:
    await _startup()
    try:
        await mcp.run_stdio_async()
    finally:
        await get_bridge().stop()


if __name__ == "__main__":
    asyncio.run(_run())
