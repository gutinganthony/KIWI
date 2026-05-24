#!/usr/bin/env python3
"""Daily market alert — reads pre-computed data from docs/index.html and sends via Telegram + LINE.

Data source: KIWI_DATA JSON embedded in docs/index.html (written by update_dashboard.py).
This guarantees both channels always show the same numbers.

Setup:
  Telegram:
    1. message @BotFather → /newbot → get TOKEN
    2. message @userinfobot → get your CHAT_ID
    3. Set env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

  LINE:
    1. https://developers.line.biz/ → Create provider → Create Messaging API channel
    2. Channel settings → Messaging API → Issue Channel access token
    3. Set env var: LINE_CHANNEL_ACCESS_TOKEN
    4. Friends add your LINE Official Account → they receive broadcasts automatically

Usage:
  python3 scripts/notify.py              # Send to all configured channels
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
    """Send HTML-formatted message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def send_line_broadcast(token, message):
    """Broadcast plain-text message to all LINE Official Account followers."""
    url = "https://api.line.me/v2/bot/message/broadcast"
    payload = json.dumps({
        "messages": [{"type": "text", "text": message}]
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return json.loads(body) if body else {"ok": True}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LINE HTTP {e.code}: {error_body}") from e


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
    if system == "cri":
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
    """Build daily alert. Returns (html_message, plain_message)."""
    today = datetime.now().strftime("%Y-%m-%d %a")

    cri_score = data.get("cri", {}).get("score")
    cri_level = data.get("cri", {}).get("level", "──")
    cri_flash = data.get("cri", {}).get("flash", False)

    tsi_score = data.get("tsi", {}).get("score")
    tsi_bias  = data.get("tsi", {}).get("bias", "──")
    tsi_flash = data.get("tsi", {}).get("flash", False)

    avi_score = data.get("avi", {}).get("score")

    snap_sp500 = data.get("market", {}).get("sp500")
    snap_vix   = data.get("market", {}).get("vix")
    snap_t10y  = data.get("market", {}).get("t10y")
    snap_t30y  = data.get("market", {}).get("t30y")

    cri_val = cri_score or 0
    tsi_val = tsi_score or 0
    avi_val = avi_score or 0

    alerts = []
    if cri_flash:
        alerts.append("CRI Flash Alert ⚡")
    if tsi_flash:
        tsi_flash_reason = data.get("tsi", {}).get("flash_reason", "")
        alerts.append(f"TSI Flash: {tsi_flash_reason}" if tsi_flash_reason else "TSI Flash Alert ⚡")

    if cri_val >= 35 and tsi_val >= 55:
        signal_html  = "🔴 <b>雙重壓力</b>：積極減倉 + 建立避險"
        signal_plain = "🔴 雙重壓力：積極減倉 + 建立避險"
    elif cri_val >= 35:
        signal_html  = "🟠 <b>崩盤概率升高</b>：檢查持倉，準備避險"
        signal_plain = "🟠 崩盤概率升高：檢查持倉，準備避險"
    elif tsi_val >= 60:
        signal_html  = "🔴 <b>科技壓力高</b>：減科技曝險"
        signal_plain = "🔴 科技壓力高：減科技曝險"
    elif tsi_val >= 45 or avi_val >= 6:
        signal_html  = "🟡 <b>謹慎持有</b>：不追高，留意觸發條件"
        signal_plain = "🟡 謹慎持有：不追高，留意觸發條件"
    elif cri_val >= 20:
        signal_html  = "🟡 <b>留意</b>：掃一眼哪個指標在升溫"
        signal_plain = "🟡 留意：掃一眼哪個指標在升溫"
    else:
        signal_html  = "🟢 <b>正常</b>：照常操作"
        signal_plain = "🟢 正常：照常操作"

    cri_d = f"{cri_val:.0f}" if cri_score is not None else "──"
    tsi_d = f"{tsi_val:.0f}" if tsi_score is not None else "──"
    avi_d = f"{avi_val:.1f}" if avi_score is not None else "──"

    snap_parts = []
    if snap_sp500: snap_parts.append(f"S&P {snap_sp500:,.0f}")
    if snap_vix:   snap_parts.append(f"VIX {snap_vix:.1f}")
    if snap_t10y:  snap_parts.append(f"10Y {snap_t10y:.2f}%")
    if snap_t30y:  snap_parts.append(f"30Y {snap_t30y:.2f}%")
    snap_line = "  ".join(snap_parts)

    # ── Telegram (HTML) ──
    html_lines = [
        f"<b>📊 每日市場體溫</b>  <i>{today}</i>",
        "─────────────────",
        f"{level_emoji(cri_score,'cri')} <b>CRI</b>  {cri_d}/100  <i>{cri_level}</i>",
        f"{level_emoji(tsi_score,'tsi')} <b>TSI</b>  {tsi_d}/100  <i>{tsi_bias}</i>",
        f"{level_emoji(avi_score,'avi')} <b>AVI</b>  {avi_d}/10",
    ]
    if alerts:
        html_lines.append("")
        for a in alerts:
            html_lines.append(f"⚡ {a}")
    if snap_line:
        html_lines += ["", snap_line.replace("S&P", "S&amp;P")]
    html_lines += ["", signal_html, "",
                   "<i>觸發條件：TSI&gt;55 減倉 · CRI&gt;35 避險 · 雙高立即行動</i>",
                   "",
                   '🌐 <a href="https://gutinganthony.github.io/KIWI/">查看完整 Dashboard</a>']

    # ── LINE (plain text) ──
    plain_lines = [
        f"📊 每日市場體溫  {today}",
        "─────────────────",
        f"{level_emoji(cri_score,'cri')} CRI  {cri_d}/100  {cri_level}",
        f"{level_emoji(tsi_score,'tsi')} TSI  {tsi_d}/100  {tsi_bias}",
        f"{level_emoji(avi_score,'avi')} AVI  {avi_d}/10",
    ]
    if alerts:
        plain_lines.append("")
        for a in alerts:
            plain_lines.append(f"⚡ {a}")
    if snap_line:
        plain_lines += ["", snap_line]
    plain_lines += ["", signal_plain, "",
                    "觸發條件：TSI>55 減倉 · CRI>35 避險 · 雙高立即行動",
                    "",
                    "🌐 查看完整 Dashboard：https://gutinganthony.github.io/KIWI/"]

    return "\n".join(html_lines), "\n".join(plain_lines)


def main():
    parser = argparse.ArgumentParser(description="Daily market alert via Telegram + LINE")
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
    logger.info(f"  CRI={data.get('cri',{}).get('score')}  TSI={data.get('tsi',{}).get('score')}  AVI={data.get('avi',{}).get('score')}")

    html_msg, plain_msg = build_message(data)

    if args.dry_run:
        print("── Telegram ──")
        print(re.sub(r"<[^>]+>", "", html_msg))
        print("\n── LINE ──")
        print(plain_msg)
        return

    # ── Telegram ──
    tg_token  = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chatid = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chatid:
        try:
            result = send_telegram(tg_token, tg_chatid, html_msg)
            if result.get("ok"):
                logger.info("✅ Telegram sent")
            else:
                logger.error(f"Telegram failed: {result}")
        except Exception as e:
            logger.error(f"Telegram error: {e}")
    else:
        logger.warning("Telegram skipped (no token/chat_id)")

    # ── LINE ──
    line_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if line_token:
        try:
            send_line_broadcast(line_token, plain_msg)
            logger.info("✅ LINE broadcast sent")
        except Exception as e:
            logger.error(f"LINE error: {e}")
    else:
        logger.warning("LINE skipped (no LINE_CHANNEL_ACCESS_TOKEN)")


if __name__ == "__main__":
    main()
