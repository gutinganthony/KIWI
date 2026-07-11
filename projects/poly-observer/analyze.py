#!/usr/bin/env python3
"""poly-observer analyze：每日觀察器（watchlist 維護＋異動報告）。

用法：
    python3 analyze.py --snapshot data/snapshots/{date} [--report-dir data/reports]

行為：
1. 讀同日 verification_{date}.json（verify_smart_money.py 的輸出）。
2. 維護 data/watchlist.json：consistent_winner 全收，逐日指標快照 append 歷史；
   不再符合條件者標 active=false 但保留歷史。
3. 與前一日 watchlist 狀態比對 → data/reports/daily_{date}.md：
   新進/退出/退化警示（30 天 PnL 轉負、頻率暴增 3x、類別漂移＝主類別改變）。
   首日無前日資料就寫「initialized」。

純唯讀分析，不含任何下單、金鑰、簽章功能。
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import config

BASE_DIR = Path(__file__).resolve().parent


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception as exc:
        print(f"[analyze] {path} 解析失敗：{exc}", file=sys.stderr)
        return None


def snapshot_point(date, metrics):
    """存進 watchlist 歷史的逐日指標快照。"""
    return {
        "date": date,
        "total_pnl": metrics.get("total_pnl"),
        "recent_30d_pnl": metrics.get("recent_30d_pnl"),
        "positive_month_ratio": metrics.get("positive_month_ratio"),
        "max_drawdown_pct": metrics.get("max_drawdown_pct"),
        "trades_per_month": metrics.get("trades_per_month"),
        "top_category": metrics.get("top_category"),
        "top_category_share": metrics.get("top_category_share"),
        "low_confidence": metrics.get("low_confidence"),
    }


def previous_point(entry, today):
    """entry 歷史中最後一筆「今天以前」的快照；沒有回 None。"""
    prev = None
    for p in entry.get("history", []):
        if p.get("date") and p["date"] < today:
            prev = p
    return prev


def detect_alerts(addr, entry, today):
    """退化警示：30 天 PnL 轉負、頻率暴增 3x、類別漂移。"""
    prev = previous_point(entry, today)
    cur = next((p for p in reversed(entry.get("history", []))
                if p.get("date") == today), None)
    if prev is None or cur is None:
        return []
    alerts = []
    p30, c30 = prev.get("recent_30d_pnl"), cur.get("recent_30d_pnl")
    if p30 is not None and c30 is not None and p30 >= 0 > c30:
        alerts.append(f"30 天 PnL 轉負：{p30:,.0f} → {c30:,.0f}")
    pf, cf = prev.get("trades_per_month"), cur.get("trades_per_month")
    if pf and cf and pf > 0 and cf >= config.ALERT_FREQ_SPIKE_MULTIPLIER * pf:
        alerts.append(f"頻率暴增 {cf / pf:.1f}x：{pf:,.1f} → {cf:,.1f} 筆/月")
    pc, cc = prev.get("top_category"), cur.get("top_category")
    if pc and cc and pc != cc:
        alerts.append(f"類別漂移：主類別 {pc} → {cc}")
    return alerts


def build_report(date, initialized, active, entered, exited, alerts, watchlist,
                 verification_missing=False):
    lines = [f"# Poly Observer 每日觀察 — {date}", ""]
    if verification_missing:
        lines += ["**錯誤：找不到同日 verification JSON，本日未更新 watchlist。**",
                  "請確認 verify_smart_money.py 是否成功產出報告。", ""]
        return "\n".join(lines)
    if initialized:
        lines += ["**initialized** — 首日建立 watchlist，無前日資料可比對。", ""]
    lines += [f"## Watchlist 概況：active {len(active)} 檔"
              f"（新進 {len(entered)}、退出 {len(exited)}）", ""]
    if active:
        lines += ["| 地址 | 總 PnL | 近 30 天 PnL | 頻率(筆/月) | 主類別 | 首次收錄 |",
                  "|---|---:|---:|---:|---|---|"]
        for addr in active:
            entry = watchlist[addr]
            cur = entry["history"][-1] if entry.get("history") else {}
            def f(v, spec=",.0f"):
                return format(v, spec) if v is not None else "—"
            lines.append(
                f"| `{addr}` | ${f(cur.get('total_pnl'))} "
                f"| ${f(cur.get('recent_30d_pnl'))} "
                f"| {f(cur.get('trades_per_month'), ',.1f')} "
                f"| {cur.get('top_category') or '—'} "
                f"| {entry.get('first_added', '—')} |")
    else:
        lines.append("（watchlist 目前無 active 錢包）")

    lines += ["", "## 新進", ""]
    lines += [f"- `{a}`" for a in entered] or ["（無）"]
    lines += ["", "## 退出", ""]
    lines += [f"- `{a}`（保留歷史，active=false）" for a in exited] or ["（無）"]
    lines += ["", "## 退化警示", ""]
    if alerts:
        for addr, msgs in alerts.items():
            for msg in msgs:
                lines.append(f"- ⚠️ `{addr}`：{msg}")
    else:
        lines.append("（無）")
    lines += ["", "> 純唯讀觀察，不構成任何交易行為或建議。", ""]
    return "\n".join(lines)


def run_analyze(snapshot_dir, report_dir, watchlist_path):
    """核心進入點（tests 可直接呼叫）。回傳 (report_path, watchlist)。"""
    snapshot_dir, report_dir = Path(snapshot_dir), Path(report_dir)
    watchlist_path = Path(watchlist_path)
    date = snapshot_dir.name
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"daily_{date}.md"

    verification = load_json(report_dir / f"verification_{date}.json")
    if verification is None:
        report_path.write_text(
            build_report(date, False, [], [], [], {}, {}, verification_missing=True),
            encoding="utf-8")
        print(f"[analyze] verification_{date}.json 缺失，已寫錯誤報告：{report_path}")
        return report_path, None

    raw_watchlist = load_json(watchlist_path)
    initialized = raw_watchlist is None
    watchlist = raw_watchlist or {}
    prev_active = {a for a, e in watchlist.items() if e.get("active")}

    winners = {addr: rec["metrics"]
               for addr, rec in (verification.get("wallets") or {}).items()
               if rec.get("classification") == "consistent_winner"}

    for addr, metrics in winners.items():
        entry = watchlist.setdefault(addr, {"first_added": date, "history": []})
        entry["active"] = True
        entry["last_active"] = date
        # 同日重跑不重複 append：先移除同日舊快照
        entry["history"] = [p for p in entry["history"] if p.get("date") != date]
        entry["history"].append(snapshot_point(date, metrics))
    for addr, entry in watchlist.items():
        if addr not in winners:
            entry["active"] = False

    new_active = sorted(winners)
    entered = sorted(set(new_active) - prev_active)
    exited = sorted(prev_active - set(new_active))
    alerts = {}
    for addr in new_active:
        msgs = detect_alerts(addr, watchlist[addr], date)
        if msgs:
            alerts[addr] = msgs

    watchlist_path.parent.mkdir(parents=True, exist_ok=True)
    watchlist_path.write_text(
        json.dumps(watchlist, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8")
    report_path.write_text(
        build_report(date, initialized, new_active, entered, exited, alerts, watchlist),
        encoding="utf-8")

    print(f"[analyze] active={len(new_active)} entered={len(entered)} "
          f"exited={len(exited)} alerts={sum(len(v) for v in alerts.values())}")
    print(f"[analyze] watchlist: {watchlist_path}")
    print(f"[analyze] report:    {report_path}")
    return report_path, watchlist


def main(argv=None):
    parser = argparse.ArgumentParser(description="Polymarket watchlist daily observer")
    parser.add_argument("--snapshot", required=True,
                        help="snapshot 目錄，例：data/snapshots/2026-07-10")
    parser.add_argument("--report-dir", default=str(BASE_DIR / "data" / "reports"))
    parser.add_argument("--watchlist", default=str(BASE_DIR / "data" / "watchlist.json"))
    args = parser.parse_args(argv)

    snapshot_dir = Path(args.snapshot)
    if not snapshot_dir.is_absolute():
        cand = BASE_DIR / snapshot_dir
        snapshot_dir = cand if cand.exists() else snapshot_dir
    report_dir = Path(args.report_dir)
    if not report_dir.is_absolute():
        report_dir = BASE_DIR / report_dir
    watchlist_path = Path(args.watchlist)
    if not watchlist_path.is_absolute():
        watchlist_path = BASE_DIR / watchlist_path

    _, watchlist = run_analyze(snapshot_dir, report_dir, watchlist_path)
    return 0 if watchlist is not None else 1


if __name__ == "__main__":
    sys.exit(main())
