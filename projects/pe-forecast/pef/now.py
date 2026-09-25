"""「現在」的資料：任何美股代號 → 最新 12 季財報 ＋ 最新股價 → 可以直接餵給組合模型的一列。

來源（都是公開、每天更新的 GitHub 鏡像；原始檔不進版控，見 data/SOURCES.md）：
  財報：loosygoosie/sec-dataset data/companies/<CIK>.json   SEC companyfacts 整理版，每家最近 12 季
  股價：ozkanpakdil/top-us-stock-tickers tickers/all.csv    約 5,300 檔美股的每日收盤與市值；git 歷史＝每日時間序列
  代號 → CIK：loosygoosie data/tickers.json（SEC 官方對照表）
  2025-09 以前的月股價（算 12 個月報酬用）：S&P 500 的 Stooq 鏡像（hanumantjain）

注意：這些財報是「最後一次申報的數字」（重述後），只能用在「現在」的預測，不能拿來回測。
"""
import json
import os
import re

import numpy as np
import pandas as pd

from . import lab
from .data import fix_share_scale
from .features import quarterly_features

# Nasdaq 的產業分類 → 回測用的 GICS 代號（S&P 500 以外的公司用這個）
NASDAQ_TO_GICS = {"Technology": "gics_it", "Telecommunications": "gics_comm", "Health Care": "gics_health",
                  "Finance": "gics_fin", "Real Estate": "gics_re", "Energy": "gics_energy", "Utilities": "gics_util",
                  "Industrials": "gics_indu", "Consumer Discretionary": "gics_discr", "Consumer Staples": "gics_staples",
                  "Basic Materials": "gics_mat"}
NOT_COMMON = re.compile(r"preferred|depositary|warrant|\bright|\bunits?\b|\bnotes?\b|debenture|%|trust preferred|subordinated", re.I)
STALE_DAYS = 240         # 最新一季季末超過 240 天：模型沒看過這麼舊的財報，不給預測


def lg_quarters(path, ticker):
    """最近 12 季 → 標準季表（股數用分割調整後的 shares_diluted_adj；每股股利＝發放總額 ÷ 股數）。"""
    j = json.load(open(path))
    rows = []
    for x in j.get("quarterly", []):
        sh = x.get("shares_diluted_adj") or x.get("shares_diluted_filled") or x.get("shares_diluted")
        ni = x.get("net_income_parent") if x.get("net_income_parent") is not None else x.get("net_income")
        rows.append({"ticker": ticker, "period_end": pd.Timestamp(x["period_end"]), "filed": pd.Timestamp(x["filed"]),
                     "rev": x.get("revenue"), "gp": x.get("gross_profit"), "oi": x.get("operating_income"), "ni": ni,
                     "sh": sh, "inv": x.get("inventory"), "equity": x.get("total_equity_parent") or x.get("total_equity"),
                     "cash": (x.get("cash") or 0) + (x.get("short_term_investments") or 0), "debt": x.get("total_debt"),
                     "div_paid": x.get("dividends_paid"), "form": x.get("form", "")})
    if not rows:
        return None, j
    q = pd.DataFrame(rows).sort_values("period_end").reset_index(drop=True)
    for c in ("rev", "gp", "oi", "ni", "sh", "inv", "equity", "cash", "debt", "div_paid"):
        q[c] = pd.to_numeric(q[c], errors="coerce")
    q["sh"] = q["sh"].ffill()
    q["sh_now"] = q["sh"]
    q["dps_now"] = (q["div_paid"].fillna(0) / q["sh"]).where(q["sh"] > 0)
    # 可用日：季報（10-Q）季末 + 45 天，年報（10-K，第四季）+ 75 天（loosygoosie 的 filed 是最後一次申報，不能當可用日）
    q["avail"] = q["period_end"] + pd.to_timedelta(np.where(q["form"].astype(str).str.startswith("10-K"), 75, 45), unit="D")
    return q, j


def _split_adjust(px, splits, since="2025-01-01"):
    """月股價串接後，找出分割造成的跳動並把之前的價格換成今天的口徑。
    loosygoosie 只知道分割落在哪兩次申報之間，所以在那個窗口（前後各放寬 2 個月）找最接近 1/比例 的月跳動。"""
    px = px.copy()
    for s in splits or []:
        r = float(s.get("ratio") or 0)
        if r <= 0 or r == 1 or pd.Timestamp(s["date"]) < pd.Timestamp(since):
            continue
        lo = pd.Timestamp(s.get("after") or s["date"]) - pd.DateOffset(months=2)
        hi = pd.Timestamp(s["date"]) + pd.DateOffset(months=2)
        jumps = (px / px.shift(1)).dropna()
        jumps = jumps[(jumps.index >= lo) & (jumps.index <= hi)]
        if jumps.empty:
            continue
        k = (np.log(jumps) + np.log(r)).abs()
        m = k.idxmin()
        if k[m] < np.log(1.35):
            px[px.index < m] = px[px.index < m] / r
    return px


