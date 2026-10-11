#!/usr/bin/env python3
"""股價偏離軌道的部分能不能事先知道？產業重新定價與利率（升降息預期）因子的走動式檢驗（README §19.2–19.3）。

    python3 lab_orbit_factors.py --cache <lab_orbit.py 的暫存目錄>      # 只有 Huber／OLS，不訓練樹模型（約 1 分鐘）

基準：lab_orbit.py 的「原始成長a」（12 個月；y12 ~ β × ln(EPS_12 ÷ EPS_0)，EPS 完全正確）。每個候選因子都「加進同一條迴歸」重估、
每年 1 月只用答案已揭曉的資料（目標日 ≤ 前一年底），比樣本外誤差有沒有變小。兩種誤差：
  總誤差＝中位 |預測 − y12|；橫斷面誤差＝先把每個月的中位數扣掉（只看「同一個月裡誰比誰多漲」）。
一、橫斷面（產業與股票；β 依公司類型各估，同月份去平均）
  產業估值偏離：產業本益比中位數 − 該產業過去 60 個月的中位（扣掉當月全市場的同一個值）——預期 −（貴的產業回歸）
  產業動能：產業過去 12 個月報酬中位數（扣掉當月全市場）——文獻（Moskowitz-Grinblatt 1999）預期 ＋
  產業共識修正：產業內 3 個月 FY1 共識修正 ÷ 股價 的中位數（I/B/E/S，到 2024-11）——預期 ＋
  個股動能：過去 12 個月報酬（扣掉當月中位）——預期 ＋
  利率 × 存續期間：個股 ln 本益比（扣掉當月中位）× 預期升降息（2 年期 − 聯邦基金利率）——預期 −（預期降息＝負值時，高本益比的股票多漲）
                   以及 × 期限利差（10 年 − 3 個月）
二、整體市場（時間序列：當月全部股票 y12 的中位數）
  預期升降息、期限利差、過去 12 個月 10 年期殖利率的變化、10 年期實質利率——走動式 OLS，和「預測 0」（軌道本身）比
三、看法的上限（不是預測，是「如果你的利率看法完全正確」）
  市場：y12 中位數 ~ 未來 12 個月 10 年期殖利率的變化；個股：再加上 ln 本益比 × 未來變化（存續期間效果）
輸出：results/orbit_factors.txt、orbit_factors_cs.csv、orbit_factors_mkt.csv
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab_orbit as lo                                   # noqa: E402
from pef.stats import huber_ols                          # noqa: E402

RES = os.path.join(HERE, "results")
DATA = os.path.join(HERE, "data")
GNAME = lo.GNAME
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def demean(d, c):
    return d[c] - d.groupby("month")[c].transform("median")


def build(cache):
    x = pd.read_pickle(os.path.join(cache, "orbit_x2.pkl"))
    x = x[x["month"] >= "2010-01-01"].copy()
    x["g12"] = x["g12"].clip(-2, 2)
    x["lpe"] = np.where(x["eps0"] > 0, np.log(x["px"] / x["eps0"]), np.nan)
    x["sec"] = x["sector"].fillna("other")
    # 產業估值偏離（相對自己過去 60 個月）
    sp = x.groupby(["sec", "month"])["lpe"].median().rename("sec_lpe").reset_index().sort_values(["sec", "month"])
    sp["sec_hist"] = sp.groupby("sec")["sec_lpe"].transform(lambda v: v.shift(1).rolling(60, min_periods=24).median())
    sp["sec_dev"] = sp["sec_lpe"] - sp["sec_hist"]
    # 產業動能
    sm = x.groupby(["sec", "month"])["ret12"].median().rename("sec_mom").reset_index()
    x = x.merge(sp[["sec", "month", "sec_dev"]], on=["sec", "month"], how="left").merge(sm, on=["sec", "month"], how="left")
    # 產業共識修正（I/B/E/S FY1，同一個財年才算）
    fe = pd.read_csv(os.path.join(DATA, "osap", "feps_sp500.csv.gz"))
    fe["month"] = pd.to_datetime(fe["yyyymm"].astype(int).astype(str) + "01")
    fe = fe.sort_values(["ticker", "month"])
    fe["rev3_raw"] = fe.groupby("ticker")["feps_raw"].diff(3)
    lagm = fe.groupby("ticker")["month"].shift(3)
    fe.loc[(fe["month"] - lagm).dt.days > 95, "rev3_raw"] = np.nan
    x = x.merge(fe[["ticker", "month", "rev3_raw"]], on=["ticker", "month"], how="left")
    # rev3_raw 是 I/B/E/S 當時的股數口徑：除以「當時股價」＝面板股價（面板口徑）× 面板的 split_fac
    x["rev3"] = (x["rev3_raw"] / (x["px"] * x["split_fac"])).clip(-0.1, 0.1)
    x.loc[x["rev3"].abs() > 0.05, "rev3"] = np.nan                         # 財年換年或分割月的跳動
    sr = x.groupby(["sec", "month"])["rev3"].median().rename("sec_rev").reset_index()
    x = x.merge(sr, on=["sec", "month"], how="left")
    # 利率
    r = pd.read_csv(os.path.join(DATA, "rates_monthly.csv"), parse_dates=["month_end"])
    r["d10_past12"] = r["DGS10"] - r["DGS10"].shift(12)
    r["d10_fwd12"] = r["DGS10"].shift(-12) - r["DGS10"]
    x["month_end"] = x["month"] + pd.offsets.MonthEnd(0)
    x = x.merge(r[["month_end", "exp_cut_2y", "slope", "DGS10", "DFII10", "d10_past12", "d10_fwd12"]], on="month_end", how="left")
    # 橫斷面因子：扣掉當月中位數
    for c in ("sec_dev", "sec_mom", "sec_rev", "ret12"):
        x[c + "_x"] = demean(x, c).clip(-3, 3)
    x["dur"] = demean(x, "lpe").clip(-2, 2)
    x["dur_cut"] = x["dur"] * x["exp_cut_2y"]
    x["dur_slope"] = x["dur"] * x["slope"]
    x["dur_d10fwd"] = x["dur"] * x["d10_fwd12"]
    return x


CANDS = {"基準（只有 EPS 成長）": [],
         "＋產業估值偏離": ["sec_dev_x"], "＋產業動能": ["sec_mom_x"], "＋產業共識修正": ["sec_rev_x"], "＋個股動能": ["ret12_x"],
         "＋利率×存續期間（預期升降息）": ["dur_cut"], "＋利率×存續期間（期限利差）": ["dur_slope"],
         "＋產業三項": ["sec_dev_x", "sec_mom_x", "sec_rev_x"],
         "＋產業三項＋個股動能＋利率×存續期間": ["sec_dev_x", "sec_mom_x", "sec_rev_x", "ret12_x", "dur_cut"],
         "（上限）＋利率看法完全正確×存續期間": ["dur_d10fwd"]}


def walk_cs(x):
    rows, coefs = [], []
    preds = {k: pd.Series(np.nan, index=x.index) for k in CANDS}
    for Y in range(2015, 2025):
        cut = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        tr = x[lo.tgt_end(x, 12) <= cut]
        te = x[(x["month_end"] > cut) & (x["month_end"] <= cut + pd.DateOffset(months=12))]
        for name, extra in CANDS.items():
            cols = ["g12"] + extra
            for g in GNAME:
                trg = tr[tr["grp"] == g].dropna(subset=["y12"] + cols)
                b = lo.beta_fit(trg, "y12", cols)
                if not np.all(np.isfinite(b)):
                    continue
                t = te[te["grp"] == g]
                ok = t[cols].notna().all(axis=1)
                preds[name].loc[t.index[ok]] = t.loc[ok, cols].to_numpy(float) @ b
                if Y == 2024:
                    coefs.append(dict(候選=name, 組別=GNAME[g], **{c: float(v) for c, v in zip(cols, b)}))
    return preds, pd.DataFrame(coefs)


def score_cs(x, preds):
    out = []
    need = [n for n in CANDS if not n.startswith("（上限）")]
    ok = pd.concat([preds[n].notna() for n in need], axis=1).all(axis=1) & x["y12"].notna()
    z = x[ok & (x["month"] >= "2015-01-01")].copy()
    ym = z.groupby("month")["y12"].transform("median")
    for per, (lo_, hi) in (("2015–2021", ("2015-01-01", "2021-12-31")), ("2022 以後", ("2022-01-01", "2026-12-31")),
                           ("全期", ("2015-01-01", "2026-12-31"))):
        for gn, gm in (("全部", None), ("科技", "tech")):
            m = (z["month"] >= lo_) & (z["month"] <= hi)
            if gm:
                m &= z["grp"] != "other"
            zz = z[m]
            r = dict(期間=per, 群組=gn, n=len(zz))
            for n in CANDS:
                p = preds[n].loc[zz.index]
                if p.isna().mean() > 0.05:
                    continue
                pm = p.groupby(zz["month"]).transform("median")
                r[n + "｜總"] = float(np.nanmedian(np.abs(p - zz["y12"])))
                r[n + "｜橫斷面"] = float(np.nanmedian(np.abs((p - pm) - (zz["y12"] - ym.loc[zz.index]))))
            out.append(r)
    return pd.DataFrame(out)


def market(x):
    """整體市場：當月全部股票 y12 中位數 ~ 利率線索（走動式 OLS）。"""
    mk = x[x["y12"].notna()].groupby("month").agg(M=("y12", "median"), exp_cut_2y=("exp_cut_2y", "first"), slope=("slope", "first"),
                                                 d10_past12=("d10_past12", "first"), DFII10=("DFII10", "first"),
                                                 d10_fwd12=("d10_fwd12", "first"), n=("y12", "size")).reset_index()
    mk = mk[mk["month"] >= "2012-01-01"]
    say("\n== 三a. 整體市場：每月全部股票「股價偏離軌道」(y12) 的中位數，和利率線索的相關（2012 起，月資料、12 個月重疊）")
    for c in ("exp_cut_2y", "slope", "d10_past12", "DFII10", "d10_fwd12"):
        say(f"   {c:<11} 相關 {mk['M'].corr(mk[c]):+.3f}（n={int(mk[c].notna().sum())}）")
    rows = []
    specs = {"預測 0（軌道本身）": [], "＋預期升降息": ["exp_cut_2y"], "＋期限利差": ["slope"], "＋過去 12 個月 10 年期變化": ["d10_past12"],
             "＋實質利率": ["DFII10"], "＋預期升降息＋期限利差": ["exp_cut_2y", "slope"], "（上限）＋未來 12 個月 10 年期變化": ["d10_fwd12"]}
    pred = {k: pd.Series(np.nan, index=mk.index) for k in specs}
    coef = {}
    for Y in range(2015, 2025):
        cut = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        tr = mk[(mk["month"] + pd.DateOffset(months=12) + pd.offsets.MonthEnd(0)) <= cut]
        te = mk[(mk["month"] > cut - pd.offsets.MonthBegin(1)) & (mk["month"] <= cut + pd.DateOffset(months=12)) & (mk["month"].dt.year == Y)]
        for k, cols in specs.items():
            if not cols:
                pred[k].loc[te.index] = 0.0
                continue
            trr = tr.dropna(subset=cols + ["M"])
            X = np.column_stack([np.ones(len(trr))] + [trr[c] for c in cols])
            b = np.linalg.lstsq(X, trr["M"].to_numpy(float), rcond=None)[0]
            tee = te.dropna(subset=cols)
            pred[k].loc[tee.index] = np.column_stack([np.ones(len(tee))] + [tee[c] for c in cols]) @ b
            if Y == 2024:
                coef[k] = b
    for per, (lo_, hi) in (("2015–2021", ("2015-01-01", "2021-12-31")), ("2022 以後", ("2022-01-01", "2026-12-31")),
                           ("全期", ("2015-01-01", "2026-12-31"))):
        mm = mk[(mk["month"] >= lo_) & (mk["month"] <= hi)]
        r = dict(期間=per, 月數=len(mm))
        for k in specs:
            p = pred[k].loc[mm.index]
            r[k] = float(np.nanmedian(np.abs(mm["M"] - p)))
        rows.append(r)
    t = pd.DataFrame(rows)
    say("\n== 三b. 整體市場的走動式樣本外：中位 |實際偏離 − 預測|（越小越好；「預測 0」＝相信軌道）")
    say(t.round(4).to_string(index=False))
    say("   2024 年 1 月版的係數（截距、斜率…）：" + "；".join(f"{k} {np.round(v, 3).tolist()}" for k, v in coef.items()))
    return t, mk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    x = build(a.cache)
    z = x[(x["month"] >= "2015-01-01") & x["y12"].notna()]
    say(f"樣本：{z['ticker'].nunique()} 家、{len(z):,} 個公司月（起點 2015-01～{z['month'].max():%Y-%m}，12 個月）")
    say("\n== 一a. 單變數：每個因子五分位（Q1＝最低）的「扣掉當月中位後的 y12」中位數（2015 以後）")
    rows = []
    z = z.assign(yx=demean(z, "y12"))
    for c, exp in (("sec_dev_x", "−"), ("sec_mom_x", "＋"), ("sec_rev_x", "＋"), ("ret12_x", "＋"), ("dur_cut", "−"), ("dur_slope", "?"),
                   ("dur_d10fwd", "−（上限）")):
        for per, (lo_, hi) in (("2015–2021", ("2015-01-01", "2021-12-31")), ("2022 以後", ("2022-01-01", "2026-12-31"))):
            zz = z[(z["month"] >= lo_) & (z["month"] <= hi) & z[c].notna()]
            if len(zz) < 1000:
                continue
            qn = pd.qcut(zz[c].rank(method="first"), 5, labels=False)
            med = zz.groupby(qn)["yx"].median()
            rows.append(dict(因子=c, 預期=exp, 期間=per, n=len(zz), Q1=med.iloc[0], Q3=med.iloc[2], Q5=med.iloc[4], Q5減Q1=med.iloc[4] - med.iloc[0],
                             spearman=float(zz[c].corr(zz["yx"], method="spearman"))))
    uni = pd.DataFrame(rows)
    say(uni.round(3).to_string(index=False))

    preds, coefs = walk_cs(x)
    sc = score_cs(x, preds)
    say("\n== 一b. 走動式樣本外（12 個月，EPS 完全正確）：中位 |誤差|。｜總＝含大盤；｜橫斷面＝扣掉每月中位後")
    cols = ["期間", "群組", "n"] + [c for c in sc.columns if c.endswith("｜橫斷面")]
    say(sc[cols].round(4).to_string(index=False))
    cols = ["期間", "群組"] + [c for c in sc.columns if c.endswith("｜總")]
    say(sc[cols].round(4).to_string(index=False))
    say("\n== 一c. 2024 年 1 月版的係數（g12＝EPS 成長；其他依候選）")
    say(coefs[coefs["候選"].isin(["＋產業三項＋個股動能＋利率×存續期間", "（上限）＋利率看法完全正確×存續期間"])].round(4).to_string(index=False))

    mt, mk = market(x)

    # 三c. 利率看法完全正確時，市場層級的敏感度（給「利率看法」參數用）
    mm = mk.dropna(subset=["d10_fwd12"])
    b = np.polyfit(mm["d10_fwd12"], mm["M"], 1)
    say(f"\n== 三c. 市場層級：y12 中位數 ≈ {b[1]:+.3f} {b[0]:+.3f} × 未來 12 個月 10 年期殖利率變化（百分點）；相關 {mm['M'].corr(mm['d10_fwd12']):+.3f}，n={len(mm)}")
    for per, (lo_, hi) in (("2012–2021", ("2012-01-01", "2021-12-31")), ("2022 以後", ("2022-01-01", "2026-12-31"))):
        q = mm[(mm["month"] >= lo_) & (mm["month"] <= hi)]
        bb = np.polyfit(q["d10_fwd12"], q["M"], 1)
        say(f"   {per}：斜率 {bb[0]:+.3f}（每升 1 個百分點，股價相對軌道 {np.exp(bb[0]) - 1:+.1%}），相關 {q['M'].corr(q['d10_fwd12']):+.3f}，n={len(q)}")

    sc.to_csv(os.path.join(RES, "orbit_factors_cs.csv"), index=False, float_format="%.6f")
    mt.to_csv(os.path.join(RES, "orbit_factors_mkt.csv"), index=False, float_format="%.6f")
    uni.to_csv(os.path.join(RES, "orbit_factors_uni.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "orbit_factors.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
