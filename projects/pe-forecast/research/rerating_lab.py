#!/usr/bin/env python3
"""README §24：模型能不能估「市場給新的本益比」？——把成長預期放進本益比（重新評價）

    python3 research/rerating_lab.py --build <lab_eps_correction.py 的 L.build pickle> > results/rerating_lab.txt

問題：軌道模型的股價對 EPS 的反應很小（β 0.05–0.2），EPS 調高 → 股價幾乎不動 → 本益比下降。
  但市場其實是「對明年的 EPS 給一個倍數」：同一個月橫斷面，ln(本益比) 對 ln(明年共識 ÷ 今年 EPS) 的斜率約 1.0。
  所以目標日的本益比 ＝ 目標日的 forward 本益比 × (目標日時市場預期的明年 EPS ÷ 目標日的最近四季 EPS)。
  → 只要你給「目標日時的成長預期」，本益比就會跟著成長重新評價。
資料：I/B/E/S 本財年共識（OSAP FEPS，距離年報 10.5–12 個月時 ≈ 未來 12 個月）、長期成長共識 LTG（fgr5y）、S&P 500 面板。
  配對：起點 t（距離年報 10.5–12 個月）↔ 目標日 T＝t＋h（h＝12、24；T 那時也剛換到下一個財年，FY1 ≈ T 之後 12 個月）。
  EPS_a＝T 的最近四季 GAAP EPS（實際）；F_T＝T 時的共識（市場在目標日對下一年的預期）；EPS_b 實現值＝T＋12 的最近四季 EPS。
寫法（預測 ln 目標日本益比；β 都是走動式、起點那一年的版本）：
  U   本益比不變
  O_a 軌道（正式版「原始成長a」）：只用 EPS_a
  O_ab 軌道「原始成長ab」：EPS_a ＋ EPS_b（b 用 F_T，或實現值）
  F   forward 倍數不變：ln(今天股價 ÷ 今天共識) ＋ ln(F_T ÷ EPS_a)
  R   重新評價（走動式迴歸）：Δ ln forward 本益比 ＝ a ＋ b1 × 今天 forward 本益比相對同月中位的溢價（回歸）
        ＋ b2 × 近期成長預期的變化 ΔG（G＝ln(下一年 ÷ 最近四季)）＋ b3 × 今年交出的 vs 預期 ln(EPS_a ÷ 今天共識)［＋ b4 × ΔLTG］
      ln 本益比_T ＝ ln forward 本益比_0 ＋ 預測的 Δ ＋ G_T。每年 1 月只用目標日在前一年底以前的配對估（Huber），依組別估或全部一起。
  輸入有三種：A＝「你猜中了目標日的市場預期」（F_T 用當時的共識）；B＝「你猜中了基本面」（F_T 換成 EPS_b 實現值）；
  C＝「沒有額外看法」：EPS_a＝今天共識、目標日的下一年預期＝今天共識 × 隱含成長（和軌道模型同樣的事前資訊）。
評分：中位 |ln 本益比誤差|；全部、2022 以後、科技、半導體類、成長加速（ΔG > 0.15）、大幅重新評價（實際 |Δ ln forward 本益比| > 0.3）。
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from pef.stats import huber_ols                          # noqa: E402

RES = os.path.join(HERE, "results")
GNAME = {"cyclical": "半導體／設備／記憶體", "growth": "軟體／網路", "tech_other": "其他科技", "other": "非科技"}
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def pairs(b, h):
    t = b[(b["lead"] > 10.5) & (b["lead"] <= 12.0) & ~b["near_split"]].copy()
    t["T"] = t["month"] + pd.DateOffset(months=h)
    cols = ["ticker", "month", "px", "eps0", "feps", "fgr5y", "lead", "near_split", "pk"]
    T = b[cols].rename(columns={c: c + "_T" for c in cols if c != "ticker"}).rename(columns={"month_T": "T"})
    d = t.merge(T, on=["ticker", "T"], how="inner")
    d = d[(d["lead_T"] > 9.5) & ~d["near_split_T"] & (d["eps0"] > 0) & (d["feps"] > 0) & (d["eps0_T"] > 0) & (d["feps_T"] > 0)
          & (d["month"] >= "2012-01-01")].copy()
    d["h"] = h
    d["EA"] = d["eps0_T"]
    d["EB"] = d[f"eps_f{h + 12}"] if f"eps_f{h + 12}" in d else np.nan
    d["act"] = np.log(d["px_T"] / d["EA"])
    d["lfpe0"] = np.log(d["px"] / d["feps"])
    d["lfpeT"] = np.log(d["px_T"] / d["feps_T"])                 # forward 本益比（用共識原值，只拿來分組）
    d["prem0"] = d["lfpe0"] - d.groupby("month")["lfpe0"].transform("median")
    # 共識換成預期的 GAAP（正式版的共識校正，走動式重訓；2025 年的列沒有係數 → 原樣），和網頁上 EPS_a／EPS_b 的口徑一致
    d["F0k"] = d["feps"] * np.exp(d["pk"].fillna(0.0))
    d["FTk"] = d["feps_T"] * np.exp(d["pk_T"].fillna(0.0))
    d["G0"] = np.log(d["F0k"] / d["eps0"]).clip(-1.5, 1.5)
    d["GT"] = np.log(d["FTk"] / d["EA"]).clip(-1.5, 1.5)
    d["GTr"] = np.log(d["EB"] / d["EA"]).where(d["EB"] > 0).clip(-1.5, 1.5)
    d["sur"] = np.log(d["EA"] / d["feps"]).clip(-1.5, 1.5)
    d["dltg"] = ((d["fgr5y_T"] - d["fgr5y"]) / 100).clip(-0.5, 0.5)
    d["year"] = d["month"].dt.year
    return d


def walk(d, cols, target, by_group=True, known_lag=0):
    """每個起點年份 Y：只用「目標日＋known_lag 個月」在 Y 年以前的配對估 Huber 迴歸（含截距）；回傳預測的 target。
    known_lag：線索要到目標日之後才揭曉時（B 用 T＋12 的實現 EPS）設 12，訓練資料才不會用到 Y 年以後才知道的數字。"""
    pred = pd.Series(np.nan, index=d.index)
    coefs = []
    for Y in range(2015, 2025):
        tr = d[(d["T"] + pd.DateOffset(months=known_lag) < pd.Timestamp(f"{Y}-01-01"))].dropna(subset=cols + [target])
        te = d[d["year"] == Y].dropna(subset=cols)
        if len(tr) < 300 or te.empty:
            continue
        groups = list(GNAME) if by_group else [None]
        for g in groups:
            trg = tr if g is None else tr[tr["grp"] == g]
            if g is not None and len(trg) < 150:
                trg = tr                                 # 組別樣本太少就用全部
            teg = te if g is None else te[te["grp"] == g]
            if teg.empty:
                continue
            X = np.column_stack([np.ones(len(trg))] + [trg[c].to_numpy(float) for c in cols])
            co = huber_ols(X, trg[target].to_numpy(float))
            Xt = np.column_stack([np.ones(len(teg))] + [teg[c].to_numpy(float) for c in cols])
            pred.loc[teg.index] = Xt @ co
            coefs.append(dict(年=Y, 組別=GNAME.get(g, "全部"), n=len(trg), **{k: v for k, v in zip(["截距"] + cols, co)}))
    return pred, pd.DataFrame(coefs)


def decompose(b):
    """§24.2：forward 本益比的變化（倍數重新評價）拆成大盤、產業、個股，和成長預期的關係。共識用原值（不需要校正）。"""
    for h in (12, 24):
        d = pairs(b, h)
        d["dfpe"] = d["lfpeT"] - d["lfpe0"]
        d = d[d["dfpe"].abs() < 2].copy()
        mk = d.groupby("month")["dfpe"].transform("median")
        sec = d.groupby(["month", "sector"])["dfpe"].transform("median")
        d["mkt"], d["sec"], d["idio"] = mk, sec - mk, d["dfpe"] - sec
        v = d["dfpe"].var()
        d["rev"] = np.log(d["feps_T"] / d["feps"])                  # 這段期間明年 EPS 預估的變化
        sp = lambda a, c: float(d[[a, c]].dropna().corr(method="spearman").iloc[0, 1])  # noqa: E731
        s = d.groupby(["month", "sector"]).agg(dfpe=("dfpe", "median"), rev=("rev", "median"), n=("dfpe", "size")).reset_index()
        s = s[s["n"] >= 4]
        for c in ("dfpe", "rev"):
            s[c] = s[c] - s.groupby("month")[c].transform("median")
        m = d.groupby("month").agg(dfpe=("dfpe", "median"), rev=("rev", "median"))
        d["y"] = d["dfpe"] - mk
        say(f"  {h} 個月（{len(d):,} 組）：forward 本益比變化的變異 ＝ 大盤 {d['mkt'].var() / v:.0%}、產業 {d['sec'].var() / v:.0%}、個股 {d['idio'].var() / v:.0%}"
            f"（三者有共變，加總不必是 100%）；和「明年 EPS 預估變化」的 Spearman：個股 {sp('idio', 'rev'):+.2f}、"
            f"產業（同月去平均）{s['dfpe'].corr(s['rev'], method='spearman'):+.2f}、大盤 {m['dfpe'].corr(m['rev']):+.2f}（Pearson，{len(m)} 個月）；"
            f"事前線索 vs 個股＋產業部分：今天的相對 forward 本益比 {sp('prem0', 'y'):+.2f}、過去 12 個月報酬 {sp('ret12', 'y'):+.2f}")


def score(d, preds, h):
    subsets = [("全部", d["act"].notna()), ("2022 以後起點", d["month"] >= "2022-01-01"), ("科技", d["grp"] != "other"), ("非科技", d["grp"] == "other"),
               ("半導體類", d["grp"] == "cyclical"), ("成長加速 ΔG > 0.15", (d["GT"] - d["G0"]) > 0.15),
               ("成長放緩 ΔG < −0.15", (d["GT"] - d["G0"]) < -0.15),
               ("forward 本益比大升（> +0.3）", (d["lfpeT"] - d["lfpe0"]) > 0.3), ("forward 本益比大降（< −0.3）", (d["lfpeT"] - d["lfpe0"]) < -0.3),
               ("目標日本益比比今天高 30% 以上", (d["act"] - np.log(d["px"] / d["eps0"])) > np.log(1.3))]
    rows = []
    for lab, m in subsets:
        r = dict(h=h, 樣本=lab, n=int(m.sum()))
        for k, p in preds.items():
            e = (p - d["act"])[m]
            r[k] = float(np.median(np.abs(e.dropna()))) if e.notna().any() else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    a = ap.parse_args()
    b = pd.read_pickle(a.build)
    sys.path.insert(0, os.path.join(HERE, "research"))
    import usage_backtest as UB                          # noqa: E402
    b["pk"] = UB.correction_wf(b)                        # 走動式共識校正（約 1 分鐘）
    beta = pd.read_csv(os.path.join(RES, "orbit_beta.csv"))
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 40)

    # 0. 橫斷面：本益比和成長預期的關係
    z = b[(b["lead"] > 10.5) & (b["lead"] <= 12) & (b["eps0"] > 0) & (b["feps"] > 0) & ~b["near_split"]].copy()
    z["lpe"] = np.log(z["px"] / z["eps0"])
    z["lfpe"] = np.log(z["px"] / z["feps"])
    z["G"] = np.log(z["feps"] / z["eps0"])
    z["ltg"] = z["fgr5y"] / 100
    for c in ("lpe", "lfpe", "G", "ltg"):
        z[c + "_d"] = z[c] - z.groupby("month")[c].transform("median")
    zz = z.dropna(subset=["lpe_d", "G_d", "ltg_d"])
    zz = zz[(zz["lpe_d"].abs() < 3) & (zz["G_d"].abs() < 1.5)]
    say(f"== 0. 同一個月橫斷面（S&P 500，{zz['month'].min():%Y}–{zz['month'].max():%Y}，{len(zz):,} 個公司月，各變數減同月中位數）")
    for lab, y, xs in (("ln 本益比 ~ G", "lpe_d", ["G_d"]), ("ln 本益比 ~ G ＋ LTG", "lpe_d", ["G_d", "ltg_d"]),
                       ("ln forward 本益比 ~ G", "lfpe_d", ["G_d"]), ("ln forward 本益比 ~ LTG", "lfpe_d", ["ltg_d"])):
        X = np.column_stack([np.ones(len(zz))] + [zz[c] for c in xs])
        co = np.linalg.lstsq(X, zz[y], rcond=None)[0]
        r2 = 1 - np.var(zz[y] - X @ co) / np.var(zz[y])
        say(f"  {lab}：斜率 {', '.join(f'{v:.2f}' for v in co[1:])}；R² {r2:.2f}")
    say("  讀法：本益比（用最近四季 EPS）對「明年成長預期 G」的斜率約 1 ＝ 市場大致對明年的 EPS 給倍數；forward 本益比和 G 幾乎無關。")
    decompose(b)

    out, coefs_all = [], []
    for h in (12, 24):
        d = pairs(b, h)
        bt_a = beta[(beta["方法"] == "原始成長a") & (beta["h"] == h)].set_index(["年", "組別"])["b0"]
        bt_ab = beta[(beta["方法"] == "原始成長ab") & (beta["h"] == h)].set_index(["年", "組別"])[["b0", "b1"]]
        key = list(zip(d["year"], d["grp"].map(GNAME)))
        d["ba"] = [bt_a.get(k, np.nan) for k in key]
        d["bab0"] = [bt_ab["b0"].get(k, np.nan) for k in key]
        d["bab1"] = [bt_ab["b1"].get(k, np.nan) for k in key]
        d = d[d["ba"].notna() & (d["year"] <= 2024)].copy()
        orb = d["orbit_lr"] * h / 12
        lp0 = np.log(d["px"])

        def orbit_pe(EA, EB=None):
            if EB is None:
                return lp0 + orb + d["ba"] * np.log(EA / d["eps0"]).clip(-2, 2) - np.log(EA)
            return lp0 + orb + d["bab0"] * np.log(EA / d["eps0"]).clip(-2, 2) + d["bab1"] * np.log(EB / d["eps0"]).clip(-2, 2) - np.log(EA)
        d["dfpe"] = d["lfpeT"] - d["lfpe0"]
        d["lpe0"] = np.log(d["px"] / d["eps0"])
        d["ga"] = np.log(d["EA"] / d["eps0"]).clip(-2, 2)
        d["ret12c"] = d["ret12"].clip(-1, 1)
        d["yo"] = d["act"] - d["lpe0"] - orb                        # 本益比的變化扣掉軌道
        base = d["lpe0"] + orb
        preds = {"U 本益比不變": d["lpe0"],
                 "O_a 軌道": orbit_pe(d["EA"]),
                 "O_ab 軌道（b＝F_T）": orbit_pe(d["EA"], d["feps_T"]),
                 "F forward 倍數不變（F_T）": np.log(d["px"] / d["F0k"]) + d["GT"]}
        # G 成長定價：本益比變化 ＝ a ＋ c_a × 交出的成長 ＋ c_T × 目標日的成長預期 ＋ c_0 × 今天的成長預期 ＋ c_r × 過去 12 個月報酬
        gcols = ["ga", "GT", "G0", "ret12c"]
        rA, cA = walk(d, gcols, "yo")
        preds["G 成長定價（F_T）"] = base + rA
        # B：猜中基本面（下一年 EPS 用實現值），同一個式子但用實現值估係數
        d["GTr_"] = d["GTr"]
        dB = d.rename(columns={"GT": "GT_mkt"}).rename(columns={"GTr_": "GT"})
        rB, cB = walk(dB, gcols, "yo", known_lag=12)          # 實現值要到 T＋12 才知道
        bpreds = {"O_a 軌道": preds["O_a 軌道"], "O_ab 軌道（b＝實現值）": orbit_pe(d["EA"], d["EB"].where(d["EB"] > 0)),
                  "G 成長定價（實現值）": base + rB}
        preds["平均：O_a 與 G（F_T）"] = (preds["O_a 軌道"] + preds["G 成長定價（F_T）"]) / 2
        # 上限：你連「產業（含大盤）的 forward 倍數變化」都猜中
        d["secmk"] = d.groupby(["month", "sector"])["dfpe"].transform("median").clip(-1, 1)
        rS, _ = walk(d, gcols + ["secmk"], "yo")
        preds["上限：G＋產業倍數猜中"] = base + rS
        # C：沒有額外看法——EPS_a＝今天共識（h＝24 再乘一次隱含成長）、目標日的下一年預期＝EPS_a × 隱含成長
        g = (d["F0k"] / d["eps0"]).clip(0.7, 1.5)
        EAc = d["F0k"] if h == 12 else d["F0k"] * g
        FTc = EAc * g
        cpred = {"U 本益比不變": d["lpe0"], "O_a 軌道": orbit_pe(EAc), "O_ab 軌道": orbit_pe(EAc, FTc),
                 "F forward 倍數不變": np.log(d["px"] / d["F0k"]) + np.log(FTc / EAc).clip(-1.5, 1.5)}
        cc = cA.set_index(["年", "組別"])
        Rc = pd.Series(np.nan, index=d.index)
        xc = pd.DataFrame({"ga": np.log(EAc / d["eps0"]).clip(-2, 2), "GT": np.log(FTc / EAc).clip(-1.5, 1.5), "G0": d["G0"], "ret12c": d["ret12c"]})
        for (Y, gname), row in cc.iterrows():
            m = (d["year"] == Y) & (d["grp"].map(GNAME) == gname)
            Rc.loc[m] = row["截距"] + sum(row[c] * xc.loc[m, c] for c in gcols)
        cpred["G 成長定價"] = base + Rc
        # 沒有看法時，目標日的成長預期改用「回歸」：GT ＝ a ＋ λ × G0（走動式：只用目標日在起點那年以前的配對估）
        gth = pd.Series(np.nan, index=d.index)
        for Y in range(2015, 2025):
            tr = d[d["T"] < pd.Timestamp(f"{Y}-01-01")].dropna(subset=["GT", "G0"])
            m = d["year"] == Y
            if len(tr) < 300 or not m.any():
                continue
            ab = huber_ols(np.column_stack([np.ones(len(tr)), tr["G0"].to_numpy(float)]), tr["GT"].to_numpy(float))
            gth.loc[m] = ab[0] + ab[1] * d.loc[m, "G0"]
        xr = xc.assign(GT=gth.clip(-1.5, 1.5))
        Rr = pd.Series(np.nan, index=d.index)
        for (Y, gname), row in cc.iterrows():
            m = (d["year"] == Y) & (d["grp"].map(GNAME) == gname)
            Rr.loc[m] = row["截距"] + sum(row[c] * xr.loc[m, c] for c in gcols)
        cpred["G 成長定價（成長預期回歸）"] = base + Rr
        cpred["平均：O_a 與 G"] = (cpred["O_a 軌道"] + cpred["G 成長定價"]) / 2
        cpred["分組：科技用 G、非科技用軌道"] = cpred["G 成長定價"].where(d["grp"] != "other", cpred["O_a 軌道"])
        cpred["分組：科技用 G（回歸）、非科技用軌道"] = cpred["G 成長定價（成長預期回歸）"].where(d["grp"] != "other", cpred["O_a 軌道"])
        if h == 24:
            cpred["O_a 軌道（不外推）"] = orbit_pe(d["F0k"])
        ok = pd.concat(preds, axis=1).notna().all(axis=1)
        dd = d[ok]
        say(f"\n== {h} 個月：{len(dd):,} 組配對（{dd['ticker'].nunique()} 家；起點 {dd['month'].min():%Y-%m}～{dd['month'].max():%Y-%m}）")
        say("-- A：你給了 EPS_a（實際）和「目標日時市場對下一年的預期」（當時的共識 × 係數）：中位 |ln 本益比誤差|")
        sA = score(dd, {k: v[ok] for k, v in preds.items()}, h)
        say(sA.drop(columns="h").round(3).to_string(index=False))
        okB = pd.concat(bpreds, axis=1).notna().all(axis=1)
        dB_ = d[okB]
        say(f"-- B：你給了 EPS_a 和下一年 EPS 的實現值（猜對基本面；係數只用 T＋12 在起點那年以前的配對估）：{len(dB_):,} 組（起點 {dB_['month'].min():%Y-%m}～{dB_['month'].max():%Y-%m}）")
        sB = score(dB_, {k: v[okB] for k, v in bpreds.items()}, h)
        say(sB.drop(columns="h").round(3).to_string(index=False))
        okc = pd.concat(cpred, axis=1).notna().all(axis=1)
        say("-- C：沒有額外看法（EPS 都用今天的共識推）：中位 |ln 本益比誤差|")
        sC = score(d[okc], {k: v[okc] for k, v in cpred.items()}, h)
        say(sC.drop(columns="h").round(3).to_string(index=False))
        yr = dd.assign(eR=(preds["G 成長定價（F_T）"][ok] - dd["act"]).abs(), eO=(preds["O_a 軌道"][ok] - dd["act"]).abs(),
                       eF=(preds["F forward 倍數不變（F_T）"][ok] - dd["act"]).abs()).groupby("year")[["eR", "eO", "eF"]].median()
        say(f"  逐年：G 比 O_a 準的年數 {int((yr['eR'] < yr['eO']).sum())}／{len(yr)}；G 比 F 準 {int((yr['eR'] < yr['eF']).sum())}／{len(yr)}")
        last = cA[cA["年"] == cA["年"].max()]
        say("  G（F_T）最後一年的係數（ga＝交出的成長、GT＝目標日的成長預期、G0＝今天的成長預期、ret12c＝過去 12 個月報酬）：")
        say(last.round(3).to_string(index=False))
        out += [sA.assign(輸入="A"), sB.assign(輸入="B"), sC.assign(輸入="C")]
        coefs_all += [cA.assign(h=h, 版本="A 市場預期"), cB.assign(h=h, 版本="B 實現值")]
        # 存逐列結果給後續（網頁、README）
        keep = dd[["ticker", "month", "grp", "px", "eps0", "feps", "EA", "feps_T", "EB", "act", "lfpe0", "lfpeT", "G0", "GT", "ret12"]].copy()
        for k, v in preds.items():
            keep[k] = v[ok]
        keep.to_csv(os.path.join(RES, f"rerating_rows_{h}.csv.gz"), index=False, float_format="%.6g")
    pd.concat(out).to_csv(os.path.join(RES, "rerating_scores.csv"), index=False, float_format="%.6f")
    pd.concat(coefs_all).to_csv(os.path.join(RES, "rerating_coefs.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "rerating_lab.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
