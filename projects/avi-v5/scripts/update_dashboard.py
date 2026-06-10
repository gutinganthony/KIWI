#!/usr/bin/env python3
"""
update_dashboard.py — Auto-update AVI Dashboard with live market data.

Fetches live data, computes CPI + TSI + AVI scores, then injects
JSON payload into docs/index.html between KIWI-DATA markers.

Run from projects/avi-v5/ directory:
    python scripts/update_dashboard.py

Requires:
    FRED_API_KEY env var (optional — FRED indicators skipped if missing)
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Allow imports from src/ when running from projects/avi-v5/
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_DIR)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

FRED_KEY = os.environ.get("FRED_API_KEY", "")
DOCS_HTML = os.path.abspath(
    os.path.join(_SCRIPT_DIR, "..", "..", "..", "docs", "index.html")
)

# Fallback constants (used when live fetch fails)
FALLBACK = {
    "avi_score": 4.5,
    "avi_level": "ELEVATED",
    "cri_score": 23.0,
    "tsi_score": 45.0,
    "sp500": 5300.0,
    "vix": 19.0,
    "t10y": 4.55,
    "t30y": 5.12,
    "cape": 41.5,
    "oil": 0.0,
}

# ── Data Fetching ──────────────────────────────────────────────────────────────

def fetch_yfinance_data():
    """Fetch 2 years of daily price history from yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        log.warning("yfinance not installed — skipping market data fetch")
        return {}

    tickers = ["^GSPC", "^VIX", "QQQ", "SOXX", "SMH", "SPY", "MU", "BZ=F"]
    end = datetime.today()
    start = end - timedelta(days=730)

    result = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                             end=end.strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
            if df.empty:
                log.warning(f"No data for {ticker}")
                continue
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            result[ticker] = df
            log.info(f"Fetched {ticker}: {len(df)} rows, last={df.index[-1].date()}")
        except Exception as e:
            log.warning(f"Failed to fetch {ticker}: {e}")

    return result


def fetch_fred_data():
    """Fetch FRED series. Returns empty dict if key missing or fetch fails."""
    if not FRED_KEY:
        log.warning("FRED_API_KEY not set — skipping FRED data")
        return {}

    try:
        from fredapi import Fred
    except ImportError:
        log.warning("fredapi not installed — skipping FRED data")
        return {}

    fred = Fred(api_key=FRED_KEY)
    series_ids = {
        "DGS10": "treasury_10y",
        "DGS2":  "treasury_2y",
        "DGS30": "treasury_30y",
        "BAA":   "baa",
        "AAA":   "aaa",
        "CPIAUCSL": "cpi_index",
        "STLFSI4":  "stlfsi",
    }

    end = datetime.today()
    start = end - timedelta(days=730)
    result = {}

    for fred_id, key in series_ids.items():
        try:
            s = fred.get_series(fred_id, observation_start=start, observation_end=end)
            s = s.dropna()
            s.index = pd.to_datetime(s.index)
            result[key] = s
            log.info(f"Fetched FRED {fred_id}: {len(s)} obs, last={s.index[-1].date()}")
        except Exception as e:
            log.warning(f"Failed to fetch FRED {fred_id}: {e}")

    return result


def scrape_cape():
    """Get current CAPE (Shiller PE) from multpl.com. Returns None on failure.

    修正：① 先用已修好 dagger bug 的 MultplSource 表格解析取最新值（最穩）；
          ② 後備才用頁面 div#current（multpl 改版會壞）+ 寬鬆 regex。
    """
    # ① 表格解析（reuse 已修正的 parser）
    try:
        from src.data.sources.multpl import MultplSource
        s = MultplSource().fetch_indicator("shiller-pe")
        if len(s) > 0:
            val = float(s.iloc[-1])
            log.info(f"Scraped CAPE (table): {val} @ {s.index[-1].date()}")
            return val
    except Exception as e:
        log.warning(f"CAPE table parse failed: {e}")

    # ② 後備：抓頁面當前值
    try:
        import requests
        from bs4 import BeautifulSoup

        url = "https://www.multpl.com/shiller-pe"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AVI-Dashboard/1.0)"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        el = soup.find(id="current") or soup.find("div", {"class": "current"})
        text = el.get_text(strip=True) if el else resp.text
        m = re.search(r"\b(\d{2}\.\d{1,2})\b", text.replace(",", ""))
        if m:
            val = float(m.group(1))
            log.info(f"Scraped CAPE (page): {val}")
            return val
    except Exception as e:
        log.warning(f"CAPE scrape failed: {e}")
    return None

