#!/usr/bin/env python3
"""
fetch_taiwan.py — Fetch Taiwan market indicators for KIWI Dashboard.

Data sources:
  • 外資台指期貨淨多空口數  → FinMind API (TaiwanFuturesInstitutionalInvestors, TX)
  • 融資餘額              → TWSE exchangeReport/MI_MARGN (MS)

Writes docs/taiwan_data.json with rolling 90-day history.
Run from projects/avi-v5/: python scripts/fetch_taiwan.py
"""

import json
import logging
import os
import re
from datetime import date, timedelta

import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", ".."))
TAIWAN_DATA_PATH = os.path.join(_REPO_ROOT, "docs", "taiwan_data.json")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; KIWI-Dashboard/1.0)"}


# ── FinMind: 外資台指期未平倉淨多空 ────────────────────────────────────────────

def fetch_futures_net_range(start: date, end: date) -> dict[str, int]:
    """
    Fetch 外資 TX futures net open interest for a date range via FinMind.
    Returns {date_str: net_long_contracts}.
    TX = 臺股期貨 (TAIEX Large Futures); net = long - short 未平倉口數.
    """
    url = (
        "https://api.finmindtrade.com/api/v4/data"
        "?dataset=TaiwanFuturesInstitutionalInvestors"
        f"&data_id=TX&start_date={start}&end_date={end}"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") != 200:
            log.warning(f"FinMind TX: status={payload.get('status')} msg={payload.get('msg')}")
            return {}

        result = {}
        for rec in payload.get("data", []):
            if rec.get("institutional_investors") != "外資":
                continue
            d = rec["date"]
            net = rec["long_open_interest_balance_volume"] - rec["short_open_interest_balance_volume"]
            result[d] = net

        log.info(f"FinMind TX 外資: fetched {len(result)} dates ({start} → {end})")
        return result

    except Exception as e:
        log.warning(f"FinMind TX fetch failed: {e}")
        return {}


# ── TWSE: 融資餘額 ─────────────────────────────────────────────────────────────

def fetch_margin_balance(target: date) -> int | None:
    """
    Fetch total market 融資金額餘額 (仟元) from TWSE MI_MARGN.
    Returns an integer (千元), or None on failure.
    """
    date_str = target.strftime("%Y%m%d")
    url = (
        f"https://www.twse.com.tw/exchangeReport/MI_MARGN"
        f"?date={date_str}&selectType=MS&response=json"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("stat") not in ("OK", "ok"):
            return None

        for table in payload.get("tables", []):
            fields = table.get("fields", [])
            # Find index of 今日餘額
            try:
                bal_idx = fields.index("今日餘額")
            except ValueError:
                bal_idx = -1

            for row in table.get("data", []):
                item = row[0] if row else ""
                if "融資金額" in item:
                    raw = row[bal_idx].replace(",", "") if bal_idx >= 0 else row[-1].replace(",", "")
                    val = int(raw)
                    log.info(f"TWSE 融資金額餘額: {val:,} 千元 ({date_str})")
                    return val

        log.warning(f"TWSE: 融資金額 row not found for {date_str}")
        return None

    except Exception as e:
        log.warning(f"TWSE margin fetch failed ({date_str}): {e}")
        return None


# ── Data Store ──────────────────────────────────────────────────────────────────

def load_data() -> dict:
    if os.path.exists(TAIWAN_DATA_PATH):
        try:
            with open(TAIWAN_DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Could not load existing data: {e}")
    return {"updated": "", "dates": [], "futures_net": [], "margin_balance": []}


def save_data(d: dict) -> None:
    os.makedirs(os.path.dirname(TAIWAN_DATA_PATH), exist_ok=True)
    with open(TAIWAN_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    log.info(f"Saved {TAIWAN_DATA_PATH} ({len(d['dates'])} records)")


def trading_days(start: date, end: date) -> list[date]:
    days, cur = [], start
    while cur <= end:
        if cur.weekday() < 5:
            days.append(cur)
        cur += timedelta(days=1)
    return days


def compute_signals(dates: list, futures: list, margin: list) -> dict:
    vf = [(d, v) for d, v in zip(dates, futures) if v is not None]
    vm = [(d, v) for d, v in zip(dates, margin) if v is not None]

    f_latest = vf[-1][1] if vf else 0
    m_latest = vm[-1][1] if vm else 0

    f_signal = "BULLISH" if f_latest > 10000 else ("BEARISH" if f_latest < -10000 else "NEUTRAL")

    m_vals = [v for _, v in vm]
    m_pct = (int(sum(1 for v in m_vals if v < m_latest) / len(m_vals) * 100)
             if len(m_vals) > 10 else 50)
    m_level = "HIGH" if m_pct >= 85 else ("ELEVATED" if m_pct >= 65 else "NORMAL")

    return {
        "futures_latest": f_latest,
        "futures_signal": f_signal,
        "margin_latest": m_latest,
        "margin_pct": m_pct,
        "margin_level": m_level,
    }


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Taiwan Data Fetch Starting ===")
    today = date.today()
    existing = load_data()

    # Rebuild record map
    records: dict = {}
    for i, d in enumerate(existing.get("dates", [])):
        records[d] = {
            "futures_net": existing["futures_net"][i],
            "margin_balance": existing["margin_balance"][i],
        }

    # Determine missing dates in rolling 90-day window
    window_start = today - timedelta(days=130)
    all_days = trading_days(window_start, today)
    existing_dates = set(records.keys())
    missing = [d for d in all_days if d.strftime("%Y-%m-%d") not in existing_dates]
    log.info(f"Missing dates: {len(missing)}, fetching all at once via FinMind range query")

    # ── Futures: bulk range fetch via FinMind ──────────────────────────────────
    if missing:
        fetch_start = missing[0]
        fetch_end = missing[-1]
        futures_batch = fetch_futures_net_range(fetch_start, fetch_end)

        for d in missing:
            dstr = d.strftime("%Y-%m-%d")
            futures_val = futures_batch.get(dstr)  # None if non-trading day
            # Margin: fetch only if futures data was returned (confirms it's a trading day)
            margin_val = None
            if futures_val is not None:
                margin_val = fetch_margin_balance(d)

            if futures_val is not None or margin_val is not None:
                records[dstr] = {"futures_net": futures_val, "margin_balance": margin_val}

    # Sort and keep last 90 records
    sorted_dates = sorted(records.keys())[-90:]
    futures_series = [records[d]["futures_net"] for d in sorted_dates]
    margin_series = [records[d]["margin_balance"] for d in sorted_dates]

    signals = compute_signals(sorted_dates, futures_series, margin_series)
    output = {
        "updated": today.strftime("%Y-%m-%d"),
        "dates": sorted_dates,
        "futures_net": futures_series,
        "margin_balance": margin_series,
        **signals,
    }

    save_data(output)
    log.info(
        f"=== Done: {len(sorted_dates)} records, "
        f"futures={signals['futures_latest']:+,} ({signals['futures_signal']}), "
        f"margin={signals['margin_latest']:,} 千元 ({signals['margin_level']}) ==="
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Unhandled error: {e}", exc_info=True)
        import sys; sys.exit(0)
