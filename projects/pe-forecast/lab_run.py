#!/usr/bin/env python3
"""改良實驗：用過去資料推估「h 個月後」的本益比——哪個距離最有效？哪個方法最好？

    python3 lab_run.py        # 約 6 分鐘。需要 results/predictions.csv.gz（舊模型；沒有就先跑 pe_forecast.py backtest）

程序（全部走動式、樣本外）：每年 1 月只用「t+h ≤ 那天」已揭曉的配對訓練，預測當年每個月的 h 個月後本益比。
評分只看「今天和 h 月後都有正盈餘」的列；對手是隨機漫步（h 月後本益比 ＝ 今天的本益比）。
選模期 2015–2021 決定方法，保留期 2022–2026 只看不調。README §12 的每個數字都由這支產生：

  results/lab.txt               人看的表
  results/lab_scores.csv        長表（期間 × 距離 × 方法）
  results/lab_horizon.csv       每個距離的組合模型成績（pe_forecast.py predict 會讀）
  results/lab_hits.csv          命中率（±10/20/30% 內、方向）與「你給盈餘」情境區間的實測涵蓋率
  results/lab_predictions.csv.gz 每一筆走動式預測（predict 的 80% 區間用它）
"""
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import lab                                     # noqa: E402
from pef.ensemble import MEMBERS, OLD_H, combine, members_for, return_surprise   # noqa: E402
from pef.load import panel                              # noqa: E402

RES = os.path.join(HERE, "results")
PERIODS = {"選模期": ("2015-01-01", "2021-12-31"), "保留期": ("2022-01-01", "2026-12-31"),
           "全期": ("2015-01-01", "2026-12-31")}
pd.set_option("display.width", 250)
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def table(title, t):
    say(f"\n== {title}")
    say(t.to_string())


def attach_old(p):
    old = pd.read_csv(os.path.join(RES, "predictions.csv.gz"), parse_dates=["month"])
    p["old"] = np.nan
    for h in OLD_H:
        m = p["h"] == h
        p.loc[m, "old"] = p.loc[m, ["ticker", "month"]].merge(
            old[["ticker", "month", f"lnpe_hat_{h}"]], on=["ticker", "month"], how="left")[f"lnpe_hat_{h}"].to_numpy()
    return p


def add_ens(p, members=MEMBERS, name="ens", with_old=True):
    p[name] = np.nan
    for h in p["h"].unique():
        m = p["h"] == h
        cols = members_for(h) if with_old else list(members)
        p.loc[m, name] = combine(p.loc[m, cols]).to_numpy()
    return p


def period(g, per):
    lo, hi = PERIODS[per]
    return g[(g["month"] >= lo) & (g["month"] <= hi)]


def horizon_rows(p, d, col="ens", tag="GAAP"):
    """每個距離：組合 vs 隨機漫步 vs 「盈餘完美預知」（知道未來真實盈餘、報酬仍用資金成本）。"""
    rows = []
    for h in lab.HORIZONS:
        g = p[(p["h"] == h) & p["actual"].notna() & p["ln_pe"].notna() & p[col].notna()]
        g = g.merge(d[["ticker", "month", "mc", "y10", f"ni_ttm_f{h}"]], on=["ticker", "month"], how="left")
        fe = g[f"ni_ttm_f{h}"]
        g["oracle"] = np.log(g["mc"]) + (g["y10"] + lab.ERP) * h / 12 - np.log(fe.where(fe > 0))
        for per in PERIODS:
            gg = period(g, per)
            if len(gg) < 30:
                continue
            e_m, e_r = gg[col] - gg["actual"], gg["ln_pe"] - gg["actual"]
            mae_m, mae_r = float(e_m.abs().median()), float(e_r.abs().median())
            mae_o = float((gg["oracle"] - gg["actual"]).abs().median())
            common = e_m.groupby(gg["month"]).transform("median")
            rows.append({"口徑": tag, "期間": per, "h": h, "n": len(gg),
                         "隨機漫步_誤差": mae_r, "組合_誤差": mae_m, "改善": mae_m / mae_r - 1,
                         "OOS_R2": float(1 - np.sum(np.minimum(e_m ** 2, 4)) / np.sum(np.minimum(e_r ** 2, 4))),
                         "方向命中": float(np.mean(np.sign(gg[col] - gg["ln_pe"]) == np.sign(gg["actual"] - gg["ln_pe"]))),
                         "盈餘全知_誤差": mae_o,
                         "拿到可預測部分": (mae_r - mae_m) / (mae_r - mae_o) if mae_r > mae_o else np.nan,
                         "大盤共同誤差占比": float(common.var() / e_m.var())})
    return pd.DataFrame(rows)