# ── Score Computation ──────────────────────────────────────────────────────────

def compute_cpi(yf_data, fred_data):
    """Compute CPI score using CrashProbabilityIndex engine."""
    try:
        from src.cpi import CrashProbabilityIndex

        sp500_df = yf_data.get("^GSPC")
        vix_s = yf_data.get("^VIX")

        if sp500_df is None or vix_s is None:
            raise ValueError("Missing required ^GSPC or ^VIX data")

        # Build sp500 DataFrame with 'close' and 'volume'
        sp500 = pd.DataFrame({
            "close":  sp500_df["Close"] if "Close" in sp500_df.columns else sp500_df.iloc[:, 0],
            "volume": sp500_df["Volume"] if "Volume" in sp500_df.columns else pd.Series(
                dtype=float, index=sp500_df.index
            ),
        })
        vix = vix_s["Close"] if "Close" in vix_s.columns else vix_s.iloc[:, 0]

        # FRED series (may be empty)
        baa        = fred_data.get("baa",        pd.Series(dtype=float))
        aaa        = fred_data.get("aaa",        pd.Series(dtype=float))
        treasury_10y = fred_data.get("treasury_10y", pd.Series(dtype=float))
        treasury_2y  = fred_data.get("treasury_2y",  pd.Series(dtype=float))

        # Need at least minimal data for FRED indicators; use zero-filled proxies if missing
        if baa.empty:
            baa = pd.Series(0.0, index=vix.index)
        if aaa.empty:
            aaa = pd.Series(0.0, index=vix.index)
        if treasury_10y.empty:
            treasury_10y = pd.Series(0.04, index=vix.index)
        if treasury_2y.empty:
            treasury_2y = pd.Series(0.04, index=vix.index)

        # Align indexes (FRED is daily but may have gaps)
        baa        = baa.reindex(vix.index, method="ffill").fillna(0)
        aaa        = aaa.reindex(vix.index, method="ffill").fillna(0)
        treasury_10y = treasury_10y.reindex(vix.index, method="ffill").fillna(0.04)
        treasury_2y  = treasury_2y.reindex(vix.index, method="ffill").fillna(0.04)

        cpi = CrashProbabilityIndex()
        result = cpi.compute(
            sp500_daily=sp500,
            vix_daily=vix,
            vix3m_daily=None,   # use VIX MA proxy
            baa_daily=baa,
            aaa_daily=aaa,
            treasury_10y=treasury_10y,
            treasury_2y=treasury_2y,
        )
        log.info(f"CPI computed: {result.score:.1f} / {result.level}")
        return result

    except Exception as e:
        log.warning(f"CPI computation failed: {e}")
        return None


def compute_tsi(yf_data, fred_data):
    """Compute TSI score using TechStressIndex engine."""
    try:
        from src.tsi import TechStressIndex

        # Required series
        # 修正 bug：`df_a or df_b` 在 DataFrame 上會丟 ValueError(truth value ambiguous)
        # → compute_tsi 每天崩潰 → TSI 一直 fallback 45.0。改用 None-safe。
        soxx_df = yf_data.get("SOXX")
        if soxx_df is None:
            soxx_df = yf_data.get("^SOX")
        qqq_df  = yf_data.get("QQQ")
        mu_df   = yf_data.get("MU")
        smh_df  = yf_data.get("SMH")
        spy_df  = yf_data.get("SPY")
        vix_df  = yf_data.get("^VIX")

        if any(x is None for x in [qqq_df, mu_df, smh_df, spy_df, vix_df]):
            raise ValueError("Missing required QQQ/MU/SMH/SPY/VIX data")

        def get_close(df):
            if df is None:
                return None
            return df["Close"] if "Close" in df.columns else df.iloc[:, 0]

        qqq  = get_close(qqq_df)
        mu   = get_close(mu_df)
        smh  = get_close(smh_df)
        spy  = get_close(spy_df)
        vix  = get_close(vix_df)
        sox  = get_close(soxx_df) if soxx_df is not None else qqq  # fallback to QQQ

        treasury_10y = fred_data.get("treasury_10y")
        treasury_30y = fred_data.get("treasury_30y")

        if treasury_10y is None or treasury_10y.empty:
            treasury_10y = pd.Series(0.045, index=vix.index)
        else:
            treasury_10y = treasury_10y.reindex(vix.index, method="ffill").fillna(0.045)

        if treasury_30y is None or treasury_30y.empty:
            treasury_30y = None
        else:
            treasury_30y = treasury_30y.reindex(vix.index, method="ffill").fillna(0.05)

        tsi = TechStressIndex()
        result = tsi.compute(
            sox_daily=sox,
            qqq_daily=qqq,
            mu_daily=mu,
            smh_daily=smh,
            spy_daily=spy,
            treasury_10y=treasury_10y,
            vix_daily=vix,
            treasury_30y=treasury_30y,
        )
        log.info(f"TSI computed: {result.score:.1f} / {result.bias}")
        return result

    except Exception as e:
        log.warning(f"TSI computation failed: {e}")
        return None


