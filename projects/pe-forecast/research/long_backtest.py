#!/usr/bin/env python3
"""README §25.1：拉長回測——2011–2024 每一年的起點，只用當時的資料預估 12、24 個月後的本益比（S&P 500 公司）

    python3 research/long_backtest.py --build <usage_backtest 的 pk pickle> --cache <orbit_x2.pkl 所在目錄> > results/long_backtest.txt

為什麼不是 1995：公司層級的 GAAP 季報（SEC XBRL）2009 年才開始，面板 2009-04～2025-09；I/B/E/S 共識（OSAP FEPS）有 2000 年以前的，
但沒有同時點的實際 EPS 和股價就不能用。1995 年起的部分改在指數層級做（research/long_index.py）。

起點：和 §24 的 I/B/E/S 配對同一套（距離年報 10.5–12 個月，本財年共識 ≈ 未來 12 個月；起點前後沒有分割）；
目標日 T＝起點＋h（h＝12、24），T 的股價、最近四季 GAAP EPS 用面板（到 2025-09），所以 12 個月起點到 2024-09、24 個月到 2023-09。
最後兩個起點（2024-09-19、2025-10-02 → 2026-10-12）是 §24.7 的回頭驗證，另外列。

方法（和 §24.7、research/case_broad.py 同一套定義）：
  事前：本益比不變｜軌道（共識 × 校正係數；24 個月外推一年、另附不外推）｜成長定價（延一年）｜成長定價（回歸）｜分組（科技用成長定價（回歸）、非科技用軌道）
  猜對：軌道（EPS_a＝實際）｜成長定價 A（EPS_a＝實際、目標日的成長預期＝T 時的共識 × 校正）｜成長定價 B（EPS_b＝實現值）
係數兩種：
  「走動式」：軌道 β、成長定價係數與 gt_hat 都用起點那年的版本（只用目標日在那年以前的配對；2015 年起才有）；
  「全期」：正式版係數（用到 2025-09 的全部配對；有後見之明）。2011–2014 年只有全期版——用 2015 年以後兩種版本的差距看後見之明有多大。
共識校正：2015 年起用走動式校正（usage_backtest.correction_wf）；2011–2014 年用同一棵樹、同一組線索，但只用起點以前已揭曉的列訓練
  （每年 1 月重訓，最少 800 列；比正式版少很多資料），再套同時點護欄。
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
sys.path.insert(0, os.path.join(HERE, "research"))
from pef import orbit, growth_price as GP               # noqa: E402

RES = os.path.join(HERE, "results")
GNAME = orbit.GNAME
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def early_correction(b):
    """2011–2014 年起點的共識校正（ln）：和 lab_eps_correction2.walk 同一棵樹與線索，每年 1 月只用報告日在前一年底以前的列（≥ 800 列）。"""
    from sklearn.ensemble import HistGradientBoostingRegressor
    import lab_eps_correction as L                       # noqa: E402
    import lab_eps_correction2 as L2                     # noqa: E402
    d = L2.add_lead_bias(b)
    pred = pd.Series(np.nan, index=b.index)
    for Y in range(2011, 2015):
        cut = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        tr = d[(d["report"] <= cut) & d["tgt"].notna() & ~d["near_split"]]
        te = d[(d["month"] > cut) & (d["month"] <= cut + pd.DateOffset(months=12))]
        if len(tr) < 800 or te.empty:
            continue
        X = tr[L.FEATS_NOW].to_numpy(float)
        X[~np.isfinite(X)] = np.nan
        empty = np.isnan(X).all(axis=0)                  # 早年還沒有的線索（例：過去偏差）→ 這一年不用
        X[:, empty] = 0.0
        mdl = HistGradientBoostingRegressor(**dict(L.GBM, min_samples_leaf=min(L.GBM["min_samples_leaf"], len(tr) // 10))).fit(X, tr["tgt"].to_numpy(float))
        Xt = te[L.FEATS_NOW].to_numpy(float)
        Xt[~np.isfinite(Xt)] = np.nan
        Xt[:, empty] = 0.0
        pred.loc[te.index] = mdl.predict(Xt)
    p = pred.clip(-1.0, 0.7)
    has = d["pb_lead"].notna() & (d["pb_lead_n"] >= 4)
    return pd.Series(np.where(has, np.clip(p, d["pb_lead"] - d["pb_abs"], d["pb_lead"] + d["pb_abs"]), p), index=b.index)


def build_pairs(b, x, h):
    s = b[(b["lead"] > 10.5) & (b["lead"] <= 12.0) & ~b["near_split"] & (b["eps0"] > 0) & (b["feps"] > 0) & (b["month"] >= "2011-01-01")].copy()
    s["T"] = s["month"] + pd.DateOffset(months=h)
    xs = x.sort_values(["ticker", "month"])
    sf_chg = xs.groupby("ticker")["split_fac"].diff().fillna(0) != 0
    ev = xs.loc[sf_chg, ["ticker", "month"]]
    evd = {t: g["month"].tolist() for t, g in ev.groupby("ticker")}
    T = x[["ticker", "month", "px", "eps0"]].rename(columns={"month": "T", "px": "px_T", "eps0": "EA"})
    d = s.merge(T, on=["ticker", "T"], how="inner")
    B = x[["ticker", "month", "eps0"]].rename(columns={"month": "TB", "eps0": "EB"})
    d["TB"] = d["T"] + pd.DateOffset(months=12)
    d = d.merge(B, on=["ticker", "TB"], how="left")
    # T 時的共識（猜對 A 用；I/B/E/S 到 2024-11）
    FT = b[["ticker", "month", "feps", "pk", "lead", "near_split"]].rename(columns={"month": "T", "feps": "feps_T", "pk": "pk_T", "lead": "lead_T", "near_split": "ns_T"})
    d = d.merge(FT, on=["ticker", "T"], how="left")
    near = [any(T_ - pd.DateOffset(months=4) < e <= T_ + pd.DateOffset(months=1) for e in evd.get(t, [])) for t, T_ in zip(d["ticker"], d["T"])]
    d = d[~np.array(near) & (d["EA"] > 0) & d["px_T"].notna()].copy()
    d["h"] = h
    d["year"] = d["month"].dt.year
    d["act"] = np.log(d["px_T"] / d["EA"])
    d["lpe0"] = np.log(d["px"] / d["eps0"])
    pm = x.groupby("month")["pe_mkt"].first()
    d["mkt_dpe"] = d["T"].map(pm).to_numpy() - d["month"].map(pm).to_numpy()            # 面板的大盤本益比（ln）在這段期間的變化
    y10 = x.groupby("month")["y10"].first()
    d["dy10"] = d["T"].map(y10).to_numpy() - d["month"].map(y10).to_numpy()
    g = np.log(d["EA"] / d["eps0"])
    d["mkt_g"] = g.groupby(d["month"]).transform("median")                            # 同一個起點月的公司，EPS 成長的中位數
    return d


def predict_all(d, h, model, gm, wb, mode):
    """mode＝"wf"（走動式；沒有那年的版本時用正式版並標記）或 "prod"（全期正式版）。回傳 DataFrame：各方法的 ln(預測 ÷ 實際) 與區間命中。"""
    out = []
    erp, alpha = model["erp"], model["alpha"]
    for r in d.itertuples(index=False):
        Y = r.year
        grp = r.grp if r.grp in GNAME else "other"
        gn = GNAME[grp]
        e0, p0, F = float(r.eps0), float(r.px), float(r.feps)
        k = float(np.exp(r.k if np.isfinite(r.k) else 0.0))
        dy0 = float(r.dy) if np.isfinite(r.dy) else 0.0
        orb = (float(r.y10) + erp - dy0) * h / 12
        wf_ok = mode == "wf" and (h, Y, "預期b＋修正ab", gn) in wb.index and str(Y) in gm["by_year"][str(h)]
        if mode == "wf" and not wf_ok:
            continue
        if wf_ok:
            b_exp = float(wb.loc[(h, Y, "預期b＋修正ab", gn), "b0"])
            b_raw = float(wb.loc[(h, Y, "原始成長a", gn), "b0"])
            yr = Y
        else:
            b_exp = float(model["h"][str(h)]["beta"]["預期b＋修正ab"][grp][0])
            b_raw = float(model["h"][str(h)]["beta"]["原始成長a"][grp][0])
            yr = None
        e1 = float(r.EA)
        pe1 = float(r.px_T) / e1
        g = float(np.clip(F / e0, 0.7, 1.5))
        ea = F if h == 12 else F * g
        p_k = p0 * np.exp(orb + b_exp * np.log(ea * k * g / e0))
        p_n = p0 * np.exp(orb + b_exp * np.log(F * k / e0))
        p_p = p0 * np.exp(orb + b_raw * float(np.clip(np.log(e1 / e0), -2, 2)))
        vol0 = float(r.vol36) if np.isfinite(r.vol36) else np.nan
        ret0 = float(r.ret12) if np.isfinite(r.ret12) else None
        row = dict(px=p0, eps0=e0, y10=float(r.y10), dy=dy0, vol36=vol0, grp=grp)
        gp_ = lambda a_, b_: GP.predict(row, h, a_, b_, F * k, ret0, model=model, gm=gm, year=yr) if (b_ and b_ > 0) else None  # noqa: E731
        ga_ = F * k if h == 12 else F * k * g
        gc = gp_(ga_, ga_ * g)
        G0_ = float(np.clip(np.log(F * k / e0), -1.5, 1.5))
        gt = (gm["by_year"]["12"][str(yr)] if yr else gm["h"]["12"])["gt_hat"]
        ea_r = F * k if h == 12 else F * k * np.exp(gt[0] + gt[1] * G0_)
        gr = gp_(ea_r, GP.eps_b_hat(gm, h, ea_r, e0, F * k, year=yr))
        FTk = float(r.feps_T) * float(np.exp(r.pk_T if np.isfinite(r.pk_T) else 0.0)) if (np.isfinite(r.feps_T) and r.feps_T > 0 and np.isfinite(r.lead_T)
                                                                                       and r.lead_T > 9.5 and not bool(r.ns_T)) else None
        go = gp_(e1, FTk)
        gb = gp_(e1, float(r.EB) if np.isfinite(r.EB) and r.EB > 0 else None)
        vq = lambda spec: vol0 if np.isfinite(vol0) else model["h"][str(h)]["bands"][spec]["vol_median"]  # noqa: E731

        def inb_orbit(pc, e_, spec):
            q = model["h"][str(h)]["bands"][spec]["q"]
            sc_ = float(np.clip(vq(spec), *orbit.VOL_CLIP) ** alpha) * float(np.exp(model["band_delta"][str(h)] * min(abs(np.log(e_ / e0)), 2.0)))
            return bool(pc * np.exp(q[0] * sc_) / e_ <= pe1 <= pc * np.exp(q[3] * sc_) / e_)
        lg = lambda o: np.log(o["pe"] / pe1) if o else np.nan                                      # noqa: E731
        inb = lambda o: (bool(o["pe_lo80"] <= pe1 <= o["pe_hi80"]) if o else np.nan)            # noqa: E731
        out.append(dict(ticker=r.ticker, month=r.month, T=r.T, year=Y, grp=gn, h=h, mode=mode, n_wf=bool(wf_ok),
                        U=np.log(p0 / e0 / pe1), O=np.log(p_k / (ea * k) / pe1), O_n=np.log(p_n / (F * k) / pe1) if h == 24 else np.log(p_k / (ea * k) / pe1),
                        G=lg(gc), Gr=lg(gr), O_or=np.log(p_p / e1 / pe1), GA=lg(go), GB=lg(gb),
                        bO=inb_orbit(p_k, ea * k, "預期b＋修正ab"), bG=inb(gc), bGr=inb(gr), bO_or=inb_orbit(p_p, e1, "原始成長a"), bGA=inb(go), bGB=inb(gb),
                        epsg=np.log(e1 / e0), eps_err=np.log(ea * k / e1), mkt_dpe=r.mkt_dpe, mkt_g=r.mkt_g, dy10=r.dy10, sector=r.sector))
    o = pd.DataFrame(out)
    tech = o["grp"] != "非科技"
    o["H"] = o["Gr"].where(tech, o["O"])
    o["bH"] = o["bGr"].where(tech, o["bO"])
    o["Hn"] = o["Gr"].where(tech, o["O_n"])              # 24 個月：非科技用不外推的軌道
    return o


EX = [("U", "本益比不變"), ("O", "軌道"), ("O_n", "軌道不外推"), ("G", "成長定價（延一年）"), ("Gr", "成長定價（回歸）"), ("H", "分組"), ("Hn", "分組（不外推）")]
OR = [("O_or", "猜對：軌道"), ("GA", "猜對：成長定價 A（T 的共識）"), ("GB", "猜對：成長定價 B（實現值）")]


def med(e):
    e = e.dropna()
    return float(np.median(np.abs(e))) if len(e) else np.nan


def table(o, by, cols, min_n=20):
    rows = []
    for k, g in o.groupby(by, observed=True):
        if len(g) < min_n:
            continue
        r = dict(zip(by if isinstance(by, list) else [by], k if isinstance(k, tuple) else [k]))
        r["n"] = len(g)
        for c, nm in cols:
            r[nm] = med(g[c])
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    b = pd.read_pickle(a.build)
    if "pk" not in b:
        import usage_backtest as UB                      # noqa: E402
        b["pk"] = UB.correction_wf(b)
    b["k"] = b["pk"]
    early = early_correction(b)
    b.loc[b["month"] < "2015-01-01", "k"] = early[b["month"] < "2015-01-01"]
    x = pd.read_pickle(os.path.join(a.cache, "orbit_x2.pkl"))
    model = orbit.load_model()                           # 含 band_delta（§22.4）
    gm = GP.load()
    wb = pd.read_csv(os.path.join(RES, "orbit_beta.csv")).set_index(["h", "年", "方法", "組別"])
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 40)
    allo = []
    for h in (12, 24):
        d = build_pairs(b, x, h)
        o = pd.concat([predict_all(d, h, model, gm, wb, "prod"), predict_all(d, h, model, gm, wb, "wf")], ignore_index=True)
        o = o[o[["U", "O", "G", "Gr"]].notna().all(axis=1)]
        allo.append(o)
        P = o[o["mode"] == "prod"]
        W = o[o["mode"] == "wf"]
        say(f"\n==================== {h} 個月（起點 {P['month'].min():%Y-%m}～{P['month'].max():%Y-%m}，{len(P):,} 組、{P['ticker'].nunique()} 家）")
        say(f"共識校正（ln）中位數：2011–2014 {d.loc[d['year'] < 2015, 'k'].median():+.3f}（有校正的比例 {d.loc[d['year'] < 2015, 'k'].notna().mean():.0%}）、"
            f"2015 以後 {d.loc[d['year'] >= 2015, 'k'].median():+.3f}（{d.loc[d['year'] >= 2015, 'k'].notna().mean():.0%}）")
        say("-- 1. 逐年（起點年份）：中位 |ln 本益比誤差|；係數＝全期版（2011–2014 只有這版）")
        t1 = table(P, "year", EX + OR, min_n=15)
        say(t1.round(3).to_string(index=False))
        say("-- 1b. 走動式係數（嚴格事前，2015 年起）")
        t1w = table(W, "year", EX + OR, min_n=15)
        say(t1w.round(3).to_string(index=False))
        # 後見之明的影響：同一批列
        both = P.merge(W, on=["ticker", "month"], suffixes=("_p", "_w"))
        W = W.assign(組=np.where(W["grp"] == "非科技", "非科技", "科技"))
        say(table(W, ["組"], EX + OR).round(3).to_string(index=False))
        say("  後見之明（2015 年起同一批列；全期 → 走動式）：" + "、".join(f"{nm} {med(both[c + '_p']):.3f} → {med(both[c + '_w']):.3f}" for c, nm in EX + OR))
        say("-- 2. 依期間與組別（全期係數）")
        P = P.assign(期間=pd.cut(P["year"], [2010, 2014, 2019, 2021, 2024], labels=["2011–2014", "2015–2019", "2020–2021", "2022–2024"]),
                     組=np.where(P["grp"] == "非科技", "非科技", "科技"))
        say(table(P, ["期間", "組"], EX + OR).round(3).to_string(index=False))
        say(table(P, ["組"], EX + OR).round(3).to_string(index=False))
        say("-- 3. 依市場環境（全期係數）")
        P["大盤倍數"] = pd.cut(P["mkt_dpe"], [-9, -0.1, 0.1, 9], labels=["收縮（< −10%）", "持平", "擴張（> +10%）"])
        P["整體獲利"] = pd.cut(P["mkt_g"] * 12 / h, [-9, -0.02, 0.10, 9], labels=["衰退（年化 < −2%）", "溫和", "大增（年化 > +10%）"])
        P["利率"] = pd.cut(P["dy10"], [-9, -0.005, 0.005, 9], labels=["降（< −0.5 點）", "持平", "升（> +0.5 點）"])
        P["個股EPS變化"] = pd.cut(P["epsg"].abs(), [0, 0.1, 0.25, 0.5, 9], labels=["< 10%", "10–25%", "25–50%", "> 50%"], include_lowest=True)
        for c in ("大盤倍數", "整體獲利", "利率", "個股EPS變化"):
            say(table(P, [c, "組"], EX + OR).round(3).to_string(index=False))
        say("-- 4. 誤差在 ±20% 內的比例、80% 區間涵蓋（全期係數，全部）")
        w20 = {nm: float(np.mean(np.abs(np.exp(P[c].dropna()) - 1) <= 0.2)) for c, nm in EX + OR}
        cov = {nm: float(P[c].dropna().astype(float).mean()) for c, nm in (("bO", "軌道"), ("bG", "成長定價（延一年）"), ("bGr", "成長定價（回歸）"), ("bH", "分組"),
                                                                       ("bO_or", "猜對：軌道"), ("bGA", "猜對：成長定價 A"), ("bGB", "猜對：成長定價 B"))}
        say("  ±20%：" + "、".join(f"{k} {v:.0%}" for k, v in w20.items()))
        say("  80% 涵蓋：" + "、".join(f"{k} {v:.0%}" for k, v in cov.items()))
        say("  逐年 80% 涵蓋（軌道／成長定價回歸）：" + "、".join(f"{y} {g['bO'].mean():.0%}／{g['bGr'].astype(float).mean():.0%}" for y, g in P.groupby("year")))
        say("-- 5. 勝負：每個起點年份 × 組別，成長定價（回歸）比軌道準的格數（全期係數）")
        for grp_lab, m in (("科技", P["組"] == "科技"), ("非科技", P["組"] == "非科技")):
            t = table(P[m], "year", [("Gr", "Gr"), ("O", "O"), ("O_n", "O_n"), ("H", "H"), ("U", "U"), ("GA", "GA"), ("O_or", "O_or")], min_n=10)
            say(f"  {grp_lab}：成長定價（回歸）勝軌道 {int((t['Gr'] < t['O']).sum())}／{len(t)} 年（勝不外推的軌道 {int((t['Gr'] < t['O_n']).sum())}）；"
                f"軌道勝本益比不變 {int((t['O'] < t['U']).sum())}／{len(t)}（不外推 {int((t['O_n'] < t['U']).sum())}）；成長定價（回歸）勝本益比不變 {int((t['Gr'] < t['U']).sum())}；"
                f"猜對時成長定價 A 勝軌道 {int((t['GA'] < t['O_or']).sum())}／{int(t['GA'].notna().sum())}")
        for grp_lab, m in (("科技", W["組"] == "科技"), ("非科技", W["組"] == "非科技")):
            t = table(W[m], "year", [("Gr", "Gr"), ("O", "O"), ("O_n", "O_n"), ("U", "U"), ("GA", "GA"), ("O_or", "O_or")], min_n=10)
            say(f"  走動式 {grp_lab}：成長定價（回歸）勝軌道 {int((t['Gr'] < t['O']).sum())}／{len(t)} 年（勝不外推 {int((t['Gr'] < t['O_n']).sum())}）；"
                f"猜對時成長定價 A 勝軌道 {int((t['GA'] < t['O_or']).sum())}／{int(t['GA'].notna().sum())}")
        say("  偏差（中位 ln(預測 ÷ 實際)，逐年）：" + "；".join(f"{y} 軌道 {g['O'].median():+.2f}、成長 {g['Gr'].median():+.2f}、不變 {g['U'].median():+.2f}" for y, g in P.groupby("year")))
    o = pd.concat(allo, ignore_index=True)
    o.to_csv(os.path.join(RES, "long_backtest_rows.csv.gz"), index=False, float_format="%.5g")
    open(os.path.join(RES, "long_backtest.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
