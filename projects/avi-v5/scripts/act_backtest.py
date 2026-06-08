#!/usr/bin/env python3
"""
ACT Backtest — AVI / CRI / TSI 歷史回測

用法（在 projects/avi-v5/ 目錄下）：
  python scripts/act_backtest.py

需要環境變數：
  FRED_API_KEY=你的FRED金鑰

回測日期：
  2000-03-24 — 網路泡沫頂點
  2007-10-09 — 金融海嘯崩盤前夕
  今天       — 現況
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import yfinance as yf

# ── CAPE 歷史值（Shiller 資料，無法從 API 動態取得）─────────────────────────
HISTORICAL_CAPE = {
    "2000-03-24": 44.2,   # 網路泡沫頂點，史上最高之一
    "2007-10-09": 27.2,   # 金融海嘯前夕
}

# ── 工具函數 ─────────────────────────────────────────────────────────────────

def yf_close(ticker, start, end):
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        return pd.Series(dtype=float)
    col = ("Close", ticker) if isinstance(df.columns, pd.MultiIndex) else "Close"
    return df[col].dropna()


def yf_df(ticker, start, end):
    """Return DataFrame with 'close' and 'volume' for CRI."""
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        close = df[("Close", ticker)]
        volume = df[("Volume", ticker)]
    else:
        close = df["Close"]
        volume = df["Volume"]
    return pd.DataFrame({"close": close, "volume": volume}).dropna()


def fred_series(fred, series_id, start, end):
    try:
        return fred.get_series(series_id,
                               observation_start=start,
                               observation_end=end).dropna()
    except Exception as e:
        print(f"  [WARN] FRED {series_id} failed: {e}")
        return pd.Series(dtype=float)


# ── AVI 計算（對齊 update_dashboard.py 邏輯）──────────────────────────────

def compute_avi(cape_val, vix_close, spy_close, t10y, baa, cpi_index, as_of_dt):
    dims = {
        "valuation":     55,
        "profitability": 34,
        "macro":         50,
        "rate":          50,
        "credit":        30,
        "momentum":      50,
    }

    # Valuation: CAPE → 百分位
    if cape_val:
        dims["valuation"] = int(min(100, max(0, (cape_val - 15) / 30 * 100)))

    # Macro: VIX 252 日滾動百分位
    if len(vix_close) > 63:
        vix_now = vix_close.iloc[-1]
        window = vix_close.tail(252)
        dims["macro"] = int((window < vix_now).sum() / len(window) * 100)

    # Rate: CPI YoY 百分位 or 10Y 殖利率百分位
    if cpi_index is not None and len(cpi_index) >= 13:
        yoy = cpi_index.pct_change(12).dropna() * 100
        if len(yoy) > 12:
            now = yoy.iloc[-1]
            dims["rate"] = int(min(100, max(0, (yoy < now).sum() / len(yoy) * 100)))
    elif len(t10y) > 252:
        now = t10y.iloc[-1]
        dims["rate"] = int(min(100, max(0, (t10y.tail(252) < now).sum() / 252 * 100)))

    # Credit: BAA-10Y 利差百分位
    if len(baa) > 60 and len(t10y) > 60:
        spread = baa.reindex(t10y.index, method="ffill") - t10y
        spread = spread.dropna()
        if len(spread) > 60:
            now = spread.iloc[-1]
            dims["credit"] = int(min(100, max(0, (spread < now).sum() / len(spread) * 100)))

    # Momentum: SPY vs 200MA
    if len(spy_close) > 200:
        ma200 = spy_close.rolling(200).mean().iloc[-1]
        ratio = (spy_close.iloc[-1] / ma200 - 1) * 100
        dims["momentum"] = int(min(100, max(0, 50 - ratio * 1.0)))

    weights = {
        "valuation": 0.38, "profitability": 0.08, "macro": 0.14,
        "rate": 0.14, "credit": 0.12, "momentum": 0.14,
    }
    score = sum(dims[d] / 100 * w * 10 for d, w in weights.items())

    if score >= 8.0:   level = "CRITICAL"
    elif score >= 7.0: level = "HIGH"
    elif score >= 5.5: level = "ELEVATED"
    elif score >= 4.0: level = "NEUTRAL"
    else:              level = "LOW"

    return round(score, 2), level, dims


# ── 主回測邏輯 ────────────────────────────────────────────────────────────────

def run_backtest(label, as_of, cape_override=None):
    print(f"\n{'='*60}")
    print(f"  📅 {label}  ({as_of})")
    print(f"{'='*60}")

    fred_key = os.environ.get("FRED_API_KEY", "")
    if not fred_key:
        print("  ❌ 需要 FRED_API_KEY 環境變數")
        return

    from fredapi import Fred
    from src.cpi import CrashProbabilityIndex
    from src.tsi import TechStressIndex

    as_of_dt = pd.Timestamp(as_of)
    # 抓取足夠的歷史資料（回到 as_of 前 2 年）
    start = (as_of_dt - timedelta(days=800)).strftime("%Y-%m-%d")
    end   = (as_of_dt + timedelta(days=3)).strftime("%Y-%m-%d")

    print(f"  資料範圍：{start} → {end}")
    print("  抓取市場資料中...")

    # ── yfinance ──
    sp500_df  = yf_df("^GSPC", start, end)
    vix_close = yf_close("^VIX", start, end)
    qqq_close = yf_close("QQQ",  start, end)
    sox_close = yf_close("^SOX", start, end)   # Philadelphia SOX index
    mu_close  = yf_close("MU",   start, end)
    spy_close = yf_close("SPY",  start, end)
    smh_close = yf_close("SMH",  start, end)   # 2000 年前不存在 → 用 QQQ 代替

    # SMH 在 2000 年不存在，用 QQQ 或 SOX 替代
    if smh_close.empty:
        print("  [INFO] SMH 無資料（可能是 2000 年前），改用 SOX 替代")
        smh_close = sox_close if not sox_close.empty else qqq_close

    # SOX 無資料則用 QQQ 替代
    if sox_close.empty:
        print("  [INFO] ^SOX 無資料，改用 QQQ 替代")
        sox_close = qqq_close

    # ── FRED ──
    fred = Fred(api_key=fred_key)
    t10y      = fred_series(fred, "DGS10",    start, end)
    t30y      = fred_series(fred, "DGS30",    start, end)
    t2y       = fred_series(fred, "DGS2",     start, end)
    baa       = fred_series(fred, "BAA",      start, end)
    aaa       = fred_series(fred, "AAA",      start, end)
    cpi_index = fred_series(fred, "CPIAUCSL", start, end)

    cape_val = cape_override or HISTORICAL_CAPE.get(as_of)

    # ── AVI ──
    print("  計算 AVI...")
    try:
        avi_score, avi_level, dims = compute_avi(
            cape_val, vix_close, spy_close, t10y, baa, cpi_index, as_of_dt
        )
        print(f"  ✅ AVI = {avi_score:.1f}/10  [{avi_level}]")
        for d, v in dims.items():
            bar = "█" * (v // 10)
            print(f"       {d:<14}: {v:3d}%  {bar}")
    except Exception as e:
        print(f"  ❌ AVI failed: {e}")
        avi_score = None

    # ── CRI ──
    print("  計算 CRI...")
    try:
        cri = CrashProbabilityIndex()
        cri_result = cri.compute(
            sp500_daily=sp500_df,
            vix_daily=vix_close,
            vix3m_daily=None,
            baa_daily=baa,
            aaa_daily=aaa,
            treasury_10y=t10y,
            treasury_2y=t2y,
            as_of=as_of,
            avi_score=avi_score,
        )
        print(f"  ✅ CRI = {cri_result.score:.0f}/100  [{cri_result.level}]")
        if cri_result.flash_alert.triggered:
            for t in cri_result.flash_alert.triggers:
                print(f"       ⚡ Flash: {t}")
        top = sorted(cri_result.indicators, key=lambda x: -x.signal)[:4]
        for ind in top:
            print(f"       {ind.name:<30}: {ind.signal:.0f}/100  [{ind.status}]")
    except Exception as e:
        print(f"  ❌ CRI failed: {e}")

    # ── TSI ──
    print("  計算 TSI...")
    try:
        tsi = TechStressIndex()
        # 若 t30y 空就不傳
        t30y_arg = t30y if not t30y.empty else None
        tsi_result = tsi.compute(
            sox_daily=sox_close,
            qqq_daily=qqq_close,
            mu_daily=mu_close if not mu_close.empty else spy_close,
            smh_daily=smh_close,
            spy_daily=spy_close,
            treasury_10y=t10y,
            vix_daily=vix_close,
            treasury_30y=t30y_arg,
            as_of=as_of,
        )
        print(f"  ✅ TSI = {tsi_result.score:.0f}/100  [{tsi_result.bias}]")
        if tsi_result.flash_alert:
            print(f"       ⚡ Flash: {tsi_result.flash_reason}")
        top = sorted(tsi_result.indicators, key=lambda x: -x.signal)[:4]
        for ind in top:
            print(f"       {ind.name:<30}: {ind.signal:.0f}/100")
    except Exception as e:
        print(f"  ❌ TSI failed: {e}")

    return


if __name__ == "__main__":
    print("ACT 回測工具 — AVI / CRI / TSI")
    print("需要 FRED_API_KEY 環境變數，且需要網路連線")

    scenarios = [
        ("2000-03-24 — 網路泡沫頂點",  "2000-03-24", 44.2),
        ("2007-10-09 — 金融海嘯前夕",  "2007-10-09", 27.2),
        ("今天 — 現況",                datetime.today().strftime("%Y-%m-%d"), None),
    ]

    for label, date, cape in scenarios:
        run_backtest(label, date, cape_override=cape)

    print(f"\n{'='*60}")
    print("  回測完成")
    print(f"{'='*60}")
