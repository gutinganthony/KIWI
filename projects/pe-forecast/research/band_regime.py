#!/usr/bin/env python3
"""README §21.2：價格區間要不要依「市場恐慌程度」放寬或收窄？（VIX、大盤實現波動；走動式樣本外）

    python3 research/band_regime.py > results/band_regime.txt

問題：80% 區間的實際涵蓋率隨時期變（2015–2021 約 70%、2022 以後約 84%）。誤差裡有一大塊是「整個市場一起偏」，
如果起點那個月就看得出市場比較不安（VIX 高、大盤最近波動大），區間應該先放寬。
做法：正式版的區間 ＝ 預測 × exp(波動^0.7 × 分位數)。這裡多乘一個 (訊號 ÷ 校準期訊號中位)^γ：
  訊號＝起點前一個月的 VIX 平均（FRED VIXCLS），或起點前 12 個月 S&P 500 成分股月報酬中位數的年化標準差（大盤實現波動）。
走動式：每一年 Y 只用目標日在 Y 年以前的誤差校準分位數（也在那裡挑 γ），再看 Y 年起點的涵蓋率與區間分數。
資料：results/orbit_predictions.csv.gz（lab_orbit.py 的走動式預測，S&P 500）；誤差＝實際偏離軌道 − 預測的調整（ln）。
評分：80% 涵蓋率（逐年、和 80% 差多少）、區間分數（寬度 ＋ 漏掉時 10 倍的距離，越低越好；Gneiting & Raftery 2007）。
"""
import io
import os
import sys
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from pef import cond                                     # noqa: E402

RES = os.path.join(HERE, "results")
VIX = os.path.join(HERE, "data", "vix_monthly.csv")
CUTOFF = pd.Timestamp("2025-09-30")
ALPHA = cond.BAND_ALPHA
GAMMAS = (0.0, 0.25, 0.5, 0.75, 1.0)
A = 0.2                                                  # 80% 區間


def vix_monthly():
    if not os.path.exists(VIX):
        req = urllib.request.Request("https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS", headers={"User-Agent": "curl/8.5.0"})
        d = pd.read_csv(io.StringIO(urllib.request.urlopen(req, timeout=60).read().decode()), parse_dates=["observation_date"])
        d["VIXCLS"] = pd.to_numeric(d["VIXCLS"], errors="coerce")
        m = d.dropna().groupby(d["observation_date"].dt.to_period("M"))["VIXCLS"].mean()
        pd.DataFrame({"month": m.index.to_timestamp(), "vix": m.round(3).to_numpy()}).to_csv(VIX, index=False)
    v = pd.read_csv(VIX, parse_dates=["month"])
    return v.set_index("month")["vix"]


def tgt_end(month, h):
    return month + pd.DateOffset(months=h)


def iscore(y, lo, hi):
    return (hi - lo) + (2 / A) * np.maximum(lo - y, 0) + (2 / A) * np.maximum(y - hi, 0)


