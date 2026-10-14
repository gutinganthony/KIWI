#!/usr/bin/env python3
"""README §23.2：回測三條使用建議中的前兩條（第三條台積電月營收見 research/tsmc_monthly_revenue.py）

    python3 research/usage_backtest.py --cache <lab_orbit.py 的暫存目錄> --build <lab_eps_correction.py 的 L.build pickle> > results/usage_backtest.txt

資料：I/B/E/S 本財年（FY1）共識（OSAP FEPS，每月一個值）＋ lab_orbit 面板（S&P 500，2015 起點起；β＝走動式「原始成長a」，起點那一年 1 月的版本）。

一、「用 12 個月、每月更新」
  目標日 T ＝ 年報公布的下一個月（那時「最近四季 EPS」剛好就是這個財年）；實際本益比 ＝ T 的股價 ÷ T 的最近四季 GAAP EPS。
  在 T 之前 L 個月（L＝2～12）各做一次預估：EPS ＝ 當月的 FY1 共識，股價 ＝ 當月股價 × exp(軌道 × L/12 ＋ β_L × ln(共識 ÷ 當月 EPS))；
  β_L 在 6、12 個月之間線性內插（0～6 個月：β_6 × L/6）。24 個月：T 之前 24 個月，用上一個財年的 FY1 外推一年（× 隱含成長，正式版）或不外推。
  同一批目標日、每個 L 都有預估的才比（共同樣本），所以差別只來自「離目標日多遠、資料多新」。
  另外：6 個月前預估、但共識用 s 個月前的（s＝0、1、2、3、5）——單看「EPS 輸入不更新」的代價。
二、「景氣循環股在谷底或高峰時填三個 EPS 情境、看區間」
  12 個月（距離年報 10.5–12 個月的起點，§18 同樣本）與 6 個月（距離年報 4.5–6 個月）。
  景氣循環＝半導體／設備／記憶體＋能源＋原物料；谷底／高峰＝今天 EPS 比自己過去 5 年中位數低 40% 以上 ／ 高 50% 以上（ln < −0.51 ／ > +0.41）。
  基準情境＝共識 × 正式版校正係數（走動式重訓）；區間＝正式版 80% 價格區間（分位數 × 波動^0.7 × exp(δ × min(|ln(EPS ÷ 今天 EPS)|, 2))；分位數走動式：只用目標日在起點那年以前的誤差校準），
  本益比區間 ＝ 價格區間 ÷ 情境 EPS。比較：只填共識一個情境 vs 三個情境（悲觀／基準／樂觀）取聯集，
  情境寬度：±20%、±40%、「經驗」（同類公司過去「實際 ÷ 共識」的 10% 和 90% 分位，只用已揭曉的年度）。
  評分：實際本益比落在區間內的比例（目標 80%）、區間寬度（高 ÷ 低）、區間分數（越低越好；寬度＋落在外面的懲罰）。
輸出：results/usage_backtest.txt、usage_update_curve.csv、usage_scenarios.csv
"""
import argparse
import io
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from pef import cond                                     # noqa: E402

RES = os.path.join(HERE, "results")
GNAME = {"cyclical": "半導體／設備／記憶體", "growth": "軟體／網路", "tech_other": "其他科技", "other": "非科技"}
A = 0.2
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def iscore(y, lo, hi):
    return (hi - lo) + (2 / A) * np.maximum(lo - y, 0) + (2 / A) * np.maximum(y - hi, 0)


def betas():
    b = pd.read_csv(os.path.join(RES, "orbit_beta.csv"))
    return b[b["方法"] == "原始成長a"].set_index(["h", "年", "組別"])["b0"].to_dict()


def beta_l(bt, L, year, grp):
    g = GNAME[grp]
    b6, b12, b24 = (bt.get((h, year, g), np.nan) for h in (6, 12, 24))
    if L <= 6:
        return b6 * L / 6
    if L <= 12:
        return b6 + (b12 - b6) * (L - 6) / 6
    return b24


