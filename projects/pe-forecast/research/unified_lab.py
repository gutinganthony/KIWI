#!/usr/bin/env python3
"""README §26.1：統一模型（pef/unified.py）vs 成長定價 vs 軌道——同一批 I/B/E/S 配對、走動式係數，四種輸入模式的本益比誤差；
並產生 results/unified_rows.csv.gz（每列的共識模式誤差，給 research/conformal_fit.py 校準區間）。

    python3 research/unified_lab.py --build <pk pickle> --cache <orbit_x2.pkl 目錄> > results/unified_lab.txt

配對：起點＝距離年報 10.5–12 個月（12、24 個月）或 4.5–6 個月（6 個月），目標日 T＝起點＋h，EPS_a＝T 時面板的最近四季 GAAP EPS，
EPS_b＝T＋12 的；F_0＝起點的 FY1 共識 × 走動式共識校正；F_T＝T 時的共識 × 校正（市場在目標日對下一年的預期；只有 T 在 2024-11 以前的配對有）。
走動式：軌道 β 用起點那年的版本（results/orbit_beta.csv）、成長定價係數與回歸 gt_hat 用 by_year（results/growth_price.json）；2017 年起。
模式：
  C  只有共識（事前）：統一模型＝軌道（市場看法）；對照 成長定價（回歸）、本益比不變
  A  猜對 EPS_a 與「目標日時市場對下一年的預期」：統一（EPS_b 標成市場預期 → 成長定價係數）vs 成長定價 vs 統一（標成基本面 → 軌道 β_sb）vs 軌道（原始成長a）
  B  猜對 EPS_a 與 EPS_b 的實現值（基本面預估對了）：統一（基本面＝軌道）vs 成長定價 vs 統一（誤標成市場預期）
  A1 只猜對 EPS_a：統一＝軌道（EPS_b＝共識）vs 成長定價（EPS_b＝共識）
相對誤差：扣掉同一起點月全體的中位誤差；相對名次：每個起點月，預測的 ln(本益比變化) 與實際的 Spearman。
"""
import argparse
import copy
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "research"))
from pef import orbit, unified                           # noqa: E402
from pef import growth_price as GP                       # noqa: E402
from pef.stats import spearman                           # noqa: E402

RES = os.path.join(HERE, "results")
GKEY = {v: k for k, v in orbit.GNAME.items()}
LEAD = {6: (4.5, 6.0), 12: (10.5, 12.0), 24: (10.5, 12.0)}
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def med(e):
    e = np.asarray(e, float)
    e = e[np.isfinite(e)]
    return float(np.median(np.abs(e))) if len(e) else np.nan


def pairs(b, x, h):
    lo, hi = LEAD[h]
    s = b[(b["lead"] > lo) & (b["lead"] <= hi) & ~b["near_split"] & (b["eps0"] > 0) & (b["feps"] > 0) & (b["month"] >= "2011-01-01")].copy()
    s["T"] = s["month"] + pd.DateOffset(months=h)
    xs = x.sort_values(["ticker", "month"])
    ev = xs.loc[xs.groupby("ticker")["split_fac"].diff().fillna(0) != 0, ["ticker", "month"]]
    evd = {t: g["month"].tolist() for t, g in ev.groupby("ticker")}
    T = x[["ticker", "month", "px", "eps0"]].rename(columns={"month": "T", "px": "px_T", "eps0": "EA"})
    d = s.merge(T, on=["ticker", "T"], how="inner")
    B = x[["ticker", "month", "eps0"]].rename(columns={"month": "TB", "eps0": "EB"})
    d["TB"] = d["T"] + pd.DateOffset(months=12)
    d = d.merge(B, on=["ticker", "TB"], how="left")
    FT = b[["ticker", "month", "feps", "pk", "lead", "near_split"]].rename(columns={"month": "T", "feps": "feps_T", "pk": "pk_T", "lead": "lead_T", "near_split": "ns_T"})
    d = d.merge(FT, on=["ticker", "T"], how="left")
    near = [any(T_ - pd.DateOffset(months=4) < e <= T_ + pd.DateOffset(months=1) for e in evd.get(t, [])) for t, T_ in zip(d["ticker"], d["T"])]
    d = d[~np.array(near) & (d["EA"] > 0) & d["px_T"].notna()].copy()
    d["F0k"] = d["feps"] * np.exp(d["pk"].fillna(0.0))
    ok_T = d["feps_T"].notna() & (d["feps_T"] > 0) & (d["lead_T"] > 9.5) & ~d["ns_T"].fillna(True).astype(bool)
    d["FTk"] = np.where(ok_T, d["feps_T"] * np.exp(d["pk_T"].fillna(0.0)), np.nan)
    d["act"] = np.log(d["px_T"] / d["EA"])
    d["year"] = d["month"].dt.year
    d["h"] = h
    return d


