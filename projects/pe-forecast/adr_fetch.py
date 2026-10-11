#!/usr/bin/env python3
"""外國公司（ADR）與 now_all.csv 沒涵蓋的大型股：從 Yahoo 抓資料 → data/adr_now.csv，並做 12 個月小型回測。

    python3 adr_fetch.py --raw <原始資料目錄>              # 抓資料（有快取，預設 72 小時內不重抓）→ 產出全部檔案
    python3 adr_fetch.py --raw <原始資料目錄> --offline    # 只用已下載的原始資料重算

為什麼要這支：模型的 now_all.csv 只涵蓋有 SEC XBRL 季報的公司。外國公司申報 20-F／6-K（沒有 XBRL 季報），
所以改用 Yahoo：股價／股利／分割（chart）、GAAP 稀釋 EPS 歷史（fundamentals-timeseries）、共識與口徑資訊（quoteSummary）。

名單：選股器快照（data/consensus_snapshots/yahoo_*.csv.gz 最新一份）裡「financialCurrency ≠ USD」或「不在 now_all.csv」的公司，
      剔除特別股（代號 -P?）與同一家公司的另一類股（BRK-A、PBR-A、HEI-A…：代號 '-' 前相同者只留市值最大的一檔），取市值前 --top 大；
      再加上 data/ndx_members_jan1.csv 2026 年名單裡不在 now_all 的全部。

口徑（每 ADR、美元）——每一檔都驗證，結果寫在 conv_ok／conv_note：
  (a) eps0＝Yahoo 的美元 GAAP 最近四季（defaultKeyStatistics.trailingEps，與選股器 epsTrailingTwelveMonths 同源；
      10/07 快照後若有變動會在 conv_note 註明），驗證 eps0 ≈ 股價 ÷ summaryDetail.trailingPE（差 < 3%；虧損股沒有 trailingPE，略過）。
  (b) conv_factor ＝ eps0 ÷ timeseries 最近四季 EPS 最新值（Yahoo 原始幣別、原始股數口徑；連續四季加總優先，見 ttm_history），
      檢查 conv_factor × 匯率（當地幣別／美元，Yahoo <幣別>=X，現價或近 12 個月平均）≈ ADR 比率：
      比率 1 容許 6%（Yahoo 美元 TTM 多用歷史匯率），其他比率（2、5、1/2…）要 2% 內（避免巧合湊上，FMX、FER 就是這樣被擋）。
      timeseries 最新一期和 mostRecentQuarter 差 > 20 天（Yahoo 還沒更新）→ 不過。實測通過的全部是比率 1（Yahoo timeseries 已是每 ADR）。
      這個比率也用在回測的歷史 EPS：當地 EPS × 比率 ÷ 當月匯率。
  (c) 共識（earningsTrend 0y、+1y 平均；幣別看 earningsEstimate.earningsCurrency）：
      USD → 直接用（要和 Yahoo forwardEps 差 < 10%，或 earningsHistory 最近四季 ÷ eps0 在 0.5～2，確認是每 ADR）；
      ＝財報幣別且 (b) 過 → × conv_factor（「共識 ÷ eps0」因此不受匯率影響），要 street÷timeseries 在 0.6～1.67 或換算後對得上 forwardEps；
      其他（含 (b) 沒過）→ 只有「÷ 現匯後和 forwardEps 差 < 10%」才採用；都不行 → NaN。+1y÷0y 超出 0.4～2.5 會加 ⚠。
  conv_ok＝(a) 與 (b) 都過（eps0 與歷史 EPS 可信）；共識另外在 conv_note 註明。
  其他：最後成交距今 > 10 天（EA 2026-08 被收購下市）不列入；chart 的股利紀錄在 2025 年起對日本 ADR、HDB、KB、NOK 等中斷，
  近 12 個月股利 < summaryDetail.dividendYield 的一半時改用 dividendYield（回測也用它當固定近似）。
  分類 grp：data/universe*.csv 有的代號用 repo 的分類，否則用 Yahoo 產業（IND_SECTOR；SKHY 等記憶體歸 memory）。

回測（README §16 的三種預測，12 個月）：起點 2023-10～2025-09，目標日＝12 個月後（≤ 2026-09），
  只用 conv_ok、今天 EPS > 0 且 12 個月後 EPS > 0 的列。EPS＝起點（目標日）那天已公布的最近四季（季末 +45 天、年度 +75 天才算公布，
  最近一期超過 270 天就當缺）。timeseries 只有 2023 年中以後的 TTM，所以 2023-10 起點幾乎都缺。
  timeseries 的 EPS 沒有回溯分割調整（CNQ 2024-06 一拆二前後 6.76 → 3.515），EPS0～EPS1 之間有分割／ADR 比率變動的列剔除。
  誤差＝ln(預測 ÷ 實際股價)，報中位 |誤差|：
    本益比不變：預測＝p0 × EPS1 ÷ EPS0                     → e＝ln(EPS1/EPS0) − ln(p1/p0)
    軌道：      預測＝p0 × exp(y10 + 0.05 − dy)              → e＝(y10 + 0.05 − dy) − ln(p1/p0)
    模型：      預測＝軌道 × exp(β × ln(EPS1/EPS0))          → e＝軌道誤差 + β × clip(ln(EPS1/EPS0), −2, 2)
  β＝results/orbit_model.json 的 h["12"]["beta"]["原始成長a"][grp][0]；y10＝data/rates_monthly.csv 起點月的 DGS10/100；
  dy＝起點前 12 個月的每 ADR 股利 ÷ p0。和 S&P 500 同期（起點 2024-10～2025-09；results/orbit_recent_scores.csv、
  orbit_recent_rows.csv.gz）對照，另附「扣掉每月共同偏離」與匯率拆解。

輸出：data/adr_now.csv、data/adr_hist.csv.gz（回測用的月資料）、results/adr_backtest.txt。
請求：UA 只用一般瀏覽器字串，不帶任何個資；請求間隔 ≥ --pause 秒（預設 0.7），429 依序退避 5／15／45／90 秒。
不訓練任何模型、不平行。
"""
import argparse
import glob
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import consensus as cs                          # noqa: E402
from pef.orbit import GROUPS, GNAME                      # noqa: E402

DATA, RES = os.path.join(HERE, "data"), os.path.join(HERE, "results")
UA = {"User-Agent": "Mozilla/5.0"}
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}?range=5y&interval=1mo&events=div%2Csplit"
TS_TYPES = "trailingDilutedEPS,quarterlyDilutedEPS,annualDilutedEPS"
TS_URL = "https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{}?type={}&period1={}&period2={}"
QS_MODULES = "assetProfile,summaryDetail,price,financialData,defaultKeyStatistics,earningsTrend,earningsHistory"
QS_URL = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{}?modules={}&crumb={}"
SUB_UNIT = {"GBp": ("GBP", 100.0), "GBX": ("GBP", 100.0), "ZAc": ("ZAR", 100.0), "ILA": ("ILS", 100.0)}
# Yahoo 產業 → 模型的類型代碼（pef/orbit.py GROUPS）。data/universe*.csv 有的代號優先用 repo 的分類。
IND_SECTOR = {"Semiconductors": "semis", "Semiconductor Equipment & Materials": "semicap",
              "Software - Application": "software", "Software - Infrastructure": "software",
              "Internet Content & Information": "internet", "Internet Retail": "internet",
              "Information Technology Services": "itservices",
              "Computer Hardware": "hardware", "Communication Equipment": "hardware", "Consumer Electronics": "hardware",
              "Electronic Components": "hardware", "Scientific & Technical Instruments": "hardware",
              "Electronics & Computer Distribution": "gics_it", "Solar": "gics_it"}
