#!/usr/bin/env python3
"""本益比軌道模型在中小型股（Russell 2000、S&P 400、S&P 600）準不準？區間夠不夠寬？（README §19.4）

    python3 lab_orbit_small.py [--cache <暫存目錄>]        # 第一次約 1 分鐘（建季頻面板），不訓練樹模型

資料：lab_small.py 的中小型股面板（1,390 家、季頻 2019-12～2026-09；股價來自指數 ETF 持股申報、財報來自 SEC 申報）。
模型完全不重估：直接用 S&P 500 估的正式版（results/orbit_model.json）——這是「搬到沒看過的股票」的樣本外檢驗。
  軌道：股價 × exp((10 年期＋5% − 股利殖利率) × h/12)；模型：軌道 × exp(β_a × ln(實際 EPS_h ÷ 今天 EPS))（原始成長a，β 依公司類型）。
  本益比不變：今天的本益比 × 實際 EPS_h。EPS 完全正確（上限）。只用今天與 h 個月後 EPS 都 > 0 的列（另報虧損占比）。
區間：正式版「原始成長a」的分位數 × 波動^0.7。波動＝過去 12 季季報酬的標準差 × 2（季資料，和 S&P 500 的月資料算法不同但同樣是年化）。
分組：起點當季是哪個指數的成分股（data/members_small.csv）。
輸出：results/orbit_small.txt、orbit_small_scores.csv；results/band_widen.json 的 "small"（中小型股區間放寬倍數，給 orbit_price.py 與網頁）
"""
import argparse
import io
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import orbit                                    # noqa: E402