def band_coverage(p, col="ens"):
    """80% 區間的走動式實測：每年用當時已揭曉的誤差分位數畫區間，看當年實際有多少落在裡面。"""
    rows = []
    q = p[p["actual"].notna() & p[col].notna()].copy()
    q["e"] = q["actual"] - q[col]
    q["tgt_end"] = q["month"] + pd.offsets.MonthEnd(0)
    for h in lab.HORIZONS:
        g = q[q["h"] == h]
        g_tgt = g["tgt_end"] + pd.DateOffset(months=h)
        hit, width = [], []
        for Y in sorted(g["fit_year"].unique()):
            asof = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
            past = g[g_tgt <= asof]["e"]
            cur = g[g["fit_year"] == Y]["e"]
            if len(past) < 300 or cur.empty:
                continue
            lo, hi = past.quantile(0.1), past.quantile(0.9)
            hit += list(((cur >= lo) & (cur <= hi)).to_numpy())
            width.append((np.exp(lo) - 1, np.exp(hi) - 1))
        if hit:
            w = np.array(width)
            rows.append({"h": h, "n": len(hit), "實測涵蓋率": float(np.mean(hit)),
                         "區間下緣中位": float(np.median(w[:, 0])), "區間上緣中位": float(np.median(w[:, 1]))})
    return pd.DataFrame(rows)


def hit_rates(p, col="ens"):
    """直覺版命中率（全期 2015–2026）：預測落在實際 ±10/20/30% 內的比例、方向命中、本益比大變動時的方向命中。"""
    rows = []
    g0 = period(p[p["actual"].notna() & p["ln_pe"].notna() & p[col].notna()], "全期")
    for h, g in g0.groupby("h"):
        em, er = (g[col] - g["actual"]).abs(), (g["ln_pe"] - g["actual"]).abs()
        up_m, up_a = np.sign(g[col] - g["ln_pe"]), np.sign(g["actual"] - g["ln_pe"])
        big = (g["actual"] - g["ln_pe"]).abs() > np.log(1.2)
        r = {"h": h, "n": len(g)}
        for k in (0.1, 0.2, 0.3):
            r[f"組合_±{int(k * 100)}%內"] = float((em <= np.log(1 + k)).mean())
            r[f"不變_±{int(k * 100)}%內"] = float((er <= np.log(1 + k)).mean())
        r.update({"方向命中": float((up_m == up_a).mean()), "大變動占比": float(big.mean()),
                  "大變動時方向命中": float((up_m == up_a)[big].mean()), "組合比不變準的比例": float((em < er).mean())})
        rows.append(r)
    return pd.DataFrame(rows)


def return_band_coverage(d):
    """你自己給盈餘時的 80% 區間（pef.ensemble.return_bands）：假設盈餘完全正確，只剩「實際報酬 − 資金成本」。
    走動式實測：每年用當時已揭曉的分位數畫區間，看當年的實際落點。"""
    rows = []
    for h in lab.HORIZONS:
        r = return_surprise(d, h)
        tgt = r["month_end"] + pd.DateOffset(months=h)
        hit, width = [], []
        for Y in range(2015, 2027):
            asof = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
            past = r[tgt <= asof]["e"]
            cur = r[r["month_end"].dt.year == Y]["e"]
            if len(past) < 300 or cur.empty:
                continue
            lo, hi = past.quantile(0.1), past.quantile(0.9)
            hit += list(((cur >= lo) & (cur <= hi)).to_numpy())
            width.append((np.exp(lo) - 1, np.exp(hi) - 1))
        if hit:
            w = np.array(width)
            rows.append({"h": h, "n": len(hit), "實測涵蓋率": float(np.mean(hit)),
                         "區間下緣中位": float(np.median(w[:, 0])), "區間上緣中位": float(np.median(w[:, 1]))})
    return pd.DataFrame(rows)


