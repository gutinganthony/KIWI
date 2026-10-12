#!/usr/bin/env python3
"""共識校正搬到中小型股：用 S&P 500 訓練的校正模型，對 Russell 2000／S&P 400／S&P 600 的共識也有用嗎？（README §20.3）

    python3 lab_eps_correction_small.py --cache <lab_orbit 暫存目錄> [--build <L.build 的 pickle>]   # 訓練樹模型（約 3 分鐘）

資料：中小型股季面板（lab_orbit_small.py 的 small_cond.pkl：季末股價、GAAP 最近四季、12 個月後的股價與 EPS）、
  中小型股的 I/B/E/S 本財年共識（osap_small.py → data/osap/feps_small.csv.gz，已換成面板口徑）、
  會計年度結束月份＝申報間隔最長的季末月份（年報比季報晚申報；在 S&P 500 上和 Yahoo 對照 98.9% 正確）。
起點：每季季末（中小型股只有季資料），距離年報 0.5～12 個月；目標＝ln(實際 GAAP 本財年 EPS ÷ 共識)。
線索：和正式版完全相同（FEATS_NOW）。市值百分位用「當月 S&P 500 面板」當參考（和正式版一樣），所以中小型股多半落在最低那一端。
比較（走動式，每年 1 月只用報告日在前一年底以前的列訓練；評分 2020–2024）：
  共識原樣｜這家過去的偏差｜S&P 500 訓練的樹（＝正式版直接搬過來）｜S&P 500＋中小型股一起訓練的樹｜上兩者＋同時點護欄
評分：EPS 誤差（全部、依距離年報、依指數），以及 12 個月後本益比（距離年報 9.5–12.5 個月的起點，EPS_a＝校正後的共識）。
輸出：results/eps_correction_small.txt、eps_correction_small_scores.csv
"""
import argparse
import io
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab_eps_correction as L                           # noqa: E402
import lab_orbit_consensus as LC                         # noqa: E402
from pef import orbit                                    # noqa: E402

RES, DATA = os.path.join(HERE, "results"), os.path.join(HERE, "data")
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def fy_month_by_lag(q):
    """申報間隔最長的季末月份＝會計年度結束月份（52／53 週制落在月初的季末算上個月）。"""
    q = q[q["period_end"] >= "2015-01-01"].copy()
    q["lag"] = (q["filed"] - q["period_end"]).dt.days
    q["m"] = q["period_end"].dt.month
    early = q["period_end"].dt.day <= 7
    q.loc[early, "m"] = (q.loc[early, "period_end"] - pd.Timedelta(days=8)).dt.month
    return q.groupby("ticker").apply(lambda g: int(g.groupby("m")["lag"].median().idxmax()) if len(g) else None)


