#!/usr/bin/env python3
"""README §23.2（三）：台積電每月公布的營收，能不能提早更新 EPS 預估？（2330 台股，新台幣）

    python3 research/tsmc_monthly_revenue.py [--refresh] > results/tsmc_monthly_revenue.txt

資料：FinMind 公開 API（不用金鑰）—— TaiwanStockMonthRevenue（月營收）、TaiwanStockFinancialStatements（單季 EPS、營收）、
  TaiwanStockPrice（日收盤，未還原）、TaiwanStockDividend（現金股利、除息日）。存成 data/tsmc/*.csv；--refresh 重抓。
可用時間（只用當時已公布的）：月營收＝次月 10 日；季報＝季末後 20 天（台積電法說會大約在 1、4、7、10 月中）。

一、本季 EPS 即時估計（2014Q1 起）：本季 EPS ≈ 本季營收 × 上一季「EPS ÷ 營收」
   每個資訊時點：季初（只知道上一季 EPS）→ 第 1 個月營收 ×3 → 前 2 個月 ×1.5 → 3 個月都公布（法說會前約一週）。
   對照：上一季 EPS 原樣、去年同季 EPS × 最近一季營收年增。
二、12 個月後的最近四季 EPS（軌道模型的 EPS_a）與 12 個月後本益比（每個月底起點，2016-01～2025-09；起點重疊、實際上只有約 10 個獨立年度）
   不變：今天的最近四季 EPS｜營收年增外推：× 最近 3 個月營收 ÷ 去年同期｜營收年化：最近 3 個月營收 × 4 × 上一季「EPS ÷ 營收」
   ｜年化＋年增各半：營收年化 × (1 ＋ 年增率 ÷ 2)｜EPS 完全猜對（上限）；另附「本益比不變」。
   另看 12 個月後股價：軌道模型的股價 vs「今天的本益比 × EPS_a」。
   本益比＝股價 × exp(軌道 ＋ β × ln(EPS_a ÷ 今天 EPS)) ÷ EPS_a；軌道＝美國 10 年期＋5% − 股利殖利率（台股用美國利率只是近似，
   各寫法共用同一個軌道，比較的是 EPS 輸入），β＝走動式「原始成長a」半導體組 12 個月。
限制：沒有台積電歷史分析師共識可比（分析師本來就會看月營收，月營收對「共識」的領先幅度會比這裡對「不變」的小）；只有一家公司。
"""
import argparse
import io
import json
import os
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "results")
DD = os.path.join(HERE, "data", "tsmc")
API = "https://api.finmindtrade.com/api/v4/data?dataset={ds}&data_id=2330&start_date=2013-01-01"
REV_LAG_DAY = 10
Q_LAG = 20
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def fetch(ds):
    with urllib.request.urlopen(API.format(ds=ds), timeout=60) as r:
        d = json.load(r)
    if d.get("status") != 200:
        raise RuntimeError(f"{ds}: {d.get('msg')}")
    return pd.DataFrame(d["data"])


