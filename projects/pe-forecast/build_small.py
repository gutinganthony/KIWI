#!/usr/bin/env python3
"""中小型股（Russell 2000、S&P 400、S&P 600）的季頻資料，2019-12 → 2026-09，回測用。

    python3 build_small.py --idx <indexkit 成分股 parquet 目錄> --v2 <loosygoosie data/v2/companies> \
                           --tickers <loosygoosie data/tickers.json> --v2u <loosygoosie data/v2/universe.csv>

股價：指數 ETF（IWM、IJH、IJR）每季向 SEC 申報的持股明細（N-PORT）：持有股數與市值 → 季末股價＝市值 ÷ 股數。
      2026-09 用 iShares 每日持股檔。持股明細只有公司名稱與 CUSIP，用正規化名稱對到 SEC 的公司代碼，再用 CUSIP 串起不同季。
      對不到的多半是已下市或被併購的公司 → 這份回測只有「活到 2026 年」的公司（倖存者偏差）。
財報：loosygoosie v2 的逐季資料（2008 起：營收、淨利、稀釋股數、現金、權益、負債；沒有毛利、營業利益、存貨）。
      可用日＝季報季末 +45 天、年報 +75 天。數字是之後申報的版本（可能重述），不是第一次申報值。
分割：同一檔 ETF 持有股數在一季內跳成整數倍、股價反向跳 → 認定為分割，之前的股價換成最新口徑；股數同理。
股數單位錯（有些季以千股、百萬股申報）：pef.data.fix_share_scale 用市銷率找出可信季，差 10^3／10^6 倍的季乘回來。
S&P 500 公司不放進來（它們在 build_broad.py 的月頻資料裡）。
產出：data/quarters_small.csv、prices_quarterly_small.csv、members_small.csv、universe_small.csv、build_log_small.csv
"""
import argparse
import glob
import json
import os
import re

import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef.data import fix_share_scale                     # noqa: E402

DATA = os.path.join(HERE, "data")
SUFFIX = (r"\b(INCORPORATED|INC|CORPORATION|CORP|COMPANY|CO|LIMITED|LTD|PLC|HOLDINGS?|GROUP|THE|NV|N V|SA|AG|LLC|LP|L P|"
          r"CLASS [A-Z]|CL [A-Z]|COMMON STOCK|COMMON|SHS|SHARES|ORDINARY|REIT|TRUST|BANCORP|BANCSHARES)\b")
SPLITS = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 1.5, 2.5, 1.25]
IDX_ZH = {"rut": "Russell 2000", "sp400": "S&P 400", "sp600": "S&P 600"}