def build(lg_dir, oz_mapped, oz_monthly, stooq_dir, sp500_uni, tech_uni, price_date):
    """回傳 (季表, {ticker: (月底收盤 Series, 最後交易日)}, 名單)。每個 CIK 只取市值最大的普通股代號，其他代號當別名。"""
    oz = oz_mapped[oz_mapped["cik"].notna() & ~oz_mapped["name"].fillna("").str.contains(NOT_COMMON)].copy()
    oz["cik"] = oz["cik"].astype(int)
    hist = oz_monthly.copy()
    hist["date"] = pd.to_datetime(hist["date"])
    sp = sp500_uni.set_index("ticker")
    tech = tech_uni.set_index("ticker")
    sp_by_cik = {int(c): t for t, c in zip(sp500_uni["ticker"], sp500_uni["cik"])}
    Q, prices, meta = [], {}, []
    for cik, g in oz.groupby("cik"):
        path = os.path.join(lg_dir, f"{cik}.json")
        if not os.path.exists(path):
            continue
        g = g.sort_values("marketCap", ascending=False)
        t = g["symbol"].iloc[0]
        q, j = lg_quarters(path, t)
        if q is None or q["rev"].notna().sum() < 8 or q["ni"].notna().sum() < 8:
            continue
        h = hist[hist["symbol"] == t].set_index("date")["px"].dropna()
        h = h[h > 0]
        spt = sp_by_cik.get(cik)
        so = os.path.join(stooq_dir, f"{(spt or t).lower().replace('.', '-')}.us.txt") if stooq_dir else None
        if so and os.path.exists(so):
            d = pd.read_csv(so)
            d.columns = [c.strip("<>").lower() for c in d.columns]
            d["date"] = pd.to_datetime(d["date"].astype(str), format="%Y%m%d")
            old = d.set_index("date")["close"].resample("ME").last().dropna()
            old = old[(old.index >= "2024-06-30") & (old.index < h.index.min() if len(h) else True)]
            h = pd.concat([old, h]).sort_index()
        if len(h) < 2:
            continue
        h = h.groupby(h.index + pd.offsets.MonthEnd(0)).last()      # 月底對齊（7 月是 07-16 的快照）
        h = _split_adjust(h, j.get("splits"))
        q["sh_now"], _ = fix_share_scale(q, h)                  # 股數單位錯（千股／百萬股）→ 乘回來
        q["sh"] = q["sh_now"]
        prices[t] = (h, pd.Timestamp(price_date))
        if t in tech.index:
            sector = tech.loc[t, "sector"]
        elif spt is not None:
            sector = sp.loc[spt, "sector"]
        else:
            sector = NASDAQ_TO_GICS.get(str(g["industry"].iloc[0]), "other")
        Q.append(q)
        meta.append(dict(ticker=t, cik=cik, name=str(g["name"].iloc[0]), aliases=" ".join(g["symbol"].iloc[1:].tolist()),
                         sector=sector, gics=sp.loc[spt, "gics"] if spt is not None else "", in_sp500=spt is not None,
                         in_tech=t in tech.index, industry=str(g["industry"].iloc[0]), mc_oz=float(g["marketCap"].iloc[0]),
                         px_oz=float(g["close"].iloc[0] if "close" in g else g["price"].iloc[0]),
                         lg_share_check=str(j.get("checks", {}).get("share_scale", "")),
                         lg_splits=";".join(f"{s.get('date')}×{s.get('ratio')}" for s in (j.get("splits") or []))))
    return pd.concat(Q, ignore_index=True), prices, pd.DataFrame(meta)


