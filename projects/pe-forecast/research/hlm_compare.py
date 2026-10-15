#!/usr/bin/env python3
"""README §28：使用者用 Gemini 做的「美股動態本益比（forward P/E）與目標股價預測系統」（HLM）vs 軌道——同一份 Bloomberg 檔、同一批配對、同一個目標
→ results/hlm_compare.txt、hlm_compare_scores.csv

    python3 research/hlm_compare.py --xlsx <Bloomberg pp2.xlsx> --cache <orbit_x2.pkl 目錄> > results/hlm_compare.txt

HLM 的規格（使用者的 prompt，照抄）：
  PE ＝ 股價 ÷ 未來 12 個月共識 EPS（1BF），只留 E1 > 0.05 且 3 ≤ PE ≤ 150；logPE ＝ ln PE。g1 ＝ ln(E2/E1)、g2 ＝ ln(E3/E2)，截在 [−1, 1.5]。
  站在 t 預測 h 個月後的 logPE 變化：
    dev_own_raw ＝ 個股到 t 為止的歷史平均 logPE − logPE[t]
    dev_own_rel ＝ (大盤中位數 logPE[t] ＋ 個股過去 36 個月相對大盤中位數的平均溢價) − logPE[t]
    dev_sub     ＝ GICS 二級次產業中位數 logPE[t] − logPE[t]
    g_roll      ＝ clip(g1 − 0.5·g2, −0.5, 0.8)
    roic_t      ＝ ROIC[t].fillna(15).clip(−40, 100) ÷ 100
    eps_surprise＝ 0（回測沒有自訂 EPS）
    delta_rf    ＝ 未來 10 年期 − 今天 10 年期（小數）——回測時事前不知道，取 0；另跑「用實際變化」的版本（事後，標成後見之明）
    pred ＝ λ_raw·dev_own_raw ＋ λ_rel·dev_own_rel ＋ λ_sub·dev_sub − γ·g_roll ＋ β_roic·roic_t ＋ β_rev·eps_surprise ＋ (rate_duration × 產業乘數)·delta_rf
    權重固定：h=6 (0.25, 0.15, 0.05, 0.22, 0.08, 0.35, −3.5)；h=12 (0.45, 0.20, 0.08, 0.35, 0.10, 0.45, −4.5)；h=24 (0.70, 0.20, 0.10, 0.45, 0.12, 0.50, −5.5)
    PE_pred ＝ exp(logPE[t] ＋ pred)；目標股價 ＝ 未來 EPS × PE_pred，未來 EPS ＝ 6M sqrt(E1·E2)、12M E2、24M E3（今天的共識）；PE 不變的股價 ＝ 未來 EPS × PE[t]
  分群：Static_Info 前 101 列＝Nasdaq 100，依近 30 日成交金額前 50 ＝「Nasdaq Top 50」、其餘「Other Nasdaq (51-101)」；第 102 列起「S&P 500 (Rest)」。
  使用者說它的走動式回測（2021–2026）MdAPE 約 6M 11.8%、12M 15.1%、24M 18.2%。

這裡放在同一個尺上比（都預測 forward 本益比的變化 Δ ＝ ln PE_T − ln PE_t，目標日 T ＝ t＋h；起點 2021-01 起、T ≤ 2026-09）：
  U        forward 本益比不變（Δ̂ ＝ 0）——HLM 的底
  HLM0     HLM 固定權重、delta_rf ＝ 0（事前）
  HLMr     HLM 固定權重、delta_rf ＝ 實際 10 年期變化（後見之明；只為對照使用者看到的數字）
  HLM-fit  同一組線索，權重每年走動式重估（Huber；只用目標日在該年以前的配對），delta_rf ＝ 0
  Orbit    軌道：股價照資金成本漲（10 年期 ＋ 5% − 股利殖利率），forward 本益比 ＝ 預測股價 ÷ 未來 EPS → Δ̂ ＝ 軌道報酬 − ln(未來 EPS ÷ E1[t])
  HLM+Orb  HLM-fit 的線索再加軌道那一項，一起重估
評分：MdAPE（中位 |PE_pred ÷ PE_T − 1|）、中位 |ln 誤差|、方向命中（Δ̂ 與 Δ 同號；Δ̂＝0 算錯）、目標股價 MdAPE（同一個未來 EPS，所以差別只來自 PE 的預測）；
     80% 區間（走動式 conformal，尺度＝波動^0.7）的涵蓋與寬度。全部、三個分群、逐年。
注意：HLM 的 PE 是 forward（分母＝共識），軌道正式版的本益比是 trailing（分母＝最近四季 GAAP）；forward 本益比平滑得多，所以這裡的誤差數字不能和 README 其他節直接比。
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "research"))
from pef.stats import huber_ols                          # noqa: E402
import bbg_load as BL                                    # noqa: E402

RES = os.path.join(HERE, "results")
W = {6: (0.25, 0.15, 0.05, 0.22, 0.08, 0.35, -3.5), 12: (0.45, 0.20, 0.08, 0.35, 0.10, 0.45, -4.5), 24: (0.70, 0.20, 0.10, 0.45, 0.12, 0.50, -5.5)}
DUR = {"資訊技術": 1.25, "通訊服務": 1.15, "非核心消費": 1.10, "房地產": 1.10, "醫療保健": 1.00, "工業": 0.95, "核心消費": 0.85, "公用事業": 0.80, "原材料": 0.80, "能源": 0.65, "金融": 0.50}
FEATS = ["dev_raw", "dev_rel", "dev_sub", "g_roll", "roic"]
START = pd.Timestamp("2021-01-01")
ERP = 0.05
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def norm(t):
    return str(t).replace("US Equity", "").strip().replace(" ", "-").replace("/", "-")


def load_roic(path, months):
    """5_ROIC：31 個季度（2019-03～2026-09 季末），每列靠右對齊（照 HLM 的規格 dropna → 右對齊），再 ffill 展開成月。"""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = next(w for w in wb.worksheets if w.title.startswith("5_ROIC"))
    rows = list(ws.iter_rows(values_only=True))[1:]
    nq = 31
    qs = pd.date_range("2019-03-01", periods=nq, freq="QS-DEC") if False else pd.date_range("2019-03-01", "2026-09-01", freq="3MS")
    mat = {}
    for r in rows:
        if not isinstance(r[0], str):
            continue
        v = np.array([float(c) if isinstance(c, (int, float)) else np.nan for c in r[1:nq + 1]], float)
        vals = v[np.isfinite(v)]
        out = np.full(nq, np.nan)
        if len(vals):
            out[nq - len(vals):] = vals
        mat[norm(r[0])] = out
    q = pd.DataFrame(mat, index=qs)
    return q.reindex(months, method="ffill")


def groups(info, tick):
    info = info.copy()
    info["ticker"] = info["ticker"].map(norm)
    info = info[info["ticker"].isin(tick) & ~info["ticker"].str.contains("#N/A")].drop_duplicates("ticker")
    info["adv30"] = pd.to_numeric(info["adv30"], errors="coerce")
    info["pos"] = np.arange(len(info))
    ndx = info[info["pos"] < 101].sort_values("adv30", ascending=False)
    g = pd.Series("S&P 500 (Rest)", index=info["ticker"].to_numpy())
    g[ndx["ticker"].iloc[:50]] = "Nasdaq Top 50"
    g[ndx["ticker"].iloc[50:]] = "Other Nasdaq (51-101)"
    return g, info.set_index("ticker")


def build(path, cache):
    d, info = BL.load(path)
    px, f1, f2, f3 = d["px"], d["f1"], d["f2"], d["f3"]
    months = px.index
    tick = [t for t in px.columns if px[t].notna().any() and "#N/A" not in t]
    grp, info = groups(info, tick)
    tick = [t for t in tick if t in grp.index]
    px, f1, f2, f3 = (x[tick] for x in (px, f1, f2, f3))
    roic = load_roic(path, months).reindex(columns=tick)
    pe = px / f1.where(f1 > 0.05)
    lpe = np.log(pe.where((pe >= 3.0) & (pe <= 150.0)))
    g1 = np.log(f2.where(f2 > 0) / f1.where(f1 > 0)).clip(-1.0, 1.5)
    g2 = np.log(f3.where(f3 > 0) / f2.where(f2 > 0)).clip(-1.0, 1.5)
    dev_raw = lpe.expanding(min_periods=1).mean() - lpe
    mkt = lpe.median(axis=1)
    prem = lpe.sub(mkt, axis=0)
    dev_rel = prem.rolling(36, min_periods=12).mean().add(mkt, axis=0) - lpe
    sub = info["gics2"].reindex(tick)
    sub_med = lpe.T.groupby(sub.to_numpy()).transform("median").T
    sub_n = lpe.notna().T.groupby(sub.to_numpy()).transform("sum").T
    dev_sub = (sub_med.where(sub_n >= 3) - lpe).fillna(0.0)
    g_roll = (g1 - 0.5 * g2).clip(-0.5, 0.8).fillna(0.0)
    roic_t = roic.fillna(15.0).clip(-40, 100) / 100.0
    # 10 年期（data/us10y_monthly.csv，%）、股利殖利率（面板 orbit_x2.pkl 對得上的公司；其餘 0）、波動（36 個月月報酬標準差 × √12）
    y10 = pd.read_csv(os.path.join(HERE, "data", "us10y_monthly.csv"), parse_dates=["Date"]).set_index("Date")["Rate"].reindex(months, method="ffill") / 100
    dy = pd.DataFrame(0.0, index=months, columns=tick)
    if cache and os.path.exists(os.path.join(cache, "orbit_x2.pkl")):
        x = pd.read_pickle(os.path.join(cache, "orbit_x2.pkl"))
        pv = x.pivot_table(index="month", columns="ticker", values="dy").reindex(months).ffill()
        common = [t for t in tick if t in pv.columns]
        dy[common] = pv[common].fillna(0.0)
    vol = np.log(px / px.shift(1)).rolling(36, min_periods=12).std() * np.sqrt(12)
    return dict(px=px, f1=f1, f2=f2, f3=f3, lpe=lpe, dev_raw=dev_raw, dev_rel=dev_rel, dev_sub=dev_sub, g_roll=g_roll, roic=roic_t, y10=y10, dy=dy, vol=vol,
                grp=grp.reindex(tick), gics1=info["gics1"].reindex(tick), months=months, tick=tick)


def pairs(D, h):
    """每個起點 t（2021-01 起）、每檔：logPE_t、logPE_T、線索、未來 EPS（今天共識的代理）、實際股價、Δrf 實際、軌道報酬。"""
    lpe = D["lpe"]
    tgt = lpe.shift(-h)
    px_T = D["px"].shift(-h)
    f1, f2, f3 = D["f1"], D["f2"], D["f3"]
    proxy = {6: np.sqrt(f1.where(f1 > 0) * f2.where(f2 > 0)), 12: f2.where(f2 > 0), 24: f3.where(f3 > 0)}[h]
    y10, dy = D["y10"], D["dy"]
    drf = (y10.shift(-h) - y10)
    rows = []
    for t in D["months"]:                                # 全部起點都建（2019 起），評分只用 2021 起（ev）；2019–2020 的配對給走動式估權重、校準區間用
        if t + pd.DateOffset(months=h) > D["months"][-1]:
            continue
        ok = lpe.loc[t].notna() & tgt.loc[t].notna() & proxy.loc[t].notna()
        if not ok.any():
            continue
        k = ok[ok].index
        rows.append(pd.DataFrame(dict(
            t=t, T=t + pd.DateOffset(months=h), ticker=k, h=h, year=t.year, grp=D["grp"].reindex(k).to_numpy(), gics1=D["gics1"].reindex(k).to_numpy(),
            lpe_t=lpe.loc[t, k].to_numpy(), lpe_T=tgt.loc[t, k].to_numpy(), px_T=px_T.loc[t, k].to_numpy(), proxy=proxy.loc[t, k].to_numpy(),
            dev_raw=D["dev_raw"].loc[t, k].fillna(0.0).to_numpy(), dev_rel=D["dev_rel"].loc[t, k].fillna(0.0).to_numpy(), dev_sub=D["dev_sub"].loc[t, k].to_numpy(),
            g_roll=D["g_roll"].loc[t, k].to_numpy(), roic=D["roic"].loc[t, k].to_numpy(), drf=float(drf.loc[t]) if np.isfinite(drf.loc[t]) else 0.0,
            orb=(float(y10.loc[t]) + ERP - dy.loc[t, k].to_numpy()) * h / 12 - np.log(proxy.loc[t, k].to_numpy() / f1.loc[t, k].to_numpy()),
            vol=D["vol"].loc[t, k].to_numpy())))
    d = pd.concat(rows, ignore_index=True)
    d["act"] = d["lpe_T"] - d["lpe_t"]
    d["mult"] = d["gics1"].map(DUR).fillna(1.0)
    d["ev"] = d["t"] >= START
    return d


def hlm_terms(d, h):
    """HLM 各項單獨（固定權重、delta_rf＝0）：看 24 個月的優勢來自哪一項。"""
    lr, ll, ls, gg, br, _, _ = W[h]
    return {"只有 dev_raw": lr * d["dev_raw"], "只有 dev_rel": ll * d["dev_rel"], "只有 dev_sub": ls * d["dev_sub"], "只有 g_roll": -gg * d["g_roll"], "只有 roic": br * d["roic"]}


def hlm(d, h, drf):
    lr, ll, ls, gg, br, _, rd = W[h]
    return lr * d["dev_raw"] + ll * d["dev_rel"] + ls * d["dev_sub"] - gg * d["g_roll"] + br * d["roic"] + rd * d["mult"] * drf


def fit_wf(d, cols):
    """每年 Y 只用目標日 T 在 Y 年以前的配對估（Huber，含截距），預測 Y 年的起點；回傳預測與逐年係數。"""
    pred = pd.Series(np.nan, index=d.index)
    coefs = {}
    for Y in sorted(d["year"].unique()):
        tr = d[d["T"] < pd.Timestamp(f"{Y}-01-01")]
        if len(tr) < 300:
            continue
        X = np.column_stack([np.ones(len(tr))] + [tr[c].to_numpy(float) for c in cols])
        b = huber_ols(X, tr["act"].to_numpy(float))
        te = d["year"] == Y
        Xt = np.column_stack([np.ones(int(te.sum()))] + [d.loc[te, c].to_numpy(float) for c in cols])
        pred[te] = Xt @ b
        coefs[Y] = [float(v) for v in b]
    return pred, coefs


def score(d, col):
    e = d[col] - d["act"]                                # ln(預測 ÷ 實際)
    pe_pred = np.exp(d["lpe_t"] + d[col])
    pe_act = np.exp(d["lpe_T"])
    px_pred = d["proxy"] * pe_pred
    hit = (np.sign(d[col]) == np.sign(d["act"])) & (d[col] != 0)
    return dict(n=len(d), MdAPE_PE=float(np.median(np.abs(pe_pred / pe_act - 1))), 中位ln=float(np.median(np.abs(e))),
                方向=float(hit.mean()), MdAPE_股價=float(np.median(np.abs(px_pred / d["px_T"] - 1))))


def band(d, col, vmed):
    """走動式 80% conformal：每年只用目標日在該年第一個起點以前的誤差校準；尺度＝波動^0.7。回傳涵蓋平均／最低、寬度倍數中位。"""
    e = d["act"] - d[col]
    sc = np.clip(d["vol"].where(np.isfinite(d["vol"]), vmed), 0.1, 1.5) ** 0.7
    cov, widths = [], []
    for Y in sorted(d.loc[d["ev"], "year"].unique()):
        cur = (d["year"] == Y) & d["ev"]
        cal = d["T"] < d.loc[cur, "t"].min()
        if cal.sum() < 200:
            continue
        u = (e[cal] / sc[cal])
        lo, hi = np.quantile(u, [0.1, 0.9])
        cov.append(float(((e[cur] >= lo * sc[cur]) & (e[cur] <= hi * sc[cur])).mean()))
        widths.append((hi - lo) * sc[cur])
    if not cov:
        return None
    w = pd.concat(widths)
    return dict(years=len(cov), 涵蓋=float(np.mean(cov)), 最低=float(np.min(cov)), 倍數=float(np.exp(np.median(w))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--fit", action="store_true", help="同時把軌道的 forward 本益比誤差分位數寫成 results/fwd_pe_band.json（網頁、命令列的 forward 本益比區間）")
    a = ap.parse_args()
    fwd = dict(version="2026-10-15", alpha=0.7, levels=[50, 60, 70, 80, 90],
               note="README §28：軌道的 forward 本益比（預測股價 ÷ 今天共識的那時下一年 EPS）誤差 u＝ln(實際÷預測)÷波動^0.7 的等尾分位，Bloomberg 512 檔 2019–2026 全部起點；"
                    "區間＝forward 本益比 × exp(尺度 × 分位數)；不含 EPS 風險（分母是共識）；wf_cover＝2021 起走動式涵蓋", h={})
    D = build(a.xlsx, a.cache)
    say(f"Bloomberg 檔：{len(D['tick'])} 檔、{D['months'][0]:%Y-%m}～{D['months'][-1]:%Y-%m}；分群 " + "、".join(f"{k} {v}" for k, v in D["grp"].value_counts().items()))
    say(f"forward 本益比有效（E1 > 0.05、3 ≤ PE ≤ 150）：{int(D['lpe'].notna().sum().sum()):,} 個月×檔（佔有股價的 {D['lpe'].notna().sum().sum() / D['px'].notna().sum().sum():.0%}）")
    pd.set_option("display.width", 250)
    allrows = []
    for h in (6, 12, 24):
        d = pairs(D, h)
        d["U"] = 0.0
        d["HLM0"] = hlm(d, h, 0.0)
        d["HLMr"] = hlm(d, h, d["drf"])
        d["Orbit"] = d["orb"]
        d["HLM-fit"], co = fit_wf(d, FEATS)
        d["HLM+Orb"], co2 = fit_wf(d, FEATS + ["orb"])
        terms = hlm_terms(d, h)
        for k, v in terms.items():
            d[k] = v
        vmed = float(d["vol"].median())
        dall = d
        d = d[d["ev"]].copy()                            # 評分：2021 起的起點
        say(f"\n==================== {h} 個月：{len(d):,} 組（起點 {d['t'].min():%Y-%m}～{d['t'].max():%Y-%m}，{d['ticker'].nunique()} 檔；另有 {int((~dall['ev']).sum()):,} 組 2019–2020 起點只用來估權重、校準區間）")
        say(f"  實際 Δ ln forward 本益比：中位 {d['act'].median():+.3f}、中位絕對 {d['act'].abs().median():.3f}；HLM0 預測 Δ 的中位 {d['HLM0'].median():+.3f}（絕對 {d['HLM0'].abs().median():.3f}）")
        methods = ["U", "HLM0", "HLMr", "HLM-fit", "HLM+Orb", "Orbit"]
        # 全部（HLM-fit 有預測的共同樣本）
        common = d["HLM-fit"].notna()
        for lab, m in (("全部（2021 起）", d["HLM-fit"].notna() | True), ("共同樣本（HLM-fit 有係數的年份）", common)):
            dd = d[m]
            say(f"-- {lab}：{len(dd):,} 組，起點 {dd['t'].min():%Y-%m}～{dd['t'].max():%Y-%m}")
            say(f"  {'方法':10s} {'n':>7s} {'MdAPE(PE)':>10s} {'中位|ln|':>9s} {'方向':>6s} {'MdAPE(股價)':>11s}")
            for mth in methods:
                dm = dd[dd[mth].notna()]
                if dm.empty:
                    continue
                s = score(dm, mth)
                say(f"  {mth:10s} {s['n']:7,d} {s['MdAPE_PE']:10.1%} {s['中位ln']:9.3f} {s['方向']:6.0%} {s['MdAPE_股價']:11.1%}")
                if lab.startswith("全部"):
                    allrows.append(dict(h=h, 樣本="全部", 方法=mth, **s))
        # 分群
        say("-- 分群（全部 2021 起）：MdAPE(PE)／方向")
        for g in ("Nasdaq Top 50", "Other Nasdaq (51-101)", "S&P 500 (Rest)"):
            dg = d[d["grp"] == g]
            cells = []
            for mth in methods:
                dm = dg[dg[mth].notna()]
                s = score(dm, mth) if len(dm) else None
                cells.append(f"{mth} {s['MdAPE_PE']:.1%}／{s['方向']:.0%}" if s else f"{mth} —")
                if s:
                    allrows.append(dict(h=h, 樣本=g, 方法=mth, **s))
            say(f"  {g:22s} n={len(dg):6,d}  " + "  ".join(cells))
        # 逐年
        say("-- 逐年 MdAPE(PE)：U／HLM0／HLM-fit／Orbit")
        for Y, dy_ in d.groupby("year"):
            cells = []
            for mth in ("U", "HLM0", "HLM-fit", "Orbit"):
                dm = dy_[dy_[mth].notna()]
                cells.append(f"{score(dm, mth)['MdAPE_PE']:.1%}" if len(dm) else "—")
            say(f"  {Y} n={len(dy_):6,d}  " + "／".join(cells))
        # HLM 各項單獨
        say("-- HLM 各項單獨（固定權重）：MdAPE(PE)／方向（全部 2021 起）")
        say("  " + "  ".join(f"{k} {score(d, k)['MdAPE_PE']:.1%}／{score(d, k)['方向']:.0%}" for k in terms))
        # 區間（校準可用 2019 起的配對）
        say("-- 80% 區間（走動式 conformal，尺度＝波動^0.7；校準含 2019–2020 起點的配對）：涵蓋 平均／最低、高 ÷ 低 中位")
        for mth in methods:
            dm = dall[dall[mth].notna()]
            b = band(dm, mth, vmed)
            if b:
                say(f"  {mth:10s} {b['years']} 年  涵蓋 {b['涵蓋']:.2f}／{b['最低']:.2f}  倍數 {b['倍數']:.2f}")
        say("-- HLM-fit 走動式係數 [常數, dev_raw, dev_rel, dev_sub, g_roll, roic]（固定權重對照：" + ", ".join(f"{v:+.2f}" for v in (W[h][0], W[h][1], W[h][2], -W[h][3], W[h][4])) + "）")
        for Y, c in co.items():
            say(f"  {Y}: " + ", ".join(f"{v:+.3f}" for v in c))
        say("-- HLM+Orb 走動式係數（最後一欄＝軌道項）")
        for Y, c in co2.items():
            say(f"  {Y}: " + ", ".join(f"{v:+.3f}" for v in c))
        if a.fit:                                        # 軌道的 forward 本益比區間：全部配對（2019 起）的 u 分位數；涵蓋用 2021 起的走動式
            e = dall["act"] - dall["Orbit"]
            sc = np.clip(dall["vol"].where(np.isfinite(dall["vol"]), vmed), 0.1, 1.5) ** 0.7
            u = (e / sc).to_numpy(float)
            wf = {}
            for L in (50, 60, 70, 80, 90):
                a_ = (1 - L / 100) / 2
                cov = []
                for Y in sorted(d["year"].unique()):
                    cur = (dall["year"] == Y) & dall["ev"]
                    cal = dall["T"] < dall.loc[cur, "t"].min()
                    if cal.sum() < 200:
                        continue
                    lo, hi = np.quantile((e[cal] / sc[cal]), [a_, 1 - a_])
                    cov.append(float(((e[cur] >= lo * sc[cur]) & (e[cur] <= hi * sc[cur])).mean()))
                wf[str(L)] = dict(avg=round(float(np.mean(cov)), 3), min=round(float(np.min(cov)), 3)) if cov else None
            fwd["h"][str(h)] = dict(n=int(len(dall)), months=[str(dall["t"].min().date()), str(dall["t"].max().date())], vol_median=vmed,
                                    q={str(L): [float(v) for v in np.quantile(u, [(1 - L / 100) / 2, 1 - (1 - L / 100) / 2])] for L in (50, 60, 70, 80, 90)},
                                    median=float(np.median(u)), mdape=round(score(d, "Orbit")["MdAPE_PE"], 4), wf_cover=wf)
            say(f"-- forward 本益比區間（軌道，寫入 fwd_pe_band.json）：80% 分位 [{fwd['h'][str(h)]['q']['80'][0]:+.3f}, {fwd['h'][str(h)]['q']['80'][1]:+.3f}]，"
                f"走動式涵蓋 " + "、".join(f"{L}% {v['avg']:.2f}／{v['min']:.2f}" for L, v in wf.items() if v))
    pd.DataFrame(allrows).to_csv(os.path.join(RES, "hlm_compare_scores.csv"), index=False)
    open(os.path.join(RES, "hlm_compare.txt"), "w").write(buf.getvalue())
    if a.fit:
        import json
        json.dump(fwd, open(os.path.join(RES, "fwd_pe_band.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
