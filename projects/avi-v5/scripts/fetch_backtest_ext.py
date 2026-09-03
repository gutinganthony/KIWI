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
    # MRI 信用觸發層用：HYG 單獨含「信用利差 + 利率久期」兩種成分，
    # 必須減掉久期相近的公債(IEF)才能分離出純信用利差。LQD 提供投等級對照，
    # HYG/LQD 則是信用內部的品質利差。三者一起才構成可用的信用壓力量測。
    "LQD": "LQD",      # 投資等級公司債
    "IEF": "IEF",      # 7-10年公債（久期與 HYG/LQD 相近的無信用風險對照組）
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
# 個別標的的起始日覆寫：信用層要回測 2008 金融海嘯，2019 起太短（只涵蓋 3 次事件）。
# LQD/IEF 都在 2002-07 成立，抓到成立日才能涵蓋 2008，事件數從 3 提升到 6 次以上。
START_OVERRIDE = {
    "LQD": "2002-07-01",
    "IEF": "2002-07-01",
}
FRESH_SECONDS = 6 * 86400


def is_fresh(path):
    return path.exists() and (time.time() - path.stat().st_mtime) < FRESH_SECONDS


def run_jp_bridge(force=False):
    """側掛：日本開示資料橋（雲端 session 對日本站一律 403，只有 runner 抓得到）。
    放在本檔是為了共用既有的 workflow step，不必動 .github/workflows/。
    **必須在所有 return 路徑上都被呼叫**——價格檔新鮮時本檔會提前 return，
    若只掛在末段，開示橋會被連帶跳過（2026-07-26 修正的 bug）。"""
    try:
        import fetch_jp_disclosures
        print("--- jp_disclosures bridge ---")
        saved = sys.argv
        sys.argv = [saved[0]] + (["--force"] if force else [])
        try:
            fetch_jp_disclosures.main()
        finally:
            sys.argv = saved
    except Exception as e:  # noqa: BLE001 — never break the host job
        print(f"⚠️ jp_disclosures bridge failed: {e}")


def run_memory_bridge(force=False):
    """側掛：記憶體產業數據橋（trendforce/micron/SEC 在雲端 403，runner 或可通）。"""
    try:
        import fetch_memory_sources
        print("--- memory_sources bridge ---")
        saved = sys.argv
        sys.argv = [saved[0]] + (["--force"] if force else [])
        try:
            fetch_memory_sources.main()
        finally:
            sys.argv = saved
    except Exception as e:  # noqa: BLE001 — never break the host job
        print(f"⚠️ memory_sources bridge failed: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    EXT.mkdir(parents=True, exist_ok=True)
    targets = {t: EXT / f"{name}.csv" for t, name in TICKERS.items()}
    if not args.force and all(is_fresh(p) for p in targets.values()):
        print("ext data fresh (<6d) — skip price fetch")
        run_jp_bridge(args.force)   # 開示橋有自己的新鮮度判定（3 天），不受價格檔影響
        run_memory_bridge(args.force)
        return 0

    try:
        import yfinance as yf
    except ImportError:
        print("yfinance unavailable — skip price fetch (best-effort)")
        run_jp_bridge(args.force)
        run_memory_bridge(args.force)
        return 0

    ok = 0
    for ticker, path in targets.items():
        try:
            df = yf.download(ticker, start=START_OVERRIDE.get(ticker, START),
                             auto_adjust=False, progress=False)
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
    run_jp_bridge(args.force)
    run_memory_bridge(args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
