"""TradingView browser automation via Playwright.

Manages a single persistent browser session for the MCP server lifetime.
Authentication uses a session cookie (more stable than username/password).

Setup:
    1. Log into TradingView in Chrome
    2. Open DevTools → Application → Cookies → tradingview.com
    3. Copy the value of `sessionid` cookie
    4. Set TV_SESSION_COOKIE=<value> in .env or environment
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TV_URL = "https://www.tradingview.com"
TV_CHART_URL = "https://www.tradingview.com/chart/"


class TradingViewBridge:
    """Manages a Playwright browser session connected to TradingView."""

    def __init__(self, session_cookie: Optional[str] = None, headless: bool = True):
        self._session_cookie = session_cookie or os.environ.get("TV_SESSION_COOKIE", "")
        self._headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._chart_ready = False

    async def start(self) -> None:
        """Launch browser and navigate to TradingView chart."""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        if self._session_cookie:
            await self._context.add_cookies([
                {
                    "name": "sessionid",
                    "value": self._session_cookie,
                    "domain": ".tradingview.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                    "sameSite": "None",
                }
            ])
            logger.info("Session cookie injected")
        else:
            logger.warning("No TV_SESSION_COOKIE set — running as guest (limited access)")

        self._page = await self._context.new_page()
        await self._page.goto(TV_CHART_URL, wait_until="domcontentloaded")
        await self._dismiss_popups()
        self._chart_ready = True
        logger.info("TradingView chart loaded")

    async def stop(self) -> None:
        """Close browser and Playwright."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._chart_ready = False
        logger.info("TradingView bridge closed")

    async def _dismiss_popups(self) -> None:
        """Dismiss common TradingView popups (cookie banner, login prompt)."""
        selectors = [
            '[data-name="accept-all"]',               # Cookie banner
            'button:has-text("Got it")',               # Feature notices
            '[aria-label="Close"]',                   # Generic close buttons
            '.tv-dialog__close',                      # Dialog close
        ]
        for sel in selectors:
            try:
                btn = self._page.locator(sel).first
                if await btn.is_visible(timeout=1500):
                    await btn.click()
                    await asyncio.sleep(0.3)
            except Exception:
                pass

    async def _wait_chart_ready(self, timeout: float = 10.0) -> None:
        """Wait until TradingView chart finishes loading."""
        if not self._chart_ready:
            raise RuntimeError("Bridge not started. Call start() first.")
        # Wait for the main chart canvas to be visible
        try:
            await self._page.wait_for_selector(
                'canvas[class*="chart-gui-wrapper"]',
                timeout=int(timeout * 1000),
            )
        except Exception:
            logger.debug("Chart canvas selector timeout — proceeding anyway")

    @property
    def page(self):
        """Direct access to Playwright Page for advanced tool use."""
        return self._page

    @property
    def is_ready(self) -> bool:
        return self._chart_ready


# Global singleton — the MCP server runs a single bridge instance.
_bridge: Optional[TradingViewBridge] = None


def get_bridge() -> TradingViewBridge:
    global _bridge
    if _bridge is None:
        _bridge = TradingViewBridge()
    return _bridge


async def ensure_bridge() -> TradingViewBridge:
    bridge = get_bridge()
    if not bridge.is_ready:
        await bridge.start()
    return bridge
