#!/usr/bin/env python3
"""README §22.2：§22.1 的個案實驗放大到整個 S&P 500——同樣兩個起點，這 5 檔是不是特例？

    python3 research/case_broad.py --cache <lab_orbit.py 的暫存目錄> --raw <Yahoo 原始 JSON 資料夾>   # 第一次約 10 分鐘（4 條連線抓約 1,000 個檔）

起點＝Yahoo 有歷史 forward 本益比的那兩天：2024-09-19（到 2026-10-12 約 24.8 個月）、2025-10-02（約 12.3 個月）。
起點輸入：當天收盤（Yahoo）、當時已公布的最近四季 EPS 與股利殖利率、波動（lab_orbit.py 的面板：起點前一個月底的列——2024-08、2025-09，
當時的 S&P 500 成分股）、前一個月底的 10 年期；β＝起點那年的走動式 β（h＝24／12），軌道按實際月數。
EPS：1 當時分析師（forward EPS ＝ 收盤 ÷ forward 本益比；24 個月再乘一次隱含年成長，上限 +50%、下限 −30%）；
     1b 再乘正式版的共識係數（forward EPS 當本財年共識、距離年報 12 個月；30／90 天前的共識沒有歷史留空；
        校正模型的訓練資料到 2024-11：對 2025 起點是樣本外，對 2024 起點只有過去偏差等公司表欄位用到 2024 年以後的年報）；
     1c 改善版：1b ＋ 24 個月不再用隱含成長外推（EPS_a＝EPS_b＝forward × 係數；§22.5 用 2012–2017 的 I/B/E/S 選的規則）；
     2 完全猜對；3 本益比不變。
實際：2026-10-12 的股價與最近四季 GAAP EPS（make_orbit_page.py 同一份資料）。只評兩端 EPS 都 > 0、而且今天還有資料的公司（有倖存者偏差：期間內被併購或下市的不在裡面）。
"""
import argparse
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import make_orbit_page as MP                             # noqa: E402
from pef import consensus, eps_correct, orbit            # noqa: E402

