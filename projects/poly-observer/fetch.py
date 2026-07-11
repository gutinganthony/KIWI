#!/usr/bin/env python3
"""poly-observer fetch：抓 Polymarket 公開 read-only 數據存 snapshot。

用法：
    python3 fetch.py [--max-wallets 60] [--out-dir data/snapshots]

行為：
1. 抓 leaderboard（1m、all 兩窗，端點依序 fallback）→ 錢包宇宙 =
   兩窗 top50 聯集 + data/seeds.json 地址，去重、上限 --max-wallets（seeds 永遠保留）。
2. 每錢包抓 activity（分頁）/positions/value/pnl 曲線，
   存 data/snapshots/{UTC日期}/wallets/{addr}.json。
3. leaderboard 原始檔與 meta（端點健康、成功/失敗計數、耗時）存同目錄。
4. 維護 data/wallet_registry.json。

防禦性設計：任何端點全掛→記進 meta（status code＋body 前 200 字），
繼續跑其他部分，永不整體 crash（main 一律 exit 0，讓後續步驟與 commit-back 能落地）。

本腳本純唯讀：只發 HTTP GET，不含任何下單、金鑰、簽章、錢包連線功能。
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import config

try:
    import requests
except Exception as exc:  # pragma: no cover - 防禦：requests 缺失也要能落 meta
    requests = None
    _REQUESTS_IMPORT_ERROR = str(exc)
else:
    _REQUESTS_IMPORT_ERROR = None

BASE_DIR = Path(__file__).resolve().parent
ADDR_RE = re.compile(r"0x[0-9a-fA-F]{40}")


# ---------------------------------------------------------------------------
# HTTP 層
# ---------------------------------------------------------------------------

class Meta:
    """收集端點健康與計數，最後寫進 meta.json。"""

    def __init__(self):
        self.endpoint_health = []   # 每次請求（含重試最終結果）一筆
        self.requests_ok = 0
        self.requests_failed = 0
        self.notes = []

    def record(self, name, url, ok, status=None, error=None, elapsed=None):
        self.endpoint_health.append({
            "name": name,
            "url": url,
            "ok": ok,
            "status": status,
            "error": (error[: config.ERROR_BODY_SNIPPET_LEN] if error else None),
            "elapsed_sec": round(elapsed, 2) if elapsed is not None else None,
        })
        if ok:
            self.requests_ok += 1
        else:
            self.requests_failed += 1

    def note(self, msg):
        print(f"[note] {msg}")
        self.notes.append(msg)


def http_get_json(url, name, meta):
    """GET url，重試 config.HTTP_RETRIES 次（backoff 1s/3s）。

    回傳 (data, ok)。失敗時 data=None，錯誤細節記進 meta。
    """
    if requests is None:
        meta.record(name, url, False, error=f"requests import failed: {_REQUESTS_IMPORT_ERROR}")
        return None, False

    headers = {"User-Agent": config.USER_AGENT, "Accept": "application/json"}
    last_error, last_status = None, None
    start = time.time()
    for attempt in range(1 + config.HTTP_RETRIES):
        if attempt > 0:
            backoff_idx = min(attempt - 1, len(config.HTTP_BACKOFFS) - 1)
            time.sleep(config.HTTP_BACKOFFS[backoff_idx])
        try:
            resp = requests.get(url, headers=headers, timeout=config.HTTP_TIMEOUT)
            last_status = resp.status_code
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError as exc:
                    last_error = f"invalid JSON: {exc}; body={resp.text[:config.ERROR_BODY_SNIPPET_LEN]}"
                    continue
                meta.record(name, url, True, status=200, elapsed=time.time() - start)
                time.sleep(config.HTTP_SLEEP_BETWEEN)
                return data, True
            last_error = f"HTTP {resp.status_code}; body={resp.text[:config.ERROR_BODY_SNIPPET_LEN]}"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    meta.record(name, url, False, status=last_status, error=last_error,
                elapsed=time.time() - start)
    time.sleep(config.HTTP_SLEEP_BETWEEN)
    return None, False


def fetch_with_fallback(url_list, name, meta):
    """依序試端點清單，回傳 (data, 成功的 url)；全掛回傳 (None, None)。"""
    for url in url_list:
        data, ok = http_get_json(url, name, meta)
        if ok:
            return data, url
    return None, None


# ---------------------------------------------------------------------------
# Leaderboard 與錢包宇宙
# ---------------------------------------------------------------------------

def _as_entry_list(data):
    """leaderboard 回應可能是 list 或包一層 dict，防禦性展開。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("leaderboard", "data", "results", "entries", "users"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def extract_address(entry):
    """從 leaderboard 條目擷取 0x 地址（欄位名防禦性掃描）。"""
    if isinstance(entry, str):
        m = ADDR_RE.search(entry)
        return m.group(0).lower() if m else None
    if not isinstance(entry, dict):
        return None
    for key in ("proxyWallet", "proxy_wallet", "user", "address", "wallet",
                "walletAddress", "userAddress"):
        val = entry.get(key)
        if isinstance(val, str):
            m = ADDR_RE.search(val)
            if m:
                return m.group(0).lower()
        elif isinstance(val, dict):
            inner = extract_address(val)
            if inner:
                return inner
    for val in entry.values():  # 最後手段：掃所有字串值
        if isinstance(val, str):
            m = ADDR_RE.fullmatch(val.strip())
            if m:
                return m.group(0).lower()
    return None


def fetch_leaderboards(meta):
    """回傳 (raw_by_window, addresses_ordered)。window 參數不被接受時試 fallback。"""
    raw_by_window = {}
    addresses = []
    for window in config.LEADERBOARD_WINDOWS:
        candidates = [window]
        fb = config.LEADERBOARD_WINDOW_FALLBACKS.get(window)
        if fb:
            candidates.append(fb)
        got = None
        for w in candidates:
            urls = [u.format(window=w) for u in config.LEADERBOARD_ENDPOINTS]
            data, used_url = fetch_with_fallback(urls, f"leaderboard[{w}]", meta)
            entries = _as_entry_list(data) if data is not None else []
            if entries:
                got = {"window_requested": window, "window_used": w,
                       "endpoint": used_url, "entries": entries}
                break
            if data is not None:
                meta.note(f"leaderboard window={w} 回應 200 但無條目，嘗試下一個 window 候選")
        if got is None:
            meta.note(f"leaderboard window={window} 全部端點失敗，該窗略過")
            raw_by_window[window] = {"window_requested": window, "window_used": None,
                                     "endpoint": None, "entries": []}
            continue
        raw_by_window[window] = got
        for entry in got["entries"][:50]:
            addr = extract_address(entry)
            if addr and addr not in addresses:
                addresses.append(addr)
    return raw_by_window, addresses


def load_seeds(data_dir, meta):
    """讀 data/seeds.json，回傳 [(addr, label)]；缺檔/壞檔記 note 不 crash。"""
    seeds_path = data_dir / "seeds.json"
    out = []
    try:
        raw = json.loads(seeds_path.read_text(encoding="utf-8"))
        for item in raw.get("wallets", []):
            addr = (item.get("address") or "").strip().lower()
            if ADDR_RE.fullmatch(addr):
                out.append((addr, item.get("label", "")))
    except FileNotFoundError:
        meta.note(f"seeds.json 不存在（{seeds_path}），只用 leaderboard 宇宙")
    except Exception as exc:
        meta.note(f"seeds.json 解析失敗：{exc}")
    return out


def build_universe(seed_addrs, lb_addrs, max_wallets):
    """seeds 永遠保留；剩餘名額按 leaderboard 順序補滿。"""
    universe = list(dict.fromkeys(seed_addrs))
    for addr in lb_addrs:
        if len(universe) >= max_wallets and addr not in universe:
            continue
        if addr not in universe:
            universe.append(addr)
    return universe[: max(max_wallets, len(seed_addrs))]


# ---------------------------------------------------------------------------
# 每錢包抓取
# ---------------------------------------------------------------------------

def fetch_activity(addr, meta):
    """分頁抓 activity，抓到無資料或上限 ACTIVITY_MAX_RECORDS 筆為止。"""
    records, truncated = [], False
    offset = 0
    while offset < config.ACTIVITY_MAX_RECORDS:
        urls = [u.format(addr=addr, off=offset) for u in config.ACTIVITY_ENDPOINTS]
        data, _ = fetch_with_fallback(urls, f"activity[{addr[:10]}…@{offset}]", meta)
        if data is None:
            return records, truncated, False
        page = data if isinstance(data, list) else _as_entry_list(data)
        if not page:
            break
        records.extend(page)
        if len(page) < config.ACTIVITY_PAGE_LIMIT:
            break
        offset += config.ACTIVITY_PAGE_LIMIT
    else:
        truncated = True
    if len(records) >= config.ACTIVITY_MAX_RECORDS:
        truncated = True
        records = records[: config.ACTIVITY_MAX_RECORDS]
    return records, truncated, True


def fetch_wallet(addr, meta):
    """抓單一錢包四類資料，任何一類失敗都記錄並繼續。"""
    wallet = {
        "address": addr,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "activity": None, "activity_truncated": False,
        "positions": None, "value": None,
        "pnl": None, "pnl_endpoint": None,
        "errors": [],
    }
    activity, truncated, ok = fetch_activity(addr, meta)
    if ok:
        wallet["activity"] = activity
        wallet["activity_truncated"] = truncated
    else:
        wallet["errors"].append("activity: all endpoints failed")

    for field, endpoints in (("positions", config.POSITIONS_ENDPOINTS),
                             ("value", config.VALUE_ENDPOINTS)):
        urls = [u.format(addr=addr) for u in endpoints]
        data, _ = fetch_with_fallback(urls, f"{field}[{addr[:10]}…]", meta)
        if data is not None:
            wallet[field] = data
        else:
            wallet["errors"].append(f"{field}: all endpoints failed")

    pnl_urls = [u.format(addr=addr) for u in config.PNL_ENDPOINTS]
    pnl, used = fetch_with_fallback(pnl_urls, f"pnl[{addr[:10]}…]", meta)
    if pnl is not None:
        wallet["pnl"], wallet["pnl_endpoint"] = pnl, used
    else:
        wallet["errors"].append("pnl: all endpoints failed")
    return wallet


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def update_registry(data_dir, universe, seed_labels, today, meta):
    registry_path = data_dir / "wallet_registry.json"
    registry = {}
    try:
        if registry_path.exists():
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        meta.note(f"wallet_registry.json 解析失敗，重建：{exc}")
        registry = {}
    for addr in universe:
        rec = registry.get(addr) or {"first_seen": today, "appearances": 0}
        rec["last_seen"] = today
        rec["appearances"] = int(rec.get("appearances", 0)) + 1
        if addr in seed_labels and seed_labels[addr]:
            rec["label"] = seed_labels[addr]
        registry[addr] = rec
    try:
        registry_path.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8")
    except Exception as exc:
        meta.note(f"wallet_registry.json 寫入失敗：{exc}")
    return registry


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Polymarket read-only snapshot fetcher")
    parser.add_argument("--max-wallets", type=int, default=config.DEFAULT_MAX_WALLETS)
    parser.add_argument("--out-dir", default=str(BASE_DIR / "data" / "snapshots"))
    args = parser.parse_args(argv)

    started = time.time()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_root = Path(args.out_dir)
    if not out_root.is_absolute():
        out_root = BASE_DIR / out_root  # 相對路徑一律以腳本所在目錄為錨
    snap_dir = out_root / today
    data_dir = BASE_DIR / "data"
    meta = Meta()

    summary = {"date": today, "snapshot_dir": str(snap_dir), "universe_size": 0,
               "wallets_ok": 0, "wallets_partial": 0, "wallets_failed": 0,
               "requests_ok": 0, "requests_failed": 0, "elapsed_sec": 0}
    try:
        print(f"[fetch] snapshot dir: {snap_dir}")
        raw_lb, lb_addrs = fetch_leaderboards(meta)
        write_json(snap_dir / "leaderboard.json", raw_lb)
        print(f"[fetch] leaderboard addresses: {len(lb_addrs)}")

        seeds = load_seeds(data_dir, meta)
        seed_labels = dict(seeds)
        universe = build_universe([a for a, _ in seeds], lb_addrs, args.max_wallets)
        summary["universe_size"] = len(universe)
        print(f"[fetch] wallet universe: {len(universe)} (seeds={len(seeds)})")

        for i, addr in enumerate(universe, 1):
            try:
                wallet = fetch_wallet(addr, meta)
            except Exception as exc:  # 單一錢包炸掉不影響其他
                meta.note(f"wallet {addr} 抓取例外：{type(exc).__name__}: {exc}")
                summary["wallets_failed"] += 1
                continue
            write_json(snap_dir / "wallets" / f"{addr}.json", wallet)
            if not wallet["errors"]:
                summary["wallets_ok"] += 1
            elif wallet["activity"] is not None or wallet["pnl"] is not None:
                summary["wallets_partial"] += 1
            else:
                summary["wallets_failed"] += 1
            print(f"[fetch] {i}/{len(universe)} {addr} "
                  f"errors={len(wallet['errors'])}")

        update_registry(data_dir, universe, seed_labels, today, meta)
    except Exception as exc:  # 永不整體 crash：記進 meta，照樣落地
        meta.note(f"fetch 主流程例外：{type(exc).__name__}: {exc}")

    summary["requests_ok"] = meta.requests_ok
    summary["requests_failed"] = meta.requests_failed
    summary["elapsed_sec"] = round(time.time() - started, 1)
    try:
        write_json(snap_dir / "meta.json", {
            **summary,
            "endpoint_health": meta.endpoint_health,
            "notes": meta.notes,
        })
    except Exception as exc:
        print(f"[fetch] meta.json 寫入失敗：{exc}", file=sys.stderr)

    print("META " + json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
