#!/usr/bin/env python3
"""Agenda reminder — parse AGENDA.md and push a Saturday progress digest to Telegram.

WHY: Jake asked for a weekly watchdog (2026-07-12): overdue / due-soon tasks from
AGENDA.md, plus the monthly self-check list on the first Saturday of each month,
plus the mac-manual-homework backlog count. AGENDA.md is the single place he adds
tasks by hand (one line each); this script only reads, never writes.

Task line format (inside the "## 📌 任務" section):
    - [ ] YYYY-MM-DD | title | summary
Lines with [x] are done and ignored. Goals ("## 🎯 目標") are counted, not nagged.

Design mirrors notify_ops.py: pure stdlib, BEST-EFFORT, always exits 0 on send
errors (the workflow's failure handler covers real breakage). Sending reuses
notify_ops.send_telegram (retry + HTML escaping conventions).

Usage:
  python3 scripts/agenda_reminder.py            # send to Telegram
  python3 scripts/agenda_reminder.py --dry-run  # print, don't send
Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""

import argparse
import datetime as dt
import html
import logging
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "projects" / "avi-v5" / "scripts"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("agenda_reminder")

TASK_RE = re.compile(r"^- \[( |x|X)\]\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|\s*(.+)$")
DUE_SOON_DAYS = 14
MAX_ITEMS = 15  # Telegram 4096-char safety; if truncated we say so explicitly


def parse_section(text, header_prefix):
    """Return the lines of the section whose '## ' header starts with header_prefix."""
    lines, active = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            active = line[3:].strip().startswith(header_prefix)
            continue
        if active:
            lines.append(line)
    return lines


def parse_tasks(section_lines):
    """Yield (due_date, title, summary) for open tasks; skip done/malformed lines."""
    tasks, malformed = [], []
    for line in section_lines:
        s = line.strip()
        if not s.startswith("- ["):
            continue
        m = TASK_RE.match(s)
        if not m:
            malformed.append(s)
            continue
        done, date_s, title, summary = m.groups()
        if done.lower() == "x":
            continue
        try:
            due = dt.date.fromisoformat(date_s)
        except ValueError:
            malformed.append(s)
            continue
        tasks.append((due, title.strip(), summary.strip()))
    return sorted(tasks, key=lambda t: t[0]), malformed


def count_goals(section_lines):
    return sum(1 for line in section_lines if line.strip().startswith("- "))


def monthly_checklist(text):
    return [line.strip() for line in parse_section(text, "🗓")
            if re.match(r"^\d+\.", line.strip())]


def homework_backlog():
    """Count open '- [ ]' items in mac-manual-homework's 待辦 section."""
    path = REPO / "topics" / "technology" / "mac-manual-homework.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    todo = text.split("## 🔴 待辦", 1)
    if len(todo) < 2:
        return None
    todo = todo[1].split("## ✅", 1)[0]
    return len(re.findall(r"^\s*- \[ \]", todo, flags=re.M))


def is_first_saturday(today):
    return today.weekday() == 5 and today.day <= 7


def build_message(today, tasks, malformed, n_goals, checklist, backlog):
    overdue = [t for t in tasks if t[0] < today]
    due_soon = [t for t in tasks if today <= t[0] <= today + dt.timedelta(days=DUE_SOON_DAYS)]

    def fmt(items, mark):
        out = []
        for due, title, summary in items[:MAX_ITEMS]:
            delta = (today - due).days if due < today else (due - today).days
            when = f"逾期 {delta} 天" if due < today else (f"{delta} 天後" if delta else "今天")
            out.append(f"{mark} <b>{html.escape(title)}</b>（{due.isoformat()}，{when}）\n"
                       f"　{html.escape(summary)}")
        if len(items) > MAX_ITEMS:
            out.append(f"…另有 {len(items) - MAX_ITEMS} 項未列出，見 AGENDA.md")
        return out

    parts = [f"<b>📋 KIWI 週六進度盯梢 {today.isoformat()}</b>"]
    if overdue:
        parts.append("🔴 已逾期：")
        parts.extend(fmt(overdue, "•"))
    if due_soon:
        parts.append(f"🟡 {DUE_SOON_DAYS} 天內到期：")
        parts.extend(fmt(due_soon, "•"))
    if not overdue and not due_soon:
        parts.append("✅ 無逾期、無 14 天內到期任務。")
    if backlog:
        parts.append(f"🖥 Mac 手動功課積欠 <b>{backlog}</b> 項（mac-manual-homework.md）")
    if n_goals:
        parts.append(f"🎯 進行中的里程碑目標 {n_goals} 項（無到期日，見 AGENDA.md）")
    if malformed:
        parts.append(f"⚠️ AGENDA.md 有 {len(malformed)} 行任務格式不符（`- [ ] 日期 | 標題 | 摘要`），bot 看不懂：\n"
                     + "\n".join(html.escape(s[:80]) for s in malformed[:3]))
    if is_first_saturday(today) and checklist:
        parts.append("🗓 <b>每月第一個週六 · 自檢清單</b>（回想上個月，逐條誠實作答）：")
        parts.extend(html.escape(item) for item in checklist)
    return "\n\n".join(parts)


def main():
    p = argparse.ArgumentParser(description="AGENDA.md Saturday reminder")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--date", help="override today (YYYY-MM-DD, for testing)")
    args = p.parse_args()

    today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    text = (REPO / "AGENDA.md").read_text(encoding="utf-8")
    tasks, malformed = parse_tasks(parse_section(text, "📌"))
    msg = build_message(
        today, tasks, malformed,
        n_goals=count_goals(parse_section(text, "🎯")),
        checklist=monthly_checklist(text),
        backlog=homework_backlog(),
    )

    if args.dry_run:
        print(msg)
        return

    import os
    from notify_ops import send_telegram  # noqa: PLC0415 — after sys.path insert
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        logger.warning("Telegram skipped (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set)")
        return
    try:
        r = send_telegram(token, chat, msg)
        logger.info("✅ Telegram sent" if r.get("ok") else f"⚠️ Telegram not-ok: {r}")
    except Exception as e:  # noqa: BLE001 — best-effort, workflow failure handler covers it
        logger.error(f"❌ Telegram failed: {e}")


if __name__ == "__main__":
    main()
