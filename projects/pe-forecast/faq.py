#!/usr/bin/env python3
"""README §11 問答用的每一張表（Jake 2026-09-25 的四個問題）。先跑 pe_forecast.py backtest。

    python3 faq.py        # → results/faq.txt，約 2 分鐘

F1 距離與兩個來源      F2 報酬能不能預測       F3 報酬假設比較（資金成本/beta/過去報酬/不動）
F4 80% 預測區間的涵蓋率 F5 價值缺口由誰收斂     F6 隱含利潤率 → 未來利潤率的校準係數
F7 押注大小與兌現比例   F8 MU 隱含利潤率的參數敏感度  F9 逐家公司驗證
"""
import io
import os
import sys
from contextlib import redirect_stdout

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import backtest as bt                  # noqa: E402
from pef import value                           # noqa: E402
from pef.features import attach_future          # noqa: E402
from pef.forecast import PEForecaster, _inputs  # noqa: E402
from pef.load import panel                      # noqa: E402

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
RES = os.path.join(HERE, "results")


def f1_horizon(df):
    print("## F1：預測距離 vs 本益比變化的兩個來源（盈餘為正、2012 起、全部公司×月）")
    rows = []
    for h in (6, 12, 24, 36):
        f = attach_future(df, h)
        d = f[(f["ni_ttm"] > 0) & (f[f"ni_ttm_f{h}"] > 0) & (f["month"] >= "2012-01-01")]
        r = np.log(d[f"mc_f{h}"] / d["mc"])
        g = np.log(d[f"ni_ttm_f{h}"] / d["ni_ttm"])
        rows.append(dict(h=h, n=len(d), 報酬中位_年化=float(np.median(r)) * 12 / h, 報酬波動=float(r.std()),
                         盈餘成長波動=float(g.std()), 報酬與盈餘相關=float(np.corrcoef(r, g)[0, 1]),
                         盈餘占變異=float(g.var() / (r.var() + g.var()))))
    print(pd.DataFrame(rows).round(3).to_string(index=False))


def f2_return_predictability(df, pred, h=12):
    print(f"\n## F2：{h} 個月股價報酬能不能預測？（走動式迴歸，樣本外 R²；基準＝當時為止的平均報酬）")
    f = attach_future(df, h)[["ticker", "month", f"mc_f{h}"]]
    d = pred.merge(df[["ticker", "month", "ret6", "ep_c", "ln_ps", "month_end"]], on=["ticker", "month"]).merge(f, on=["ticker", "month"])
    d["ret"] = np.log(d[f"mc_f{h}"] / d["mc"])
    ok = (d["ni_hat_12"] > 0) & (d["ni_ttm"] > 0)
    d["g_hat"] = np.log((d["ni_hat_12"] / d["ni_ttm"]).where(ok))
    d["imp_gap"] = (d["implied_m"] - df.set_index(["ticker", "month"]).loc[list(zip(d["ticker"], d["month"])), "m_bar"].to_numpy()).clip(-0.5, 0.8)
    cands = {"股價動能（6 個月報酬）": ["ret6"], "E/P": ["ep_c"], "P/S": ["ln_ps"], "模型預測的盈餘成長": ["g_hat"],
             "隱含利潤率缺口": ["imp_gap"], "以上全部": ["ret6", "ep_c", "ln_ps", "g_hat", "imp_gap"]}
    out = []
    for name, cols in cands.items():
        se_m = se_b = 0.0
        n = 0
        for Y in range(2015, 2027):
            asof = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
            tr = d[d["month_end"] + pd.DateOffset(months=h) <= asof].dropna(subset=cols + ["ret"])
            te = d[(d["month_end"] > asof) & (d["month_end"] <= asof + pd.DateOffset(months=12))].dropna(subset=cols + ["ret"])
            if len(tr) < 300 or te.empty:
                continue
            q = {c: tr[c].quantile([.01, .99]).to_numpy() for c in cols}
            X = np.column_stack([np.ones(len(tr))] + [tr[c].clip(*q[c]) for c in cols])
            b = np.linalg.lstsq(X, tr["ret"].clip(*tr["ret"].quantile([.01, .99])), rcond=None)[0]
            Xt = np.column_stack([np.ones(len(te))] + [te[c].clip(*q[c]) for c in cols])
            se_m += float(((te["ret"] - Xt @ b) ** 2).sum())
            se_b += float(((te["ret"] - tr["ret"].mean()) ** 2).sum())
            n += len(te)
        out.append(dict(預測變數=name, n=n, 樣本外R2=1 - se_m / se_b))
    print(pd.DataFrame(out).round(4).to_string(index=False))
    r = d["ret"].dropna()
    print("12 個月 log 報酬分位數（全樣本，含倖存者偏誤）：", {q: round(float(r.quantile(q)), 3) for q in (0.1, 0.25, 0.5, 0.75, 0.9)})


