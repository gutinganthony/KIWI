#!/usr/bin/env python3
"""共識校正模型：用當時看得到的線索，修正分析師共識（I/B/E/S FY1）對「實際 GAAP 本財年 EPS」的偏差（README §19.1）。

    python3 lab_eps_correction.py --cache <lab_orbit.py 的暫存目錄>     # 會訓練樹模型（約 1–2 分鐘）：不要和其他訓練程式同時跑

目標：t ＝ ln(實際 GAAP 本財年 EPS ÷ 那個月的 FY1 共識)（兩者都 > 0 的列）。正＝共識太低、負＝共識太高。
訓練列：每個公司月（距離年報 0.5～12 個月，FY1 對得上的月份），約 4–5 萬列；評分列：和 README §18 相同的乾淨起點
  （年報在 10.5～12 個月後、上一份年報在當月 14 號以前、起點前後沒有分割），所以結果能直接和 §18 比。
線索（都在當月看得到）：
  共識隱含成長 ln(共識 ÷ 今天 EPS)、距離年報的月數、共識修正（1／3／6 個月，同一個財年，÷ 股價）、
  這家公司過去的偏差（報告日 ≤ 當月的年度，lead≈11 個月時的 ln(實際 ÷ 共識) 中位數）、長期成長預估 LTG（fgr5yrLag）、
  我們自己的 EPS 成長預測（lab_orbit.py 的樹模型代理 e12）和共識的差距、應計項目、營收成長、利潤率、股價動能、波動、市值、本益比、產業。
比較（走動式：每年 1 月只用報告日在前一年底以前的列訓練）：
  原樣（不修正）、公司過去偏差（§18 的「共識校正」）、線性（Huber，含截距）、樹模型（絕對誤差）、樹模型＋過去偏差兩者平均
另外逐一檢查每個線索的方向是否符合文獻（單變數五分位）：修正動能（分析師反應不足）＋、LTG（過度樂觀）－、應計（Sloan）－、
  價格動能（分析師慢半拍）＋、過去偏差（口徑與習慣持續）＋、我們的預測和共識的差距＋。
輸出：results/eps_correction.txt、eps_correction_scores.csv、eps_correction_logic.csv、eps_correction_rows.csv.gz（評分列的修正係數，給整合用）
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab_orbit_consensus as LC                         # noqa: E402
from pef import consensus, orbit                         # noqa: E402
from pef.stats import huber_ols                          # noqa: E402

RES = os.path.join(HERE, "results")
DATA = os.path.join(HERE, "data")
GNAME = LC.GNAME
GBM = dict(loss="absolute_error", learning_rate=0.05, max_iter=300, max_leaf_nodes=15, min_samples_leaf=200,
           l2_regularization=1.0, random_state=0)
FEATS = ["cons_g", "lead", "rev1", "rev3", "rev6", "past_bias", "n_past", "ltg", "gap_model", "e12", "acc", "g_rev", "m_ttm",
         "ret6", "ret12", "sigma", "ln_mc", "ln_pe", "lev", "sector_id", "loss0"]
LIN = ["cons_g", "lead", "rev3", "rev6", "past_bias", "ltg", "gap_model", "acc", "ret12"]
# 正式使用時今天拿得到的線索（Yahoo 共識 d30／d90 → rev1、rev3；OSAP 到 2024 的過去偏差與 LTG；now_all 的公司特徵）
FEATS_NOW = ["cons_g", "lead", "rev1", "rev3", "past_bias", "n_past", "ltg", "g_rev", "ret12", "vol36", "ln_mc", "ln_pe", "grp_id", "loss0"]
GRP_ID = {"cyclical": 0, "growth": 1, "tech_other": 2, "other": 3}
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def build(cache):
    x = pd.read_pickle(os.path.join(cache, "orbit_x2.pkl"))
    x = x[x["month"] >= "2010-01-01"].copy()
    if "grp" not in x:                                                  # lab_orbit.prepare() 已經算過
        x["grp"] = x["sector"].map(orbit.GROUPS).fillna("other")
    fe = pd.read_csv(os.path.join(DATA, "osap", "feps_sp500.csv.gz"))
    fe["month"] = pd.to_datetime(fe["yyyymm"].astype(int).astype(str) + "01")
    qs = pd.read_csv(os.path.join(DATA, "quarters_sp500.csv"), parse_dates=["period_end"])[["ticker", "period_end", "split_fac"]]
    qs = qs.rename(columns={"period_end": "me"}).sort_values("me")
    fe["me"] = fe["month"] + pd.offsets.MonthEnd(0)
    fe = pd.merge_asof(fe.sort_values("me"), qs, on="me", by="ticker", direction="backward")
    fe["split_fac"] = fe["split_fac"].fillna(fe["ticker"].map(qs.groupby("ticker")["split_fac"].first()))
    fe["feps"] = fe["feps_raw"] / fe["split_fac"]                       # 面板股數口徑（同 lab_orbit_consensus.py）
    fe = fe[fe["feps"].notna()][["ticker", "month", "feps", "fgr5y"]]
    d = x.merge(fe, on=["ticker", "month"], how="inner")

    # 會計年度：FY1 結束日、年報日、上一份年報日
    q = pd.read_csv(os.path.join(DATA, "quarters_sp500.csv"), parse_dates=["period_end", "avail"])
    cache_y = os.path.join(HERE, ".cache", "yahoo")
    meta, splits = [], {}
    sq = qs.sort_values(["ticker", "me"]).copy()
    sq["chg"] = sq.groupby("ticker")["split_fac"].diff().fillna(0) != 0
    for t, e in sq[sq["chg"]].groupby("ticker")["me"]:
        splits[t] = list(e)
    for t, g in d.groupby("ticker"):
        mth = consensus.fy_month(t, cache_y, max_age_h=24 * 90)
        if mth is None:
            continue
        fy = LC.fy_report_dates(q[q["ticker"] == t], mth)
        for r in g.itertuples():
            me = r.month + pd.offsets.MonthEnd(0)
            fut, prev = fy[fy["report"] > me], fy[fy["report"] <= me]
            if fut.empty:
                continue
            meta.append((r.Index, fut.iloc[0]["fy_end"], fut.iloc[0]["report"], prev["report"].iloc[-1] if len(prev) else pd.NaT))
    m = pd.DataFrame(meta, columns=["idx", "fy1", "report", "prev_report"]).set_index("idx")
    d = d.join(m, how="inner")
    d["lead"] = (d["report"] - (d["month"] + pd.offsets.MonthEnd(0))).dt.days / 30.44
    ok = d["prev_report"].isna() | ~((d["prev_report"] > d["month"] + pd.Timedelta(days=13)) &
                                     (d["prev_report"] <= d["month"] + pd.offsets.MonthEnd(0)))
    d = d[ok & (d["lead"] > 0.5) & (d["lead"] <= 12.0)].copy()

    # 實際本財年 EPS＝年報公布那個月的「最近四季」EPS（面板口徑）
    ep = x[["ticker", "month", "eps0"]].rename(columns={"month": "rm", "eps0": "actual"})
    d["rm"] = d["report"].dt.to_period("M").dt.to_timestamp()
    d = d.merge(ep, on=["ticker", "rm"], how="left")
    # 起點到年報之間有分割：共識與實際的口徑可能錯位 → 不用
    d["near_split"] = [any(mo - pd.DateOffset(months=4) < e <= rp + pd.DateOffset(months=1) for e in splits.get(t, []))
                       for t, mo, rp in zip(d["ticker"], d["month"], d["report"])]

    # 線索
    d = d.sort_values(["ticker", "month"]).reset_index(drop=True)
    d["cons_g"] = np.where((d["eps0"] > 0) & (d["feps"] > 0), np.log(d["feps"] / d["eps0"]), np.nan)
    d["cons_g"] = d["cons_g"].clip(-2, 2)
    d["loss0"] = (d["eps0"] <= 0).astype(float)
    for k in (1, 3, 6):
        prev_f = d.groupby("ticker")["feps"].shift(k)
        same = d.groupby("ticker")["fy1"].shift(k) == d["fy1"]
        lagm = d.groupby("ticker")["month"].shift(k)
        same &= (d["month"] - lagm).dt.days.between(28 * k, 32 * k)
        d[f"rev{k}"] = np.where(same, (d["feps"] - prev_f) / d["px"], np.nan)
        d[f"rev{k}"] = d[f"rev{k}"].clip(-0.2, 0.2)
    d["ltg"] = (d["fgr5y"] / 100).clip(-0.5, 1.0)
    d["gap_model"] = (d["e12"] - d["cons_g"]).clip(-2, 2)
    d["grp_id"] = d["grp"].map(GRP_ID).astype(float)
    d["tgt"] = np.where((d["actual"] > 0) & (d["feps"] > 0), np.log(d["actual"] / d["feps"]), np.nan)
    d["tgt"] = d["tgt"].clip(-1.5, 1.5)

    # 這家公司過去的偏差（lead≈11 個月、報告日 ≤ 當月）
    base = d[(d["lead"] > 10.5) & (d["lead"] <= 12.0) & d["tgt"].notna() & ~d["near_split"]][["ticker", "report", "tgt"]]
    pb, npb = [], []
    by = {t: g.sort_values("report") for t, g in base.groupby("ticker")}
    for t, mo in zip(d["ticker"], d["month"]):
        g = by.get(t)
        past = g[g["report"] <= mo]["tgt"] if g is not None else pd.Series(dtype=float)
        pb.append(float(np.median(past)) if len(past) >= 2 else np.nan)
        npb.append(len(past))
    d["past_bias"], d["n_past"] = pb, npb
    return d


def logic_checks(d):
    """每個線索的五分位 → 目標中位數（2015 以後；分 2015–2021、2022 以後兩段看方向是否一致）。"""
    rows = []
    expect = {"rev3": "+", "rev6": "+", "ltg": "−", "acc": "−", "ret12": "+", "past_bias": "+", "gap_model": "+", "cons_g": "−",
              "lead": "（距離越遠、誤差越大）"}
    z = d[d["tgt"].notna() & (d["month"] >= "2015-01-01") & ~d["near_split"]]
    for f, exp in expect.items():
        for per, (lo, hi) in (("2015–2021", ("2015-01-01", "2021-12-31")), ("2022 以後", ("2022-01-01", "2026-12-31"))):
            zz = z[(z["month"] >= lo) & (z["month"] <= hi) & z[f].notna()]
            if len(zz) < 500:
                continue
            qn = pd.qcut(zz[f].rank(method="first"), 5, labels=False)
            med = zz.groupby(qn)["tgt"].median()
            mad = zz.groupby(qn)["tgt"].apply(lambda v: np.median(np.abs(v)))
            r = dict(線索=f, 預期方向=exp, 期間=per, n=len(zz), Q1=med.iloc[0], Q2=med.iloc[1], Q3=med.iloc[2], Q4=med.iloc[3], Q5=med.iloc[4],
                     Q5減Q1=med.iloc[4] - med.iloc[0], spearman=float(zz[f].corr(zz["tgt"], method="spearman")))
            if f == "lead":
                r.update(Q1=mad.iloc[0], Q2=mad.iloc[1], Q3=mad.iloc[2], Q4=mad.iloc[3], Q5=mad.iloc[4], Q5減Q1=mad.iloc[4] - mad.iloc[0])
            rows.append(r)
    return pd.DataFrame(rows)


def walk(d):
    preds = {k: pd.Series(np.nan, index=d.index) for k in ("lin", "gbm", "gbm_now")}
    coefs = []
    for Y in range(2015, 2025):
        cut = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        tr = d[(d["report"] <= cut) & d["tgt"].notna() & ~d["near_split"]]
        te = d[(d["month"] > cut) & (d["month"] <= cut + pd.DateOffset(months=12))]
        if len(tr) < 3000 or te.empty:
            continue
        Xl = np.column_stack([np.ones(len(tr))] + [tr[c].fillna(0).to_numpy(float) for c in LIN])
        b = huber_ols(Xl, tr["tgt"].to_numpy(float))
        coefs.append(dict(年=Y, **{"截距": b[0]}, **{c: b[i + 1] for i, c in enumerate(LIN)}))
        Xt = np.column_stack([np.ones(len(te))] + [te[c].fillna(0).to_numpy(float) for c in LIN])
        preds["lin"].loc[te.index] = Xt @ b
        X = tr[FEATS].to_numpy(float)
        X[~np.isfinite(X)] = np.nan
        mdl = HistGradientBoostingRegressor(**GBM).fit(X, tr["tgt"].to_numpy(float))
        Xt = te[FEATS].to_numpy(float)
        Xt[~np.isfinite(Xt)] = np.nan
        preds["gbm"].loc[te.index] = mdl.predict(Xt)
        X = tr[FEATS_NOW].to_numpy(float)
        X[~np.isfinite(X)] = np.nan
        mdl = HistGradientBoostingRegressor(**GBM).fit(X, tr["tgt"].to_numpy(float))
        Xt = te[FEATS_NOW].to_numpy(float)
        Xt[~np.isfinite(Xt)] = np.nan
        preds["gbm_now"].loc[te.index] = mdl.predict(Xt)
    return preds, pd.DataFrame(coefs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    d = build(a.cache)
    say(f"公司月：{len(d):,}（{d['ticker'].nunique()} 家，{d['month'].min():%Y-%m}～{d['month'].max():%Y-%m}）；有目標值 {int(d['tgt'].notna().sum()):,}")
    say(f"共識比實際高（ln(實際÷共識) 的中位）：{np.median(d['tgt'].dropna()):+.3f}；平均 {np.mean(d['tgt'].dropna()):+.3f}")

    lg = logic_checks(d)
    say("\n== 1. 邏輯檢查：每個線索五分位（Q1＝最低）的 ln(實際 ÷ 共識) 中位數；+＝實際比共識高。lead 那一列是 |誤差| 中位數")
    say(lg.round(3).to_string(index=False))

    preds, coefs = walk(d)
    d["p_lin"], d["p_gbm"], d["p_now"] = preds["lin"], preds["gbm"], preds["gbm_now"]
    d["p_past"] = d["past_bias"]
    d["p_mix"] = np.where(d["past_bias"].notna(), (d["p_gbm"] + d["past_bias"]) / 2, d["p_gbm"])
    say("\n== 2. 線性模型係數（每年 1 月重估；ln(實際÷共識) ~ 截距＋線索；最後一年）")
    say(coefs.tail(3).round(3).to_string(index=False))

    # 3. 評分：全部月份（依距離年報）＋ §18 的乾淨起點（EPS 誤差與本益比誤差）
    ev = d[(d["month"] >= "2015-01-01") & d["tgt"].notna() & ~d["near_split"] & d["p_gbm"].notna()].copy()
    meths = {"原樣": 0.0, "過去偏差": ev["p_past"].fillna(0), "線性": ev["p_lin"], "樹模型": ev["p_gbm"], "樹＋過去偏差": ev["p_mix"],
             "樹（今天的線索）": ev["p_now"]}
    rows = []
    ev["lead_b"] = pd.cut(ev["lead"], [0.5, 3, 6, 9, 12], labels=["0.5–3", "3–6", "6–9", "9–12"])
    for lb, g in [("全部", ev)] + [(f"距離年報 {k} 個月", g) for k, g in ev.groupby("lead_b", observed=True)]:
        r = dict(樣本=lb, n=len(g))
        for nm, p in meths.items():
            pp = p if np.isscalar(p) else p.loc[g.index]
            r[nm] = float(np.median(np.abs(g["tgt"] - pp)))
        rows.append(r)
    sc = pd.DataFrame(rows)
    say("\n== 3. EPS 誤差：中位 |ln(實際 ÷ 修正後的共識)|（2015 以後，走動式樣本外）")
    say(sc.round(4).to_string(index=False))

    # §18 的評分起點：本益比誤差
    one = ev[(ev["lead"] > 10.5) & (ev["lead"] <= 12.0) & (ev["eps0"] > 0) & ev["y12"].notna()].copy()
    beta = pd.read_csv(os.path.join(RES, "orbit_beta.csv"))
    bt = beta[beta["方法"] == "原始成長a"].set_index(["h", "年", "組別"])["b0"]
    one["b"] = [bt.get((12, mo.year, GNAME[g]), np.nan) for mo, g in zip(one["month"], one["grp"])]
    one = one[one["b"].notna() & (one["eps_f12"] > 0)]
    act_lpe = np.log(one["px"]) + one["y12"] + one["orbit_lr"] - np.log(one["eps_f12"])
    def pe_err(ea):
        lpx = np.log(one["px"]) + one["orbit_lr"] + one["b"] * np.log(ea / one["eps0"]).clip(-2, 2)
        return lpx - np.log(ea) - act_lpe
    out = []
    one["tech"] = one["grp"] != "other"
    for per, (lo, hi) in (("2015–2021", ("2015-01-01", "2021-12-31")), ("2022 以後", ("2022-01-01", "2026-12-31")), ("全期", ("2015-01-01", "2026-12-31"))):
        for gn, gm in (("全部", None), ("科技", "tech")):
            g = one[(one["month"] >= lo) & (one["month"] <= hi)]
            if gm:
                g = g[g["tech"]]
            r = dict(期間=per, 群組=gn, n=len(g), 本益比不變=float(np.median(np.abs(np.log(g["px"] / g["eps0"]) - act_lpe.loc[g.index]))))
            for nm in ("原樣", "過去偏差", "線性", "樹模型", "樹＋過去偏差", "樹（今天的線索）"):
                p = 0.0 if nm == "原樣" else {"過去偏差": g["p_past"].fillna(0), "線性": g["p_lin"], "樹模型": g["p_gbm"], "樹＋過去偏差": g["p_mix"],
                                             "樹（今天的線索）": g["p_now"]}[nm]
                ea = g["feps"] * np.exp(p)
                r[nm] = float(np.median(np.abs(pe_err(ea).loc[g.index])))
                r[nm + "_EPS"] = float(np.median(np.abs(np.log(ea / g["eps_f12"]))))
            r["EPS完全正確"] = float(np.median(np.abs(pe_err(g["eps_f12"]).loc[g.index])))
            out.append(r)
    pe = pd.DataFrame(out)
    say("\n== 4. 12 個月後本益比的中位 |ln 誤差|（§18 的乾淨起點；EPS_a＝修正後的共識）；_EPS＝那一種共識對 12 個月後 GAAP EPS 的誤差")
    say(pe[["期間", "群組", "n", "本益比不變", "原樣", "過去偏差", "線性", "樹模型", "樹＋過去偏差", "樹（今天的線索）", "EPS完全正確"]].round(4).to_string(index=False))
    say(pe[["期間", "群組", "原樣_EPS", "過去偏差_EPS", "線性_EPS", "樹模型_EPS", "樹＋過去偏差_EPS", "樹（今天的線索）_EPS"]].round(4).to_string(index=False))

    # 5. 逐年（穩定性）：樹＋過去偏差 vs 過去偏差 vs 原樣（本益比誤差）
    yr = []
    for Y, g in one.groupby(one["month"].dt.year):
        r = dict(年=Y, n=len(g))
        for nm, p in (("原樣", 0.0), ("過去偏差", g["p_past"].fillna(0)), ("樹模型", g["p_gbm"]), ("樹（今天的線索）", g["p_now"])):
            r[nm] = float(np.median(np.abs(pe_err(g["feps"] * np.exp(p)).loc[g.index])))
        yr.append(r)
    say("\n== 5. 逐年本益比誤差")
    say(pd.DataFrame(yr).round(4).to_string(index=False))

    lg.to_csv(os.path.join(RES, "eps_correction_logic.csv"), index=False, float_format="%.6f")
    pd.concat([sc.assign(表="EPS"), pe.assign(表="PE")]).to_csv(os.path.join(RES, "eps_correction_scores.csv"), index=False, float_format="%.6f")
    one[["ticker", "month", "grp", "feps", "eps0", "eps_f12", "p_past", "p_lin", "p_gbm", "p_mix", "p_now"]].to_csv(
        os.path.join(RES, "eps_correction_rows.csv.gz"), index=False, float_format="%.6g", compression={"method": "gzip", "mtime": 0})
    open(os.path.join(RES, "eps_correction.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
