"""市場共識 EPS（README §16.5、research/06）：Yahoo 預設產業選股器的本財年（0y）與下一財年（+1y）共識。

這個雲端環境能直接連（不用 cookie、crumb、key；2026-10-07 實測）。只有當下值，沒有歷史——
所以 consensus_snapshot.py 每次把全部類股存一份快照（data/consensus_snapshots/），累積我們自己的歷史時點資料。
口徑：Yahoo 的 epsTrailingTwelveMonths 是 GAAP 稀釋，但 epsCurrentYear／epsForward 多半是調整後（street）口徑——
股權報酬費用高的公司（軟體）兩者可差 30% 以上。orbit_price.py 會印出「共識 ÷ 目前 GAAP 最近四季」讓你判斷，
可用 --cons-scale 換算，或直接手動給共識（命令列與 data/consensus.csv 永遠優先）。
"""
import glob
import http.cookiejar
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

from pef.yahoo import yahoo_symbol

SCREENERS = ["ms_technology", "ms_communication_services", "ms_consumer_cyclical", "ms_healthcare", "ms_financial_services",
             "ms_industrials", "ms_consumer_defensive", "ms_energy", "ms_utilities", "ms_real_estate", "ms_basic_materials"]
SCR_URL = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds={}&count=250&start={}"
TS_URL = ("https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{}"
          "?type=annualDilutedEPS&period1={}&period2={}")
FIELDS = ["symbol", "shortName", "regularMarketTime", "regularMarketPrice", "currency", "financialCurrency",
          "epsTrailingTwelveMonths", "epsCurrentYear", "epsForward", "forwardPE", "priceEpsCurrentYear",
          "earningsTimestamp", "marketCap", "averageAnalystRating"]
UA = {"User-Agent": "Mozilla/5.0"}
QS_URL = ("https://query2.finance.yahoo.com/v10/finance/quoteSummary/{}"
          "?modules=earningsTrend,earningsHistory,defaultKeyStatistics&crumb={}")
_QS = {}


def _get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))


def snapshot(screeners=SCREENERS, pause=1.5, log=print):
    """抓全部類股選股器 → DataFrame（每列一檔：asof_utc、screener、FIELDS）。失敗的類股跳過並記錄。"""
    rows, asof = [], pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%MZ")
    for s in screeners:
        start = 0
        try:
            while True:
                r = _get(SCR_URL.format(s, start))["finance"]["result"][0]
                q = r["quotes"]
                rows += [dict(asof_utc=asof, screener=s, **{f: x.get(f) for f in FIELDS}) for x in q]
                start += len(q)
                if not q or start >= r.get("total", 0):
                    break
                time.sleep(pause)
        except Exception as e:                                # noqa: BLE001 — 單一類股失敗不影響其他
            log(f"  {s}：失敗（{type(e).__name__}）")
        time.sleep(pause)
    d = pd.DataFrame(rows)
    return d.drop_duplicates("symbol") if len(d) else d


def fy_month(ticker, cache_dir=None, max_age_h=24 * 7):
    """會計年度結束的月份（Yahoo fundamentals-timeseries 的 annualDilutedEPS 日期；最常見的那個月）。失敗回傳 None。
    注意：這個介面的年度資料會晚幾週才加上剛公布的年度，所以只拿它判斷「幾月結束」，不判斷「最近公布到哪一年」。"""
    sym = yahoo_symbol(ticker)
    path = os.path.join(cache_dir, f"{sym}_annualDilutedEPS.json") if cache_dir else None
    raw = None
    if path and os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age_h * 3600:
        raw = json.load(open(path))
    if raw is None:
        try:
            raw = _get(TS_URL.format(sym, int(time.time()) - 6 * 365 * 86400, int(time.time()) + 86400))
        except Exception:                                     # noqa: BLE001
            return None
        if path:
            os.makedirs(cache_dir, exist_ok=True)
            json.dump(raw, open(path, "w"))
    try:
        v = [x for x in raw["timeseries"]["result"][0].get("annualDilutedEPS", []) if x]
        months = pd.Series([pd.Timestamp(x["asOfDate"]).month for x in v])
        return int(months.mode().iloc[0]) if len(months) else None
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def last_earnings(row, now=None):
    """快照裡的 earningsTimestamp：已經過去的才算「最近一次公布」，未來的是「下一次」。回傳 (時間, 是否已過)。"""
    ts = row.get("earningsTimestamp")
    if ts is None or pd.isna(ts):
        return None, False
    when = pd.Timestamp(int(ts), unit="s")
    now = pd.Timestamp.now() if now is None else now
    return when, when <= now


