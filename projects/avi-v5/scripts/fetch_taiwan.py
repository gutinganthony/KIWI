#!/usr/bin/env python3
"""
fetch_taiwan.py — Fetch Taiwan market indicators for KIWI Dashboard.

Data sources:
  • 外資台指期貨淨多空口數  → FinMind API (TaiwanFuturesInstitutionalInvestors, TX)
  • 融資餘額              → TWSE exchangeReport/MI_MARGN (MS)
  • 加權指數 TAIEX        → FinMind (TaiwanStockPrice, TAIEX)；備援 TWSE FMTQIK

融資餘額用「融資餘額 ÷ 加權指數」正規化：指數翻倍時融資自然跟著變大，
絕對金額跨年代不可比；比率上升才代表槓桿增速超過大盤（真正的過熱訊號）。

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


# ── TAIEX 加權指數 ─────────────────────────────────────────────────────────────

def fetch_taiex_range(start: date, end: date) -> dict[str, float]:
    """
    Fetch TAIEX daily closes for a date range.
    Primary: FinMind TaiwanStockPrice (data_id=TAIEX).
    Fallback: TWSE FMTQIK monthly tables (發行量加權股價指數).
    Returns {date_str: close}.
    """
    # ── Primary: FinMind ──
    url = (
        "https://api.finmindtrade.com/api/v4/data"
        "?dataset=TaiwanStockPrice"
        f"&data_id=TAIEX&start_date={start}&end_date={end}"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") == 200 and payload.get("data"):
            result = {rec["date"]: float(rec["close"]) for rec in payload["data"]}
            log.info(f"FinMind TAIEX: fetched {len(result)} dates ({start} → {end})")
            if result:
                return result
        else:
            log.warning(f"FinMind TAIEX: status={payload.get('status')} msg={payload.get('msg')}")
    except Exception as e:
        log.warning(f"FinMind TAIEX fetch failed: {e}")

    # ── Fallback: TWSE FMTQIK（每月一表，含每日發行量加權股價指數收盤）──
    result: dict[str, float] = {}
    cur = date(start.year, start.month, 1)
    while cur <= end:
        url = (
            f"https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK"
            f"?date={cur.strftime('%Y%m%d')}&response=json"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("stat") in ("OK", "ok"):
                fields = payload.get("fields", [])
                try:
                    idx_col = fields.index("發行量加權股價指數")
                except ValueError:
                    idx_col = 4
                for row in payload.get("data", []):
                    # 民國年格式 115/06/11 → 2026-06-11
                    m = re.match(r"(\d+)/(\d+)/(\d+)", row[0])
                    if not m:
                        continue
                    y = int(m.group(1)) + 1911
                    dstr = f"{y:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
                    result[dstr] = float(row[idx_col].replace(",", ""))
        except Exception as e:
            log.warning(f"TWSE FMTQIK fetch failed ({cur}): {e}")
        # next month
        cur = date(cur.year + (cur.month == 12), (cur.month % 12) + 1, 1)
    log.info(f"TWSE FMTQIK TAIEX fallback: fetched {len(result)} dates")
    return result


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


def compute_ratio_series(margin: list, taiex: list) -> list:
    """
    融資餘額 ÷ 加權指數，再以窗內第一個有效值為基期 100 的百分比序列。
    111 = 槓桿強度比 90 日前高 11%（融資增速超過大盤）。
    任一邊缺值時該點為 None。
    """
    raw = [
        (m / t) if (m is not None and t is not None and t > 0) else None
        for m, t in zip(margin, taiex)
    ]
    base = next((v for v in raw if v is not None), None)
    if base is None or base == 0:
        return [None] * len(raw)
    return [round(v / base * 100, 2) if v is not None else None for v in raw]


def compute_signals(dates: list, futures: list, margin: list, ratio_pct: list) -> dict:
    vf = [(d, v) for d, v in zip(dates, futures) if v is not None]
    vm = [(d, v) for d, v in zip(dates, margin) if v is not None]

    f_latest = vf[-1][1] if vf else 0
    m_latest = vm[-1][1] if vm else 0

    f_signal = "BULLISH" if f_latest > 10000 else ("BEARISH" if f_latest < -10000 else "NEUTRAL")

    # 過熱百分位：優先用「融資÷指數」正規化序列（消除大盤水位影響），
    # 沒有 TAIEX 數據時退回原始融資金額。
    r_vals = [v for v in ratio_pct if v is not None]
    if len(r_vals) > 10:
        r_latest = r_vals[-1]
        m_pct = int(sum(1 for v in r_vals if v < r_latest) / len(r_vals) * 100)
        pct_basis = "ratio"
    else:
        m_vals = [v for _, v in vm]
        m_pct = (int(sum(1 for v in m_vals if v < m_latest) / len(m_vals) * 100)
                 if len(m_vals) > 10 else 50)
        pct_basis = "raw"
    m_level = "HIGH" if m_pct >= 85 else ("ELEVATED" if m_pct >= 65 else "NORMAL")

    return {
        "futures_latest": f_latest,
        "futures_signal": f_signal,
        "margin_latest": m_latest,
        "margin_pct": m_pct,
        "margin_pct_basis": pct_basis,
        "margin_ratio_latest": (r_vals[-1] if r_vals else None),
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

    # ── TAIEX：每次整窗重抓（單一 range 請求，便宜），用於融資正規化 ──────────
    taiex_map: dict[str, float] = {}
    if sorted_dates:
        t_start = date.fromisoformat(sorted_dates[0])
        t_end = date.fromisoformat(sorted_dates[-1])
        taiex_map = fetch_taiex_range(t_start, t_end)
    taiex_series = [taiex_map.get(d) for d in sorted_dates]
    ratio_pct = compute_ratio_series(margin_series, taiex_series)

    signals = compute_signals(sorted_dates, futures_series, margin_series, ratio_pct)
    output = {
        "updated": today.strftime("%Y-%m-%d"),
        "dates": sorted_dates,
        "futures_net": futures_series,
        "margin_balance": margin_series,
        "taiex": taiex_series,
        "margin_ratio_pct": ratio_pct,
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
