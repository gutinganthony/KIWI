#!/usr/bin/env python3
"""多源即時報價工具（純 stdlib，無第三方依賴）。

用法:
  python3 quote.py AAPL 6758.T 2330.TW          # 表格輸出
  python3 quote.py --json AAPL 6758.T           # JSON 輸出（給程式/agent 用）

來源順序（每檔逐一 fallback）:
  一般:  Yahoo chart API(免key) → stooq(免key) → Alpha Vantage(需 ALPHAVANTAGE_API_KEY)
  台股(.TW/.TWO/純數字): Yahoo → FinMind(FINMIND_TOKEN 可選) → stooq

執行環境注意: claude.ai 雲端 session 的 proxy 擋這些域名（2026-07-08 實測 CONNECT 403）。
本腳本設計在 Mac 或 GitHub Actions 執行；雲端要用需先把域名加進環境網路白名單。
分流細節見 skills/reprice/SKILL.md。
"""
import csv
import io
import json
import os
import sys
import urllib.request
from datetime import date, timedelta

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def _get(url, timeout=10):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def yahoo(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
    meta = json.loads(_get(url))["chart"]["result"][0]["meta"]
    return {"symbol": sym, "price": meta["regularMarketPrice"],
            "currency": meta.get("currency"),
            "asof": str(meta.get("regularMarketTime", "")), "source": "yahoo"}


def stooq(sym):
    s = sym.lower()
    if s.endswith(".t"):
        s = s[:-2] + ".jp"          # 東證: 6758.T → 6758.jp
    elif "." not in s:
        s += ".us"                   # 無後綴視為美股
    txt = _get(f"https://stooq.com/q/l/?s={s}&f=sd2t2ohlcv&h&e=csv")
    row = next(csv.DictReader(io.StringIO(txt)))
    if row.get("Close") in (None, "", "N/D"):
        raise ValueError(f"stooq no data for {s}")
    return {"symbol": sym, "price": float(row["Close"]), "currency": None,
            "asof": f'{row.get("Date", "")} {row.get("Time", "")}'.strip(),
            "source": "stooq"}


def finmind(sym):
    code = sym.split(".")[0]
    start = (date.today() - timedelta(days=14)).isoformat()
    url = (f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice"
           f"&data_id={code}&start_date={start}")
    token = os.environ.get("FINMIND_TOKEN")
    if token:
        url += f"&token={token}"
    rows = json.loads(_get(url)).get("data", [])
    if not rows:
        raise ValueError(f"finmind no data for {code}")
    last = rows[-1]
    return {"symbol": sym, "price": last["close"], "currency": "TWD",
            "asof": last["date"], "source": "finmind"}


def alphavantage(sym):
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not key:
        raise ValueError("no ALPHAVANTAGE_API_KEY")
    url = (f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE"
           f"&symbol={sym}&apikey={key}")
    q = json.loads(_get(url)).get("Global Quote", {})
    if not q.get("05. price"):
        raise ValueError(f"alphavantage no data for {sym}")
    return {"symbol": sym, "price": float(q["05. price"]), "currency": None,
            "asof": q.get("07. latest trading day", ""), "source": "alphavantage"}


def is_taiwan(sym):
    s = sym.upper()
    return s.endswith(".TW") or s.endswith(".TWO") or s.isdigit()


def fetch(sym):
    chain = [yahoo, finmind, stooq] if is_taiwan(sym) else [yahoo, stooq, alphavantage]
    errors = []
    for fn in chain:
        try:
            return fn(sym)
        except Exception as e:  # noqa: BLE001 — 逐源 fallback，錯誤彙整後回報
            errors.append(f"{fn.__name__}: {e}")
    return {"symbol": sym, "error": " | ".join(errors)}


def main():
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(2)
    results = [fetch(s) for s in args]
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if "error" in r:
                print(f"{r['symbol']:<10} ERROR  {r['error']}", file=sys.stderr)
            else:
                ccy = r.get("currency") or "?"
                print(f"{r['symbol']:<10} {r['price']:>12}  {ccy:<4} {r['asof']:<12} [{r['source']}]")
    sys.exit(1 if all("error" in r for r in results) else 0)


if __name__ == "__main__":
    main()
