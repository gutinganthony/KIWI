#!/usr/bin/env python3
"""Daily market alert — reads pre-computed data from docs/index.html and sends via Telegram.

Data source: KIWI_DATA JSON embedded in docs/index.html (written by update_dashboard.py).
This guarantees Telegram and Dashboard always show the same numbers.

Setup:
  1. Telegram: message @BotFather → /newbot → get TOKEN
  2. Telegram: message @userinfobot → get your CHAT_ID
  3. Set env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

Usage:
  python3 scripts/notify.py              # Send alert now
  python3 scripts/notify.py --dry-run    # Print without sending
"""

import argparse
import json
import logging
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_INDEX = PROJECT_ROOT.parent.parent / "docs" / "index.html"

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


def load_dashboard_data():
    """Extract KIWI_DATA JSON from docs/index.html."""
    if not DOCS_INDEX.exists():
        raise FileNotFoundError(f"Dashboard not found: {DOCS_INDEX}")
    html = DOCS_INDEX.read_text(encoding="utf-8")
    match = re.search(
        r"//\s*\[KIWI-DATA-START\].*?(?:var|const|let)\s+KIWI_DATA\s*=\s*(\{.*?\});\s*//\s*\[KIWI-DATA-END\]",
        html, re.DOTALL
    )
    if not match:
        raise ValueError("KIWI_DATA block not found in index.html")
    return json.loads(match.group(1))


def level_emoji(score, system):
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


def build_message(data):
    """Build the daily alert message from dashboard data."""
    today = datetime.now().strftime("%Y-%m-%d %a")

    cpi_score = data.get("cpi", {}).get("score")
    cpi_level = data.get("cpi", {}).get("level", "──")
    cpi_flash = data.get("cpi", {}).get("flash", False)

    tsi_score = data.get("tsi", {}).get("score")
    tsi_bias  = data.get("tsi", {}).get("bias", "──")
    tsi_flash = data.get("tsi", {}).get("flash", False)

    avi_score = data.get("avi", {}).get("score")

    snap_sp500 = data.get("market", {}).get("sp500")
    snap_vix   = data.get("market", {}).get("vix")
    snap_t10y  = data.get("market", {}).get("t10y")
    snap_t30y  = data.get("market", {}).get("t30y")

    cpi_val = cpi_score or 0
    tsi_val = tsi_score or 0
    avi_val = avi_score or 0

    # Flash alerts
    alerts = []
    if cpi_flash:
        alerts.append("CPI Flash Alert ⚡")
    if tsi_flash:
        tsi_flash_reason = data.get("tsi", {}).get("flash_reason", "")
        alerts.append(f"TSI Flash: {tsi_flash_reason}" if tsi_flash_reason else "TSI Flash Alert ⚡")

    # Combined signal
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

    lines = [
        f"<b>📊 每日市場體溫</b>  <i>{today}</i>",
        "─────────────────",
    ]

    cpi_d = f"{cpi_val:.0f}" if cpi_score is not None else "──"
    tsi_d = f"{tsi_val:.0f}" if tsi_score is not None else "──"
    avi_d = f"{avi_val:.1f}" if avi_score is not None else "──"

    lines.append(f"{level_emoji(cpi_score, 'cpi')} <b>CPI</b>  {cpi_d}/100  <i>{cpi_level}</i>")
    lines.append(f"{level_emoji(tsi_score, 'tsi')} <b>TSI</b>  {tsi_d}/100  <i>{tsi_bias}</i>")
    lines.append(f"{level_emoji(avi_score, 'avi')} <b>AVI</b>  {avi_d}/10")

    if alerts:
        lines.append("")
        for a in alerts:
            lines.append(f"⚡ {a}")

    snap_parts = []
    if snap_sp500:
        snap_parts.append(f"S&amp;P {snap_sp500:,.0f}")
    if snap_vix:
        snap_parts.append(f"VIX {snap_vix:.1f}")
    if snap_t10y:
        snap_parts.append(f"10Y {snap_t10y:.2f}%")
    if snap_t30y:
        snap_parts.append(f"30Y {snap_t30y:.2f}%")
    if snap_parts:
        lines.append("")
        lines.append("  ".join(snap_parts))

    lines.append("")
    lines.append(signal_line)
    lines.append("")
    lines.append("<i>觸發條件：TSI&gt;55 減倉 · CPI&gt;35 避險 · 雙高立即行動</i>")
    lines.append("")
    lines.append("🌐 <a href=\"https://gutinganthony.github.io/KIWI/\">查看完整 Dashboard</a>")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Daily market alert via Telegram")
    parser.add_argument("--dry-run", action="store_true", help="Print message without sending")
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)

    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

    logger.info(f"Loading dashboard data from {DOCS_INDEX}...")
    data = load_dashboard_data()
    logger.info(f"  CPI={data.get('cpi',{}).get('score')}  TSI={data.get('tsi',{}).get('score')}  AVI={data.get('avi',{}).get('score')}")

    message = build_message(data)

    if args.dry_run:
        print(re.sub(r"<[^>]+>", "", message))
        return

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        print("\nMessage preview:")
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