def f3_return_modes(df):
    print("\n## F3：報酬假設的比較（ln PE 中位絕對誤差，括號＝偏誤；偏誤 < 0 ＝ 預測的本益比偏低）")
    for mode, label in (("coe", "資金成本 10年期+5%"), ("beta", "CAPM：10年期+beta×5%"), ("hist", "過去10年中位報酬"), ("zero", "股價不動")):
        pred, _ = bt.run(df, start_year=2015, fc_kwargs=dict(mu_mode=mode), verbose=False)
        for per, rng in (("選模期", bt.SELECT), ("保留期", bt.HOLDOUT)):
            sc = bt.evaluate(df, pred, period=rng)
            a = sc[sc["方法"] == "模型（報酬＝資金成本）"].set_index("h")
            print(f"  {label:22s} {per}", "  ".join(f"{h}m {a.loc[h, '中位絕對誤差']:.3f}({a.loc[h, '偏誤']:+.2f})" for h in (6, 12, 24, 36)),
                  f"｜平均 {a['中位絕對誤差'].mean():.3f}")
    print(f"  beta 的分布（對 68 家等權平均）：中位 {df['beta'].median():.2f}，10%/90% {df['beta'].quantile(.1):.2f}/{df['beta'].quantile(.9):.2f}")


def f4_intervals(df, pred):
    print("\n## F4：80% 預測區間（用當時以前的模型誤差分位數；走動式檢查實際涵蓋率）")
    rows = []
    for h in (6, 12, 24, 36):
        j = bt.joined(df, pred, h)
        j = j[j[f"ln_pe_f{h}"].notna() & j[f"lnpe_hat_{h}"].notna()].copy()
        j["e"] = j[f"ln_pe_f{h}"] - j[f"lnpe_hat_{h}"]
        j["month_end"] = j["month"] + pd.offsets.MonthEnd(0)
        hit = n = 0
        widths = []
        for Y in range(2016, 2027):
            asof = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
            past = j[j["month_end"] + pd.DateOffset(months=h) <= asof]
            te = j[(j["month_end"] > asof) & (j["month_end"] <= asof + pd.DateOffset(months=12))]
            if len(past) < 300 or te.empty:
                continue
            lo, hi = past["e"].quantile([0.1, 0.9])
            hit += int(((te["e"] >= lo) & (te["e"] <= hi)).sum())
            n += len(te)
            widths.append(hi - lo)
        past = j[j["month_end"] + pd.DateOffset(months=h) <= pd.Timestamp("2026-09-30")]
        rows.append(dict(h=h, n=n, 實際涵蓋率=hit / n, 平均寬度=f"×/÷{np.exp(np.mean(widths) / 2):.2f}",
                         現在的誤差分位數_10_50_90=past["e"].quantile([0.1, 0.5, 0.9]).round(3).tolist()))
    print(pd.DataFrame(rows).to_string(index=False))


def value_panel(df):
    parts = []
    for Y in range(2015, 2027):
        asof = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        fc = PEForecaster().fit(df, asof)
        w = df[(df["month_end"] > asof) & (df["month_end"] <= asof + pd.DateOffset(months=12)) & df["sigma"].notna()
               & df["m_bar"].notna() & (df["mc"] > 0)].copy()
        E = fc.E1.predict(w)
        V, _ = value.intrinsic(*_inputs(w, E), fc.v_params, s=0)
        w["lnV"] = np.log(V)
        w["u"] = np.log(w["mc"]) - w["lnV"]
        w["imp"] = fc.implied_margin(w, E)
        parts.append(w[["ticker", "month", "mc", "lnV", "u", "imp", "m_bar", "m_ttm"]])
    return pd.concat(parts)


def f5_convergence(P):
    print("\n## F5：股價與「歷史利潤率 DCF 價值」的缺口，是誰在收斂？（Δ 對缺口 u 的斜率）")
    for h in (12, 24):
        fut = P[["ticker", "month", "mc", "lnV"]].copy()
        fut["month"] = fut["month"] - pd.DateOffset(months=h)
        j = P.merge(fut, on=["ticker", "month"], suffixes=("", "_f"))
        j = j[np.isfinite(j["u"]) & np.isfinite(j["lnV_f"]) & np.isfinite(j["lnV"])]
        X = np.column_stack([np.ones(len(j)), j["u"].clip(-3, 3)])
        bP = np.linalg.lstsq(X, np.log(j["mc_f"] / j["mc"]).clip(-2, 2), rcond=None)[0][1]
        bV = np.linalg.lstsq(X, (j["lnV_f"] - j["lnV"]).clip(-2, 2), rcond=None)[0][1]
        print(f"  {h} 個月 n={len(j)}：股價的斜率 {bP:+.3f}（負＝股價回頭）；基本面價值的斜率 {bV:+.3f}（正＝基本面追上）；"
              f"缺口收斂 {bV - bP:.2f}")


