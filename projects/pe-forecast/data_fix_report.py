#!/usr/bin/env python3
"""股數單位修正（README §14.1）的影響，與現在預測的指數分組家數（§14.6）。

    python3 data_fix_report.py [--old-rev <修正前的 git 版本，預設 dd9ad414^>]

修正前的 S&P 500 資料與回測預測從 git 歷史讀（data/quarters_sp500.csv、prices_monthly_sp500.csv、results/broad_predictions.csv.gz）；
中小型股修正前的資料沒有進版控，只報修正的家數與季數（data/build_log_small.csv）。輸出：results/data_fix.txt
"""
import argparse
import gzip
import io
import os
import subprocess

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REL = "projects/pe-forecast"


def old_file(rev, path):
    raw = subprocess.run(["git", "-C", HERE, "show", f"{rev}:{REL}/{path}"], capture_output=True, check=True).stdout
    return gzip.decompress(raw) if path.endswith(".gz") else raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-rev", default="dd9ad414^")
    a = ap.parse_args()
    out = []
    say = out.append
    for name in ("sp500", "small"):
        lg = pd.read_csv(os.path.join(HERE, "data", f"build_log_{name}.csv"))
        ok = lg[lg["status"] == "ok"]
        say(f"{name}：修正 {int((ok['share_scale_fixed'] > 0).sum())} 家、{int(ok['share_scale_fixed'].sum())} 季（建檔 {len(ok)} 家）")
    po = pd.read_csv(io.BytesIO(old_file(a.old_rev, "data/prices_monthly_sp500.csv")))
    pn = pd.read_csv(os.path.join(HERE, "data", "prices_monthly_sp500.csv"))
    m = po.merge(pn, on=["ticker", "month"], how="outer", suffixes=("_o", "_n"), indicator=True)
    both = m[m["_merge"] == "both"]
    big = np.log10(both["mc_n"] / both["mc_o"]).abs() > 1
    say(f"S&P 500 月市值改變超過 10 倍：{int(big.sum())} 個公司月、{both[big]['ticker'].nunique()} 家；"
        f"市銷率不合理而剔除：{int((m['_merge'] == 'left_only').sum())} 個公司月；新增：{int((m['_merge'] == 'right_only').sum())}")
    qo = pd.read_csv(io.BytesIO(old_file(a.old_rev, "data/quarters_sp500.csv")))
    qn = pd.read_csv(os.path.join(HERE, "data", "quarters_sp500.csv"))
    g = qo[(qo["ticker"] == "GRMN") & (qo["period_end"] == "2014-03-29")].iloc[0]
    h = qn[(qn["ticker"] == "GRMN") & (qn["period_end"] == "2014-03-29")].iloc[0]
    say(f"GRMN 2014-03-29 稀釋股數：修正前 {g['sh_now']:,.0f} → 修正後 {h['sh_now']:,.0f}")
    bo = pd.read_csv(io.BytesIO(old_file(a.old_rev, "results/broad_predictions.csv.gz")))
    x = bo[(bo["ticker"] == "GRMN") & (bo["h"] == 12)].dropna(subset=["E_all", "actual"])
    e = (x["E_all"] - x["actual"]).abs().median()
    say(f"GRMN 修正前 12 個月預測的中位 |ln 誤差|：{e:.2f}（本益比差 {np.exp(e):,.0f} 倍）")
    d = pd.read_csv(os.path.join(HERE, "results", "now_all.csv"))
    tiers = d["tier"].fillna("不在主要指數").replace("", "不在主要指數").value_counts()
    say("現在預測的所屬指數（results/now_all.csv）：" + "、".join(f"{k} {v:,}" for k, v in tiers.items())
        + f"；Nasdaq-100 {int(d['in_ndx'].fillna(False).astype(bool).sum())}")
    txt = "\n".join(out) + "\n"
    print(txt, end="")
    open(os.path.join(HERE, "results", "data_fix.txt"), "w").write(txt)


if __name__ == "__main__":
    main()
