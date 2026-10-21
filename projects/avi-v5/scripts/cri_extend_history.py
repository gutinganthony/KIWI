#!/usr/bin/env python3
"""
cri_extend_history.py — 把 CRI v2 日序列從既有快取（1994–2020-04）延伸到今天

與 cri_30yr_backtest.py 同一套算法（只用 SPY＋VIX 的 9 個指標，信用/利率 3 指標停用），
資料改用 Yahoo（SPY adjclose＋volume、^VIX）。從 2019-06 開始算，與舊快取重疊 10 個月以檢查一致性。
輸出：data/backtest/cri_history_ext.csv

用法：python scripts/cri_extend_history.py [--cache DIR]
"""
import argparse, json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from src.cpi import CrashProbabilityIndex

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "backtest", "cri_history_ext.csv")


def yahoo(tk, cache):
    p = os.path.join(cache, f"y_{urllib.request.quote(tk)}.json") if cache else None
    if p and os.path.exists(p):
        raw = open(p, "rb").read()
    else:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(tk)}?period1=-1325635200&period2=4102444800&interval=1d"
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
    r = json.loads(raw)["chart"]["result"][0]
    idx = pd.to_datetime(r["timestamp"], unit="s").normalize()
    q = r["indicators"]
    close = q.get("adjclose", [{}])[0].get("adjclose") or q["quote"][0]["close"]
    return pd.DataFrame({"close": close, "volume": q["quote"][0]["volume"]}, index=idx).dropna().groupby(level=0).last()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cache"); ap.add_argument("--start", default="2019-06-01")
    a = ap.parse_args()
    spy = yahoo("SPY", a.cache)
    vix = yahoo("^VIX", a.cache)["close"]
    empty = pd.Series(dtype=float)
    cri = CrashProbabilityIndex()
    rows = []
    for d in spy.index[spy.index >= a.start]:
        sp_w = spy[spy.index <= d].tail(300)
        vx_w = vix[vix.index <= d].tail(300)
        try:
            r = cri.compute(sp500_daily=sp_w, vix_daily=vx_w, vix3m_daily=None, baa_daily=empty, aaa_daily=empty,
                            treasury_10y=empty, treasury_2y=empty)
            rows.append({"date": d.date().isoformat(), "score": r.score})
        except Exception as e:
            print("skip", d.date(), e, file=sys.stderr)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"✓ {OUT}  {rows[0]['date']} → {rows[-1]['date']}  ({len(rows)} 日)")


if __name__ == "__main__":
    main()
