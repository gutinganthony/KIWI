#!/usr/bin/env python3
"""README §22：如果 2024 年、2025 年就用這個模型，能不能算準 2026-10-12 的本益比？（TSM、GOOGL、NVDA、MU、META）

    python3 research/case_2024_2025.py --raw <放 Yahoo 原始 JSON 的資料夾>      # 沒有的檔案會自動下載

兩個情境（只用起點當時拿得到的資料）：
  A. 2024-10-11 起點，預測 24 個月後（2026-10-12）
  B. 2025-10-10 起點，預測 12 個月後（2026-10-12）
起點的輸入：Yahoo 收盤價（分割調整、不含股利）、起點當時已公布的最近四季 GAAP EPS（data/quarters.csv；TSM 用 data/adr_hist.csv.gz 的
每 ADR 美元）、前一個月底的 10 年期（data/rates_monthly.csv）、股利殖利率、過去 36 個月波動；β 用「起點那年」的走動式 β
（results/orbit_beta.csv，只用當時已揭曉的資料估的），區間用正式版的分位數（README §16）。
三種 EPS：
  1. 當時的分析師預估：Yahoo 的歷史 forward 本益比（trailingForwardPeRatio，起點前最近的一筆：2024-09-19、2025-10-02）
     → forward EPS ＝ 當天收盤 ÷ forward 本益比（約等於「未來 12 個月」的預估，調整後口徑）。
     12 個月：EPS_a ＝ forward EPS；24 個月：再乘一次分析師隱含的年成長 forward ÷ 今天 EPS（上限 +50%、下限 −30%，和模型外推同一規則）。
     EPS_b ＝ EPS_a × 同一個年成長。股價調整＝β_預期 × ln(EPS_b ÷ 今天 EPS)（網頁「沒填自己的 EPS」時的算法）。
  2. EPS 完全猜對：EPS_a ＝ 2026-10-12 實際的最近四季 GAAP EPS；股價調整＝β × ln(EPS_a ÷ 今天 EPS)（原始成長a）。
  1b. 再乘正式版的共識係數（外國 ADR 係數 1）；1c（24 個月）改善版：不再用隱含成長外推（§22.5），EPS_a＝EPS_b＝forward × 係數。
  3. 本益比不變：起點的本益比。
實際：2026-10-12 收盤 ÷ 當時已公布的最近四季 GAAP EPS（網頁同一份，含 Yahoo 更新的新一季）。
誤差拆解：ln(預測本益比 ÷ 實際) ＝ ln(預測股價 ÷ 實際股價) − ln(預測 EPS ÷ 實際 EPS)。
"""
import argparse
import json
import os
import sys
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from pef import cond, orbit                              # noqa: E402
from pef import growth_price as GP                       # noqa: E402

RES = os.path.join(HERE, "results")
DATA = os.path.join(HERE, "data")
TICKERS = {"TSM": "cyclical", "GOOGL": "growth", "NVDA": "cyclical", "MU": "cyclical", "META": "growth"}
NOW = pd.Timestamp("2026-10-12")
SCEN = [("A：2024 起點", pd.Timestamp("2024-10-11"), 24, pd.Timestamp("2024-09-19")),
        ("B：2025 起點", pd.Timestamp("2025-10-10"), 12, pd.Timestamp("2025-10-02"))]
NOW_EPS = {"GOOGL": 19.8395, "META": 26.5386, "MU": 77.33, "NVDA": 7.9078, "TSM": 13.76}   # make_orbit_page 的 e（2026-10-12）
UA = {"User-Agent": "Mozilla/5.0"}


def get_json(url, path):
    if not os.path.exists(path):
        open(path, "wb").write(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
    return json.load(open(path))


def prices(t, raw):
    d = get_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=5y&interval=1d&events=div,split",
                 os.path.join(raw, f"px_{t}.json"))["chart"]["result"][0]
    idx = pd.to_datetime(d["timestamp"], unit="s").normalize()
    close = pd.Series(d["indicators"]["quote"][0]["close"], index=idx).dropna()
    adj = pd.Series(d["indicators"]["adjclose"][0]["adjclose"], index=idx).dropna()
    return close, adj


def fwd_eps(t, raw, date, close):
    d = get_json(f"https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{t}"
                 "?type=trailingForwardPeRatio&period1=1640995200&period2=1800000000", os.path.join(raw, f"fpe_{t}.json"))
    v = {pd.Timestamp(x["asOfDate"]): x["reportedValue"]["raw"] for r in d["timeseries"]["result"]
         for x in r.get("trailingForwardPeRatio", []) if x}
    pe = v.get(date)
    return (float(close[:date].iloc[-1]) / pe, pe) if pe else (np.nan, np.nan)