def correction_wf(b):
    """正式版共識校正的走動式版本：每年 1 月只用報告日在前一年底以前的列訓練樹（lab_eps_correction2.walk，正式版線索），
    截在 −1～+0.7，再套同時點護欄（過去偏差 ± 過去 |偏差|，≥ 4 個年度才套；和 pef/eps_correct.guard 同規則）。回傳 ln 校正值。"""
    import lab_eps_correction as L                       # noqa: E402
    import lab_eps_correction2 as L2                     # noqa: E402
    d = L2.add_lead_bias(b)
    p = L2.walk(d, L.FEATS_NOW).clip(-1.0, 0.7)
    has = d["pb_lead"].notna() & (d["pb_lead_n"] >= 4)
    return pd.Series(np.where(has, np.clip(p, d["pb_lead"] - d["pb_abs"], d["pb_lead"] + d["pb_abs"]), p), index=b.index)


def update_curve(b, x, bt):
    """一、同一個目標日，越接近時預估（每月更新）誤差掉多少。"""
    px = x.drop_duplicates(["ticker", "month"]).set_index(["ticker", "month"])[["px", "eps0"]]
    b = b[~b["near_split"]].copy()
    b["T"] = (b["report"].dt.to_period("M") + 1).dt.to_timestamp()
    tg = b.drop_duplicates(["ticker", "report"])[["ticker", "report", "T", "grp"]]
    tg = tg.join(px, on=["ticker", "T"]).rename(columns={"px": "pT", "eps0": "eT"})
    tg = tg[(tg["eT"] > 0) & tg["pT"].notna() & (tg["T"] >= "2016-01-01")]
    rows = []
    look = b.set_index(["ticker", "report", "month"])
    for L in list(range(2, 13)):
        m = tg.assign(month=tg["T"] - pd.DateOffset(months=L))
        r = m.join(look[["feps", "pk", "eps0", "px", "orbit_lr"]], on=["ticker", "report", "month"], how="inner")
        r = r[(r["eps0"] > 0) & (r["feps"] > 0) & (r["month"] >= "2015-01-01")]
        r["L"] = L
        rows.append(r)
    # 24 個月：上一個財年的 FY1（T 之前 24 個月 ＝ 上一份年報之前約 11 個月）
    rep = b.drop_duplicates(["ticker", "report"]).sort_values(["ticker", "report"])[["ticker", "report"]].copy()
    rep["prev"] = rep.groupby("ticker")["report"].shift(1)
    pr = rep.set_index(["ticker", "report"])["prev"]
    m = tg.assign(prev=pr.reindex(pd.MultiIndex.from_frame(tg[["ticker", "report"]])).to_numpy(), month=tg["T"] - pd.DateOffset(months=24))
    m = m[m["prev"].notna()]
    r = m.join(look[["feps", "pk", "eps0", "px", "orbit_lr"]], on=["ticker", "prev", "month"], how="inner")
    r = r[(r["eps0"] > 0) & (r["feps"] > 0) & (r["month"] >= "2015-01-01")]
    r["L"] = 24
    rows.append(r)
    d = pd.concat(rows, ignore_index=True)
    d["beta"] = [beta_l(bt, L, m_.year, g) for L, m_, g in zip(d["L"], d["month"], d["grp"])]
    d = d[d["beta"].notna()]
    g = (d["feps"] / d["eps0"]).clip(0.7, 1.5)
    d["E"] = np.where(d["L"] == 24, d["feps"] * g, d["feps"])
    d["E_noext"] = d["feps"]
    kk = np.exp(d["pk"].fillna(0.0))
    d["E_k"] = np.where(d["L"] == 24, d["feps"] * kk * g, d["feps"] * kk)
    act = np.log(d["pT"] / d["eT"])

    def err(E):
        lp = np.log(d["px"]) + d["orbit_lr"] * d["L"] / 12 + d["beta"] * np.log(E / d["eps0"]).clip(-2, 2)
        return lp - np.log(E) - act
    d["e"] = err(d["E"])
    d["e_noext"] = err(d["E_noext"])
    d["e_k"] = err(d["E_k"])
    d["e_k_noext"] = err(d["feps"] * kk)
    d["e_eps_k"] = np.log(d["E_k"] / d["eT"])
    d["e_perfect"] = err(d["eT"])
    d["e_unch"] = np.log(d["px"] / d["eps0"]) - act
    d["e_eps"] = np.log(d["E"] / d["eT"])
    key = d.groupby(["ticker", "report"])["L"].apply(set)
    full = key[key.apply(lambda s: set(range(2, 13)) <= s)].index
    d["common"] = pd.MultiIndex.from_frame(d[["ticker", "report"]]).isin(full)
    d["common24"] = d["common"] & pd.MultiIndex.from_frame(d[["ticker", "report"]]).isin(key[key.apply(lambda s: 24 in s)].index)
    return d