MEMORY = {"SKHY", "MU", "WDC", "STX", "SNDK"}            # 記憶體／儲存（模型把 MU、WDC、STX 歸 memory）
NICE = sorted({float(n) for n in (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 100)}
              | {1.0 / n for n in (2, 3, 4, 5, 6, 8, 10, 20, 25, 50, 100)} | {0.4, 2.5, 1.5, 2.0 / 3})
PAUSE = [0.7]
_last = [0.0]
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


# ───────────────────────────── 網路（快取、間隔、429 退避） ─────────────────────────────
def _fetch(url, opener=None):
    for wait in (5, 15, 45, 90, None):
        dt = time.time() - _last[0]
        if dt < PAUSE[0]:
            time.sleep(PAUSE[0] - dt)
        _last[0] = time.time()
        try:
            if opener is not None:
                return json.load(opener.open(url, timeout=30))
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
        except urllib.error.HTTPError as e:
            if e.code == 429 and wait is not None:
                print(f"    429 → 等 {wait} 秒")
                time.sleep(wait)
                continue
            if e.code == 404:
                return {"_error": 404}
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            if wait is not None:
                print(f"    {type(e).__name__} → 等 {wait} 秒")
                time.sleep(wait)
                continue
            raise
    return None


def cached(path, url_fn, offline, max_age_h, opener_fn=None):
    """有新鮮快取就讀；否則抓（url_fn 可能需要 crumb，所以延後組）。失敗回傳 None。"""
    if os.path.exists(path) and (offline or time.time() - os.path.getmtime(path) < max_age_h * 3600):
        return json.load(open(path))
    if offline:
        return None
    try:
        op = opener_fn() if opener_fn else None
        raw = _fetch(url_fn(), op)
    except Exception as e:                               # noqa: BLE001 — 單檔失敗不影響其他
        print(f"    失敗：{type(e).__name__} {e}")
        return None
    if raw is not None:
        json.dump(raw, open(path, "w"))
    return raw


def _qs_opener():
    op, crumb = cs._qs_session()
    if op is None:
        raise RuntimeError("拿不到 quoteSummary 的 cookie／crumb")
    return op


def fetch_all(syms, ccys, raw_dir, offline, max_age_h, log=print):
    os.makedirs(raw_dir, exist_ok=True)
    p1, p2 = int(pd.Timestamp("2018-01-01").timestamp()), int(time.time()) + 86400
    for i, s in enumerate(syms):
        ys = urllib.parse.quote(s)
        log(f"  [{i + 1}/{len(syms)}] {s}")
        cached(os.path.join(raw_dir, f"{s}_5y_1mo.json"), lambda: CHART_URL.format(ys), offline, max_age_h)
        cached(os.path.join(raw_dir, f"{s}_ts.json"), lambda: TS_URL.format(ys, TS_TYPES, p1, p2), offline, max_age_h)
        cached(os.path.join(raw_dir, f"{s}_qs.json"),
               lambda: QS_URL.format(ys, QS_MODULES, urllib.parse.quote(cs._qs_session()[1])), offline, max_age_h, _qs_opener)
    for c in sorted(ccys):
        log(f"  匯率 {c}=X")
        cached(os.path.join(raw_dir, f"{c}=X_5y_1mo.json"), lambda: CHART_URL.format(urllib.parse.quote(f"{c}=X")),
               offline, max_age_h)


# ───────────────────────────── 解析 ─────────────────────────────
def load(path):
    return json.load(open(path)) if os.path.exists(path) else None


def parse_chart(raw):
    """→ dict(close＝月底收盤（月底日期索引；最後一筆＝本月至今）, div, split, px, px_time, currency)；失敗 None。"""
    try:
        r = raw["chart"]["result"][0]
        # 月線時間戳是「交易所當地月初 00:00」：匯率（Europe/London）夏令時間是前一天 23:00 UTC，
        # 直接用 UTC 會整個月份錯位（實測 EUR=X：2025-10 那根 K 棒的時間戳是 2025-09-30 23:00 UTC）→ 先轉成交易所時區
        tz = (r.get("meta") or {}).get("exchangeTimezoneName") or "UTC"
        ts = pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert(tz).tz_localize(None)
        close = pd.Series(r["indicators"]["quote"][0]["close"], index=ts, dtype=float).dropna()
    except (KeyError, TypeError, IndexError):
        return None
    close.index = close.index.normalize() + pd.offsets.MonthEnd(0)
    close = close.groupby(level=0).last()
    ev = r.get("events") or {}
    div = pd.Series({pd.to_datetime(v["date"], unit="s"): v["amount"] for v in (ev.get("dividends") or {}).values()},
                    dtype=float).sort_index()
    spl = pd.Series({pd.to_datetime(v["date"], unit="s"): v["numerator"] / v["denominator"]
                     for v in (ev.get("splits") or {}).values()}, dtype=float).sort_index()
    if div.empty:
        div = pd.Series([], index=pd.DatetimeIndex([]), dtype=float)
    if spl.empty:
        spl = pd.Series([], index=pd.DatetimeIndex([]), dtype=float)
    m = r.get("meta", {})
    return dict(close=close, div=div, split=spl, px=m.get("regularMarketPrice"),
                px_time=pd.to_datetime(m.get("regularMarketTime"), unit="s") if m.get("regularMarketTime") else None,
                currency=m.get("currency"))


def parse_ts(raw):
    """→ {type: DataFrame(date, value, ccy, ptype)}。"""
    out = {}
    for r in ((raw or {}).get("timeseries") or {}).get("result") or []:
        t = (r.get("meta") or {}).get("type", [None])[0]
        rows = [dict(date=pd.Timestamp(x["asOfDate"]), value=float(x["reportedValue"]["raw"]), ccy=x.get("currencyCode"),
                     ptype=x.get("periodType")) for x in (r.get(t) or []) if x and x.get("reportedValue")]
        if t:
            out[t] = pd.DataFrame(rows, columns=["date", "value", "ccy", "ptype"]).sort_values("date").reset_index(drop=True)
    return out