RES = os.path.join(HERE, "results")
NOW = pd.Timestamp("2026-10-12")
# 面板的列是「那個月底」的資料（EPS＝月底前已公布的）：起點 2024-09-19 要用 2024-08 那一列（8/31），才不會用到 9/20–9/30 才公布的財報
SCEN = [("A：2024-09-19 起點", pd.Timestamp("2024-09-19"), "2024-08-01", 24), ("B：2025-10-02 起點", pd.Timestamp("2025-10-02"), "2025-09-01", 12)]
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url, path):
    if os.path.exists(path):
        return True
    try:
        open(path, "wb").write(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        return True
    except Exception:                                    # noqa: BLE001
        return False


def get(t, raw):
    s = consensus.yahoo_symbol(t)
    ok1 = fetch(f"https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{s}"
                "?type=trailingForwardPeRatio&period1=1640995200&period2=1800000000", os.path.join(raw, f"fpe_{s}.json"))
    ok2 = fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=3y&interval=1d", os.path.join(raw, f"px3_{s}.json"))
    return t, ok1 and ok2


def load(t, raw):
    s = consensus.yahoo_symbol(t)
    try:
        f = json.load(open(os.path.join(raw, f"fpe_{s}.json")))
        fpe = {pd.Timestamp(x["asOfDate"]): x["reportedValue"]["raw"] for r in f["timeseries"]["result"]
               for x in r.get("trailingForwardPeRatio", []) if x}
        c = json.load(open(os.path.join(raw, f"px3_{s}.json")))["chart"]["result"][0]
        close = pd.Series(c["indicators"]["quote"][0]["close"], index=pd.to_datetime(c["timestamp"], unit="s").normalize()).dropna()
        return fpe, close
    except Exception:                                    # noqa: BLE001
        return {}, pd.Series(dtype=float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--raw", required=True)
    a = ap.parse_args()
    os.makedirs(a.raw, exist_ok=True)
    x = pd.read_pickle(os.path.join(a.cache, "orbit_x2.pkl"))
    tk, _ = MP.tickers()
    now = {d["t"]: d for d in tk}
    model = orbit.load_model()
    wb = pd.read_csv(os.path.join(RES, "orbit_beta.csv")).set_index(["h", "年", "方法", "組別"])
    rates = pd.read_csv(os.path.join(HERE, "data", "rates_monthly.csv"), parse_dates=["month_end"]).set_index("month_end")["DGS10"] / 100
    names = sorted(set(x.loc[x["month"].isin(pd.to_datetime([m for _, _, m, _ in SCEN])), "ticker"]) & set(now))
    with ThreadPoolExecutor(4) as ex:
        okn = sum(ok for _, ok in ex.map(lambda t: get(t, a.raw), names))
    print(f"S&P 500 面板裡、今天也有資料的 {len(names)} 家；Yahoo 抓到 {okn} 家")
    rows = []
    for t in names:
        fpe, close = load(t, a.raw)
        n = now[t]
        p1, e1 = float(n["px"]), float(n["e"])
        for nm, t0, mon, h in SCEN:
            r = x[(x["ticker"] == t) & (x["month"] == mon)]
            if r.empty or t0 not in fpe or close[:t0].empty:
                continue
            r = r.iloc[0]
            p0, e0 = float(close[:t0].iloc[-1]), float(r["eps0"])
            if not (e0 > 0 and e1 > 0 and fpe[t0] > 0):
                continue
            months = (NOW - t0).days / 30.4375
            r10 = float(rates[rates.index < t0].iloc[-1])
            orb = (r10 + model["erp"] - (r["dy"] if np.isfinite(r["dy"]) else 0)) * months / 12
            F = p0 / fpe[t0]
            g = float(np.clip(F / e0, 0.7, 1.5))
            ea = F if h == 12 else F * g
            gn = orbit.GNAME[r["grp"]]
            b_exp = float(wb.loc[(h, t0.year, "預期b＋修正ab", gn), "b0"])
            b_raw = float(wb.loc[(h, t0.year, "原始成長a", gn), "b0"])
            pe1 = p1 / e1
            row = dict(px=p0, eps0=e0, g_rev=r["g_rev"], ret12=r["ret12"], vol36=r["vol36"], mc=p0 * r["mc"] / r["px"], grp=r["grp"])
            k, _ = eps_correct.correction(eps_correct.features(t, row, F, t0 + pd.DateOffset(months=12), today=t0), ticker=t)
            k = k if k is not None else 1.0
            p_k = p0 * np.exp(orb + b_exp * np.log(ea * k * g / e0))
            p_n = p0 * np.exp(orb + b_exp * np.log(F * k / e0))           # 24 個月不外推（§22.5）：EPS_a＝EPS_b＝forward × 係數
            p_c = p0 * np.exp(orb + b_exp * np.log(ea * g / e0))
            p_p = p0 * np.exp(orb + b_raw * float(np.clip(np.log(e1 / e0), -2, 2)))
            rows.append(dict(股票=t, 情境=nm, 組別=gn, 起點本益比=p0 / e0, 實際本益比=pe1,
                             誤差_分析師=np.log(p_c / ea / pe1), 誤差_股價=np.log(p_c / p1), 誤差_EPS=np.log(ea / e1),
                             共識係數=k, 誤差_分析師校正=np.log(p_k / (ea * k) / pe1), 誤差_EPS校正=np.log(ea * k / e1),
                             誤差_改善版=np.log(p_n / (F * k) / pe1) if h == 24 else np.log(p_k / (ea * k) / pe1),
                             誤差_EPS猜對=np.log(p_p / e1 / pe1), 誤差_本益比不變=np.log(p0 / e0 / pe1), EPS變化=np.log(e1 / e0)))
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(RES, "case_broad.csv"), index=False, float_format="%.6g")
    out = []
    for nm, g in d.groupby("情境", sort=False):
        for lab, gg in [("全部", g), ("科技", g[g["組別"] != "非科技"]), ("半導體／設備／記憶體", g[g["組別"] == "半導體／設備／記憶體"]),
                        ("EPS 變化 > ±50%", g[g["EPS變化"].abs() > np.log(1.5)])]:
            m = lambda c: float(np.median(np.abs(gg[c])))                   # noqa: E731
            w20 = lambda c: float(np.mean(np.abs(np.exp(gg[c]) - 1) <= 0.2))  # noqa: E731
            out.append(dict(情境=nm, 樣本=lab, n=len(gg), 分析師預估=m("誤差_分析師"), 分析師乘共識係數=m("誤差_分析師校正"),
                            改善版=m("誤差_改善版"), EPS完全猜對=m("誤差_EPS猜對"), 本益比不變=m("誤差_本益比不變"),
                            分析師_股價部分=m("誤差_股價"), 分析師_EPS部分=m("誤差_EPS"),
                            EPS偏差中位_原樣=float(np.median(gg["誤差_EPS"])), EPS偏差中位_校正=float(np.median(gg["誤差_EPS校正"])),
                            分析師_20內=w20("誤差_分析師"), 校正_20內=w20("誤差_分析師校正"), 改善_20內=w20("誤差_改善版"), 猜對_20內=w20("誤差_EPS猜對"), 不變_20內=w20("誤差_本益比不變")))
    t = pd.DataFrame(out)
    pd.set_option("display.width", 250)
    print("\n== 中位 |ln 本益比誤差|（0.20 ≈ 差 20%）與誤差在 ±20% 內的比例")
    print(t.round(3).to_string(index=False))
    t.to_csv(os.path.join(RES, "case_broad_scores.csv"), index=False, float_format="%.6f")
    five = d[d["股票"].isin(["GOOGL", "NVDA", "MU", "META"])]
    print("\n== 對照：個案的 4 檔在這個表裡（TSM 不是 S&P 500）")
    print(five[["股票", "情境", "起點本益比", "實際本益比", "誤差_分析師", "誤差_EPS猜對", "誤差_本益比不變"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
