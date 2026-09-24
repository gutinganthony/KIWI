#!/usr/bin/env python3
"""把原始資料（SEC companyfacts JSON + Stooq 日股價）轉成模型用的兩張小表。

    python3 build_data.py --facts <較新 companyfacts 目錄> <較舊 companyfacts 目錄> \
                          --stooq <stooq 目錄> --splitonly <只分割還原股價目錄>

原始檔很大（69 家約 270MB），不進版控；產出的 data/quarters.csv、data/prices_monthly.csv 才進。
原始檔來源與取得方式見 data/SOURCES.md。
"""
import argparse
import os

import pandas as pd

from pef.data import load_universe

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", required=True, nargs="+", help="companyfacts 目錄，較新的快照放前面")
    ap.add_argument("--stooq", required=True)
    ap.add_argument("--splitonly", default=None, help="只做分割還原的日股價目錄（<TICKER>.csv）")
    ap.add_argument("--universe", default="universe.csv", help="data/ 底下的名單檔")
    ap.add_argument("--tag", default="", help="輸出檔名後綴，例 _ext → quarters_ext.csv")
    a = ap.parse_args()
    uni = pd.read_csv(os.path.join(DATA, a.universe), keep_default_na=False)
    q, p, log = load_universe(a.facts, a.stooq, a.splitonly, uni)
    cols = ["ticker", "period_end", "filed", "avail", "rev", "gp", "oi", "ni", "sh", "split_fac", "sh_now", "dps", "dps_now",
            "inv", "equity", "cash", "debt"]
    q[cols].to_csv(os.path.join(DATA, f"quarters{a.tag}.csv"), index=False, float_format="%.6g")
    p.to_csv(os.path.join(DATA, f"prices_monthly{a.tag}.csv"), index=False, float_format="%.6g")
    log.to_csv(os.path.join(DATA, f"build_log{a.tag}.csv"), index=False)
    pd.set_option("display.width", 200)
    print(log.to_string())
    print(f"\nquarters: {len(q)} 列；prices: {len(p)} 列")


if __name__ == "__main__":
    main()
