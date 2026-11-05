#!/usr/bin/env python3
"""
market_cockpit.py — 全局觀測台（Market Cockpit）資料層

把三個問題數據化、指標化，輸出給 docs/cockpit/index.html：
  (1) 市場 regime：多頭 / 盤整 / 空頭（Regime Score −100…+100，四支柱：趨勢 / 廣度 / 波動 / 信用）
  (2) 板塊強弱：11 個 SPDR 板塊 + SMH，多期間相對強度排名 + RRG（JdK RS-Ratio / RS-Momentum）象限
  (3) 資金流向（價量代理）：Chaikin 式 20 日淨資金流 ÷ 20 日成交金額 = 流向強度，
      對照該板塊自身的 1 年均值、全歷史均值與歷史百分位；另算成交金額佔比的變化（注意力轉移）
  (4) 回測：regime 條件化前瞻報酬與轉移矩陣、板塊動能 Top3/Bottom3 月調倉、RRG 象限前瞻超額、
      資金流 IC / 五分位、regime × 板塊超額報酬熱圖

資料：Yahoo chart API（免金鑰；UA 必須是專案自己的，不要假冒瀏覽器）。只用 pandas / numpy。
輸出：docs/cockpit/data.json（現況）與 docs/cockpit/backtest.json（回測；每日重算但內容只隨歷史緩慢改變）。

用法：python scripts/market_cockpit.py [--cache DIR] [--no-backtest]
      雲端 Claude 容器可直接跑（2026-11-05 實測 Yahoo 200）；GitHub Actions runner 亦可。
"""

import argparse
import json
import math
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(ROOT))
OUT_DIR = os.path.join(REPO, "docs", "cockpit")
OUT_DATA = os.path.join(OUT_DIR, "data.json")
OUT_BT = os.path.join(OUT_DIR, "backtest.json")
WATCH_CFG = os.path.join(ROOT, "config", "cockpit_watch.json")

UA = {"User-Agent": "KIWI-cockpit/1.0 (+https://github.com/gutinganthony/KIWI)"}

BENCH = "SPY"
SECTORS = [  # (symbol, 中文名, 英文名)
    ("XLK", "科技", "Technology"),
    ("XLC", "通訊服務", "Communication"),
    ("XLY", "非必需消費", "Cons. Discretionary"),
    ("XLF", "金融", "Financials"),
    ("XLV", "醫療", "Health Care"),
    ("XLI", "工業", "Industrials"),
    ("XLE", "能源", "Energy"),
    ("XLB", "原物料", "Materials"),
    ("XLP", "必需消費", "Cons. Staples"),
    ("XLU", "公用事業", "Utilities"),
    ("XLRE", "不動產", "Real Estate"),
    ("SMH", "半導體", "Semiconductors"),
]
SECTOR_SYMS = [s for s, _, _ in SECTORS]
AUX = ["RSP", "IWM", "QQQ", "HYG", "IEF", "TLT", "GLD", "^VIX"]

# 四支柱權重（NaN 的支柱自動剔除並重新正規化）
PILLAR_W = {"trend": 0.40, "breadth": 0.25, "vol": 0.20, "credit": 0.15}
# regime 進出門檻（含遲滯，避免每日翻轉）
BULL_IN, BULL_OUT, BEAR_IN, BEAR_OUT = 25, 10, -25, -10
CONFIRM_DAYS = 3  # 狀態切換需連續 3 個交易日滿足條件（抑制日內雜訊翻轉）
REGIME_LABEL = {"bull": "多頭", "range": "盤整", "bear": "空頭"}
FLOW_LABELS = [(80, "強勢流入"), (60, "流入"), (40, "中性"), (20, "流出"), (-1, "強勢流出")]


# ---------------------------------------------------------------- data layer
def _get(url, path=None, timeout=25, retries=4):
    if path and os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            return f.read()
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                raw = r.read()
            if path:
                with open(path, "wb") as f:
                    f.write(raw)
            return raw
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3.0 * (i + 1))
    raise last


def yahoo_ohlcv(tk, cache=None):
    """全歷史日線（含 adjclose）。回 DataFrame[open, high, low, close, adj, volume]，index 正規化日期。"""
    q = urllib.request.quote(tk)
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{q}"
           f"?period1=-1325635200&period2=4102444800&interval=1d&events=div%2Csplit")
    raw = _get(url, os.path.join(cache, f"y_{q.replace('%5E', '_')}.json") if cache else None)
    r = json.loads(raw)["chart"]["result"][0]
    qd = r["indicators"]["quote"][0]
    adj = r["indicators"].get("adjclose", [{}])[0].get("adjclose", qd["close"])
    df = pd.DataFrame({"open": qd["open"], "high": qd["high"], "low": qd["low"], "close": qd["close"],
                       "adj": adj, "volume": qd["volume"]},
                      index=pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert("America/New_York").normalize().tz_localize(None))
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["close"])
    df["adj"] = df["adj"].fillna(df["close"])
    return df


