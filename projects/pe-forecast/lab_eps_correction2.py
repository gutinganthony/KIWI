#!/usr/bin/env python3
"""共識校正模型的修正：加上「這家公司在同一個時點（距離年報同一段）的過去偏差」（README §20.2）。

    python3 lab_eps_correction2.py --cache <lab_orbit.py 的暫存目錄> [--build <已建好的 build pickle>]   # 訓練樹模型（約 3 分鐘）

問題：正式版（§19.1）只用「lead≈11 個月時的過去偏差」。快公布年報時（本財年已公布三季），共識離實際通常很近，
但樹模型對高本益比的大型股會給出很大的修正（AAPL 2026-10：+7.6%；2020-09 樣本內 +13%，實際 +1%）。
邏輯：同一家公司在「同一個時點」的歷史偏差最能說明它現在離實際多遠——Apple 年報前一個月，過去十幾年都在 ±2% 內。
新線索（都只用起點當月以前已公布的年度）：
  pb_lead   ＝這家公司在同一個距離年報區間（0.5–3、3–6、6–9、9–12 個月）的過去偏差：每個年度取該區間的中位數，再取各年度的中位數（≥ 2 個年度）
  pb_lead_n ＝上面用到幾個年度（上限 8）
  pb_abs    ＝同一區間過去的 |偏差| 中位數（這家公司在這個時點通常差多少）
比較（走動式，每年 1 月只用報告日在前一年底以前的列訓練，2015–2024）：
  A 正式版線索（FEATS_NOW）；B ＋pb_lead、pb_lead_n；C ＋pb_lead、pb_lead_n、pb_abs；D ＝B 拿掉 ln 本益比
  護欄（不用重訓，套在樹的預測上）：這家公司在同一時點有 ≥ 4 個年度的紀錄時，把預測限制在
  「同時點過去偏差 ± k × 同時點過去 |偏差|」之內（k＝1、2），或和同時點過去偏差各半平均。
評分：EPS 誤差（全部、依距離年報、依市值）、§18 乾淨起點的 12 個月本益比誤差、大幅修正（|預測| > 5%）的命中、AAPL 的逐年樣本外預測。
輸出：results/eps_correction2.txt、eps_correction2_scores.csv
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
import lab_eps_correction as L                           # noqa: E402

RES = os.path.join(HERE, "results")
BUCKETS = [0.5, 3, 6, 9, 12]
NEW_B = ["pb_lead", "pb_lead_n"]
NEW_C = ["pb_lead", "pb_lead_n", "pb_abs"]
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def add_lead_bias(d):
    """同一距離年報區間的過去偏差（只用報告日 ≤ 起點當月的年度）。"""
    d = d.copy()
    d["lead_b"] = pd.cut(d["lead"], BUCKETS, labels=False)
    ok = d["tgt"].notna() & ~d["near_split"]
    per_fy = d[ok].groupby(["ticker", "lead_b", "fy1"]).agg(report=("report", "first"), tg=("tgt", "median"),
                                                            ab=("tgt", lambda v: np.median(np.abs(v)))).reset_index()
    by = {k: g.sort_values("report") for k, g in per_fy.groupby(["ticker", "lead_b"])}
    pb, pn, pa = [], [], []
    for t, b, mo in zip(d["ticker"], d["lead_b"], d["month"]):
        g = by.get((t, b))
        past = g[g["report"] <= mo] if g is not None else None
        if past is None or len(past) < 2:
            pb.append(np.nan), pn.append(0 if past is None else len(past)), pa.append(np.nan)
            continue
        pb.append(float(np.median(past["tg"])))
        pn.append(len(past))
        pa.append(float(np.median(past["ab"])))
    d["pb_lead"], d["pb_lead_n"], d["pb_abs"] = pb, np.minimum(pn, 8), pa
    return d


def walk(d, feats):
    pred = pd.Series(np.nan, index=d.index)
    for Y in range(2015, 2025):
        cut = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        tr = d[(d["report"] <= cut) & d["tgt"].notna() & ~d["near_split"]]
        te = d[(d["month"] > cut) & (d["month"] <= cut + pd.DateOffset(months=12))]
        if len(tr) < 3000 or te.empty:
            continue
        X = tr[feats].to_numpy(float)
        X[~np.isfinite(X)] = np.nan
        mdl = HistGradientBoostingRegressor(**L.GBM).fit(X, tr["tgt"].to_numpy(float))
        Xt = te[feats].to_numpy(float)
        Xt[~np.isfinite(Xt)] = np.nan
        pred.loc[te.index] = mdl.predict(Xt)
    return pred


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--build", default=None, help="L.build() 的 pickle（省時間）")
    a = ap.parse_args()
    d = pd.read_pickle(a.build) if a.build and os.path.exists(a.build) else L.build(a.cache)
    d = add_lead_bias(d)
    say(f"公司月 {len(d):,}；有同時點過去偏差的 {int(d['pb_lead'].notna().sum()):,}（{d['pb_lead'].notna().mean():.0%}）")
    z = d[d["tgt"].notna() & ~d["near_split"] & (d["month"] >= "2015-01-01") & d["pb_lead"].notna()]
    say("\n== 1. 邏輯檢查：同時點過去偏差的五分位 → ln(實際 ÷ 共識) 中位數（2015 以後）；應該由低到高")
    for lb, g in z.groupby("lead_b"):
        qn = pd.qcut(g["pb_lead"].rank(method="first"), 5, labels=False)
        med = g.groupby(qn)["tgt"].median()
        say(f"  距離年報 {BUCKETS[int(lb)]}–{BUCKETS[int(lb) + 1]} 個月（n={len(g):,}）：" + "  ".join(f"{v:+.3f}" for v in med)
            + f"   Spearman {g['pb_lead'].corr(g['tgt'], method='spearman'):+.3f}；舊的過去偏差（lead≈11）{g['past_bias'].corr(g['tgt'], method='spearman'):+.3f}")
    preds = {"A 正式版": walk(d, L.FEATS_NOW), "B ＋同時點偏差": walk(d, L.FEATS_NOW + NEW_B), "C ＋同時點偏差＋常差多少": walk(d, L.FEATS_NOW + NEW_C),
             "D ＝B 拿掉本益比": walk(d, [f for f in L.FEATS_NOW if f != "ln_pe"] + NEW_B)}
    for k, p in preds.items():
        d[k] = p
    has = d["pb_lead"].notna() & (d["pb_lead_n"] >= 4)
    for base in ("A 正式版", "B ＋同時點偏差"):
        tag = base[0]
        for kk in (1, 2):
            lo, hi = d["pb_lead"] - kk * d["pb_abs"], d["pb_lead"] + kk * d["pb_abs"]
            d[f"{tag}＋護欄±{kk}"] = np.where(has, np.clip(d[base], lo, hi), d[base])
            preds[f"{tag}＋護欄±{kk}"] = d[f"{tag}＋護欄±{kk}"]
        d[f"{tag}＋各半"] = np.where(has, (d[base] + d["pb_lead"]) / 2, d[base])
        preds[f"{tag}＋各半"] = d[f"{tag}＋各半"]
    ev = d[(d["month"] >= "2015-01-01") & d["tgt"].notna() & ~d["near_split"] & d["A 正式版"].notna()].copy()
    ev["lead_lab"] = pd.cut(ev["lead"], BUCKETS, labels=["0.5–3", "3–6", "6–9", "9–12"])
    ev["mc_lab"] = pd.cut(ev["mc_rank"], [0, 0.5, 0.9, 1.0], labels=["後 50%", "50–90%", "前 10%"])
    rows = []
    groups = [("全部", ev)] + [(f"距離年報 {k}", g) for k, g in ev.groupby("lead_lab", observed=True)] + \
             [(f"市值 {k}", g) for k, g in ev.groupby("mc_lab", observed=True)] + \
             [("前 10% × 0.5–3", ev[(ev["mc_lab"] == "前 10%") & (ev["lead_lab"] == "0.5–3")])] + \
             [(f"{per}", ev[(ev["month"] >= lo) & (ev["month"] <= hi)]) for per, lo, hi in
              (("2015–2021", "2015-01-01", "2021-12-31"), ("2022 以後", "2022-01-01", "2026-12-31"))]
    for lab, g in groups:
        r = dict(樣本=lab, n=len(g), 原樣=float(np.median(np.abs(g["tgt"]))))
        for k in preds:
            r[k] = float(np.median(np.abs(g["tgt"] - g[k])))
        rows.append(r)
    sc = pd.DataFrame(rows)
    say("\n== 2. EPS 誤差：中位 |ln(實際 ÷ 校正後的共識)|（2015 以後，走動式樣本外）")
    say(sc.round(4).to_string(index=False))

    say("\n== 3. 大幅修正（|預測| > 5%）的品質：這些列的實際偏差中位數與 |誤差| 中位數（預測方向對不對、有沒有過頭）")
    for k in preds:
        big = ev[ev[k].abs() > 0.05]
        same = np.sign(big[k]) == np.sign(big["tgt"])
        say(f"  {k}：{len(big):,} 列（{len(big) / len(ev):.0%}）；方向對 {same.mean():.0%}；預測中位 {big[k].median():+.3f}、實際中位 {big['tgt'].median():+.3f}；"
            f"|誤差| 校正 {np.median(np.abs(big['tgt'] - big[k])):.3f} vs 原樣 {np.median(np.abs(big['tgt'])):.3f}")

    # 4. §18 乾淨起點的本益比誤差（同 lab_eps_correction.py 第 4 節的算法）
    one = ev[(ev["lead"] > 10.5) & (ev["lead"] <= 12.0) & (ev["eps0"] > 0) & ev["y12"].notna()].copy()
    beta = pd.read_csv(os.path.join(RES, "orbit_beta.csv"))
    bt = beta[beta["方法"] == "原始成長a"].set_index(["h", "年", "組別"])["b0"]
    one["b"] = [bt.get((12, mo.year, L.GNAME[g]), np.nan) for mo, g in zip(one["month"], one["grp"])]
    one = one[one["b"].notna() & (one["eps_f12"] > 0)]
    act = np.log(one["px"]) + one["y12"] + one["orbit_lr"] - np.log(one["eps_f12"])
    pe_rows = []
    for per, lo, hi in (("2015–2021", "2015-01-01", "2021-12-31"), ("2022 以後", "2022-01-01", "2026-12-31"), ("全期", "2015-01-01", "2026-12-31")):
        g = one[(one["month"] >= lo) & (one["month"] <= hi)]
        r = dict(期間=per, n=len(g))
        for nm, p in [("原樣", 0.0)] + [(k, g[k]) for k in preds]:
            ea = g["feps"] * np.exp(p)
            lpx = np.log(g["px"]) + g["orbit_lr"] + g["b"] * np.log(ea / g["eps0"]).clip(-2, 2)
            r[nm] = float(np.median(np.abs(lpx - np.log(ea) - act.loc[g.index])))
        pe_rows.append(r)
    pe = pd.DataFrame(pe_rows)
    say("\n== 4. 12 個月後本益比的中位 |ln 誤差|（§18 的乾淨起點，EPS_a＝校正後的共識）")
    say(pe.round(4).to_string(index=False))

    say("\n== 5. AAPL：距離年報 2 個月內的樣本外預測 vs 實際")
    ap_ = ev[(ev["ticker"] == "AAPL") & (ev["lead"] < 2)][["month", "lead", "tgt"] + list(preds)]
    say(ap_.round(3).to_string(index=False))

    say("\n== 6. 逐年 EPS 誤差（穩定性）：正式版 vs 正式版＋護欄±1")
    yr = ev.groupby(ev["month"].dt.year).apply(lambda g: pd.Series({"n": len(g), "原樣": np.median(np.abs(g["tgt"])),
                                                                   "A 正式版": np.median(np.abs(g["tgt"] - g["A 正式版"])),
                                                                   "A＋護欄±1": np.median(np.abs(g["tgt"] - g["A＋護欄±1"]))}))
    say(yr.round(4).to_string())
    say(f"  護欄±1 比正式版準的年份：{int((yr['A＋護欄±1'] < yr['A 正式版']).sum())}／{len(yr)}")
    sc.assign(表="EPS").to_csv(os.path.join(RES, "eps_correction2_scores.csv"), index=False, float_format="%.6f")
    pe.assign(表="PE").to_csv(os.path.join(RES, "eps_correction2_scores.csv"), mode="a", index=False, float_format="%.6f")
    open(os.path.join(RES, "eps_correction2.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
