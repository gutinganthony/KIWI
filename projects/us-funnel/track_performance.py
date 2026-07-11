#!/usr/bin/env python3
"""us-funnel 前瞻表現追蹤：候選買訊後 1週/1月/3月/6月/12月 報酬回填。

用法：
    python3 track_performance.py

行為：
1. 讀 data/candidates_latest.json 的新候選 → append 進 data/performance_tracking.json
   的 positions（去重：同 ticker 在 config.TRACK_DEDUP_DAYS=30 日內不重複開倉追蹤）。
2. 每個未完結 position 用 Stooq 免費日線 CSV 回填「已到期」窗口的報酬
   （窗口日曆日見 config.RETURN_WINDOWS；未到期一律留 null），並更新 current_price。
   報酬定義：窗口終點日（signal_date + N 日）當日或之後第一個交易日收盤 / entry_price_ref - 1。
3. 全部窗口回填完 → status 轉 "completed"，之後不再抓價。
4. meta（價格源健康、回填計數、錯誤）合併寫進 data/meta_latest.json 的 tracking 節。

價格源：Stooq CSV（免金鑰）https://stooq.com/q/d/l/?s={ticker}.us&i=d，
每請求 sleep config.STOOQ_SLEEP_BETWEEN=0.5s。刻意不用 yfinance（CI 限流前科，擇穩）。
價格抓不到＝該 position 本輪不動（報酬留 null 下輪重試），記 meta，不 crash。

輸出契約（monitor 網頁依 schema 讀取，鍵名不可改）：
data/performance_tracking.json =
    {"updated_at": ISO8601, "positions": [{"ticker","signal_date","entry_price_ref",
     "current_price","returns":{"1w","1m","3m","6m","12m"},"status"}]}

本腳本純唯讀分析：不含任何下單、券商 API、簽章、金鑰。
"""

import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import config
from fetch_edgar import Meta, http_get_text, update_meta, write_json

BASE_DIR = Path(__file__).resolve().parent

# position 的 status 值：tracking（回填中）/ completed（12m 窗口已回填，不再抓價）
STATUS_TRACKING = "tracking"
STATUS_COMPLETED = "completed"


# ---------------------------------------------------------------------------
# 價格源（Stooq；funnel.py 的流動性否決與 dip 評分也 import 這一段）
# ---------------------------------------------------------------------------

def stooq_symbol(ticker):
    """美股 ticker → Stooq symbol：小寫＋'.us'；class 股的 '.'/'/' 轉 '-'（BRK.B → brk-b.us）。"""
    return ticker.strip().lower().replace(".", "-").replace("/", "-") + ".us"


def parse_stooq_csv(text):
    """Stooq 日線 CSV → [(date_str, close, volume), ...]（升冪）；無效回 None。

    正常首行 'Date,Open,High,Low,Close,Volume'；查無代號時 Stooq 回 'No data' 或
    空 HTML——防禦性驗證首行與最少行數（config.PRICE_HISTORY_MIN_ROWS）。
    """
    if not text or not text.lstrip().startswith("Date,"):
        return None
    rows = []
    for line in text.strip().splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 6:
            continue
        try:
            close = float(parts[4])
        except ValueError:
            continue
        try:
            volume = float(parts[5])
        except ValueError:
            volume = 0.0
        rows.append((parts[0], close, volume))
    if len(rows) < config.PRICE_HISTORY_MIN_ROWS:
        return None
    rows.sort(key=lambda r: r[0])
    return rows


def fetch_price_history(ticker, meta, get_fn=None):
    """抓單一 ticker 的 Stooq 日線 → rows 或 None（失敗記 meta，不 raise）。"""
    get_fn = get_fn or http_get_text
    url = config.STOOQ_DAILY_URL.format(symbol=stooq_symbol(ticker))
    text, _, ok = get_fn(url, f"stooq {ticker}", meta, record_ok=False,
                         sleep=config.STOOQ_SLEEP_BETWEEN)
    if not ok:
        return None
    rows = parse_stooq_csv(text)
    if rows is None:
        meta.error(f"stooq {ticker}: 回應非有效 CSV（No data？）")
    return rows


def make_price_fetcher(meta, get_fn=None):
    """回傳帶快取的 price_fn(ticker) -> rows|None（同 ticker 每輪只抓一次）。"""
    cache = {}

    def price_fn(ticker):
        if ticker not in cache:
            cache[ticker] = fetch_price_history(ticker, meta, get_fn=get_fn)
        return cache[ticker]

    return price_fn


# ---------------------------------------------------------------------------
# 回填邏輯（純函式，離線測試覆蓋）
# ---------------------------------------------------------------------------