def load_all(cache=None):
    syms = [BENCH] + SECTOR_SYMS + AUX
    out = {}
    with ThreadPoolExecutor(max_workers=3) as ex:  # Yahoo 對並行請求容易 429，寧可慢
        for s, df in zip(syms, ex.map(lambda t: _safe(yahoo_ohlcv, t, cache), syms)):
            if df is not None and len(df) > 300:
                out[s] = df
            else:
                print(f"[warn] {s}: no data", file=sys.stderr)
    missing = [s for s in SECTOR_SYMS if s not in out]
    if len(missing) > 2:
        print(f"板塊缺太多（{missing}），放棄本次更新以免輸出殘缺資料", file=sys.stderr)
        sys.exit(1)
    out["_missing"] = missing
    return out


def _safe(fn, *a):
    try:
        return fn(*a)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] {fn.__name__}{a[:1]}: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------- helpers
def clip100(x):
    return np.clip(x, -100, 100)


def _prank(a):
    b = a[:-1]
    b = b[~np.isnan(b)]
    if len(b) < 60 or np.isnan(a[-1]):
        return np.nan
    return (b < a[-1]).mean()


def pct_rank_rolling(s, win, min_periods=None):
    """s 在過去 win 期內的百分位（0–1），排除 NaN（板塊上市前的空值不能算進分母）。"""
    return s.rolling(win, min_periods=min_periods or win).apply(_prank, raw=True)


def pct_rank_5y(s):
    """5 年（1260 日）滾動百分位（0–100）；資料不足 5 年時用現有的（至少 1 年）。"""
    return pct_rank_rolling(s, 1260, min_periods=252) * 100


def r(x, n=2):
    if x is None:
        return None
    try:
        if isinstance(x, (float, np.floating)) and (math.isnan(x) or math.isinf(x)):
            return None
        return round(float(x), n)
    except (TypeError, ValueError):
        return None


def max_drawdown(eq):
    peak = eq.cummax()
    return float((eq / peak - 1).min())


def perf_stats(monthly_ret):
    """月報酬序列 → CAGR / vol / Sharpe / MDD / 勝率。"""
    m = monthly_ret.dropna()
    if len(m) < 12:
        return None
    eq = (1 + m).cumprod()
    yrs = len(m) / 12
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    vol = m.std() * math.sqrt(12)
    return {"cagr": r(cagr * 100), "vol": r(vol * 100), "sharpe": r(cagr / vol if vol else None),
            "mdd": r(max_drawdown(eq) * 100), "win": r((m > 0).mean() * 100, 1), "months": int(len(m))}


# ---------------------------------------------------------------- (1) regime
def build_regime(data):
    spy = data[BENCH]
    px = spy["adj"]
    close = spy["close"]
    ma50, ma200 = px.rolling(50).mean(), px.rolling(200).mean()
    out = pd.DataFrame(index=px.index)
    out["spy"] = px
    out["spy_close"] = close
    out["ma50"], out["ma200"] = ma50, ma200
    out["dist200"] = px / ma200 - 1
    # --- 趨勢
    t1 = clip100((px / ma200 - 1) / 0.10 * 100)
    t2 = clip100((ma50 / ma200 - 1) / 0.05 * 100)
    t3 = clip100(ma200.pct_change(20) / 0.02 * 100)
    out["trend"] = 0.5 * t1 + 0.25 * t2 + 0.25 * t3
    out["t_dist200"], out["t_golden"], out["t_slope"] = t1, t2, t3
    # --- 廣度（板塊站上均線比例 + 等權/小型股參與度）
    above200, above50 = [], []
    for s in SECTOR_SYMS:
        if s not in data:
            continue
        p = data[s]["adj"].reindex(px.index)
        above200.append((p > p.rolling(200).mean()).where(p.notna()))
        above50.append((p > p.rolling(50).mean()).where(p.notna()))
    a200 = pd.concat(above200, axis=1).mean(axis=1)
    a50 = pd.concat(above50, axis=1).mean(axis=1)
    out["pct_above200"], out["pct_above50"] = a200, a50
    parts = []
    for s in ("RSP", "IWM"):
        if s in data:
            rel = (data[s]["adj"].reindex(px.index) / px)
            parts.append(clip100(rel.pct_change(63) / 0.05 * 100))
    part = pd.concat(parts, axis=1).mean(axis=1) if parts else pd.Series(np.nan, index=px.index)
    b1, b2 = (a200 - 0.5) * 200, (a50 - 0.5) * 200
    out["breadth"] = 0.4 * b1 + 0.3 * b2 + 0.3 * part.fillna((b1 + b2) / 2)
    out["b_above200"], out["b_above50"], out["b_particip"] = b1, b2, part
    # --- 波動
    if "^VIX" in data:
        vix = data["^VIX"]["close"].reindex(px.index).ffill()
        v1 = (0.5 - pct_rank_rolling(vix, 252)) * 200
        v2 = clip100(-(vix / vix.rolling(50).mean() - 1) / 0.30 * 100)
    else:
        vix = pd.Series(np.nan, index=px.index)
        v1 = v2 = pd.Series(np.nan, index=px.index)
    rv = px.pct_change().rolling(20).std() * math.sqrt(252)
    v3 = (0.5 - pct_rank_rolling(rv, 252)) * 200
    out["vix"], out["rv20"] = vix, rv
    out["vol"] = (0.4 * v1 + 0.3 * v2 + 0.3 * v3) if vix.notna().any() else v3
    out["v_vix_pct"], out["v_vix_trend"], out["v_rv_pct"] = v1, v2, v3
    # --- 信用 / 風險偏好（HYG/IEF）
    if "HYG" in data and "IEF" in data:
        ratio = (data["HYG"]["adj"] / data["IEF"]["adj"]).reindex(px.index)
        c1 = clip100((ratio / ratio.rolling(63).mean() - 1) / 0.03 * 100)
        c2 = clip100(ratio.pct_change(20) / 0.02 * 100)
        out["credit"] = 0.6 * c1 + 0.4 * c2
        out["c_level"], out["c_change"] = c1, c2
        out["hyg_ief"] = ratio
    else:
        out["credit"] = np.nan
    # --- 合成分數（缺支柱時重新正規化）
    W = pd.DataFrame({k: out[k].notna() * w for k, w in PILLAR_W.items()})
    score = sum(out[k].fillna(0) * PILLAR_W[k] for k in PILLAR_W) / W.sum(axis=1).replace(0, np.nan)
    out["score"] = score
    # --- 狀態機（遲滯）
    states, st = [], "range"
    sc, d2 = score.values, out["dist200"].values
    pend, pend_n = None, 0  # 候選狀態與連續確認天數
    for i in range(len(out)):
        s, d = sc[i], d2[i]
        if np.isnan(s) or np.isnan(d):
            states.append(None)
            continue
        if st == "bull":
            want = "range" if s < BULL_OUT else "bull"
        elif st == "bear":
            want = "range" if s > BEAR_OUT else "bear"
        else:
            want = "bull" if (s >= BULL_IN and d > 0) else "bear" if (s <= BEAR_IN and d < 0) else "range"
        if want != st:
            pend_n = pend_n + 1 if want == pend else 1
            pend = want
            if pend_n >= CONFIRM_DAYS:
                st, pend, pend_n = want, None, 0
        else:
            pend, pend_n = None, 0
        states.append(st)
    out["state"] = states
    return out


