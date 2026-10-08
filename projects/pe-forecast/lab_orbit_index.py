#!/usr/bin/env python3
"""本益比軌道模型（README §16）依指數分組的回測報告：S&P 500 與 Nasdaq-100（README §17）。

    python3 lab_orbit_index.py          # 幾秒；只讀 lab_orbit.py／lab_orbit_recent.py／orbit_fit.py 的結果，不重新訓練

預測本身沒有變：用 lab_orbit.py 的走動式樣本外預測（每年 1 月只用當時已揭曉的資料估 β 與市場預期代理），只是換分組評分。
分組（預測起點那個月）：
  S&P 500（名單）＝面板的 476 家（2025 年的 S&P 500 名單，有倖存者偏誤）
  S&P 500（當時成分股）＝起點那個月真的在 S&P 500 裡（data/sp500_membership_spells.csv）
  Nasdaq-100（當年 1 月成分股）＝起點那一年 1 月 1 日的名單（data/ndx_members_jan1.csv，jmccarrell/n100tickers）；
    只有同時在 S&P 500 面板裡的公司有資料（ASML、PDD 這類外國公司、和不在 S&P 500 的 Nasdaq 公司沒有）
假設 EPS 完全正確（你的 EPS＝事後實際公布的最近四季）；另列 EPS 有誤差時。本益比的 ln 誤差＝股價的 ln 誤差（分母 EPS 給定）。
區間涵蓋率：用目標日 ≤ 2021-12-31 的樣本外誤差校準（波動^0.7、置中），檢查 2022 以後的起點（和 orbit_fit.py 同做法）。
輸出：results/orbit_index.txt、orbit_index_scores.csv、orbit_index_years.csv、orbit_index_bands.csv、orbit_index_firms.csv、
      orbit_index_epsnoise.csv
"""
import io
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import cond                                     # noqa: E402

RES = os.path.join(HERE, "results")
DATA = os.path.join(HERE, "data")
PAIR = {6: (6, 18), 12: (12, 24), 24: (24, 36)}
PERIODS = {"2015–2021": ("2015-01-01", "2021-12-31"), "2022 以後": ("2022-01-01", "2026-12-31")}
Q = (0.1, 0.25, 0.75, 0.9)
GNAME = {"cyclical": "半導體／設備／記憶體", "growth": "軟體／網路", "tech_other": "其他科技", "other": "非科技"}
METH = {"unch": "本益比不變", "orbit": "軌道", "raw_a": "＋你的EPS(a)", "raw_ab": "＋你的EPS(a,b)", "cons_ab": "＋共識代理＋你的EPS"}
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def tgt(month, h):
    return month + pd.DateOffset(months=h) + pd.offsets.MonthEnd(0)


def scale(vol, vmed):
    return np.clip(np.where(np.isfinite(vol), vol, vmed), *cond.VOL_CLIP) ** cond.BAND_ALPHA


def load():
    p = pd.read_csv(os.path.join(RES, "orbit_predictions.csv.gz"), parse_dates=["month"])
    p = p[p["month"] >= "2015-01-01"].copy()
    sp = pd.read_csv(os.path.join(DATA, "sp500_membership_spells.csv"), parse_dates=["start_date", "end_date"])
    sp["end_date"] = sp["end_date"].fillna(pd.Timestamp("2100-01-01"))
    sp["ticker"] = sp["ticker"].str.replace(".", "-", regex=False)
    me = p[["ticker", "month"]].drop_duplicates().merge(sp, on="ticker", how="left")
    me["pit"] = (me["start_date"] <= me["month"] + pd.offsets.MonthEnd(0)) & (me["end_date"] > me["month"])
    pit = me.groupby(["ticker", "month"])["pit"].any().rename("sp_pit").reset_index()
    p = p.merge(pit, on=["ticker", "month"], how="left")
    nd = pd.read_csv(os.path.join(DATA, "ndx_members_jan1.csv"))
    p["year"] = p["month"].dt.year
    p = p.merge(nd.assign(ndx=True), on=["year", "ticker"], how="left")
    p["ndx"] = p["ndx"].fillna(False).astype(bool)
    p["sp_pit"] = p["sp_pit"].fillna(False).astype(bool)
    return p, nd