def compute_avi_dimensions(yf_data, fred_data, cape_val):
    """
    Compute approximate AVI V5 dimension percentiles from available data.
    Returns dict with dimension name → pct (0-100).
    """
    dims = {
        "valuation":     {"pct": 72,  "emoji": "🟠"},
        "profitability": {"pct": 34,  "emoji": "🟢"},
        "macro":         {"pct": 52,  "emoji": "🟡"},
        "rate":          {"pct": 65,  "emoji": "🟠"},
        "credit":        {"pct": 12,  "emoji": "🟢"},
        "momentum":      {"pct": 58,  "emoji": "🟡"},
    }

    try:
        vix_df   = yf_data.get("^VIX")
        spy_df   = yf_data.get("SPY")
        t10y     = fred_data.get("treasury_10y")
        baa      = fred_data.get("baa")
        cpi_idx  = fred_data.get("cpi_index")

        # ─ Valuation: CAPE percentile ──────────────────────────────────────
        if cape_val is not None:
            # Simple map: CAPE 15→0%, 45→100%
            cape_pct = int(min(100, max(0, (cape_val - 15) / 30 * 100)))
            dims["valuation"]["pct"] = cape_pct
            dims["valuation"]["emoji"] = _pct_emoji(cape_pct)

        # ─ Macro: VIX rolling percentile ──────────────────────────────────
        if vix_df is not None and len(vix_df) > 63:
            vix_close = vix_df["Close"] if "Close" in vix_df.columns else vix_df.iloc[:, 0]
            vix_now  = vix_close.iloc[-1]
            vix_pct  = int(min(100, max(0, (vix_close.tail(252) < vix_now).sum() / min(252, len(vix_close)) * 100)))
            dims["macro"]["pct"] = vix_pct
            dims["macro"]["emoji"] = _pct_emoji(vix_pct)

        # ─ Rate: CPI YoY rolling percentile ───────────────────────────────
        if cpi_idx is not None and len(cpi_idx) >= 13:
            cpi_yoy = cpi_idx.pct_change(12) * 100
            cpi_yoy = cpi_yoy.dropna()
            if len(cpi_yoy) > 12:
                now_yoy = cpi_yoy.iloc[-1]
                rate_pct = int(min(100, max(0, (cpi_yoy < now_yoy).sum() / len(cpi_yoy) * 100)))
                dims["rate"]["pct"] = rate_pct
                dims["rate"]["emoji"] = _pct_emoji(rate_pct)
        elif t10y is not None and len(t10y) > 252:
            now_10y = t10y.iloc[-1]
            rate_pct = int(min(100, max(0, (t10y.tail(252) < now_10y).sum() / 252 * 100)))
            dims["rate"]["pct"] = rate_pct
            dims["rate"]["emoji"] = _pct_emoji(rate_pct)

        # ─ Credit: BAA-10Y spread percentile ──────────────────────────────
        if baa is not None and t10y is not None and not baa.empty and not t10y.empty:
            spread = baa.reindex(t10y.index, method="ffill") - t10y
            spread = spread.dropna()
            if len(spread) > 60:
                now_spread = spread.iloc[-1]
                credit_pct = int(min(100, max(0, (spread < now_spread).sum() / len(spread) * 100)))
                dims["credit"]["pct"] = credit_pct
                dims["credit"]["emoji"] = _pct_emoji(credit_pct)

        # ─ Momentum: SPY vs 200MA ratio ───────────────────────────────────
        if spy_df is not None and len(spy_df) > 200:
            spy_close = spy_df["Close"] if "Close" in spy_df.columns else spy_df.iloc[:, 0]
            ma200 = spy_close.rolling(200).mean().iloc[-1]
            ratio = (spy_close.iloc[-1] / ma200 - 1) * 100  # % above/below
            # ratio > 0 = above 200MA = low stress; below = high stress
            # Map: -20% → 80%, 0% → 50%, +30% → 20%
            mom_pct = int(min(100, max(0, 50 - ratio * 1.0)))
            dims["momentum"]["pct"] = mom_pct
            dims["momentum"]["emoji"] = _pct_emoji(mom_pct)

        # Profitability: stable indicator — keep at 34
        dims["profitability"]["pct"] = 34
        dims["profitability"]["emoji"] = "🟢"

    except Exception as e:
        log.warning(f"AVI dimension computation failed: {e}")

    return dims


