"""track_performance.py — 買訊後前瞻表現追蹤（1w/1m/3m/6m/12m）。

每日 CI 於漏斗之後執行：
  1. 把 candidates_latest.json 的新事件（ticker × first_filing_date 首見）登記進
     data/performance_tracking.json；
  2. 對既有事件逐一回填：訊號日起算滿 N 日曆日的第一個交易日，用當日收盤價
     計算報酬；價格不可得（下市/停牌/端點失敗）→ 維持 null，之後每日重試。

schema（與美股管線同契約，monitor 統一讀 positions/current_price/status/returns）：
{
  "updated_at": ISO8601,
  "windows_days": {"1w":7,"1m":30,"3m":91,"6m":182,"12m":365},
  "positions": [{
    "market":"TW","ticker","company","signal_date","first_filing_date",
    "entry_price_ref","score",
    "returns": {"1w": 0.031|null, ...},          # (fill價/entry)-1，滿窗才填
    "return_fill_dates": {"1w": "YYYY-MM-DD"},   # 實際回填用的交易日
    "current_price", "current_price_date", "status": "tracking"|"completed"
  }]
}
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import config

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
STATE_DIR = DATA_DIR / "state"


def load_json(path: Path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def empty_tracking() -> dict:
    return {
        "updated_at": None,
        "windows_days": dict(config.PERFORMANCE_WINDOWS_DAYS),
        "positions": [],
    }


def _entry_key(e: dict) -> str:
    return f"{e['ticker']}:{e['first_filing_date']}"


def register_new_entries(tracking: dict, candidates_doc: dict, signal_date: str) -> int:
    """candidates 首見事件（ticker×first_filing_date）→ 登記追蹤；回傳新增數。

    同一事件連續多日留在候選榜不會重複登記；同一票的新連買段（新 first_filing_date）
    視為新事件。entry_price_ref 取事件首次入榜當日的參考價。
    """
    known = {_entry_key(e) for e in tracking["positions"]}
    added = 0
    for c in candidates_doc.get("candidates", []):
        e = {
            "market": "TW",
            "ticker": c["ticker"],
            "company": c.get("company", ""),
            "signal_date": signal_date,
            "first_filing_date": c.get("first_filing_date") or signal_date,
            "entry_price_ref": c.get("entry_price_ref"),
            "score": c.get("score"),
            "returns": {w: None for w in config.PERFORMANCE_WINDOWS_DAYS},
            "return_fill_dates": {},
            "current_price": None,
            "current_price_date": None,
            "status": "tracking",
        }
        if _entry_key(e) in known:
            continue
        tracking["positions"].append(e)
        known.add(_entry_key(e))
        added += 1
    return added


def backfill(tracking: dict, close_map: dict, close_date: str | None) -> int:
    """用當日收盤回填滿窗的報酬；回傳本次填值數。純函數（就地修改 tracking）。"""
    if not close_date or not close_map:
        return 0
    today = datetime.strptime(close_date, "%Y-%m-%d")
    windows = tracking.get("windows_days", config.PERFORMANCE_WINDOWS_DAYS)
    filled = 0
    for e in tracking["positions"]:
        px = close_map.get(e["ticker"])
        if px is not None:
            e["current_price"] = px
            e["current_price_date"] = close_date
        entry_px = e.get("entry_price_ref")
        if entry_px in (None, 0) or px is None:
            continue  # 無進場參考價或今日無價 → 無法回填，維持 null 之後重試
        signal = datetime.strptime(e["signal_date"], "%Y-%m-%d")
        elapsed = (today - signal).days
        for w, ndays in windows.items():
            if e["returns"].get(w) is None and elapsed >= ndays:
                e["returns"][w] = round(px / entry_px - 1, 4)
                e["return_fill_dates"][w] = close_date
                filled += 1
        if all(v is not None for v in e["returns"].values()):
            e["status"] = "completed"
    return filled


def main() -> int:
    tracking = load_json(DATA_DIR / "performance_tracking.json", empty_tracking())
    tracking.setdefault("windows_days", dict(config.PERFORMANCE_WINDOWS_DAYS))
    tracking.setdefault("positions", [])

    candidates_doc = load_json(DATA_DIR / "candidates_latest.json", {"candidates": []})
    latest_close = load_json(STATE_DIR / "latest_close.json",
                             {"date": None, "close": {}})
    meta = load_json(DATA_DIR / "meta_latest.json", {})
    signal_date = meta.get("as_of_trading_day") or (
        (candidates_doc.get("generated_at") or "")[:10]) or None

    added = 0
    if signal_date:
        added = register_new_entries(tracking, candidates_doc, signal_date)
    filled = backfill(tracking, latest_close.get("close", {}), latest_close.get("date"))

    tracking["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_json(DATA_DIR / "performance_tracking.json", tracking)
    active = sum(1 for e in tracking["positions"] if e["status"] == "tracking")
    print(f"表現追蹤：新登記 {added} 事件、回填 {filled} 窗；"
          f"追蹤中 {active}／總計 {len(tracking['positions'])} 事件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