def regime_episodes(reg, min_days=1):
    s = reg["state"].dropna()
    eps, start, cur = [], None, None
    for d, v in s.items():
        if v != cur:
            if cur is not None:
                eps.append((cur, start, prev))
            cur, start = v, d
        prev = d
    if cur is not None:
        eps.append((cur, start, prev))
    out = []
    for st, a, b in eps:
        seg = reg.loc[a:b, "spy"]
        if len(seg) < min_days:
            continue
        out.append({"state": st, "start": a.strftime("%Y-%m-%d"), "end": b.strftime("%Y-%m-%d"),
                    "days": int(len(seg)), "spy_ret": r((seg.iloc[-1] / seg.iloc[0] - 1) * 100, 1),
                    "mdd": r(max_drawdown(seg) * 100, 1)})
    return out


# ---------------------------------------------------------------- (2) sectors: strength + RRG
def rrg_series(sector_adj, bench_adj, n_ratio=63, n_mom=21):
    rs = 100 * sector_adj / bench_adj
    rs_ratio = 100 + 10 * (rs - rs.rolling(n_ratio).mean()) / rs.rolling(n_ratio).std()
    rs_mom = 100 + 10 * (rs_ratio - rs_ratio.rolling(n_mom).mean()) / rs_ratio.rolling(n_mom).std()
    return rs_ratio, rs_mom


def quadrant(ratio, mom):
    if ratio is None or mom is None or np.isnan(ratio) or np.isnan(mom):
        return None
    if ratio >= 100 and mom >= 100:
        return "leading"
    if ratio >= 100:
        return "weakening"
    if mom >= 100:
        return "improving"
    return "lagging"


QUAD_LABEL = {"leading": "領先", "weakening": "轉弱", "lagging": "落後", "improving": "改善"}


def build_sectors(data, idx):
    bench = data[BENCH]["adj"].reindex(idx)
    panel = {}
    for s in SECTOR_SYMS:
        if s not in data:
            continue
        df = data[s].reindex(idx)
        p = df["adj"]
        d = pd.DataFrame(index=idx)
        d["adj"] = p
        d["close"] = df["close"]
        for h, name in ((5, "1w"), (21, "1m"), (63, "3m"), (126, "6m"), (252, "1y")):
            d[f"ret_{name}"] = p.pct_change(h)
            d[f"exc_{name}"] = p.pct_change(h) - bench.pct_change(h)
        d["above50"] = p > p.rolling(50).mean()
        d["above200"] = p > p.rolling(200).mean()
        d["rs_ratio"], d["rs_mom"] = rrg_series(p, bench)
        # 資金流代理：Chaikin money-flow 乘數 × 成交金額
        hl = (df["high"] - df["low"]).replace(0, np.nan)
        mult = (((df["close"] - df["low"]) - (df["high"] - df["close"])) / hl).fillna(0)
        dv = df["close"] * df["volume"]
        d["dv20"] = dv.rolling(20).sum()
        d["net20"] = (mult * dv).rolling(20).sum()
        d["flow"] = d["net20"] / d["dv20"]
        d["flow_avg_1y"] = d["flow"].rolling(252).mean()
        d["flow_avg_5y"] = d["flow"].rolling(1260, min_periods=252).mean()
        d["flow_pct"] = pct_rank_5y(d["flow"])
        d["flow_z1y"] = (d["flow"] - d["flow_avg_1y"]) / d["flow"].rolling(252).std()
        panel[s] = d
    # 跨板塊強度分數：多期間超額報酬的橫斷面百分位（1M 25% / 3M 50% / 6M 25%）
    strength = {}
    for h, w in (("3m", 0.30), ("6m", 0.40), ("1y", 0.30)):
        exc = pd.concat({s: panel[s][f"exc_{h}"] for s in panel}, axis=1)
        rk = exc.rank(axis=1, pct=True)
        strength[h] = rk * w
    tot = sum(strength.values())
    # 用可得板塊數修正（早期只有 9 檔）
    cnt = pd.concat({s: panel[s]["exc_1y"] for s in panel}, axis=1).notna().sum(axis=1)
    score = (tot * 100).where(cnt >= 6)
    for s in panel:
        panel[s]["strength"] = score[s]
    # 成交金額佔比（注意力）
    dv_all = pd.concat({s: panel[s]["dv20"] for s in panel}, axis=1)
    share = dv_all.div(dv_all.sum(axis=1), axis=0)
    for s in panel:
        panel[s]["share"] = share[s]
        panel[s]["share_avg_1y"] = share[s].rolling(252).mean()
    return panel