RES = os.path.join(HERE, "results")
DATA = os.path.join(HERE, "data")
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def panel(cache):
    pk = os.path.join(cache, "small_cond.pkl") if cache else None
    if pk and os.path.exists(pk):
        return pd.read_pickle(pk)
    import lab_small as LS
    from pef import cond, lab
    dfL, qfL = LS.small_panel()
    c = cond.build(lab.build(dfL, qfL), dfL)
    if pk:
        os.makedirs(cache, exist_ok=True)
        c.to_pickle(pk)
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=None)
    a = ap.parse_args()
    c = panel(a.cache).sort_values(["ticker", "month"]).copy()
    model = json.load(open(os.path.join(RES, "orbit_model.json")))
    # 季報酬波動（年化）
    prev_px, prev_m = c.groupby("ticker")["px"].shift(1), c.groupby("ticker")["month"].shift(1)
    c["qret"] = np.where((c["month"] - prev_m).dt.days.between(80, 100), np.log(c["px"] / prev_px), np.nan)
    c["volq"] = c.groupby("ticker")["qret"].transform(lambda s: s.rolling(12, min_periods=8).std()) * 2
    c["grp"] = c["sector"].map(orbit.GROUPS).fillna("other") if "sector" in c else "other"
    mem = pd.read_csv(os.path.join(DATA, "members_small.csv"), parse_dates=["date"])
    mem["month"] = mem["date"] - pd.offsets.MonthBegin(1)
    for k in ("rut", "sp400", "sp600"):
        c[k] = c.set_index(["ticker", "month"]).index.isin(pd.MultiIndex.from_frame(mem[mem["idx"] == k][["ticker", "month"]]))
    c["orbit_lr"] = c["y10"] + model["erp"] - c["dy"].fillna(0)
    rows, cov = [], []
    for h in (6, 12):
        hm = model["h"][str(h)]
        b = {g: v[0] for g, v in hm["beta"]["原始成長a"].items()}
        band = hm["bands"]["原始成長a"]
        d = c[c[f"rp_{h}"].notna() & c[f"eps_f{h}"].notna() & c["eps0"].notna()].copy()
        n_all = len(d)
        loss = ((d["eps0"] <= 0) | (d[f"eps_f{h}"] <= 0)).mean()
        d = d[(d["eps0"] > 0) & (d[f"eps_f{h}"] > 0)]
        g = np.log(d[f"eps_f{h}"] / d["eps0"]).clip(-2, 2)
        dev = d[f"rp_{h}"] - d["orbit_lr"] * h / 12                       # 實際偏離軌道
        d["e_unch"] = g - d[f"rp_{h}"]
        d["e_orbit"] = -dev
        d["e_model"] = d["grp"].map(b) * g - dev
        vol = d["volq"].fillna(d["volq"].median())
        sc = np.clip(vol, *model["vol_clip"]) ** model["alpha"]
        u = (-d["e_model"]) / sc                                            # 實際 − 預測，除以波動^α
        d["in80"] = (u >= band["q"][0]) & (u <= band["q"][3])
        d["in50"] = (u >= band["q"][1]) & (u <= band["q"][2])
        uu = u - u.groupby(d["month"]).transform("median")                  # 扣掉當季大盤偏差後的寬度
        d["in80c"] = (uu >= band["q"][0]) & (uu <= band["q"][3])
        say(f"{h} 個月：{n_all:,} 列，其中今天或 {h} 個月後虧損 {loss:.0%}（不評分）；評分 {len(d):,} 列、{d['ticker'].nunique()} 家；"
            f"波動中位 {d['volq'].median():.0%}（S&P 500 正式版的中位 {band['vol_median']:.0%}）")
        for per, (lo, hi) in (("起點 2020–2022", ("2020-01-01", "2022-12-31")), ("起點 2023 以後", ("2023-01-01", "2026-12-31")),
                              ("全期", ("2020-01-01", "2026-12-31"))):
            for gn in ("rut", "sp400", "sp600", "全部"):
                m = (d["month"] >= lo) & (d["month"] <= hi)
                if gn != "全部":
                    m &= d[gn]
                dd = d[m]
                if len(dd) < 100:
                    continue
                r = dict(h=h, 期間=per, 指數={"rut": "Russell 2000", "sp400": "S&P 400", "sp600": "S&P 600"}.get(gn, gn), n=len(dd),
                         家數=dd["ticker"].nunique())
                for k, lab in (("e_unch", "本益比不變"), ("e_orbit", "軌道"), ("e_model", "模型")):
                    r[lab] = float(np.median(np.abs(dd[k])))
                    r[lab + "_±20%"] = float(np.mean(np.abs(np.exp(dd[k]) - 1) <= 0.2))
                r["80%涵蓋"] = float(dd["in80"].mean())
                r["50%涵蓋"] = float(dd["in50"].mean())
                r["80%涵蓋_扣大盤"] = float(dd["in80c"].mean())
                r["偏離軌道中位"] = float(np.median(-dd["e_orbit"]))
                rows.append(r)
        # 區間要放寬多少才夠：讓 80% 區間在中小型股涵蓋 80% 的倍數
        w = np.quantile(np.abs(uu - np.median(uu)), 0.8) / max(abs(band["q"][0]), abs(band["q"][3]))
        # 不扣大盤（單一股票的使用者事先不知道大盤會怎麼偏）：把 80% 區間放寬幾倍，涵蓋率才到 80%（二分搜尋，期間分開看穩不穩）
        def need(uv):
            lo_, hi_ = 0.5, 3.0
            for _ in range(40):
                m_ = (lo_ + hi_) / 2
                lo_, hi_ = (m_, hi_) if ((uv >= band["q"][0] * m_) & (uv <= band["q"][3] * m_)).mean() < 0.8 else (lo_, m_)
            return hi_
        early = (d["month"] < "2023-01-01").to_numpy()
        cov.append(dict(h=h, 扣大盤後需要的倍數=float(w), 不扣大盤需要的倍數=float(need(u.to_numpy())),
                        不扣大盤_2020_2022=float(need(u.to_numpy()[early])), 不扣大盤_2023以後=float(need(u.to_numpy()[~early]))))
    sc = pd.DataFrame(rows)
    say("\n== 中位 |ln 誤差|（EPS 完全正確；本益比與股價的 ln 誤差相同）、±20% 命中、區間涵蓋（目標 80%／50%）")
    say(sc[["h", "期間", "指數", "n", "家數", "本益比不變", "軌道", "模型", "本益比不變_±20%", "模型_±20%", "80%涵蓋", "50%涵蓋", "80%涵蓋_扣大盤",
            "偏離軌道中位"]].round(3).to_string(index=False))
    say("\n== 區間放寬：讓 80% 區間在中小型股真的涵蓋 80% 需要的倍數（扣掉當季大盤偏差後＝只看個股；不扣＝單一股票使用者實際面對的）")
    say(pd.DataFrame(cov).round(3).to_string(index=False))
    # S&P 500 同期對照（月頻 → 取季末月份，起點 2020-12 以後）
    p = pd.read_csv(os.path.join(RES, "orbit_predictions.csv.gz"), parse_dates=["month"])
    p = p[(p["month"] >= "2020-12-01") & (p["month"].dt.month.isin([3, 6, 9, 12])) & p["y12"].notna() & p["p12_原始成長a"].notna()]
    say(f"\n對照 S&P 500 同期（季末起點 2020-12 以後、12 個月）：本益比不變 {np.median(np.abs(p['g12'] - (p['y12'] + p['orbit_lr']))):.3f}、"
        f"軌道 {np.median(np.abs(p['y12'])):.3f}、模型 {np.median(np.abs(p['p12_原始成長a'] - p['y12'])):.3f}（n={len(p):,}）")
    sc.to_csv(os.path.join(RES, "orbit_small_scores.csv"), index=False, float_format="%.6f")
    bw_path = os.path.join(RES, "band_widen.json")
    bw = json.load(open(bw_path)) if os.path.exists(bw_path) else {}
    w = {str(r["h"]): round(r["不扣大盤需要的倍數"], 3) for r in cov}
    w["24"] = w["12"]                                                       # 24 個月沒有測（季資料太短），沿用 12 個月
    bw["small"] = dict(h=w, note="不在 S&P 500／Nasdaq-100 的股票：80% 區間放寬倍數（lab_orbit_small.py，2020–2026，不扣大盤）")
    json.dump(bw, open(bw_path, "w"), ensure_ascii=False, indent=1)
    open(os.path.join(RES, "orbit_small.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
