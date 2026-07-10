#!/usr/bin/env python3
"""hyper-observer fetch：抓 Hyperliquid 公開 read-only 數據存 snapshot。

用法：
    python3 fetch.py [--max-wallets 60] [--out-dir data/snapshots]
        [--wallets-file data/scan/candidates_YYYY-MM-DD.json]  # 宇宙改用掃描候選清單
        [--snapshot-suffix -scan] [--sleep 0.75]

行為：
1. 試打未文件化 leaderboard 端點（GET，脆弱）→ 寬鬆解析出 0x 地址清單。
   失敗（403/非 JSON/schema 不符）→ 記進 meta.endpoint_health 並退回只用 seeds，不 crash。
   若給 --wallets-file 則略過 leaderboard，宇宙改用該清單（scan_universe.py 的輸出）。
2. 錢包宇宙 = (leaderboard 或 wallets-file 地址) ∪ data/seeds.json 地址，
   去重、上限 --max-wallets（seeds 永遠保留）。
3. 每錢包 POST info API 抓 clearinghouseState / portfolio / userFills / userFunding，
   存 data/snapshots/{UTC日期}{suffix}/wallets/{addr}.json。
4. snapshot 內的 leaderboard.json 只存**瘦身摘要**（地址清單＋列數；raw 不入版控）；
   完整 raw 落到 data/tmp/leaderboard_raw_{日期}.json（.gitignore，供 scan_universe.py 用）。
5. meta（端點健康、成功/失敗計數、耗時）存 snapshot 目錄；維護 data/wallet_registry.json。

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


def leaderboard_summary(raw, addresses, raw_dump_path=None):
    """snapshot 版控內 leaderboard.json 的**瘦身摘要**（絕不含 raw——全量 raw 約 36MB，
    入版控會炸 repo；本 repo 曾因 36MB 原始檔重寫過歷史，此處是防回歸的單一出口）。"""
    return {
        "endpoint_tried": config.LEADERBOARD_ENDPOINTS,
        "addresses": addresses,
        "n_rows_total": len(_as_row_list(raw)) if raw is not None else 0,
        "note": ("raw 原始回應不入版控"
                 + (f"；已落 {raw_dump_path}（.gitignore，供 scan_universe.py 使用）"
                    if raw_dump_path else "（本次未取得 raw）")),
    }


def load_wallets_file(path, meta):
    """--wallets-file（scan_universe.py 的 candidates json）→ 去重地址清單。

    防禦性接受三種形狀：{"candidates": [{"address": ...}]}、{"wallets": [...]}、
    或純地址 list。壞檔/缺檔記 note 回空清單，不 crash。
    """
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        meta.note(f"wallets-file 讀取失敗（{path}）：{exc}")
        return []
    items = None
    if isinstance(raw, dict):
        for key in ("candidates", "wallets", "addresses"):
            if isinstance(raw.get(key), list):
                items = raw[key]
                break
    elif isinstance(raw, list):
        items = raw
    if items is None:
        meta.note(f"wallets-file 解析不到候選清單（{path}）")
        return []
    out = []
    for it in items:
        addr = it.get("address") if isinstance(it, dict) else it
        addr = (addr or "").strip().lower() if isinstance(addr, str) else ""
        if ADDR_RE.fullmatch(addr) and addr not in out:
            out.append(addr)
    return out


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
    parser.add_argument("--wallets-file", default=None,
                        help="宇宙改用此候選清單（scan_universe.py 輸出）；略過 leaderboard")
    parser.add_argument("--snapshot-suffix", default="",
                        help="snapshot 目錄名後綴，例 -scan → data/snapshots/{日期}-scan/")
    # Rate limit 計算（info API 每 IP 1200 權重/分）——150 錢包掃描的餘裕：
    #   每錢包 4 呼叫 ≈ clearinghouseState(2) + portfolio(20) + userFills(20；大回應每 20 筆
    #   另加權重，2000 筆上限最壞 +100) + userFunding(20) ≈ 62（典型）～162（最壞）權重。
    #   每請求間隔 ≈ sleep + 網路延遲(~0.3s)，平均權重 62/4 ≈ 15.5/請求：
    #     sleep 0.35s → ~92 req/min ≈ 1,430 權重/min > 1200 ✗（提案值不足，不採用）
    #     sleep 0.50s → ~75 req/min ≈ 1,160 權重/min（無餘裕，且未計大 userFills 附加）✗
    #     sleep 0.75s → ~57 req/min ≈   890 權重/min（~26% 餘裕，容納 userFills 附加權重）✓
    #   150 錢包 × 4 req × ~1.05s ≈ 10.5 分鐘，CI 可接受。掃描段（--max-wallets 150）
    #   一律配 --sleep 0.75；每日 top-60 維持預設 0.5（總量減半，實測未觸限）。
    parser.add_argument("--sleep", type=float, default=None,
                        help=f"每請求間隔秒數（預設 config.HTTP_SLEEP_BETWEEN="
                             f"{config.HTTP_SLEEP_BETWEEN}）")
    args = parser.parse_args(argv)

    if args.sleep is not None:
        config.HTTP_SLEEP_BETWEEN = args.sleep

    started = time.time()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_root = Path(args.out_dir)
    if not out_root.is_absolute():
        out_root = BASE_DIR / out_root  # 相對路徑一律以腳本所在目錄為錨
    snap_dir = out_root / (today + args.snapshot_suffix)
    data_dir = BASE_DIR / "data"
    meta = Meta()

    summary = {"date": today, "snapshot_dir": str(snap_dir), "universe_size": 0,
               "wallets_ok": 0, "wallets_partial": 0, "wallets_failed": 0,
               "leaderboard_addresses": 0,
               "requests_ok": 0, "requests_failed": 0, "elapsed_sec": 0}
    try:
        print(f"[fetch] snapshot dir: {snap_dir}")
        if args.wallets_file:
            # 掃描模式：宇宙來自 scan_universe.py 的候選清單，不再打 leaderboard
            wf_path = Path(args.wallets_file)
            if not wf_path.is_absolute():
                wf_path = BASE_DIR / wf_path
            lb_addrs = load_wallets_file(wf_path, meta)
            meta.note(f"宇宙來自 --wallets-file（{len(lb_addrs)} 地址），略過 leaderboard 端點")
            write_json(snap_dir / "leaderboard.json",
                       {"source": "wallets_file", "wallets_file": str(wf_path),
                        "addresses": lb_addrs, "n_rows_total": len(lb_addrs),
                        "note": "掃描模式：宇宙取自 scan_universe.py 候選清單"})
        else:
            raw_lb, lb_addrs = fetch_leaderboard(meta)
            # 完整 raw（全量可達 ~36MB）只落工作區暫存 data/tmp/（.gitignore、CI prune），
            # 供 scan_universe.py 讀取；版控內 snapshot 只留瘦身摘要，嚴禁回歸塞 raw。
            raw_dump_path = None
            if raw_lb is not None:
                raw_dump_path = data_dir / "tmp" / f"leaderboard_raw_{today}.json"
                try:
                    write_json(raw_dump_path, raw_lb)
                    print(f"[fetch] leaderboard raw → {raw_dump_path}")
                except Exception as exc:
                    meta.note(f"leaderboard raw 暫存失敗：{exc}")
                    raw_dump_path = None
            write_json(snap_dir / "leaderboard.json",
                       leaderboard_summary(raw_lb, lb_addrs, raw_dump_path))
        summary["leaderboard_addresses"] = len(lb_addrs)
        print(f"[fetch] universe source addresses: {len(lb_addrs)}")

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
