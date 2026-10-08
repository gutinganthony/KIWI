#!/usr/bin/env python3
"""把驗證延伸到「至今」：12 個月（起點 2024-10～2025-09、目標日到 2026-09）與 6 個月（起點 2025-04～2025-09）（README §16）。

    python3 lab_orbit_recent.py --lg <loosygoosie data/companies> --yahoo-cache <快取目錄>

S&P 500 歷史面板（SEC 第一次申報值、Stooq 股價）只到 2025-09，答案最晚 2025-09。這裡改用：
  股價：Yahoo 月底收盤（分割調整後；pef/yahoo.py），起點和目標日用同一個來源，報酬口徑一致；
  EPS：loosygoosie 最近 12 季（重述後的最後申報值；可用日＝季末 +45 天、年報 +75 天），最近四季淨利 ÷ 分割調整後的稀釋股數。
起點的線索、市場預期（代理）、β 用 lab_orbit.py 的走動式結果（results/orbit_predictions.csv.gz、orbit_beta.csv），
同一個起點年用同一組 β（2024 年的起點用 2024 年 1 月版，2025 年的起點用 2025 年 1 月版）。
限制：EPS 是重述後的版本（略偏樂觀）；只能評「只需 a 時點 EPS」的寫法（b 時點的 EPS 還沒揭曉）。
輸出：results/orbit_recent.txt、orbit_recent_scores.csv、orbit_recent_rows.csv.gz（逐筆，給 lab_orbit_index.py 依指數分組）
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import yahoo                                    # noqa: E402
from pef.now import lg_quarters                          # noqa: E402

RES = os.path.join(HERE, "results")
GNAME = {"cyclical": "半導體／設備／記憶體", "growth": "軟體／網路", "tech_other": "其他科技", "other": "非科技"}
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def ttm_eps(q, when):
    """when 那天已公布的最近四季：淨利合計 ÷ 最新一季的稀釋股數（分割調整後）。四季要連續。"""
    k = q[q["avail"] <= when].tail(4)
    if len(k) < 4 or k["ni"].isna().any() or not (k["sh"].iloc[-1] > 0):
        return np.nan
    if (k["period_end"].diff().dt.days.iloc[1:] > 120).any():
        return np.nan
    return float(k["ni"].sum() / k["sh"].iloc[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lg", required=True)
    ap.add_argument("--yahoo-cache", required=True)
    a = ap.parse_args()
    u = pd.read_csv(os.path.join(HERE, "data", "universe_sp500.csv"), keep_default_na=False)
    o = pd.read_csv(os.path.join(RES, "orbit_predictions.csv.gz"), parse_dates=["month"])
    beta = pd.read_csv(os.path.join(RES, "orbit_beta.csv"))
    win = {12: ("2024-10-01", "2025-09-01"), 6: ("2025-04-01", "2025-09-01")}
    o = o[(o["month"] >= "2024-10-01") & (o["month"] <= "2025-09-01")]
    rows = []
    for t, g in o.groupby("ticker"):
        cik = u.loc[u["ticker"] == t, "cik"]
        if cik.empty:
            continue
        path = os.path.join(a.lg, f"{int(cik.iloc[0])}.json")
        y = yahoo.chart(t, "5y", "1mo", cache_dir=a.yahoo_cache, max_age_h=24 * 30)
        if not os.path.exists(path) or y is None:
            continue
        q, _ = lg_quarters(path, t)
        if q is None:
            continue
        px = y["close"]
        for r in g.itertuples():
            m0 = r.month + pd.offsets.MonthEnd(0)
            if m0 not in px.index:
                continue
            e0 = ttm_eps(q, m0)
            for h, (lo, hi) in win.items():
                m1 = m0 + pd.offsets.MonthEnd(h)
                if not (pd.Timestamp(lo) <= r.month <= pd.Timestamp(hi)) or m1 not in px.index:
                    continue
                rows.append(dict(ticker=t, grp=r.grp, month=r.month, h=h, p0=px[m0], p1=px[m1], eps0=e0, eps1=ttm_eps(q, m1),
                                 orbit_lr=r.orbit_lr, e_exp=getattr(r, f"e{h}"), year=r.month.year))
    x = pd.DataFrame(rows)
    x = x[(x["eps0"] > 0) & (x["eps1"] > 0)].copy()
    x["lr"] = np.log(x["p1"] / x["p0"])
    x["y"] = x["lr"] - x["orbit_lr"] * x["h"] / 12
    x["g"] = np.log(x["eps1"] / x["eps0"]).clip(-2, 2)
    x["s"] = (x["g"] - x["e_exp"]).clip(-2, 2)
    bt = beta.set_index(["h", "年", "方法", "組別"])
    def b(h, Y, meth, gn, i):
        try:
            return float(bt.loc[(h, Y, meth, gn), f"b{i}"])
        except KeyError:
            return np.nan
    gname = x["grp"].map(GNAME)
    x["adj_raw"] = [b(h, Y, "原始成長a", gn, 0) for h, Y, gn in zip(x["h"], x["year"], gname)] * x["g"]
    x["adj_es"] = ([b(h, Y, "預期＋修正a", gn, 0) for h, Y, gn in zip(x["h"], x["year"], gname)] * x["e_exp"]
                   + [b(h, Y, "預期＋修正a", gn, 1) for h, Y, gn in zip(x["h"], x["year"], gname)] * x["s"])
    x["e_unch"] = x["g"] - x["lr"]
    x["e_orbit"] = -x["y"]
    x["e_raw"] = x["adj_raw"] - x["y"]
    x["e_es"] = x["adj_es"] - x["y"]
    say(f"延伸樣本：{x['ticker'].nunique()} 家；12 個月 {int((x['h'] == 12).sum()):,} 個公司月（起點 2024-10～2025-09，目標日到 2026-09）、"
        f"6 個月 {int((x['h'] == 6).sum()):,} 個（起點 2025-04～2025-09，目標日到 2026-03）")
    rows = []
    for h in (6, 12):
        xh = x[x["h"] == h]
        for gl, d in [("全部", xh), ("科技", xh[xh["grp"] != "other"])] + [(GNAME[k], xh[xh["grp"] == k]) for k in GNAME]:
            d = d.dropna(subset=["e_raw", "e_es"])
            if len(d) < 30:
                continue
            r = dict(h=h, 組別=gl, n=len(d))
            for m, lab in (("e_unch", "本益比不變"), ("e_orbit", "軌道"), ("e_raw", "軌道＋原始成長a"), ("e_es", "軌道＋預期＋修正a")):
                e = d[m].to_numpy(float)
                r[lab] = float(np.median(np.abs(e)))
            r["軌道_命中20"] = float(np.mean(np.abs(np.exp(d["e_orbit"]) - 1) <= 0.2))
            r["市場偏離軌道中位"] = float(np.median(d["y"]))
            rows.append(r)
    sc = pd.DataFrame(rows)
    say("\n== 中位 |ln 誤差|（越小越好）；「市場偏離軌道中位」＝這段期間股價比軌道多漲（+）或少漲（−）")
    say(sc.round(4).to_string(index=False))
    say("\n== 12 個月，依起點月份（全部）：")
    for mth, d in x[x["h"] == 12].groupby("month"):
        say(f"  {mth:%Y-%m} n={len(d):4d}  軌道 {np.median(np.abs(d['e_orbit'])):.3f}  ＋原始成長 {np.nanmedian(np.abs(d['e_raw'])):.3f}"
            f"  本益比不變 {np.median(np.abs(d['e_unch'])):.3f}  市場偏離軌道 {np.median(d['y']):+.3f}")
    sc.to_csv(os.path.join(RES, "orbit_recent_scores.csv"), index=False, float_format="%.6f")
    x[["ticker", "grp", "month", "h", "p0", "p1", "eps0", "eps1", "orbit_lr", "e_exp", "lr", "y", "g", "s",
       "e_unch", "e_orbit", "e_raw", "e_es"]].to_csv(os.path.join(RES, "orbit_recent_rows.csv.gz"), index=False,
                                                    float_format="%.6g", compression={"method": "gzip", "mtime": 0})
    open(os.path.join(RES, "orbit_recent.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