def near_now(p, d, col="ens"):
    """「用過去推到現在」：每家公司資料的最後 12 個月當目標月（以及只看最後一個月）。"""
    last = d.groupby("ticker")["month"].max()
    rows = []
    for h in lab.HORIZONS:
        g = p[(p["h"] == h) & p["actual"].notna() & p["ln_pe"].notna() & p[col].notna()].copy()
        g["tgt"] = g["month"] + pd.DateOffset(months=h)
        g["last"] = g["ticker"].map(last)
        for win, lab_ in ((12, "最後12個月"), (1, "最後1個月")):
            gg = g[g["tgt"] > g["last"] - pd.DateOffset(months=win)]
            if len(gg) < 20:
                continue
            gg = gg.assign(em=(gg[col] - gg["actual"]).abs(), er=(gg["ln_pe"] - gg["actual"]).abs())
            per_co = gg.groupby("ticker")[["em", "er"]].median()
            rows.append({"窗口": lab_, "h": h, "公司數": len(per_co), "n": len(gg),
                         "隨機漫步_誤差": float(gg["er"].median()), "組合_誤差": float(gg["em"].median()),
                         "改善": float(gg["em"].median() / gg["er"].median() - 1),
                         "組合贏的公司比例": float((per_co["em"] < per_co["er"]).mean())})
    return pd.DataFrame(rows)


def core_panel(d):
    """核心本益比：市值 ÷ (營業利益TTM × 0.85)。把目標換成核心口徑，其餘程序不變。"""
    dc = d.copy()
    dc["core_ttm"] = dc["oi_ttm"] * 0.85
    dc["ln_pe"] = np.log(dc["mc"] / dc["core_ttm"].where(dc["core_ttm"] > 0))
    for h in lab.HORIZONS:
        fut = dc[["ticker", "month", "core_ttm", "ln_pe"]].copy()
        fut["month"] = fut["month"] - pd.DateOffset(months=h)
        fut = fut.rename(columns={"core_ttm": f"core_f{h}", "ln_pe": f"lncpe_f{h}"})
        dc = dc.merge(fut, on=["ticker", "month"], how="left")
        dc[f"y_{h}"] = (dc[f"core_f{h}"] / dc["mc"]).clip(-0.5, 0.5)
        dc[f"z_{h}"] = dc[f"lncpe_f{h}"] - dc["ln_pe"]
        dc[f"ln_pe_f{h}"] = dc[f"lncpe_f{h}"]
        dc[f"ni_ttm_f{h}"] = dc[f"core_f{h}"]            # 「盈餘完美預知」也換成核心口徑
    return dc[dc["core_ttm"].notna()]


