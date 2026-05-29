#!/usr/bin/env python3
"""
fetch_taiwan.py — Fetch Taiwan market indicators for KIWI Dashboard.

Fetches daily:
  • 外資台指期貨淨多空口數  (TAIFEX 三大法人未平倉)
  • 融資餘額              (TWSE 全市場融資餘額合計)

Writes docs/taiwan_data.json with rolling 90-day history.

Run from projects/avi-v5/:
    python scripts/fetch_taiwan.py
"""

import json
import logging
import os
import re
import time
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
_REPO_ROOT = os.path.abspath(os.path.join(_PROJECT_DIR, "..", ".."))
TAIWAN_DATA_PATH = os.path.join(_REPO_ROOT, "docs", "taiwan_data.json")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── TAIFEX: 外資期貨淨多空 ──────────────────────────────────────────────────────

def fetch_taifex_net(target: date) -> int | None:
    """Fetch 外資及陸資 net TAIEX futures open interest (all contract types summed)."""
    date_str = target.strftime("%Y/%m/%d")
    url = "https://www.taifex.com.tw/cht/3/totalTableDate"
    try:
        resp = requests.post(
            url,
            data={"queryDate": date_str},
            headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded",
                     "Referer": url},
            timeout=25,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        net_positions = []
        for td in soup.find_all("td"):
            if "外資及陸資" not in td.get_text(strip=True):
                continue
            cells = td.parent.find_all("td")
            nums = []
            for c in cells:
                raw = c.get_text(strip=True).replace(",", "").replace("\xa0", "")
                if re.fullmatch(r"-?\d+", raw):
                    nums.append(int(raw))
            # Row format: [long_qty, long_notional, short_qty, short_notional, net_qty, net_notional]
            if len(nums) >= 5:
                net_positions.append(nums[4])  # 多空淨額口數

        if not net_positions:
            log.warning(f"TAIFEX: no 外資 rows found for {date_str}")
            return None

        total = sum(net_positions)
        log.info(f"TAIFEX 外資期貨淨多空: {total:+,} 口 ({date_str}, {len(net_positions)} contract types)")
        return total

    except Exception as e:
        log.warning(f"TAIFEX fetch failed {date_str}: {e}")
        return None


# ── TWSE: 融資餘額 ─────────────────────────────────────────────────────────────

def fetch_twse_margin(target: date) -> int | None:
    """Fetch total market margin balance (融資餘額合計) in thousand TWD."""
    date_str = target.strftime("%Y%m%d")
    urls = [
        f"https://www.twse.com.tw/rwd/zh/marginShortSelling/MI_MARGN?date={date_str}&selectType=MS&response=json",
        f"https://www.twse.com.tw/fund/MI_MARGN?date={date_str}&selectType=MS&response=json",
        f"https://www.twse.com.tw/exchangeReport/MI_MARGN?date={date_str}&selectType=MS&response=json",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code != 200:
                continue
            payload = resp.json()
            if payload.get("stat") not in ("OK", "ok"):
                continue
            rows = payload.get("data", [])
            if not rows:
                continue
            # Last row is 合計; find largest numeric field
            total_row = rows[-1]
            candidates = []
            for col in total_row:
                raw = str(col).replace(",", "")
                try:
                    v = int(raw)
                    if v > 100_000:
                        candidates.append(v)
                except ValueError:
                    pass
            if candidates:
                total = max(candidates)
                log.info(f"TWSE 融資餘額: {total:,} 千元 ({date_str})")
                return total
        except Exception as e:
            log.warning(f"TWSE margin fetch failed ({url[:60]}...): {e}")
    log.warning(f"All TWSE attempts failed for {date_str}")
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


def compute_signals(dates, futures, margin) -> dict:
    vf = [(d, v) for d, v in zip(dates, futures) if v is not None]
    vm = [(d, v) for d, v in zip(dates, margin) if v is not None]

    f_latest = vf[-1][1] if vf else 0
    m_latest = vm[-1][1] if vm else 0

    f_signal = "BULLISH" if f_latest > 10000 else ("BEARISH" if f_latest < -10000 else "NEUTRAL")

    m_vals = [v for _, v in vm]
    m_pct = int(sum(1 for v in m_vals if v < m_latest) / len(m_vals) * 100) if len(m_vals) > 10 else 50
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
    existing_dates = set(existing.get("dates", []))

    # Rebuild record map from existing data
    records: dict = {}
    for i, d in enumerate(existing.get("dates", [])):
        records[d] = {
            "futures_net": existing["futures_net"][i],
            "margin_balance": existing["margin_balance"][i],
        }

    # Find missing dates (rolling 90-day window)
    all_days = trading_days(today - timedelta(days=130), today)
    missing = [d for d in all_days if d.strftime("%Y-%m-%d") not in existing_dates]
    log.info(f"Missing dates: {len(missing)}, will fetch last 10")

    for d in missing[-10:]:
        dstr = d.strftime("%Y-%m-%d")
        futures = fetch_taifex_net(d)
        time.sleep(1)
        margin = fetch_twse_margin(d)
        if futures is not None or margin is not None:
            records[dstr] = {"futures_net": futures, "margin_balance": margin}
        time.sleep(1)

    # Sort and keep last 90 days
    sorted_dates = sorted(records.keys())[-90:]
    futures_series = [records[d]["futures_net"] for d in sorted_dates]
    margin_series = [records[d]["margin_balance"] for d in sorted_dates]

    signals = compute_signals(sorted_dates, futures_series, margin_series)

    output = {"updated": today.strftime("%Y-%m-%d"),
              "dates": sorted_dates,
              "futures_net": futures_series,
              "margin_balance": margin_series,
              **signals}

    save_data(output)
    log.info(
        f"=== Done: futures={signals['futures_latest']:+,}  "
        f"signal={signals['futures_signal']}  "
        f"margin_pct={signals['margin_pct']}%  "
        f"level={signals['margin_level']} ==="
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Unhandled error: {e}", exc_info=True)
        import sys; sys.exit(0)
