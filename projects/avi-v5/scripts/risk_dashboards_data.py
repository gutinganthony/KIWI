#!/usr/bin/env python3
"""
risk_dashboards_data.py — 兩個風險 dashboard 的資料層

(1) 歷史對照：1973 / 1987 / 2000 三次見頂當下 vs 今天，同一組指標並排，算出今天最像哪一次。
(2) 系統性風險監控：1987 年那類「結構性盲點」在今天的對應物（利率管線、機械式賣壓、
    私募信貸、AI 融資鏈、散戶槓桿、日圓、油價、集中度），每一點的現值、警戒線、狀態。
(3) 1987 年時間軸：見頂 → 跌破 200 日線 → 崩盤，驗證「規則 3 在 1987 何時成立」。

資料：FRED（fredgraph.csv，免金鑰）、Yahoo chart API、Shiller CAPE（GitHub 鏡像 datasets/s-and-p-500）。
今天的 CAPE 取 KIWI 儀表板（docs/index.html 的 market.cape）。
只用標準函式庫＋pandas。輸出：projects/avi-v5/data/risk_dashboards.json

用法：python scripts/risk_dashboards_data.py [--cache DIR]
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import date

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "risk_dashboards.json")
DOCS_INDEX = os.path.join(os.path.dirname(os.path.dirname(ROOT)), "docs", "index.html")
UA = {"User-Agent": "Mozilla/5.0"}


def _get(url, path):
    if path and os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            return f.read()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        raw = r.read()
    if path:
        with open(path, "wb") as f:
            f.write(raw)
    return raw


def fred(sid, cache):
    raw = _get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",
               os.path.join(cache, f"{sid}.csv") if cache else None).decode()
    rows = [l.split(",") for l in raw.splitlines()[1:]]
    s = pd.Series({pd.Timestamp(d): float(v) for d, v in rows if v not in ("", ".")})
    return s.sort_index()


def yahoo(tk, cache):
    q = urllib.request.quote(tk)
    raw = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{q}?period1=-1325635200&period2=4102444800&interval=1d",
               os.path.join(cache, f"y_{q}.json") if cache else None)
    r = json.loads(raw)["chart"]["result"][0]
    s = pd.Series(r["indicators"]["quote"][0]["close"], index=pd.to_datetime(r["timestamp"], unit="s").normalize())
    return s.dropna().groupby(level=0).last()


def shiller(cache):
    raw = _get("https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv",
               os.path.join(cache, "shiller_gh.csv") if cache else None).decode()
    df = pd.read_csv(pd.io.common.StringIO(raw), parse_dates=["Date"]).set_index("Date")
    return df["PE10"].replace(0, np.nan).dropna()


def kiwi_market():
    try:
        html = open(DOCS_INDEX, encoding="utf-8").read()
        m = re.search(r"KIWI_DATA\s*=\s*(\{.*?\});", html, re.S)
        return json.loads(m.group(1)).get("market", {}) if m else {}
    except Exception:
        return {}


def at(s, d):
    """d 當天或之前最近一筆。"""
    s = s[s.index <= pd.Timestamp(d)]
    return (float(s.iloc[-1]), s.index[-1].date().isoformat()) if len(s) else (None, None)


def chg(s, d, months=12, pct=False):
    v, _ = at(s, d)
    v0, _ = at(s, pd.Timestamp(d) - pd.DateOffset(months=months))
    if v is None or v0 is None:
        return None
    return (v / v0 - 1) * 100 if pct else v - v0


def r(x, n=2):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=None, help="下載快取目錄（可省略）")
    a = ap.parse_args()
    if a.cache:
        os.makedirs(a.cache, exist_ok=True)
    C = a.cache

    F = {k: fred(k, C) for k in ["GS10", "FEDFUNDS", "CPIAUCSL", "UNRATE", "BAA", "M2SL", "WTISPLC", "TB3MS",
                                 "FYFSGDA188S", "TWEXMMTH", "DTWEXBGS", "DGS10", "DGS30", "VXOCLS", "VIXCLS",
                                 "BAMLH0A0HYM2", "BAMLC0A0CM", "BAMLH0A3HYC", "T10Y3M", "SOFR", "IORB",
                                 "RRPONTSYD", "WRESBAL", "DCOILBRENTEU", "DCOILWTICO", "DEXJPUS", "NFCI",
                                 "STLFSI4", "IRLTLT01JPM156N"]}
    spx = yahoo("^GSPC", C)
    cape = shiller(C)
    km = kiwi_market()
    today = spx.index[-1]
    ma200 = spx.rolling(200).mean()

    # ─── (1) 歷史對照 ────────────────────────────────────────────────────────
    eps = {"1973": "1973-01-11", "1987": "1987-08-25", "2000": "2000-03-24", "now": today.date().isoformat()}

    def cape_at(k, d):
        if k == "now":
            return km.get("cape")
        return at(cape, pd.Timestamp(d).replace(day=1))[0]

    rows = {}
    for k, d in eps.items():
        d = pd.Timestamp(d)
        cp = cape_at(k, d)
        y10 = at(F["DGS10"], d)[0] if d.year >= 1962 else at(F["GS10"], d)[0]
        cpi = chg(F["CPIAUCSL"], d, 12, pct=True)
        cpi_prev = chg(F["CPIAUCSL"], d - pd.DateOffset(months=12), 12, pct=True)
        dollar = F["DTWEXBGS"] if k == "now" else F["TWEXMMTH"]
        vol = F["VIXCLS"] if d.year >= 1990 else (F["VXOCLS"] if d.year >= 1986 else None)
        rows[k] = {
            "date": d.date().isoformat(),
            "cape": r(cp, 1),
            "gap": r(y10 - 100 / cp, 2) if cp and y10 else None,
            "y10": r(y10, 2),
            "y10_chg": r(chg(F["GS10"], d), 2),
            "ff_chg": r(chg(F["FEDFUNDS"], d), 2),
            "curve": r(at(F["GS10"], d)[0] - at(F["TB3MS"], d)[0], 2),
            "cpi": r(cpi, 1),
            "cpi_accel": r(cpi - cpi_prev, 1) if cpi is not None and cpi_prev is not None else None,
            "oil_chg": r(chg(F["WTISPLC"], d, 12, pct=True), 0),
            "unemp_chg": r(chg(F["UNRATE"], d), 1),
            "credit": r(at(F["BAA"], d)[0] - at(F["GS10"], d)[0], 2),
            "m2": r(chg(F["M2SL"], d, 12, pct=True), 1),
            "spx_12m": r(chg(spx, d, 12, pct=True), 0),
            "ma_dist": r((at(spx, d)[0] / at(ma200, d)[0] - 1) * 100, 1),
            "vol": r(at(vol, d)[0], 1) if vol is not None else None,
            "dollar_chg": r(chg(dollar, d, 12, pct=True), 1) if (k == "now" or d.year >= 1974) else None,
            "deficit": r(at(F["FYFSGDA188S"], d)[0], 1),
        }

    # 結局：見頂後最大跌幅、到谷底月數、收復月數
    outcome = {}
    for k in ("1973", "1987", "2000"):
        d = pd.Timestamp(eps[k])
        peak = at(spx, d)[0]
        after = spx[spx.index > d]
        rec = after[after >= peak]
        trough_win = after[: rec.index[0]] if len(rec) else after
        tdate = trough_win.idxmin()
        outcome[k] = {"max_dd": r((trough_win.min() / peak - 1) * 100, 0),
                      "months_to_trough": int(round((tdate - d).days / 30.44)),
                      "months_to_recover": int(round((rec.index[0] - d).days / 30.44)) if len(rec) else None,
                      "trough_date": tdate.date().isoformat()}

    # 相似度：每個量化指標用四期的全距正規化，距離越小越像
    keys = ["cape", "gap", "y10_chg", "ff_chg", "curve", "cpi", "cpi_accel", "oil_chg", "unemp_chg",
            "credit", "m2", "spx_12m", "ma_dist", "dollar_chg", "deficit"]
    sim, closest = {k: [] for k in ("1973", "1987", "2000")}, {}
    for key in keys:
        vals = {k: rows[k][key] for k in rows}
        now = vals["now"]
        hist = {k: v for k, v in vals.items() if k != "now" and v is not None}
        if now is None or not hist:
            continue
        span = max(list(hist.values()) + [now]) - min(list(hist.values()) + [now]) or 1
        dists = {k: abs(v - now) / span for k, v in hist.items()}
        closest[key] = min(dists, key=dists.get)
        for k, dist in dists.items():
            sim[k].append(1 - dist)
    similarity = {k: r(100 * np.mean(v), 0) for k, v in sim.items()}

    # ─── (3) 1987 時間軸（規則 3 何時成立）─────────────────────────────────────
    s87 = spx["1987-01-01":"1988-12-31"]
    m87 = ma200["1987-01-01":"1988-12-31"]
    vxo = F["VXOCLS"]
    first_below = s87[(s87 < m87) & (s87.index > "1987-08-25")].index[0]
    tl = []
    for d in ["1987-03-31", "1987-06-30", "1987-08-25", "1987-09-30", "1987-10-05", "1987-10-06", "1987-10-13",
              "1987-10-14", "1987-10-15", "1987-10-16", "1987-10-19", "1987-10-20", "1987-10-26", "1987-12-04"]:
        p, _ = at(spx, d)
        tl.append({"date": d, "spx": r(p, 2), "ma200": r(at(ma200, d)[0], 1),
                   "dd": r((p / at(spx, "1987-08-25")[0] - 1) * 100, 1),
                   "y10": r(at(F["DGS10"], d)[0], 2), "vxo": r(at(vxo, d)[0], 1)})
    back_above = s87[(s87 > m87) & (s87.index > "1987-10-19")]
    timeline87 = {"first_close_below_ma200": first_below.date().isoformat(),
                  "first_close_back_above_ma200": back_above.index[0].date().isoformat() if len(back_above) else None,
                  "rows": tl}

    # ─── (2) 系統性風險監控 ───────────────────────────────────────────────────
    def last(s):
        return at(s, today + pd.Timedelta(days=7))

    def dd_from_high(s, days=252):
        w = s[s.index > s.index[-1] - pd.Timedelta(days=int(days * 1.45))]
        return r((w.iloc[-1] / w.max() - 1) * 100, 1)

    yq = {t: yahoo(t, C) for t in ["^MOVE", "^SKEW", "^VIX3M", "BIZD", "ARCC", "OWL", "BX", "APO", "KKR",
                                   "BKLN", "SMH", "NVDA"]}
    vix_now = last(F["VIXCLS"])[0]
    sofr, iorb = last(F["SOFR"])[0], last(F["IORB"])[0]
    pc_basket = np.mean([dd_from_high(yq[t]) for t in ("OWL", "BX", "APO", "KKR")])
    monitor = {
        "asof": today.date().isoformat(),
        "values": {
            "y10": last(F["DGS10"]), "y30": last(F["DGS30"]),
            "gap": [r(last(F["DGS10"])[0] - 100 / km["cape"], 2), "CAPE " + str(km.get("cape"))] if km.get("cape") else [None, None],
            "move": last(yq["^MOVE"]), "curve_10y3m": last(F["T10Y3M"]),
            "sofr_iorb_bp": [r((sofr - iorb) * 100, 0), last(F["SOFR"])[1]],
            "reserves_tn": [r(last(F["WRESBAL"])[0] / 1e6, 2), last(F["WRESBAL"])[1]],
            "rrp_bn": [r(last(F["RRPONTSYD"])[0], 1), last(F["RRPONTSYD"])[1]],
            "vix": last(F["VIXCLS"]),
            "vix_term": [r(vix_now / last(yq["^VIX3M"])[0], 2), last(yq["^VIX3M"])[1]],
            "skew": last(yq["^SKEW"]),
            "hy_oas_bp": [r(last(F["BAMLH0A0HYM2"])[0] * 100, 0), last(F["BAMLH0A0HYM2"])[1]],
            "hy_oas_3m_chg_bp": r(chg(F["BAMLH0A0HYM2"], today, 3) * 100, 0),
            "ccc_oas_bp": [r(last(F["BAMLH0A3HYC"])[0] * 100, 0), last(F["BAMLH0A3HYC"])[1]],
            "ig_oas_bp": [r(last(F["BAMLC0A0CM"])[0] * 100, 0), last(F["BAMLC0A0CM"])[1]],
            "bizd_dd": dd_from_high(yq["BIZD"]), "arcc_dd": dd_from_high(yq["ARCC"]),
            "pc_mgr_dd": r(pc_basket, 1), "bkln_dd": dd_from_high(yq["BKLN"]),
            "smh_dd": dd_from_high(yq["SMH"]), "nvda_dd": dd_from_high(yq["NVDA"]),
            "smh_ma_dist": r((yq["SMH"].iloc[-1] / yq["SMH"].rolling(200).mean().iloc[-1] - 1) * 100, 1),
            "spx_ma_dist": r((spx.iloc[-1] / ma200.iloc[-1] - 1) * 100, 1),
            "usdjpy": last(F["DEXJPUS"]), "usdjpy_3m_chg": r(chg(F["DEXJPUS"], today, 3, pct=True), 1),
            "jgb10": last(F["IRLTLT01JPM156N"]),
            "brent_dated": last(F["DCOILBRENTEU"]), "wti": last(F["DCOILWTICO"]),
            "wti_12m_chg": r(chg(F["DCOILWTICO"], today, 12, pct=True), 0),
            "cpi_yoy": [r(chg(F["CPIAUCSL"], today, 12, pct=True), 1), last(F["CPIAUCSL"])[1]],
            "unemp": last(F["UNRATE"]), "unemp_12m_chg": r(chg(F["UNRATE"], today, 12), 1),
            "m2_yoy": [r(chg(F["M2SL"], today, 12, pct=True), 1), last(F["M2SL"])[1]],
            "nfci": last(F["NFCI"]), "stlfsi": last(F["STLFSI4"]),
            "dollar_3m_chg": r(chg(F["DTWEXBGS"], today, 3, pct=True), 1),
        },
    }

    out = {"generated": date.today().isoformat(), "analog": {"episodes": eps, "rows": rows, "outcome": outcome,
           "similarity": similarity, "closest": closest}, "timeline87": timeline87, "monitor": monitor}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o if not isinstance(o, tuple) else list(o))
    print(json.dumps(out, ensure_ascii=False, default=str)[:200], "...\n→", OUT)


if __name__ == "__main__":
    sys.exit(main())
