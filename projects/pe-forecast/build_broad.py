#!/usr/bin/env python3
"""S&P 500 全體的季表與月市值（回測用，2009 → 2025-09）。

    python3 build_broad.py --hj <hanumantjain/sp500_agentic_ai 的 data 目錄>

來源（都在同一個公開鏡像）：
  company_facts/CIK*.json              SEC companyfacts（財報，取第一次申報值，同 pef/data.py）
  sp500_stooq_ohcl/<t>.us.txt          Stooq 日股價（有做股利與分割還原）
  sp500_corporate_actions_yfinance.csv 每一次除息（日期、金額）與分割（含「分拆」記成的非整數比例）
  S_and_P_500_component_stocks.csv     名單、CIK、GICS 產業

和科技股版（build_data.py）的差別：
  1. 股利還原用「每一次除息日與金額」逐日拿掉，不再用財報每股股利近似。
  2. 分拆（例：3M 2024-04 的 1.196）在 Stooq 裡的處理不一致，分拆日以前的月份直接不用（無法人工逐家檢查）。
產出：data/quarters_sp500.csv、prices_monthly_sp500.csv、universe_sp500.csv、build_log_sp500.csv。
"""
import argparse
import os

import numpy as np
import pandas as pd

from pef.data import REV, company_quarters, fix_share_scale

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
REV_BROAD = REV + ["RevenuesNetOfInterestExpense"]      # 銀行：淨利息收入＋非利息收入
SKIP = {"GOOG", "FOX", "NWS"}                           # 同一家公司的第二種股票，只留一種
SPLIT_RATIOS = [2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20, 25, 30, 40, 50, 1.5, 2.5, 1.25, 4 / 3, 5 / 3]
GICS_SLUG = {"Information Technology": "gics_it", "Communication Services": "gics_comm", "Consumer Discretionary": "gics_discr",
             "Consumer Staples": "gics_staples", "Health Care": "gics_health", "Financials": "gics_fin", "Industrials": "gics_indu",
             "Energy": "gics_energy", "Utilities": "gics_util", "Real Estate": "gics_re", "Materials": "gics_mat"}


def is_split(r):
    """整數或常見分數比例（含反分割）＝分割；其他（1.196 這種）＝分拆被記成分割。"""
    for k in SPLIT_RATIOS:
        if abs(r - k) / k < 0.01 or abs(1 / r - k) / k < 0.01:
            return True
    return False


def stooq_daily(path):
    d = pd.read_csv(path)
    d.columns = [c.strip("<>").lower() for c in d.columns]
    d["date"] = pd.to_datetime(d["date"].astype(str), format="%Y%m%d")
    return d.set_index("date")["close"].sort_index()