def build_small(cache):
    c = pd.read_pickle(os.path.join(cache, "small_cond.pkl")).sort_values(["ticker", "month"]).copy()
    prev_px, prev_m = c.groupby("ticker")["px"].shift(1), c.groupby("ticker")["month"].shift(1)
    c["qret"] = np.where((c["month"] - prev_m).dt.days.between(80, 100), np.log(c["px"] / prev_px), np.nan)
    c["vol36"] = c.groupby("ticker")["qret"].transform(lambda s: s.rolling(12, min_periods=8).std()) * 2
    c["grp"] = c["sector"].map(orbit.GROUPS).fillna("other")
    fe = pd.read_csv(os.path.join(DATA, "osap", "feps_small.csv.gz"))
    fe["month"] = pd.to_datetime(fe["yyyymm"].astype(int).astype(str) + "01")
    q = pd.read_csv(os.path.join(DATA, "quarters_small.csv"), parse_dates=["period_end", "filed", "avail"])
    fym = fy_month_by_lag(q)
    fy_tab = {t: LC.fy_report_dates(g, int(fym[t])) for t, g in q.groupby("ticker") if t in fym.index and pd.notna(fym[t])}

    def fy_of(t, me):
        fy = fy_tab.get(t)
        if fy is None or fy.empty:
            return None, None, None
        fut, prev = fy[fy["report"] > me], fy[fy["report"] <= me]
        if fut.empty:
            return None, None, None
        return fut.iloc[0]["fy_end"], fut.iloc[0]["report"], (prev["report"].iloc[-1] if len(prev) else pd.NaT)

    # 每月 FEPS 的本財年（算 1／3 個月修正：只比同一個本財年）
    fe["me"] = fe["month"] + pd.offsets.MonthEnd(0)
    fe["fy1"] = [fy_of(t, me)[0] for t, me in zip(fe["ticker"], fe["me"])]
    fe = fe.sort_values(["ticker", "month"])
    for k in (1, 3):
        pf, pfy, pm = (fe.groupby("ticker")[c_].shift(k) for c_ in ("feps", "fy1", "month"))
        fe[f"chg{k}"] = np.where((pfy == fe["fy1"]) & (fe["month"] - pm).dt.days.between(28 * k, 32 * k), fe["feps"] - pf, np.nan)
    d = c.merge(fe[["ticker", "month", "feps", "fgr5y", "chg1", "chg3"]], on=["ticker", "month"], how="inner")
    meta = [fy_of(t, m + pd.offsets.MonthEnd(0)) for t, m in zip(d["ticker"], d["month"])]
    d["fy1"], d["report"], d["prev_report"] = [x[0] for x in meta], [x[1] for x in meta], [x[2] for x in meta]
    d = d[d["fy1"].notna()].copy()
    d["fy1"], d["report"], d["prev_report"] = pd.to_datetime(d["fy1"]), pd.to_datetime(d["report"]), pd.to_datetime(d["prev_report"])
    d["lead"] = (d["report"] - (d["month"] + pd.offsets.MonthEnd(0))).dt.days / 30.44
    ok = d["prev_report"].isna() | ~((d["prev_report"] > d["month"] + pd.Timedelta(days=13)) & (d["prev_report"] <= d["month"] + pd.offsets.MonthEnd(0)))
    d = d[ok & (d["lead"] > 0.5) & (d["lead"] <= 12.0)].copy()
    # 實際本財年 EPS＝period_end 等於年度結束日的那一列的 GAAP 最近四季
    act = c[["ticker", "period_end", "eps0"]].dropna().drop_duplicates(["ticker", "period_end"]).rename(columns={"period_end": "fy1", "eps0": "actual"})
    d = d.merge(act, on=["ticker", "fy1"], how="left")
    d["near_split"] = False
    d["tgt"] = np.where((d["actual"] > 0) & (d["feps"] > 0), np.log(d["actual"] / d["feps"]), np.nan)
    d["tgt"] = d["tgt"].clip(-1.5, 1.5)
    d["cons_g"] = np.where((d["eps0"] > 0) & (d["feps"] > 0), np.log(d["feps"] / d["eps0"]), np.nan).clip(-2, 2)
    d["loss0"] = (d["eps0"] <= 0).astype(float)
    d["rev1"], d["rev3"] = (d["chg1"] / d["px"]).clip(-0.2, 0.2), (d["chg3"] / d["px"]).clip(-0.2, 0.2)
    d["ltg"] = (d["fgr5y"] / 100).clip(-0.5, 1.0)
    d["grp_id"] = d["grp"].map(L.GRP_ID).astype(float)
    # 過去偏差（lead 9–12，報告日 ≤ 當月；季起點比較少落在 10.5–12）、同時點偏差
    d = d.sort_values(["ticker", "month"]).reset_index(drop=True)
    d["lead_b"] = pd.cut(d["lead"], [0.5, 3, 6, 9, 12], labels=False)
    base = d[d["tgt"].notna()]
    pf = base.groupby(["ticker", "lead_b", "fy1"]).agg(report=("report", "first"), tg=("tgt", "median"),
                                                      ab=("tgt", lambda v: np.median(np.abs(v)))).reset_index()
    byb = {k: g.sort_values("report") for k, g in pf.groupby(["ticker", "lead_b"])}
    by9 = {t: g.sort_values("report") for t, g in base[base["lead"] > 9].groupby("ticker")}
    pb, npb, pbl, pal, pnl = [], [], [], [], []
    for t, b, mo in zip(d["ticker"], d["lead_b"], d["month"]):
        g = by9.get(t)
        past = g[g["report"] <= mo]["tgt"] if g is not None else pd.Series(dtype=float)
        pb.append(float(np.median(past)) if len(past) >= 2 else np.nan)
        npb.append(len(past))
        g2 = byb.get((t, b))
        pp = g2[g2["report"] <= mo] if g2 is not None else None
        ok2 = pp is not None and len(pp) >= 2
        pbl.append(float(np.median(pp["tg"])) if ok2 else np.nan)
        pal.append(float(np.median(pp["ab"])) if ok2 else np.nan)
        pnl.append(0 if pp is None else len(pp))
    d["past_bias"], d["n_past"], d["n_past8"] = pb, npb, np.minimum(npb, 8)
    d["pb_lead"], d["pb_abs"], d["pb_lead_n"] = pbl, pal, pnl
    # 市值百分位：當月 S&P 500 面板當參考
    x = pd.read_pickle(os.path.join(cache, "orbit_x2.pkl"))[["month", "ln_mc"]].dropna()
    ref = {m: np.sort(g["ln_mc"].to_numpy()) for m, g in x.groupby("month")}
    d["mc_rank"] = [float(np.searchsorted(ref[m], v, side="right") / len(ref[m])) if m in ref and np.isfinite(v) else np.nan
                    for m, v in zip(d["month"], d["ln_mc"])]
    mem = pd.read_csv(os.path.join(DATA, "members_small.csv"), parse_dates=["date"])
    mem["month"] = mem["date"] - pd.offsets.MonthBegin(1)
    for k in ("rut", "sp400", "sp600"):
        d[k] = d.set_index(["ticker", "month"]).index.isin(pd.MultiIndex.from_frame(mem[mem["idx"] == k][["ticker", "month"]]))
    return d