def freshness(b, x, bt):
    """一之二：6 個月前預估，共識用 s 個月前的（股價、今天 EPS 都是最新的）。"""
    px = x.drop_duplicates(["ticker", "month"]).set_index(["ticker", "month"])[["px", "eps0"]]
    b = b[~b["near_split"]].copy()
    b["T"] = (b["report"].dt.to_period("M") + 1).dt.to_timestamp()
    look = b.set_index(["ticker", "report", "month"])
    tg = b.drop_duplicates(["ticker", "report"])[["ticker", "report", "T", "grp"]].join(px, on=["ticker", "T"]).rename(columns={"px": "pT", "eps0": "eT"})
    tg = tg[(tg["eT"] > 0) & tg["pT"].notna() & (tg["T"] >= "2016-01-01")]
    m = tg.assign(month=tg["T"] - pd.DateOffset(months=6))
    base = m.join(look[["eps0", "px", "orbit_lr"]], on=["ticker", "report", "month"], how="inner")
    base = base[(base["eps0"] > 0) & (base["month"] >= "2015-01-01")]
    base["beta"] = [beta_l(bt, 6, m_.year, g) for m_, g in zip(base["month"], base["grp"])]
    out = {}
    for s in (0, 1, 2, 3, 5):
        q = base.assign(cm=base["month"] - pd.DateOffset(months=s)).join(look[["feps", "pk"]], on=["ticker", "report", "cm"], how="inner")
        q = q[q["feps"] > 0]
        for tag, E in (("", q["feps"]), ("_k", q["feps"] * np.exp(q["pk"].fillna(0.0)))):
            lp = np.log(q["px"]) + q["orbit_lr"] * 0.5 + q["beta"] * np.log(E / q["eps0"]).clip(-2, 2)
            q["e" + tag] = lp - np.log(E) - np.log(q["pT"] / q["eT"])
            q["e_eps" + tag] = np.log(E / q["eT"])
        out[s] = q.set_index(["ticker", "report"])[["e", "e_eps", "e_k", "e_eps_k"]]
    common = set.intersection(*[set(v.index) for v in out.values()])
    return {s: v.loc[sorted(common)] for s, v in out.items()}, len(common)


def band_q(p, h, alpha, delta):
    """每個起點年份 Y：只用目標日在 Y 年以前的「原始成長a」誤差校準 10%／90% 分位（和 band_epschange.py 同一套正規化）。"""
    z = p[p[f"y{h}"].notna() & p[f"p{h}_原始成長a"].notna()].copy()
    g = np.log(z[f"eps_f{h}"] / z["eps0"]).where((z[f"eps_f{h}"] > 0) & (z["eps0"] > 0)).abs().clip(upper=2)
    vmed = float(z["vol36"].median())
    base = np.clip(z["vol36"].where(np.isfinite(z["vol36"]), vmed), *cond.VOL_CLIP) ** alpha
    u = (z[f"y{h}"] - z[f"p{h}_原始成長a"]) / (base * np.exp(delta * g))
    ok = u.notna()
    out = {}
    for Y in range(2015, 2026):
        m = ok & ((z["month"] + pd.DateOffset(months=h)) < pd.Timestamp(f"{Y}-01-01"))
        if m.sum() < 2000:
            continue                                     # 校準資料不夠的年份不評分（走動式）
        uu = u[m] - u[m].median()
        out[Y] = (float(np.quantile(uu, A / 2)), float(np.quantile(uu, 1 - A / 2)))
    return out, vmed


