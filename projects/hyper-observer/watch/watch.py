#!/usr/bin/env python3
"""近即時持倉哨兵（read-only）——每 N 分鐘輪詢 TRACKED 錢包，開/平/加/減倉推 Telegram。

為什麼要與 hyper-observer 的每日班分開
  - 每日班（cron 22:45 UTC）抓 portfolio + userFills + userFunding + ledger，權重重、
    要 commit 資料回 repo，一天只能跑一次；「他開新倉了」這種事一天知道一次太慢。
  - 這支只查 clearinghouseState（原生＋builder dex），每錢包權重 2×(1+dex 數)，
    10 分鐘一次的成本可忽略，且**完全不寫 repo**（狀態走 Actions cache），
    所以不會製造 commit、不會與 main 的資料檔衝突。

唯讀保證：只 POST config.INFO_URL 的 info 查詢（clearinghouseState / perpDexs）。
無下單、無簽章、無私鑰，也不引用 Hyperliquid 的交易端點（exchange endpoint）。
測試會 grep 這支檔案確保這些字樣不存在，所以連註解都刻意不寫出那些字面。

狀態檔（--state）格式
  {"version":1, "updated_at": iso, "wallets": {addr: {"positions": {key: {...}},
   "account_value": float|None, "last_alert_ts": {key: epoch_sec}}}}
  key = "dex|coin|side"（dex 空字串＝原生）。同一幣多空對翻會被視為兩個 key，
  刻意如此：對跟單者而言「翻空」是新事件，不是加減倉。

第一次跑（或 cache 遺失）→ 只建基準、**不推播**（否則每次 cache 過期就會把所有部位
當成新倉全部推一次，是最經典的假警報來源）。

用法
  python3 watch.py --state state/state.json --out-message msg.txt
  python3 watch.py --test-notify --out-message msg.txt   # 產生測試訊息（不查 API）
  python3 watch.py --dry-run                             # 查 API、印結果、不寫狀態
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import classify           # noqa: E402
import config             # noqa: E402
import fetch              # noqa: E402
import watch_config as wcfg  # noqa: E402

STATE_VERSION = 1


# ---------------------------------------------------------------------------
# 抓取（只 clearinghouseState：原生 + builder dex）
# ---------------------------------------------------------------------------

def fetch_positions_light(addr, meta, dex_names, post_fn=None):
    """回 wallet-like dict，餵給 classify.parse_positions_by_dex。

    刻意**不**抓 portfolio/userFills/userFunding/spot：哨兵只需要「現在有哪些部位」。
    單一 dex 失敗只記錄不 crash（部分場所看不到 → 該場所視為未知，見 all_ok）。
    """
    post_fn = post_fn or fetch.http_post_info
    out = {"address": addr, "clearinghouseState": None, "clearinghouseStateByDex": {}}
    n_fail = 0
    data, ok = post_fn({"type": "clearinghouseState", "user": addr},
                       f"clearinghouseState:{addr[:10]}", meta)
    if ok:
        out["clearinghouseState"] = data
    else:
        n_fail += 1
    for dex in dex_names or []:
        data, ok = post_fn({"type": "clearinghouseState", "user": addr, "dex": dex},
                           f"clearinghouseState:{dex}:{addr[:10]}", meta)
        if ok:
            out["clearinghouseStateByDex"][dex] = data
        else:
            n_fail += 1
    out["n_endpoint_failures"] = n_fail
    return out


# ---------------------------------------------------------------------------
# 指紋與比對
# ---------------------------------------------------------------------------

def position_key(p):
    dex = (p.get("dex") or "").strip()
    return f"{dex}|{p.get('coin') or ''}|{p.get('side') or ''}"


def snapshot_positions(positions):
    """持倉清單 → {key: {szi, entry_px, notional, leverage, liq_px, coin, side, dex}}。"""
    snap = {}
    for p in positions:
        key = position_key(p)
        prev = snap.get(key)
        szi = abs(p.get("szi") or 0.0)
        notional = p.get("position_value")
        if prev:  # 同 key 重複（理論上不會）→ 取名目較大者，不相加以免虛胖
            if (prev.get("notional") or 0) >= (notional or 0):
                continue
        snap[key] = {
            "dex": (p.get("dex") or "").strip(),
            "coin": p.get("coin"),
            "side": p.get("side"),
            "szi": szi,
            "entry_px": p.get("entry_px"),
            "notional": notional,
            "leverage": p.get("leverage_value"),
            "liq_px": p.get("liquidation_px"),
        }
    return snap


def _pct_change(new, old):
    if old is None or new is None or abs(old) < 1e-12:
        return None
    return (new - old) / abs(old)


def diff_positions(old_snap, new_snap, size_change_pct):
    """回 events 清單：[{"type": opened|closed|increased|reduced, "key", "new", "old", "pct"}]。

    size_change_pct：|倉位大小變化| 達此比例才算加/減倉（低於此值＝雜訊，不推播）。
    """
    events = []
    for key, new in new_snap.items():
        old = old_snap.get(key)
        if old is None:
            events.append({"type": "opened", "key": key, "new": new, "old": None, "pct": None})
            continue
        pct = _pct_change(new.get("szi"), old.get("szi"))
        if pct is not None and abs(pct) >= size_change_pct:
            events.append({"type": "increased" if pct > 0 else "reduced",
                           "key": key, "new": new, "old": old, "pct": pct})
    for key, old in old_snap.items():
        if key not in new_snap:
            events.append({"type": "closed", "key": key, "new": None, "old": old, "pct": None})
    order = {"opened": 0, "closed": 1, "increased": 2, "reduced": 3}
    events.sort(key=lambda e: (order.get(e["type"], 9),
                               -abs((e["new"] or e["old"] or {}).get("notional") or 0)))
    return events


def apply_cooldown(events, last_alert, now_ts, cooldown_sec):
    """同一 key 在 cooldown 內只推一次（避免部位大小抖動造成連續轟炸）。

    opened / closed 永不受 cooldown 壓制——那是真事件，漏掉的代價遠大於多一則通知。
    """
    kept, suppressed = [], 0
    for ev in events:
        if ev["type"] in ("opened", "closed"):
            kept.append(ev)
            continue
        prev = last_alert.get(ev["key"])
        if prev is not None and (now_ts - prev) < cooldown_sec:
            suppressed += 1
            continue
        kept.append(ev)
    return kept, suppressed


# ---------------------------------------------------------------------------
# 訊息
# ---------------------------------------------------------------------------

def _money(v):
    if v is None:
        return "?"
    a = abs(v)
    if a >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if a >= 1_000:
        return f"${v/1_000:.1f}k"
    return f"${v:,.0f}"


def _venue(dex):
    return dex or "原生"


def format_events(addr, label, events, account_value, n_positions):
    """事件清單 → Telegram 純文字行（notify_ops 會做 HTML escape）。"""
    head = f"{label or addr[:10]}（{addr[:6]}…{addr[-4:]}）"
    lines = [head]
    for ev in events:
        if ev["type"] == "more":
            lines.append(f"…另有 {ev['n']} 個變動未列出（避免訊息被 Telegram 截斷）")
            continue
        p = ev["new"] or ev["old"] or {}
        venue, coin, side = _venue(p.get("dex")), p.get("coin") or "?", p.get("side") or "?"
        lev = p.get("leverage")
        lev_s = f"・{lev:g}x" if isinstance(lev, (int, float)) else ""
        if ev["type"] == "opened":
            lines.append(f"🟢 新開倉 {venue} {coin} {side}{lev_s}｜名目 {_money(p.get('notional'))}"
                         f"｜進場 {p.get('entry_px')}")
        elif ev["type"] == "closed":
            lines.append(f"⚪ 平倉 {venue} {coin} {side}｜原名目 {_money(p.get('notional'))}")
        else:
            arrow = "加倉" if ev["type"] == "increased" else "減倉"
            icon = "🔵" if ev["type"] == "increased" else "🟠"
            old_sz = (ev["old"] or {}).get("szi")
            new_sz = p.get("szi")
            size_s = (f"{old_sz:g} → {new_sz:g}"
                      if isinstance(old_sz, (int, float)) and isinstance(new_sz, (int, float))
                      else "倉位大小未知")
            pct_s = f"（{ev['pct']*100:+.0f}%）" if isinstance(ev.get("pct"), float) else ""
            lines.append(f"{icon} {arrow} {venue} {coin} {side}{lev_s}｜"
                         f"{size_s}{pct_s}｜名目 {_money(p.get('notional'))}")
    lines.append(f"目前 {n_positions} 個部位・帳戶淨值合計 {_money(account_value)}")
    return "\n".join(lines)


def test_message():
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    return ("這是 hyper-watch 哨兵的一次性測試推播，看到就代表管線通了。\n"
            f"檢查時間：{now}\n"
            f"輪詢頻率：每 {wcfg.WATCH_INTERVAL_MINUTES} 分鐘（GitHub cron 實際可能延遲數分鐘）\n"
            "真實通知只在偵測到「新開倉／平倉／加減倉」時才發，沒事不吵。\n"
            "唯讀：只查 Hyperliquid 公開 info API，不下單、不簽章、無私鑰。")


# ---------------------------------------------------------------------------
# 狀態檔
# ---------------------------------------------------------------------------

def load_state(path):
    """回 (state, is_fresh)。讀不到／版本不符 → 空狀態 + is_fresh=True（只建基準不推播）。"""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, ValueError, OSError):
        return {"version": STATE_VERSION, "wallets": {}}, True
    if not isinstance(data, dict) or data.get("version") != STATE_VERSION:
        return {"version": STATE_VERSION, "wallets": {}}, True
    if not isinstance(data.get("wallets"), dict):
        data["wallets"] = {}
        return data, True
    return data, False


def save_state(path, state):
    state["version"] = STATE_VERSION
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run(args, post_fn=None):
    """回 (message_or_None, summary_dict)。message 為 None＝無事發生（不推播）。"""
    meta = fetch.Meta()
    state, is_fresh = load_state(args.state)
    wallets_state = state.setdefault("wallets", {})
    now_ts = int(time.time())

    dex_names = []
    if wcfg.WATCH_FETCH_DEXS:
        dex_names = fetch.fetch_perp_dexs(meta, post_fn=post_fn)[: wcfg.WATCH_MAX_DEXS]

    tracked = [(w.get("address"), w.get("label")) if isinstance(w, dict) else (w, None)
               for w in (config.TRACKED_WALLETS or [])]
    tracked = [(a.lower(), lb) for a, lb in tracked if isinstance(a, str) and a]

    blocks, summary = [], {"wallets": [], "n_events": 0, "is_fresh": is_fresh,
                           "dexs": dex_names, "suppressed": 0, "endpoint_failures": 0}

    for addr, label in tracked:
        wallet = fetch_positions_light(addr, meta, dex_names, post_fn=post_fn)
        summary["endpoint_failures"] += wallet.get("n_endpoint_failures") or 0
        positions, by_dex = classify.parse_positions_by_dex(wallet)
        new_snap = snapshot_positions(positions)
        acct = classify.account_value_union(by_dex)

        ws = wallets_state.setdefault(addr, {})
        old_snap = ws.get("positions") if isinstance(ws.get("positions"), dict) else {}
        last_alert = ws.get("last_alert_ts") if isinstance(ws.get("last_alert_ts"), dict) else {}

        # 全端點失敗 → 持倉「看起來全平了」，這是資料缺失而不是事件。保留舊基準、不推播。
        all_failed = (wallet.get("n_endpoint_failures") or 0) >= (1 + len(dex_names))
        if all_failed:
            summary["wallets"].append({"address": addr, "n_positions": None,
                                       "n_events": 0, "skipped": "all_endpoints_failed"})
            continue

        events = [] if is_fresh else diff_positions(old_snap, new_snap, wcfg.WATCH_SIZE_CHANGE_PCT)
        events, suppressed = apply_cooldown(events, last_alert, now_ts,
                                            wcfg.WATCH_COOLDOWN_MINUTES * 60)
        summary["suppressed"] += suppressed
        if len(events) > wcfg.WATCH_MAX_EVENTS_PER_MESSAGE:
            n_more = len(events) - wcfg.WATCH_MAX_EVENTS_PER_MESSAGE
            events = events[: wcfg.WATCH_MAX_EVENTS_PER_MESSAGE]
            events.append({"type": "more", "key": "…", "n": n_more, "new": None, "old": None})

        ws["positions"] = new_snap
        ws["account_value"] = acct
        ws["last_seen"] = now_ts
        for ev in events:
            if ev["key"] != "…":
                last_alert[ev["key"]] = now_ts
        ws["last_alert_ts"] = {k: v for k, v in last_alert.items()
                               if now_ts - v < wcfg.WATCH_ALERT_TTL_DAYS * 86400}

        summary["wallets"].append({"address": addr, "n_positions": len(new_snap),
                                   "n_events": len(events),
                                   "account_value": acct,
                                   "by_dex": {d: v["n_positions"] for d, v in by_dex.items()}})
        summary["n_events"] += len(events)
        if events:
            blocks.append(format_events(addr, label, events, acct, len(new_snap)))

    if not args.dry_run:
        save_state(args.state, state)

    message = "\n\n".join(blocks) if blocks else None
    return message, summary


def main(argv=None):
    p = argparse.ArgumentParser(description="Hyperliquid 持倉哨兵（唯讀）")
    p.add_argument("--state", default=str(Path(__file__).resolve().parent / "state" / "state.json"))
    p.add_argument("--out-message", default="", help="有事件時把訊息寫到此檔（給 notify 用）")
    p.add_argument("--test-notify", action="store_true", help="不查 API，只產生一則測試訊息")
    p.add_argument("--dry-run", action="store_true", help="查 API 但不寫狀態檔")
    args = p.parse_args(argv)

    if args.test_notify:
        msg = test_message()
        title = "🧪 hyper-watch 測試推播"
    else:
        msg, summary = run(args)
        print("[watch] " + json.dumps(summary, ensure_ascii=False, default=str))
        if summary["is_fresh"]:
            print("[watch] 首次執行或狀態遺失 → 只建基準，不推播（避免把既有部位誤報為新開倉）")
        n = summary["n_events"]
        title = f"🔔 追蹤錢包持倉異動（{n} 筆）" if n else ""

    if msg and args.out_message:
        Path(args.out_message).write_text(f"{title}\n---\n{msg}\n", encoding="utf-8")
        print(f"[watch] 訊息已寫入 {args.out_message}")
    elif not msg:
        print("[watch] 無異動，不推播")
    return 0


if __name__ == "__main__":
    sys.exit(main())