def model_by_year(model, wb):
    out = {}
    for (h, Y), g in wb.reset_index().groupby(["h", "年"]):
        m = out.setdefault(int(Y), copy.deepcopy(model))
        for r in g.itertuples(index=False):
            key = GKEY.get(r.組別)
            spec = r.方法
            if key is None or spec not in m["h"][str(h)]["beta"]:
                continue
            vals = [v for v in (r.b0, r.b1, r.b2, r.b3) if pd.notna(v)]
            if len(vals) == len(m["h"][str(h)]["beta"][spec][key]):       # 那一年估不出來（NaN）就保留正式版
                m["h"][str(h)]["beta"][spec][key] = vals
    return out


def run(d, h, model, gm, wb_models):
    rows = []
    for r in d.itertuples(index=False):
        Y = int(r.year)
        if Y < 2017 or Y not in wb_models or (h != 6 and str(Y) not in gm["by_year"][str(h)]):
            continue
        mY = wb_models[Y]
        grp = r.grp if r.grp in orbit.GNAME else "other"
        row = dict(px=float(r.px), eps0=float(r.eps0), y10=float(r.y10), dy=float(r.dy) if np.isfinite(r.dy) else 0.0,
                   vol36=float(r.vol36) if np.isfinite(r.vol36) else np.nan, grp=grp)
        e0, F0k, EA = float(r.eps0), float(r.F0k), float(r.EA)
        pe1 = float(r.px_T) / EA
        lg = lambda o, ea=None: np.log(o["px"] / (ea if ea else o["eps_a"]) / pe1) if o else np.nan    # noqa: E731
        out = dict(ticker=r.ticker, month=r.month, T=r.T, year=Y, h=h, grp=orbit.GNAME[grp], sector=r.sector, vol36=row["vol36"],
                   act=r.act, U=np.log(row["px"] / e0 / pe1), epsg=np.log(EA / e0))
        if h == 6:
            u = unified.predict(row, h, model=mY, gm=gm, cq={}, cons_a=F0k, year=None)
            out.update(C=lg(u), ga_c=np.log(F0k / e0), eps_err=np.log(F0k / EA))
            oa = orbit.predict(row, h, mY, EA, None, F0k, None)
            out.update(A_o=np.log(oa["px"] / EA / pe1))
            rows.append(out)
            continue
        # 共識模式的 EPS_a：12 個月＝F_0；24 個月不外推（＝F_0；§22.5、§25：延一年會高估；網頁有下一財年共識時用分析師的，§25.2 誤差相近）
        gt12 = gm["by_year"]["12"][str(Y)]["gt_hat"]
        G0 = float(np.clip(np.log(F0k / e0), -1.5, 1.5))
        ca = F0k
        kw = dict(model=mY, gm=gm, cq={}, cons_a=ca, cons_b=None, fwd0=F0k, year=Y)
        uC = unified.predict(row, h, **kw)
        out.update(C=lg(uC), ga_c=np.log(ca / e0), eps_err=np.log(ca / EA), gt_cons=uC["gt_cons"])
        if h == 24:                                      # 對照：第二年用回歸的成長延長
            ca2 = F0k * np.exp(gt12[0] + gt12[1] * G0)
            out["C_ext"] = lg(unified.predict(row, h, model=mY, gm=gm, cq={}, cons_a=ca2, cons_b=None, fwd0=F0k, year=Y))
        # 成長定價（回歸）：和 §25.1 一樣
        ea_r = F0k if h == 12 else F0k * np.exp(gt12[0] + gt12[1] * G0)
        gr = GP.predict(row, h, ea_r, GP.eps_b_hat(gm, h, ea_r, e0, F0k, year=Y), F0k, float(r.ret12) if np.isfinite(r.ret12) else None, model=mY, gm=gm, year=Y)
        out["Gr"] = lg(gr, ea_r)
        cb = uC["eps_b"]
        c = GP.coefs(gm, h, grp, Y)
        r12 = float(r.ret12) if np.isfinite(r.ret12) else None
        # A：猜對 EPS_a 與「目標日時市場對下一年的預期」
        if np.isfinite(r.FTk) and r.FTk > 0:
            FTk = float(r.FTk)
            gt_mkt = float(np.log(FTk / EA))
            uA = unified.predict(row, h, eps_a=EA, eps_b=FTk, eb_kind="market", **kw)      # 統一：EPS_b＝市場預期 → 成長定價係數
            gA = GP.predict(row, h, EA, FTk, F0k, r12, model=mY, gm=gm, year=Y)
            oA = unified.predict(row, h, eps_a=EA, eps_b=FTk, eb_kind="fund", **kw)        # 把市場預期當基本面預估（軌道 β_sb）
            oAr = orbit.predict(row, h, mY, EA, None, None, None)
            out.update(A_u=lg(uA), A_g=lg(gA, EA), A_o=lg(oA), A_or=np.log(oAr["px"] / EA / pe1))
            # A1：只猜對 EPS_a（沒有別的看法）＝統一（軌道 β_sa，EPS_b＝共識）
            uA1 = unified.predict(row, h, eps_a=EA, **kw)
            gA1 = GP.predict(row, h, EA, cb, F0k, r12, model=mY, gm=gm, year=Y)
            out.update(A1_u=lg(uA1), A1_g=lg(gA1, EA))
        # B：猜對 EPS_a 與 EPS_b 的實現值（基本面預估對了）＝統一（軌道 β_sa、β_sb）
        if np.isfinite(r.EB) and r.EB > 0:
            EB = float(r.EB)
            uB = unified.predict(row, h, eps_a=EA, eps_b=EB, eb_kind="fund", **kw)
            gB = GP.predict(row, h, EA, EB, F0k, r12, model=mY, gm=gm, year=Y)
            mB = unified.predict(row, h, eps_a=EA, eps_b=EB, eb_kind="market", **kw)      # 把基本面預估當市場預期（錯的用法）
            out.update(B_u=lg(uB), B_g=lg(gB, EA), B_m=lg(mB))
        rows.append(out)
    return pd.DataFrame(rows)


