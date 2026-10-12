#!/usr/bin/env python3
"""共識校正模型的正式版（README §19.1）：用全部已揭曉的資料訓練「今天拿得到的線索」版樹模型，存成 results/eps_correction_model.pkl。

    python3 eps_correction_fit.py --cache <lab_orbit.py 的暫存目錄>      # 會訓練樹模型（約 30 秒）

另外存每家公司今天用得到的歷史線索（results/eps_correction_firm.csv）：過去偏差（lead≈11 個月時 ln(實際 GAAP ÷ 共識) 的中位數與筆數）、
最新的長期成長預估 LTG（OSAP fgr5yrLag）、年報通常在會計年度結束後幾天公布（算「距離年報幾個月」用）、
同時點護欄（README §20.2）：距離年報 0.5–3／3–6／6–9／9–12 個月各自的過去偏差 pbK、過去 |偏差| paK、年度數 pnK（K＝0～3）。
中小型股（README §20.3，有 data/osap/feps_small.csv.gz 與 <cache>/small_cond.pkl 時）：同樣的欄位，scope＝small（模型不重訓，只補公司表）。
使用：pef/eps_correct.py（orbit_price.py --cons auto、make_orbit_page.py）。
"""
import argparse
import json
import os
import pickle
import sys

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab_eps_correction as L                           # noqa: E402

RES = os.path.join(HERE, "results")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    d = L.build(a.cache)
    tr = d[d["tgt"].notna() & ~d["near_split"]]
    X = tr[L.FEATS_NOW].to_numpy(float)
    X[~np.isfinite(X)] = np.nan
    mdl = HistGradientBoostingRegressor(**L.GBM).fit(X, tr["tgt"].to_numpy(float))
    pickle.dump(mdl, open(os.path.join(RES, "eps_correction_model.pkl"), "wb"))
    pred = mdl.predict(X)
    meta = dict(features=L.FEATS_NOW, grp_id=L.GRP_ID, n_train=int(len(tr)), firms=int(tr["ticker"].nunique()),
                months=[str(tr["month"].min().date()), str(tr["month"].max().date())], last_report=str(tr["report"].max().date()),
                sklearn=sklearn.__version__, target="ln(實際 GAAP 本財年 EPS ÷ FY1 共識)",
                in_sample_mae_raw=float(np.median(np.abs(tr["tgt"]))), in_sample_mae_corrected=float(np.median(np.abs(tr["tgt"] - pred))),
                walk_forward_note="樣本外成績見 results/eps_correction.txt（樹（今天的線索））",
                medians={c: float(np.nanmedian(X[:, i])) for i, c in enumerate(L.FEATS_NOW)})   # 解釋用：把一條線索換成中位數，預測變多少
    json.dump(meta, open(os.path.join(RES, "eps_correction_model.json"), "w"), ensure_ascii=False, indent=1)

    # 每家公司的歷史線索
    base = d[(d["lead"] > 10.5) & (d["lead"] <= 12.0) & d["tgt"].notna() & ~d["near_split"]]
    pb = base.groupby("ticker")["tgt"].agg(past_bias="median", n_past="size")
    ltg = d.sort_values("month").groupby("ticker")["ltg"].last().rename("ltg")
    lag = d.drop_duplicates(["ticker", "fy1"]).assign(lag=lambda v: (v["report"] - v["fy1"]).dt.days).groupby("ticker")["lag"].median()
    # 同時點護欄：每個年度取該距離區間的中位數，再取各年度的中位數（lab_eps_correction2.py 的 add_lead_bias，用全部已公布的年度）
    ok = d[d["tgt"].notna() & ~d["near_split"]].assign(lb=lambda v: pd.cut(v["lead"], [0.5, 3, 6, 9, 12], labels=False))
    pf = ok.groupby(["ticker", "lb", "fy1"]).agg(tg=("tgt", "median"), ab=("tgt", lambda v: np.median(np.abs(v)))).reset_index()
    gb = pf.groupby(["ticker", "lb"]).agg(pb=("tg", "median"), pa=("ab", "median"), pn=("tg", "size")).reset_index()
    wide = gb.pivot(index="ticker", columns="lb")
    wide.columns = [f"{a}{int(b)}" for a, b in wide.columns]
    firm = pd.concat([pb, ltg, lag.rename("report_lag_days"), wide], axis=1)
    firm.index.name = "ticker"
    firm["scope"] = "sp500"
    if os.path.exists(os.path.join(HERE, "data", "osap", "feps_small.csv.gz")) and os.path.exists(os.path.join(a.cache, "small_cond.pkl")):
        import lab_eps_correction_small as LS
        s = LS.build_small(a.cache)
        s = s[~s["ticker"].isin(firm.index)]
        sb = s[(s["lead"] > 9) & s["tgt"].notna()].groupby("ticker")["tgt"].agg(past_bias="median", n_past="size")
        sl = s.sort_values("month").groupby("ticker")["ltg"].last().rename("ltg")
        slag = s.drop_duplicates(["ticker", "fy1"]).assign(lag=lambda v: (v["report"] - v["fy1"]).dt.days).groupby("ticker")["lag"].median()
        sk = s[s["tgt"].notna()]
        spf = sk.groupby(["ticker", "lead_b", "fy1"]).agg(tg=("tgt", "median"), ab=("tgt", lambda v: np.median(np.abs(v)))).reset_index()
        sgb = spf.groupby(["ticker", "lead_b"]).agg(pb=("tg", "median"), pa=("ab", "median"), pn=("tg", "size")).reset_index()
        sw = sgb.pivot(index="ticker", columns="lead_b")
        sw.columns = [f"{x}{int(y)}" for x, y in sw.columns]
        small = pd.concat([sb, sl, slag.rename("report_lag_days"), sw], axis=1)
        small["scope"] = "small"
        small.index.name = "ticker"
        firm = pd.concat([firm, small])
        print(f"中小型股公司表 {len(small)} 家")
    firm.round(5).to_csv(os.path.join(RES, "eps_correction_firm.csv"))
    print(f"訓練 {len(tr):,} 列、{tr['ticker'].nunique()} 家（{meta['months'][0]}～{meta['months'][1]}）；樣本內 |誤差| 中位 "
          f"{meta['in_sample_mae_raw']:.3f} → {meta['in_sample_mae_corrected']:.3f}；公司表 {len(firm)} 家")


if __name__ == "__main__":
    main()
