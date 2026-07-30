#!/usr/bin/env python3
"""在 GitHub Actions runner 上抓日線 → 落地成 CSV 供 run_report.py 回測。

**為什麼要跑在 runner 上**：Claude 雲端 session 的 agent proxy 對所有行情源
一律 CONNECT 403（實測 Yahoo/stooq/coingecko/binance/tiingo/nasdaqtrader… 全擋，
stooq 甚至過了 PoW 仍回 Access denied）。runner 不受此限——同 avi-v5 的
fetch_backtest_ext.py 資料橋。

輸出：<outdir>/<SYMBOL>.csv，欄位 Date,Open,High,Low,Close,Volume
      **已 auto_adjust**（除權息還原），故開盤與收盤同一基準，回測不會失真。

用法:
  python3 fetch_prices.py --universe ndx100 --out data/prices --start 2018-01-01
  python3 fetch_prices.py --universe nasdaq-all --out data/prices
  python3 fetch_prices.py --symbols BTC-USD,ETH-USD --out data/prices
"""

from __future__ import annotations

import argparse
import io
import sys
import time
from pathlib import Path

CRYPTO = ["BTC-USD", "ETH-USD"]

# 參考基準：整體市場（Nasdaq-100 ETF / 大盤 / 半導體），用來判斷策略表現
# 是「策略有效」還是「這兩年市場本來就漲」。
BENCHMARKS = ["QQQ", "SPY", "^IXIC", "^NDX"]

# Nasdaq-100 成分股快照（2026 上半年）。**此清單為靜態備援**——
# main() 會先嘗試從 Wikipedia 取當期權威清單，取不到才用這份。
# ⚠️ 用「今天的成分股」回測過去 24 個月＝存活者偏差（被剔除的輸家不在清單裡），
#    報告中必須標註。
NDX100_SNAPSHOT = [
    "AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP", "AMAT", "AMD", "AMGN",
    "AMZN", "ANSS", "APP", "ARM", "ASML", "AVGO", "AXON", "AZN", "BIIB", "BKNG",
    "BKR", "CCEP", "CDNS", "CDW", "CEG", "CHTR", "CMCSA", "COST", "CPRT", "CRWD",
    "CSCO", "CSGP", "CSX", "CTAS", "CTSH", "DASH", "DDOG", "DXCM", "EA", "EXC",
    "FANG", "FAST", "FTNT", "GEHC", "GFS", "GILD", "GOOG", "GOOGL", "HON", "IDXX",
    "ILMN", "INTC", "INTU", "ISRG", "KDP", "KHC", "KLAC", "LIN", "LRCX", "LULU",
    "MAR", "MCHP", "MDB", "MDLZ", "MELI", "META", "MNST", "MRVL", "MSFT", "MSTR",
    "MU", "NFLX", "NVDA", "NXPI", "ODFL", "ON", "ORLY", "PANW", "PAYX", "PCAR",
    "PDD", "PEP", "PLTR", "PYPL", "QCOM", "REGN", "ROP", "ROST", "SBUX", "SNPS",
    "TEAM", "TMUS", "TSLA", "TTD", "TTWO", "TXN", "VRSK", "VRTX", "WBD", "WDAY",
    "XEL", "ZS",
]


# --------------------------------------------------------------------------
def ndx100_from_wikipedia():
    """從 Wikipedia 取當期 Nasdaq-100 成分股；失敗回 None（呼叫端退回快照）。"""
    try:
        import pandas as pd
        import requests

        r = requests.get(
            "https://en.wikipedia.org/wiki/Nasdaq-100",
            headers={"User-Agent": "Mozilla/5.0 (compatible; KIWI-research/1.0)"},
            timeout=30,
        )
        r.raise_for_status()
        for tbl in pd.read_html(io.StringIO(r.text)):
            cols = {str(c).strip().lower() for c in tbl.columns}
            if {"ticker", "company"} & cols and len(tbl) > 90:
                col = next(c for c in tbl.columns if str(c).strip().lower() == "ticker")
                syms = [str(s).strip().upper() for s in tbl[col].tolist()]
                syms = [s for s in syms if s and s != "NAN" and len(s) <= 6]
                if len(syms) >= 90:
                    print(f"✅ Wikipedia Nasdaq-100: {len(syms)} 檔")
                    return syms
        print("⚠️ Wikipedia 頁面結構不符預期")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Wikipedia 取清單失敗: {e}")
    return None