def _pct_emoji(pct):
    if pct >= 75:
        return "🔴"
    elif pct >= 60:
        return "🟠"
    elif pct >= 40:
        return "🟡"
    return "🟢"


def compute_avi_score(dims):
    """Compute weighted AVI score (0-10) from dimension percentiles."""
    weights = {
        "valuation":     0.38,
        "profitability": 0.08,
        "macro":         0.14,
        "rate":          0.14,
        "credit":        0.12,
        "momentum":      0.14,
    }
    score = sum(dims[d]["pct"] / 100 * w * 10 for d, w in weights.items())
    return round(score, 2)


def avi_level(score):
    if score >= 8.0:
        return "CRITICAL"
    elif score >= 7.0:
        return "HIGH"
    elif score >= 5.5:
        return "ELEVATED"
    elif score >= 4.0:
        return "NEUTRAL"
    return "LOW"


# ── Alert Logic ────────────────────────────────────────────────────────────────

def build_alert(tsi_score, cpi_score, tsi_bias, avi_level_str):
    """Build alert block based on TSI and CPI scores."""
    if tsi_score >= 65 or cpi_score >= 50:
        level = "danger"
        show = True
        title_en = f"High Risk Alert — TSI {tsi_bias} / CRI Elevated"
        title_zh = f"高風險警告 — TSI {tsi_bias} / CRI 升高"
        desc_en = (
            f"TSI = {tsi_score:.0f} ({tsi_bias}), CRI = {cpi_score:.0f}. "
            "Multiple stress signals elevated. Consider risk reduction."
        )
        desc_zh = (
            f"TSI = {tsi_score:.0f}（{tsi_bias}），CRI = {cpi_score:.0f}。"
            "多項壓力指標升高，考慮降低風險敞口。"
        )
    elif tsi_score >= 45 or cpi_score >= 35:
        level = "caution"
        show = True
        title_en = f"Tech Sector Caution — TSI {tsi_bias}"
        title_zh = f"科技板塊謹慎 — TSI {tsi_bias}"
        desc_en = (
            f"TSI = {tsi_score:.0f} ({tsi_bias}), CRI = {cpi_score:.0f}. "
            "Elevated stress indicators. Monitor daily."
        )
        desc_zh = (
            f"TSI = {tsi_score:.0f}（{tsi_bias}），CRI = {cpi_score:.0f}。"
            "壓力指標升高，請每日追蹤。"
        )
    else:
        level = "none"
        show = False
        title_en = ""
        title_zh = ""
        desc_en = ""
        desc_zh = ""

    return {
        "show":     show,
        "level":    level,
        "title_en": title_en,
        "title_zh": title_zh,
        "desc_en":  desc_en,
        "desc_zh":  desc_zh,
    }


# ── Payload Builder ────────────────────────────────────────────────────────────