REPORT_GAP = 95           # 年度結束後多少天內的財報日，算是「這一年的年報」；更晚的是下一年第一季


def fy0_end(month, row, now=None):
    """Yahoo 的 epsCurrentYear（0y）指的是哪一個會計年度：還沒公布的最早那一年。
    E＝最近一個已經結束的年度結束日。結束超過 100 天一定已公布 → 0y＝E＋12 個月。100 天內看財報日：
      已經過去、而且在 E 之後 → 年報已公布；
      還沒到（Yahoo 公布後會把日期滾到「下一次」）：距離 E 超過 95 天 → 那是下一年第一季 → 年報已公布；
      95 天內 → 那一次就是年報 → 還沒公布，0y＝E。沒有財報日 → 當作還沒公布。"""
    now = pd.Timestamp.now() if now is None else now
    e = pd.Timestamp(year=now.year, month=month, day=1) + pd.offsets.MonthEnd(0)
    if e > now:
        e = pd.Timestamp(year=now.year - 1, month=month, day=1) + pd.offsets.MonthEnd(0)
    nxt = e + pd.DateOffset(months=12) + pd.offsets.MonthEnd(0)
    if (now - e).days > 100:
        return nxt
    when, past = last_earnings(row, now)
    if when is None:
        return e
    if past:
        return nxt if when > e else e
    return nxt if (when - e).days > REPORT_GAP else e


def last_reported_quarter(period_end, row, now=None):
    """快照的財報日推「現在已公布到哪一季」：從 period_end 每次加 3 個月往後找。
    財報日已過 → 公布的是財報日前最後一個季末；財報日還沒到 → 那一次要公布的季再往前一季。回傳 (季末, 比 period_end 多幾季)。"""
    when, past = last_earnings(row, now)
    q = pd.Timestamp(period_end)
    if when is None:
        return q, 0
    lim = when - pd.Timedelta(days=10)
    chain = [q]
    while chain[-1] + pd.DateOffset(months=3) <= lim:
        chain.append(chain[-1] + pd.DateOffset(months=3))
    if not past and len(chain) > 1:
        chain = chain[:-1]                                # 下一次要公布的那一季還沒公布
    return chain[-1], len(chain) - 1


def refresh_eps(row, snap, now=None, mrq=None):
    """repo 的最近四季 EPS（row["eps0"]、row["period_end"]）比快照舊時，改用快照的 GAAP 最近四季（epsTrailingTwelveMonths）。
    只在美元報價、美元財報時更新。mrq（quoteSummary 的最近一季季末）有給就用它，否則用財報日推。
    回傳 dict(eps0, period_end, n_new, ratio, note)；不更新時 n_new＝0。"""
    out = dict(eps0=float(row["eps0"]), period_end=pd.Timestamp(row["period_end"]), n_new=0, ratio=None, note=None)
    if snap is None:
        return out
    ttm = snap.get("epsTrailingTwelveMonths")
    cur, fcur = str(snap.get("currency") or ""), str(snap.get("financialCurrency") or "")
    if ttm is None or pd.isna(ttm) or cur != "USD" or fcur not in ("USD", "nan", ""):
        return out
    if mrq is not None:                                   # quoteSummary 的最近一季季末（精確）
        mrq = pd.Timestamp(mrq)
        if mrq <= out["period_end"] + pd.Timedelta(days=20):
            return out
        q, n = mrq, max(1, int(round((mrq - out["period_end"]).days / 91)))
    else:
        q, n = last_reported_quarter(out["period_end"], snap, now)
    if n < 1:
        return out
    old = out["eps0"]
    ratio = float(ttm) / old if old else None
    note = (f"今天的 EPS 已更新：repo 之後又公布了 {n} 季（推到季末約 {q.date()}）→ 最近四季 EPS {old:,.2f} → {float(ttm):,.2f}"
            "（Yahoo，GAAP 稀釋）")
    if ratio is not None and (ratio <= 0 or ratio > 3 or ratio < 1 / 3):
        note += f"　⚠ 新舊相差 {ratio:.2f} 倍（或正負號改變），請確認"
    return dict(eps0=float(ttm), period_end=q, n_new=n, ratio=ratio, note=note)


