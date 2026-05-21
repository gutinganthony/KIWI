#!/usr/bin/env python3
"""Daily market alert — compute CPI + TSI + AVI and send via Telegram.

Setup:
  1. Telegram: message @BotFather → /newbot → get TOKEN
  2. Telegram: message @userinfobot → get your CHAT_ID
  3. Set env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, FRED_API_KEY

Usage:
  python3 scripts/notify.py              # Send alert now
  python3 scripts/notify.py --dry-run    # Print without sending
"""

import argparse
import json
import logging
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("notify")


def send_telegram(token, chat_id, message):
    """Send message via Telegram Bot API (no external library needed)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def compute_tsi():
    """Compute today's TSI score."""
    try:
        from src.tsi.data import TSIDataCollector
        from src.tsi import TechStressIndex
        collector = TSIDataCollector()
        data = collector.collect_all()
        tsi = TechStressIndex()
        result = tsi.compute(
            sox_daily=data["sox"], qqq_daily=data["qqq"],
            mu_daily=data["mu"], smh_daily=data["smh"],
            spy_daily=data["spy"], treasury_10y=data["t10y"],
            vix_daily=data["vix"], treasury_30y=data.get("t30y"),
        )
        return result.score, result.bias, result.flash_alert, result.flash_reason
    except Exception as e:
        logger.error(f"TSI failed: {e}")
        return None, None, False, ""


def compute_cpi():
    """Compute today's CPI score."""
    try:
        import pandas as pd
        from src.cpi.data import CPIDataCollector
        from src.cpi import CrashProbabilityIndex
        collector = CPIDataCollector()
        data = collector.collect_all()
        cpi = CrashProbabilityIndex()
        result = cpi.compute(
            sp500_daily=data["sp500"],
            vix_daily=data.get("vix", pd.Series(dtype=float)),
            vix3m_daily=data.get("vix3m"),
            baa_daily=data.get("baa", pd.Series(dtype=float)),
            aaa_daily=data.get("aaa", pd.Series(dtype=float)),
            treasury_10y=data.get("t10y", pd.Series(dtype=float)),
            treasury_2y=data.get("t2y", pd.Series(dtype=float)),
        )
        return result.score, result.level, result.flash_alert.triggered
    except Exception as e:
        logger.error(f"CPI failed: {e}")
        return None, None, False


def compute_avi():
    """Compute current AVI V5 score."""
    try:
        from src.pipeline.avi_v5_pipeline import AVIV5Pipeline
        fred_key = os.environ.get("FRED_API_KEY", "")
        if not fred_key:
            return None
        pipeline = AVIV5Pipeline(fred_api_key=fred_key)
        result = pipeline.run(verbose=False)
        return result.avi_v4_score
    except Exception as e:
        logger.error(f"AVI failed: {e}")
        return None


def level_emoji(score, system):
    """Get emoji for score level."""
    if score is None:
        return "⚪"
    if system == "cpi":
        if score >= 50: return "🔴"
        if score >= 35: return "🟠"
        if score >= 20: return "🟡"
        return "🟢"
    elif system == "tsi":
        if score >= 60: return "🔴"
        if score >= 40: return "🟠"
        if score >= 22: return "🟡"
        return "🟢"
    elif system == "avi":
        if score >= 7: return "🔴"
        if score >= 5: return "🟠"
        if score >= 3: return "🟡"
        return "🟢"
    return "⚪"


def fetch_market_snapshot():
    """Fetch quick market snapshot from yfinance (no API key needed)."""
    snap = {"sp500": None, "vix": None, "t10y": None, "t30y": None}
    try:
        import yfinance as yf
        tickers = yf.download(
            ["^GSPC", "^VIX", "^TNX", "^TYX"],
            period="2d", auto_adjust=True, progress=False
        )
        closes = tickers["Close"].iloc[-1]
        snap["sp500"] = float(closes.get("^GSPC", 0) or 0) or None
        snap["vix"]   = float(closes.get("^VIX",  0) or 0) or None
        snap["t10y"]  = float(closes.get("^TNX",  0) or 0) or None  # ^TNX is in %
        snap["t30y"]  = float(closes.get("^TYX",  0) or 0) or None  # ^TYX is in %
    except Exception as e:
        logger.warning(f"Market snapshot failed: {e}")
    return snap