def f6_f7_calibration(df, P):
    print("\n## F6：隱含利潤率 → 未來利潤率的校準係數（偏離＝減掉 5 年中位）")
    for h in (12, 24):
        f = attach_future(df, h)[["ticker", "month", f"ni_ttm_f{h}", f"rev_ttm_f{h}"]]
        j = P.merge(f, on=["ticker", "month"])
        j["m_act"] = j[f"ni_ttm_f{h}"] / j[f"rev_ttm_f{h}"]
        j = j[np.isfinite(j["m_act"]) & np.isfinite(j["imp"]) & np.isfinite(j["m_ttm"]) & np.isfinite(j["m_bar"])]
        for per, lo, hi in (("選模期", "2015-01-01", "2021-12-31"), ("保留期", "2022-01-01", "2026-12-31"), ("全期", "2015-01-01", "2026-12-31")):
            x = j[(j["month"] >= lo) & (j["month"] <= hi)]
            y = (x["m_act"] - x["m_bar"]).clip(-0.5, 0.5).to_numpy()
            a = (x["imp"] - x["m_bar"]).clip(-0.5, 0.8).to_numpy()
            c = (x["m_ttm"] - x["m_bar"]).clip(-0.5, 0.5).to_numpy()
            b = np.linalg.lstsq(np.column_stack([np.ones(len(x)), c, a]), y, rcond=None)[0]
            print(f"  {h} 個月 {per} n={len(x)}：未來偏離 ＝ {b[0]:+.3f} ＋ {b[1]:.2f}×現在偏離 ＋ {b[2]:.2f}×隱含偏離")
        if h == 24:
            print("\n## F7：押注大小 vs 兌現（24 個月，全期）")
            j["押注"] = (j["imp"] - j["m_bar"]).clip(-0.5, 0.8)
            j["實際"] = (j["m_act"] - j["m_bar"]).clip(-0.5, 0.5)
            j["組"] = pd.cut(j["押注"], [-0.5, -0.1, -0.03, 0.03, 0.1, 0.2, 0.8])
            g = j.groupby("組", observed=True)
            t = pd.DataFrame({"n": g.size(), "押注中位": g["押注"].median(), "實際偏離中位": g["實際"].median(),
                              "方向對的比例": g.apply(lambda s: float(np.mean(np.sign(s["實際"]) == np.sign(s["押注"]))), include_groups=False)})
            print(t.round(3).to_string())


def f8_sensitivity(df, ticker="MU"):
    print(f"\n## F8：{ticker} 隱含長期淨利率對 DCF 參數的敏感度（2026-09；列＝風險溢酬×成長半衰期，欄＝長期成長率）")
    row = df[df["ticker"] == ticker].tail(1)
    fc = PEForecaster().fit(df, row["month_end"].iloc[0])
    E = fc.E1.predict(row)
    res = []
    for erp in (0.04, 0.05, 0.06):
        for H in (3, 5, 8):
            for g in (0.02, 0.03, 0.04):
                fc.v_params = dict(theta0=erp, theta1=0.0, H=H, g_inf=g)
                res.append(dict(風險溢酬=erp, 半衰期=H, 長期成長=g, 隱含=float(fc.implied_margin(row, E)[0])))
    print(f"  5 年中位淨利率 {row['m_bar'].iloc[0]:.3f}")
    print(pd.DataFrame(res).pivot_table(index=["風險溢酬", "半衰期"], columns="長期成長", values="隱含").round(3).to_string())


def f9_per_company(df, pred):
    print("\n## F9：逐家公司驗證（12 個月，所有「12 個月前的預測 vs 實際」配對的中位 ln 誤差）")
    j = bt.joined(df, pred, 12)
    j = j[j["ln_pe_f12"].notna() & j["lnpe_hat_12"].notna() & j["b_rw"].notna()]
    per = j.groupby("ticker").apply(lambda g: pd.Series(dict(
        產業=g["sector"].iloc[0], n=len(g), 模型=np.median(np.abs(g["lnpe_hat_12"] - g["ln_pe_f12"])),
        隨機漫步=np.median(np.abs(g["b_rw"] - g["ln_pe_f12"])),
        歷史均值=np.nanmedian(np.abs(g["b_hist"] - g["ln_pe_f12"])))), include_groups=False)
    per["贏隨機漫步"] = per["模型"] < per["隨機漫步"]
    per["贏歷史均值"] = per["模型"] < per["歷史均值"]
    print(f"  公司 {len(per)} 家：贏隨機漫步 {int(per['贏隨機漫步'].sum())} 家、贏歷史均值 {int(per['贏歷史均值'].sum())} 家")
    print(per.groupby("產業")[["贏隨機漫步", "贏歷史均值"]].agg(["sum", "count"]).to_string())
    print(per.sort_values("模型").round(3).to_string())
    per.to_csv(os.path.join(RES, "per_company_12m.csv"), float_format="%.4f")


def main():
    df, _ = panel()
    pred = pd.read_csv(os.path.join(RES, "predictions.csv.gz"), parse_dates=["month"])
    buf = io.StringIO()
    with redirect_stdout(buf):
        f1_horizon(df)
        f2_return_predictability(df, pred)
        f3_return_modes(df)
        f4_intervals(df, pred)
        P = value_panel(df)
        f5_convergence(P)
        f6_f7_calibration(df, P)
        f8_sensitivity(df)
        f9_per_company(df, pred)
    txt = buf.getvalue()
    open(os.path.join(RES, "faq.txt"), "w").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