def nn(s):
    s = str(s).upper().replace("&", " AND ")
    s = re.sub(r"/[A-Z]{2}/?|\\[A-Z]{2}\\?", " ", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(SUFFIX, " ", s)
    return re.sub(r"\s+", "", s)


def sic_sector(sic):
    """SIC 產業碼 → 回測用的 GICS 代號（粗略）。"""
    try:
        s = int(sic)
    except (TypeError, ValueError):
        return "other"
    if 1300 <= s <= 1399 or 2900 <= s <= 2999:
        return "gics_energy"
    if 1000 <= s <= 1499 or 2600 <= s <= 2699 or 2800 <= s <= 2829 or 3300 <= s <= 3399:
        return "gics_mat"
    if 2830 <= s <= 2836 or 3841 <= s <= 3851 or 8000 <= s <= 8099 or 8731 == s:
        return "gics_health"
    if 3570 <= s <= 3579 or 3600 <= s <= 3699 or 7370 <= s <= 7379 or 3820 <= s <= 3829:
        return "gics_it"
    if 4800 <= s <= 4899 or 2700 <= s <= 2799 or 7800 <= s <= 7899:
        return "gics_comm"
    if 4900 <= s <= 4999:
        return "gics_util"
    if 6500 <= s <= 6599 or s == 6798:
        return "gics_re"
    if 6000 <= s <= 6799:
        return "gics_fin"
    if 2000 <= s <= 2199 or 5400 <= s <= 5499 or 2840 <= s <= 2844:
        return "gics_staples"
    if 5000 <= s <= 5999 or 7000 <= s <= 7299 or 2300 <= s <= 2399 or 3710 <= s <= 3716 or 7900 <= s <= 7999:
        return "gics_discr"
    return "gics_indu"


def holdings(idx_dir, tickers, v2u):
    rows = []
    for f in sorted(glob.glob(os.path.join(idx_dir, "*.parquet"))):
        idx = os.path.basename(f).split("-")[0]
        if idx not in IDX_ZH:
            continue
        d = pd.read_parquet(f)
        if d["source"].iloc[0] == "ishares_cdn":
            d = d[d["as_of"] == d["as_of"].max()]
        rows.append(d.assign(idx=idx)[["idx", "as_of", "ticker", "name", "cusip", "shares", "market_value_usd"]])
    H = pd.concat(rows, ignore_index=True)
    H = H[(H["shares"] > 0) & (H["market_value_usd"] > 0)].copy()
    name2cik = {}
    for v in tickers.values():
        name2cik.setdefault(nn(v["name"]), set()).add(v["cik"])
    for r in v2u.itertuples():
        name2cik.setdefault(nn(r.name), set()).add(r.cik)
    t2c = {k.upper().replace(".", "-"): v["cik"] for k, v in tickers.items()}
    H["cik"] = H["ticker"].map(lambda t: t2c.get(str(t).upper().replace(".", "-").replace(" ", "-")) if isinstance(t, str) and t else None)
    by_name = H["name"].map(lambda s: next(iter(name2cik[nn(s)])) if nn(s) in name2cik and len(name2cik[nn(s)]) == 1 else None)
    H["cik"] = H["cik"].fillna(by_name)
    ok = H["cusip"].notna() & (H["cusip"] != "")
    cmap = H[ok & H["cik"].notna()].groupby("cusip")["cik"].agg(lambda s: s.mode().iloc[0])
    m = H["cik"].isna() & ok
    H.loc[m, "cik"] = H.loc[m, "cusip"].map(cmap)
    H["date"] = (pd.to_datetime(H["as_of"]) + pd.offsets.MonthEnd(0)).astype("datetime64[ns]")
    H["px"] = H["market_value_usd"] / H["shares"]
    return H


def price_series(h):
    """一家公司的季末股價（最新口徑）。分割：同一檔 ETF 持股數整數倍跳動、股價反向跳動。回傳 (Series, 分割清單)。"""
    p = h.groupby("date")["px"].median().sort_index()
    splits = []
    for idx, g in h.groupby("idx"):
        g = g.groupby("date")[["shares", "px"]].median().sort_index()
        rs, rp = g["shares"] / g["shares"].shift(1), g["px"] / g["px"].shift(1)
        for dt in g.index[1:]:
            for k in SPLITS + [1 / s for s in SPLITS]:
                if abs(rs[dt] / k - 1) < 0.1 and 0.5 < rp[dt] * k < 2.0:
                    splits.append((dt, k))
                    break
    seen = {}
    for dt, k in splits:
        seen.setdefault(dt, k)
    for dt, k in sorted(seen.items()):
        p[p.index < dt] = p[p.index < dt] / k
    return p, sorted(seen.items())


def v2_quarters(path, splits):
    j = json.load(open(path))
    rows = []
    for x in j.get("v2_quarterly", []):
        src = x.get("src", {}).get("revenue") or x.get("src", {}).get("net_income") or {}
        rows.append({"period_end": pd.Timestamp(x["end"]), "rev": x.get("revenue"), "ni": x.get("net_income"),
                     "sh": x.get("shares_diluted"), "cash": x.get("cash_and_sti", x.get("cash")), "equity": x.get("equity"),
                     "debt": x.get("total_debt"), "form": src.get("form", "")})
    if not rows:
        return None, j
    q = pd.DataFrame(rows).sort_values("period_end").drop_duplicates("period_end", keep="last").reset_index(drop=True)
    for c in ("rev", "ni", "sh", "cash", "equity", "debt"):
        q[c] = pd.to_numeric(q[c], errors="coerce").astype(float)
    q = q[q["rev"].notna() & (q["rev"] > 0)].reset_index(drop=True)
    # 股數換成最新口徑：分割前的季，如果股數約是分割後的 1/k，乘上 k
    for dt, k in splits:
        post = q[q["period_end"] >= dt]["sh"].dropna()
        if post.empty:
            continue
        ref = post.iloc[:2].median()
        pre = q["period_end"] < dt
        ratio = q.loc[pre, "sh"] / ref
        fix = pre & (ratio.reindex(q.index) * k).between(0.6, 1.6)
        q.loc[fix, "sh"] = q.loc[fix, "sh"] * k
    q["sh"] = q["sh"].ffill()
    q["sh_now"] = q["sh"]
    for c in ("gp", "oi", "inv", "dps_now"):
        q[c] = np.nan
    q["avail"] = q["period_end"] + pd.to_timedelta(np.where(q["form"].astype(str).str.startswith("10-K"), 75, 45), unit="D")
    q["avail"] = q["avail"].astype("datetime64[ns]")
    q["period_end"] = q["period_end"].astype("datetime64[ns]")
    q["filed"] = q["avail"]
    return q, j


def main():
    ap = argparse.ArgumentParser()
    for k in ("idx", "v2", "tickers", "v2u"):
        ap.add_argument(f"--{k}", required=True)
    a = ap.parse_args()
    tickers = json.load(open(a.tickers))
    v2u = pd.read_csv(a.v2u)
    sp = pd.read_csv(os.path.join(DATA, "universe_sp500.csv"), keep_default_na=False)
    sp_ciks = set(sp["cik"].astype(int))
    H = holdings(a.idx, tickers, v2u)
    cik2ts = {}
    for t, v in tickers.items():
        cik2ts.setdefault(v["cik"], []).append(t)
    pick = lambda ts: min(ts, key=lambda t: ("-" in t, len(t), t))
    sic = dict(zip(v2u["cik"], v2u["sic"]))
    Q, P, M, U, log = [], [], [], [], []
    for cik, h in H[H["cik"].notna()].groupby("cik"):
        cik = int(cik)
        if cik in sp_ciks:
            continue
        path = os.path.join(a.v2, f"{cik}.json")
        if not os.path.exists(path):
            log.append(dict(cik=cik, status="no v2"))
            continue
        px, splits = price_series(h)
        q, j = v2_quarters(path, splits)
        if q is None or len(q) < 12 or q["ni"].notna().sum() < 12:
            log.append(dict(cik=cik, status="short financials"))
            continue
        cur = h["ticker"].dropna()
        cur = cur[cur != ""]
        t = cur.iloc[-1].replace(".", "-") if len(cur) else (pick(cik2ts[cik]) if cik in cik2ts else f"CIK{cik}")
        q["ticker"] = t
        q["sh_now"], n_fix = fix_share_scale(q, px)              # 股數單位錯（千股／百萬股）→ 乘回來
        q["sh"] = q["sh_now"]
        q["rev_ttm_chk"] = q["rev"].rolling(4, min_periods=4).sum()
        sh = q[["avail", "sh_now", "rev_ttm_chk"]].dropna(subset=["sh_now"]).sort_values("avail")
        p = pd.DataFrame({"month_end": pd.DatetimeIndex(px.index).astype("datetime64[ns]"), "px": px.values})
        p = pd.merge_asof(p, sh, left_on="month_end", right_on="avail", direction="backward")
        p["mc"] = p["px"] * p["sh_now"]
        # 股數單位錯修不回來的季（前後都錯、沒有可信季）：市銷率 < 0.02 或 > 5000 倍 → 那一季不用
        ps = p["mc"] / p["rev_ttm_chk"]
        p = p[~((ps < 0.02) | (ps > 5000))]
        q = q.drop(columns=["rev_ttm_chk"])
        p["ticker"] = t
        p["month"] = p["month_end"] - pd.offsets.MonthBegin(1)
        # 市值一季跳 3 倍以上而營收沒跟著變：股數或分割口徑可疑 → 那一季不用
        jump = (np.log(p["mc"] / p["mc"].shift(1))).abs() > np.log(3)
        p = p[~jump & p["mc"].notna()]
        Q.append(q)
        P.append(p[["ticker", "month", "mc", "px"]])
        mem = h.groupby(["date", "idx"]).size().reset_index()[["date", "idx"]]
        mem["ticker"] = t
        M.append(mem)
        U.append(dict(ticker=t, cik=cik, name=str(h["name"].iloc[-1]), sector=sic_sector(sic.get(cik)), sic=sic.get(cik),
                      splits=";".join(f"{d.date()}×{k:g}" for d, k in splits)))
        log.append(dict(cik=cik, ticker=t, status="ok", quarters=len(q), prices=len(p), splits=len(splits), share_scale_fixed=n_fix))
    cols = ["ticker", "period_end", "filed", "avail", "rev", "gp", "oi", "ni", "sh", "sh_now", "dps_now", "inv", "equity", "cash", "debt"]
    pd.concat(Q, ignore_index=True)[cols].to_csv(os.path.join(DATA, "quarters_small.csv"), index=False, float_format="%.6g")
    pd.concat(P, ignore_index=True).to_csv(os.path.join(DATA, "prices_quarterly_small.csv"), index=False, float_format="%.6g")
    pd.concat(M, ignore_index=True).to_csv(os.path.join(DATA, "members_small.csv"), index=False)
    pd.DataFrame(U).to_csv(os.path.join(DATA, "universe_small.csv"), index=False)
    lg = pd.DataFrame(log)
    lg.to_csv(os.path.join(DATA, "build_log_small.csv"), index=False)
    print(lg["status"].value_counts().to_string())
    print(f"持股明細對到公司的列：{H['cik'].notna().mean():.1%}；排除 S&P 500 後建檔 {len(U)} 家")


if __name__ == "__main__":
    main()
