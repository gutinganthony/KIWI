#!/usr/bin/env python3
"""README §22.3：EPS 變化很大時，股價是不是比模型以為的更跟著 EPS 走？兩種修正的走動式檢驗。

    python3 research/pe_anchor.py --cache <lab_orbit.py 的暫存目錄> > results/pe_anchor.txt

起因（§22.1 個案）：MU 2024-10 的最近四季 EPS 只有 0.70（景氣谷底，本益比 154），兩年後 77。給模型完全正確的 EPS，
正式版預測股價 193（實際 989），本益比 2.5（實際 12.8）——β × ln(EPS 變化) 是線性的，又截在 ±2，谷底的極端本益比完全沒有回歸。
兩個候選（都只用起點當時看得到的資料，β／γ 每年 1 月只用已揭曉的配對重估、分公司類型、同月份去平均、Huber；和正式版同一套）：
  M1 本益比回歸：多一個線索 x_pe ＝ 錨 − 「只靠軌道、股價不跟 EPS 時」目標日的 ln 本益比
                 ＝ 錨 − (今天 ln 本益比 ＋ 軌道 − ln(EPS_a ÷ 今天 EPS))；錨＝同產業當月的中位 ln 本益比（pe_sec）或自己過去 5 年中位（pe_own）。
                 γ 是「往正常本益比拉回幾成」。
  M2 非線性：多一個 g × |g|（g＝ln(EPS_a ÷ 今天 EPS)）——EPS 變化越大，股價每單位的反應越大（或越小）。
評分：中位 |實際偏離軌道 − 預測|（＝ 本益比的 ln 誤差，因為 EPS 給定），全部／2022 以後／|g| > 0.5 的大變化／半導體類。
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import lab_orbit as lo                                   # noqa: E402

RES = os.path.join(HERE, "results")
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def walk(x, h, cols, start=2015, end=2025):
    pred = pd.Series(np.nan, index=x.index)
    coefs = []
    for Y in range(start, end + 1):
        cutoff = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        te_all = x[(x["month_end"] > cutoff) & (x["month_end"] <= cutoff + pd.DateOffset(months=12))]
        tr_all = x[lo.tgt_end(x, h) <= cutoff]
        for g in lo.GNAME:
            b = lo.beta_fit(tr_all[tr_all["grp"] == g], f"y{h}", cols)
            te = te_all[te_all["grp"] == g].dropna(subset=cols)
            if np.all(np.isfinite(b)) and len(te):
                pred.loc[te.index] = te[cols].to_numpy(float) @ b
            coefs.append(dict(h=h, 年=Y, 組別=lo.GNAME[g], **{c: v for c, v in zip(cols, b)}))
    return pred, pd.DataFrame(coefs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    x = pd.read_pickle(os.path.join(a.cache, "orbit_x2.pkl"))
    x = x[x["month"] >= "2012-01-01"].copy()
    rows, last = [], {}
    for h in (12, 24):
        g = np.log(x[f"eps_f{h}"] / x["eps0"]).where((x[f"eps_f{h}"] > 0) & (x["eps0"] > 0))
        x[f"gg{h}"] = g.clip(-2, 2)                                            # 正式版的寫法（截在 ±2）
        x[f"graw{h}"] = g.clip(-5, 5)
        x[f"gabs{h}"] = x[f"graw{h}"] * x[f"graw{h}"].abs()
        base_pe = x["ln_pe"] + x["orbit_lr"] * h / 12 - g                       # 股價只走軌道時，目標日的 ln 本益比
        x[f"xsec{h}"] = (x["pe_sec"] - base_pe).clip(-4, 4)
        x[f"xown{h}"] = (x["pe_own"] - base_pe).clip(-4, 4)
        ok = x[f"y{h}"].notna() & g.notna() & x["ln_pe"].notna()
        z = x[ok].copy()
        specs = {"正式版 β×g（截 ±2）": [f"gg{h}"], "β×g（不截）": [f"graw{h}"], "M2 ＋g×|g|": [f"graw{h}", f"gabs{h}"],
                 "M1 ＋回歸到產業本益比": [f"graw{h}", f"xsec{h}"], "M1 ＋回歸到自己 5 年本益比": [f"graw{h}", f"xown{h}"],
                 "M1 兩個錨都放": [f"graw{h}", f"xsec{h}", f"xown{h}"]}
        preds = {}
        for nm, cols in specs.items():
            zz = z.dropna(subset=cols)
            p, cf = walk(zz, h, cols)
            preds[nm] = p.reindex(z.index)
            last[(h, nm)] = cf[cf["年"] == cf["年"].max()]
        ev = z[preds["M1 兩個錨都放"].notna() & preds["正式版 β×g（截 ±2）"].notna()].copy()
        say(f"\n== {h} 個月（EPS 給定＝實際；走動式 2015 起；n＝{len(ev):,}）：中位 |ln 本益比誤差|")
        for lab, m in (("全部", slice(None)), ("2015–2021", ev["month"] < "2022-01-01"), ("2022 以後", ev["month"] >= "2022-01-01"),
                       ("|g| > 0.5（EPS 大變化）", ev[f"graw{h}"].abs() > 0.5), ("|g| > 1", ev[f"graw{h}"].abs() > 1),
                       ("起點本益比 > 60", ev["ln_pe"] > np.log(60)), ("半導體／設備／記憶體", ev["grp"] == "cyclical"),
                       ("非科技", ev["grp"] == "other")):
            g_ = ev.loc[m]
            r = dict(h=h, 樣本=lab, n=len(g_), 軌道=float(np.median(np.abs(g_[f"y{h}"]))))
            for nm in specs:
                r[nm] = float(np.median(np.abs(g_[f"y{h}"] - preds[nm].loc[g_.index])))
            rows.append(r)
        t = pd.DataFrame([r for r in rows if r["h"] == h]).drop(columns="h")
        say(t.round(4).to_string(index=False))
        yr = ev.groupby(ev["month"].dt.year).apply(lambda g_: pd.Series({k: np.median(np.abs(g_[f"y{h}"] - preds[k].loc[g_.index]))
                                                                          for k in ("正式版 β×g（截 ±2）", "M1 兩個錨都放", "M1 ＋回歸到產業本益比")}))
        say(f"  逐年：M1 兩個錨比正式版準 {int((yr['M1 兩個錨都放'] < yr['正式版 β×g（截 ±2）']).sum())}／{len(yr)} 年；"
            f"產業錨 {int((yr['M1 ＋回歸到產業本益比'] < yr['正式版 β×g（截 ±2）']).sum())}／{len(yr)} 年")
        say("  最後一年的係數（M1 兩個錨）：")
        say(last[(h, "M1 兩個錨都放")].round(3).to_string(index=False))
    pd.DataFrame(rows).to_csv(os.path.join(RES, "pe_anchor_scores.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "pe_anchor.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
