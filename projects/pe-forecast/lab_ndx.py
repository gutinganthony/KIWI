#!/usr/bin/env python3
"""Nasdaq-100 的歷史回測：把 S&P 500 回測（lab_broad.py）的預測，只挑「當年是 Nasdaq-100 成分股」的公司重新評分。

    python3 lab_ndx.py --n100 <jmccarrell/n100tickers 的 src/nasdaq_100_ticker_history 目錄>

成分股：每年 1 月 1 日的名單（年中的換股不算）。只有同時在 S&P 500 回測裡的公司有資料
（不在 S&P 500 的外國公司，例如 ASML、PDD、BIDU，沒有）。預測本身完全沒變，只是換一個分組。
輸出：results/ndx_hist.txt、ndx_hist.csv
"""
import argparse
import glob
import io
import os
import sys

import numpy as np
import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import lab                                      # noqa: E402

RES = os.path.join(HERE, "results")
PERIODS = {"選模期": ("2015-01-01", "2021-12-31"), "保留期": ("2022-01-01", "2026-12-31"), "全期": ("2015-01-01", "2026-12-31")}
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n100", required=True)
    a = ap.parse_args()
    mem = []
    for f in sorted(glob.glob(os.path.join(a.n100, "n100-ticker-changes-*.yaml"))):
        y = yaml.load(open(f), Loader=yaml.BaseLoader)       # BaseLoader：代號 ON（安森美）不能被讀成 True
        mem += [(int(y["year"]), t.replace(".", "-")) for t in y["tickers_on_Jan_1"]]
    mem = pd.DataFrame(mem, columns=["year", "ticker"])
    p = pd.read_csv(os.path.join(RES, "broad_predictions.csv.gz"), parse_dates=["month"])
    p["year"] = p["month"].dt.year
    p = p.merge(mem.assign(ndx=True), on=["year", "ticker"], how="left")
    p["ndx"] = p["ndx"].fillna(False).astype(bool)
    cov = pd.DataFrame({"名單": mem[mem["year"].between(2015, 2025)].groupby("year")["ticker"].nunique(),
                        "回測有資料": p[p["ndx"]].groupby("year")["ticker"].nunique()})
    say("Nasdaq-100 每年 1 月的成分股 vs 在 S&P 500 回測裡有資料的家數")
    say(cov.T.to_string())

    rows = []
    for per, rng in PERIODS.items():
        for g, m in [("Nasdaq-100", p["ndx"]), ("S&P 500 其他", ~p["ndx"])]:
            s = lab.score(p[m], ["E_all"], rng)
            rw = s[s["方法"] == "rw"][["h", "中位絕對誤差"]].rename(columns={"中位絕對誤差": "本益比不變"})
            s = s[s["方法"] == "E_all"].rename(columns={"中位絕對誤差": "模型"}).merge(rw, on="h")
            in_per = p[m & (p["month"] >= rng[0]) & (p["month"] <= rng[1])]
            s["公司數"] = in_per.groupby("h")["ticker"].nunique().reindex(s["h"]).to_numpy()
            rows.append(s.assign(期間=per, 群組=g))
    r = pd.concat(rows, ignore_index=True)[["期間", "群組", "h", "公司數", "n", "本益比不變", "模型", "相對隨機漫步", "OOS_R2", "方向命中"]]
    say("\n== S&P 500 回測的預測，依「當年是否 Nasdaq-100 成分股」分組（誤差＝中位 |ln|）")
    say(r.round(3).to_string(index=False))

    x = p[p["ndx"] & (p["h"] == 12) & p["actual"].notna() & p["ln_pe"].notna() & p["E_all"].notna()]
    pc = pd.DataFrame({"ticker": x["ticker"], "m": (x["E_all"] - x["actual"]).abs(), "r": (x["ln_pe"] - x["actual"]).abs()})
    pc = pc.groupby("ticker").agg(n=("m", "size"), m=("m", "median"), r=("r", "median"))
    pc = pc[pc["n"] >= 12]
    say(f"\n逐家（Nasdaq-100、12 個月、至少 12 筆）：{int((pc['m'] < pc['r']).sum())}/{len(pc)} 家模型比本益比不變準")
    worst = (pc["m"] - pc["r"]).sort_values()
    say("模型贏最多：" + "、".join(f"{t} {pc.loc[t, 'r']:.2f}→{pc.loc[t, 'm']:.2f}" for t in worst.index[:5]))
    say("模型輸最多：" + "、".join(f"{t} {pc.loc[t, 'r']:.2f}→{pc.loc[t, 'm']:.2f}" for t in worst.index[::-1][:5]))
    r.to_csv(os.path.join(RES, "ndx_hist.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "ndx_hist.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
