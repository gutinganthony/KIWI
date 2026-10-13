#!/usr/bin/env python3
"""README §21.3：分析師意見分歧（I/B/E/S 預估的標準差 ÷ |平均|）能不能讓共識校正更準、讓區間更貼近個股？

    python3 lab_dispersion.py --cache <lab_orbit.py 的暫存目錄> --raw <OSAP 原始檔目錄（含 ForecastDispersion.csv）> [--build <L.build 的 pickle>]
    # 訓練樹模型約 3 分鐘：不要和其他訓練程式同時跑

邏輯：分析師意見越分歧，代表這家公司的獲利越難預測（Diether, Malloy & Scherbina 2002：分歧大的股票之後報酬較低，
共識也較樂觀）。兩個可能的用途：
  (a) 共識校正：分歧大 → 共識更可能高估？加進樹模型當第 15 條線索。
  (b) 區間：分歧大 → 股價偏離軌道更多？在「波動^0.7」之外再乘 (分歧 ÷ 中位)^δ。
資料：OSAP 的 ForecastDispersion（I/B/E/S FY1 預估標準差 ÷ |平均|，每月）；permno 對代號用 data/osap/permno_map.csv（ok 的）。
今天要用時，Yahoo 只有最高、最低與人數：標準差 ≈ (最高 − 最低) ÷ d2(人數)（常態樣本全距的期望值），所以最後也比對兩者的量級。
評分：(a) 走動式 EPS 誤差（2015 以後；正式版 vs 加分歧，都套同時點護欄 ±1）與 §18 乾淨起點的 12 個月本益比誤差；
     (b) 走動式 80% 區間：依分歧五分位的涵蓋率（條件校準）與區間分數。
輸出：results/dispersion.txt、dispersion_scores.csv
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab_eps_correction as L                           # noqa: E402
import lab_eps_correction2 as L2                         # noqa: E402
from pef import cond                                     # noqa: E402

RES = os.path.join(HERE, "results")
A = 0.2
DELTAS = (0.0, 0.1, 0.2, 0.3)
D2 = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326, 6: 2.534, 7: 2.704, 8: 2.847, 9: 2.970, 10: 3.078, 11: 3.173, 12: 3.258,
      13: 3.336, 14: 3.407, 15: 3.472, 16: 3.532, 17: 3.588, 18: 3.640, 19: 3.689, 20: 3.735, 25: 3.931, 30: 4.086}
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def d2(n):
    """常態樣本全距的期望值（以標準差為單位）；人數之間線性內插，> 30 用 30 的值。"""
    if not np.isfinite(n) or n < 2:
        return np.nan
    ks = sorted(D2)
    n = min(n, ks[-1])
    return float(np.interp(n, ks, [D2[k] for k in ks]))


def load_disp(raw):
    s = pd.read_csv(os.path.join(raw, "ForecastDispersion.csv"))
    col = [c for c in s.columns if c not in ("permno", "yyyymm")][0]
    pm = pd.read_csv(os.path.join(HERE, "data", "osap", "permno_map.csv"))
    pm = pm[pm["ok"].astype(bool)][["ticker", "permno"]]
    s = s.merge(pm, on="permno", how="inner")
    s["month"] = pd.to_datetime(s["yyyymm"].astype(int).astype(str) + "01")
    s["disp"] = pd.to_numeric(s[col], errors="coerce").clip(0, 2)
    return s[["ticker", "month", "disp"]].dropna()


def iscore(y, lo, hi):
    return (hi - lo) + (2 / A) * np.maximum(lo - y, 0) + (2 / A) * np.maximum(y - hi, 0)


def part_a(d):
    say("\n== (a) 共識校正：加上分歧當線索")
    z = d[d["tgt"].notna() & ~d["near_split"] & (d["month"] >= "2015-01-01") & d["disp"].notna()]
    qn = pd.qcut(z["disp"].rank(method="first"), 5, labels=False)
    say("  邏輯：分歧五分位 → ln(實際 ÷ 共識) 中位（負＝共識高估）："
        + "  ".join(f"{v:+.3f}" for v in z.groupby(qn)["tgt"].median())
        + f"；|偏差| 中位：" + "  ".join(f"{v:.3f}" for v in z.groupby(qn)["tgt"].apply(lambda v: np.median(np.abs(v))))
        + f"；Spearman（偏差）{z['disp'].corr(z['tgt'], method='spearman'):+.3f}")
    preds = {"正式版": L2.walk(d, L.FEATS_NOW), "＋分歧": L2.walk(d, L.FEATS_NOW + ["disp"])}
    has = d["pb_lead"].notna() & (d["pb_lead_n"] >= 4)
    lo, hi = d["pb_lead"] - d["pb_abs"], d["pb_lead"] + d["pb_abs"]
    for k in list(preds):
        preds[k] = pd.Series(np.where(has, np.clip(preds[k], lo, hi), preds[k]), index=d.index)  # 同時點護欄 ±1（正式版的做法）
    ev = d[(d["month"] >= "2015-01-01") & d["tgt"].notna() & ~d["near_split"] & preds["正式版"].notna()].copy()
    for k, p in preds.items():
        ev[k] = p.loc[ev.index]
    ev["lead_lab"] = pd.cut(ev["lead"], L2.BUCKETS, labels=["0.5–3", "3–6", "6–9", "9–12"])
    ev["dq"] = pd.qcut(ev["disp"].rank(method="first"), 5, labels=["分歧最低 20%", "2", "3", "4", "分歧最高 20%"]) if ev["disp"].notna().any() else np.nan
    rows = []
    groups = [("全部", ev)] + [(f"距離年報 {k}", g) for k, g in ev.groupby("lead_lab", observed=True)] + \
             [(f"{k}", g) for k, g in ev[ev["disp"].notna()].groupby("dq", observed=True)] + \
             [(per, ev[(ev["month"] >= a) & (ev["month"] <= b)]) for per, a, b in
              (("2015–2021", "2015-01-01", "2021-12-31"), ("2022 以後", "2022-01-01", "2026-12-31"))]
    for lab, g in groups:
        r = dict(樣本=lab, n=len(g), 原樣=float(np.median(np.abs(g["tgt"]))))
        for k in preds:
            r[k] = float(np.median(np.abs(g["tgt"] - g[k])))
        rows.append(r)
    sc = pd.DataFrame(rows)
    say("  EPS 誤差：中位 |ln(實際 ÷ 校正後的共識)|（走動式樣本外，兩者都含同時點護欄 ±1）")
    say(sc.round(4).to_string(index=False))
    yr = ev.groupby(ev["month"].dt.year).apply(lambda g: pd.Series({k: np.median(np.abs(g["tgt"] - g[k])) for k in preds}))
    say(f"  逐年：＋分歧比正式版準的年份 {int((yr['＋分歧'] < yr['正式版']).sum())}／{len(yr)}")
    # §18 乾淨起點的 12 個月本益比（同 lab_eps_correction2.py 第 4 節）
    one = ev[(ev["lead"] > 10.5) & (ev["lead"] <= 12.0) & (ev["eps0"] > 0) & ev["y12"].notna()].copy()
    beta = pd.read_csv(os.path.join(RES, "orbit_beta.csv"))
    bt = beta[beta["方法"] == "原始成長a"].set_index(["h", "年", "組別"])["b0"]
    one["b"] = [bt.get((12, mo.year, L.GNAME[g]), np.nan) for mo, g in zip(one["month"], one["grp"])]
    one = one[one["b"].notna() & (one["eps_f12"] > 0)]
    act = np.log(one["px"]) + one["y12"] + one["orbit_lr"] - np.log(one["eps_f12"])
    pe = []
    for per, a_, b_ in (("2015–2021", "2015-01-01", "2021-12-31"), ("2022 以後", "2022-01-01", "2026-12-31"), ("全期", "2015-01-01", "2026-12-31")):
        g = one[(one["month"] >= a_) & (one["month"] <= b_)]
        r = dict(期間=per, n=len(g))
        for nm, p in [("原樣", 0.0)] + [(k, g[k]) for k in preds]:
            ea = g["feps"] * np.exp(p)
            lpx = np.log(g["px"]) + g["orbit_lr"] + g["b"] * np.log(ea / g["eps0"]).clip(-2, 2)
            r[nm] = float(np.median(np.abs(lpx - np.log(ea) - act.loc[g.index])))
        pe.append(r)
    pe = pd.DataFrame(pe)
    say("  12 個月後本益比的中位 |ln 誤差|（§18 的乾淨起點）")
    say(pe.round(4).to_string(index=False))
    return sc.assign(表="EPS"), pe.assign(表="PE")


def part_b(disp):
    say("\n== (b) 區間：分歧大的股票，股價偏離軌道是不是更多？")
    p = pd.read_csv(os.path.join(RES, "orbit_predictions.csv.gz"), parse_dates=["month"])
    p = p.merge(disp, on=["ticker", "month"], how="left")
    out = []
    for h in (6, 12, 24):
        z = p[p[f"y{h}"].notna() & (p["month"] + pd.DateOffset(months=h) <= pd.Timestamp("2025-09-30")) & p["disp"].notna()].copy()
        e = z[f"y{h}"].where(z[f"eps_f{h}"] > 0)                     # 軌道的誤差（2012 起最長；目標日虧損的另外放寬，這裡不算）
        z = z[e.notna()]
        e = e[e.notna()]
        vmed = float(z["vol36"].median())
        base = np.clip(z["vol36"].fillna(vmed), *cond.VOL_CLIP) ** cond.BAND_ALPHA
        u = e / base
        dq = pd.qcut(z["disp"].rank(method="first"), 5, labels=False)
        w = u.groupby(dq).apply(lambda v: np.quantile(v, 0.9) - np.quantile(v, 0.1))
        say(f"  {h} 個月：除以波動^0.7 之後的 10–90% 寬度，依分歧五分位：" + "  ".join(f"{v:.3f}" for v in w)
            + f"（最高 ÷ 最低 {w.iloc[-1] / w.iloc[0]:.2f}；n={len(z):,}）")
        for dl in DELTAS + ("走動式挑 δ",):
            res = []
            for Y in sorted({m.year for m in z["month"]}):
                cal = (z["month"] + pd.DateOffset(months=h)) < pd.Timestamp(f"{Y}-01-01")
                tst = z["month"].dt.year == Y
                if cal.sum() < 3000 or tst.sum() < 300:
                    continue
                dmed = float(z.loc[cal, "disp"].median())
                cand = DELTAS if dl == "走動式挑 δ" else (dl,)
                best = None
                for g in cand:
                    sc = base[cal] * (z.loc[cal, "disp"].clip(lower=0.005) / dmed) ** g
                    uu = e[cal] / sc
                    uu = uu - uu.median()
                    q = np.quantile(uu, [A / 2, 1 - A / 2])
                    isc = float(np.mean(iscore(uu.to_numpy(), q[0], q[1]) * sc.to_numpy()))
                    if best is None or isc < best[0]:
                        best = (isc, g, q)
                _, g, q = best
                st = base[tst] * (z.loc[tst, "disp"].clip(lower=0.005) / dmed) ** g
                lo, hi = q[0] * st, q[1] * st
                inside = (e[tst] >= lo) & (e[tst] <= hi)
                res.append(pd.DataFrame({"in": inside, "is": iscore(e[tst].to_numpy(), lo.to_numpy(), hi.to_numpy()), "dq": dq[tst]}))
            if not res:
                continue
            rr = pd.concat(res)
            cq = rr.groupby("dq")["in"].mean()
            out.append(dict(h=h, δ=dl, n=len(rr), 涵蓋=float(rr["in"].mean()), 區間分數=float(rr["is"].mean()),
                            分歧最低組涵蓋=float(cq.iloc[0]), 分歧最高組涵蓋=float(cq.iloc[-1]),
                            五組涵蓋和80差平均=float(np.mean(np.abs(cq - 0.8)))))
    t = pd.DataFrame(out)
    say("  走動式 80% 區間（δ＝0 是正式版；『五組』＝依分歧五分位的涵蓋率，越接近 80% 越好）")
    say(t.round(4).to_string(index=False))
    return t.assign(表="區間")


def yahoo_check(disp):
    """今天 Yahoo 的分歧（全距 ÷ d2(人數) ÷ |平均|）和 OSAP 最後一年的量級比較（同一批代號）。"""
    import glob
    f = sorted(glob.glob(os.path.join(HERE, "data", "consensus_snapshots", "yahoo_detail_*.csv.gz")))[-1]
    q = pd.read_csv(f)
    q["yd"] = (q["0y_high"] - q["0y_low"]) / q["0y_n"].map(d2) / q["0y_avg"].abs()
    q["ticker"] = q["symbol"].str.replace(".", "-", regex=False)
    last = disp[disp["month"] >= disp["month"].max() - pd.DateOffset(months=11)].groupby("ticker")["disp"].median()
    m = q.set_index("ticker")["yd"].to_frame().join(last, how="inner").dropna()
    say(f"\n== Yahoo 換算 vs OSAP（{os.path.basename(f)}；OSAP 最後 12 個月中位；{len(m):,} 檔）：中位 {m['yd'].median():.4f} vs {m['disp'].median():.4f}；"
        f"Spearman {m['yd'].corr(m['disp'], method='spearman'):+.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--build", default=None)
    a = ap.parse_args()
    disp = load_disp(a.raw)
    say(f"ForecastDispersion：{len(disp):,} 個公司月、{disp['ticker'].nunique()} 家（{disp['month'].min():%Y-%m}～{disp['month'].max():%Y-%m}）；"
        f"中位 {disp['disp'].median():.4f}")
    d = pd.read_pickle(a.build) if a.build and os.path.exists(a.build) else L.build(a.cache)
    d = L2.add_lead_bias(d)
    d = d.merge(disp, on=["ticker", "month"], how="left")
    say(f"共識校正的公司月 {len(d):,}；有分歧資料的 {d['disp'].notna().mean():.0%}")
    sc, pe = part_a(d)
    bd = part_b(disp)
    yahoo_check(disp)
    pd.concat([sc, pe, bd]).to_csv(os.path.join(RES, "dispersion_scores.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "dispersion.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
