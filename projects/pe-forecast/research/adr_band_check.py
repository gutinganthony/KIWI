#!/usr/bin/env python3
"""README §19.4：外國公司 ADR 用 S&P 500 校準的區間，涵蓋率夠不夠？要放寬幾倍？

    python3 research/adr_band_check.py > results/adr_bands.txt      # 另寫 results/band_widen.json 的 "adr"

資料：data/adr_hist.csv.gz（adr_fetch.py：月底股價、每 ADR 美元的最近四季 EPS、股利殖利率）、data/adr_now.csv（類型、今天的波動，
當作歷史波動的近似——ADR 月資料只有約 3 年，算不出起點當時的 36 個月波動）、data/rates_monthly.csv（10 年期）。
評分：起點 2023-10～2025-09，h＝6、12；起點與目標日 EPS 都 > 0、ADR 比率沒變、|ln EPS 成長| < 2；用正式版「原始成長a」的 β 與區間。
「需要的倍數」＝讓 80% 區間涵蓋 80% 要放寬幾倍（不扣大盤＝單一股票使用者實際面對的；扣掉每月共同偏離＝只看個股）。
對照：S&P 500 同一段起點（2023-10～2025-09）用同一個做法的涵蓋率——results/orbit_predictions.csv.gz（走動式，目標日到 2025-09）
不夠的月份用 results/orbit_recent_rows.csv.gz（lab_orbit_recent.py，目標日到 2026-09）補；波動用 orbit_predictions 的 vol36（當時的值）。
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model = json.load(open(os.path.join(HERE, "results", "orbit_model.json")))
h_ = pd.read_csv(os.path.join(HERE, "data", "adr_hist.csv.gz"), parse_dates=["month_end"])
now = pd.read_csv(os.path.join(HERE, "data", "adr_now.csv"))
ok = set(now.loc[now["conv_ok"].astype(bool), "ticker"])
vol = now.set_index("ticker")["vol36"]
rt = pd.read_csv(os.path.join(HERE, "data", "rates_monthly.csv"), parse_dates=["month_end"]).set_index("month_end")["DGS10"] / 100
h_ = h_[h_["ticker"].isin(ok)].sort_values(["ticker", "month_end"])


def need(u, q):
    lo, hi = 0.5, 3.0
    for _ in range(40):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if ((u >= q[0] * m) & (u <= q[3] * m)).mean() < 0.8 else (lo, m)
    return hi


print(__doc__.strip().splitlines()[0])
w = {}
for h in (6, 12):
    hm = model["h"][str(h)]
    beta = {g: v[0] for g, v in hm["beta"]["原始成長a"].items()}
    band = hm["bands"]["原始成長a"]
    nx = h_.groupby("ticker").shift(-h)
    d = h_.assign(p1=nx["px"], e1=nx["eps_usd"], r1=nx["ratio"], m1=nx["month_end"])
    d = d[(d["month_end"] >= "2023-10-01") & (d["month_end"] <= "2025-09-30") & (d["m1"] - d["month_end"]).dt.days.between(h * 30 - 10, h * 30 + 10)]
    d = d[(d["eps_usd"] > 0) & (d["e1"] > 0) & (d["ratio"] == d["r1"]) & d["p1"].notna()]
    g = np.log(d["e1"] / d["eps_usd"])
    d = d[g.abs() < 2]
    g = g[d.index]
    orbit_lr = (d["month_end"].map(rt).ffill() + model["erp"] - d["dy"].fillna(0)) * h / 12
    dev = np.log(d["p1"] / d["px"]) - orbit_lr
    pred = d["grp"].map(beta) * g
    v = d["ticker"].map(vol).fillna(band["vol_median"])
    sc = np.clip(v, *model["vol_clip"]) ** model["alpha"]
    u = ((dev - pred) / sc).to_numpy()
    uc = u - pd.Series(u, index=d.index).groupby(d["month_end"]).transform("median").to_numpy()
    q = band["q"]
    cov = ((u >= q[0]) & (u <= q[3])).mean()
    covc = ((uc >= q[0]) & (uc <= q[3])).mean()
    print(f"\n{h} 個月：{len(d):,} 列、{d['ticker'].nunique()} 家；中位 |誤差| 模型 {np.median(np.abs(dev - pred)):.3f}；偏離軌道中位 {np.median(dev):+.3f}")
    print(f"  80% 區間涵蓋：{cov:.1%}（扣掉每月共同偏離後 {covc:.1%}）；需要的倍數：不扣 {need(u, q):.2f}、扣掉後 {need(uc, q):.2f}")
    w[str(h)] = round(max(1.0, need(u, q)), 3)
    # S&P 500 同期對照
    pr = pd.read_csv(os.path.join(HERE, "results", "orbit_predictions.csv.gz"), parse_dates=["month"],
                     usecols=["ticker", "month", "vol36", f"y{h}", f"p{h}_原始成長a"])
    a1 = pr[(pr["month"] >= "2023-10-01") & (pr["month"] <= "2025-09-30") & pr[f"y{h}"].notna() & pr[f"p{h}_原始成長a"].notna()]
    a1 = a1.assign(res=a1[f"y{h}"] - a1[f"p{h}_原始成長a"])
    rr = pd.read_csv(os.path.join(HERE, "results", "orbit_recent_rows.csv.gz"), parse_dates=["month"])
    rr = rr[(rr["h"] == h) & ~rr["month"].isin(a1["month"].unique()) & rr["e_raw"].notna()]
    rr = rr.merge(pr[["ticker", "month", "vol36"]], on=["ticker", "month"], how="left").assign(res=lambda v: -v["e_raw"])
    sp = pd.concat([a1[["month", "vol36", "res"]], rr[["month", "vol36", "res"]]])
    us = (sp["res"] / np.clip(sp["vol36"].fillna(band["vol_median"]), *model["vol_clip"]) ** model["alpha"]).to_numpy()
    print(f"  對照 S&P 500 同一段起點（{sp['month'].min():%Y-%m}～{sp['month'].max():%Y-%m}，{len(sp):,} 列）：80% 區間涵蓋 "
          f"{((us >= q[0]) & (us <= q[3])).mean():.1%}；需要的倍數 {need(us, q):.2f}")
w["24"] = w["12"]                                                           # 24 個月沒有測，沿用 12 個月
p = os.path.join(HERE, "results", "band_widen.json")
bw = json.load(open(p)) if os.path.exists(p) else {}
bw["adr"] = dict(h=w, note="外國公司 ADR：80% 區間放寬倍數（research/adr_band_check.py，起點 2023-10～2025-09，不扣大盤；只有約 2 年資料）")
json.dump(bw, open(p, "w"), ensure_ascii=False, indent=1)
