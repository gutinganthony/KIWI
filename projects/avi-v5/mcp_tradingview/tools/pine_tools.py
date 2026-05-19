"""Pine Script tools: create, update, and upload indicators to TradingView."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_PROJ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJ))

# Pine generation helpers live in src/pine_export.py (shared with run_dashboard.py)
from src.pine_export import generate_cpi_pine, generate_tsi_pine, generate_composite_pine


async def create_pine_indicator(name: str, source_code: str) -> dict:
    """Upload a Pine Script indicator to TradingView and add it to the chart.

    Opens the Pine Editor, pastes the code, saves as a new indicator,
    then adds it to the chart.

    Args:
        name: Indicator name (used for the save dialog)
        source_code: Complete Pine Script v5 source code

    Returns:
        {"ok": True, "name": name}
    """
    from mcp_tradingview.tradingview_bridge import ensure_bridge

    bridge = await ensure_bridge()
    page = bridge.page

    # Open Pine Editor
    await _open_pine_editor(page)
    await asyncio.sleep(0.8)

    # Clear existing code and paste new code
    editor = page.locator('.cm-content, .pine-editor-container .CodeMirror-code').first
    await editor.click()
    await page.keyboard.press("Control+A")
    await asyncio.sleep(0.1)
    await page.keyboard.type(source_code, delay=2)
    await asyncio.sleep(0.5)

    # Save
    await page.keyboard.press("Alt+s")
    await asyncio.sleep(1.0)

    # Handle "Save as" dialog if it appears
    title_input = page.locator('[placeholder*="name"], [placeholder*="title"]').first
    try:
        if await title_input.is_visible(timeout=1500):
            await title_input.fill(name)
            confirm_btn = page.locator('button:has-text("Save"), button:has-text("OK")').first
            await confirm_btn.click()
            await asyncio.sleep(0.5)
    except Exception:
        pass

    # Add to chart
    add_btn = page.locator('button:has-text("Add to chart"), [data-name="add-to-chart"]').first
    try:
        if await add_btn.is_visible(timeout=2000):
            await add_btn.click()
            await asyncio.sleep(1.0)
            logger.info("Pine indicator '%s' added to chart", name)
    except Exception:
        logger.warning("Could not find 'Add to chart' button — indicator may already be added")

    return {"ok": True, "name": name}


async def update_avi_indicators() -> dict:
    """Generate latest CPI + TSI + AVI values and push all three Pine Scripts.

    One-click update:
    1. Fetches fresh market data
    2. Computes CPI, TSI, AVI V5
    3. Fills Pine templates, writes *_current.pine files
    4. Uploads all three indicators to TradingView

    Returns:
        {"ok": True, "cpi": ..., "tsi": ..., "avi": ..., "files": [...], "uploaded": {...}}
    """
    import os
    import pandas as pd
    from src.tsi.data import TSIDataCollector
    from src.tsi import TechStressIndex
    from src.cpi.data import CPIDataCollector
    from src.cpi import CrashProbabilityIndex

    logger.info("Collecting CPI data...")
    cpi_data = CPIDataCollector().collect_all()
    cpi_result = CrashProbabilityIndex().compute(
        sp500_daily=cpi_data["sp500"],
        vix_daily=cpi_data.get("vix", pd.Series(dtype=float)),
        vix3m_daily=cpi_data.get("vix3m"),
        baa_daily=cpi_data.get("baa", pd.Series(dtype=float)),
        aaa_daily=cpi_data.get("aaa", pd.Series(dtype=float)),
        treasury_10y=cpi_data.get("t10y", pd.Series(dtype=float)),
        treasury_2y=cpi_data.get("t2y", pd.Series(dtype=float)),
    )

    logger.info("Collecting TSI data...")
    tsi_data = TSIDataCollector().collect_all()
    tsi_result = TechStressIndex().compute(
        sox_daily=tsi_data["sox"], qqq_daily=tsi_data["qqq"],
        mu_daily=tsi_data["mu"], smh_daily=tsi_data["smh"],
        spy_daily=tsi_data["spy"], treasury_10y=tsi_data["t10y"],
        vix_daily=tsi_data["vix"], treasury_30y=tsi_data.get("t30y"),
    )

    avi_score = None
    try:
        from src.pipeline.avi_v5_pipeline import AVIV5Pipeline
        fred_key = os.environ.get("FRED_API_KEY", "")
        if fred_key:
            pipeline = AVIV5Pipeline(fred_api_key=fred_key)
            avi_score = pipeline.run(verbose=False).avi_v4_score
    except Exception as e:
        logger.warning("AVI pipeline failed (non-fatal): %s", e)

    # Generate Pine files
    cpi_path = generate_cpi_pine(cpi_result)
    tsi_path = generate_tsi_pine(tsi_result)
    composite_path = generate_composite_pine(cpi_result, tsi_result, avi_score)

    # Upload each to TradingView
    uploaded = {}
    for label, path in [("CPI", cpi_path), ("TSI", tsi_path), ("AVI Composite", composite_path)]:
        code = Path(path).read_text(encoding="utf-8")
        r = await create_pine_indicator(name=label, source_code=code)
        uploaded[label] = r.get("ok", False)
        await asyncio.sleep(1.0)

    return {
        "ok": all(uploaded.values()),
        "cpi": round(cpi_result.score, 1),
        "tsi": round(tsi_result.score, 1),
        "avi": round(avi_score, 2) if avi_score else None,
        "files": [cpi_path, tsi_path, composite_path],
        "uploaded": uploaded,
    }


async def _open_pine_editor(page) -> None:
    """Open the TradingView Pine Script editor."""
    try:
        pine_btn = page.locator(
            '[data-name="pine-editor-button"], button[aria-label*="Pine"], '
            'button:has-text("Pine Editor")'
        ).first
        if await pine_btn.is_visible(timeout=2000):
            await pine_btn.click()
            return
    except Exception:
        pass
    await page.keyboard.press("Alt+p")
