#!/usr/bin/env python3
"""Fetch extension price history for backtests (runs in GitHub Actions, where
yfinance is NOT blocked — the Claude cloud container can't fetch these itself).

Writes yahoo-style daily CSVs to data/ext/ so research sessions can extend the
1994-2020 backtest sample into the modern regime (2019→today).

Frugality guard: skips fetching if files exist and are fresh (<6 days old), so
the 3x-daily dashboard workflow only actually downloads ~weekly.

Usage: python3 scripts/fetch_backtest_ext.py [--force]
Exit code is ALWAYS 0 — this is a best-effort side-task and must never break
the dashboard update job that hosts it.
"""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "data" / "ext"

TICKERS = {
    # 大盤/信用/vol（LFI 第四錶 + 領先指標回測用）
    "SPY": "SPY",
    "QQQ": "QQQ",
    "HYG": "HYG",
    "SMH": "SMH",
    "^VVIX": "VVIX",   # extends local VVIX.csv beyond 2025-02
    "^VIX": "VIX",     # 讓 LFI 用完整 3 年校準（否則受限於 yfinance 2 年窗）
    # 真實 Serenity 標的（供未來用真標的驗證節流閥/擇時，取代高beta代理籃）
    "6855.T": "JEM",         # 記憶體探針卡
    "6315.T": "Towa",        # HBM molding
    "6525.T": "Kokusai",     # 批次 ALD
    "6857.T": "Advantest",   # AI/HBM 測試
    "6777.T": "santec",      # 光通訊測試
    "8035.T": "TokyoElectron",
}
START = "2019-01-01"
FRESH_SECONDS = 6 * 86400


def is_fresh(path):
    return path.exists() and (time.time() - path.stat().st_mtime) < FRESH_SECONDS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    EXT.mkdir(parents=True, exist_ok=True)
    targets = {t: EXT / f"{name}.csv" for t, name in TICKERS.items()}
    if not args.force and all(is_fresh(p) for p in targets.values()):
        print("ext data fresh (<6d) — skip fetch")
        return 0

    try:
        import yfinance as yf
    except ImportError:
        print("yfinance unavailable — skip (best-effort)")
        return 0

    ok = 0
    for ticker, path in targets.items():
        try:
            df = yf.download(ticker, start=START, auto_adjust=False, progress=False)
            if df is None or len(df) < 100:
                print(f"⚠️ {ticker}: too little data ({0 if df is None else len(df)}) — kept old file")
                continue
            # yfinance MultiIndex columns → flatten to yahoo classic layout
            if hasattr(df.columns, "levels"):
                df.columns = [c[0] for c in df.columns]
            df = df.reset_index()
            keep = [c for c in ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"] if c in df.columns]
            df[keep].to_csv(path, index=False)
            print(f"✅ {ticker} → {path.name}  rows={len(df)}  last={df['Date'].iloc[-1]}")
            ok += 1
        except Exception as e:  # noqa: BLE001 — never break the host job
            print(f"⚠️ {ticker} failed: {e}")
    print(f"fetched {ok}/{len(targets)} at {datetime.now(timezone.utc).isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
