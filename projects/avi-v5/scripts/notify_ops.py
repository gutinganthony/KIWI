#!/usr/bin/env python3
"""Ops notification — push a short operational message (workflow success/failure,
session completion) to Telegram, and optionally broadcast to LINE.

WHY a separate script from notify.py:
  - notify.py sends *market data* (reads KIWI_DATA out of docs/index.html). It is
    useless — and will itself crash — when a workflow fails *before* producing that
    data. This script has ZERO data dependencies and is pure stdlib, so it runs on
    any job (even ones without setup-python) and even when everything else is broken.
  - Ops alerts (a workflow failed, a weekly digest is ready) are for the operator
    (Jake) only, so they default to Telegram's personal CHAT_ID. LINE is an
    *audience* broadcast channel (market followers) — you do NOT want "deploy failed"
    going to your followers, so LINE is opt-in via --line.

Design: BEST-EFFORT. Always exits 0. A notifier that hard-fails inside a failure
handler would only mask the workflow's real status and add noise. It logs loudly
instead.

Usage:
  python3 notify_ops.py --title "❌ Deploy 失敗" --body "去按 Re-run" --url "$RUN_URL"
  python3 notify_ops.py --title "✅ 週報完成" --body "..." --url "..." --line
  echo "long body" | python3 notify_ops.py --title "..."       # body from stdin
  python3 notify_ops.py --title "test" --dry-run                # print, don't send

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  (required for Telegram)
     LINE_CHANNEL_ACCESS_TOKEN             (only used with --line)
"""

import argparse
import html
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("notify_ops")


def _post(url, payload, headers, retries=3):
    """POST JSON with retry. Retries network errors and 5xx; does NOT retry 4xx
    (a bad request won't fix itself). Returns parsed JSON (or {"ok": True} if empty)."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read()
                return json.loads(body) if body else {"ok": True}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            last_err = RuntimeError(f"HTTP {e.code}: {err_body}")
            if e.code < 500 or attempt == retries:
                raise last_err
        except Exception as e:  # noqa: BLE001 — network/DNS/timeout, worth retrying
            last_err = e
            if attempt == retries:
                raise
        time.sleep(2 ** attempt)
    if last_err:
        raise last_err


def send_telegram(token, chat_id, text_html):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    return _post(url, payload, {"Content-Type": "application/json"})


def send_line_broadcast(token, text_plain):
    url = "https://api.line.me/v2/bot/message/broadcast"
    payload = json.dumps({"messages": [{"type": "text", "text": text_plain}]}).encode("utf-8")
    return _post(url, payload, {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    })


def build(title, body, url):
    """Return (telegram_html, line_plain)."""
    # Telegram: HTML — escape user text, keep our own tags.
    tg = [f"<b>{html.escape(title)}</b>"]
    if body:
        tg.append(html.escape(body))
    if url:
        tg.append(f'🔗 <a href="{html.escape(url, quote=True)}">開啟</a>')
    # LINE: plain text.
    ln = [title]
    if body:
        ln.append(body)
    if url:
        ln.append(url)
    return "\n".join(tg), "\n".join(ln)


def main():
    p = argparse.ArgumentParser(description="Ops notification (Telegram default, LINE opt-in)")
    p.add_argument("--title", required=True)
    p.add_argument("--body", default="")
    p.add_argument("--url", default="")
    p.add_argument("--line", action="store_true", help="Also broadcast to LINE followers")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    body = args.body
    if not body and not sys.stdin.isatty():
        body = sys.stdin.read().strip()

    tg_html, line_plain = build(args.title, body, args.url)

    if args.dry_run:
        print("── Telegram ──"); print(tg_html)
        print("\n── LINE ──"); print(line_plain)
        return

    # ── Telegram (operator's personal chat) ──
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        try:
            r = send_telegram(tg_token, tg_chat, tg_html)
            logger.info("✅ Telegram sent" if r.get("ok") else f"⚠️ Telegram not-ok: {r}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"❌ Telegram failed: {e}")
    else:
        logger.warning("Telegram skipped (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set)")

    # ── LINE (audience broadcast, opt-in) ──
    if args.line:
        line_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        if line_token:
            try:
                send_line_broadcast(line_token, line_plain)
                logger.info("✅ LINE broadcast sent")
            except Exception as e:  # noqa: BLE001
                logger.error(f"❌ LINE failed: {e}")
        else:
            logger.warning("LINE skipped (LINE_CHANNEL_ACCESS_TOKEN not set)")

    # Best-effort: never mask the workflow's real exit status.
    sys.exit(0)


if __name__ == "__main__":
    main()
