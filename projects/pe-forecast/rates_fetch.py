#!/usr/bin/env python3
"""美國利率月資料（月底值）→ data/rates_monthly.csv（README §19 利率因子用）。

    python3 rates_fetch.py

來源：FRED 公開 CSV（fredgraph.csv，不用 key；2026-10-11 起這個雲端環境可連）。
  DGS10 10 年期、DGS2 2 年期、DGS3MO 3 個月、FEDFUNDS 聯邦基金有效利率（月平均）、DFII10 10 年期實質（TIPS）、T10YIE 10 年期損益平衡通膨
衍生：exp_cut_2y＝DGS2 − FEDFUNDS（市場預期未來約兩年政策利率的變化：負＝預期降息）、slope＝DGS10 − DGS3MO（期限利差）
"""
import io
import os
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = ["DGS10", "DGS2", "DGS3MO", "FEDFUNDS", "DFII10", "T10YIE"]


def fred(sid):
    req = urllib.request.Request(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",
                                 headers={"User-Agent": "curl/8.5.0"})          # FRED 會擋瀏覽器或自訂的 UA
    raw = urllib.request.urlopen(req, timeout=60).read().decode()
    d = pd.read_csv(io.StringIO(raw))
    d.columns = ["date", sid]
    d["date"] = pd.to_datetime(d["date"])
    d[sid] = pd.to_numeric(d[sid], errors="coerce")
    return d.dropna().set_index("date")[sid]


def main():
    s = {k: fred(k) for k in SERIES}
    m = pd.DataFrame({k: v.resample("ME").last() for k, v in s.items()})
    m = m[m.index >= "1990-01-01"]
    m["exp_cut_2y"] = m["DGS2"] - m["FEDFUNDS"]
    m["slope"] = m["DGS10"] - m["DGS3MO"]
    m.index.name = "month_end"
    out = os.path.join(HERE, "data", "rates_monthly.csv")
    m.round(4).to_csv(out)
    print(f"{len(m)} 個月 {m.index.min():%Y-%m}～{m.index.max():%Y-%m} → {os.path.relpath(out, HERE)}")
    print(m.tail(3).round(2).to_string())


if __name__ == "__main__":
    main()
