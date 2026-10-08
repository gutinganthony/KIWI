#!/usr/bin/env python3
"""
risk_dashboards_data.py — 兩個風險 dashboard 的資料層

(1) 歷史對照：1973 / 1987 / 2000 三次見頂當下 vs 今天，同一組指標並排，算出今天最像哪一次。
(2) 系統性風險監控：1987 年那類「結構性盲點」在今天的對應物（利率管線、機械式賣壓、
    私募信貸、AI 融資鏈、散戶槓桿、日圓、油價、集中度），每一點的現值、警戒線、狀態。
(3) 1987 年時間軸：見頂 → 跌破 200 日線 → 崩盤，驗證「規則 3 在 1987 何時成立」。

資料：FRED（fredgraph.csv，免金鑰）、Yahoo chart API、Shiller CAPE（GitHub 鏡像 datasets/s-and-p-500）。
今天的 CAPE 取 KIWI 儀表板（docs/index.html 的 market.cape）。
只用標準函式庫＋pandas。輸出：docs/risk/data.json（公開頁 docs/risk/index.html 讀取；每日由 update-dashboard.yml 更新）

用法：python scripts/risk_dashboards_data.py [--cache DIR]
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(ROOT))
OUT = os.path.join(REPO, "docs", "risk", "data.json")          # 公開頁 docs/risk/index.html 讀這個檔
DOCS_INDEX = os.path.join(REPO, "docs", "index.html")
# 沒有免費 API 的指標：每月手動更新（FINRA 融資餘額約每月中旬公布上月數字）
MANUAL = {"margin_debt": {"value": "1.50 兆美元（6 月紀錄）；7 月 −850 億", "asof": "2026-07", "status": "warn"},
          "top10_weight": {"value": "手動", "asof": None, "status": "na"},
          "nvda_dso": {"value": "53→51→45→60 天", "asof": "Q2 FY27（2026-07-26）", "status": "hot"}}
# FRED 會把 "Mozilla/5.0" 這種假瀏覽器 UA 拖到逾時（2026-10-08 實測）；Yahoo 反而要它。所以依網站分開設。
UA_YAHOO = {"User-Agent": "Mozilla/5.0"}
UA_DEFAULT = {"User-Agent": "KIWI-risk-board/1.0 (+https://github.com/gutinganthony/KIWI)"}


def _get(url, path, timeout=20):
    if path and os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            return f.read()
    headers = UA_YAHOO if "yahoo.com" in url else UA_DEFAULT
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
        raw = r.read()
    if path:
        with open(path, "wb") as f:
            f.write(raw)
    return raw


def fred(sid, cache):
    """有 FRED_API_KEY（GitHub runner）走官方 API，否則用免金鑰的 fredgraph.csv。"""
    key = os.environ.get("FRED_API_KEY", "").strip()
    path = os.path.join(cache, f"{sid}.csv") if cache else None
    if key and not (path and os.path.exists(path)):
        url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
               f"&api_key={key}&file_type=json&observation_start=1950-01-01")
        obs = json.loads(_get(url, None))["observations"]
        rows = [(o["date"], o["value"]) for o in obs]
    else:
        raw = _get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", path).decode()
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


def kiwi_data():
    try:
        html = open(DOCS_INDEX, encoding="utf-8").read()
        m = re.search(r"KIWI_DATA\s*=\s*(\{.*?\});", html, re.S)
        return json.loads(m.group(1)) if m else {}
    except Exception:
        return {}


def safe(fn, *a):
    """單一資料源失敗不擋整體（GitHub runner 偶爾被 Yahoo 429）。"""
    try:
        return fn(*a)
    except Exception as e:
        print(f"  ⚠️ {a[0] if a else fn.__name__} 失敗：{e}", file=sys.stderr)
        return None


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


EPISODES = {"1973": "1973-01-11", "1987": "1987-08-25", "2000": "2000-03-24"}
TOPS_ALL = ["1968-11-29", "1973-01-11", "1980-11-28", "1987-08-25", "1990-07-16", "2000-03-24",
            "2007-10-09", "2020-02-19", "2022-01-03"]


def fed_cycle(ff, cpi, nfci, d):
    """d 當下的 Fed 循環位置：36 個月內利率低點、距低點月數、升幅、實質政策利率、金融條件。"""
    d = pd.Timestamp(d)
    w = ff[d - pd.DateOffset(months=36):d]
    infl = chg(cpi, d, 12, pct=True)
    now = at(ff, d)[0]
    n = at(nfci, d)[0] if d >= nfci.index[0] else None
    return {"ff": r(now, 2), "ff_12m": r(chg(ff, d), 2), "trough": r(w.min(), 2),
            "trough_date": w.idxmin().strftime("%Y-%m"), "months_from_trough": int(round((d - w.idxmin()).days / 30.44)),
            "rise_from_trough": r(now - w.min(), 2), "real_ff": r(now - infl, 2) if infl is not None else None,
            "nfci": r(n, 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=None, help="下載快取目錄（可省略）")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    if a.cache:
        os.makedirs(a.cache, exist_ok=True)
    C = a.cache
    prev = {}
    if os.path.exists(a.out):
        try:
            prev = json.load(open(a.out, encoding="utf-8"))
        except Exception:
            prev = {}

    F = {}
    series = ["GS10", "FEDFUNDS", "CPIAUCSL", "UNRATE", "BAA", "M2SL", "WTISPLC", "TB3MS", "FYFSGDA188S",
              "TWEXMMTH", "DTWEXBGS", "DGS10", "DGS30", "VXOCLS", "VIXCLS", "BAMLH0A0HYM2", "BAMLC0A0CM",
              "BAMLH0A3HYC", "T10Y3M", "SOFR", "IORB", "RRPONTSYD", "WRESBAL", "DCOILBRENTEU", "DCOILWTICO",
              "DEXJPUS", "NFCI", "STLFSI4", "IRLTLT01JPM156N", "SP500"]
    # 並行下載：單一請求最多 20 秒，整批不會因為一個慢來源卡住整個 workflow
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = dict(zip(series, ex.map(lambda k: safe(fred, k, C), series)))
    for k in series:
        F[k] = res[k] if res[k] is not None else pd.Series(dtype=float)
    if not len(F["DGS10"]) or not len(F["FEDFUNDS"]):
        print("  ⚠️ FRED 關鍵序列抓不到，保留上次的 data.json 不覆寫", file=sys.stderr)
        return 0
    kd = kiwi_data()
    km = kd.get("market", {})
    cape_hist = safe(shiller, C)

    # S&P：Yahoo 有完整歷史；失敗就用 FRED SP500（只有近 10 年）算「現在」，歷史部分沿用上次結果
    spx_full = safe(yahoo, "^GSPC", C)
    spx = spx_full if spx_full is not None and len(spx_full) > 10000 else F["SP500"]
    hist_ok = spx is spx_full and cape_hist is not None
    today = max(spx.index[-1], F["DGS10"].index[-1]) if len(spx) else F["DGS10"].index[-1]
    ma200 = spx.rolling(200).mean()

    def last(s):
        return at(s, today + pd.Timedelta(days=7)) if len(s) else (None, None)

    # ─── (1) 歷史對照 ────────────────────────────────────────────────────────
    def row(d, cape_v):
        d = pd.Timestamp(d)
        y10 = at(F["DGS10"], d)[0] if d.year >= 1962 else at(F["GS10"], d)[0]
        if d >= F["DGS10"].index[-1] - pd.Timedelta(days=10):
            y10 = last(F["DGS10"])[0]
        cpi = chg(F["CPIAUCSL"], d, 12, pct=True)
        cpi_prev = chg(F["CPIAUCSL"], d - pd.DateOffset(months=12), 12, pct=True)
        is_now = d.year >= 2020
        dollar = F["DTWEXBGS"] if is_now else F["TWEXMMTH"]
        vol = F["VIXCLS"] if d.year >= 1990 else (F["VXOCLS"] if d.year >= 1986 else None)
        sp, mp = at(spx, d)[0], at(ma200, d)[0]
        fc = fed_cycle(F["FEDFUNDS"], F["CPIAUCSL"], F["NFCI"], d)
        return {
            "date": d.date().isoformat(), "cape": r(cape_v, 1),
            "gap": r(y10 - 100 / cape_v, 2) if cape_v and y10 else None, "y10": r(y10, 2),
            "y10_chg": r(chg(F["GS10"], d), 2), "ff_chg": fc["ff_12m"],
            "curve": r(at(F["GS10"], d)[0] - at(F["TB3MS"], d)[0], 2),
            "cpi": r(cpi, 1), "cpi_accel": r(cpi - cpi_prev, 1) if cpi is not None and cpi_prev is not None else None,
            "oil_chg": r(chg(F["WTISPLC"], d, 12, pct=True), 0), "unemp_chg": r(chg(F["UNRATE"], d), 1),
            "credit": r(at(F["BAA"], d)[0] - at(F["GS10"], d)[0], 2), "m2": r(chg(F["M2SL"], d, 12, pct=True), 1),
            "spx_12m": r(chg(spx, d, 12, pct=True), 0) if sp else None,
            "ma_dist": r((sp / mp - 1) * 100, 1) if sp and mp else None,
            "vol": r(at(vol, d)[0], 1) if vol is not None and len(vol) else None,
            "dollar_chg": r(chg(dollar, d, 12, pct=True), 1) if (is_now or d.year >= 1974) and len(dollar) else None,
            "deficit": r(at(F["FYFSGDA188S"], d)[0], 1),
            "real_ff": fc["real_ff"], "real_10y": r(y10 - cpi, 2) if cpi is not None and y10 else None,
            "nfci": fc["nfci"], "months_from_trough": fc["months_from_trough"], "rise_from_trough": fc["rise_from_trough"],
        }

    if hist_ok:
        rows = {k: row(d, at(cape_hist, pd.Timestamp(d).replace(day=1))[0]) for k, d in EPISODES.items()}
        outcome, paths = {}, {}
        for k, d in list(EPISODES.items()) + [("2008", "2007-10-09")]:
            d = pd.Timestamp(d)
            peak = at(spx, d)[0]
            after = spx[spx.index > d]
            rec = after[after >= peak]
            win = after[: rec.index[0]] if len(rec) else after
            outcome[k] = {"max_dd": r((win.min() / peak - 1) * 100, 0),
                          "months_to_trough": int(round((win.idxmin() - d).days / 30.44)),
                          "months_to_recover": int(round((rec.index[0] - d).days / 30.44)) if len(rec) else None}
            s = spx[d: d + pd.DateOffset(months=36)]
            wk = s.resample("W").last()
            m = ma200.reindex(wk.index)
            paths[k] = [[int((t - d).days), r((v / s.iloc[0] - 1) * 100, 1), bool(v < m[t])] for t, v in wk.items()]
        # 1987 日線（圖）與關鍵日
        w = spx["1986-10-01":"1988-07-29"]
        y10s, vxo = F["DGS10"], F["VXOCLS"]
        chart87 = [[t.strftime("%Y-%m-%d"), r(v, 2), r(ma200[t], 2), r(at(y10s, t)[0], 2), r(at(vxo, t)[0], 1)]
                   for t, v in w.items()]
        s87, m87 = spx["1987-08-26":"1988-12-31"], ma200["1987-08-26":"1988-12-31"]
        fb = s87[s87 < m87].index[0]
        tl = []
        for t in ["1987-03-31", "1987-06-30", "1987-08-25", "1987-09-30", "1987-10-05", "1987-10-06", "1987-10-13",
                  "1987-10-14", "1987-10-15", "1987-10-16", "1987-10-19", "1987-10-20", "1987-10-26", "1987-12-04"]:
            p = at(spx, t)[0]
            tl.append({"date": t, "spx": r(p, 2), "ma200": r(at(ma200, t)[0], 1),
                       "dd": r((p / at(spx, "1987-08-25")[0] - 1) * 100, 1),
                       "y10": r(at(y10s, t)[0], 2), "vxo": r(at(vxo, t)[0], 1)})
        tops = [{"top": t, **fed_cycle(F["FEDFUNDS"], F["CPIAUCSL"], F["NFCI"], t)} for t in TOPS_ALL]
        hist = {"rows": rows, "outcome": outcome, "paths": paths, "chart87": chart87,
                "timeline87": {"first_close_below_ma200": fb.date().isoformat(), "rows": tl}, "tops_fed": tops}
    else:
        hist = prev.get("hist", {})
        print("  ⚠️ 歷史資料源不完整，沿用上次的歷史對照", file=sys.stderr)
        if not hist:
            raise SystemExit("沒有歷史資料可用（首次執行需要 Yahoo ^GSPC 與 Shiller CAPE）")

    now_row = row(today, km.get("cape"))
    keys = ["cape", "gap", "y10_chg", "ff_chg", "curve", "cpi", "cpi_accel", "oil_chg", "unemp_chg", "credit", "m2",
            "spx_12m", "ma_dist", "dollar_chg", "deficit", "real_ff", "real_10y", "nfci"]
    sim, closest = {k: [] for k in EPISODES}, {}
    for key in keys:
        nowv = now_row.get(key)
        hv = {k: hist["rows"][k].get(key) for k in EPISODES if hist["rows"][k].get(key) is not None}
        if nowv is None or not hv:
            continue
        allv = list(hv.values()) + [nowv]
        span = (max(allv) - min(allv)) or 1
        dists = {k: abs(v - nowv) / span for k, v in hv.items()}
        closest[key] = min(dists, key=dists.get)
        for k, dist in dists.items():
            sim[k].append(1 - dist)
    similarity = {k: r(100 * np.mean(v), 0) for k, v in sim.items() if v}

    # ─── (2) 系統性風險監控 ───────────────────────────────────────────────────
    def dd_from_high(s, days=252):
        if s is None or not len(s):
            return None
        w = s[s.index > s.index[-1] - pd.Timedelta(days=int(days * 1.45))]
        return r((w.iloc[-1] / w.max() - 1) * 100, 1)

    def ylast(s):
        return (r(s.iloc[-1], 2), s.index[-1].date().isoformat()) if s is not None and len(s) else (None, None)

    tks = ["^MOVE", "^SKEW", "^VIX3M", "BIZD", "ARCC", "OWL", "BX", "APO", "KKR", "BKLN", "SMH", "NVDA"]
    with ThreadPoolExecutor(max_workers=6) as ex:
        yq = dict(zip(tks, ex.map(lambda t: safe(yahoo, t, C), tks)))
    vix_now = last(F["VIXCLS"])[0]
    sofr, iorb = last(F["SOFR"])[0], last(F["IORB"])[0]
    pcs = [x for x in (dd_from_high(yq[t]) for t in ("OWL", "BX", "APO", "KKR")) if x is not None]
    smh = yq["SMH"]
    v = {
        "y10": last(F["DGS10"]), "y30": last(F["DGS30"]),
        "gap": now_row["gap"], "move": ylast(yq["^MOVE"]), "curve_10y3m": last(F["T10Y3M"]),
        "sofr_iorb_bp": r((sofr - iorb) * 100, 0) if sofr is not None and iorb is not None else None,
        "reserves_tn": r(last(F["WRESBAL"])[0] / 1e6, 2) if last(F["WRESBAL"])[0] else None,
        "rrp_bn": r(last(F["RRPONTSYD"])[0], 1),
        "vix": last(F["VIXCLS"]),
        "vix_term": r(vix_now / ylast(yq["^VIX3M"])[0], 2) if vix_now and ylast(yq["^VIX3M"])[0] else None,
        "skew": ylast(yq["^SKEW"]),
        "hy_oas_bp": r(last(F["BAMLH0A0HYM2"])[0] * 100, 0),
        "hy_oas_3m_chg_bp": r(chg(F["BAMLH0A0HYM2"], today, 3) * 100, 0),
        "ccc_oas_bp": r(last(F["BAMLH0A3HYC"])[0] * 100, 0), "ig_oas_bp": r(last(F["BAMLC0A0CM"])[0] * 100, 0),
        "bizd_dd": dd_from_high(yq["BIZD"]), "arcc_dd": dd_from_high(yq["ARCC"]),
        "pc_mgr_dd": r(np.mean(pcs), 1) if pcs else None, "bkln_dd": dd_from_high(yq["BKLN"]),
        "smh_dd": dd_from_high(smh), "nvda_dd": dd_from_high(yq["NVDA"]),
        "smh_ma_dist": r((smh.iloc[-1] / smh.rolling(200).mean().iloc[-1] - 1) * 100, 1) if smh is not None else None,
        "spx": r(at(spx, today)[0], 2), "spx_ma200": r(at(ma200, today)[0], 1),
        "spx_ma_dist": now_row["ma_dist"],
        "usdjpy": last(F["DEXJPUS"]), "usdjpy_3m_chg": r(chg(F["DEXJPUS"], today, 3, pct=True), 1),
        "jgb10": last(F["IRLTLT01JPM156N"]),
        "brent_dated": last(F["DCOILBRENTEU"]), "wti": last(F["DCOILWTICO"]),
        "wti_12m_chg": r(chg(F["DCOILWTICO"], today, 12, pct=True), 0),
        "cpi_yoy": now_row["cpi"], "unemp": last(F["UNRATE"]), "m2_yoy": now_row["m2"],
        "nfci": last(F["NFCI"]), "stlfsi": last(F["STLFSI4"]),
        "fed": fed_cycle(F["FEDFUNDS"], F["CPIAUCSL"], F["NFCI"], today),
        "real_10y": now_row["real_10y"],
    }
    kiwi = {k: (kd.get(k) or {}).get("score") for k in ("cri", "avi", "tsi")}
    kiwi["updated"] = kd.get("updated")

    out = {"generated": date.today().isoformat(), "asof": today.date().isoformat(), "kiwi": kiwi,
           "hist": hist, "now": now_row, "similarity": similarity, "closest": closest,
           "monitor": v, "manual": MANUAL}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"), default=lambda o: list(o) if isinstance(o, tuple) else str(o))
    print(f"✓ {a.out}  asof={out['asof']}  similarity={similarity}  hist_ok={hist_ok}")


if __name__ == "__main__":
    sys.exit(main())