def flow_label(pct):
    if pct is None or np.isnan(pct):
        return None
    for th, lab in FLOW_LABELS:
        if pct >= th:
            return lab
    return FLOW_LABELS[-1][1]


# ---------------------------------------------------------------- (3) watch / holdings tracking
def build_watch(cache, idx, bench_adj):
    """config/cockpit_watch.json 裡的個股：給 dashboard 持倉面板對應用（價格、趨勢、RS、資金流）。"""
    try:
        cfg = json.load(open(WATCH_CFG, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    out = []
    for item in cfg.get("symbols", []):
        sym = item["symbol"] if isinstance(item, dict) else item
        time.sleep(1.0)  # Yahoo 對連續請求會 429
        df = _safe(yahoo_ohlcv, sym, cache)
        if df is None or len(df) < 60:
            out.append({"symbol": sym, "error": "no data"})
            continue
        p = df["adj"]
        last = p.index[-1]
        b = bench_adj.reindex(p.index).ffill()
        ma200 = p.rolling(200).mean()
        rs_ratio, rs_mom = rrg_series(p, b)
        hl = (df["high"] - df["low"]).replace(0, np.nan)
        mult = (((df["close"] - df["low"]) - (df["high"] - df["close"])) / hl).fillna(0)
        dv = df["close"] * df["volume"]
        flow = (mult * dv).rolling(20).sum() / dv.rolling(20).sum()
        fp = pct_rank_5y(flow)
        rec = {"symbol": sym, "name": item.get("name") if isinstance(item, dict) else None,
               "sector": item.get("sector") if isinstance(item, dict) else None,
               "asof": last.strftime("%Y-%m-%d"), "close": r(df["close"].iloc[-1], 2),
               "ret_1m": r(p.pct_change(21).iloc[-1] * 100, 1), "ret_3m": r(p.pct_change(63).iloc[-1] * 100, 1),
               "exc_1m": r((p.pct_change(21) - b.pct_change(21)).iloc[-1] * 100, 1),
               "exc_3m": r((p.pct_change(63) - b.pct_change(63)).iloc[-1] * 100, 1),
               "dist200": r((p / ma200 - 1).iloc[-1] * 100, 1) if ma200.notna().iloc[-1] else None,
               "above200": bool(p.iloc[-1] > ma200.iloc[-1]) if ma200.notna().iloc[-1] else None,
               "rs_ratio": r(rs_ratio.iloc[-1], 1), "rs_mom": r(rs_mom.iloc[-1], 1),
               "quadrant": quadrant(rs_ratio.iloc[-1], rs_mom.iloc[-1]),
               "flow": r(flow.iloc[-1], 3), "flow_pct": r(fp.iloc[-1], 0), "flow_label": flow_label(fp.iloc[-1]),
               "spark": [r(x, 2) for x in p.iloc[-60:].tolist()]}
        out.append(rec)
    return out


# ---------------------------------------------------------------- (4) backtests
def _me():
    """pandas ≥2.2 用 "ME"，舊版只有 "M"。"""
    try:
        pd.Series([0.0], index=pd.to_datetime(["2020-01-31"])).resample("ME").last()
        return "ME"
    except ValueError:
        return "M"



def month_ends(idx):
    return idx.to_series().groupby([idx.year, idx.month]).last().values


def bt_regime(reg):
    """regime 條件化：各狀態的前瞻 21/63 日報酬、勝率、年化波動、轉移矩陣、策略 vs 買進持有。"""
    df = reg.dropna(subset=["state", "score"]).copy()
    px = df["spy"]
    for h in (21, 63):
        df[f"fwd{h}"] = px.shift(-h) / px - 1
    df["ret1"] = px.pct_change()
    stats = {}
    for st in ("bull", "range", "bear"):
        g = df[df["state"] == st]
        if g.empty:
            continue
        stats[st] = {
            "label": REGIME_LABEL[st], "days": int(len(g)), "share": r(len(g) / len(df) * 100, 1),
            "fwd21_mean": r(g["fwd21"].mean() * 100), "fwd21_median": r(g["fwd21"].median() * 100),
            "fwd21_win": r((g["fwd21"] > 0).mean() * 100, 1), "fwd21_p10": r(g["fwd21"].quantile(0.10) * 100),
            "fwd63_mean": r(g["fwd63"].mean() * 100), "fwd63_win": r((g["fwd63"] > 0).mean() * 100, 1),
            "fwd63_p10": r(g["fwd63"].quantile(0.10) * 100),
            "ann_vol": r(g["ret1"].std() * math.sqrt(252) * 100, 1),
            "ann_ret": r(g["ret1"].mean() * 252 * 100, 1),
            "worst_day": r(g["ret1"].min() * 100), "crash_prob_21": r((g["fwd21"] < -0.05).mean() * 100, 1),
        }
    base = {"fwd21_mean": r(df["fwd21"].mean() * 100), "fwd21_win": r((df["fwd21"] > 0).mean() * 100, 1),
            "fwd63_mean": r(df["fwd63"].mean() * 100), "crash_prob_21": r((df["fwd21"] < -0.05).mean() * 100, 1),
            "ann_vol": r(df["ret1"].std() * math.sqrt(252) * 100, 1)}
    # 轉移矩陣（月頻，看一個月後在哪個狀態）
    me = df.loc[month_ends(df.index)]
    nxt = me["state"].shift(-1)
    tm = pd.crosstab(me["state"], nxt, normalize="index").reindex(index=["bull", "range", "bear"],
                                                                      columns=["bull", "range", "bear"]).fillna(0)
    trans = {a: {b: r(tm.loc[a, b] * 100, 1) for b in tm.columns} for a in tm.index}
    # 策略：多頭 100% / 盤整 50% / 空頭 0%（T+1 執行），vs 買進持有
    expo = df["state"].map({"bull": 1.0, "range": 0.5, "bear": 0.0}).shift(1).fillna(0)
    strat = expo * df["ret1"]
    eq_s, eq_b = (1 + strat.fillna(0)).cumprod(), (1 + df["ret1"].fillna(0)).cumprod()
    rule = _me()
    ms = eq_s.resample(rule).last().pct_change()
    mb = eq_b.resample(rule).last().pct_change()
    # 月取樣的權益曲線給前端
    eqm = pd.DataFrame({"s": eq_s, "b": eq_b}).resample(rule).last().dropna()
    eps = regime_episodes(reg)
    return {"stats": stats, "base": base, "transition": trans,
            "strategy": {"rule": "多頭 100% SPY／盤整 50%／空頭 0%（現金 0%，次日執行）",
                         "strategy": perf_stats(ms), "buy_hold": perf_stats(mb)},
            "equity": {"dates": [d.strftime("%Y-%m") for d in eqm.index],
                       "strategy": [r(x, 3) for x in eqm["s"]], "buy_hold": [r(x, 3) for x in eqm["b"]]},
            "episodes": [e for e in eps if e["days"] >= 10][-40:],
            "n_switches": int(len(eps)), "period": [df.index[0].strftime("%Y-%m-%d"), df.index[-1].strftime("%Y-%m-%d")]}


def bt_sectors(panel, bench_adj, reg):
    """板塊動能：月底依 strength 排名，次月持有 Top3 / Bottom3 / 等權；RRG 象限前瞻；regime × 板塊熱圖。"""
    idx = bench_adj.index
    adj = pd.concat({s: panel[s]["adj"] for s in panel}, axis=1)
    strength = pd.concat({s: panel[s]["strength"] for s in panel}, axis=1)
    me = month_ends(idx)
    m_px = adj.loc[me]
    m_ret = m_px.pct_change().shift(-1)  # 次月報酬
    b_ret = bench_adj.loc[me].pct_change().shift(-1)
    m_str = strength.loc[me]
    rows_top, rows_bot, rows_all, rank_exc = [], [], [], {}
    for d in m_str.index:
        s = m_str.loc[d].dropna()
        rr = m_ret.loc[d]
        if len(s) < 6 or rr.dropna().empty:
            rows_top.append(np.nan); rows_bot.append(np.nan); rows_all.append(np.nan)
            continue
        order = s.sort_values(ascending=False).index
        rows_top.append(rr[order[:3]].mean())
        rows_bot.append(rr[order[-3:]].mean())
        rows_all.append(rr[s.index].mean())
        for k, sym in enumerate(order, 1):
            if not np.isnan(rr[sym]) and not np.isnan(b_ret[d]):
                rank_exc.setdefault(k, []).append(rr[sym] - b_ret[d])
    top, bot, allw = (pd.Series(v, index=m_str.index) for v in (rows_top, rows_bot, rows_all))
    valid = top.notna() & b_ret.notna()
    top, bot, allw, bch = top[valid], bot[valid], allw[valid], b_ret[valid]
    ls = top - bot
    eq = pd.DataFrame({"top3": (1 + top).cumprod(), "bottom3": (1 + bot).cumprod(),
                       "spy": (1 + bch).cumprod(), "ew": (1 + allw).cumprod()})
    by_rank = [{"rank": k, "exc_next_month": r(np.mean(v) * 100), "win": r((np.array(v) > 0).mean() * 100, 1), "n": len(v)}
               for k, v in sorted(rank_exc.items()) if len(v) >= 24]
    # 年度 Top3 − SPY
    yr = pd.DataFrame({"top": top, "spy": bch})
    yearly = yr.groupby(yr.index.year).apply(lambda g: ((1 + g["top"]).prod() - (1 + g["spy"]).prod()) * 100)
    # 不同回看期的 Top3−Bottom3（告訴使用者為什麼強度分數不含 1M）
    horizons = {}
    for name, h, skip in (("1m", 21, 0), ("3m", 63, 0), ("6m", 126, 0), ("12m", 252, 0), ("12-1", 252, 21)):
        sig = (adj.shift(skip) / adj.shift(h) - 1).loc[me]
        lsx = []
        for d in sig.index:
            s = sig.loc[d].dropna(); rr = m_ret.loc[d]
            if len(s) < 6 or rr.dropna().empty:
                continue
            o = s.sort_values(ascending=False).index
            lsx.append(rr[o[:3]].mean() - rr[o[-3:]].mean())
        lsx = pd.Series(lsx).dropna()
        horizons[name] = {"ann_mean": r(lsx.mean() * 12 * 100), "t_stat": r(lsx.mean() / lsx.std() * math.sqrt(len(lsx)), 2),
                          "win": r((lsx > 0).mean() * 100, 1), "months": int(len(lsx))}
    sector_mom = {
        "horizons": horizons,
        "top3": perf_stats(top), "bottom3": perf_stats(bot), "spy": perf_stats(bch), "equal_weight": perf_stats(allw),
        "long_short": {"ann_mean": r(ls.mean() * 12 * 100), "t_stat": r(ls.mean() / ls.std() * math.sqrt(len(ls)), 2),
                       "win": r((ls > 0).mean() * 100, 1), "months": int(len(ls))},
        "top3_beats_spy": r((top > bch).mean() * 100, 1),
        "by_rank": by_rank,
        "yearly_top3_minus_spy": {str(k): r(v, 1) for k, v in yearly.items()},
        "equity": {"dates": [d.strftime("%Y-%m") for d in eq.index], **{c: [r(x, 3) for x in eq[c]] for c in eq.columns}},
    }
    # RRG 象限 → 前瞻 21 日超額（每 5 日取樣減少重疊）
    quad_stats = {}
    for s in panel:
        d = panel[s]
        fwd = (d["adj"].shift(-21) / d["adj"] - 1) - (bench_adj.shift(-21) / bench_adj - 1)
        q = pd.Series([quadrant(a, b) for a, b in zip(d["rs_ratio"], d["rs_mom"])], index=d.index)
        sub = pd.DataFrame({"q": q, "f": fwd}).iloc[::5].dropna()
        for k, g in sub.groupby("q"):
            quad_stats.setdefault(k, []).extend(g["f"].tolist())
    rrg = {k: {"label": QUAD_LABEL[k], "exc21_mean": r(np.mean(v) * 100), "win": r((np.array(v) > 0).mean() * 100, 1), "n": len(v)}
           for k, v in quad_stats.items()}
    # regime × 板塊：各 regime 下板塊月超額報酬均值
    st_m = reg["state"].reindex(me)
    heat = {}
    for s in panel:
        exc = (m_ret[s] - b_ret)
        heat[s] = {st: r(exc[st_m == st].mean() * 100) for st in ("bull", "range", "bear")}
        heat[s]["win_bear"] = r((exc[st_m == "bear"] > 0).mean() * 100, 0)
    return {"sector_momentum": sector_mom, "rrg": rrg, "regime_heatmap": heat,
            "period": [str(top.index[0].date()), str(top.index[-1].date())]}


def bt_flows(panel, bench_adj):
    """資金流代理的預測力：月頻橫斷面 Spearman IC、五分位（Q5−Q1）、極端流入/流出後的前瞻超額。"""
    idx = bench_adj.index
    adj = pd.concat({s: panel[s]["adj"] for s in panel}, axis=1)
    flow = pd.concat({s: panel[s]["flow"] for s in panel}, axis=1)
    fpct = pd.concat({s: panel[s]["flow_pct"] for s in panel}, axis=1)
    me = month_ends(idx)
    nxt = adj.loc[me].pct_change().shift(-1).sub(bench_adj.loc[me].pct_change().shift(-1), axis=0)
    ics, q5, q1 = [], [], []
    for d in me:
        f, n = flow.loc[d], nxt.loc[d]
        ok = f.notna() & n.notna()
        if ok.sum() < 6:
            continue
        ics.append(f[ok].rank().corr(n[ok].rank()))
        order = f[ok].sort_values().index
        k = max(2, len(order) // 4)
        q1.append(n[order[:k]].mean()); q5.append(n[order[-k:]].mean())
    ics = pd.Series(ics)
    spread = pd.Series(q5) - pd.Series(q1)
    # 時序：板塊自身流向百分位 ≥80 / ≤20 之後 21 日超額
    hi, lo = [], []
    for s in panel:
        d = panel[s]
        fwd = (d["adj"].shift(-21) / d["adj"] - 1) - (bench_adj.shift(-21) / bench_adj - 1)
        sub = pd.DataFrame({"p": d["flow_pct"], "f": fwd}).iloc[::5].dropna()
        hi.extend(sub[sub["p"] >= 80]["f"].tolist()); lo.extend(sub[sub["p"] <= 20]["f"].tolist())
    return {"ic": {"mean": r(ics.mean(), 3), "std": r(ics.std(), 3), "t_stat": r(ics.mean() / ics.std() * math.sqrt(len(ics)), 2),
                   "pct_positive": r((ics > 0).mean() * 100, 1), "n_months": int(len(ics))},
            "quartile_spread": {"ann_mean": r(spread.mean() * 12 * 100), "win": r((spread > 0).mean() * 100, 1),
                                "t_stat": r(spread.mean() / spread.std() * math.sqrt(len(spread)), 2)},
            "extreme": {"inflow_ge80": {"exc21_mean": r(np.mean(hi) * 100), "win": r((np.array(hi) > 0).mean() * 100, 1), "n": len(hi)},
                        "outflow_le20": {"exc21_mean": r(np.mean(lo) * 100), "win": r((np.array(lo) > 0).mean() * 100, 1), "n": len(lo)}},
            "note": "流向＝Chaikin 式 20 日淨資金流 ÷ 20 日成交金額（價量代理，非 ETF 申贖實際流量）。"}


# ---------------------------------------------------------------- assemble
def latest_snapshot(data, reg, panel, watch):
    d = reg.dropna(subset=["score"]).index[-1]
    row = reg.loc[d]
    spy = data[BENCH]
    px = spy["adj"]
    hist_n = 504
    h = reg.loc[:d].tail(hist_n)
    ytd = px.loc[d] / px[px.index.year == d.year].iloc[0] - 1 if (px.index.year == d.year).any() else np.nan
    eps = regime_episodes(reg)
    cur = eps[-1] if eps else None
    pillars = {
        "trend": {"label": "趨勢", "score": r(row["trend"], 1), "weight": PILLAR_W["trend"],
                  "parts": {"價格 vs 200日線": r(row["t_dist200"], 0), "50日線 vs 200日線": r(row["t_golden"], 0), "200日線斜率": r(row["t_slope"], 0)}},
        "breadth": {"label": "廣度", "score": r(row["breadth"], 1), "weight": PILLAR_W["breadth"],
                    "parts": {"板塊站上200日線": r(row["b_above200"], 0), "板塊站上50日線": r(row["b_above50"], 0), "等權/小型股參與": r(row["b_particip"], 0)}},
        "vol": {"label": "波動", "score": r(row["vol"], 1), "weight": PILLAR_W["vol"],
                "parts": {"VIX 一年百分位": r(row["v_vix_pct"], 0), "VIX vs 50日均": r(row["v_vix_trend"], 0), "實現波動百分位": r(row["v_rv_pct"], 0)}},
        "credit": {"label": "信用", "score": r(row["credit"], 1), "weight": PILLAR_W["credit"],
                   "parts": {"HYG/IEF vs 63日均": r(row.get("c_level"), 0), "HYG/IEF 20日變化": r(row.get("c_change"), 0)}},
    }
    sectors = []
    for sym, zh, en in SECTORS:
        if sym not in panel:
            continue
        p = panel[sym].loc[d]
        trail = panel[sym].loc[:d, ["rs_ratio", "rs_mom"]].iloc[::-5].head(6).iloc[::-1]
        sectors.append({
            "symbol": sym, "name": zh, "name_en": en, "close": r(p["close"], 2),
            "ret": {k: r(p[f"ret_{k}"] * 100, 1) for k in ("1w", "1m", "3m", "6m", "1y")},
            "exc": {k: r(p[f"exc_{k}"] * 100, 1) for k in ("1w", "1m", "3m", "6m", "1y")},
            "above50": bool(p["above50"]), "above200": bool(p["above200"]),
            "strength": r(p["strength"], 0), "rs_ratio": r(p["rs_ratio"], 1), "rs_mom": r(p["rs_mom"], 1),
            "quadrant": quadrant(p["rs_ratio"], p["rs_mom"]),
            "trail": [[r(a, 1), r(b, 1)] for a, b in zip(trail["rs_ratio"], trail["rs_mom"])],
            "flow": {"intensity": r(p["flow"], 3), "pct": r(p["flow_pct"], 0), "label": flow_label(p["flow_pct"]),
                     "avg_1y": r(p["flow_avg_1y"], 3), "avg_5y": r(p["flow_avg_5y"], 3), "z_1y": r(p["flow_z1y"], 2),
                     "net20_usd": r(p["net20"] / 1e9, 2), "dv20_usd": r(p["dv20"] / 1e9, 1),
                     "share": r(p["share"] * 100, 1), "share_avg_1y": r(p["share_avg_1y"] * 100, 1)},
            "spark": [r(x, 2) for x in panel[sym]["adj"].loc[:d].tail(60).tolist()],
        })
    sectors.sort(key=lambda x: -(x["strength"] if x["strength"] is not None else -1))
    for i, s in enumerate(sectors, 1):
        s["rank"] = i
    flows_sorted = sorted([s for s in sectors if s["flow"]["pct"] is not None], key=lambda x: -x["flow"]["pct"])
    aux = {}
    for s in ("QQQ", "IWM", "RSP", "TLT", "GLD", "HYG"):
        if s in data:
            a = data[s]["adj"].reindex(reg.index).ffill()
            aux[s] = {"ret_1m": r(a.pct_change(21).loc[d] * 100, 1), "ret_3m": r(a.pct_change(63).loc[d] * 100, 1),
                      "exc_3m": r((a.pct_change(63) - px.pct_change(63)).loc[d] * 100, 1)}
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "asof": d.strftime("%Y-%m-%d"),
        "regime": {
            "state": row["state"], "label": REGIME_LABEL.get(row["state"]), "score": r(row["score"], 1),
            "since": cur["start"] if cur else None, "days": cur["days"] if cur else None,
            "thresholds": {"bull_in": BULL_IN, "bull_out": BULL_OUT, "bear_in": BEAR_IN, "bear_out": BEAR_OUT},
            "pillars": pillars,
            "spy": {"close": r(row["spy_close"], 2), "ma50": r(row["ma50"] / row["spy"] * row["spy_close"], 2),
                    "ma200": r(row["ma200"] / row["spy"] * row["spy_close"], 2), "dist200": r(row["dist200"] * 100, 1),
                    "ret_1m": r(px.pct_change(21).loc[d] * 100, 1), "ret_3m": r(px.pct_change(63).loc[d] * 100, 1), "ytd": r(ytd * 100, 1)},
            "vix": r(row["vix"], 2), "rv20": r(row["rv20"] * 100, 1),
            "breadth": {"pct_above200": r(row["pct_above200"] * 100, 0), "pct_above50": r(row["pct_above50"] * 100, 0)},
            "hyg_ief": r(row.get("hyg_ief"), 4),
            "history": {"dates": [x.strftime("%Y-%m-%d") for x in h.index], "score": [r(x, 1) for x in h["score"]],
                        "state": h["state"].tolist(), "spy": [r(x, 2) for x in h["spy_close"]],
                        "ma200": [r(x / y * z, 2) if not np.isnan(x) else None for x, y, z in zip(h["ma200"], h["spy"], h["spy_close"])]},
            "episodes": eps[-8:],
        },
        "sectors": sectors,
        "flows": {"ranking": [s["symbol"] for s in flows_sorted],
                  "total_net20_usd": r(sum((s["flow"]["net20_usd"] or 0) for s in sectors), 2),
                  "inflow": [s["symbol"] for s in flows_sorted if (s["flow"]["pct"] or 0) >= 60],
                  "outflow": [s["symbol"] for s in flows_sorted if (s["flow"]["pct"] or 100) <= 40]},
        "aux": aux,
        "watch": watch,
        "method": {
            "regime": "Regime Score = 趨勢40% + 廣度25% + 波動20% + 信用15%（各 −100…+100）。多頭：分數≥+25 且 SPY>200日線；空頭：≤−25 且 <200日線；離開門檻 +10/−10（遲滯），切換需連續 3 日確認。",
            "strength": "板塊強度 = 3M/6M/12M 相對 SPY 超額報酬的橫斷面百分位加權（30/40/30；1M 動能實證為反向故不納入）→ 0–100。RRG：JdK RS-Ratio（63日）/ RS-Momentum（21日）。",
            "flow": "資金流向 = Chaikin 20 日淨資金流 ÷ 20 日成交金額（價量代理）。百分位 = 該板塊自身過去 5 年的分位；對照 1 年均值與 5 年均值。",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=None, help="快取目錄（研究用；正式管線不快取）")
    ap.add_argument("--no-backtest", action="store_true")
    args = ap.parse_args()
    if args.cache:
        os.makedirs(args.cache, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    data = load_all(args.cache)
    missing = data.pop("_missing", [])
    if BENCH not in data:
        print("SPY 抓不到，放棄", file=sys.stderr)
        sys.exit(1)
    reg = build_regime(data)
    panel = build_sectors(data, reg.index)
    watch = build_watch(args.cache, reg.index, data[BENCH]["adj"])
    snap = latest_snapshot(data, reg, panel, watch)
    snap["missing"] = missing
    json.dump(snap, open(OUT_DATA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {OUT_DATA}: {snap['asof']} regime={snap['regime']['label']} score={snap['regime']['score']} "
          f"top={[s['symbol'] for s in snap['sectors'][:3]]} bottom={[s['symbol'] for s in snap['sectors'][-3:]]}")
    if not args.no_backtest:
        bt = {"generated": snap["generated"], "asof": snap["asof"],
              "regime": bt_regime(reg), "sectors": bt_sectors(panel, data[BENCH]["adj"], reg),
              "flows": bt_flows(panel, data[BENCH]["adj"]),
              "caveats": [
                  "所有回測皆為樣本內、無交易成本、ETF 價格含股息（Adj Close）；XLRE 2015、XLC 2018 才上市，之前的橫斷面只有 9–10 檔。",
                  "Regime 門檻與支柱權重是設計值，不是最佳化值——目的是可解釋，而非最高報酬。",
                  "資金流向是價量代理（Chaikin money flow），不是基金申贖資料；請把它當『買盤/賣盤強度』而非『真實資金』。",
              ]}
        json.dump(bt, open(OUT_BT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print(f"wrote {OUT_BT}")


if __name__ == "__main__":
    main()
