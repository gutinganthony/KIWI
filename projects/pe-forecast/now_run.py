#!/usr/bin/env python3
"""任何美股代號的「現在」預測（網頁的代號查詢用）。

    python3 now_run.py --lg <loosygoosie data/companies> --oz <ozkanpakdil tickers/all.csv 對上 CIK 的表> \
                       --ozm <月底股價表> --stooq <S&P 500 Stooq 目錄> [--train tech|sp500]

模型：組合模型（README §13），用 --train 指定的名單訓練到今天；財報來源與限制見 pef/now.py。
輸出：results/now_all.csv（每家一列：市值、TTM 淨利、目前本益比、3–36 個月的組合預測與成員）。
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import lab, now                          # noqa: E402
from pef.data import load_macro                   # noqa: E402
from pef.ensemble import OLD_H, EnsembleForecaster   # noqa: E402
from pef.forecast import PEForecaster             # noqa: E402
from pef.load import panel, panel_sp500           # noqa: E402

DATA = os.path.join(HERE, "data")
ASOF = pd.Timestamp("2026-09-30")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lg", required=True)
    ap.add_argument("--oz", required=True)
    ap.add_argument("--ozm", required=True)
    ap.add_argument("--stooq", required=True)
    ap.add_argument("--price-date", default="2026-09-24")
    ap.add_argument("--train", default="sp500", choices=["tech", "sp500"])
    a = ap.parse_args()
    sp = pd.read_csv(os.path.join(DATA, "universe_sp500.csv"), keep_default_na=False)
    tech = pd.read_csv(os.path.join(DATA, "universe.csv"), keep_default_na=False)
    Q, prices, meta = now.build(a.lg, pd.read_csv(a.oz), pd.read_csv(a.ozm), a.stooq, sp, tech, a.price_date)
    d = now.rows(Q, prices, meta, load_macro(DATA), ASOF)
    print(f"有財報＋股價：{len(d)} 家；其中 S&P 500 {int(d['in_sp500'].sum())} 家")
    df, qf = panel_sp500() if a.train == "sp500" else panel()
    fc = PEForecaster().fit(df, ASOF)
    ens = EnsembleForecaster().fit(df, qf, ASOF, old=fc)
    ok = ~d["too_old"] & d["sigma"].notna() & d["m_bar"].notna() & (d["mc"] > 0)
    v = d[ok].reset_index(drop=True)
    e = ens.predict(v)
    keep = ["ticker", "name", "aliases", "cik", "sector", "gics", "industry", "in_sp500", "in_tech", "price_date", "px", "mc",
            "mc_check", "ni_ttm", "rev_ttm", "oi_ttm", "pe", "period_end", "fin_age_days", "n_quarters", "stale", "y10"]
    out = v[keep].join(e.drop(columns=["ticker", "month"]))
    skipped = d[~ok][keep]
    out = pd.concat([out, skipped.assign(too_old=True)], ignore_index=True)
    out.to_csv(os.path.join(HERE, "results", "now_all.csv"), index=False, float_format="%.6g")
    # 沒有季報的代號（外國公司只交年報、ETF 以外的其他普通股）：網頁只帶入市值，淨利讓使用者自己填
    oz = pd.read_csv(a.oz)
    oz = oz[~oz["name"].fillna("").str.contains(now.NOT_COMMON) & (oz["marketCap"] > 0)]
    have = set(out["ticker"]) | {x for s_ in out["aliases"].fillna("") for x in s_.split()}
    mc_only = oz[~oz["symbol"].isin(have)]
    mc_only = mc_only.assign(px=mc_only["close"] if "close" in mc_only else mc_only["price"])[["symbol", "name", "marketCap", "px", "industry"]]
    mc_only.columns = ["ticker", "name", "mc", "px", "industry"]
    mc_only.to_csv(os.path.join(HERE, "results", "now_mc_only.csv"), index=False, float_format="%.6g")
    print(f"只有市值（沒有季報）：{len(mc_only)} 檔 → results/now_mc_only.csv")
    print(f"給預測：{int(ok.sum())} 家；財報過舊或季數不足：{int((~ok).sum())} 家 → results/now_all.csv")


if __name__ == "__main__":
    main()
