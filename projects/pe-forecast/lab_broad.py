#!/usr/bin/env python3
"""S&P 500 全體回測：模型能不能推廣到所有美股？哪裡還能提高準確度？

    python3 lab_broad.py --cache <暫存目錄>      # 第一次約 30 分鐘（之後讀暫存，幾十秒）

資料：build_broad.py 產出的 480 家 S&P 500（2009 → 2025-09）。程序與 lab_run.py 相同（走動式、樣本外，
選模期 2015–2021 決定、保留期 2022–2026 只看）。比較：

  A. 訓練名單：只用 68 家科技股（現行） vs 用全部 S&P 500
  B. 多兩個特徵：股利殖利率、淨負債 ÷ 市值
  C. 報酬假設：資金成本（現行）、CAPM beta、同產業過去 10 年中位報酬、全體過去 10 年中位報酬、零
輸出：results/broad.txt、broad_scores.csv、broad_sector.csv、broad_horizon.csv、broad_bands.csv
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import backtest as bt                      # noqa: E402
from pef import lab                                 # noqa: E402
from pef.ensemble import OLD_H, combine             # noqa: E402
from pef.load import panel_sp500                    # noqa: E402

RES = os.path.join(HERE, "results")
PERIODS = {"選模期": ("2015-01-01", "2021-12-31"), "保留期": ("2022-01-01", "2026-12-31"), "全期": ("2015-01-01", "2026-12-31")}
GICS_ZH = {"Information Technology": "資訊科技", "Communication Services": "通訊服務", "Consumer Discretionary": "非必需消費",
           "Consumer Staples": "必需消費", "Health Care": "醫療保健", "Financials": "金融", "Industrials": "工業",
           "Energy": "能源", "Utilities": "公用事業", "Real Estate": "不動產", "Materials": "原物料"}
pd.set_option("display.width", 250)
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def table(title, t):
    say(f"\n== {title}")
    say(t.to_string())


def cached(cache, name, fn):
    path = os.path.join(cache, f"broad_{name}.pkl")
    if os.path.exists(path):
        return pd.read_pickle(path)
    x = fn()
    x.to_pickle(path)
    return x


def old_preds(df, tag, cache):
    def run():
        pred, _ = bt.run(df, start_year=2015, verbose=False)
        keep = ["ticker", "month"] + [f"lnpe_hat_{h}" for h in OLD_H] + [f"ni_hat_{h}" for h in OLD_H]
        return pred[keep]
    return cached(cache, f"old_{tag}", run)


def attach_old(p, old, col):
    p[col] = np.nan
    for h in OLD_H:
        m = p["h"] == h
        v = p.loc[m, ["ticker", "month"]].merge(old[["ticker", "month", f"lnpe_hat_{h}", f"ni_hat_{h}"]],
                                                 on=["ticker", "month"], how="left")
        p.loc[m, col] = np.where(v[f"ni_hat_{h}"] > 0, v[f"lnpe_hat_{h}"], np.nan)
    return p


def ens(p, cols_by_h):
    out = pd.Series(np.nan, index=p.index)
    for h in lab.HORIZONS:
        m = p["h"] == h
        cols = cols_by_h(h)
        if all(c in p for c in cols):
            out[m] = combine(p.loc[m, cols]).to_numpy()
    return out


def sector_returns(d, h, years=10):
    """每個訓練年度：同產業、過去 10 年已揭曉的 h 個月報酬中位數（ln）。回傳 {(年, 產業): 報酬}、{年: 全體}。"""
    x = d[d[f"mc_f{h}"].notna() & (d["mc"] > 0)][["month_end", "gics", f"mc_f{h}", "mc"]].copy()
    x["r"] = np.log(x[f"mc_f{h}"] / x["mc"])
    sec, allm = {}, {}
    for Y in range(2015, 2027):
        asof = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        w = x[(x["month_end"] + pd.DateOffset(months=h) <= asof) & (x["month_end"] > asof - pd.DateOffset(years=years))]
        allm[Y] = float(w["r"].median())
        for g, v in w.groupby("gics")["r"]:
            sec[(Y, g)] = float(v.median())
    return sec, allm


def score_subsets(p, methods, tag):
    rows = []
    for per in ("選模期", "保留期"):
        for sub, mask in (("全部", None), ("科技股名單", lambda g: g["in_tech"].astype(bool)),
                          ("非科技股", lambda g: ~g["in_tech"].astype(bool))):
            s = lab.score(p, methods, PERIODS[per], extra_mask=mask)
            rows.append(s.assign(期間=per, 樣本=sub, 比較=tag))
    return pd.concat(rows, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    df, qf = panel_sp500()
    d = lab.build(df, qf)
    say(f"面板：{d['ticker'].nunique()} 家 S&P 500 公司，{d['month'].min():%Y-%m} ~ {d['month'].max():%Y-%m}，{len(d):,} 個公司月"
        f"（其中 {d[d['in_tech']]['ticker'].nunique()} 家在 68 家科技股名單）")

    # ── 走動式預測 ──
    base = ["huber", "gbm", "gbm_z"]
    pA = cached(a.cache, "walk_all", lambda: lab.walk(d, base))
    pT = cached(a.cache, "walk_tech", lambda: lab.walk(d, base, train_col="in_tech"))
    pB = cached(a.cache, "walk_b", lambda: lab.walk(d, ["gbm_b", "gbm_z_b"], horizons=OLD_H))
    oA = old_preds(df, "all", a.cache)
    oT = old_preds(df.assign(train=df["in_tech"]), "tech", a.cache)
    key = ["ticker", "month", "h"]
    p = pA.rename(columns={m: m + "_A" for m in base})
    p = p.merge(pT[key + base].rename(columns={m: m + "_T" for m in base}), on=key, how="left")
    p = p.merge(pB[key + ["gbm_b", "gbm_z_b"]], on=key, how="left")
    p = p.merge(d[["ticker", "month", "gics", "in_tech", "y10", "beta"]], on=["ticker", "month"], how="left")
    p = attach_old(p, oA, "old_A")
    p = attach_old(p, oT, "old_T")
    old_if = lambda h, c: [c] if h in OLD_H else []
    p["E_tech"] = ens(p, lambda h: old_if(h, "old_T") + ["huber_T", "gbm_T", "gbm_z_T"])
    p["E_all"] = ens(p, lambda h: old_if(h, "old_A") + ["huber_A", "gbm_A", "gbm_z_A"])
    p["E_all_b"] = ens(p, lambda h: (old_if(h, "old_A") + ["huber_A", "gbm_b", "gbm_z_b"]) if h in OLD_H else ["_na"])

    # ── A、B：訓練名單與額外特徵 ──
    scores = []
    for h_set, methods, tag in (((3, 6, 9, 12, 18, 24, 36), ["E_tech", "E_all"], "訓練名單"),
                                (OLD_H, ["E_all", "E_all_b"], "額外特徵")):
        q = p[p["h"].isin(h_set)]
        s = score_subsets(q, methods, tag)
        scores.append(s)
        for per in ("選模期", "保留期"):
            for sub in ("全部", "科技股名單", "非科技股"):
                x = s[(s["期間"] == per) & (s["樣本"] == sub)]
                table(f"{tag}｜{per}｜{sub}：OOS R²（相對本益比不變）", x.pivot(index="方法", columns="h", values="OOS_R2").round(3))
            x = s[(s["期間"] == per) & (s["樣本"] == "全部")]
            table(f"{tag}｜{per}｜全部：典型誤差（中位 |ln|）", x.pivot(index="方法", columns="h", values="中位絕對誤差").round(3))

    # ── C：報酬假設（只動「預測盈餘」的成員；樹-本益比變化不受影響）──
    coe = (p["y10"] + lab.ERP) * p["h"] / 12
    beta = p["beta"].where(np.isfinite(p["beta"]), 1.0).fillna(1.0)
    shifts = {"資金成本": pd.Series(0.0, index=p.index),
              "CAPM beta": (p["y10"] + beta * lab.ERP) * p["h"] / 12 - coe,
              "零": -coe}
    sec_r, mkt_r = {}, {}
    for h in lab.HORIZONS:
        sec_r[h], mkt_r[h] = sector_returns(d, h)
    fy = p["month"].dt.year
    shifts["同產業過去10年"] = pd.Series([sec_r[h].get((y, g), mkt_r[h].get(y, np.nan)) for h, y, g in zip(p["h"], fy, p["gics"])],
                                  index=p.index) - coe
    shifts["全體過去10年"] = pd.Series([mkt_r[h].get(y, np.nan) for h, y in zip(p["h"], fy)], index=p.index) - coe
    rv = []
    for name, dlt in shifts.items():
        col = "R_" + name
        cols = {}
        for c in ("old_A", "huber_A", "gbm_A"):
            cols[c] = p[c] + dlt
        tmp = p.assign(**{c + "_s": v for c, v in cols.items()})
        p[col] = ens(tmp, lambda h: old_if(h, "old_A_s") + ["huber_A_s", "gbm_A_s", "gbm_z_A"])
        rv.append(col)
    q = p[p["h"].isin((6, 12, 24, 36))]
    s = score_subsets(q, rv, "報酬假設")
    scores.append(s)
    for per in ("選模期", "保留期"):
        x = s[(s["期間"] == per) & (s["樣本"] == "全部")]
        table(f"報酬假設｜{per}｜全部：OOS R²", x.pivot(index="方法", columns="h", values="OOS_R2").round(3))
        table(f"報酬假設｜{per}｜全部：典型誤差", x.pivot(index="方法", columns="h", values="中位絕對誤差").round(3))

    # ── D：樹模型參數（資料多了 10 倍，大一點的樹會不會更好？只測 12、24 個月）──
    hp = []
    for name, tag, params in (("big", "大樹（31 葉、每葉 ≥200、600 輪）", dict(max_iter=600, max_leaf_nodes=31, min_samples_leaf=200)),
                              ("lr", "小學習率（0.03、600 輪）", dict(max_iter=600, learning_rate=0.03))):
        def run(params=params):
            saved = dict(lab.GBM_PARAMS)
            lab.GBM_PARAMS.update(params)
            try:
                return lab.walk(d, ["gbm", "gbm_z"], horizons=(12, 24))
            finally:
                lab.GBM_PARAMS.clear(); lab.GBM_PARAMS.update(saved)
        pn = cached(a.cache, "hp_" + name, run).rename(columns={"gbm": "gbm_n", "gbm_z": "gbm_z_n"})
        q = p[p["h"].isin((12, 24))].merge(pn[key + ["gbm_n", "gbm_z_n"]], on=key, how="left")
        q["E_hp"] = ens(q, lambda h: old_if(h, "old_A") + ["huber_A", "gbm_n", "gbm_z_n"])
        for per in ("選模期", "保留期"):
            s_ = lab.score(q, ["E_all", "E_hp"], PERIODS[per])
            for r in s_.itertuples():
                if r.方法 != "rw":
                    hp.append({"參數": tag, "期間": per, "h": r.h, "方法": "現行" if r.方法 == "E_all" else "新參數", "OOS_R2": r.OOS_R2,
                               "典型誤差": r.中位絕對誤差})
    hp = pd.DataFrame(hp)
    table("樹模型參數（組合的 OOS R²）", hp.pivot_table(index=["參數", "方法"], columns=["期間", "h"], values="OOS_R2").round(3))
    scores.append(hp.rename(columns={"參數": "比較"}).assign(樣本="全部"))

    # ── 各產業（12 個月、全期）──
    g = p[(p["h"] == 12) & p["actual"].notna() & p["ln_pe"].notna() & p["E_all"].notna() & p["E_tech"].notna()]
    g = g[(g["month"] >= "2015-01-01")]
    sec = []
    for gi, x in g.groupby("gics"):
        er = (x["ln_pe"] - x["actual"]).abs()
        row = {"產業": GICS_ZH.get(gi, gi), "gics": gi, "n": len(x), "公司數": x["ticker"].nunique(), "本益比不變": er.median()}
        for m in ("E_tech", "E_all"):
            e = (x[m] - x["actual"]).abs()
            row[m] = e.median()
            row[m + "_R2"] = 1 - np.sum(np.minimum((x[m] - x["actual"]) ** 2, 4)) / np.sum(np.minimum((x["ln_pe"] - x["actual"]) ** 2, 4))
        row["方向命中_all"] = float(np.mean(np.sign(x["E_all"] - x["ln_pe"]) == np.sign(x["actual"] - x["ln_pe"])))
        sec.append(row)
    sec = pd.DataFrame(sec).sort_values("E_all")
    table("12 個月｜各 GICS 產業（全期 2015–2026）：典型誤差與 R²", sec.drop(columns=["gics"]).set_index("產業").round(3))

    # ── 採用的模型（E_all）× 預測距離：全部 S&P 500 ──
    rows = []
    for h in lab.HORIZONS:
        x = p[(p["h"] == h) & p["actual"].notna() & p["ln_pe"].notna() & p["E_all"].notna()]
        for per in PERIODS:
            lo, hi = PERIODS[per]
            y = x[(x["month"] >= lo) & (x["month"] <= hi)]
            em, er = y["E_all"] - y["actual"], y["ln_pe"] - y["actual"]
            rows.append({"期間": per, "h": h, "n": len(y), "本益比不變": float(er.abs().median()), "模型": float(em.abs().median()),
                         "改善": float(em.abs().median() / er.abs().median() - 1),
                         "OOS_R2": float(1 - np.sum(np.minimum(em ** 2, 4)) / np.sum(np.minimum(er ** 2, 4))),
                         "方向命中": float(np.mean(np.sign(y["E_all"] - y["ln_pe"]) == np.sign(y["actual"] - y["ln_pe"]))),
                         "±20%內": float((em.abs() <= np.log(1.2)).mean()), "±20%內_不變": float((er.abs() <= np.log(1.2)).mean()),
                         "±30%內": float((em.abs() <= np.log(1.3)).mean()), "±30%內_不變": float((er.abs() <= np.log(1.3)).mean()),
                         "大變動時方向命中": float(np.mean((np.sign(y["E_all"] - y["ln_pe"]) == np.sign(y["actual"] - y["ln_pe"]))[er.abs() > np.log(1.2)])),
                         "組合比不變準": float((em.abs() < er.abs()).mean())})
    hz = pd.DataFrame(rows)
    table("全部 S&P 500 × 預測距離（模型＝用全部 S&P 500 訓練的組合）", hz.set_index(["期間", "h"]).round(3))

    # 推到現在（每家最後 12 個月當目標）
    last = d.groupby("ticker")["month"].max()
    nn = []
    for h in lab.HORIZONS:
        x = p[(p["h"] == h) & p["actual"].notna() & p["ln_pe"].notna() & p["E_all"].notna()].copy()
        x = x[x["month"] + pd.DateOffset(months=h) > x["ticker"].map(last) - pd.DateOffset(months=12)]
        x = x.assign(em=(x["E_all"] - x["actual"]).abs(), er=(x["ln_pe"] - x["actual"]).abs())
        pc = x.groupby("ticker")[["em", "er"]].median()
        nn.append({"h": h, "公司數": len(pc), "n": len(x), "本益比不變": float(x["er"].median()), "模型": float(x["em"].median()),
                   "模型較準的公司": float((pc["em"] < pc["er"]).mean())})
    nn = pd.DataFrame(nn)
    table("推到現在（每家公司最後 12 個月當目標）", nn.set_index("h").round(3))

    # 80% 區間（給 predict／網頁用）：到 2025-09 為止已揭曉的組合誤差分位數，另存走動式涵蓋率
    bands = []
    for h in lab.HORIZONS:
        x = p[(p["h"] == h) & p["actual"].notna() & p["E_all"].notna()].copy()
        e = x["actual"] - x["E_all"]
        tgt = x["month"] + pd.offsets.MonthEnd(0) + pd.DateOffset(months=h)
        hit = []
        for Y in range(2016, 2027):
            asof = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
            past, cur = e[tgt <= asof], e[x["month"].dt.year == Y]
            if len(past) >= 300 and len(cur):
                lo, hi = past.quantile(0.1), past.quantile(0.9)
                hit += list(((cur >= lo) & (cur <= hi)).to_numpy())
        bands.append({"h": h, "n": len(e), "q10": float(e.quantile(0.1)), "q90": float(e.quantile(0.9)),
                      "涵蓋率": float(np.mean(hit)) if hit else np.nan})
    bands = pd.DataFrame(bands)
    table("80% 區間（全部 S&P 500，已揭曉誤差的 10–90% 分位數；涵蓋率＝走動式實測）", bands.set_index("h").round(3))

    pd.concat(scores, ignore_index=True).to_csv(os.path.join(RES, "broad_scores.csv"), index=False, float_format="%.6f")
    sec.to_csv(os.path.join(RES, "broad_sector.csv"), index=False, float_format="%.6f")
    hz.to_csv(os.path.join(RES, "broad_horizon.csv"), index=False, float_format="%.6f")
    nn.to_csv(os.path.join(RES, "broad_near_now.csv"), index=False, float_format="%.6f")
    bands.to_csv(os.path.join(RES, "broad_bands.csv"), index=False, float_format="%.6f")
    p[["ticker", "month", "h", "gics", "in_tech", "ln_pe", "actual", "E_all", "E_tech"]].to_pickle(os.path.join(a.cache, "broad_final.pkl"))
    keep = p[p["h"].isin((12, 36)) & p["E_all"].notna()][["ticker", "month", "h", "ln_pe", "actual", "E_all"]]
    keep.to_csv(os.path.join(RES, "broad_predictions.csv.gz"), index=False, float_format="%.6f")
    open(os.path.join(RES, "broad.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
