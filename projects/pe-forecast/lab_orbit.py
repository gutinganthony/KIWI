#!/usr/bin/env python3
"""本益比軌道＋看法修正：走動式回測（README §16）。

    python3 lab_orbit.py --cache <暫存目錄>      # 第一次約 10 分鐘（會訓練樹模型：不要和其他訓練程式同時跑）

模型：h 個月後股價 ＝ 軌道 × exp(調整)；本益比 ＝ 股價 ÷ h 個月後那時已公布的最近四季 EPS（h＝6、12、24）
  軌道（Leibowitz）：市場看法不變時，股價照資金成本漲、扣掉股利：今天股價 × exp((r − 股利殖利率) × h/12)，r＝10 年期＋5%
  兩個 EPS：a＝h 個月後（本益比的分母）；b＝再 12 個月後（h 個月時市場看的「下一年」）
  調整的寫法（β 依公司類型、預測距離分開估；只用同月份、同類公司之間的差異估，不學大盤）：
    原始成長：β × ln(你的 EPS ÷ 今天的 EPS)                              ← 沒有共識 EPS 時用
    預期＋修正：β_e × 市場預期的成長 ＋ β_s × ln(你的 EPS ÷ 市場預期)     ← 有共識 EPS 時用
回測沒有歷史共識，「市場預期」用代理：每年 1 月只用當時已揭曉的資料訓練的 EPS 成長預測（樹模型；線索含本益比本身）。
「你的 EPS」＝事後實際公布的 EPS（完全正確的上限），另測 EPS 有誤差時。
期間：選模期＝預測起點 2015–2021；保留期＝2022 以後。12 個月的保留期另外用 lab_orbit_recent.py 延伸到起點 2025-09。
輸出：results/orbit.txt、orbit_scores.csv、orbit_beta.csv、orbit_years.csv、orbit_predictions.csv.gz
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
from pef import cond, lab                                # noqa: E402
from pef.load import panel_sp500                         # noqa: E402
from pef.stats import huber_ols                          # noqa: E402

RES = os.path.join(HERE, "results")
GROUPS = {"software": "growth", "internet": "growth", "semis": "cyclical", "semicap": "cyclical", "memory": "cyclical",
          "hardware": "tech_other", "itservices": "tech_other", "gics_it": "tech_other"}
GNAME = {"cyclical": "半導體／設備／記憶體", "growth": "軟體／網路", "tech_other": "其他科技", "other": "非科技"}
HS = (6, 12, 24)
PAIR = {6: (6, 18), 12: (12, 24), 24: (24, 36)}          # 預測距離 h → (a, b)：用到哪兩個時點的 EPS
EPS_H = (6, 12, 18, 24, 36)
EXP_FEATS = ["ln_pe", "pe_rel_sec", "ey_ttm", "ln_ps", "g_rev", "acc", "g_qoq", "gap", "m_ttm", "m_bar", "sigma", "ln_mc",
             "dy", "lev", "ret6", "ret12", "vol36", "sector_id", "past_g"]
GBM = dict(loss="absolute_error", learning_rate=0.05, max_iter=250, max_leaf_nodes=15, min_samples_leaf=100,
           l2_regularization=1.0, random_state=0)
SEL, HOLD = ("2015-01-01", "2021-12-31"), ("2022-01-01", "2026-12-31")
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def tgt_end(v, h):
    return v["month"] + pd.DateOffset(months=h) + pd.offsets.MonthEnd(0)


def specs_for(h):
    a, b = PAIR[h]
    return {"原始成長a": ([f"g{a}"], a), "原始成長ab": ([f"g{a}", f"g{b}"], b), "修正a": ([f"s{a}"], a),
            "預期＋修正a": ([f"e{a}", f"s{a}"], a), "預期＋修正ab": ([f"e{a}", f"e{b}", f"s{a}", f"s{b}"], b),
            "預期b＋修正ab": ([f"e{b}", f"s{a}", f"s{b}"], b)}      # 預期只用 b（e_a、e_b 高度相關，一起放係數會互相抵銷）


def prepare(c):
    x = c.copy()
    x["grp"] = x["sector"].map(GROUPS).fillna("other")
    x["r"] = x["y10"] + cond.ERP
    x["orbit_lr"] = x["r"] - x["dy"].fillna(0)                       # 軌道：每年 ln 股價報酬的預期
    for h in HS:
        x[f"y{h}"] = x[f"rp_{h}"] - x["orbit_lr"] * h / 12              # 實際偏離軌道
    ok0 = x["eps0"] > 0
    for k in EPS_H:
        x[f"g{k}"] = pd.Series(np.where(ok0 & (x[f"eps_f{k}"] > 0), np.log(x[f"eps_f{k}"] / x["eps0"]), np.nan),
                               index=x.index).clip(-2, 2)
    lag = x.groupby("ticker")["eps0"].shift(12)                      # 過去 12 個月的 EPS 成長（月面板，同一家公司）
    x["past_g"] = np.where(ok0 & (lag > 0), np.log(x["eps0"] / lag), np.nan)
    return x


def expectation(x, target, h, start=2012, end=2025, log=None):
    """「市場預期」的代理：每年 1 月只用 t+h 已揭曉的配對，訓練 ln(EPS_{t+h} ÷ EPS_t) 的預測；回傳每列的樣本外預測。"""
    out = pd.Series(np.nan, index=x.index)
    feats = [f for f in EXP_FEATS if f in x]
    for Y in range(start, end + 1):
        cutoff = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        tr = x[(tgt_end(x, h) <= cutoff) & x[target].notna()]
        te = x[(x["month_end"] > cutoff) & (x["month_end"] <= cutoff + pd.DateOffset(months=12)) & (x["eps0"] > 0)]
        if len(tr) < 2000 or te.empty:
            continue
        assert (tgt_end(tr, h) <= cutoff).all() and (te["avail"] <= te["month_end"]).all()
        X = tr[feats].to_numpy(float)
        X[~np.isfinite(X)] = np.nan
        m = HistGradientBoostingRegressor(**GBM).fit(X, tr[target].to_numpy(float))
        Xt = te[feats].to_numpy(float)
        Xt[~np.isfinite(Xt)] = np.nan
        out.loc[te.index] = m.predict(Xt)
    if log:
        log(f"  市場預期代理 {target}：完成（{int(out.notna().sum()):,} 筆樣本外預測）")
    return out


def beta_fit(d, ycol, cols):
    """同月份去平均（只用公司之間的差異）後，Huber 迴歸 y ~ cols（沒有截距：不學大盤）。"""
    d = d.dropna(subset=[ycol] + cols)
    if len(d) < 300:
        return np.full(len(cols), np.nan)
    yy = d[ycol] - d.groupby("month")[ycol].transform("median")
    X = np.column_stack([d[c] - d.groupby("month")[c].transform("median") for c in cols])
    return huber_ols(X, yy.to_numpy(float))


def walk_beta(x, h, start=2015, end=2025):
    """每年 1 月、每個公司類型各自重估 β；只用答案已揭曉的配對（用到 b 時點 EPS 的寫法要 t+b 已揭曉）。"""
    ycol, specs = f"y{h}", specs_for(h)
    preds = {k: pd.Series(np.nan, index=x.index) for k in specs}
    betas = []
    for Y in range(start, end + 1):
        cutoff = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        te_all = x[(x["month_end"] > cutoff) & (x["month_end"] <= cutoff + pd.DateOffset(months=12))]
        for name, (cols, mat) in specs.items():
            tr_all = x[(tgt_end(x, max(h, mat)) <= cutoff)]
            for g in GNAME:
                b = beta_fit(tr_all[tr_all["grp"] == g], ycol, cols)
                te = te_all[te_all["grp"] == g]
                if np.all(np.isfinite(b)):
                    preds[name].loc[te.index] = np.column_stack([te[c] for c in cols]) @ b
                betas.append(dict(h=h, 年=Y, 方法=name, 組別=GNAME[g], 線索="、".join(cols),
                                  β="、".join(f"{v:+.3f}" for v in b), **{f"b{i}": v for i, v in enumerate(b)}))
    return preds, betas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    pk = os.path.join(a.cache, "orbit_x2.pkl")
    if os.path.exists(pk):
        x = pd.read_pickle(pk)
    else:
        df, qf = panel_sp500()
        x = prepare(cond.build(lab.build(df, qf), df))
        for k in EPS_H:
            x[f"e{k}"] = expectation(x, f"g{k}", k, log=say)
        x.to_pickle(pk)
    for k in EPS_H:
        x[f"s{k}"] = (x[f"g{k}"] - x[f"e{k}"]).clip(-2, 2)             # 看法修正（回測裡你的 EPS＝實際）
    x = x[x["month"] >= "2012-01-01"].copy()
    say(f"樣本：{x['ticker'].nunique()} 家、{len(x):,} 個公司月（S&P 500，2012 起）")

    v = x[x["y12"].notna() & x["g12"].notna() & x["e12"].notna()]
    say(f"\n== 1. 市場預期代理（12 個月）：ln EPS 成長的中位 |誤差| {np.median(np.abs(v['g12'] - v['e12'])):.3f}"
        f"（假設 EPS 不變 {np.median(np.abs(v['g12'])):.3f}）")

    betas = []
    for h in HS:
        p, b = walk_beta(x, h)
        betas += b
        for k, s in p.items():
            x[f"p{h}_{k}"] = s
    betas = pd.DataFrame(betas)
    say("\n== 2. 最新一次（2025 年 1 月）估出的 β（EPS 多 10% → 股價約 β×10%；係數順序同「線索」欄）")
    say(betas[betas["年"] == 2025][["h", "方法", "組別", "線索", "β"]].to_string(index=False))

    pc = pd.read_csv(os.path.join(RES, "cond_predictions.csv.gz"), usecols=["ticker", "h", "origin", "xs", "xs2", "actual"],
                     parse_dates=["origin"]).rename(columns={"origin": "month"})
    rows, z12 = [], None
    for h in HS:
        aa = PAIR[h][0]
        z = x.merge(pc[pc["h"] == h][["ticker", "month", "xs", "xs2", "actual"]], on=["ticker", "month"], how="left")
        z["e_unch"] = z[f"g{aa}"] - z[f"rp_{h}"]
        z["e_orbit"] = -z[f"y{h}"]
        for k in specs_for(h):
            z[f"e_{k}"] = z[f"p{h}_{k}"] - z[f"y{h}"]
        z["e_xs"], z["e_xs2"] = z["xs"] - z["actual"], z["xs2"] - z["actual"]
        for per, rng in (("選模期 2015–2021", SEL), ("保留期 2022 以後", HOLD)):
            base = z[(z["month"] >= rng[0]) & (z["month"] <= rng[1]) & z[f"y{h}"].notna() & z[f"g{aa}"].notna()]
            for need, label, meths in (
                    (["e_原始成長a", "e_預期＋修正a", "e_xs"], "只需 a 時點 EPS",
                     ["unch", "orbit", "原始成長a", "修正a", "預期＋修正a", "xs"]),
                    (["e_原始成長ab", "e_預期＋修正ab", "e_預期b＋修正ab"], "也有 b 時點 EPS",
                     ["unch", "orbit", "原始成長a", "原始成長ab", "預期＋修正a", "預期＋修正ab", "預期b＋修正ab", "xs", "xs2"])):
                for g in list(GNAME) + ["科技", "全部"]:
                    d = base if g == "全部" else base[base["grp"] != "other"] if g == "科技" else base[base["grp"] == g]
                    d = d.dropna(subset=need)
                    if len(d) < 100:
                        continue
                    r = {"h": h, "期間": per, "樣本": label, "組別": GNAME.get(g, g), "n": len(d)}
                    for m in meths:
                        e = d[f"e_{m}"].to_numpy(float)
                        if np.isfinite(e).mean() > 0.95:
                            r[m] = float(np.nanmedian(np.abs(e)))
                    rows.append(r)
        if h == 12:
            z12 = z
    sc = pd.DataFrame(rows)
    for h in HS:
        say(f"\n== 3. {h} 個月後股價／本益比的中位 |ln 誤差|（越小越好；同一批列；a＝{PAIR[h][0]} 個月、b＝{PAIR[h][1]} 個月後的 EPS）")
        say(sc[sc["h"] == h].drop(columns="h").round(4).to_string(index=False))

    yr = []
    zz = z12[z12["y12"].notna() & z12["g12"].notna() & z12["p12_原始成長a"].notna() & z12["xs"].notna()]
    for Y, d in zz.groupby(zz["month"].dt.year):
        for g, dd in (("全部", d), ("科技", d[d["grp"] != "other"])):
            if len(dd) < 50:
                continue
            r = {"年": Y, "組別": g, "n": len(dd)}
            for m in ["unch", "orbit", "原始成長a", "預期＋修正a", "xs"]:
                r[m] = float(np.nanmedian(np.abs(dd[f"e_{m}"])))
            r["市場偏離軌道中位"] = float(np.nanmedian(dd["y12"]))
            yr.append(r)
    yr = pd.DataFrame(yr)
    say("\n== 4. 逐年（12 個月，預測起點年）；「市場偏離軌道中位」＝那一年股價比軌道多漲（+）或少漲（−）")
    say(yr.round(3).to_string(index=False))

    rng_ = np.random.default_rng(0)
    hh = zz[zz["month"] >= HOLD[0]].copy()
    b22 = betas[(betas["h"] == 12) & (betas["年"] == 2022) & (betas["方法"] == "原始成長a")].set_index("組別")["b0"]
    bvec = hh["grp"].map({k: b22.get(GNAME[k], np.nan) for k in GNAME}).to_numpy(float)
    say("\n== 5. 你的 EPS 有誤差時（12 個月、保留期；EPS × exp(N(0,σ))；β 用 2022 年版的「原始成長 a」）")
    for sig in (0.0, 0.1, 0.2, 0.3):
        noise = rng_.normal(0, sig, len(hh)) if sig else 0
        say(f"   σ={sig:.1f}：軌道 {np.median(np.abs(hh['y12'])):.4f}  軌道＋原始成長 "
            f"{np.median(np.abs(bvec * (hh['g12'] + noise) - hh['y12'])):.4f}")

    sc.to_csv(os.path.join(RES, "orbit_scores.csv"), index=False, float_format="%.6f")
    betas.to_csv(os.path.join(RES, "orbit_beta.csv"), index=False, float_format="%.6f")
    yr.to_csv(os.path.join(RES, "orbit_years.csv"), index=False, float_format="%.6f")
    keep = (["ticker", "sector", "grp", "month", "px", "eps0", "r", "dy", "orbit_lr", "vol36"]
            + [f"y{h}" for h in HS] + [f"eps_f{k}" for k in EPS_H] + [f"g{k}" for k in EPS_H] + [f"e{k}" for k in EPS_H]
            + [c for c in x.columns if c[:3] in ("p6_", "p12", "p24")])
    x[keep].to_csv(os.path.join(RES, "orbit_predictions.csv.gz"), index=False, float_format="%.6g",
                   compression={"method": "gzip", "mtime": 0})
    open(os.path.join(RES, "orbit.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
