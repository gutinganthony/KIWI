#!/usr/bin/env python3
"""hyper-observer fetch：抓 Hyperliquid 公開 read-only 數據存 snapshot。

用法：
    python3 fetch.py [--max-wallets 60] [--out-dir data/snapshots]

行為：
1. 試打未文件化 leaderboard 端點（GET，脆弱）→ 寬鬆解析出 0x 地址清單。
   失敗（403/非 JSON/schema 不符）→ 記進 meta.endpoint_health 並退回只用 seeds，不 crash。
2. 錢包宇宙 = leaderboard 地址 ∪ data/seeds.json 地址，去重、上限 --max-wallets（seeds 永遠保留）。
3. 每錢包 POST info API 抓 clearinghouseState / portfolio / userFills / userFunding，
   存 data/snapshots/{UTC日期}/wallets/{addr}.json。
4. leaderboard 原始檔與 meta（端點健康、成功/失敗計數、耗時）存同目錄。
5. 維護 data/wallet_registry.json。

防禦性設計：任何端點全掛→記進 meta（status code＋body 前 200 字），繼續跑其他部分，
永不整體 crash（main 一律 exit 0，讓後續步驟與 commit-back 能落地）。

本腳本純唯讀：只發公開 info API 的唯讀查詢（POST info + GET leaderboard），
不含任何下單、簽章、私鑰、錢包連線、exchange endpoint。
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
# Meta：端點健康與計數
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


# ---------------------------------------------------------------------------
# HTTP 層（GET 供 leaderboard；POST 供 info API；皆唯讀查詢）
# ---------------------------------------------------------------------------

def http_get_json(url, name, meta):
    """GET url（leaderboard），重試 config.HTTP_RETRIES 次。回傳 (data, ok)。"""
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


def http_post_info(body, name, meta):
    """POST config.INFO_URL 的免金鑰 info API（唯讀查詢）。回傳 (data, ok)。

    body 例：{"type": "clearinghouseState", "user": "0x..."}。純查詢，不含簽章/下單。
    """
    if requests is None:
        meta.record(name, config.INFO_URL, False,
                    error=f"requests import failed: {_REQUESTS_IMPORT_ERROR}")
        return None, False
    headers = {"Content-Type": "application/json",
               "User-Agent": config.USER_AGENT, "Accept": "application/json"}
    last_error, last_status = None, None
    start = time.time()
    for attempt in range(1 + config.HTTP_RETRIES):
        if attempt > 0:
            backoff_idx = min(attempt - 1, len(config.HTTP_BACKOFFS) - 1)
            time.sleep(config.HTTP_BACKOFFS[backoff_idx])
        try:
            resp = requests.post(config.INFO_URL, headers=headers, json=body,
                                 timeout=config.HTTP_TIMEOUT)
            last_status = resp.status_code
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError as exc:
                    last_error = f"invalid JSON: {exc}; body={resp.text[:config.ERROR_BODY_SNIPPET_LEN]}"
                    continue
                meta.record(name, config.INFO_URL, True, status=200, elapsed=time.time() - start)
                time.sleep(config.HTTP_SLEEP_BETWEEN)
                return data, True
            last_error = f"HTTP {resp.status_code}; body={resp.text[:config.ERROR_BODY_SNIPPET_LEN]}"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    meta.record(name, config.INFO_URL, False, status=last_status, error=last_error,
                elapsed=time.time() - start)
    time.sleep(config.HTTP_SLEEP_BETWEEN)
    return None, False


# ---------------------------------------------------------------------------
# Leaderboard 與錢包宇宙
# ---------------------------------------------------------------------------

def _as_row_list(data):
    """leaderboard 回應可能是 list 或包一層 dict，防禦性展開成 rows。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("leaderboardRows", "leaderboard", "rows", "data",
                    "results", "entries", "users"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def extract_address(entry):
    """從 leaderboard 條目寬鬆擷取 0x 地址（欄位名不確定，防禦性掃描）。"""
    if isinstance(entry, str):
        m = ADDR_RE.search(entry)
        return m.group(0).lower() if m else None
    if not isinstance(entry, dict):
        return None
    for key in ("ethAddress", "eth_address", "address", "user", "wallet",
                "walletAddress", "userAddress", "account"):
        val = entry.get(key)
        if isinstance(val, str):
            m = ADDR_RE.search(val)
            if m:
                return m.group(0).lower()
        elif isinstance(val, dict):
            inner = extract_address(val)
            if inner:
                return inner
    for val in entry.values():  # 最後手段：掃所有字串值找完整 40-hex 地址
        if isinstance(val, str):
            m = ADDR_RE.fullmatch(val.strip())
            if m:
                return m.group(0).lower()
    return None


def extract_addresses(data, limit=200):
    """leaderboard 原始回應 → 去重的地址清單（純函式，供離線測試）。"""
    addresses = []
    for row in _as_row_list(data)[:limit]:
        addr = extract_address(row)
        if addr and addr not in addresses:
            addresses.append(addr)
    return addresses


def fetch_leaderboard(meta, get_fn=None):
    """試打 leaderboard 端點清單，回傳 (raw, addresses)。

    get_fn 可注入（測試用）以模擬端點失敗；預設用 http_get_json。
    任一端點失敗或無地址 → 記 note 並回傳空清單（呼叫端會退回只用 seeds），不 crash。
    """
    get_fn = get_fn or http_get_json
    for url in config.LEADERBOARD_ENDPOINTS:
        data, ok = get_fn(url, "leaderboard", meta)
        if ok and data is not None:
            addresses = extract_addresses(data)
            if addresses:
                return data, addresses
            meta.note(f"leaderboard 端點回應 200 但解析不到地址：{url}")
    meta.note("leaderboard 全部端點失敗或無地址，退回只用 seeds（宇宙 = seeds）")
    return None, []


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
# 每錢包抓取（POST info API）
# ---------------------------------------------------------------------------

def _info_body(info_type, addr):
    body = {"type": info_type, "user": addr}
    if info_type == "userFunding" and config.USER_FUNDING_START_MS is not None:
        body["startTime"] = config.USER_FUNDING_START_MS
    return body


def fetch_wallet(addr, meta, post_fn=None):
    """抓單一錢包的四類 info 資料，任何一類失敗都記錄並繼續。"""
    post_fn = post_fn or http_post_info
    wallet = {
        "address": addr,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "clearinghouseState": None,
        "portfolio": None,
        "userFills": None,
        "userFunding": None,
        "errors": [],
    }
    for info_type in config.INFO_TYPES:
        body = _info_body(info_type, addr)
        data, ok = post_fn(body, f"{info_type}[{addr[:10]}…]", meta)
        if ok:
            wallet[info_type] = data
        else:
            wallet["errors"].append(f"{info_type}: request failed")
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
    parser = argparse.ArgumentParser(description="Hyperliquid read-only snapshot fetcher")
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
               "leaderboard_addresses": 0,
               "requests_ok": 0, "requests_failed": 0, "elapsed_sec": 0}
    try:
        print(f"[fetch] snapshot dir: {snap_dir}")
        raw_lb, lb_addrs = fetch_leaderboard(meta)
        write_json(snap_dir / "leaderboard.json",
                   {"endpoint_tried": config.LEADERBOARD_ENDPOINTS,
                    "addresses": lb_addrs, "raw": raw_lb})
        summary["leaderboard_addresses"] = len(lb_addrs)
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
            elif len(wallet["errors"]) < len(config.INFO_TYPES):
                summary["wallets_partial"] += 1
            else:
                summary["wallets_failed"] += 1
            print(f"[fetch] {i}/{len(universe)} {addr} errors={len(wallet['errors'])}")

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