def errors(d, h):
    """每列各方法的 ln(預測 ÷ 實際)。"""
    a = PAIR[h][0]
    e = pd.DataFrame(index=d.index)
    e["unch"] = d[f"g{a}"] - (d[f"y{h}"] + d["orbit_lr"] * h / 12)
    e["orbit"] = -d[f"y{h}"]
    e["raw_a"] = d[f"p{h}_原始成長a"] - d[f"y{h}"]
    e["raw_ab"] = d[f"p{h}_原始成長ab"] - d[f"y{h}"]
    e["cons_ab"] = d[f"p{h}_預期b＋修正ab"] - d[f"y{h}"]
    return e


def main():
    p, nd = load()
    groups = {"S&P 500（2025 名單）": p["ticker"].notna(), "S&P 500（當時成分股）": p["sp_pit"], "Nasdaq-100（當年成分股）": p["ndx"]}
    cov = pd.DataFrame({"Nasdaq-100 名單": nd[nd["year"].between(2015, 2025)].groupby("year")["ticker"].nunique(),
                        "有資料": p[p["ndx"]].groupby("year")["ticker"].nunique(),
                        "S&P 500 當時成分股": p[p["sp_pit"]].groupby("year")["ticker"].nunique()})
    say("== 0. 樣本：每年有資料的家數（預測起點那一年）")
    say(cov.T.fillna(0).astype(int).to_string())

    # 1. 主表
    rows = []
    for h in PAIR:
        a = PAIR[h][0]
        base = p[p[f"y{h}"].notna() & p[f"g{a}"].notna() & p[f"p{h}_原始成長a"].notna()]
        for per, (lo, hi) in PERIODS.items():
            bp = base[(base["month"] >= lo) & (base["month"] <= hi)]
            for gn, gm in groups.items():
                for sub, sm in (("全部", None), ("科技", "tech")):
                    d = bp[gm.reindex(bp.index).fillna(False)]
                    if sm:
                        d = d[d["grp"] != "other"]
                    e = errors(d, h)
                    for samp, need in (("a", ["raw_a"]), ("ab", ["raw_ab", "cons_ab"])):
                        ee = e.dropna(subset=need)
                        if len(ee) < 100:
                            continue
                        r = dict(h=h, 期間=per, 指數=gn, 類型=sub, 樣本=samp, 家數=int(d.loc[ee.index, "ticker"].nunique()), n=len(ee))
                        for m in (["unch", "orbit", "raw_a"] + (["raw_ab", "cons_ab"] if samp == "ab" else [])):
                            r[METH[m]] = float(np.median(np.abs(ee[m])))
                            r[f"{METH[m]}_±20%"] = float(np.mean(np.abs(np.exp(ee[m]) - 1) <= 0.2))
                        rows.append(r)
    sc = pd.DataFrame(rows)
    show = ["本益比不變", "軌道", "＋你的EPS(a)", "＋你的EPS(a,b)", "＋共識代理＋你的EPS"]
    for h in PAIR:
        say(f"\n== 1. {h} 個月後本益比（＝股價）的中位 |ln 誤差|，EPS 完全正確；樣本 a＝只需 {PAIR[h][0]} 個月後 EPS（含較新的起點），"
            f"ab＝也有 {PAIR[h][1]} 個月後 EPS")
        t = sc[sc["h"] == h][["期間", "指數", "類型", "樣本", "家數", "n"] + [c for c in show if c in sc]]
        say(t.round(3).to_string(index=False))
    say("\n== 1b. 落在實際 ±20% 內的比例（12 個月，樣本 a）")
    t = sc[(sc["h"] == 12) & (sc["樣本"] == "a")][["期間", "指數", "類型", "n", "本益比不變_±20%", "軌道_±20%", "＋你的EPS(a)_±20%"]]
    say(t.round(3).to_string(index=False))

    # 2. 區間涵蓋率（2021 以前校準 → 2022 以後檢查）
    brow = []
    for h in PAIR:
        a = PAIR[h][0]
        z = p[p[f"y{h}"].notna() & p[f"p{h}_原始成長a"].notna() & (p[f"eps_f{a}"] > 0)].copy()
        z["e"] = z[f"y{h}"] - z[f"p{h}_原始成長a"]                   # 實際 − 預測
        cal = z[tgt(z["month"], h) <= pd.Timestamp("2021-12-31")]
        vmed = float(cal["vol36"].median())                    # 缺波動時補的中位數也只用校準期
        u = cal["e"].to_numpy() / scale(cal["vol36"].to_numpy(float), vmed)
        q = np.quantile(u - np.median(u), Q)
        chk = z[z["month"] >= "2022-01-01"]
        for gn, gm in groups.items():
            d = chk[gm.reindex(chk.index).fillna(False)]
            if len(d) < 100:
                continue
            uu = d["e"].to_numpy() / scale(d["vol36"].to_numpy(float), vmed)
            raw = dict(h=h, 指數=gn, n=len(d), 偏差中位=float(np.median(d["e"])))
            for lab, v in (("置中後", uu - np.median(uu)), ("不置中", uu)):
                raw[f"{lab}_涵蓋50"] = float(np.mean((v >= q[1]) & (v <= q[2])))
                raw[f"{lab}_涵蓋80"] = float(np.mean((v >= q[0]) & (v <= q[3])))
            brow.append(raw)
    bands = pd.DataFrame(brow)
    say("\n== 2. 區間涵蓋率（2021 以前的誤差校準 → 2022 以後檢查；目標 50%／80%；「不置中」＝含那段期間的大盤偏差，是實際用起來的涵蓋率）")
    say(bands.round(3).to_string(index=False))

    # 3. EPS 有誤差時（12 個月、2022 以後、樣本 ab）
    m = json.load(open(os.path.join(RES, "orbit_model.json")))
    rng = np.random.default_rng(0)
    say("\n== 3. 你的 EPS 有誤差時的本益比誤差（12 個月，2022 以後；σ＝0.1／0.2／0.3 約等於 EPS 中位差 7%／13%／20%）")
    bt = m["h"]["12"]["beta"]["原始成長ab"]
    nrow = []
    for gn, gm in groups.items():
        d = p[gm & (p["month"] >= "2022-01-01") & p["y12"].notna() & p["p12_原始成長ab"].notna()]
        ba, bb = d["grp"].map({g: v[0] for g, v in bt.items()}), d["grp"].map({g: v[1] for g, v in bt.items()})
        base_e = d["p12_原始成長ab"] - d["y12"]
        r = dict(指數=gn, n=len(d), 本益比不變=float(np.median(np.abs(d["g12"] - (d["y12"] + d["orbit_lr"])))))
        for sig in (0.0, 0.1, 0.2, 0.3):
            na, nb = rng.normal(0, sig, len(d)), rng.normal(0, sig, len(d))
            r[f"σ={sig:.1f}"] = float(np.median(np.abs(base_e + ba * na + bb * nb - na)))
        nrow.append(r)
    noise = pd.DataFrame(nrow)
    say(noise.round(3).to_string(index=False))

    # 4. 逐年（12 個月，樣本 a）
    yrow = []
    d0 = p[p["y12"].notna() & p["g12"].notna() & p["p12_原始成長a"].notna()]
    for gn, gm in groups.items():
        for Y, d in d0[gm.reindex(d0.index).fillna(False)].groupby("year"):
            e = errors(d, 12)
            yrow.append(dict(指數=gn, 起點年=Y, n=len(d), 本益比不變=float(np.median(np.abs(e["unch"]))),
                             軌道=float(np.median(np.abs(e["orbit"]))), 模型=float(np.median(np.abs(e["raw_a"]))),
                             股價偏離軌道中位=float(np.median(d["y12"]))))
    yrs = pd.DataFrame(yrow)
    say("\n== 4. 逐年（12 個月；模型＝軌道＋你的 EPS(a)；「股價偏離軌道」＝那一年實際比軌道多漲（+）或少漲（−），ln）")
    say(yrs.pivot_table(index="起點年", columns="指數", values=["模型", "本益比不變", "股價偏離軌道中位"]).round(3).to_string())

    # 5. 逐家（12 個月，樣本 a，2015 以後，至少 12 個起點）
    frow = []
    for gn, gm in groups.items():
        d = d0[gm.reindex(d0.index).fillna(False)]
        e = errors(d, 12).assign(ticker=d["ticker"], grp=d["grp"])
        g = e.groupby("ticker").agg(n=("orbit", "size"), unch=("unch", lambda v: np.median(np.abs(v))),
                                    orbit=("orbit", lambda v: np.median(np.abs(v))), model=("raw_a", lambda v: np.median(np.abs(v))),
                                    grp=("grp", "first"))
        g = g[g["n"] >= 12]
        frow.append(g.assign(指數=gn).reset_index())
        say(f"\n== 5. 逐家（{gn}，12 個月，至少 12 個起點，{len(g)} 家）：模型比本益比不變準 {int((g['model'] < g['unch']).sum())} 家"
            f"（{(g['model'] < g['unch']).mean():.0%}）；比單純軌道準 {int((g['model'] < g['orbit']).sum())} 家（{(g['model'] < g['orbit']).mean():.0%}）")
        gg = g.sort_values("model")
        say("   最準：" + "、".join(f"{t} {r.model:.2f}" for t, r in gg.head(6).iterrows()))
        say("   最不準：" + "、".join(f"{t} {r.model:.2f}" for t, r in gg.tail(6)[::-1].iterrows()))
        by = g.groupby("grp")[["unch", "orbit", "model"]].median()
        say("   依類型（各家中位數的中位）：" + "；".join(f"{GNAME[k]} 模型 {r.model:.2f}／不變 {r.unch:.2f}" for k, r in by.iterrows()))
    firms = pd.concat(frow, ignore_index=True)

    # 6. 最近一段（lab_orbit_recent.py：起點 2024-10～2025-09，目標日到 2026-09）
    rp = os.path.join(RES, "orbit_recent_rows.csv.gz")
    if os.path.exists(rp):
        r = pd.read_csv(rp, parse_dates=["month"])
        r["year"] = r["month"].dt.year
        r = r.merge(nd.assign(ndx=True), on=["year", "ticker"], how="left")
        r["ndx"] = r["ndx"].fillna(False).astype(bool)
        sp = pd.read_csv(os.path.join(DATA, "sp500_membership_spells.csv"), parse_dates=["start_date", "end_date"])
        sp["end_date"] = sp["end_date"].fillna(pd.Timestamp("2100-01-01"))
        sp["ticker"] = sp["ticker"].str.replace(".", "-", regex=False)
        mm = r[["ticker", "month"]].drop_duplicates().merge(sp, on="ticker", how="left")
        mm["pit"] = (mm["start_date"] <= mm["month"] + pd.offsets.MonthEnd(0)) & (mm["end_date"] > mm["month"])
        r = r.merge(mm.groupby(["ticker", "month"])["pit"].any().rename("sp_pit").reset_index(), on=["ticker", "month"], how="left")
        rrow = []
        for h in (6, 12):
            for gn, mask in (("S&P 500（2025 名單）", r["ticker"].notna()), ("S&P 500（當時成分股）", r["sp_pit"].fillna(False)),
                             ("Nasdaq-100（當年成分股）", r["ndx"])):
                d = r[mask & (r["h"] == h)].dropna(subset=["e_raw"])
                for sub, dd in (("全部", d), ("科技", d[d["grp"] != "other"])):
                    if len(dd) < 30:
                        continue
                    rrow.append(dict(h=h, 指數=gn, 類型=sub, 家數=dd["ticker"].nunique(), n=len(dd),
                                     本益比不變=float(np.median(np.abs(dd["e_unch"]))), 軌道=float(np.median(np.abs(dd["e_orbit"]))),
                                     模型=float(np.median(np.abs(dd["e_raw"]))),
                                     命中20_模型=float(np.mean(np.abs(np.exp(dd["e_raw"]) - 1) <= 0.2)),
                                     股價偏離軌道中位=float(np.median(dd["y"]))))
        rec = pd.DataFrame(rrow)
        say("\n== 6. 最近一段（起點 2024-10～2025-09，目標日到 2026-09；股價 Yahoo、EPS 最新申報值；模型＝軌道＋你的 EPS(a)）")
        say(rec.round(3).to_string(index=False))
        sc = pd.concat([sc, rec.assign(期間="最近（目標日到 2026-09）", 樣本="a")], ignore_index=True)

    sc.to_csv(os.path.join(RES, "orbit_index_scores.csv"), index=False, float_format="%.6f")
    yrs.to_csv(os.path.join(RES, "orbit_index_years.csv"), index=False, float_format="%.6f")
    bands.to_csv(os.path.join(RES, "orbit_index_bands.csv"), index=False, float_format="%.6f")
    firms.to_csv(os.path.join(RES, "orbit_index_firms.csv"), index=False, float_format="%.6f")
    noise.to_csv(os.path.join(RES, "orbit_index_epsnoise.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "orbit_index.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