def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def new_position(candidate):
    """candidate（candidates_latest.json 條目）→ 新 position（契約 schema，鍵名固定）。"""
    return {
        "ticker": candidate["ticker"],
        "signal_date": candidate["first_filing_date"],
        "entry_price_ref": candidate["entry_price_ref"],
        "current_price": 0,
        "returns": {key: None for key in config.RETURN_WINDOWS},
        "status": STATUS_TRACKING,
    }


def should_add(positions, ticker, signal_date, dedup_days=None):
    """去重：同 ticker 在 dedup_days（預設 30）日內已有 position → 不重複開倉。"""
    dedup_days = config.TRACK_DEDUP_DAYS if dedup_days is None else dedup_days
    sig = _parse_date(signal_date)
    if sig is None:
        return False
    for pos in positions:
        if pos.get("ticker") != ticker:
            continue
        existing = _parse_date(pos.get("signal_date"))
        if existing is not None and abs((sig - existing).days) < dedup_days:
            return False
    return True


def update_position(pos, rows, today):
    """用價格序列回填單一 position 的已到期窗口；回傳更新後 pos（就地修改）。

    rows = [(date_str, close, volume), ...] 升冪；today = datetime.date。
    規則：
    - 窗口終點 = signal_date + N 日曆日；終點 > today → 未到期，留 null。
    - 已到期：取第一個 date >= 終點 的交易日收盤計報酬；序列尚無該日
      （假日/數據延遲）→ 本輪留 null，下輪重試。
    - current_price = 序列最後收盤。
    - 五個窗口全部回填 → status=completed。
    entry_price_ref <= 0 或 signal_date 壞值 → 不動（防除零/壞資料），留給人工檢查。
    """
    entry = pos.get("entry_price_ref") or 0
    sig = _parse_date(pos.get("signal_date"))
    if not rows or entry <= 0 or sig is None:
        return pos
    pos["current_price"] = rows[-1][1]
    for key, days in config.RETURN_WINDOWS.items():
        if pos["returns"].get(key) is not None:
            continue
        end = sig + timedelta(days=days)
        if end > today:
            continue  # 未到期
        row = next((r for r in rows if _parse_date(r[0]) is not None
                    and _parse_date(r[0]) >= end), None)
        if row is None:
            continue  # 已到期但序列尚無交易日（假日/延遲），下輪重試
        pos["returns"][key] = round(row[1] / entry - 1, 4)
    if all(pos["returns"].get(k) is not None for k in config.RETURN_WINDOWS):
        pos["status"] = STATUS_COMPLETED
    return pos


def run_tracking(candidates, tracking, today, price_fn):
    """核心流程（純函式；network 全在 price_fn 內）：append 新倉＋回填舊倉。

    回傳 (新 tracking dict, stats dict)。
    """
    positions = list(tracking.get("positions") or [])
    stats = {"positions_new": 0, "positions_updated": 0, "price_failed": 0}
    for cand in candidates.get("candidates") or []:
        ticker = cand.get("ticker") or ""
        if not ticker or not cand.get("first_filing_date"):
            continue
        if should_add(positions, ticker, cand["first_filing_date"]):
            positions.append(new_position(cand))
            stats["positions_new"] += 1
    for pos in positions:
        if pos.get("status") == STATUS_COMPLETED:
            continue
        rows = price_fn(pos.get("ticker") or "")
        if rows is None:
            stats["price_failed"] += 1
            continue
        update_position(pos, rows, today)
        stats["positions_updated"] += 1
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "positions": positions,
    }, stats


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def _load_json(path, fallback):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return fallback


def main(argv=None):
    started = time.time()
    data_dir = BASE_DIR / "data"
    meta = Meta()
    today = datetime.now(timezone.utc).date()

    candidates = _load_json(data_dir / "candidates_latest.json", {"candidates": []})
    tracking = _load_json(data_dir / "performance_tracking.json", {"positions": []})
    stats = {"positions_new": 0, "positions_updated": 0, "price_failed": 0}
    try:
        tracking, stats = run_tracking(candidates, tracking, today,
                                       make_price_fetcher(meta))
        write_json(data_dir / "performance_tracking.json", tracking)
    except Exception as exc:  # 永不整體 crash
        meta.error(f"tracking 主流程例外：{type(exc).__name__}: {exc}")

    payload = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "positions_total": len(tracking.get("positions") or []),
        **stats,
        "requests_ok": meta.requests_ok,
        "requests_failed": meta.requests_failed,
        "elapsed_sec": round(time.time() - started, 1),
        "endpoint_health": meta.endpoint_health,
        "errors": meta.errors,
    }
    try:
        update_meta(data_dir, "tracking", payload)
    except Exception as exc:
        print(f"[track] meta 寫入失敗：{exc}", file=sys.stderr)

    print("META " + json.dumps({k: payload[k] for k in
                                ("positions_total", "positions_new",
                                 "positions_updated", "price_failed", "elapsed_sec")},
                               ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