def build_message():
    """Build the daily alert message aligned with the Dashboard layout."""
    today = datetime.now().strftime("%Y-%m-%d %a")

    logger.info("Computing TSI...")
    tsi_score, tsi_bias, tsi_flash, tsi_flash_reason = compute_tsi()

    logger.info("Computing CPI...")
    cpi_score, cpi_level, cpi_flash = compute_cpi()

    logger.info("Computing AVI...")
    avi_score = compute_avi()

    logger.info("Fetching market snapshot...")
    snap = fetch_market_snapshot()

    cpi_val = cpi_score or 0
    tsi_val = tsi_score or 0
    avi_val = avi_score or 0

    # ── Flash alerts ──
    alerts = []
    if cpi_flash:
        alerts.append("CPI Flash Alert ⚡")
    if tsi_flash and tsi_flash_reason:
        alerts.append(f"TSI Flash: {tsi_flash_reason}")

    # ── Combined signal ──
    if cpi_val >= 35 and tsi_val >= 55:
        signal_line = "🔴 <b>雙重壓力</b>：積極減倉 + 建立避險"
    elif cpi_val >= 35:
        signal_line = "🟠 <b>崩盤概率升高</b>：檢查持倉，準備避險"
    elif tsi_val >= 60:
        signal_line = "🔴 <b>科技壓力高</b>：減科技曝險"
    elif tsi_val >= 45 or avi_val >= 6:
        signal_line = "🟡 <b>謹慎持有</b>：不追高，留意觸發條件"
    elif cpi_val >= 20:
        signal_line = "🟡 <b>留意</b>：掃一眼哪個指標在升溫"
    else:
        signal_line = "🟢 <b>正常</b>：照常操作"

    # ── Build message ──
    lines = [
        f"<b>📊 每日市場體溫</b>  <i>{today}</i>",
        "─────────────────",
    ]

    # Scores
    cpi_d = f"{cpi_val:.0f}" if cpi_score is not None else "──"
    tsi_d = f"{tsi_val:.0f}" if tsi_score is not None else "──"
    avi_d = f"{avi_val:.1f}" if avi_score is not None else "──"
    cpi_l = cpi_level or "──"
    tsi_b = tsi_bias or "──"

    lines.append(f"{level_emoji(cpi_score, 'cpi')} <b>CPI</b>  {cpi_d}/100  <i>{cpi_l}</i>")
    lines.append(f"{level_emoji(tsi_score, 'tsi')} <b>TSI</b>  {tsi_d}/100  <i>{tsi_b}</i>")
    lines.append(f"{level_emoji(avi_score, 'avi')} <b>AVI</b>  {avi_d}/10")

    # Flash alerts
    if alerts:
        lines.append("")
        for a in alerts:
            lines.append(f"⚡ {a}")

    # Market snapshot
    snap_parts = []
    if snap["sp500"]:
        snap_parts.append(f"S&amp;P {snap['sp500']:,.0f}")
    if snap["vix"]:
        snap_parts.append(f"VIX {snap['vix']:.1f}")
    if snap["t10y"]:
        snap_parts.append(f"10Y {snap['t10y']:.2f}%")
    if snap["t30y"]:
        snap_parts.append(f"30Y {snap['t30y']:.2f}%")
    if snap_parts:
        lines.append("")
        lines.append("  ".join(snap_parts))

    # Combined signal
    lines.append("")
    lines.append(signal_line)

    # Trigger reminders
    lines.append("")
    lines.append("<i>觸發條件：TSI&gt;55 減倉 · CPI&gt;35 避險 · 雙高立即行動</i>")

    # Dashboard link
    lines.append("")
    lines.append("🌐 <a href=\"https://gutinganthony.github.io/KIWI/\">查看完整 Dashboard</a>")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Daily market alert via Telegram")
    parser.add_argument("--dry-run", action="store_true", help="Print message without sending")
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)

    # Load .env manually (no dotenv dependency needed)
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

    message = build_message()

    if args.dry_run:
        # Convert HTML to plain text for terminal display
        import re
        plain = re.sub(r"<[^>]+>", "", message)
        print(plain)
        return

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        print("Set them in .env or environment variables")
        print("\nMessage preview:")
        import re
        print(re.sub(r"<[^>]+>", "", message))
        return

    logger.info("Sending Telegram alert...")
    result = send_telegram(token, chat_id, message)
    if result.get("ok"):
        logger.info("✅ Alert sent successfully!")
    else:
        logger.error(f"Failed: {result}")


if __name__ == "__main__":
    main()
