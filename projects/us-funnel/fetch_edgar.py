#!/usr/bin/env python3
"""us-funnel fetch：抓 EDGAR Form 4 每日索引與逐筆 filing，解析成精簡事件檔。

用法：
    python3 fetch_edgar.py [--days 10] [--max-filings 4000] [--force]

行為：
1. 往回掃 --days 個日曆日（跳過週六日）的每日索引
   https://www.sec.gov/Archives/edgar/daily-index/{YYYY}/QTR{q}/form.{YYYYMMDD}.idx，
   篩 form type 恰為 "4"（排除 4/A 與 424B*）。索引 404＝假日，跳過不算錯。
2. 逐筆抓 filing 全文（.txt），擷取 <ownershipDocument> XML，解析 issuer、
   reportingOwner（officerTitle/isDirector）、nonDerivativeTransaction 的 P/S 交易
   與 10b5-1 checkbox（aff10b5One，2023-04 起強制欄位）。
3. 每個申報日落一個精簡事件檔 data/events/form4_{YYYY-MM-DD}.json：
   buys 逐筆保留（集群偵測與評分需要人與職稱）、sells 按 issuer 聚合（否決關卡只需總額）。
   已存在且標記 complete 的日檔跳過（每日增量只抓最新一天）；過期日檔自動刪除。
4. meta（端點健康、成功/失敗計數、耗時）合併寫進 data/meta_latest.json 的 fetch 節。

EDGAR 禮儀（SEC fair access policy——規定，不是建議；違反封鎖 10 分鐘）：
- User-Agent 必須含可聯絡方式：config.EDGAR_USER_AGENT（GitHub repo＋noreply 信箱，
  真實可聯絡——假信箱疑遭過濾致 403，見 config 註解）
- 限速 ≤10 req/s：每請求後 sleep config.EDGAR_SLEEP_BETWEEN（0.15s），序列執行絕不並行
- 403（AccessDenied，疑共享 IP 暫時封鎖）：重試前等 config.HTTP_403_BACKOFFS=[10,30]s

防禦性設計：任何端點失敗→記進 meta（status code＋body 前 200 字），繼續跑其他部分，
永不整體 crash（main 一律 exit 0，讓後續 funnel/track 與 commit-back 能落地）。
本腳本純唯讀：只 GET 公開資料，不含任何下單、券商連線、簽章、金鑰。
"""

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
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

