"""「現在」快照：把任何來源的最新財報＋最新股價，組成模型要的一列，交給已經訓練好的模型。

回測用的是 data/quarters*.csv（時點正確的第一次申報值）；快照只需要「今天的一列」，
所以可以混用較新的來源（yennanliu 的財報 CSV、AXIOM 的最近幾季、kotoba 的 companyfacts）。
每一列都記錄：財報最新季、資料來源、股價來源、是否資料落後。
"""
import json
import os

import numpy as np
import pandas as pd

from .data import company_quarters
from .features import quarterly_features

STALE_DAYS = 150     # 最新一季季末距今超過 150 天 → 下一季應已公告，標為「財報落後」


# ----------------------------------------------------------------------------- 財報來源
def yen_quarters(path, ticker):
    """yennanliu/finance_data 的 fundamentals CSV → 標準季表。

    注意：它的 filed 是「最後一次申報」、數字是重述後的值，只能用在快照，不能用在回測。
    """
    d = pd.read_csv(path, parse_dates=["period_end", "filed"])
    q = pd.DataFrame({
        "ticker": ticker, "period_end": d["period_end"], "filed": d["filed"],
        "rev": d["revenue"], "gp": d["gross_profit"], "oi": d["operating_income"], "ni": d["net_income"],
        "sh": d["shares_diluted"].where(d["shares_diluted"] > 0),
        "inv": np.nan, "equity": d["total_equity"],
        "cash": d["cash_and_equiv"].fillna(0) + d["short_term_investments"].fillna(0),
        "debt": d["long_term_debt"].fillna(0) + d["short_term_debt"].fillna(0)})
    q["sh"] = q["sh"].fillna(q["ni"] / d["eps_diluted"].where(d["eps_diluted"].abs() > 0.01)).ffill()
    q["sh_now"] = q["sh"]
    q["avail"] = q["period_end"] + pd.Timedelta(days=45)
    return q.sort_values("period_end").reset_index(drop=True)


def axiom_append(q, path):
    """在既有季表後面接上 AXIOM 的最近幾季（只有營收、淨利、稀釋股數；毛利與資產負債表沿用最後一季）。"""
    j = json.load(open(path))
    rows = {}
    for x in j:
        if x.get("period_type") != "duration":
            continue
        k = pd.Timestamp(x["period_end"])
        if (k - pd.Timestamp(x["period_start"])).days > 100:
            continue
        rows.setdefault(k, {})[x["metric"]] = float(x["value"])
        rows[k]["filed"] = pd.Timestamp(x["filed_at"][:10])
    last = q["period_end"].max()
    add = []
    for k, v in sorted(rows.items()):
        if k <= last + pd.Timedelta(days=20) or "revenue" not in v or "net_income" not in v:
            continue
        add.append({"ticker": q["ticker"].iloc[0], "period_end": k, "filed": v["filed"], "rev": v["revenue"],
                    "ni": v["net_income"], "sh": v.get("diluted_shares_outstanding", np.nan)})
    if not add:
        return q, 0
    a = pd.DataFrame(add)
    tail = q.iloc[-1]
    for c in ("equity", "cash", "debt", "inv"):
        a[c] = tail.get(c, np.nan)
    a["gp"] = np.nan
    a["oi"] = np.nan
    a["sh"] = a["sh"].fillna(tail["sh"])
    a["sh_now"] = a["sh"]          # AXIOM 的股數是申報當時口徑；之後若有分割，由 snapshot_run 的價格口徑檢查補上
    a["avail"] = a["filed"]
    return pd.concat([q, a], ignore_index=True).sort_values("period_end").reset_index(drop=True), len(a)


def facts_quarters(path, ticker):
    q, splits = company_quarters(path, ticker)
    return q


# ----------------------------------------------------------------------------- 股價來源
def monthly_close(path, kind):
    """回傳月底收盤（最新口徑、只做分割還原或總報酬還原都可；快照只用最新價與 6 個月報酬）。"""
    if kind == "blake":
        d = pd.read_csv(path, parse_dates=["date"]).set_index("date")["close"]
    elif kind == "yen":
        d = pd.read_csv(path, parse_dates=["date"]).set_index("date")["close"]
    elif kind == "stell0":
        d = pd.read_csv(path, index_col=0, parse_dates=True)["Close"]
    elif kind == "natezone":
        d = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")["Close"]
    else:
        raise ValueError(kind)
    d = d.dropna()
    d = d[d > 0]
    return d.resample("ME").last().dropna(), d.index.max()


# ----------------------------------------------------------------------------- 組一列
def snapshot_rows(quarters, prices, macro, sectors, now):
    """quarters：標準季表（多家）；prices：{ticker: (月底收盤 Series, 最後交易日)}。回傳可餵給 predict 的列。"""
    now = pd.Timestamp(now)
    qf = quarterly_features(quarters)
    y = macro.dropna(subset=["y10"]).iloc[-1]
    out = []
    for t, g in qf.groupby("ticker"):
        g = g[g["rev_ttm"].notna() & g["ni_ttm"].notna()]
        if t not in prices or g.empty:
            continue
        px, last_day = prices[t]
        r = g.iloc[-1].copy()
        age = (now - r["period_end"]).days
        p_now = px.iloc[-1]
        p_6m = px[px.index <= px.index[-1] - pd.DateOffset(months=6)]
        r["mc"] = p_now * r["sh_now"]
        r["ret6"] = np.log(p_now / p_6m.iloc[-1]) if len(p_6m) else np.nan
        r["ln_ps"] = np.log(r["mc"] / r["rev_ttm"])
        r["pe"] = r["mc"] / r["ni_ttm"]
        r["ep"] = r["ni_ttm"] / r["mc"]
        r["ep_c"] = np.clip(r["ep"], -0.3, 0.3)
        r["y10"], r["infl"] = y["y10"], y.get("infl", np.nan)
        r["month"] = pd.Timestamp(now.year, now.month, 1)
        r["month_end"] = r["month"] + pd.offsets.MonthEnd(0)
        r["sector"] = sectors.get(t, "")
        r["price"], r["price_date"] = p_now, last_day
        r["fin_age_days"] = age
        r["stale"] = age > STALE_DAYS
        r["n_quarters"] = len(g)
        out.append(r)
    return pd.DataFrame(out).reset_index(drop=True)
