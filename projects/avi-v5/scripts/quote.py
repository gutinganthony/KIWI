#!/usr/bin/env python3
"""多源即時報價工具（純 stdlib，無第三方依賴）。

用法:
  python3 quote.py AAPL 6758.T 2330.TW          # 表格輸出
  python3 quote.py --json AAPL 6758.T           # JSON 輸出（給程式/agent 用）
  python3 quote.py --risk PLAB RMBS             # 美股風險分級（beta × 市值）

來源順序（每檔逐一 fallback）:
  一般:  Yahoo chart API(免key) → stooq(免key) → Alpha Vantage(需 ALPHAVANTAGE_API_KEY)
  台股(.TW/.TWO/純數字): Yahoo → FinMind(FINMIND_TOKEN 可選) → stooq
  --risk: Yahoo quoteSummary(可能需 cookie 而 401) → Alpha Vantage OVERVIEW(需 key)

風險分級規則（skills/serenity/SKILL.md §美股風險分級）: beta 與市值各分三級取較高者。
beta ≤0.9 低 / 0.9–1.3 中 / >1.3 或查無＝高；市值 ≥$10B 低 / $2–10B 中 / <$2B 高。

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


def yahoo_summary(sym):
    """拉 beta + marketCap。注意: Yahoo v10 quoteSummary 有時要求 cookie/crumb 而回 401。"""
    url = (f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sym}"
           f"?modules=summaryDetail,price")
    d = json.loads(_get(url))["quoteSummary"]["result"][0]
    beta = (d.get("summaryDetail", {}).get("beta") or {}).get("raw")
    mcap = (d.get("price", {}).get("marketCap") or {}).get("raw")
    return beta, mcap, "yahoo"


def av_overview(sym):
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not key:
        raise ValueError("no ALPHAVANTAGE_API_KEY")
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={sym}&apikey={key}"
    d = json.loads(_get(url))
    if not d.get("Symbol"):
        raise ValueError(f"alphavantage OVERVIEW no data for {sym}")
    beta = float(d["Beta"]) if d.get("Beta") not in (None, "", "None", "-") else None
    mcap = float(d["MarketCapitalization"]) if d.get("MarketCapitalization") not in (None, "", "None") else None
    return beta, mcap, "alphavantage"


def risk_tier(beta, mcap):
    """兩維各分級取較高風險者。回 (tier, 說明)。規則見 skills/serenity/SKILL.md。"""
    b = 2 if (beta is None or beta > 1.3) else (0 if beta <= 0.9 else 1)
    m = 2 if (mcap is None or mcap < 2e9) else (0 if mcap >= 10e9 else 1)
    return ["low", "mid", "high"][max(b, m)]


def fetch_risk(sym):
    errors = []
    for fn in (yahoo_summary, av_overview):
        try:
            beta, mcap, src = fn(sym)
            return {"symbol": sym, "beta": beta, "mcap": mcap,
                    "risk": risk_tier(beta, mcap), "source": src}
        except Exception as e:  # noqa: BLE001
            errors.append(f"{fn.__name__}: {e}")
    return {"symbol": sym, "error": " | ".join(errors)}


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


RISK_ZH = {"low": "低", "mid": "中", "high": "高"}


def main():
    args = [a for a in sys.argv[1:] if a not in ("--json", "--risk")]
    as_json = "--json" in sys.argv
    as_risk = "--risk" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(2)
    results = [fetch_risk(s) if as_risk else fetch(s) for s in args]
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif as_risk:
        for r in results:
            if "error" in r:
                print(f"{r['symbol']:<10} ERROR  {r['error']}", file=sys.stderr)
            else:
                mcap_b = f"${r['mcap']/1e9:.2f}B" if r["mcap"] is not None else "查無"
                beta_s = f"{r['beta']:.2f}" if r["beta"] is not None else "查無"
                print(f"{r['symbol']:<10} beta={beta_s:<6} mcap={mcap_b:<10} "
                      f"風險={RISK_ZH[r['risk']]} ({r['risk']}) [{r['source']}]")
        print("備註: 風險=beta×市值取較高者; beta ≤0.9低/0.9–1.3中/>1.3或查無=高; "
              "市值 ≥$10B低/$2–10B中/<$2B高 (見 skills/serenity/SKILL.md)")
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