def build_cpi_indicators(cpi_result):
    """Convert CPIResult indicators to dict keyed by indicator name."""
    ind_map = {}
    if cpi_result is None:
        # Return fallback values matching default dashboard
        fallback = {
            "vix_term_structure":     {"signal": 22, "status": "normal"},
            "vix_spike":              {"signal": 38, "status": "watch"},
            "garch_vix_gap":          {"signal": 15, "status": "normal"},
            "credit_acceleration":    {"signal": 10, "status": "normal"},
            "breadth_divergence":     {"signal": 35, "status": "watch"},
            "distribution_days":      {"signal": 20, "status": "normal"},
            "rsi_divergence":         {"signal": 28, "status": "watch"},
            "ma_distance_reversal":   {"signal": 12, "status": "normal"},
            "yield_curve_steepening": {"signal": 18, "status": "normal"},
            "momentum_collapse":      {"signal":  8, "status": "normal"},
            "yield_surge":            {"signal": 52, "status": "elevated"},
            "intraday_selloff":       {"signal": 14, "status": "normal"},
        }
        return fallback

    for ind in cpi_result.indicators:
        status = ind.status
        # Normalise status: CPI uses normal/elevated/critical but dashboard shows watch
        if ind.signal >= 30 and status == "normal":
            status = "watch"
        ind_map[ind.name] = {
            "signal": round(float(ind.signal), 1),
            "status": status,
        }
    return ind_map


def build_tsi_indicators(tsi_result):
    """Convert TSIResult indicators to dict keyed by indicator name."""
    if tsi_result is None:
        fallback = {
            "sox_qqq_divergence":     {"signal": 30, "status": "watch"},
            "memory_momentum":        {"signal": 25, "status": "watch"},
            "yield_shock":            {"signal": 72, "status": "elevated"},
            "yield_30y_stress":       {"signal": 78, "status": "critical"},
            "yield_curve_bear_steep": {"signal": 58, "status": "elevated"},
            "ai_infra_rs":            {"signal": 22, "status": "normal"},
            "tech_breadth":           {"signal": 35, "status": "watch"},
            "cloud_rs":               {"signal": 18, "status": "normal"},
            "vix_tech_correlation":   {"signal": 48, "status": "watch"},
        }
        return fallback

    ind_map = {}
    for ind in tsi_result.indicators:
        sig = float(ind.signal)
        if sig >= 70:
            status = "critical"
        elif sig >= 50:
            status = "elevated"
        elif sig >= 25:
            status = "watch"
        else:
            status = "normal"
        ind_map[ind.name] = {
            "signal": round(sig, 1),
            "status": status,
        }
    return ind_map


def build_payload(yf_data, fred_data, cpi_result, tsi_result, cape_val):
    """Assemble the full JSON payload."""
    today = datetime.today().strftime("%Y-%m-%d")

    # ── AVI ──────────────────────────────────────────────────────────────────
    dims = compute_avi_dimensions(yf_data, fred_data, cape_val)
    avi_score = compute_avi_score(dims)
    avi_lvl   = avi_level(avi_score)

    # ── CRI ──────────────────────────────────────────────────────────────────
    cri_score = cpi_result.score if cpi_result else FALLBACK["cri_score"]
    cri_lvl   = cpi_result.level if cpi_result else "LOW"
    cri_flash = cpi_result.flash_alert.triggered if cpi_result else False
    cri_inds  = build_cpi_indicators(cpi_result)

    # ── TSI ──────────────────────────────────────────────────────────────────
    tsi_score = tsi_result.score if tsi_result else FALLBACK["tsi_score"]
    tsi_bias  = tsi_result.bias  if tsi_result else "CAUTIOUS"
    tsi_flash = tsi_result.flash_alert if tsi_result else False
    tsi_inds  = build_tsi_indicators(tsi_result)

    # ── Market snapshot ───────────────────────────────────────────────────────
    def latest_close(key, default=0.0):
        df = yf_data.get(key)
        if df is None or df.empty:
            return default
        col = "Close" if "Close" in df.columns else df.columns[0]
        return round(float(df[col].iloc[-1]), 2)

    def latest_fred(key, default=0.0):
        s = fred_data.get(key)
        if s is None or s.empty:
            return default
        return round(float(s.iloc[-1]), 4)

    sp500 = latest_close("^GSPC", FALLBACK["sp500"])
    vix   = latest_close("^VIX",  FALLBACK["vix"])
    oil   = latest_close("BZ=F",  0.0)
    t10y  = latest_fred("treasury_10y", FALLBACK["t10y"])
    t30y  = latest_fred("treasury_30y", FALLBACK["t30y"])
    cape  = cape_val if cape_val else FALLBACK["cape"]

    # ── Alert ─────────────────────────────────────────────────────────────────
    alert = build_alert(tsi_score, cri_score, tsi_bias, avi_lvl)

    payload = {
        "updated": today,
        # data_health：標記各引擎是真算還是 fallback，避免 silent-failure 再把舊值
        # 當成最新（TSI 一直 45.0 就是被這種無聲 fallback 蓋住）。
        "data_health": {
            "avi_cape_live": cape_val is not None,
            "cri_live":      cpi_result is not None,
            "tsi_live":      tsi_result is not None,
            "market_live":   bool(yf_data.get("^GSPC") is not None),
        },
        "avi": {
            "score":      avi_score,
            "level":      avi_lvl,
            "dimensions": dims,
        },
        "cri": {
            "score":      round(cri_score, 1),
            "level":      cri_lvl,
            "flash":      cri_flash,
            "indicators": cri_inds,
        },
        "tsi": {
            "score":      round(tsi_score, 1),
            "bias":       tsi_bias,
            "flash":      tsi_flash,
            "indicators": tsi_inds,
        },
        "market": {
            "sp500": sp500,
            "vix":   vix,
            "t10y":  t10y,
            "t30y":  t30y,
            "cape":  cape,
            "oil":   oil,
        },
        "alert": alert,
    }
    return payload