def ttm_history(ts):
    """最近四季 GAAP 稀釋 EPS 的歷史（Yahoo 原始幣別、原始口徑）。
    來源優先序：連續四季加總（quarterlyDilutedEPS，只有最近 5 季）＞ trailingDilutedEPS ＞ 年度（＝年底那一季的 TTM）。
    四季加總優先，因為實測 trailingDilutedEPS 偶有自相矛盾（ASML 2026-06-30：trailing 25.41，但四季 5.48+7.34+7.15+7.58＝27.55，
    與 earningsHistory、Yahoo 美元 TTM 都對得上的是 27.55）。兩者差 > 2% 時記在 src 欄（"4q≠trailing"）。"""
    pts = {}
    q = ts.get("quarterlyDilutedEPS")
    if q is not None and len(q) >= 4:
        for i in range(3, len(q)):
            k = q.iloc[i - 3:i + 1]
            if k["date"].diff().dt.days.iloc[1:].between(80, 100).all() and k["ccy"].nunique() == 1:
                pts[k["date"].iloc[-1]] = (float(k["value"].sum()), k["ccy"].iloc[-1], "4q")
    near = lambda d: next((k for k in pts if abs((d - k).days) <= 10), None)
    tr = ts.get("trailingDilutedEPS")
    if tr is not None:
        for r in tr.itertuples():
            k = near(r.date)
            if k is None:
                pts[r.date] = (r.value, r.ccy, "trailing")
            elif abs(pts[k][0] - r.value) > 0.02 * max(abs(r.value), 1e-9):
                pts[k] = (pts[k][0], pts[k][1], f"4q≠trailing({r.value:g})")
    an = ts.get("annualDilutedEPS")
    if an is not None:
        for r in an.itertuples():
            if near(r.date) is None:
                pts[r.date] = (r.value, r.ccy, "annual")
    d = pd.DataFrame([dict(date=k, eps_loc=v[0], ccy=v[1], src=v[2]) for k, v in pts.items()],
                     columns=["date", "eps_loc", "ccy", "src"])
    return d.sort_values("date").reset_index(drop=True)


