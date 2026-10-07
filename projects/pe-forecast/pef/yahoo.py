"""Yahoo Finance 的公開股價介面（query1.finance.yahoo.com/v8/finance/chart；這個雲端環境可以連）。

月底收盤是「分割調整後、未做股利調整」的 close——和 loosygoosie 的分割調整後股數（shares_diluted_adj）同一個口徑，
所以 股價 ÷（最近四季淨利 ÷ 股數）＝本益比。分析師預估（quoteSummary）需要 cookie，這個環境拿不到（見 research/06）。
"""
import json
import os
import time
import urllib.request

import pandas as pd

URL = "https://query1.finance.yahoo.com/v8/finance/chart/{t}?range={rng}&interval={iv}&events=div%2Csplit"


def yahoo_symbol(ticker):
    return str(ticker).upper().replace(".", "-")


def chart(ticker, rng="5y", interval="1mo", cache_dir=None, max_age_h=24):
    """回傳 dict(close＝月底收盤 Series（以月底日期為索引）, div＝股利 Series, meta)。失敗回傳 None。"""
    sym = yahoo_symbol(ticker)
    path = os.path.join(cache_dir, f"{sym}_{rng}_{interval}.json") if cache_dir else None
    raw = None
    if path and os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age_h * 3600:
        raw = json.load(open(path))
    if raw is None:
        req = urllib.request.Request(URL.format(t=sym, rng=rng, iv=interval), headers={"User-Agent": "Mozilla/5.0"})
        try:
            raw = json.load(urllib.request.urlopen(req, timeout=30))
        except Exception:                                    # noqa: BLE001 — 網路錯誤一律當成沒資料
            return None
        if path:
            os.makedirs(cache_dir, exist_ok=True)
            json.dump(raw, open(path, "w"))
    try:
        r = raw["chart"]["result"][0]
        ts = pd.to_datetime(r["timestamp"], unit="s")
        close = pd.Series(r["indicators"]["quote"][0]["close"], index=ts, dtype=float).dropna()
    except (KeyError, TypeError, IndexError):
        return None
    if interval == "1mo":
        close.index = close.index.normalize() + pd.offsets.MonthEnd(0)  # 月資料的時間戳是月初（含時區時間）→ 對齊到月底
        close = close.groupby(level=0).last()
    divs = (r.get("events") or {}).get("dividends") or {}
    div = pd.Series({pd.to_datetime(v["date"], unit="s"): v["amount"] for v in divs.values()}, dtype=float).sort_index()
    return dict(close=close, div=div, meta=r.get("meta", {}))