def rows(Q, prices, meta, macro, now):
    """每家公司一列（最新一季＋最新股價），帶齊組合模型與盈餘模型要的特徵。"""
    now = pd.Timestamp(now)
    qf = quarterly_features(Q)
    ex = lab.quarter_extras(qf)
    y = macro.dropna(subset=["y10"]).iloc[-1]
    m = meta.set_index("ticker")
    out = []
    for t, g in qf.groupby("ticker"):
        g = g[g["rev_ttm"].notna() & g["ni_ttm"].notna()]
        if g.empty or t not in prices:
            continue
        px, last_day = prices[t]
        r = g.iloc[-1].copy()
        r["sh_now"] = g["sh_now"].iloc[-2:].max()          # 虧損季只揭露基本股數，取近兩季較大者
        p_now = float(px.iloc[-1])
        r["px"] = p_now
        r["mc"] = p_now * r["sh_now"]
        ratio = m.loc[t, "mc_oz"] / r["mc"] if r["mc"] > 0 else np.nan
        r["mc_check"] = ratio
        if not (0.5 < ratio < 2.0) and m.loc[t, "mc_oz"] > 0:  # 股數或分割口徑不對：改用交易所公布的市值
            r["mc"] = m.loc[t, "mc_oz"]
        p6 = px[px.index <= px.index[-1] - pd.DateOffset(months=6)]
        p12 = px[px.index <= px.index[-1] - pd.DateOffset(months=12)]
        r["ret6"] = np.log(p_now / p6.iloc[-1]) if len(p6) and p6.index[-1] >= px.index[-1] - pd.DateOffset(months=8) else np.nan
        r["ret12"] = np.log(p_now / p12.iloc[-1]) if len(p12) and p12.index[-1] >= px.index[-1] - pd.DateOffset(months=14) else np.nan
        r["y10"] = y["y10"]
        r["month"] = pd.Timestamp(now.year, now.month, 1)
        r["month_end"] = r["month"] + pd.offsets.MonthEnd(0)
        r["price_date"] = last_day
        r["fin_age_days"] = (now - r["period_end"]).days
        r["n_quarters"] = len(g)
        for k in ("sector", "gics", "name", "in_sp500", "in_tech", "aliases", "industry", "cik"):
            r[k] = m.loc[t, k]
        out.append(r)
    d = pd.DataFrame(out).reset_index(drop=True)
    d = d.drop(columns=[c for c in ("g_qoq", "g_qoq_prev", "oi_ttm", "dps_ttm") if c in d]).merge(
        ex, on=["ticker", "period_end"], how="left")
    d["ln_ps"] = np.log(d["mc"] / d["rev_ttm"])
    d["pe"] = d["mc"] / d["ni_ttm"]
    d["ep"] = d["ni_ttm"] / d["mc"]
    d["ep_c"] = d["ep"].clip(-0.3, 0.3)
    d["ln_pe"] = np.log(d["mc"] / d["ni_ttm"].where(d["ni_ttm"] > 0))
    d["stale"] = d["fin_age_days"] > 150
    d["too_old"] = d["fin_age_days"] > STALE_DAYS
    return lab.add_features(d)


IDX_FILES = (("ndx", "ndx"), ("sp400", "sp400"), ("sp600", "sp600"), ("rut", "rut"))


def index_tiers(idx_dir, meta, sp500_tickers, month="2026-09"):
    """每家公司屬於哪個指數（kovagent/indexkit 的成分股檔，<指數>-<月份>.parquet）。
    回傳 DataFrame：ticker、in_ndx、in_sp400、in_sp600、in_rut、tier（S&P 500 > S&P 400 > S&P 600 > Russell 2000 > 空白）。
    代號比對用主代號加別名（BRK.B / BRK-B 視為同一個）。"""
    norm = lambda t: str(t).upper().replace(".", "-").replace("/", "-")
    sets = {"sp500": {norm(t) for t in sp500_tickers}}
    for k, f in IDX_FILES:
        d = pd.read_parquet(os.path.join(idx_dir, f"{f}-{month}.parquet"))
        sets[k] = {norm(t) for t in d["ticker"].dropna()}
    rows = []
    for r in meta.itertuples():
        keys = {norm(r.ticker)} | {norm(x) for x in str(r.aliases).split() if x and x != "nan"}
        x = {f"in_{k}": bool(keys & sets[k]) for k in ("ndx", "sp400", "sp600", "rut")}
        sp5 = bool(r.in_sp500) or bool(keys & sets["sp500"])
        x["tier"] = ("S&P 500" if sp5 else "S&P 400" if x["in_sp400"] else "S&P 600" if x["in_sp600"]
                     else "Russell 2000" if x["in_rut"] else "")
        rows.append(dict(ticker=r.ticker, **x))
    return pd.DataFrame(rows)