def unadjust_daily(adj, divs):
    """Stooq 股利還原：A(t) = P(t) × Π_{除息日 d > t}(1 − y_d)。用每次除息的金額 D（今日分割口徑）逐一反推 y_d。"""
    F = pd.Series(1.0, index=adj.index)
    f_after = 1.0
    for ex, D in divs.sort_index(ascending=False).items():
        before = adj[adj.index < ex]
        if before.empty or not (D > 0):
            continue
        c = D * f_after / before.iloc[-1]
        if c > 0.5:                    # 單次股利 > 股價一半：資料錯，略過
            continue
        y = c / (1 + c)
        f_after *= (1 - y)
        F[F.index < ex] = f_after
    return adj / F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hj", required=True)
    a = ap.parse_args()
    comp = pd.read_csv(os.path.join(a.hj, "S_and_P_500_component_stocks.csv"), encoding="latin-1")
    comp.columns = ["ticker", "name", "gics", "sub", "hq", "added", "cik", "founded"]
    act = pd.read_csv(os.path.join(a.hj, "sp500_corporate_actions_yfinance.csv"), parse_dates=["ex_date"])
    tech = pd.read_csv(os.path.join(DATA, "universe.csv"), keep_default_na=False).set_index("ticker")
    qs, ps, log, uni = [], [], [], []
    for r in comp.itertuples():
        t = r.ticker
        if t in SKIP:
            continue
        fp = os.path.join(a.hj, "company_facts", f"CIK{int(r.cik):010d}.json")
        sp = os.path.join(a.hj, "sp500_stooq_ohcl", f"{t.lower().replace('.', '-')}.us.txt")
        sector = tech.loc[t, "sector"] if t in tech.index else GICS_SLUG.get(r.gics, "gics_other")
        row = dict(ticker=t, cik=int(r.cik), sector=sector, gics=r.gics, start="", end="", note="")
        if not (os.path.exists(fp) and os.path.exists(sp)):
            log.append(dict(ticker=t, gics=r.gics, status="missing"))
            continue
        q, splits = company_quarters(fp, t, REV_BROAD)
        if q is None or q["rev"].notna().sum() < 12:
            log.append(dict(ticker=t, gics=r.gics, status="no revenue"))
            continue
        a_t = act[act["symbol"] == t]
        spins = a_t[(a_t["event_type"] == "split") & (a_t["ex_date"] >= "2008-01-01")]
        spins = spins[~spins["ratio"].apply(is_split)]
        start = None
        if len(spins):
            start = spins["ex_date"].max() + pd.offsets.MonthEnd(0)
            row["start"] = str(start.date())
            row["note"] = "分拆 " + ";".join(f"{d.date()}×{x:g}" for d, x in zip(spins["ex_date"], spins["ratio"]))
        # 科技股名單裡人工標過的區間（分拆、合併）沿用：取較晚的起點
        if t in tech.index:
            ts, te = tech.loc[t, "start"], tech.loc[t, "end"]
            if ts and (not row["start"] or ts > row["start"]):
                row["start"] = ts
            if te:
                row["end"] = te
        start = pd.Timestamp(row["start"]) if row["start"] else None
        end = pd.Timestamp(row["end"]) if row["end"] else None
        if start is not None:
            q = q[q["period_end"] >= start]
        if end is not None:
            q = q[q["period_end"] <= end]
        if q["rev"].notna().sum() < 8:
            log.append(dict(ticker=t, gics=r.gics, status="too short after spin-off cut"))
            continue
        adj = stooq_daily(sp)
        divs = a_t[a_t["event_type"] == "dividend"].set_index("ex_date")["cash_amount"].dropna()
        raw = unadjust_daily(adj, divs[divs.index > adj.index.min()])
        px_m = raw.resample("ME").last().dropna()
        q = q.copy()
        q["sh_now"], n_fix = fix_share_scale(q, px_m)          # 股數單位錯（千股／百萬股）→ 乘回來
        q["sh"] = q["sh_now"] / q["split_fac"]
        q["rev_ttm_chk"] = q["rev"].rolling(4, min_periods=4).sum()
        sh = q[["avail", "sh_now", "rev_ttm_chk"]].dropna(subset=["sh_now"]).sort_values("avail")
        px = pd.DataFrame({"month_end": px_m.index, "px": px_m.values})
        px = pd.merge_asof(px, sh, left_on="month_end", right_on="avail", direction="backward")
        px["mc"] = px["px"] * px["sh_now"]
        # 修不回來的股數（合併前空殼公司的 100 股之類）：市銷率 < 0.02 或 > 5000 倍 → 那個月不用
        ps_chk = px["mc"] / px["rev_ttm_chk"]
        px = px[~((ps_chk < 0.02) | (ps_chk > 5000))]
        q = q.drop(columns=["rev_ttm_chk"])
        px["ticker"] = t
        px["month"] = px["month_end"] - pd.offsets.MonthBegin(1)
        if start is not None:
            px = px[px["month_end"] >= start]
        if end is not None:
            px = px[px["month_end"] <= end]
        px = px[px["month_end"] >= "2008-01-01"].dropna(subset=["mc"])
        ps.append(px[["ticker", "month", "mc", "px"]])
        qs.append(q)
        uni.append(row)
        log.append(dict(ticker=t, gics=r.gics, status="ok", quarters=int(q["rev"].notna().sum()),
                        first=str(q["period_end"].min().date()), last=str(q["period_end"].max().date()),
                        px_last=str(px["month_end"].max().date()) if len(px) else "",
                        splits=";".join(f"{d.date()}:{v:g}" for d, v in splits.items()), note=row["note"],
                        share_scale_fixed=n_fix))
    cols = ["ticker", "period_end", "filed", "avail", "rev", "gp", "oi", "ni", "sh", "split_fac", "sh_now", "dps", "dps_now",
            "inv", "equity", "cash", "debt"]
    Q = pd.concat(qs, ignore_index=True)
    Q[cols].to_csv(os.path.join(DATA, "quarters_sp500.csv"), index=False, float_format="%.6g")
    pd.concat(ps, ignore_index=True).to_csv(os.path.join(DATA, "prices_monthly_sp500.csv"), index=False, float_format="%.6g")
    pd.DataFrame(uni).to_csv(os.path.join(DATA, "universe_sp500.csv"), index=False)
    lg = pd.DataFrame(log)
    lg.to_csv(os.path.join(DATA, "build_log_sp500.csv"), index=False)
    print(lg.groupby(["gics", "status"]).size().unstack(fill_value=0).to_string())
    print(f"\nquarters: {len(Q)} 列；公司：{len(uni)}")


if __name__ == "__main__":
    main()
