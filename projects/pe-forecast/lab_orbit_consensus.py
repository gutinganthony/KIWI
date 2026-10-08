#!/usr/bin/env python3
"""拿「真正的歷史分析師共識」當你的 EPS：12 個月後的本益比實際多準？（README §18）

    python3 lab_orbit_consensus.py         # 要先跑過 osap_fetch.py（data/osap/feps_sp500.csv.gz）與 lab_orbit.py

共識：OSAP 的 FEPS＝I/B/E/S 每月 FY1（還沒公布的本財年）共識平均，分割調整到今天的股數（osap_fetch.py）。口徑是調整後（street）。
挑起點：本財年的年報在「起點後 10.5～12 個月」之間公布 → 12 個月後的最近四季 EPS 剛好就是本財年 EPS，FY1 共識不用換算。
  年報公布日＝那一季財報的可用日（data/quarters_sp500.csv 的 avail）；會計年度結束月份＝Yahoo 年度資料（pef/consensus.fy_month，有快取）。
比較（都用 lab_orbit.py 的走動式「原始成長a」β：起點那一年 1 月的版本）：
  共識（原樣）：EPS_a＝FEPS
  共識（校正）：EPS_a＝FEPS × 這家公司過去（起點以前已揭曉的）「實際 GAAP 本財年 EPS ÷ 一年前的 FY1 共識」的中位數（至少 2 筆，否則用全體過去的中位數）
  EPS 完全正確：EPS_a＝實際（上限）；本益比不變：今天的本益比（不用 EPS）
本益比誤差 ＝ ln(預測本益比 ÷ 實際本益比)，實際本益比＝12 個月後股價 ÷ 那時已公布的最近四季 GAAP EPS。
另外用真正的共識重估 β：y12 ~ β_e × ln(共識 ÷ 今天 EPS) ＋ β_s × ln(實際 ÷ 共識)（同月份去平均、Huber、沒有截距），和代理預期的 β 對照。
輸出：results/orbit_consensus.txt、orbit_consensus_scores.csv、orbit_consensus_beta.csv
"""
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import consensus                                # noqa: E402
from pef.stats import huber_ols                          # noqa: E402

RES = os.path.join(HERE, "results")
DATA = os.path.join(HERE, "data")
GNAME = {"cyclical": "半導體／設備／記憶體", "growth": "軟體／網路", "tech_other": "其他科技", "other": "非科技"}
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def fy_report_dates(q, month):
    """每個會計年度結束那一季 → (年度結束日, 年報可用日)。季末月份和結束月份差 ≤ 1 個月的才算（52／53 週制會差幾天）；
    相隔不到 200 天的歸成同一個年度，取月份最接近的那一季。"""
    m = q["period_end"].dt.month
    dist = np.minimum((m - month).abs(), 12 - (m - month).abs())
    c = q[dist <= 1].assign(dist=dist[dist <= 1]).sort_values("period_end")
    out, grp = [], []
    for r in c.itertuples():
        if grp and (r.period_end - grp[-1].period_end).days >= 200:
            out.append(min(grp, key=lambda k: (k.dist, -k.period_end.value)))
            grp = []
        grp.append(r)
    if grp:
        out.append(min(grp, key=lambda k: (k.dist, -k.period_end.value)))
    return pd.DataFrame([(k.period_end, k.avail) for k in out], columns=["fy_end", "report"])