def _qs_session():
    """quoteSummary 要 cookie＋crumb：先連 fc.yahoo.com 拿 cookie（回 404 也會設），再到 query2 拿 crumb。
    需要環境允許 fc.yahoo.com、query2.finance.yahoo.com（2026-10-08 起這個雲端環境已允許）。失敗回傳 None。"""
    if "op" in _QS:
        return _QS["op"], _QS["crumb"]
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders = list(UA.items())
    try:
        try:
            op.open("https://fc.yahoo.com/", timeout=20)
        except urllib.error.HTTPError:
            pass
        crumb = op.open("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=20).read().decode().strip()
    except Exception:                                     # noqa: BLE001
        return None, None
    if not crumb or "<" in crumb:
        return None, None
    _QS.update(op=op, crumb=crumb)
    return op, crumb


def _raw(d, k):
    v = (d or {}).get(k)
    return v.get("raw") if isinstance(v, dict) else None


def parse_quote_summary(raw):
    """quoteSummary JSON → dict(last_fy, mrq, trend={0q,+1q,0y,+1y: dict(avg, low, high, n, d7, d30, d60, d90, up30, down30)},
    street=[(季, 調整後實際 EPS)…], street_ttm)。
    last_fy（defaultKeyStatistics.lastFiscalYearEnd）＝最近一個「已公布」的會計年度結束日——實測可靠；
    earningsTrend 裡的 endDate 在剛公布後會落後一期（MU 2026-10：0y 標 2026-08-31，其實是 FY2027），不用。"""
    try:
        r = raw["quoteSummary"]["result"][0]
    except (KeyError, IndexError, TypeError):
        return None
    k = r.get("defaultKeyStatistics") or {}
    ts = lambda v: pd.Timestamp(int(v), unit="s").normalize() if v else None
    out = dict(last_fy=ts(_raw(k, "lastFiscalYearEnd")), mrq=ts(_raw(k, "mostRecentQuarter")), trend={})
    for t in (r.get("earningsTrend") or {}).get("trend", []):
        e, tr, rv = t.get("earningsEstimate") or {}, t.get("epsTrend") or {}, t.get("epsRevisions") or {}
        out["trend"][t.get("period")] = dict(avg=_raw(e, "avg"), low=_raw(e, "low"), high=_raw(e, "high"),
                                             n=_raw(e, "numberOfAnalysts"), d7=_raw(tr, "7daysAgo"), d30=_raw(tr, "30daysAgo"),
                                             d60=_raw(tr, "60daysAgo"), d90=_raw(tr, "90daysAgo"),
                                             up30=_raw(rv, "upLast30days"), down30=_raw(rv, "downLast30days"))
    hist = [(ts(_raw(h, "quarter")), _raw(h, "epsActual")) for h in (r.get("earningsHistory") or {}).get("history", [])]
    hist = sorted([(q, v) for q, v in hist if q is not None and v is not None])
    out["street"] = hist
    last4 = hist[-4:]
    ok = len(last4) == 4 and all((last4[i + 1][0] - last4[i][0]).days < 120 for i in range(3))
    out["street_ttm"] = float(sum(v for _, v in last4)) if ok else None
    return out


def quote_summary(ticker, cache_dir=None, max_age_h=24):
    """一檔的完整分析師資料（parse_quote_summary 的格式）；拿不到回傳 None。"""
    sym = yahoo_symbol(ticker)
    path = os.path.join(cache_dir, f"{sym}_quoteSummary.json") if cache_dir else None
    raw = None
    if path and os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age_h * 3600:
        raw = json.load(open(path))
    if raw is None:
        op, crumb = _qs_session()
        if op is None:
            return None
        try:
            raw = json.load(op.open(QS_URL.format(sym, urllib.parse.quote(crumb)), timeout=30))
        except Exception:                                 # noqa: BLE001
            return None
        if path:
            os.makedirs(cache_dir, exist_ok=True)
            json.dump(raw, open(path, "w"))
    return parse_quote_summary(raw)


def latest_snapshot(snap_dir, ticker, max_age_days=7):
    """data/consensus_snapshots/ 裡最新、且 max_age_days 天內的選股器快照（yahoo_YYYY-MM-DD；不含 yahoo_detail_）中這一檔的那一列，沒有就 None。"""
    sym = yahoo_symbol(ticker)
    for f in sorted(glob.glob(os.path.join(snap_dir, "yahoo_2*.csv.gz")), reverse=True):
        d = pd.read_csv(f)
        when = pd.Timestamp(d["asof_utc"].iloc[0]) if len(d) else None
        if when is None or (pd.Timestamp.now(tz="UTC") - when).days > max_age_days:
            return None
        hit = d[d["symbol"] == sym]
        if len(hit):
            return hit.iloc[0].to_dict()
    return None


def save_snapshot(d, snap_dir):
    os.makedirs(snap_dir, exist_ok=True)
    day = d["asof_utc"].iloc[0][:10]
    path = os.path.join(snap_dir, f"yahoo_{day}.csv.gz")
    d.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})
    return path