def fit_predict(tr, te, feats):
    X = tr[feats].to_numpy(float)
    X[~np.isfinite(X)] = np.nan
    m = HistGradientBoostingRegressor(**L.GBM).fit(X, tr["tgt"].to_numpy(float))
    Xt = te[feats].to_numpy(float)
    Xt[~np.isfinite(Xt)] = np.nan
    return m.predict(Xt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--build", default=None, help="S&P 500 的 L.build() pickle（省時間）")
    a = ap.parse_args()
    sp = pd.read_pickle(a.build) if a.build and os.path.exists(a.build) else L.build(a.cache)
    sp = sp[sp["tgt"].notna() & ~sp["near_split"]]
    d = build_small(a.cache)
    say(f"中小型股校正資料：{len(d):,} 個公司季（{d['ticker'].nunique()} 家，{d['month'].min():%Y-%m}～{d['month'].max():%Y-%m}）；"
        f"有目標值 {int(d['tgt'].notna().sum()):,}；市值百分位（對照 S&P 500）中位 {d['mc_rank'].median():.2f}")
    say(f"共識比實際高（ln(實際÷共識) 中位）：中小型股 {d['tgt'].median():+.3f}；S&P 500 {sp['tgt'].median():+.3f}")
    z = d[d["tgt"].notna()]
    say("\n== 1. 邏輯檢查（中小型股）：五分位 → ln(實際 ÷ 共識) 中位數")
    for f in ("cons_g", "past_bias", "rev3", "ret12"):
        zz = z.dropna(subset=[f])
        if len(zz) < 300:
            continue
        qn = pd.qcut(zz[f].rank(method="first"), 5, labels=False)
        med = zz.groupby(qn)["tgt"].median()
        say(f"  {f}：" + "  ".join(f"{v:+.3f}" for v in med) + f"   Spearman {zz[f].corr(zz['tgt'], method='spearman'):+.3f}（n={len(zz):,}）")
    preds = {k: pd.Series(np.nan, index=d.index) for k in ("S&P 500 訓練", "一起訓練")}
    for Y in range(2020, 2025):
        cut = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        te = d[(d["month"] > cut) & (d["month"] <= cut + pd.DateOffset(months=12))]
        if te.empty:
            continue
        tr_sp = sp[sp["report"] <= cut]
        tr_sm = d[(d["report"] <= cut) & d["tgt"].notna()]
        preds["S&P 500 訓練"].loc[te.index] = fit_predict(tr_sp, te, L.FEATS_NOW)
        preds["一起訓練"].loc[te.index] = fit_predict(pd.concat([tr_sp, tr_sm]), te, L.FEATS_NOW)
    for k in list(preds):
        d[k] = preds[k]
        has = d["pb_lead"].notna() & (d["pb_lead_n"] >= 4)
        d[k + "＋護欄"] = np.where(has, np.clip(d[k], d["pb_lead"] - d["pb_abs"], d["pb_lead"] + d["pb_abs"]), d[k])
    meths = ["原樣", "過去偏差", "S&P 500 訓練", "S&P 500 訓練＋護欄", "一起訓練", "一起訓練＋護欄"]
    ev = d[d["tgt"].notna() & d["S&P 500 訓練"].notna()].copy()
    ev["過去偏差"] = ev["past_bias"].fillna(0)
    ev["原樣"] = 0.0
    ev["lead_lab"] = pd.cut(ev["lead"], [0.5, 3, 6, 9, 12], labels=["0.5–3", "3–6", "6–9", "9–12"])
    rows = []
    groups = [("全部", ev)] + [(f"距離年報 {k}", g) for k, g in ev.groupby("lead_lab", observed=True)] + \
             [(nm, ev[ev[k]]) for k, nm in (("rut", "Russell 2000"), ("sp400", "S&P 400"), ("sp600", "S&P 600"))] + \
             [(f"{Y}", g) for Y, g in ev.groupby(ev["month"].dt.year)]
    for lab, g in groups:
        if len(g) < 100:
            continue
        r = dict(樣本=lab, n=len(g))
        for k in meths:
            r[k] = float(np.median(np.abs(g["tgt"] - g[k])))
        rows.append(r)
    sc = pd.DataFrame(rows)
    say("\n== 2. EPS 誤差：中位 |ln(實際 ÷ 校正後的共識)|（中小型股，起點 2020–2024，走動式樣本外）")
    say(sc.round(4).to_string(index=False))

    # 3. 12 個月後本益比（距離年報 9.5–12.5 個月的起點：12 個月後的最近四季≈本財年）
    model = orbit.load_model(RES)
    b = {g: v[0] for g, v in model["h"]["12"]["beta"]["原始成長a"].items()}
    one = ev[(ev["lead"] > 9.5) & (ev["lead"] <= 12.5) & (ev["eps0"] > 0) & (ev["eps_f12"] > 0) & ev["rp_12"].notna()].copy()
    olr = one["y10"] + model["erp"] - one["dy"].fillna(0)
    act = np.log(one["px"]) + one["rp_12"] - np.log(one["eps_f12"])
    pe = dict(n=len(one), 本益比不變=float(np.median(np.abs(np.log(one["px"] / one["eps0"]) - act))))
    for k in meths + ["EPS 完全正確"]:
        ea = one["eps_f12"] if k == "EPS 完全正確" else one["feps"] * np.exp(one[k])
        lpx = np.log(one["px"]) + olr + one["grp"].map(b) * np.log(ea / one["eps0"]).clip(-2, 2)
        pe[k] = float(np.median(np.abs(lpx - np.log(ea) - act)))
    say("\n== 3. 12 個月後本益比的中位 |ln 誤差|（中小型股，距離年報 9.5–12.5 個月的起點，EPS_a＝各種共識）")
    say(pd.DataFrame([pe]).round(4).to_string(index=False))
    sc.assign(表="EPS").to_csv(os.path.join(RES, "eps_correction_small_scores.csv"), index=False, float_format="%.6f")
    pd.DataFrame([pe]).assign(表="PE").to_csv(os.path.join(RES, "eps_correction_small_scores.csv"), mode="a", index=False, float_format="%.6f")
    open(os.path.join(RES, "eps_correction_small.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