def eps_then(t, t0):
    """起點當時已公布的最近四季 GAAP EPS（今天的股數口徑）與股利殖利率用的每股股利。"""
    if t == "TSM":
        a = pd.read_csv(os.path.join(DATA, "adr_hist.csv.gz"), parse_dates=["month_end"])
        a = a[(a["ticker"] == "TSM") & (a["month_end"] < t0)].iloc[-1]
        return float(a["eps_usd"]), float(a["dy"]), str(a["eps_period"])
    q = pd.read_csv(os.path.join(DATA, "quarters.csv"), parse_dates=["period_end", "avail"])
    q = q[(q["ticker"] == t) & (q["avail"] <= t0)].sort_values("period_end").tail(4)
    return float(q["ni"].sum() / q["sh_now"].iloc[-1]), float(q["dps_now"].fillna(0).sum()), str(q["period_end"].iloc[-1].date())


def cfactor(t, t0, p0, e0, F, adj, grp):
    """正式版共識校正係數（pef/eps_correct.py）。forward EPS 當作「本財年」共識、距離年報取上限 12 個月（正式版對下一財年也用同一個係數）；
    30／90 天前的共識沒有歷史，留空。"""
    from pef import eps_correct
    q = pd.read_csv(os.path.join(DATA, "quarters.csv"), parse_dates=["period_end", "avail"])
    q = q[(q["ticker"] == t) & (q["avail"] <= t0)].sort_values("period_end")
    rev = q["rev"].tail(8).to_numpy(float)
    g_rev = float(np.log(rev[-4:].sum() / rev[:4].sum())) if len(rev) == 8 and rev[:4].sum() > 0 else np.nan
    m = adj[:t0].resample("ME").last().dropna()
    row = dict(px=p0, eps0=e0, g_rev=g_rev, ret12=float(np.log(m.iloc[-1] / m.iloc[-13])) if len(m) > 13 else np.nan,
               vol36=float(np.log(m).diff().dropna().tail(36).std() * np.sqrt(12)), mc=p0 * float(q["sh_now"].iloc[-1]), grp=grp)
    f = eps_correct.features(t, row, F, t0 + pd.DateOffset(months=12), today=t0)
    k, _ = eps_correct.correction(f, ticker=t)
    return k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    a = ap.parse_args()
    os.makedirs(a.raw, exist_ok=True)
    model = orbit.load_model()
    wb = pd.read_csv(os.path.join(RES, "orbit_beta.csv")).set_index(["h", "年", "方法", "組別"])
    rates = pd.read_csv(os.path.join(DATA, "rates_monthly.csv"), parse_dates=["month_end"]).set_index("month_end")["DGS10"] / 100
    import make_orbit_page as MP                         # 今天的共識（成長定價用，README §24.4）
    tk, _ = MP.tickers()
    nowc = {x["t"]: x for x in tk}
    gm = GP.load()
    rows = []
    for t, grp in TICKERS.items():
        close, adj = prices(t, a.raw)
        p1 = float(close[:NOW].iloc[-1])
        e1 = NOW_EPS[t]
        # 目標日（今天）時市場對下一年的預期：今天的共識換算成未來 12 個月（和網頁 consFor 一樣）
        n = nowc[t]
        c = n.get("c") or {}
        kc = c.get("cf") if c.get("cf") is not None else 1.0
        fy = {pd.Timestamp(c["f0"]): c["c0"] * kc}
        if c.get("c1") is not None:
            fy[pd.Timestamp(c["f1"])] = c["c1"] * kc
        eb_now, _ = orbit.calendarize(fy, pd.Timestamp(n["d"]) + pd.DateOffset(months=12), pd.Timestamp(n["q"]), float(n["e"]), extrapolate=True)
        for name, t0, h, fdate in SCEN:
            p0 = float(close[:t0].iloc[-1])
            e0, dv, eper = eps_then(t, t0)
            dy = dv if t == "TSM" else dv / p0
            r10 = float(rates[rates.index < t0].iloc[-1])
            m = adj[:t0].resample("ME").last().dropna()
            vol = float(np.log(m).diff().dropna().tail(36).std() * np.sqrt(12))
            orb = (r10 + model["erp"] - dy) * h / 12
            F, fpe = fwd_eps(t, a.raw, fdate, close)
            g = float(np.clip(F / e0, 0.7, 1.5)) if e0 > 0 else 1.5
            ea_c = F if h == 12 else F * g
            eb_c = ea_c * g
            gn = orbit.GNAME[grp]
            b_exp = float(wb.loc[(h, t0.year, "預期b＋修正ab", gn), "b0"])
            b_raw = float(wb.loc[(h, t0.year, "原始成長a", gn), "b0"])
            bw = orbit.band_widen("adr", h) if t == "TSM" else 1.0
            base = dict(股票=t, 情境=name, h=h, 起點股價=p0, 起點EPS=e0, 起點EPS季末=eper, 起點本益比=p0 / e0, r10=r10, dy=dy, 波動=vol,
                        forward日=str(fdate.date()), forward本益比=fpe, forwardEPS=F, 年成長=g, 實際股價=p1, 實際EPS=e1, 實際本益比=p1 / e1)
            vers = [("1 當時分析師預估", ea_c, b_exp * np.log(eb_c / e0), "預期b＋修正ab")]
            # 正式版共識校正（訓練資料到 2024-11：對 2025 起點是樣本外；2024 起點要預測的年度在 2025–26 公布，也不在訓練資料裡）；外國 ADR 不校正
            k = cfactor(t, t0, p0, e0, F, adj, grp) if t != "TSM" else 1.0
            base["共識係數"] = k
            vers.append(("1b 分析師預估×共識係數", ea_c * k, b_exp * np.log(eb_c * k / e0), "預期b＋修正ab"))
            if h == 24:                          # 改善版（§22.5）：24 個月不再用隱含成長外推
                vers.append(("1c 改善版（不外推＋係數）", F * k, b_exp * np.log(F * k / e0), "預期b＋修正ab"))
            vers.append(("2 EPS 完全猜對", e1, b_raw * float(np.clip(np.log(e1 / e0), -2, 2)), "原始成長a"))
            for ver, ea, adj_, spec in vers:
                q = model["h"][str(h)]["bands"][spec]["q"]
                ppred = p0 * np.exp(orb + adj_)
                ew = float(np.exp(float(model.get("band_delta", {}).get(str(h), 0)) * min(abs(np.log(ea / e0)), 2.0)))   # §22.4
                qs = [ppred * np.exp(v * (np.clip(vol, *cond.VOL_CLIP) ** model["alpha"]) * bw * ew) for v in q]
                rows.append(dict(base, 版本=ver, 預測EPS=ea, 軌道=orb, 調整=adj_, 預測股價=ppred, 預測本益比=ppred / ea,
                                 本益比80低=qs[0] / ea, 本益比80高=qs[3] / ea, 股價在80區間=bool(qs[0] <= p1 <= qs[3]),
                                 誤差_本益比=np.log(ppred / ea / (p1 / e1)), 誤差_股價=np.log(ppred / p1), 誤差_EPS=np.log(ea / e1)))
            # 成長定價（README §24）：走動式係數（只用目標日在起點那年以前的配對）；F_0＝起點的 forward EPS × 係數
            ret0 = float(np.log(m.iloc[-1] / m.iloc[-13])) if len(m) > 13 else np.nan
            grow = dict(px=p0, eps0=e0, y10=r10, dy=dy, vol36=vol, grp=grp)
            for ver, ea, eb in (("4 成長定價（EPS 猜對＋目標日成長預期用今天共識）", e1, eb_now), ("4b 成長定價（事前：分析師×係數）", ea_c * k, ea_c * k * g)):
                o = GP.predict(grow, h, ea, eb, F * k, ret0, model=model, gm=gm, band_mult=bw, year=t0.year)
                if o is None:
                    continue
                rows.append(dict(base, 版本=ver, 預測EPS=ea, 目標日下一年EPS=eb, 軌道=o["mk"], 調整=o["adj"], 預測股價=o["px"], 預測本益比=o["pe"],
                                 本益比80低=o["pe_lo80"], 本益比80高=o["pe_hi80"], 股價在80區間=bool(o["px_lo80"] <= p1 <= o["px_hi80"]),
                                 誤差_本益比=np.log(o["pe"] / (p1 / e1)), 誤差_股價=np.log(o["px"] / p1), 誤差_EPS=np.log(ea / e1)))
            rows.append(dict(base, 版本="3 本益比不變", 預測EPS=np.nan, 預測股價=np.nan, 預測本益比=p0 / e0,
                             誤差_本益比=np.log((p0 / e0) / (p1 / e1))))
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(RES, "case_2024_2025.csv"), index=False, float_format="%.6g")
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    for name, _, h, _ in SCEN:
        g = d[d["情境"] == name]
        x = g.drop_duplicates("股票")
        print(f"\n== {name}（{h} 個月後 2026-10-12）：起點資料")
        print(x[["股票", "起點股價", "起點EPS", "起點EPS季末", "起點本益比", "r10", "dy", "波動", "forward日", "forward本益比", "forwardEPS", "年成長",
                 "實際股價", "實際EPS", "實際本益比"]].round(3).to_string(index=False))
        print(f"-- 預測 vs 實際（誤差＝ln 比值；+0.20 ≈ 高估 22%）")
        print(g[["股票", "版本", "預測EPS", "預測股價", "預測本益比", "本益比80低", "本益比80高", "實際本益比", "誤差_本益比", "誤差_股價", "誤差_EPS",
                 "股價在80區間"]].round(3).to_string(index=False))
        s = g.groupby("版本")["誤差_本益比"].apply(lambda v: pd.Series({"中位|誤差|": np.median(np.abs(v)), "平均誤差": v.mean()})).unstack()
        print(s.round(3).to_string())


if __name__ == "__main__":
    main()