def main():
    df, qf = panel()
    d = lab.build(df, qf)
    say(f"面板：{d['ticker'].nunique()} 家科技股，{d['month'].min():%Y-%m} ~ {d['month'].max():%Y-%m}，{len(d):,} 個公司月")

    # 1) 各方法（GAAP 本益比）
    p = lab.walk(d, ["run_rate", "huber", "gbm", "gbm_z", "gbm_hist", "gbm_z_hist"])
    p = attach_old(p)
    p = add_ens(p)                                                    # 最終組合（6/12/24/36 含舊模型）
    p = add_ens(p, name="ens3", with_old=False)                       # 不含舊模型
    p = add_ens(p, members=("huber", "gbm_hist", "gbm_z_hist"), name="ens3_hist", with_old=False)
    scores = []
    for per in ("選模期", "保留期"):
        s = lab.score(p, ["run_rate", "huber", "gbm", "gbm_z", "ens3", "ens"], PERIODS[per]).assign(期間=per, 比較="各方法")
        scores.append(s)
        table(f"{per}｜各方法 中位絕對誤差（ln，0.25 ≈ ±25%；共同樣本）", s.pivot(index="方法", columns="h", values="中位絕對誤差").round(3))
        table(f"{per}｜各方法 OOS R²（相對隨機漫步；> 0 ＝ 比「本益比不變」好）", s.pivot(index="方法", columns="h", values="OOS_R2").round(3))
        q = p[p["h"].isin(OLD_H)]
        s = lab.score(q, ["old", "ens3", "ens"], PERIODS[per]).assign(期間=per, 比較="舊模型")
        scores.append(s)
        table(f"{per}｜舊模型 vs 組合（只在 6/12/24/36 月）OOS R²", s.pivot(index="方法", columns="h", values="OOS_R2").round(3))
        s = lab.score(p, ["ens3", "ens3_hist"], PERIODS[per]).assign(期間=per, 比較="歷史本益比特徵")
        scores.append(s)
        table(f"{per}｜加「自己過去 5 年／同業／全體中位本益比」特徵 OOS R²", s.pivot(index="方法", columns="h", values="OOS_R2").round(3))

    # 2) 距離表
    hz = horizon_rows(p, d)
    table("最終組合 × 預測距離（誤差＝中位 |ln 預測 − ln 實際|）",
          hz.drop(columns=["口徑"]).set_index(["期間", "h"]).round(3))
    cov = band_coverage(p)
    table("80% 區間走動式實測（每年用當時已揭曉的誤差畫區間）", cov.set_index("h").round(3))
    nn = near_now(p, d)
    table("用過去推到「現在」：每家公司資料的最後 12 個月／最後 1 個月當目標", nn.set_index(["窗口", "h"]).round(3))
    q = p[p["h"].isin(OLD_H) & p["old"].notna() & p["ens"].notna()]
    nn_old = near_now(q, d, col="old").merge(near_now(q, d, col="ens"), on=["窗口", "h", "公司數", "n", "隨機漫步_誤差"],
                                             suffixes=("_舊模型", "_組合"))
    table("同上，舊模型 vs 組合（共同樣本）", nn_old[["窗口", "h", "公司數", "n", "隨機漫步_誤差", "組合_誤差_舊模型", "組合_誤差_組合",
                                          "組合贏的公司比例_舊模型", "組合贏的公司比例_組合"]].rename(
        columns={"組合_誤差_舊模型": "舊模型_誤差", "組合_誤差_組合": "組合_誤差",
                 "組合贏的公司比例_舊模型": "舊模型贏RW的公司比例", "組合贏的公司比例_組合": "組合贏RW的公司比例"}).set_index(["窗口", "h"]).round(3))

    hits = hit_rates(p)
    table("命中率（全期 2015–2026）：落在實際 ±10/20/30% 內的比例；大變動＝實際本益比變動超過 20%", hits.set_index("h").round(3))
    rcov = return_band_coverage(d)
    table("你自己給盈餘（且完全正確）時的 80% 區間：只剩股價的不確定（走動式實測）", rcov.set_index("h").round(3))

    # 3) 產業（12 個月，全期）
    g = period(p[(p["h"] == 12) & p["actual"].notna() & p["ln_pe"].notna() & p["ens"].notna()], "全期")
    sec = g.assign(em=(g["ens"] - g["actual"]).abs(), er=(g["ln_pe"] - g["actual"]).abs()).groupby("sector").agg(
        n=("em", "size"), 隨機漫步_誤差=("er", "median"), 組合_誤差=("em", "median"))
    sec["改善"] = sec["組合_誤差"] / sec["隨機漫步_誤差"] - 1
    table("12 個月｜各產業（全期 2015–2026）", sec.round(3))

    # 4) 核心本益比
    dc = core_panel(d)
    pc = lab.walk(dc, list(MEMBERS))
    pc = add_ens(pc, name="ens", with_old=False)
    hzc = horizon_rows(pc, dc, tag="核心")
    table("核心本益比（市值 ÷ 營業利益TTM×0.85）× 預測距離", hzc.drop(columns=["口徑"]).set_index(["期間", "h"]).round(3))

    # 輸出
    pd.concat(scores, ignore_index=True).to_csv(os.path.join(RES, "lab_scores.csv"), index=False, float_format="%.4f")
    pd.concat([hz, hzc], ignore_index=True).to_csv(os.path.join(RES, "lab_horizons_all.csv"), index=False, float_format="%.4f")
    full = hz[hz["期間"] == "全期"][["h", "n", "隨機漫步_誤差", "組合_誤差", "改善", "OOS_R2", "方向命中"]]
    full.merge(cov[["h", "實測涵蓋率"]], on="h", how="left").to_csv(os.path.join(RES, "lab_horizon.csv"), index=False, float_format="%.4f")
    nn.to_csv(os.path.join(RES, "lab_near_now.csv"), index=False, float_format="%.4f")
    hits.merge(rcov.add_prefix("情境區間_").rename(columns={"情境區間_h": "h"}), on="h", how="left").to_csv(
        os.path.join(RES, "lab_hits.csv"), index=False, float_format="%.4f")
    keep = ["ticker", "month", "h", "fit_year", "sector", "ln_pe", "actual", "old"] + list(MEMBERS) + ["ens"]
    p[keep].to_csv(os.path.join(RES, "lab_predictions.csv.gz"), index=False, float_format="%.4f")
    open(os.path.join(RES, "lab.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