# 每日索引行：form type 恰為 "4" 開頭，行尾為 edgar/data/... 的 .txt 路徑
IDX_LINE_RE = re.compile(
    r"^4\s+(?P<company>.*?)\s+(?P<cik>\d+)\s+(?P<date>\d{4}-?\d{2}-?\d{2})\s+"
    r"(?P<path>edgar/[^\s]+\.txt)\s*$"
)
# filing 全文（SGML 包裹）內的 ownershipDocument XML 區段
OWNERSHIP_XML_RE = re.compile(
    r"<ownershipDocument\b.*?</ownershipDocument>", re.DOTALL | re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Meta：端點健康與計數（合併寫入 data/meta_latest.json 的單一節）
# ---------------------------------------------------------------------------

class Meta:
    """收集端點健康與錯誤，最後由 update_meta() 合併寫進 meta_latest.json。"""

    def __init__(self):
        self.endpoint_health = []   # 索引級請求與「失敗的」filing 請求（成功 filing 只計數）
        self.requests_ok = 0
        self.requests_failed = 0
        self.errors = []
        # 價格源健康（make_price_fetcher 填；fetch 腳本不用，恆為零/空）——
        # 兩源各自成功/失敗計數＋per-ticker 使用源（stooq|yahoo|none），供 monitor 頁判讀
        self.price_source_stats = {"stooq": {"ok": 0, "failed": 0},
                                   "yahoo": {"ok": 0, "failed": 0}}
        self.price_sources = {}     # ticker -> "stooq" | "yahoo" | "none"
        # 市值來源計數（funnel 的 run_funnel 填；fetch/tracking 不用，恆為零）——
        # edgar=company facts 股數×收盤、yahoo=quoteSummary/v7 批次備援、none=全敗保守
        self.mcap_source_stats = {"edgar": 0, "yahoo": 0, "none": 0}

    def record(self, name, url, ok, status=None, error=None, elapsed=None,
               record_ok=True, count=True):
        if count:
            if ok:
                self.requests_ok += 1
            else:
                self.requests_failed += 1
        if ok and not record_ok:
            return  # 大量 filing 成功請求只計數不逐筆記錄，防 meta 膨脹
        self.endpoint_health.append({
            "name": name,
            "url": url,
            "ok": ok,
            "status": status,
            "error": (error[: config.ERROR_BODY_SNIPPET_LEN] if error else None),
            "elapsed_sec": round(elapsed, 2) if elapsed is not None else None,
        })

    def error(self, msg):
        print(f"[error] {msg}")
        self.errors.append(msg)

    def note(self, msg):
        print(f"[note] {msg}")


def load_meta(data_dir):
    """讀既有 meta_latest.json；缺檔/壞檔回空 dict（防禦，不 crash）。"""
    path = Path(data_dir) / "meta_latest.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def update_meta(data_dir, section, payload):
    """把 payload 合併寫進 meta_latest.json 的 section 節（fetch/funnel/tracking）。

    各腳本只覆蓋自己那一節，其他節保留——monitor 網頁靠此檔看整條管線健康。
    endpoint_health / errors 依 config 上限截尾。
    """
    if isinstance(payload.get("endpoint_health"), list):
        payload["endpoint_health"] = payload["endpoint_health"][-config.META_ENDPOINT_HEALTH_MAX:]
    if isinstance(payload.get("errors"), list):
        payload["errors"] = payload["errors"][-config.META_ERRORS_MAX:]
    meta = load_meta(data_dir)
    meta[section] = payload
    meta["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(Path(data_dir) / "meta_latest.json", meta)


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------------------
# HTTP 層（GET 純文字；EDGAR 禮儀見模組 docstring）
# ---------------------------------------------------------------------------

def http_get_text(url, name, meta, record_ok=True, sleep=None, headers=None,
                  retries=None):
    """GET url 回傳 (text, status, ok)。重試 retries（預設 config.HTTP_RETRIES）次，永不 raise。

    - headers 預設 EDGAR 禮儀 UA（config.EDGAR_USER_AGENT，SEC 規定含可聯絡方式；
      Stooq 亦沿用無害）；需要瀏覽器 UA 的源（Yahoo）由呼叫端覆蓋。
    - 每請求後 sleep（預設 config.EDGAR_SLEEP_BETWEEN=0.15s，≤10 req/s 規定的餘裕值）。
    - 404 視為「明確不存在」（假日索引），不重試。
    - 403（EDGAR AccessDenied，疑共享 IP 暫時封鎖）：重試前改等
      config.HTTP_403_BACKOFFS=[10,30]s；仍失敗 → 呼叫端既有優雅降級（吃快取/跳過檢查）。
    """
    sleep = config.EDGAR_SLEEP_BETWEEN if sleep is None else sleep
    retries = config.HTTP_RETRIES if retries is None else retries
    if requests is None:
        meta.record(name, url, False, error=f"requests import failed: {_REQUESTS_IMPORT_ERROR}")
        return None, None, False
    if headers is None:
        headers = {"User-Agent": config.EDGAR_USER_AGENT,
                   "Accept-Encoding": "gzip, deflate"}
    last_error, last_status = None, None
    start = time.time()
    for attempt in range(1 + retries):
        if attempt > 0:
            backoffs = (config.HTTP_403_BACKOFFS if last_status == 403
                        else config.HTTP_BACKOFFS)
            backoff_idx = min(attempt - 1, len(backoffs) - 1)
            time.sleep(backoffs[backoff_idx])
        try:
            resp = requests.get(url, headers=headers, timeout=config.HTTP_TIMEOUT)
            last_status = resp.status_code
            if resp.status_code == 200:
                meta.record(name, url, True, status=200,
                            elapsed=time.time() - start, record_ok=record_ok)
                time.sleep(sleep)
                return resp.text, 200, True
            if resp.status_code == 404:
                last_error = "HTTP 404"
                break  # 明確不存在（週末/假日索引），不重試
            last_error = f"HTTP {resp.status_code}; body={resp.text[:config.ERROR_BODY_SNIPPET_LEN]}"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    meta.record(name, url, False, status=last_status, error=last_error,
                elapsed=time.time() - start)
    time.sleep(sleep)
    return None, last_status, False


# ---------------------------------------------------------------------------
# EDGAR company facts：流通股數（風險分級的市值來源；funnel.py import 使用）
# ---------------------------------------------------------------------------

def parse_shares_outstanding(text):
    """company concept JSON → 最新一筆 units.shares 的 val；無效/缺 → None。純函式。

    units.shares 條目按 end（期末日）取最新；缺 end 時退回列表最後一筆。
    """
    try:
        data = json.loads(text)
    except Exception:
        return None
    entries = (data.get("units") or {}).get("shares") or []
    entries = [e for e in entries if isinstance(e, dict) and e.get("val") is not None]
    if not entries:
        return None
    latest = max(entries, key=lambda e: str(e.get("end") or ""))
    try:
        val = float(latest["val"])
    except (TypeError, ValueError):
        return None
    return val if val > 0 else None


def fetch_shares_outstanding(cik, meta, get_fn=None):
    """issuer CIK → 最新流通股數（shares）；全部來源失敗 → None（呼叫端保守分級）。

    依序試 config.SHARES_OUTSTANDING_CONCEPTS 的 (taxonomy, tag)：404 或缺數據換下一個。
    沿用 EDGAR UA 禮儀與 sleep（http_get_text 預設值）；只對否決關 survivors 呼叫。
    回 None 時必記一筆 company-facts 失敗進 meta.endpoint_health（count=False 不重複
    計數）——mcap unknown 在 meta 必須有痕跡，供 monitor 頁健康判讀。
    """
    get_fn = get_fn or http_get_text
    cik10 = str(cik or "").strip().lstrip("0")
    if not cik10.isdigit():
        meta.record(f"company-facts {cik or '?'}", None, False,
                    error="CIK 無效，未發請求（mcap → None 保守分級）", count=False)
        return None
    url = None
    for taxonomy, tag in config.SHARES_OUTSTANDING_CONCEPTS:
        url = config.EDGAR_COMPANY_CONCEPT_URL.format(
            cik10=cik10.zfill(10), taxonomy=taxonomy, tag=tag)
        text, _, ok = get_fn(url, f"company-concept {cik10} {taxonomy}/{tag}", meta,
                             record_ok=False)
        if not ok:
            continue
        shares = parse_shares_outstanding(text)
        if shares is not None:
            return shares
    meta.record(f"company-facts {cik10}", url, False,
                error="所有 concept 皆失敗或缺 units.shares（mcap → None 保守分級）",
                count=False)
    return None


# ---------------------------------------------------------------------------
# 每日索引
# ---------------------------------------------------------------------------

def daily_index_url(d):
    quarter = (d.month - 1) // 3 + 1
    return config.EDGAR_DAILY_INDEX_URL.format(
        year=d.year, quarter=quarter, yyyymmdd=d.strftime("%Y%m%d"))


def parse_daily_index(text):
    """form.idx 內容 → [{'company','cik','path'}]，只收 form type 恰為 '4' 的行。

    純函式（離線測試用）。行格式為固定欄寬，但用 regex 防禦解析：
    form type 為行首 token，'4/A'、'424B5' 等以 '4' 開頭的其他型別不會匹配
    （regex 要求 '4' 後緊接空白）。日期欄 daily 與 full-index 格式不同
    （YYYYMMDD vs YYYY-MM-DD），皆容忍。
    """
    rows = []
    for line in text.splitlines():
        m = IDX_LINE_RE.match(line.strip())
        if not m:
            continue
        rows.append({
            "company": m.group("company").strip(),
            "cik": m.group("cik"),
            "path": m.group("path"),
        })
    return rows


# ---------------------------------------------------------------------------
# Form 4 解析（純函式，離線測試覆蓋）
# ---------------------------------------------------------------------------

def extract_ownership_xml(text):
    """filing 全文（SGML 包裹的 .txt）→ <ownershipDocument> XML 字串；找不到回 None。"""
    if not text:
        return None
    m = OWNERSHIP_XML_RE.search(text)
    return m.group(0) if m else None


def _text(el):
    """元素文字；若有 <value> 子元素（Form 4 慣用包法）優先取之。"""
    if el is None:
        return None
    v = el.find("value")
    if v is not None and v.text is not None:
        return v.text.strip()
    return el.text.strip() if el.text else None


def _find_text(root, path):
    return _text(root.find(path))


def _to_float(s):
    try:
        return float(str(s).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _to_bool(s):
    return str(s).strip().lower() in ("1", "true")


def parse_form4_xml(xml_text):
    """ownershipDocument XML → 精簡 dict；解析失敗回 None（呼叫端計 parse_failed）。

    回傳：{issuer_cik, ticker, company, ten_b5_1, owners:[{cik,name,title,dir,off}],
           transactions:[{code, date, shares, price}]}
    - ten_b5_1：文件級 <aff10b5One>（10b5-1 checkbox，2023-04 起強制；更早的檔案
      沒有此欄位 → 預設 False，v0 不追溯舊制猜測）。
    - transactions 只收 nonDerivativeTransaction 的 P / S 兩碼（漏斗只用得到這兩種；
      A=獎酬授予、F=繳稅回售、M=行權等非自主市場交易一律不收）。
    """
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return None
    issuer = root.find("issuer")
    if issuer is None:
        return None
    ticker = (_find_text(issuer, "issuerTradingSymbol") or "").strip().upper()
    doc = {
        "issuer_cik": (_find_text(issuer, "issuerCik") or "").lstrip("0") or None,
        "ticker": ticker,
        "company": _find_text(issuer, "issuerName") or "",
        "ten_b5_1": _to_bool(_find_text(root, "aff10b5One")),
        "owners": [],
        "transactions": [],
    }
    for ro in root.findall("reportingOwner"):
        rel = ro.find("reportingOwnerRelationship")
        is_dir = _to_bool(_find_text(rel, "isDirector")) if rel is not None else False
        is_off = _to_bool(_find_text(rel, "isOfficer")) if rel is not None else False
        title = (_find_text(rel, "officerTitle") or "") if rel is not None else ""
        if not title:
            if is_dir:
                title = "Director"
            elif rel is not None and _to_bool(_find_text(rel, "isTenPercentOwner")):
                title = "10% Owner"
            else:
                title = "Other"
        doc["owners"].append({
            "cik": (_find_text(ro, "reportingOwnerId/rptOwnerCik") or "").lstrip("0"),
            "name": _find_text(ro, "reportingOwnerId/rptOwnerName") or "",
            "title": title,
            "dir": int(is_dir),
            "off": int(is_off),
        })
    for tx in root.findall("nonDerivativeTable/nonDerivativeTransaction"):
        code = _find_text(tx, "transactionCoding/transactionCode")
        if code not in ("P", "S"):
            continue
        shares = _to_float(_find_text(tx, "transactionAmounts/transactionShares"))
        price = _to_float(_find_text(tx, "transactionAmounts/transactionPricePerShare"))
        doc["transactions"].append({
            "code": code,
            "date": _find_text(tx, "transactionDate") or "",
            "shares": shares,
            "price": price,
        })
    return doc


def build_day_events(filed_date, parsed, raw_filings, parse_failed, complete):
    """單日解析結果 → 事件檔 dict（data/events/form4_{date}.json 的內容）。

    buys 逐筆保留（含 owners——集群偵測/評分需要）；sells 按 issuer 聚合成總額
    （否決關卡只需要「同 issuer 同窗賣出總額」，逐筆存徒增體積）。純函式。
    """
    buys, sells_agg = [], {}
    for acc, doc in parsed:
        for tx in doc["transactions"]:
            value = (tx["shares"] or 0.0) * (tx["price"] or 0.0)
            if tx["code"] == "P":
                if not tx["shares"] or tx["price"] is None:
                    continue  # 缺股數/價格（footnote 型申報）無法計值，略過
                buys.append({
                    "acc": acc,
                    "filed": filed_date,
                    "date": tx["date"] or filed_date,
                    "cik": doc["issuer_cik"],
                    "ticker": doc["ticker"],
                    "company": doc["company"],
                    "owners": doc["owners"],
                    "shares": tx["shares"],
                    "price": tx["price"],
                    "usd": round(value, 2),
                    "p10b51": doc["ten_b5_1"],
                })
            else:  # S
                key = doc["issuer_cik"] or doc["ticker"]
                agg = sells_agg.setdefault(key, {
                    "cik": doc["issuer_cik"], "ticker": doc["ticker"],
                    "company": doc["company"], "usd": 0.0, "n_tx": 0})
                agg["usd"] = round(agg["usd"] + value, 2)
                agg["n_tx"] += 1
    return {
        "date": filed_date,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "complete": complete,
        "raw_filings": raw_filings,
        "parse_failed": parse_failed,
        "buys": buys,
        "sells": list(sells_agg.values()),
    }


# ---------------------------------------------------------------------------
# 抓取流程
# ---------------------------------------------------------------------------

def index_is_complete(d, now_utc):
    """某日的 daily index 是否已「日結」（見 config.INDEX_COMPLETE_*）。"""
    boundary = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(
        days=1, hours=config.INDEX_COMPLETE_UTC_HOUR,
        minutes=config.INDEX_COMPLETE_UTC_MINUTE)
    return now_utc >= boundary


def fetch_day(d, meta, max_filings, get_fn=None):
    """抓單日索引＋逐筆 filing，回傳事件檔 dict；索引 404（假日）回 None。

    get_fn 可注入（測試用）。單筆 filing 失敗只計數，不中斷整日。
    """
    get_fn = get_fn or http_get_text
    date_str = d.strftime("%Y-%m-%d")
    idx_text, status, ok = get_fn(daily_index_url(d), f"daily-index {date_str}", meta)
    if not ok:
        if status == 404:
            meta.note(f"{date_str} 索引 404（週末/假日），跳過")
            return None
        meta.error(f"{date_str} 索引抓取失敗（status={status}）")
        return None
    rows = parse_daily_index(idx_text)
    if len(rows) > max_filings:
        meta.error(f"{date_str} Form 4 共 {len(rows)} 筆 > 上限 {max_filings}，截斷")
        rows = rows[:max_filings]
    print(f"[fetch] {date_str}: {len(rows)} Form 4 filings")
    parsed, parse_failed = [], 0
    for i, row in enumerate(rows, 1):
        url = config.EDGAR_ARCHIVES_BASE + row["path"]
        acc = row["path"].rsplit("/", 1)[-1].replace(".txt", "")
        text, _, f_ok = get_fn(url, f"filing {acc}", meta, record_ok=False)
        if not f_ok:
            parse_failed += 1
            continue
        xml_text = extract_ownership_xml(text)
        doc = parse_form4_xml(xml_text) if xml_text else None
        if doc is None:
            parse_failed += 1
            continue
        parsed.append((acc, doc))
        if i % 200 == 0:
            print(f"[fetch] {date_str}: {i}/{len(rows)}")
    complete = index_is_complete(d, datetime.now(timezone.utc))
    return build_day_events(date_str, parsed, len(rows), parse_failed, complete)


def prune_event_files(events_dir, today, meta):
    """刪除超過 config.EVENT_RETENTION_DAYS 的事件檔（控 repo 體積）。"""
    cutoff = today - timedelta(days=config.EVENT_RETENTION_DAYS)
    for f in sorted(Path(events_dir).glob("form4_*.json")):
        try:
            d = datetime.strptime(f.stem.replace("form4_", ""), "%Y-%m-%d").date()
        except ValueError:
            continue
        if d < cutoff:
            f.unlink()
            meta.note(f"事件檔過期刪除：{f.name}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="EDGAR Form 4 daily fetcher (read-only)")
    parser.add_argument("--days", type=int, default=config.INDEX_LOOKBACK_DAYS,
                        help="往回掃的日曆日數（預設 %(default)s）")
    parser.add_argument("--max-filings", type=int, default=config.MAX_FILINGS_PER_DAY)
    parser.add_argument("--force", action="store_true",
                        help="已存在且 complete 的日檔也重抓")
    args = parser.parse_args(argv)

    started = time.time()
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    data_dir = BASE_DIR / "data"
    events_dir = data_dir / "events"
    meta = Meta()

    summary = {"days_scanned": 0, "days_fetched": 0, "days_skipped_cached": 0,
               "raw_filings": 0, "parse_failed": 0}
    try:
        for back in range(args.days):
            d = today - timedelta(days=back)
            if d.weekday() >= 5:
                continue  # 週六日無索引，省請求
            summary["days_scanned"] += 1
            out_path = events_dir / f"form4_{d.strftime('%Y-%m-%d')}.json"
            if out_path.exists() and not args.force:
                try:
                    cached = json.loads(out_path.read_text(encoding="utf-8"))
                except Exception:
                    cached = {}
                if cached.get("complete"):
                    summary["days_skipped_cached"] += 1
                    continue  # 已日結的存檔不重抓（每日增量核心）
            day = fetch_day(d, meta, args.max_filings)
            if day is None:
                continue
            write_json(out_path, day)
            summary["days_fetched"] += 1
            summary["raw_filings"] += day["raw_filings"]
            summary["parse_failed"] += day["parse_failed"]
        prune_event_files(events_dir, today, meta)
    except Exception as exc:  # 永不整體 crash：記進 meta，照樣落地
        meta.error(f"fetch 主流程例外：{type(exc).__name__}: {exc}")

    payload = {
        "ran_at": now_utc.isoformat(),
        **summary,
        "requests_ok": meta.requests_ok,
        "requests_failed": meta.requests_failed,
        "elapsed_sec": round(time.time() - started, 1),
        "endpoint_health": meta.endpoint_health,
        "errors": meta.errors,
    }
    try:
        update_meta(data_dir, "fetch", payload)
    except Exception as exc:
        print(f"[fetch] meta 寫入失敗：{exc}", file=sys.stderr)

    print("META " + json.dumps({k: payload[k] for k in
                                ("days_scanned", "days_fetched", "raw_filings",
                                 "requests_ok", "requests_failed", "elapsed_sec")},
                               ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