def table(o, cols, title):
    say(f"-- {title}")
    tech = o["grp"] != "非科技"
    hdr = f"  {'':14s}" + "".join(f"{nm:>14s}" for _, nm in cols)
    say(hdr)
    for lab, m in (("全部", o["grp"].notna()), ("科技", tech), ("非科技", ~tech)):
        ok = o[[c for c, _ in cols]].notna().all(axis=1) & m
        say(f"  {lab:6s} n={int(ok.sum()):5d}" + "".join(f"{med(o.loc[ok, c]):14.3f}" for c, _ in cols))
    ok = o[[c for c, _ in cols]].notna().all(axis=1)
    yrs = sorted(o.loc[ok, "year"].unique())
    best = {nm: 0 for _, nm in cols}
    for y in yrs:
        m = ok & (o["year"] == y)
        vals = {nm: med(o.loc[m, c]) for c, nm in cols}
        best[min(vals, key=vals.get)] += 1
    say("  逐年最準的次數：" + "、".join(f"{k} {v}" for k, v in best.items()) + f"（{len(yrs)} 年）")
    say("  誤差在 ±20% 內：" + "、".join(f"{nm} {np.mean(np.abs(np.exp(o.loc[ok, c]) - 1) <= 0.2):.0%}" for c, nm in cols))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    b = pd.read_pickle(a.build)
    if "pk" not in b:
        import usage_backtest as UB                      # noqa: E402
        b["pk"] = UB.correction_wf(b)
    x = pd.read_pickle(os.path.join(a.cache, "orbit_x2.pkl"))
    model = orbit.load_model()
    gm = GP.load()
    wb = pd.read_csv(os.path.join(RES, "orbit_beta.csv"))
    wb_models = model_by_year(model, wb)
    allo = []
    for h in (6, 12, 24):
        d = pairs(b, x, h)
        o = run(d, h, model, gm, wb_models)
        allo.append(o)
        say(f"\n==================== {h} 個月：{len(o):,} 組（{o['ticker'].nunique()} 家；起點 {o['month'].min():%Y-%m}～{o['month'].max():%Y-%m}，走動式係數 2017 年起）")
        say(f"  共識 EPS_a 的誤差中位 |ln(共識 ÷ 實際)| {med(o['eps_err']):.3f}")
        if h == 6:
            table(o, [("U", "本益比不變"), ("C", "統一（＝軌道）"), ("A_o", "猜對：軌道")], "C 只有共識 ｜ A 猜對 EPS_a（6 個月只有軌道）")
        else:
            cols = [("U", "本益比不變"), ("C", "統一（＝軌道）"), ("Gr", "成長定價（回歸）")] + ([("C_ext", "統一（第二年延回歸）")] if h == 24 else [])
            table(o, cols, "C 只有共識（事前）" + ("；統一的 24 個月 EPS_a 不外推" if h == 24 else ""))
            table(o, [("A_u", "統一（EPS_b＝市場預期）"), ("A_g", "成長定價"), ("A_o", "統一（當基本面＝軌道）"), ("A_or", "軌道（原始成長a）")],
                  "A 猜對 EPS_a 與「目標日時市場對下一年的預期」")
            table(o, [("B_u", "統一（基本面＝軌道）"), ("B_g", "成長定價"), ("B_m", "統一（誤標成市場預期）")], "B 猜對 EPS_a、EPS_b 的實現值（基本面預估對）")
            table(o, [("A1_u", "統一（＝軌道，EPS_b＝共識）"), ("A1_g", "成長定價（EPS_b＝共識）")], "A1 只猜對 EPS_a")
        # 相對誤差與相對名次
        rel = o["C"] - o.groupby("month")["C"].transform("median")
        say(f"  相對誤差（扣同月中位）：統一 {med(rel):.3f}（絕對 {med(o['C']):.3f}）；本益比不變 {med(o['U'] - o.groupby('month')['U'].transform('median')):.3f}（絕對 {med(o['U']):.3f}）")
        # 相對名次：每個起點月，預測的 ln 本益比（＝誤差＋實際）對實際的 Spearman；本益比不變＝今天的本益比對實際
        rk = lambda c: [spearman((g[c] + g["act"]).to_numpy(float), g["act"].to_numpy(float)) for _, g in o.groupby("month") if len(g) >= 15]  # noqa: E731
        s_u, s_0 = rk("C"), rk("U")
        say(f"  每個起點月，預測 ln 本益比 vs 實際的 Spearman 中位：統一 {np.nanmedian(s_u):.2f}、本益比不變 {np.nanmedian(s_0):.2f}（{len(s_u)} 個月）")
    o = pd.concat(allo, ignore_index=True)
    o.to_csv(os.path.join(RES, "unified_rows.csv.gz"), index=False, float_format="%.5g", compression=dict(method="gzip", mtime=0))   # 位元組可重現
    open(os.path.join(RES, "unified_lab.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