def num(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return np.nan
    return v if np.isfinite(v) else np.nan


def raw_(d, k):
    v = (d or {}).get(k)
    return v.get("raw") if isinstance(v, dict) else v


def fx_series(raw_dir, ccy):
    """當地幣別／美元：月底收盤序列＋現價。USD → 1。"""
    if ccy in (None, "USD"):
        return None, 1.0
    base, div = SUB_UNIT.get(ccy, (ccy, 1.0))
    c = parse_chart(load(os.path.join(raw_dir, f"{base}=X_5y_1mo.json")))
    if c is None or not c["px"]:
        return None, np.nan
    return c["close"] * div, float(c["px"]) * div


def nearest_nice(x):
    if not (np.isfinite(x) and x > 0):
        return np.nan, np.inf
    n = min(NICE, key=lambda v: abs(np.log(x / v)))
    return n, abs(np.log(x / n))


# ───────────────────────────── 名單 ─────────────────────────────
def known_tickers():
    n = pd.read_csv(os.path.join(RES, "now_all.csv"), usecols=["ticker", "aliases"])
    k = set(n["ticker"].astype(str).str.upper().str.replace(".", "-", regex=False))
    for a in n["aliases"].dropna():
        k |= {x.upper().replace(".", "-") for x in str(a).split()}
    return k


def latest_snapshot_file():
    f = sorted(f for f in glob.glob(os.path.join(DATA, "consensus_snapshots", "yahoo_*.csv.gz")) if "detail" not in f)
    return f[-1]


def pick_names(snap, top):
    known = known_tickers()
    s = snap.copy()
    s["sym"] = s["symbol"].astype(str).str.upper()
    s = s[~s["sym"].str.contains(r"-P[A-Z]?$", regex=True)]              # 特別股（WFC-PC…）
    s = s[(s["financialCurrency"].fillna("USD") != "USD") | (~s["sym"].isin(known))].sort_values("marketCap", ascending=False)
    keep, bases, dropped = [], set(), []
    for r in s.itertuples():
        b = r.sym.split("-")[0]
        if b in bases or (b != r.sym and b in known):                     # 同公司另一類股
            dropped.append(r.sym)
            continue
        bases.add(b)
        keep.append(r.sym)
    top_list = keep[:top]
    nd = pd.read_csv(os.path.join(DATA, "ndx_members_jan1.csv"))
    ndx = [t.upper().replace(".", "-") for t in nd.loc[nd["year"] == 2026, "ticker"]]
    ndx_add = [t for t in ndx if t not in known]
    names = top_list + [t for t in ndx_add if t not in top_list]
    return names, ndx_add, dropped


# ───────────────────────────── 每一檔「今天」 ─────────────────────────────
def repo_sector():
    out = {}
    for f in ("universe_sp500.csv", "universe_ext.csv", "universe.csv"):         # 後讀的優先
        p = os.path.join(DATA, f)
        if os.path.exists(p):
            u = pd.read_csv(p, keep_default_na=False)
            out.update({str(t).upper().replace(".", "-"): s for t, s in zip(u["ticker"], u["sector"]) if s})
    return out


def sector_of(sym, industry, rsec):
    if sym in rsec:
        return rsec[sym], "repo"
    if sym in MEMORY:
        return "memory", "yahoo"
    return IND_SECTOR.get(str(industry), "other"), "yahoo"


def now_row(sym, snap_row, raw_dir, rates, rsec, asof):
    note = []
    ch = parse_chart(load(os.path.join(raw_dir, f"{sym}_5y_1mo.json")))
    qsraw = load(os.path.join(raw_dir, f"{sym}_qs.json"))
    try:
        q = qsraw["quoteSummary"]["result"][0]
    except (TypeError, KeyError, IndexError):
        q = None
    ts = parse_ts(load(os.path.join(raw_dir, f"{sym}_ts.json")))
    if ch is None or not ch["px"] or q is None:
        return None, f"{sym}：{'沒有股價' if ch is None or not ch['px'] else '沒有 quoteSummary'}，跳過"
    pr, sd, ks = q.get("price") or {}, q.get("summaryDetail") or {}, q.get("defaultKeyStatistics") or {}
    fd, ap = q.get("financialData") or {}, q.get("assetProfile") or {}
    px = float(raw_(pr, "regularMarketPrice") or ch["px"])
    pt = raw_(pr, "regularMarketTime")
    price_date = (pd.Timestamp(int(pt), unit="s") if pt else ch["px_time"]).date()
    if (asof - pd.Timestamp(price_date)).days > 10:
        return None, f"{sym}：最後成交 {price_date}，已停止交易（下市／被收購），跳過"
    fin = raw_(fd, "financialCurrency") or (snap_row.get("financialCurrency") if snap_row is not None else None) or "USD"
    industry = ap.get("industry") or ""
    sec, sec_src = sector_of(sym, industry, rsec)
    grp = GROUPS.get(sec, "other")
    # (a) eps0 與 trailingPE
    eps_ks = raw_(ks, "trailingEps")
    eps_scr = snap_row.get("epsTrailingTwelveMonths") if snap_row is not None else None
    eps0 = float(eps_ks) if eps_ks is not None else (float(eps_scr) if eps_scr is not None and np.isfinite(eps_scr) else np.nan)
    tpe = raw_(sd, "trailingPE")
    a_ok = False
    if tpe and np.isfinite(eps0) and eps0 > 0:
        d = abs(np.log(eps0 / (px / tpe)))
        a_ok = d < np.log(1.03)
        note.append(f"(a) 股價÷trailingPE={px / tpe:.3f} vs eps0={eps0:.3f}（差 {np.exp(d) - 1:.1%}）{'過' if a_ok else '不過'}")
    elif np.isfinite(eps0) and eps0 <= 0:
        a_ok = True                                  # 虧損：Yahoo 不給 trailingPE，只能靠 (b)
        note.append("(a) 虧損，無 trailingPE 可驗")
    else:
        note.append("(a) 缺 trailingPE 或 eps0")
    if eps_scr is not None and np.isfinite(eps_scr) and np.isfinite(eps0) and abs(eps_scr - eps0) > 0.02 * max(abs(eps0), 0.01):
        note.append(f"選股器 TTM {eps_scr} ≠ 即時 {eps0}（10/07 後有新財報？）")
    # (b) 換算係數
    th = ttm_history(ts)
    mrq = raw_(ks, "mostRecentQuarter")
    mrq = pd.Timestamp(int(mrq), unit="s").normalize() if mrq else None
    period_end = mrq if mrq is not None else (th["date"].iloc[-1] if len(th) else None)
    conv, ratio, b_ok, ts_ccy, ts_last = np.nan, np.nan, False, None, np.nan
    fx_now = np.nan
    if len(th):
        last = th.iloc[-1]
        ts_ccy, ts_last = last["ccy"] or fin, float(last["eps_loc"])
        fxs, fx_now = fx_series(raw_dir, ts_ccy)
        stale = mrq is not None and abs((last["date"] - mrq).days) > 20
        if stale:
            note.append(f"(b) timeseries 最新 {last['date'].date()} 與 mostRecentQuarter {mrq.date()} 不同期")
        if np.isfinite(eps0) and abs(ts_last) > 1e-9 and np.isfinite(fx_now) and not stale and np.sign(ts_last) == np.sign(eps0):
            conv = eps0 / ts_last
            fx12 = float(fxs.iloc[-13:-1].mean()) if fxs is not None and len(fxs) > 13 else fx_now
            cand = [(nearest_nice(conv * f), f) for f in (fx_now, fx12)]
            (ratio, dev), fxu = min(cand, key=lambda c: c[0][1])
            # 比率 1（Yahoo 的 timeseries 幾乎都已是「每 ADR」）容許 6%（匯率換算時點不同）；其他比率要 2% 內，避免巧合湊上
            b_ok = dev < (np.log(1.06) if ratio == 1 else np.log(1.02))
            note.append(f"(b) 係數={conv:.5g}（{ts_ccy}→USD/ADR），×匯率 {fxu:.4g}＝{conv * fxu:.3f} ≈ 比率 {ratio:g}（差 {np.exp(dev) - 1:.1%}）"
                        f"{'過' if b_ok else '不過'}")
        elif not stale:
            note.append(f"(b) 無法算係數（eps0={eps0}, ts={ts_last}, 匯率={fx_now}）")
    else:
        note.append("(b) 沒有 timeseries EPS")
    conv_ok = bool(a_ok and b_ok)
    # (c) 共識
    trend = {t.get("period"): t for t in ((q.get("earningsTrend") or {}).get("trend") or [])}
    cons, cons_note = {}, []
    hist = [(raw_(h, "quarter"), raw_(h, "epsActual"), h.get("currency")) for h in ((q.get("earningsHistory") or {}).get("history") or [])]
    hist = sorted([h for h in hist if h[0] and h[1] is not None])[-4:]
    street = sum(h[1] for h in hist) if len(hist) == 4 else np.nan
    feps = num(raw_(ks, "forwardEps"))                    # Yahoo 的 forwardEps：美元／ADR、以現匯換算（forwardPE＝股價÷它）
    raw_cons = {}
    for per in ("0y", "+1y"):
        e = (trend.get(per) or {}).get("earningsEstimate") or {}
        raw_cons[per] = (num(raw_(e, "avg")), raw_(e, "earningsCurrency"))
    match_f = lambda vals: np.isfinite(feps) and feps > 0 and any(np.isfinite(v) and v > 0 and abs(np.log(v / feps)) < np.log(1.10)
                                                                   for v in vals)
    ccys_c = {c for _, c in raw_cons.values() if c}
    c_ccy = ccys_c.pop() if len(ccys_c) == 1 else None
    if len(ccys_c) > 1:
        cons_note.append(f"0y／+1y 幣別不同（{'、'.join(sorted(ccys_c | {c_ccy} - {None}))}）→不用")
    vals = [v for v, _ in raw_cons.values()]
    factor, how = np.nan, None
    if c_ccy == "USD":
        street_ok = np.isfinite(street) and np.isfinite(eps0) and eps0 > 0 and street > 0 and 0.5 < street / eps0 < 2.0
        if match_f(vals) or street_ok:
            factor, how = 1.0, "美元，" + ("和 forwardEps 對得上" if match_f(vals) else "street 最近四季與 eps0 同量級")
        elif not (np.isfinite(feps) or np.isfinite(street)):
            factor, how = 1.0, "美元（無法交叉驗證）"
        else:
            cons_note.append(f"美元共識但 forwardEps={feps}、street/eps0={street / eps0 if eps0 else np.nan:.2f}（股數口徑不同？）→不用")
    elif c_ccy is not None and c_ccy == ts_ccy and b_ok and np.isfinite(conv):
        basis_ok = np.isfinite(street) and street > 0 and ts_last > 0 and 0.6 < street / ts_last < 1 / 0.6
        if basis_ok or match_f([v * conv for v in vals]):
            factor, how = conv, f"{c_ccy}×係數 {conv:.5g}（" + ("street/timeseries 同股數口徑" if basis_ok else "換算後和 forwardEps 對得上") + "）"
        else:
            cons_note.append(f"{c_ccy}：street/ts={street / ts_last if ts_last else np.nan:.2f} 且換算後和 forwardEps 對不上→不用")
    elif c_ccy is not None:
        _, fxc = fx_series(raw_dir, c_ccy)              # 係數不過（或幣別不同）：只在「現匯換算後和 Yahoo forwardEps 對得上」時採用
        if np.isfinite(fxc) and match_f([v / fxc for v in vals]):
            factor, how = 1.0 / fxc, f"{c_ccy}÷現匯 {fxc:.4g}（係數未過，但換算後和 forwardEps 對得上）"
        else:
            cons_note.append(f"{c_ccy}（timeseries {ts_ccy}）{'係數不過，' if not b_ok else ''}換算後和 forwardEps 對不上→不用")
    cons = {"cons_0y": raw_cons["0y"][0] * factor, "cons_1y": raw_cons["+1y"][0] * factor}
    c0, c1 = cons["cons_0y"], cons["cons_1y"]
    if np.isfinite(c0) and np.isfinite(c1) and c0 > 0 and c1 > 0 and not (0.4 < c1 / c0 < 2.5):
        cons_note.append(f"⚠ +1y÷0y＝{c1 / c0:.2f}，落差異常，用前請人工確認")
    if how:
        cons_note.insert(0, how)
    note.append("(c) 共識 " + ("；".join(cons_note) if cons_note else "（Yahoo 沒有）"))
    if sec_src == "yahoo" and grp != "other":
        note.append(f"類型依 Yahoo 產業「{industry}」")
    # 股利殖利率、波動
    div = ch["div"]
    pdate = pd.Timestamp(price_date)
    dps = float(div[(div.index > pdate - pd.Timedelta(days=365)) & (div.index <= pdate)].sum()) if len(div) else 0.0
    dy, dy_proxy = dps / px, np.nan
    sd_y = num(raw_(sd, "dividendYield"))
    if np.isfinite(sd_y) and sd_y > 0 and dy < 0.5 * sd_y:   # 日本 ADR、HDB、KB、NOK…：chart 的股利紀錄 2025 年起就斷了
        dy = dy_proxy = sd_y
        note.append(f"chart 股利紀錄不完整（近 12 個月 {dps / px:.4f}），dy 改用 summaryDetail.dividendYield {sd_y:.4f}"
                    "（美元股利÷股價；回測也用它當固定近似）")
    w = ch["close"][ch["close"].index > ch["close"].index[-1] - pd.DateOffset(months=36)]
    gap_ok = (w.index.to_series().diff().dt.days.between(20, 40)).to_numpy()
    mr = np.log(w / w.shift(1)).to_numpy()[gap_ok]
    mr = mr[np.isfinite(mr)]
    vol36 = float(np.std(mr, ddof=1) * np.sqrt(12)) if len(mr) >= 6 else np.nan
    lfy = raw_(ks, "lastFiscalYearEnd")
    spl = ch["split"][ch["split"].index >= pd.Timestamp("2022-06-01")]
    if len(spl):
        note.append("分割／ADR 比率變動：" + "、".join(f"{d.date()}×{v:g}" for d, v in spl.items()))
    row = dict(ticker=sym, name=raw_(pr, "longName") or raw_(pr, "shortName") or (snap_row.get("shortName") if snap_row is not None else ""),
               grp=grp, industry=industry, px=px, price_date=price_date, eps0=eps0,
               period_end=period_end.date() if period_end is not None else None, y10=rates, dy=dy, vol36=vol36,
               last_fy=pd.Timestamp(int(lfy), unit="s").date() if lfy else None, cons_0y=cons["cons_0y"], cons_1y=cons["cons_1y"],
               conv_factor=conv, conv_ok=conv_ok, currency_fin=fin, conv_note="｜".join(note),
               # 下面幾欄只給回測／驗收用，不寫進 adr_now.csv
               _sector=sec, _ratio=ratio, _ts_ccy=ts_ccy, _ts_last=ts_last, _fx_now=fx_now, _tpe=tpe,
               _fpe=raw_(sd, "forwardPE"), _feps=feps, _dy_proxy=dy_proxy, _c_ccy=c_ccy, _country=ap.get("country"), _street=street,
               _lfy_month=pd.Timestamp(int(lfy), unit="s").month if lfy else None)
    return row, None


# ───────────────────────────── 回測 ─────────────────────────────
def eps_at(th, when, fy_month):
    """when 那天已公布的最近四季（季末 +45 天；會計年度結束那季 +75 天）；太舊（> 270 天）→ NaN。"""
    if th is None or th.empty:
        return np.nan, None, None
    lag = np.where(th["date"].dt.month == (fy_month or 12), 75, 45)
    avail = th["date"] + pd.to_timedelta(lag, unit="D")
    k = th[avail <= when]
    if k.empty or (when - k["date"].iloc[-1]).days > 270:
        return np.nan, None, None
    return float(k["eps_loc"].iloc[-1]), k["ccy"].iloc[-1], k["date"].iloc[-1]


def build_hist(rows, raw_dir):
    out = []
    for r in rows:
        if not r["conv_ok"] or not np.isfinite(r["_ratio"]):
            continue
        sym = r["ticker"]
        ch = parse_chart(load(os.path.join(raw_dir, f"{sym}_5y_1mo.json")))
        th = ttm_history(parse_ts(load(os.path.join(raw_dir, f"{sym}_ts.json"))))
        fxcache = {}
        close = ch["close"][ch["close"].index < pd.Timestamp(r["price_date"]) + pd.offsets.MonthEnd(0)]  # 去掉本月至今那一筆
        for m, p in close.items():
            if m < pd.Timestamp("2023-09-30"):
                continue
            e, ccy, pe_date = eps_at(th, m, r["_lfy_month"])
            if ccy not in fxcache:
                fxcache[ccy] = fx_series(raw_dir, ccy)[0]
            fxs = fxcache[ccy]
            fx = 1.0 if ccy in (None, "USD") else (float(fxs.get(m, np.nan)) if fxs is not None else np.nan)
            div = ch["div"]
            dps = float(div[(div.index > m - pd.Timedelta(days=365)) & (div.index <= m)].sum()) if len(div) else 0.0
            dy = r["_dy_proxy"] if np.isfinite(r["_dy_proxy"]) else dps / p
            out.append(dict(ticker=sym, grp=r["grp"], month_end=m, px=p, eps_loc=e, eps_ccy=ccy, eps_period=pe_date,
                            fx=fx, ratio=r["_ratio"], eps_usd=e * r["_ratio"] / fx if np.isfinite(e) else np.nan,
                            dps_ttm=dps, dy=dy))
    return pd.DataFrame(out)


def split_events(tickers, raw_dir):
    """各檔的分割／ADR 比率變動（Yahoo chart 的 splits；|ln 比率| > 0.05 才算）。"""
    out = {}
    for t in tickers:
        ch = parse_chart(load(os.path.join(raw_dir, f"{t}_5y_1mo.json")))
        sp = ch["split"] if ch is not None else pd.Series(dtype=float)
        out[t] = [d for d, v in sp.items() if abs(np.log(v)) > 0.05]
    return out


def backtest(hist, rates, model, foreign, nonusd, splits):
    """splits：{代號: [日期…]}。Yahoo 的股價已做分割調整，但 timeseries 的 EPS 是「當時公布的每股（每 ADR）數字」、沒有回溯調整
    （實測 CNQ 2024-06 一拆二：2024-03-31 TTM 6.76 → 2024-06-30 3.515），各家 ADR 比率變動的處理也不一致（AZN、IX），
    所以 EPS0 與 EPS1 之間（前後各留緩衝）有分割或比率變動的列一律剔除，不自行換算。"""
    beta = {g: model["h"]["12"]["beta"]["原始成長a"][g][0] for g in GNAME}
    h = hist.set_index(["ticker", "month_end"])
    rows = []
    for (t, m0), r in h.iterrows():
        if not (pd.Timestamp("2023-10-31") <= m0 <= pd.Timestamp("2025-09-30")):
            continue
        m1 = m0 + pd.offsets.MonthEnd(12)
        if (t, m1) not in h.index:
            continue
        r1 = h.loc[(t, m1)]
        straddle = (pd.notna(r["eps_period"]) and pd.notna(r1["eps_period"])
                    and any(pd.Timestamp(r["eps_period"]) - pd.Timedelta(days=30) < d <= pd.Timestamp(r1["eps_period"]) + pd.Timedelta(days=120)
                            for d in splits.get(t, [])))
        rows.append(dict(ticker=t, grp=r["grp"], month=m0, p0=r["px"], p1=r1["px"], eps0=r["eps_usd"], eps1=r1["eps_usd"],
                         y10=rates.get(m0, np.nan), dy=r["dy"], beta=beta[r["grp"]], straddle=straddle, fx0=r["fx"], fx1=r1["fx"]))
    x = pd.DataFrame(rows)
    n_split = int((x["straddle"] & (x["eps0"] > 0) & (x["eps1"] > 0)).sum())
    x = x[~x["straddle"]]
    x = x[(x["eps0"] > 0) & (x["eps1"] > 0) & x["y10"].notna()].copy()
    x["lr"] = np.log(x["p1"] / x["p0"])
    x["g"] = np.log(x["eps1"] / x["eps0"]).clip(-2, 2)
    x["orbit"] = x["y10"] + 0.05 - x["dy"]
    x["e_unch"] = np.log(x["eps1"] / x["eps0"]) - x["lr"]
    x["e_orbit"] = x["orbit"] - x["lr"]
    x["e_model"] = x["e_orbit"] + x["beta"] * x["g"]
    x["foreign"] = x["ticker"].isin(foreign)
    x["nonusd"] = x["ticker"].isin(nonusd)
    x.attrs["n_split"] = n_split
    return x


def score(x, label_rows):
    out = []
    for lab, d in label_rows:
        if len(d) == 0:
            continue
        out.append(dict(組別=lab, 筆數=len(d), 公司=d["ticker"].nunique(),
                        本益比不變=np.median(np.abs(d["e_unch"])), 軌道=np.median(np.abs(d["e_orbit"])),
                        模型=np.median(np.abs(d["e_model"])),
                        軌道_命中20=np.mean(np.abs(np.exp(d["e_orbit"]) - 1) <= 0.2), 市場偏離軌道中位=np.median(-d["e_orbit"])))
    return pd.DataFrame(out)


def groups_of(x):
    return ([("全部", x), ("科技", x[x["grp"] != "other"])]
            + [(GNAME[k], x[x["grp"] == k]) for k in GNAME])


# ───────────────────────────── 主程式 ─────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", required=True, help="原始資料（Yahoo JSON）目錄")
    ap.add_argument("--snap", default=None, help="選股器快照（預設最新一份）")
    ap.add_argument("--top", type=int, default=120)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--max-age-h", type=float, default=72)
    ap.add_argument("--pause", type=float, default=0.7)
    a = ap.parse_args()
    PAUSE[0] = max(0.6, a.pause)
    snap_path = a.snap or latest_snapshot_file()
    snap = pd.read_csv(snap_path)
    names, ndx_add, dropped = pick_names(snap, a.top)
    say(f"快照：{os.path.relpath(snap_path, HERE)}；名單 {len(names)} 檔（市值前 {a.top}＋Nasdaq-100 2026 不在 now_all 的 "
        f"{len([t for t in ndx_add if t not in names[:a.top]])} 檔）；剔除同公司另一類股：{', '.join(dropped[:12])}")
    snapi = snap.assign(sym=snap["symbol"].astype(str).str.upper()).drop_duplicates("sym").set_index("sym")
    ccys = {c for c in snapi.loc[[n for n in names if n in snapi.index], "financialCurrency"].dropna() if c != "USD"}
    ccys = {SUB_UNIT.get(c, (c, 1))[0] for c in ccys}
    fetch_all(names, ccys, a.raw, a.offline, a.max_age_h)
    # timeseries／共識裡出現、但快照沒列到的幣別也補抓
    extra = set()
    for s in names:
        for df in parse_ts(load(os.path.join(a.raw, f"{s}_ts.json"))).values():
            extra |= {SUB_UNIT.get(c, (c, 1))[0] for c in df["ccy"].dropna() if c != "USD"}
    if extra - ccys:
        fetch_all([], extra - ccys, a.raw, a.offline, a.max_age_h)
    rates_df = pd.read_csv(os.path.join(DATA, "rates_monthly.csv"), parse_dates=["month_end"])
    rates_df = rates_df.dropna(subset=["DGS10"])
    y10_now = float(rates_df["DGS10"].iloc[-1]) / 100
    rates = dict(zip(rates_df["month_end"], rates_df["DGS10"] / 100))
    rsec = repo_sector()
    asof = max(pd.Timestamp(parse_chart(load(os.path.join(a.raw, f"{s}_5y_1mo.json")))["px_time"]).normalize()
               for s in names if parse_chart(load(os.path.join(a.raw, f"{s}_5y_1mo.json"))) is not None)
    rows, skipped = [], []
    for s in names:
        r, msg = now_row(s, snapi.loc[s].to_dict() if s in snapi.index else None, a.raw, y10_now, rsec, asof)
        (rows.append(r) if r else skipped.append(msg))
    cols = ["ticker", "name", "grp", "industry", "px", "price_date", "eps0", "period_end", "y10", "dy", "vol36", "last_fy",
            "cons_0y", "cons_1y", "conv_factor", "conv_ok", "currency_fin", "conv_note"]
    now = pd.DataFrame(rows)
    now[cols].to_csv(os.path.join(DATA, "adr_now.csv"), index=False, float_format="%.6g")
    say(f"data/adr_now.csv：{len(now)} 列（跳過 {len(skipped)}：{'；'.join(skipped)}）；y10＝{y10_now:.4f}（rates_monthly 最新 DGS10）")
    nonusd = now["currency_fin"] != "USD"
    say(f"口徑換算通過 {int(now['conv_ok'].sum())} 檔、不通過 {int((~now['conv_ok']).sum())} 檔"
        f"（財報非美元：通過 {int(now.loc[nonusd, 'conv_ok'].sum())}／{int(nonusd.sum())}）；"
        f"共識可用 0y {int(now['cons_0y'].notna().sum())}、+1y {int(now['cons_1y'].notna().sum())}")
    for r in now[~now["conv_ok"]].itertuples():
        say(f"  ✗ {r.ticker}（{r.currency_fin}）：{r.conv_note}")
    # 回測
    hist = build_hist(rows, a.raw)
    hist.to_csv(os.path.join(DATA, "adr_hist.csv.gz"), index=False, float_format="%.6g")
    model = json.load(open(os.path.join(RES, "orbit_model.json")))
    foreign = set(now.loc[now["_country"].fillna("") != "United States", "ticker"])
    x = backtest(hist, rates, model, foreign, set(now.loc[nonusd, "ticker"]), split_events(hist["ticker"].unique(), a.raw))
    report(now, hist, x, model, a.raw)


def report(now, hist, x, model, raw_dir):
    pd.set_option("display.width", 250)
    say("\n" + "=" * 100)
    say("ADR／未涵蓋大型股的 12 個月小型回測（起點 2023-10～2025-09，目標日 12 個月後、到 2026-09）")
    say("=" * 100)
    say("誤差公式（ln(預測 ÷ 實際股價)；表中是中位 |誤差|，越小越好）：")
    say("  本益比不變  e = ln(EPS1/EPS0) − ln(p1/p0)                 （預測 = p0 × EPS1/EPS0 ＝ 實際 EPS × 今天本益比）")
    say("  軌道        e = (y10 + 0.05 − dy) − ln(p1/p0)             （預測 = p0 × exp(y10 + 0.05 − dy)）")
    say("  模型        e = 軌道 e + β_grp × clip(ln(EPS1/EPS0), −2, 2)（預測 = 軌道 × exp(β × ln(EPS1/EPS0))）")
    say("  β（orbit_model.json h12 原始成長a）：" + "、".join(f"{GNAME[g]} {model['h']['12']['beta']['原始成長a'][g][0]:.4f}" for g in GNAME))
    say("  EPS＝那天已公布的最近四季 GAAP 稀釋（季末 +45 天、年度 +75 天），換成美元／ADR＝當地 EPS × ADR 比率 ÷ 當月匯率；"
        "只用 conv_ok、EPS0 > 0 且 EPS1 > 0 的列。y10＝起點月 DGS10；dy＝起點前 12 個月每 ADR 股利 ÷ p0。")
    say(f"  剔除 EPS0～EPS1 之間有分割／ADR 比率變動的列 {x.attrs.get('n_split', 0)} 筆（timeseries 的 EPS 沒有回溯分割調整）。")
    say(f"  「市場偏離軌道中位」＝ln(p1/p0) − 軌道 的中位（+＝股價比軌道多漲）。樣本：{x['ticker'].nunique()} 家、{len(x)} 筆公司月"
        f"（同一家公司 24 個起點高度相關，有效樣本遠小於筆數）。")
    subsets = [("全部名單（含總部在美國、但 now_all 沒有的公司）", "全部", x),
               ("總部在美國以外（assetProfile.country ≠ United States；含美元財報的 NVS、AZN、SHEL…，也含 ETN、ACN 這類愛爾蘭註冊的 10-K 公司）",
                "外國總部", x[x["foreign"]]),
               ("財報幣別 ≠ USD（最純的「外國申報」樣本：20-F／6-K、40-F）", "非美元財報", x[x["nonusd"]])]
    for title, _, d in subsets:
        say(f"\n== {title}")
        say(score(d, groups_of(d)).round(4).to_string(index=False))
    sp = pd.read_csv(os.path.join(RES, "orbit_recent_scores.csv"))
    sp = sp[sp["h"] == 12].set_index("組別")
    for lab, xn in (("起點 2023-10～2025-09", x[x["nonusd"]]), ("起點 2024-10～2025-09", x[x["nonusd"] & (x["month"] >= "2024-10-01")])):
        fxr = np.log(xn["fx0"] / xn["fx1"])                # 匯率對美元報酬的貢獻（+＝當地貨幣升值）
        say(f"\n   匯率拆解（財報非美元，{lab}，{len(xn)} 筆）：美元報酬＝當地幣別報酬＋匯率貢獻；匯率貢獻中位 {np.median(fxr):+.3f}，"
            f"市場偏離軌道中位 {np.median(-xn['e_orbit']):+.3f} → 扣掉匯率 {np.median(-xn['e_orbit'] - fxr):+.3f}；"
            f"軌道中位 |誤差| {np.median(np.abs(xn['e_orbit'])):.3f} → 以當地幣別報酬計 {np.median(np.abs(xn['e_orbit'] + fxr)):.3f}"
            "（軌道仍用美國 10 年期，只是診斷）")
    say("\n== 和 S&P 500 同期對照（起點都限 2024-10～2025-09；S&P 500 來自 results/orbit_recent_scores.csv 的 h=12，"
        "那邊 EPS 是 SEC 重述後數字、β 用走動式版本，口徑相近但不完全相同）")
    say("   每格：筆數／本益比不變／軌道／模型（中位 |ln 誤差|）")
    lines = []
    for lab in ["全部", "科技"] + list(GNAME.values()):
        line = dict(組別=lab)
        for _, short, d in subsets:
            d = d[d["month"] >= "2024-10-01"]
            sc = score(d, groups_of(d)).set_index("組別")
            line[short] = (f"{int(sc.loc[lab, '筆數'])}／{sc.loc[lab, '本益比不變']:.3f}／{sc.loc[lab, '軌道']:.3f}／{sc.loc[lab, '模型']:.3f}"
                           if lab in sc.index else "—")
        line["S&P 500"] = (f"{int(sp.loc[lab, 'n'])}／{sp.loc[lab, '本益比不變']:.3f}／{sp.loc[lab, '軌道']:.3f}／{sp.loc[lab, '軌道＋原始成長a']:.3f}"
                           if lab in sp.index else "—")
        lines.append(line)
    say(pd.DataFrame(lines).to_string(index=False))
    # 去掉「每個起點月份的共同偏離」：同一個宇宙（ADR 名單／非美元財報／S&P 500）每月所有列的誤差中位數先扣掉
    beta = {g: model["h"]["12"]["beta"]["原始成長a"][g][0] for g in GNAME}
    spr = pd.read_csv(os.path.join(RES, "orbit_recent_rows.csv.gz"), parse_dates=["month"])
    spr = spr[spr["h"] == 12].copy()
    spr["e_model"] = spr["e_orbit"] + spr["grp"].map(beta) * spr["g"]      # 和這裡同一組固定 β（不是走動式）
    unis = [("全部名單", x[x["month"] >= "2024-10-01"].copy()), ("非美元財報", x[x["nonusd"] & (x["month"] >= "2024-10-01")].copy()),
            ("S&P 500", spr)]
    for _, d in unis:
        for c in ("e_unch", "e_orbit", "e_model"):
            d[c + "_dm"] = d[c] - d.groupby("month")[c].transform("median")
    say("\n== 同期（起點 2024-10～2025-09）扣掉共同市場因子：每個宇宙先減去「該起點月份所有列的誤差中位數」再算中位 |誤差|。")
    say("   S&P 500 這裡用 results/orbit_recent_rows.csv.gz 逐筆、套同一組固定 β 重算（和上表的走動式 β 略有不同）。")
    say("   每格：筆數／本益比不變／軌道／模型（原始）‖ 本益比不變／軌道／模型（去共同因子）")
    lines = []
    for lab in ["全部", "科技"] + list(GNAME.values()):
        line = dict(組別=lab)
        for name, d in unis:
            sub = d if lab == "全部" else d[d["grp"] != "other"] if lab == "科技" else d[d["grp"].map(GNAME) == lab]
            if len(sub) == 0:
                line[name] = "—"
                continue
            m = lambda c: np.median(np.abs(sub[c]))
            line[name] = (f"{len(sub)}／{m('e_unch'):.3f}／{m('e_orbit'):.3f}／{m('e_model'):.3f} ‖ "
                          f"{m('e_unch_dm'):.3f}／{m('e_orbit_dm'):.3f}／{m('e_model_dm'):.3f}")
        lines.append(line)
    say(pd.DataFrame(lines).to_string(index=False))
    say("\n== 12 個月，依起點月份（全部名單）：")
    for m, d in x.groupby("month"):
        say(f"  {m:%Y-%m} n={len(d):4d}  不變 {np.median(np.abs(d['e_unch'])):.3f}  軌道 {np.median(np.abs(d['e_orbit'])):.3f}"
            f"  模型 {np.median(np.abs(d['e_model'])):.3f}  市場偏離軌道 {np.median(-d['e_orbit']):+.3f}")
    # 手算抽查
    say("\n== 手算抽查（每檔取一列；數字全部來自 data/adr_hist.csv.gz，照上面公式逐步算）")
    for t in ("TSM", "ASML", "SAP"):
        d = x[x["ticker"] == t]
        if d.empty:
            say(f"  {t}：回測沒有可用的列")
            continue
        r = d.iloc[len(d) // 2]
        hr = hist[(hist["ticker"] == t) & (hist["month_end"] == r["month"])].iloc[0]
        hr1 = hist[(hist["ticker"] == t) & (hist["month_end"] == r["month"] + pd.offsets.MonthEnd(12))].iloc[0]
        lr = np.log(r.p1 / r.p0)
        g = float(np.clip(np.log(r.eps1 / r.eps0), -2, 2))
        say(f"  {t} 起點 {r['month']:%Y-%m}：p0={r.p0:.2f} p1={r.p1:.2f} → ln(p1/p0)={lr:+.4f}")
        say(f"     EPS0＝{hr.eps_loc:g} {hr.eps_ccy}（{pd.Timestamp(hr.eps_period).date()} 止四季）× 比率 {hr.ratio:g} ÷ 匯率 {hr.fx:.4f} = {r.eps0:.4f} 美元／ADR；"
              f"EPS1＝{hr1.eps_loc:g} {hr1.eps_ccy}（{pd.Timestamp(hr1.eps_period).date()}）× {hr1.ratio:g} ÷ {hr1.fx:.4f} = {r.eps1:.4f}")
        say(f"     本益比不變：ln({r.eps1:.4f}/{r.eps0:.4f}) − {lr:.4f} = {np.log(r.eps1 / r.eps0) - lr:+.4f}（表內 {r.e_unch:+.4f}）")
        say(f"     軌道：({r.y10:.4f} + 0.05 − {r.dy:.4f}) − {lr:.4f} = {r.y10 + 0.05 - r.dy - lr:+.4f}（表內 {r.e_orbit:+.4f}）")
        say(f"     模型：{r.e_orbit:+.4f} + {r.beta:.4f} × {g:+.4f} = {r.e_orbit + r.beta * g:+.4f}（表內 {r.e_model:+.4f}）")
    # 驗收
    say("\n== 驗收：和 Yahoo 頁面的 trailingPE／forwardPE 比（差 < 5% 算過）")
    say("   forwardPE 的分母是 Yahoo 的 forwardEps（多半是 +1y 共識換成美元），所以拿 px ÷ cons_1y 比；Yahoo 若用 0y 當 forward 會註明。")
    vr = []
    for t in ("TSM", "ASML", "SAP", "NVO", "SKHY", "BABA", "ARM", "PDD"):
        r = now[now["ticker"] == t]
        if r.empty:
            vr.append(dict(代號=t, 結果="不在名單"))
            continue
        r = r.iloc[0]
        tpe, fpe = num(r["_tpe"]), num(r["_fpe"])
        pe = r.px / r.eps0 if r.eps0 > 0 else np.nan
        fpe_m = r.px / r.cons_1y if r.cons_1y and r.cons_1y > 0 else np.nan
        fpe_0 = r.px / r.cons_0y if r.cons_0y and r.cons_0y > 0 else np.nan
        dt, df1, df0 = pe / tpe - 1, fpe_m / fpe - 1, fpe_0 / fpe - 1
        use0 = np.isfinite(df0) and (not np.isfinite(df1) or abs(df0) < abs(df1))
        dfx = df0 if use0 else df1
        gaap = r["_ts_last"] * r["_ratio"] / r["_fx_now"] if np.isfinite(num(r["_ratio"])) else np.nan
        vr.append(dict(代號=t, 幣別=r.currency_fin, px=round(r.px, 2), eps0=round(r.eps0, 3),
                       GAAP現匯=round(gaap, 3) if np.isfinite(gaap) else None,
                       差_g=f"{r.eps0 / gaap - 1:+.1%}" if np.isfinite(gaap) else "—", 本益比=round(pe, 2),
                       Y_trailingPE=round(tpe, 2), 差_t=f"{dt:+.1%}" if np.isfinite(dt) else "—",
                       cons_0y=round(r.cons_0y, 3) if np.isfinite(r.cons_0y) else None,
                       cons_1y=round(r.cons_1y, 3) if np.isfinite(r.cons_1y) else None,
                       px_cons=round(fpe_0 if use0 else fpe_m, 2) if np.isfinite(fpe_0 if use0 else fpe_m) else None,
                       Y_forwardPE=round(fpe, 2), 差_f=f"{dfx:+.1%}" if np.isfinite(dfx) else "—",
                       f用=("0y" if use0 else "+1y"),
                       結果=("過" if (np.isfinite(dt) and abs(dt) < 0.05 and np.isfinite(dfx) and abs(dfx) < 0.05) else "見註"),
                       共識幣別=r["_c_ccy"],
                       係數x現匯=(f"{r.conv_factor * r['_fx_now'] - 1:+.1%}" if r["_c_ccy"] not in (None, "USD") and np.isfinite(r.conv_factor)
                                 else "—")))
    say(pd.DataFrame(vr).to_string(index=False))
    say("   註：本益比＝px÷eps0，eps0 就是 Yahoo 的美元 TTM（通過 (a)(b) 驗證），所以 trailingPE 必然一致——真正的口徑檢查在 (b)（conv_note）；")
    say("   「GAAP現匯」＝timeseries 當地幣別最近四季 × ADR 比率 ÷ 現在匯率，是和 Yahoo 美元 TTM 無關的獨立算法，差_g＝eps0 相對它的差。")
    say("   當地幣別共識 × conv_factor（＝Yahoo 美元 TTM ÷ 當地 TTM）讓「共識 ÷ eps0」不受匯率影響；但 Yahoo 的美元 TTM 多半用歷史匯率，")
    say("   forwardEps 用現匯，兩者差距＝「係數x現匯」欄（偏離 1 的幅度），這就是 px÷共識 和 Yahoo forwardPE 的落差來源，不是單位錯。")
    open(os.path.join(RES, "adr_backtest.txt"), "w").write(buf.getvalue())
    print(f"\n→ results/adr_backtest.txt、data/adr_hist.csv.gz（{len(hist)} 列）")


if __name__ == "__main__":
    main()
