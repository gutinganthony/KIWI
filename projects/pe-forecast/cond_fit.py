#!/usr/bin/env python3
"""給定 EPS 的本益比模型：正式版係數與區間表（README §15）。

    python3 cond_fit.py          # 要先跑 lab_cond.py（區間用它的樣本外誤差）

輸出 results/cond_model.json：
  xs[h]、xs2[12]：線性係數（第一個是常數）、每個特徵的截斷上下限、訓練筆數、最晚的答案月份
  bands[h]、bands2[12]：區間表——ln(實際 ÷ 預測) 除以 波動^alpha、置中之後的 10／25／75／90% 分位數 q
                        （只用 cutoff 以前已揭曉的樣本外誤差；沒有波動資料時用 vol_median）
  backtest：網頁要顯示的回測摘要（results/cond_scores.csv、cond_bands.csv、cond_noise.csv）
預測：ln 本益比(t+h) ＝ ln[今天股價 ÷ 你的 EPS] ＋ 資金成本 × h/12 ＋ 相對大盤的部分（線性）
     股價 ＝ 本益比 × 你的 EPS；區間 ＝ 點預測 × exp(波動^alpha × q)
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import cond, lab                                # noqa: E402
from pef.load import panel_sp500                         # noqa: E402

RES = os.path.join(HERE, "results")


def r(x, k=4):
    return None if x is None or not np.isfinite(x) else round(float(x), k)


def main():
    df, qf = panel_sp500()
    d = lab.build(df, qf)
    c = cond.build(d, df)
    cutoff = (df["month"].max() + pd.offsets.MonthEnd(0)).normalize()
    model = cond.fit_production(c, cutoff)
    p = pd.read_csv(os.path.join(RES, "cond_predictions.csv.gz"),
                    parse_dates=["origin", "target_available_at", "training_cutoff"])
    bands, bands2 = {}, {}
    rnd = lambda b: dict(b, vol_median=r(b["vol_median"]), q=[r(x) for x in b["q"]])
    for h in cond.HORIZONS:
        bands[h] = rnd(cond.calib_table(p, "xs", cutoff, h))
    bands2[12] = rnd(cond.calib_table(p, "xs2", cutoff, 12))
    sc = pd.read_csv(os.path.join(RES, "cond_scores.csv"))
    bd = pd.read_csv(os.path.join(RES, "cond_bands.csv"))
    nz = pd.read_csv(os.path.join(RES, "cond_noise.csv"))
    main_s = sc[sc["樣本"] == "今天有盈餘"]
    bt = {}
    for per in ("選模期", "保留期", "全期"):
        x = main_s[main_s["期間"] == per]
        bt[per] = {m: {int(h): dict(err=r(g["中位絕對誤差"].iloc[0]), hit20=r(g["命中20"].iloc[0]), n=int(g["n"].iloc[0]))
                       for h, g in x[x["方法"] == m].groupby("h")} for m in ("unch", "coe", "xs", "gbm_abs", "gbm_xs")}
        y2 = sc[(sc["樣本"] == "也知道 24 個月後 EPS") & (sc["期間"] == per)]
        bt[per]["f2"] = {m: dict(err=r(g["中位絕對誤差"].iloc[0]), n=int(g["n"].iloc[0])) for m, g in y2.groupby("方法")}
    cov = {per: {int(h): dict(cover80=r(g["涵蓋80"].iloc[0]), cover50=r(g["涵蓋50"].iloc[0]),
                              low=r(g["涵蓋80_低波動"].iloc[0]), mid=r(g["涵蓋80_中波動"].iloc[0]), high=r(g["涵蓋80_高波動"].iloc[0]),
                              vol45=r(g["涵蓋80_波動45以上"].iloc[0]), width80=r(g["寬度80_ln"].iloc[0]))
                 for h, g in bd[(bd["期間"] == per) & (bd["區間"] == "依波動^α縮放＋置中")].groupby("h")} for per in ("選模期", "保留期")}
    noise = {int(h): {str(s): dict(px=r(g["股價中位絕對誤差"].iloc[0]), pe=r(g["本益比中位絕對誤差"].iloc[0]))
                      for s, g in x.groupby("EPS誤差")} for h, x in nz.groupby("h")}
    out = dict(version=cond.VERSION, cutoff=str(cutoff.date()), erp=cond.ERP, horizons=list(cond.HORIZONS),
               xs={str(h): v for h, v in model["xs"].items()}, xs2={str(h): v for h, v in model["xs2"].items()},
               bands={str(h): v for h, v in bands.items()}, bands2={str(h): v for h, v in bands2.items()},
               backtest=bt, coverage=cov, noise=noise)
    path = os.path.join(RES, "cond_model.json")
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"訓練截止 {cutoff.date()}；寫入 {path}")
    for h in cond.HORIZONS:
        m = model["xs"][h]
        print(f"  h={h:2d}：訓練 {m['n_train']:,} 筆（答案最晚 {m['last_target']}）  係數 "
              + "、".join(f"{f} {b:+.3f}" for f, b in zip(["常數"] + m["feats"], m["beta"])))
        b = bands[h]
        s20, s60 = cond.band_scale(0.2, b["alpha"]), cond.band_scale(0.6, b["alpha"])
        print(f"        區間：ln 誤差 ÷ 波動^{b['alpha']} 的分位數 {b['q']}（{b['n']:,} 筆）；80% 區間 ln 寬度：波動 20% → "
              f"{s20 * (b['q'][3] - b['q'][0]):.2f}、60% → {s60 * (b['q'][3] - b['q'][0]):.2f}")
    m = model["xs2"][12]
    print("  xs2（12 個月＋24 個月後 EPS）：" + "、".join(f"{f} {b:+.3f}" for f, b in zip(["常數"] + m["feats"], m["beta"])))


if __name__ == "__main__":
    main()