def scenarios(b, x, bt, p, model, band):
    st = []
    for t, g in x[["ticker", "month", "eps0"]].drop_duplicates(["ticker", "month"]).groupby("ticker"):
        s = g.set_index("month")["eps0"].sort_index().asfreq("MS")
        med = s.where(s > 0).rolling(60, min_periods=36).median()
        st.append(pd.DataFrame({"ticker": t, "month": s.index, "med5": med.to_numpy()}))
    st = pd.concat(st, ignore_index=True)
    cyc_sec = {"semis", "semicap", "memory", "gics_energy", "gics_mat"}
    rows = []
    for h, lo_, hi_ in ((12, 10.5, 12.0), (6, 4.5, 6.0)):
        z = b[(b["lead"] > lo_) & (b["lead"] <= hi_) & (b["month"] >= "2015-01-01") & ~b["near_split"] & (b["eps0"] > 0)
              & (b["feps"] > 0) & (b[f"eps_f{h}"] > 0) & b[f"y{h}"].notna()].merge(st, on=["ticker", "month"], how="left")
        z["beta"] = [bt.get((h, m_.year, GNAME[g]), np.nan) for m_, g in zip(z["month"], z["grp"])]
        z = z[z["beta"].notna()].copy()
        z["cyc"] = z["sector"].isin(cyc_sec)
        r5 = np.log(z["eps0"] / z["med5"])
        z["phase"] = np.select([r5 < np.log(0.6), r5 > np.log(1.5)], ["谷底", "高峰"], "平常")
        z.loc[z["med5"].isna(), "phase"] = "沒有 5 年資料"
        z["cat"] = np.where(z["cyc"], "景氣循環", "其他") + "｜" + z["phase"]
        z["Fk"] = z["feps"] * np.exp(z["pk"].fillna(0.0))              # 基準情境＝共識 × 校正係數（正式版）
        z["miss"] = np.log(z[f"eps_f{h}"] / z["Fk"])                   # 實際 ÷ 基準
        # 經驗情境寬度：同一類（景氣循環／其他 × 谷底高峰／平常）在起點那年以前已揭曉的「實際 ÷ 共識」10%、90% 分位
        z["ext"] = np.where(z["phase"].isin(["谷底", "高峰"]), "極端", "平常")
        z["emp_lo"] = np.nan
        z["emp_hi"] = np.nan
        for Y in range(2015, 2026):
            for cyc in (True, False):
                for ext in ("極端", "平常"):
                    past = z[(z["report"] < pd.Timestamp(f"{Y}-01-01")) & (z["cyc"] == cyc) & (z["ext"] == ext)]["miss"]
                    if len(past) < 30:
                        past = z[(z["report"] < pd.Timestamp(f"{Y}-01-01")) & (z["cyc"] == cyc)]["miss"]
                    if len(past) < 30:
                        past = z[z["report"] < pd.Timestamp(f"{Y}-01-01")]["miss"]
                    if len(past) < 30:
                        continue
                    m = (z["month"].dt.year == Y) & (z["cyc"] == cyc) & (z["ext"] == ext)
                    z.loc[m, "emp_lo"] = np.quantile(past, 0.1)
                    z.loc[m, "emp_hi"] = np.quantile(past, 0.9)
        qy, vmed = band[h]
        z = z[z["month"].dt.year.isin(list(qy))].copy()
        act_lpe = np.log(z["px"]) + z[f"y{h}"] + z["orbit_lr"] * h / 12 - np.log(z[f"eps_f{h}"])
        base = np.clip(z["vol36"].where(np.isfinite(z["vol36"]), vmed), *cond.VOL_CLIP) ** model["alpha"]
        q10 = z["month"].dt.year.map(lambda y: qy[y][0])
        q90 = z["month"].dt.year.map(lambda y: qy[y][1])
        dl = model["band_delta"][str(h)]

        def band_for(E):
            gg = np.log(E / z["eps0"])
            c = np.log(z["px"]) + z["orbit_lr"] * h / 12 + z["beta"] * gg.clip(-2, 2)
            sc = base * np.exp(dl * gg.abs().clip(upper=2))
            return c + q10 * sc - np.log(E), c + q90 * sc - np.log(E)        # ln 本益比區間
        F = z["Fk"]
        variants = {"只填共識×係數（一個情境）": [F], "三情境 ±20%": [F * 0.8, F, F * 1.2], "三情境 ±40%": [F * 0.6, F, F * 1.4],
                    "三情境 經驗寬度": [F * np.exp(z["emp_lo"]), F, F * np.exp(z["emp_hi"])]}
        for vn, Es in variants.items():
            bands = [band_for(E) for E in Es]
            lo = pd.concat([bb[0] for bb in bands], axis=1).min(axis=1, skipna=False)
            hi = pd.concat([bb[1] for bb in bands], axis=1).max(axis=1, skipna=False)
            ok = lo.notna() & hi.notna()
            for cat in ["景氣循環｜谷底", "景氣循環｜高峰", "景氣循環｜平常", "其他｜谷底", "其他｜高峰", "其他｜平常", "全部"]:
                m = ok & ((z["cat"] == cat) if cat != "全部" else True)
                if m.sum() < 15:
                    continue
                y = act_lpe[m]
                rows.append(dict(h=h, 類別=cat, 做法=vn, n=int(m.sum()), 涵蓋=float(((y >= lo[m]) & (y <= hi[m])).mean()),
                                 偏低=float((y < lo[m]).mean()), 偏高=float((y > hi[m]).mean()),
                                 寬度_高除以低=float(np.median(np.exp(hi[m] - lo[m]))), 區間分數=float(np.mean(iscore(y, lo[m], hi[m]))),
                                 共識偏差中位=float(np.median(-z.loc[m, "miss"])), 經驗寬度_低=float(np.nanmedian(np.exp(z.loc[m, "emp_lo"]) - 1)),
                                 經驗寬度_高=float(np.nanmedian(np.exp(z.loc[m, "emp_hi"]) - 1))))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--build", required=True)
    a = ap.parse_args()
    x = pd.read_pickle(os.path.join(a.cache, "orbit_x2.pkl"))
    b = pd.read_pickle(a.build)
    b["pk"] = correction_wf(b)
    bt = betas()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)

    d = update_curve(b, x, bt)
    say("== 一、同一個目標日（年報公布的下一個月），提前 L 個月預估的本益比誤差（共同樣本：L＝2～12 都有預估的目標日）")
    rows = []
    for L, g in d[d["common"]].groupby("L"):
        rows.append(dict(提前月數=L, n=len(g), 中位誤差=float(np.median(np.abs(g["e"]))), 共識校正=float(np.median(np.abs(g["e_k"]))),
                         EPS部分=float(np.median(np.abs(g["e_eps"]))), EPS部分_校正=float(np.median(np.abs(g["e_eps_k"]))),
                         校正_20內=float(np.mean(np.abs(np.exp(g["e_k"]) - 1) <= 0.2)), 偏差_校正=float(np.median(g["e_k"])),
                         在20內=float(np.mean(np.abs(np.exp(g["e"]) - 1) <= 0.2)), EPS猜對=float(np.median(np.abs(g["e_perfect"]))),
                         本益比不變=float(np.median(np.abs(g["e_unch"]))), 偏差中位=float(np.median(g["e"]))))
    c = pd.DataFrame(rows)
    say(f"目標日 {d.loc[d['common'], ['ticker', 'report']].drop_duplicates().shape[0]:,} 個（{d.loc[d['common'], 'ticker'].nunique()} 家；目標日 2016-01～{d['T'].max():%Y-%m}）")
    say(c.round(3).to_string(index=False))
    c24 = []
    for L, g in d[d["common24"] & d["L"].isin([24, 12, 6, 3])].groupby("L"):
        c24.append(dict(提前月數=L, n=len(g), 中位誤差=float(np.median(np.abs(g["e"]))), 不外推=float(np.median(np.abs(g["e_noext"]))),
                        共識校正=float(np.median(np.abs(g["e_k"]))), 校正不外推=float(np.median(np.abs(g["e_k_noext"]))),
                        校正不外推_20內=float(np.mean(np.abs(np.exp(g["e_k_noext"]) - 1) <= 0.2)),
                        在20內=float(np.mean(np.abs(np.exp(g["e"]) - 1) <= 0.2)), EPS部分=float(np.median(np.abs(g["e_eps"]))),
                        本益比不變=float(np.median(np.abs(g["e_unch"])))))
    say("\n-- 同一批目標日再加 24 個月前的預估（24 個月：上一個財年的共識 × 隱含成長外推；「不外推」＝直接用上一個財年的共識）")
    say(pd.DataFrame(c24).round(3).to_string(index=False))
    for grp in ("cyclical", "growth", "tech_other", "other"):
        sub = d[d["common"] & (d["grp"] == grp) & d["L"].isin([12, 9, 6, 3])]
        gg = sub.groupby("L").agg(e=("e_k", lambda v: np.median(np.abs(v))), ee=("e_eps_k", lambda v: np.median(np.abs(v))),
                                  pp=("e_perfect", lambda v: np.median(np.abs(v))))
        say(f"  {GNAME[grp]}（{sub['ticker'].nunique()} 家）共識校正版：" + "、".join(
            f"{L} 個月前 {r.e:.3f}（EPS 部分 {r.ee:.3f}、EPS 猜對 {r.pp:.3f}）" for L, r in gg.sort_index(ascending=False).iterrows()))
    yr = d[d["common"] & d["L"].isin([12, 6])].assign(Y=lambda v: v["T"].dt.year).groupby(["Y", "L"])["e"].apply(lambda v: np.median(np.abs(v))).unstack()
    say(f"  逐年（目標日年份）：6 個月前預估比 12 個月前準的年數 {int((yr[6] < yr[12]).sum())}／{len(yr)}")
    pd.concat([c.assign(樣本="L＝2～12 共同"), pd.DataFrame(c24).assign(樣本="加 24 個月")]).to_csv(
        os.path.join(RES, "usage_update_curve.csv"), index=False, float_format="%.6f")

    fr, n = freshness(b, x, bt)
    say(f"\n== 一之二、6 個月前預估，股價和今天 EPS 是最新的，但共識用 s 個月前的（共同樣本 {n:,} 個目標日）")
    for s, v in fr.items():
        say(f"  共識舊 {s} 個月：中位 |本益比誤差| 原樣 {np.median(np.abs(v['e'])):.3f}、校正 {np.median(np.abs(v['e_k'])):.3f}；"
            f"EPS 部分 原樣 {np.median(np.abs(v['e_eps'])):.3f}、校正 {np.median(np.abs(v['e_eps_k'])):.3f}；"
            f"±20% 內（校正）{np.mean(np.abs(np.exp(v['e_k']) - 1) <= 0.2):.0%}")

    model = json.load(open(os.path.join(RES, "orbit_model.json")))
    model["band_delta"] = json.load(open(os.path.join(RES, "band_epschange.json")))["delta"]
    p = pd.read_csv(os.path.join(RES, "orbit_predictions.csv.gz"), parse_dates=["month"])
    band = {h: band_q(p, h, model["alpha"], model["band_delta"][str(h)]) for h in (6, 12)}
    s = scenarios(b, x, bt, p, model, band)
    say("\n== 二、80% 本益比區間：只填共識 vs 三個情境取聯集（涵蓋目標 80%；區間分數越低越好）")
    for h in (12, 6):
        say(f"-- {h} 個月")
        say(s[s["h"] == h].drop(columns="h").round(3).to_string(index=False))
    s.to_csv(os.path.join(RES, "usage_scenarios.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "usage_backtest.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