def main():
    p = pd.read_csv(os.path.join(RES, "orbit_predictions.csv.gz"), parse_dates=["month"])
    vix = vix_monthly()
    p["vix"] = (p["month"] - pd.DateOffset(months=1)).map(vix)          # 起點前一個月的 VIX 平均（事前就知道）
    px = p.pivot_table(index="month", columns="ticker", values="px")
    mret = np.log(px / px.shift(1)).median(axis=1)                        # 成分股月報酬中位數
    p["mvol"] = p["month"].map(mret.rolling(12, min_periods=10).std() * np.sqrt(12))
    print(f"資料：{len(p):,} 個公司月（S&P 500，{p['month'].min():%Y-%m}～{p['month'].max():%Y-%m}）；"
          f"VIX 中位 {p['vix'].median():.1f}、大盤實現波動中位 {p['mvol'].median():.3f}")
    out, yearly = [], []
    for h in (6, 12, 24):
        z = p[p[f"y{h}"].notna() & (tgt_end(p["month"], h) <= CUTOFF) & p["vix"].notna() & p["mvol"].notna()].copy()
        a_ = {6: 6, 12: 12, 24: 24}[h]
        specs = {"軌道": z[f"y{h}"].where(z[f"eps_f{a_}"] > 0)}
        for s in ("預期b＋修正ab",):
            if f"p{h}_{s}" in z:
                specs[s] = z[f"y{h}"] - z[f"p{h}_{s}"]
        vmed = float(z["vol36"].median())
        base = np.clip(z["vol36"].fillna(vmed), *cond.VOL_CLIP) ** ALPHA
        for sname, e in specs.items():
            ok = e.notna()
            for sig in ("vix", "mvol"):
                res = {g: [] for g in GAMMAS + ("走動式挑 γ",)}
                picks = []
                years = sorted({m.year for m in z.loc[ok, "month"]})
                for Y in years:
                    cal = ok & (tgt_end(z["month"], h) < pd.Timestamp(f"{Y}-01-01"))
                    tst = ok & (z["month"].dt.year == Y)
                    if cal.sum() < 3000 or tst.sum() < 300:
                        continue
                    smed = float(z.loc[cal, sig].median())
                    best, best_sc = None, None
                    per = {}
                    for g in GAMMAS:
                        sc_cal = base[cal] * (z.loc[cal, sig] / smed) ** g
                        u = e[cal] / sc_cal
                        u = u - u.median()
                        q = np.quantile(u, [A / 2, 1 - A / 2])
                        # 在校準期內挑 γ：同一份校準資料的區間分數（樣本內，但只用過去）
                        isc = float(np.mean(iscore(u.to_numpy(), q[0], q[1]) * sc_cal.to_numpy()))
                        if best_sc is None or isc < best_sc:
                            best, best_sc = g, isc
                        sc_t = base[tst] * (z.loc[tst, sig] / smed) ** g
                        lo, hi = q[0] * sc_t, q[1] * sc_t
                        cov = float(np.mean((e[tst] >= lo) & (e[tst] <= hi)))
                        per[g] = (cov, float(np.mean(iscore(e[tst].to_numpy(), lo.to_numpy(), hi.to_numpy()))), int(tst.sum()))
                        res[g].append(per[g])
                    res["走動式挑 γ"].append(per[best])
                    picks.append(best)
                    yearly.append(dict(h=h, 寫法=sname, 訊號=sig, 年=Y, n=per[0.0][2], 訊號中位=float(z.loc[tst, sig].median()),
                                       涵蓋_固定=per[0.0][0], 涵蓋_γ1=per[1.0][0], 挑到的γ=best, 涵蓋_挑γ=per[best][0]))
                for g, v in res.items():
                    if not v:
                        continue
                    c = np.array([x[0] for x in v])
                    s_ = np.array([x[1] for x in v])
                    n = np.array([x[2] for x in v])
                    out.append(dict(h=h, 寫法=sname, 訊號=sig, γ=g, 年數=len(v), 涵蓋_加權=float(np.average(c, weights=n)),
                                    涵蓋_逐年最低=float(c.min()), 涵蓋_逐年最高=float(c.max()), 和80差_逐年平均=float(np.mean(np.abs(c - 0.8))),
                                    區間分數=float(np.average(s_, weights=n)),
                                    挑到的γ="" if g != "走動式挑 γ" else "、".join(f"{x:g}" for x in picks)))
    t = pd.DataFrame(out)
    print("\n== 走動式樣本外：80% 區間（γ＝0 是正式版；區間分數越低越好；和 80% 差＝逐年 |涵蓋 − 0.8| 的平均）")
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(t.round(4).to_string(index=False))
        y = pd.DataFrame(yearly)
        print("\n== 逐年（12 個月、軌道）：起點那年的訊號中位與涵蓋率")
        print(y[(y["h"] == 12) & (y["寫法"] == "軌道")].round(3).to_string(index=False))
    t.to_csv(os.path.join(RES, "band_regime_scores.csv"), index=False, float_format="%.6f")


if __name__ == "__main__":
    main()