def nasdaq_all_listed():
    """Nasdaq 全上市證券清單（~3,000+ 檔）。失敗回 None。"""
    try:
        import requests

        r = requests.get(
            "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
            timeout=60,
        )
        r.raise_for_status()
        syms = []
        for line in r.text.splitlines()[1:]:
            parts = line.split("|")
            if len(parts) < 7 or parts[0].startswith("File Creation"):
                continue
            sym, _name, _cat, test_issue, _status, _lot, etf = parts[:7]
            if test_issue == "Y" or etf == "Y":   # 排除測試代碼與 ETF
                continue
            if not sym.isalpha():                  # 排除權證/特別股等含符號代碼
                continue
            syms.append(sym.upper())
        print(f"✅ nasdaqtrader 全上市普通股: {len(syms)} 檔")
        return sorted(set(syms))
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ nasdaqtrader 取清單失敗: {e}")
    return None


# --------------------------------------------------------------------------
def download(symbols, outdir: Path, start: str, chunk: int = 40, min_rows: int = 400):
    """分批下載並落地。回傳 (成功清單, 失敗清單)。"""
    import pandas as pd
    import yfinance as yf

    outdir.mkdir(parents=True, exist_ok=True)
    ok, bad = [], []

    for i in range(0, len(symbols), chunk):
        batch = symbols[i : i + chunk]
        print(f"[{i+1}-{i+len(batch)}/{len(symbols)}] {' '.join(batch)}", flush=True)
        try:
            df = yf.download(
                batch, start=start, auto_adjust=True, progress=False,
                group_by="ticker", threads=True, timeout=60,
            )
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ batch failed: {e}")
            bad.extend(batch)
            time.sleep(5)
            continue

        for sym in batch:
            try:
                sub = df[sym] if len(batch) > 1 else df
                sub = sub.dropna(subset=["Close"])
                if sub is None or len(sub) < min_rows:
                    print(f"  ⚠️ {sym}: rows={0 if sub is None else len(sub)} < {min_rows}")
                    bad.append(sym)
                    continue
                out = sub.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
                safe = sym.replace("^", "IDX_").replace("/", "_")
                out.to_csv(outdir / f"{safe}.csv", index=False)
                ok.append(sym)
            except Exception as e:  # noqa: BLE001
                print(f"  ⚠️ {sym}: {e}")
                bad.append(sym)
        time.sleep(1.5)

    return ok, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", default="ndx100",
                    choices=["ndx100", "nasdaq-all", "none"])
    ap.add_argument("--symbols", default="", help="額外代碼，逗號分隔")
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--min-rows", type=int, default=400)
    args = ap.parse_args()

    syms: list[str] = []
    if args.universe == "ndx100":
        syms += ndx100_from_wikipedia() or NDX100_SNAPSHOT
    elif args.universe == "nasdaq-all":
        syms += nasdaq_all_listed() or (ndx100_from_wikipedia() or NDX100_SNAPSHOT)

    syms += CRYPTO + BENCHMARKS
    if args.symbols:
        syms += [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    seen, uniq = set(), []
    for s in syms:
        if s not in seen:
            seen.add(s)
            uniq.append(s)

    print(f"universe={args.universe}  總計 {len(uniq)} 檔  start={args.start}")
    ok, bad = download(uniq, Path(args.out), args.start, min_rows=args.min_rows)
    print(f"\n✅ 成功 {len(ok)} 檔 / ❌ 失敗 {len(bad)} 檔")
    if bad:
        print("失敗清單:", " ".join(bad[:60]), "..." if len(bad) > 60 else "")
    # 資料橋的驗收句是「檔案有沒有出現」，不是「腳本有沒有成功」
    n_files = len(list(Path(args.out).glob("*.csv")))
    print(f"落地 CSV 檔數: {n_files}")
    return 0 if n_files > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