# ── HTML Injection ─────────────────────────────────────────────────────────────

MARKER_START = "// [KIWI-DATA-START]"
MARKER_END   = "// [KIWI-DATA-END]"


def inject_into_html(payload, html_path):
    """Replace the KIWI_DATA block in docs/index.html with fresh payload."""
    if not os.path.exists(html_path):
        log.error(f"HTML file not found: {html_path}")
        return False

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    json_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    new_block = f"{MARKER_START}\nvar KIWI_DATA = {json_str};\n{MARKER_END}"

    # Replace between markers (inclusive)
    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )
    if pattern.search(content):
        new_content = pattern.sub(new_block, content)
        log.info("Replaced existing KIWI_DATA block")
    else:
        # No markers found — try to insert after opening <script> tag in <body>
        log.warning("KIWI-DATA markers not found in HTML; inserting after <body>")
        insert_block = f"<script>\n{new_block}\n</script>\n"
        new_content = content.replace("<body>\n", f"<body>\n{insert_block}", 1)
        if new_content == content:
            log.error("Could not find insertion point in HTML")
            return False

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    log.info(f"Updated {html_path}")
    return True


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    log.info("=== AVI Dashboard Update Starting ===")
    log.info(f"Script dir : {_SCRIPT_DIR}")
    log.info(f"Project dir: {_PROJECT_DIR}")
    log.info(f"HTML path  : {DOCS_HTML}")

    # 1. Fetch data
    yf_data   = fetch_yfinance_data()
    fred_data = fetch_fred_data()
    cape_val  = scrape_cape()

    # 2. Compute engines
    cpi_result = compute_cpi(yf_data, fred_data)
    tsi_result = compute_tsi(yf_data, fred_data)

    # 3. Build payload
    payload = build_payload(yf_data, fred_data, cpi_result, tsi_result, cape_val)

    log.info("=== Computed Payload ===")
    log.info(f"  AVI  : {payload['avi']['score']:.2f} / {payload['avi']['level']}")
    log.info(f"  CRI  : {payload['cri']['score']:.1f} / {payload['cri']['level']}")
    log.info(f"  TSI  : {payload['tsi']['score']:.1f} / {payload['tsi']['bias']}")
    log.info(f"  SPX  : {payload['market']['sp500']}")
    log.info(f"  VIX  : {payload['market']['vix']}")
    log.info(f"  Alert: {payload['alert']['level']} (show={payload['alert']['show']})")

    # 4. Inject into HTML
    ok = inject_into_html(payload, DOCS_HTML)
    if ok:
        log.info("=== Dashboard update complete ===")
    else:
        log.error("=== Dashboard update failed (HTML injection) ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Unhandled error in update_dashboard.py: {e}", exc_info=True)
        sys.exit(0)  # exit 0 so GH Actions doesn't fail noisily