def load(refresh):
    os.makedirs(DD, exist_ok=True)
    paths = {k: os.path.join(DD, f"{k}.csv") for k in ("month_revenue", "quarterly", "price_monthly", "dividend")}
    if refresh or not all(os.path.exists(p) for p in paths.values()):
        r = fetch("TaiwanStockMonthRevenue")
        r = r[["revenue_year", "revenue_month", "revenue"]].rename(columns={"revenue_year": "year", "revenue_month": "month"})
        r.drop_duplicates(["year", "month"], keep="last").sort_values(["year", "month"]).to_csv(paths["month_revenue"], index=False)
        f = fetch("TaiwanStockFinancialStatements")
        q = f[f["type"].isin(["EPS", "Revenue", "EquityAttributableToOwnersOfParent"])].pivot(index="date", columns="type", values="value")
        q = q.rename(columns={"EPS": "eps", "Revenue": "revenue", "EquityAttributableToOwnersOfParent": "ni_parent"}).reset_index()
        q.rename(columns={"date": "quarter_end"}).to_csv(paths["quarterly"], index=False)
        p = fetch("TaiwanStockPrice")[["date", "close"]]
        p["date"] = pd.to_datetime(p["date"])
        p = p.set_index("date")["close"].resample("ME").last().dropna().reset_index().rename(columns={"date": "month_end"})
        p.to_csv(paths["price_monthly"], index=False)
        dv = fetch("TaiwanStockDividend")[["CashExDividendTradingDate", "CashEarningsDistribution", "CashStatutorySurplus"]]
        dv = dv[dv["CashExDividendTradingDate"].astype(str).str.len() == 10]
        dv = pd.DataFrame({"ex_date": dv["CashExDividendTradingDate"], "cash": dv["CashEarningsDistribution"].astype(float) + dv["CashStatutorySurplus"].astype(float)})
        dv.to_csv(paths["dividend"], index=False)
    r = pd.read_csv(paths["month_revenue"])
    r["rel"] = pd.to_datetime(dict(year=r["year"], month=r["month"], day=1)) + pd.DateOffset(months=1) + pd.Timedelta(days=REV_LAG_DAY - 1)
    r["q"] = pd.PeriodIndex.from_fields(year=r["year"], quarter=(r["month"] - 1) // 3 + 1, freq="Q")
    q = pd.read_csv(paths["quarterly"], parse_dates=["quarter_end"])
    q["q"] = q["quarter_end"].dt.to_period("Q")
    q["rel"] = q["quarter_end"] + pd.Timedelta(days=Q_LAG)
    rq = r.groupby("q").agg(rev_m=("revenue", "sum"), n=("revenue", "size"))
    q = q.join(rq, on="q")
    p = pd.read_csv(paths["price_monthly"], parse_dates=["month_end"]).set_index("month_end")["close"]
    dv = pd.read_csv(paths["dividend"], parse_dates=["ex_date"])
    return r, q.sort_values("q").reset_index(drop=True), p, dv


def nowcast(r, q):
    rows = []
    qi = q.set_index("q")
    for i in range(5, len(q)):
        cur, prev, ly = q.iloc[i], q.iloc[i - 1], q.iloc[i - 4]
        if not (cur["eps"] > 0 and prev["eps"] > 0 and prev["n"] == 3 and cur["n"] == 3):
            continue
        m = r[r["q"] == cur["q"]].sort_values("month")["revenue"].to_numpy()
        epr = prev["eps"] / prev["rev_m"]
        epr4 = np.mean([q.iloc[i - k]["eps"] / q.iloc[i - k]["rev_m"] for k in range(1, 5)])
        prev_ly = qi.loc[prev["q"] - 4] if (prev["q"] - 4) in qi.index else None
        yoy = prev["rev_m"] / prev_ly["rev_m"] if prev_ly is not None else np.nan
        f = {"上一季 EPS 原樣": prev["eps"], "去年同季 × 營收年增": ly["eps"] * yoy, "第 1 個月營收 ×3": 3 * m[0] * epr,
             "前 2 個月 ×1.5": 1.5 * (m[0] + m[1]) * epr, "3 個月營收（法說前約一週）": m.sum() * epr,
             "3 個月營收 × 近 4 季平均利潤率": m.sum() * epr4}
        rows.append(dict(q=str(cur["q"]), 實際=cur["eps"], **{k: float(np.log(v / cur["eps"])) for k, v in f.items()}))
    return pd.DataFrame(rows)


def forward(r, q, p, dv, bt, rates):
    rows = []
    months = p.index[(p.index >= "2016-01-01") & (p.index <= "2025-09-30")]          # 半導體組 β 從 2016 才有

    def ttm(t):
        k = q[q["rel"] <= t].tail(4)
        return float(k["eps"].sum()) if len(k) == 4 else np.nan
    for t in months:
        e0 = ttm(t)
        t12 = t + pd.offsets.MonthEnd(12)
        e12 = ttm(t12)
        if not (e0 > 0 and e12 > 0) or t12 not in p.index:
            continue
        rr = r[r["rel"] <= t].tail(3)
        ym = set(zip(rr["year"] - 1, rr["month"]))
        ly = r[[(y, m) in ym for y, m in zip(r["year"], r["month"])]]
        yoy = rr["revenue"].sum() / ly["revenue"].sum() if len(ly) == 3 else np.nan
        lq = q[q["rel"] <= t].iloc[-1]
        run = rr["revenue"].sum() * 4 * lq["eps"] / lq["rev_m"]
        cand = {"不變（今天的四季 EPS）": e0, "營收年增外推": e0 * yoy, "營收年化 × 上一季利潤率": run,
                "年化 ＋ 年增一半": run * (1 + (yoy - 1) / 2), "EPS 完全猜對": e12}
        cash = dv[(dv["ex_date"] > t - pd.DateOffset(months=12)) & (dv["ex_date"] <= t)]["cash"].sum()
        dy = cash / p[t]
        r10 = float(rates[rates.index <= t].iloc[-1])
        orb = r10 + 0.05 - dy
        b = bt.get(t.year, np.nan)
        act = np.log(p[t12] / e12)
        row = dict(t=t, e0=e0, e12=e12, 本益比不變=float(np.log(p[t] / e0) - act))
        for k, v in cand.items():
            lp = np.log(p[t]) + orb + b * float(np.clip(np.log(v / e0), -2, 2))
            row[k] = float(lp - np.log(v) - act)
            row[k + "_EPS"] = float(np.log(v / e12))
            row[k + "_價模型"] = float(lp - np.log(p[t12]))                      # 軌道模型的股價
            row[k + "_價固定本益比"] = float(np.log(p[t] / e0 * v) - np.log(p[t12]))  # 今天的本益比 × EPS_a
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    r, q, p, dv = load(a.refresh)
    say(f"資料：月營收 {r['year'].min()}-{r['month'].iloc[0]:02d}～{r['year'].max()}-{r['month'].iloc[-1]:02d}（{len(r)} 個月）；"
        f"單季 EPS {q['q'].iloc[0]}～{q['q'].iloc[-1]}（{len(q)} 季）；月底股價 {p.index[0]:%Y-%m}～{p.index[-1]:%Y-%m}")
    bad = q[(q["n"] == 3) & ((q["rev_m"] / q["revenue"] - 1).abs() > 0.01)]
    say(f"檢查：季報營收 vs 3 個月月營收加總，差 > 1% 的季數 {len(bad)}／{int((q['n'] == 3).sum())}")

    n = nowcast(r, q)
    cols = [c for c in n.columns if c not in ("q", "實際")]
    say(f"\n== 一、本季 EPS 即時估計（{n['q'].iloc[0]}～{n['q'].iloc[-1]}，{len(n)} 季）：ln(估計 ÷ 實際)")
    rows = []
    for c in cols:
        v = n[c]
        rows.append(dict(做法=c, 中位絕對誤差=float(np.median(np.abs(v))), 平均絕對誤差=float(np.mean(np.abs(v))), 偏差中位=float(np.median(v)),
                         在5內=float(np.mean(np.abs(np.exp(v) - 1) <= 0.05)), 在10內=float(np.mean(np.abs(np.exp(v) - 1) <= 0.10)),
                         近5年中位=float(np.median(np.abs(v[n["q"] >= "2021Q1"])))))
    say(pd.DataFrame(rows).round(3).to_string(index=False))
    say("  最近 8 季（估計 ÷ 實際 − 1）：")
    show = n.tail(8)[["q", "實際", "上一季 EPS 原樣", "第 1 個月營收 ×3", "前 2 個月 ×1.5", "3 個月營收（法說前約一週）"]].copy()
    for c in show.columns[2:]:
        show[c] = (np.exp(show[c]) - 1).map(lambda v: f"{v:+.1%}")
    say(show.to_string(index=False))
    # 即時：最新一季若 3 個月營收都出來、季報還沒有
    last_q = r["q"].max()
    if last_q not in set(q["q"]) and (r["q"] == last_q).sum() == 3:
        prev = q.iloc[-1]
        est = r[r["q"] == last_q]["revenue"].sum() * prev["eps"] / prev["rev_m"]
        lo, hi = np.quantile(np.exp(n["3 個月營收（法說前約一週）"]), [0.1, 0.9])
        say(f"\n  ▶ 即時預估 {last_q} EPS（3 個月營收都已公布、季報還沒出）：{est:.2f} 元"
            f"（上一季 {prev['eps']:.2f}；用過去的誤差 10–90% 分位 → {est / hi:.2f}～{est / lo:.2f}）")
        n.attrs["live"] = (str(last_q), float(est), float(est / hi), float(est / lo))

    beta = pd.read_csv(os.path.join(RES, "orbit_beta.csv"))
    bt = beta[(beta["方法"] == "原始成長a") & (beta["h"] == 12) & (beta["組別"] == "半導體／設備／記憶體")].set_index("年")["b0"].to_dict()
    rates = pd.read_csv(os.path.join(HERE, "data", "rates_monthly.csv"), parse_dates=["month_end"]).set_index("month_end")["DGS10"] / 100
    f = forward(r, q, p, dv, bt, rates)
    names = ["不變（今天的四季 EPS）", "營收年增外推", "營收年化 × 上一季利潤率", "年化 ＋ 年增一半", "EPS 完全猜對"]
    say(f"\n== 二、12 個月後（每個月底起點 {f['t'].min():%Y-%m}～{f['t'].max():%Y-%m}，{len(f)} 個；重疊，約 {len(f) / 12:.0f} 個獨立年度）")
    rows = []
    for k in names:
        rows.append(dict(EPS_a=k, EPS中位誤差=float(np.median(np.abs(f[k + "_EPS"]))), EPS偏差中位=float(np.median(f[k + "_EPS"])),
                         本益比中位誤差=float(np.median(np.abs(f[k]))), 本益比在20內=float(np.mean(np.abs(np.exp(f[k]) - 1) <= 0.2)),
                         近5年本益比誤差=float(np.median(np.abs(f.loc[f["t"] >= "2020-10-01", k]))),
                         股價誤差_軌道模型=float(np.median(np.abs(f[k + "_價模型"]))), 股價誤差_今天本益比乘EPS=float(np.median(np.abs(f[k + "_價固定本益比"])))))
    rows.append(dict(EPS_a="（本益比不變）", 本益比中位誤差=float(np.median(np.abs(f["本益比不變"]))),
                     本益比在20內=float(np.mean(np.abs(np.exp(f["本益比不變"]) - 1) <= 0.2)),
                     近5年本益比誤差=float(np.median(np.abs(f.loc[f["t"] >= "2020-10-01", "本益比不變"])))))
    t = pd.DataFrame(rows)
    say(t.round(3).to_string(index=False))
    yr = f.assign(Y=f["t"].dt.year).groupby("Y")[["不變（今天的四季 EPS）", "營收年增外推", "營收年化 × 上一季利潤率", "年化 ＋ 年增一半"]].apply(
        lambda g: g.abs().median())
    say("  逐年（起點年份）中位 |本益比誤差|：")
    say(yr.round(3).to_string())
    n.to_csv(os.path.join(RES, "tsmc_nowcast.csv"), index=False, float_format="%.6f")
    f.to_csv(os.path.join(RES, "tsmc_forward.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "tsmc_monthly_revenue.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