def get_row(ticker, snap_dir, live=False, log=print):
    """這一檔在最新快照（7 天內）裡的那一列；沒有且 live=True 時即時抓全部類股並存成今天的快照。回傳 (row, 來源)。"""
    row = latest_snapshot(snap_dir, ticker)
    if row is not None:
        return row, "data/consensus_snapshots"
    if not live:
        return None, None
    log("  抓 Yahoo 選股器的目前共識（全部類股，約 30 秒；存成今天的快照）…")
    d = snapshot(log=log)
    if not len(d):
        return None, None
    save_snapshot(d, snap_dir)
    hit = d[d["symbol"] == yahoo_symbol(ticker)]
    return (hit.iloc[0].to_dict(), "Yahoo 選股器（剛抓）") if len(hit) else (None, None)


def auto(ticker, row, src, cache_dir=None, now=None, qs=None):
    """回傳 dict(fy={0y 年度結束日: 0y, +1y 年度結束日: +1y}, source, warn=[...], fy0, basis_k, info=[...])；拿不到回傳 None。
    有 quoteSummary（qs）時：年度用 last_fy＋12／24 個月（精確），數字用 qs 的平均；另算口徑係數
    basis_k＝GAAP 最近四季 ÷ 調整後（street）最近四季，用來把共識換成 GAAP 口徑。沒有 qs 時用選股器＋fy0_end 推估。"""
    info, warn = [], []
    vals = {}
    if qs and qs.get("last_fy") is not None and qs["trend"].get("0y", {}).get("avg") is not None:
        e0 = qs["last_fy"] + pd.DateOffset(months=12)
        for k, p in ((0, "0y"), (1, "+1y")):
            v = qs["trend"].get(p, {}).get("avg")
            if v is not None:
                vals[e0 + pd.DateOffset(months=12 * k)] = float(v)
        src = "Yahoo quoteSummary（剛抓）"
        if row is not None:
            m = pd.Timestamp(qs["last_fy"]).month
            guess = fy0_end(m, row, now)
            if abs((guess - e0).days) > 40:
                info.append(f"（選股器推估的本財年是 {guess.date()}，以 Yahoo 的「最近已公布年度」為準）")
        for p in ("0y", "+1y"):
            t = qs["trend"].get(p) or {}
            if t.get("avg") and t.get("d90"):
                info.append(f"{p}：分析師 {t.get('n') or '?'} 位、區間 {t.get('low') or float('nan'):,.2f}–{t.get('high') or float('nan'):,.2f}、"
                            f"90 天來 {t['avg'] / t['d90'] - 1:+.1%}（30 天上修 {t.get('up30') or 0}、下修 {t.get('down30') or 0} 位）")
        gaap = row.get("epsTrailingTwelveMonths") if row is not None else None
        st = qs.get("street_ttm")
        basis_k = float(gaap) / st if (gaap is not None and pd.notna(gaap) and st and st > 0) else None
    else:
        if row is None:
            return None
        m = fy_month(ticker, cache_dir)
        if m is None:
            return None
        e0 = fy0_end(m, row, now)
        for k, col in ((0, "epsCurrentYear"), (1, "epsForward")):
            v = row.get(col)
            if v is not None and pd.notna(v):
                vals[e0 + pd.DateOffset(months=12 * k) + pd.offsets.MonthEnd(0)] = float(v)
        basis_k = None
        src = f"{src}，{str(row['asof_utc'])[:10]}"
    if row is not None:
        cur, fcur = str(row.get("currency") or ""), str(row.get("financialCurrency") or "")
        if cur != "USD" or (fcur and fcur not in ("nan", cur)):
            warn.append(f"幣別：報價 {cur}、財報 {fcur}——共識可能和股價不同幣別（ADR 常見），請手動確認或改用 --cons")
    if not vals:
        return None
    return dict(fy=vals, source=src, warn=warn, fy0=min(vals), basis_k=basis_k, info=info)