def main():
    fe = pd.read_csv(os.path.join(DATA, "osap", "feps_sp500.csv.gz"))
    fe["month"] = pd.to_datetime(fe["yyyymm"].astype(int).astype(str) + "01")
    fe = fe[fe["feps"].notna()][["ticker", "month", "feps"]]
    p = pd.read_csv(os.path.join(RES, "orbit_predictions.csv.gz"), parse_dates=["month"])
    beta = pd.read_csv(os.path.join(RES, "orbit_beta.csv"))
    q = pd.read_csv(os.path.join(DATA, "quarters_sp500.csv"), parse_dates=["period_end", "avail"])
    sp = pd.read_csv(os.path.join(DATA, "sp500_membership_spells.csv"), parse_dates=["start_date", "end_date"])
    sp["end_date"] = sp["end_date"].fillna(pd.Timestamp("2100-01-01"))
    sp["ticker"] = sp["ticker"].str.replace(".", "-", regex=False)
    nd = pd.read_csv(os.path.join(DATA, "ndx_members_jan1.csv"))

    x = p.merge(fe, on=["ticker", "month"], how="inner")
    say(f"有共識的公司月：{len(x):,}（{x['ticker'].nunique()} 家，{x['month'].min():%Y-%m}～{x['month'].max():%Y-%m}）")

    # 每家公司的會計年度與年報公布日
    rows = []
    cache = os.path.join(HERE, ".cache", "yahoo")
    for t, g in x.groupby("ticker"):
        mth = consensus.fy_month(t, cache, max_age_h=24 * 90)
        if mth is None:
            continue
        fy = fy_report_dates(q[q["ticker"] == t], mth)
        for r in g.itertuples():
            fut = fy[fy["report"] > r.month + pd.offsets.MonthEnd(0)]
            if fut.empty:
                continue
            f1 = fut.iloc[0]
            lead = (f1["report"] - (r.month + pd.offsets.MonthEnd(0))).days / 30.44
            rows.append((r.Index, f1["fy_end"], f1["report"], lead))
    meta = pd.DataFrame(rows, columns=["idx", "fy_end", "report", "lead"]).set_index("idx")
    x = x.join(meta, how="inner")
    say(f"對上會計年度：{len(x):,} 列、{x['ticker'].nunique()} 家")

    # 校正係數：過去（報告日 ≤ 起點）「實際 GAAP 本財年 EPS ÷ 那一年 lead≈11 個月時的共識」
    one = x[(x["lead"] > 10.5) & (x["lead"] <= 12.0)].copy()          # 每家每年約一個起點
    one = one[one["y12"].notna() & one["eps_f12"].notna()]
    one["ratio"] = one["eps_f12"] / one["feps"]
    ks = []
    allpast = one[["report", "ratio"]].sort_values("report")
    for r in one.itertuples():
        past = one[(one["ticker"] == r.ticker) & (one["report"] <= r.month)]["ratio"]
        past = past[(past > 0) & np.isfinite(past)]
        if len(past) >= 2:
            ks.append(float(np.clip(np.median(past), 0.3, 1.5)))
        else:
            gp = allpast[(allpast["report"] <= r.month) & (allpast["ratio"] > 0)]["ratio"]
            ks.append(float(np.clip(np.median(gp), 0.3, 1.5)) if len(gp) >= 50 else 1.0)
    one["k"] = ks
    say(f"評分用的起點（年報在 10.5～12 個月後公布）：{len(one):,} 列、{one['ticker'].nunique()} 家；"
        f"共識 ÷ 實際 GAAP 的中位 {np.exp(np.median(np.log(one['feps'] / one['eps_f12']).dropna())):.3f}（> 1：共識比 GAAP 高）")

    bt = beta[beta["方法"] == "原始成長a"].set_index(["h", "年", "組別"])["b0"]
    one["b"] = [bt.get((12, m.year, GNAME[g]), np.nan) for m, g in zip(one["month"], one["grp"])]
    pos = (one["eps0"] > 0) & (one["eps_f12"] > 0) & (one["feps"] > 0) & one["b"].notna()
    d = one[pos].copy()
    act_lpe = np.log(d["px"]) + d["y12"] + d["orbit_lr"] - np.log(d["eps_f12"])            # 實際 ln 本益比（12 個月後）
    def pe_err(ea):
        lpx = np.log(d["px"]) + d["orbit_lr"] + d["b"] * np.log(ea / d["eps0"]).clip(-2, 2)
        return lpx - np.log(ea) - act_lpe
    d["e_unch"] = np.log(d["px"] / d["eps0"]) - act_lpe
    d["e_perfect"] = pe_err(d["eps_f12"])
    d["e_cons"] = pe_err(d["feps"])
    d["e_consk"] = pe_err(d["feps"] * d["k"])
    d["eps_err_cons"] = np.log(d["feps"] / d["eps_f12"])
    d["eps_err_consk"] = np.log(d["feps"] * d["k"] / d["eps_f12"])
    d["year"] = d["month"].dt.year
    mm = d[["ticker", "month"]].merge(sp, on="ticker", how="left")
    mm["pit"] = (mm["start_date"] <= mm["month"] + pd.offsets.MonthEnd(0)) & (mm["end_date"] > mm["month"])
    d = d.merge(mm.groupby(["ticker", "month"])["pit"].any().rename("sp_pit").reset_index(), on=["ticker", "month"], how="left")
    d = d.merge(nd.rename(columns={"year": "year"}).assign(ndx=True), on=["year", "ticker"], how="left")
    d["ndx"] = d["ndx"].fillna(False).astype(bool)
    d["sp_pit"] = d["sp_pit"].fillna(False).astype(bool)

    out = []
    for per, (lo, hi) in {"2012–2021": ("2012-01-01", "2021-12-31"), "2022 以後": ("2022-01-01", "2026-12-31"),
                          "全期": ("2012-01-01", "2026-12-31")}.items():
        dp = d[(d["month"] >= lo) & (d["month"] <= hi)]
        for gn, m in (("S&P 500（當時成分股）", dp["sp_pit"]), ("Nasdaq-100（當年成分股）", dp["ndx"]),
                      ("科技（S&P 500 面板）", dp["grp"] != "other"), ("全部", dp["ticker"].notna())):
            dd = dp[m]
            if len(dd) < 50:
                continue
            r = dict(期間=per, 群組=gn, n=len(dd), 家數=dd["ticker"].nunique())
            for k, lab in (("e_unch", "本益比不變"), ("e_cons", "共識原樣"), ("e_consk", "共識校正"), ("e_perfect", "EPS完全正確")):
                r[lab] = float(np.median(np.abs(dd[k])))
                r[lab + "_±20%"] = float(np.mean(np.abs(np.exp(dd[k]) - 1) <= 0.2))
            r["共識EPS誤差"] = float(np.median(np.abs(dd["eps_err_cons"])))
            r["校正後EPS誤差"] = float(np.median(np.abs(dd["eps_err_consk"])))
            r["共識偏高中位"] = float(np.median(dd["eps_err_cons"]))
            out.append(r)
    sc = pd.DataFrame(out)
    say("\n== 1. 12 個月後本益比的中位 |ln 誤差|（拿共識當你的 EPS）")
    say(sc[["期間", "群組", "n", "家數", "本益比不變", "共識原樣", "共識校正", "EPS完全正確", "共識EPS誤差", "校正後EPS誤差", "共識偏高中位"]]
        .round(3).to_string(index=False))
    say("\n== 1b. 落在實際 ±20% 內的比例")
    say(sc[["期間", "群組", "本益比不變_±20%", "共識原樣_±20%", "共識校正_±20%", "EPS完全正確_±20%"]].round(3).to_string(index=False))

    # 2. 用真正的共識重估 β（y12 ~ e + s）
    brow = []
    z = x[(x["eps0"] > 0) & (x["feps"] > 0) & (x["eps_f12"] > 0) & x["y12"].notna() & (x["lead"] > 10.5) & (x["lead"] <= 12.0)].copy()
    z["e"] = np.log(z["feps"] / z["eps0"]).clip(-2, 2)
    z["s"] = np.log(z["eps_f12"] / z["feps"]).clip(-2, 2)
    z["g"] = np.log(z["eps_f12"] / z["eps0"]).clip(-2, 2)
    for g in list(GNAME) + ["科技", "全部"]:
        dd = z if g == "全部" else z[z["grp"] != "other"] if g == "科技" else z[z["grp"] == g]
        if len(dd) < 200:
            continue
        yy = dd["y12"] - dd.groupby("month")["y12"].transform("median")
        dm = lambda c: dd[c] - dd.groupby("month")[c].transform("median")
        b_es = huber_ols(np.column_stack([dm("e"), dm("s")]), yy.to_numpy(float))
        b_g = huber_ols(np.column_stack([dm("g")]), yy.to_numpy(float))
        brow.append(dict(組別=GNAME.get(g, g), n=len(dd), β_共識預期=float(b_es[0]), β_和共識的差距=float(b_es[1]), β_原始成長=float(b_g[0])))
    bb = pd.DataFrame(brow)
    say("\n== 2. 用真正的共識估的 β（12 個月；同月份去平均、Huber；和 orbit_model.json 用代理預期估的 β 對照）")
    say(bb.round(3).to_string(index=False))

    sc.to_csv(os.path.join(RES, "orbit_consensus_scores.csv"), index=False, float_format="%.6f")
    bb.to_csv(os.path.join(RES, "orbit_consensus_beta.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "orbit_consensus.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
