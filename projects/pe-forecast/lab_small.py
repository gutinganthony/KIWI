#!/usr/bin/env python3
"""中小型股回測：Russell 2000、S&P 400、S&P 600，2021 → 2026，季頻。

    python3 lab_small.py --cache <暫存目錄>       # 第一次約 20 分鐘

資料：build_small.py（1,407 家中小型股，季末股價來自指數 ETF 的持股申報）＋ build_broad.py（S&P 500 月頻）。
每年 1 月只用當時已揭曉的配對訓練，預測當年每季的 3／6／9／12 個月後本益比。分組用「當時」的成分股（持股申報）。
選模期 2021–2023 決定、保留期 2024–2026 只看。比較：

  V1  現行模型：只用 S&P 500 訓練，四個預測器（中小型股缺的毛利、營業利益、存貨當作缺值）
  V2  精簡特徵：拿掉用到毛利、營業利益、存貨的 4 個特徵，只用 S&P 500 訓練（三個預測器）
  V3  精簡特徵＋把中小型股也放進訓練資料
  V4  V3 和「本益比不變」各半
限制：只有活到 2026 年、對得到公司代碼、有 v2 長期財報的公司（倖存者偏差）；財報是之後申報的版本。
輸出：results/small.txt、small_scores.csv
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import lab                                      # noqa: E402
from pef.data import load_macro                          # noqa: E402
from pef.ensemble import combine                         # noqa: E402
from pef.features import monthly_panel, quarterly_features   # noqa: E402
from pef.forecast import PEForecaster                    # noqa: E402
from pef.load import panel_sp500                         # noqa: E402

DATA = os.path.join(HERE, "data")
RES = os.path.join(HERE, "results")
H = (3, 6, 9, 12)
PERIODS = {"選模期": ("2021-01-01", "2023-12-31"), "保留期": ("2024-01-01", "2026-12-31"), "全期": ("2021-01-01", "2026-12-31")}
GROUPS = {"rut": "Russell 2000", "sp400": "S&P 400 中型股", "sp600": "S&P 600 小型股"}
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def cached(cache, name, fn):
    path = os.path.join(cache, f"small_{name}.pkl")
    if os.path.exists(path):
        return pd.read_pickle(path)
    x = fn()
    x.to_pickle(path)
    return x


def lag_ret(d, q):
    """季頻列的 k 季報酬（前一列必須剛好是 3k 個月前）。"""
    d = d.sort_values(["ticker", "month"])
    prev_mc = d.groupby("ticker")["mc"].shift(q)
    prev_m = d.groupby("ticker")["month"].shift(q)
    ok = (d["month"] - prev_m).dt.days.between(q * 91 - 20, q * 91 + 20)
    return np.log(d["mc"] / prev_mc).where(ok)


def small_panel():
    q = pd.read_csv(os.path.join(DATA, "quarters_small.csv"), parse_dates=["period_end", "filed", "avail"])
    p = pd.read_csv(os.path.join(DATA, "prices_quarterly_small.csv"), parse_dates=["month"])
    u = pd.read_csv(os.path.join(DATA, "universe_small.csv"))
    qf = quarterly_features(q)
    df = monthly_panel(qf, p, load_macro(DATA))
    df = df[(df["month_end"] - df["period_end"]).dt.days <= 240].reset_index(drop=True)
    df = df.merge(u[["ticker", "sector"]], on="ticker", how="left")
    df["ret6"] = lag_ret(df, 2).reindex(df.index)
    df["train"] = True
    return df, qf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    dfS, qfS = panel_sp500()
    dS = lab.build(dfS, qfS)
    dS["is_sp"] = True
    dfL, qfL = small_panel()
    dL = lab.build(dfL, qfL)
    dL["ret12"] = lag_ret(dL, 4).reindex(dL.index)
    dL["is_sp"] = False
    mem = pd.read_csv(os.path.join(DATA, "members_small.csv"), parse_dates=["date"])
    mem["month"] = mem["date"] - pd.offsets.MonthBegin(1)
    for k in GROUPS:
        dL[k] = dL.set_index(["ticker", "month"]).index.isin(pd.MultiIndex.from_frame(mem[mem["idx"] == k][["ticker", "month"]]))
    say(f"中小型股：{dL['ticker'].nunique()} 家、{len(dL):,} 個公司季（{dL['month'].min():%Y-%m} ～ {dL['month'].max():%Y-%m}）；"
        f"其中曾在 Russell 2000 {dL[dL['rut']]['ticker'].nunique()} 家、S&P 400 {dL[dL['sp400']]['ticker'].nunique()} 家、"
        f"S&P 600 {dL[dL['sp600']]['ticker'].nunique()} 家")
    x = dL[dL["month"] == "2024-06-01"]
    say(f"抽查 2024-06：本益比中位 {x['pe'][x['pe'] > 0].median():.1f}、虧損公司占 {(x['ni_ttm'] <= 0).mean():.0%}")
    d = pd.concat([dS, dL], ignore_index=True)
    d["is_sp"] = d["is_sp"].astype(bool)

    full, red = ["huber", "gbm", "gbm_z"], ["huber_r", "gbm_r", "gbm_z_r"]
    small_rows = lambda p: p.merge(dL[["ticker", "month"]], on=["ticker", "month"])
    pV1 = cached(a.cache, "v1", lambda: small_rows(lab.walk(d, full, horizons=H, start=2021, train_col="is_sp")))
    pV2 = cached(a.cache, "v2", lambda: small_rows(lab.walk(d, red, horizons=H, start=2021, train_col="is_sp")))
    pV3 = cached(a.cache, "v3", lambda: small_rows(lab.walk(d, red, horizons=H, start=2021)))

    def old_run():
        out = []
        for Y in range(2021, 2027):
            asof = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
            fc = PEForecaster().fit(dfS, asof)
            w = dfL[(dfL["month_end"] > asof) & (dfL["month_end"] <= asof + pd.DateOffset(months=12))]
            w = w[w["sigma"].notna() & w["m_bar"].notna() & (w["mc"] > 0)]
            if w.empty:
                continue
            pr = fc.predict(w, (6, 12))
            out.append(pr[["ticker", "month"] + [f"lnpe_hat_{h}" for h in (6, 12)] + [f"ni_hat_{h}" for h in (6, 12)]])
        return pd.concat(out, ignore_index=True)
    old = cached(a.cache, "old", old_run)

    key = ["ticker", "month", "h"]
    p = pV1.rename(columns={m: m + "_1" for m in full})
    p = p.merge(pV2[key + red].rename(columns={m: m + "_2" for m in red}), on=key, how="left")
    p = p.merge(pV3[key + red].rename(columns={m: m + "_3" for m in red}), on=key, how="left")
    p["old"] = np.nan
    for h in (6, 12):
        m = p["h"] == h
        v = p.loc[m, ["ticker", "month"]].merge(old[["ticker", "month", f"lnpe_hat_{h}", f"ni_hat_{h}"]], on=["ticker", "month"], how="left")
        p.loc[m, "old"] = np.where(v[f"ni_hat_{h}"] > 0, v[f"lnpe_hat_{h}"], np.nan)
    ens = lambda cols_by_h: pd.concat([combine(p.loc[p["h"] == h, cols_by_h(h)]) for h in H]).reindex(p.index)
    p["V1"] = ens(lambda h: (["old"] if h in (6, 12) else []) + [m + "_1" for m in full])
    p["V2"] = ens(lambda h: [m + "_2" for m in red])
    p["V3"] = ens(lambda h: [m + "_3" for m in red])
    p["V4"] = 0.5 * p["V3"] + 0.5 * p["ln_pe"]
    p = p.merge(dL[["ticker", "month", "mc", "sector"] + list(GROUPS)], on=["ticker", "month"], how="left", suffixes=("", "_u"))

    rows = []
    for per in PERIODS:
        for g, gname in [("all", "全部中小型股")] + list(GROUPS.items()):
            x = p if g == "all" else p[p[g].astype(bool)]
            s = lab.score(x, ["V1", "V2", "V3", "V4"], PERIODS[per])
            rows.append(s.assign(期間=per, 群組=gname))
    sc = pd.concat(rows, ignore_index=True)
    for per in ("選模期", "保留期", "全期"):
        for gname in ["全部中小型股"] + list(GROUPS.values()):
            x = sc[(sc["期間"] == per) & (sc["群組"] == gname)]
            if x.empty:
                continue
            say(f"\n== {per}｜{gname}：OOS R²（相對本益比不變）")
            say(x.pivot(index="方法", columns="h", values="OOS_R2").round(3).to_string())
            say(f"== {per}｜{gname}：典型誤差（中位 |ln|）")
            say(x.pivot(index="方法", columns="h", values="中位絕對誤差").round(3).to_string())

    # 依市值分層（全期、12 個月、V3）：越小的公司越難？
    x = p[(p["h"] == 12) & p["actual"].notna() & p["ln_pe"].notna() & p["V3"].notna() & (p["month"] >= "2021-01-01")].copy()
    x["size"] = pd.qcut(x["mc"], 4, labels=["最小 1/4", "第 2", "第 3", "最大 1/4"])
    tiers = []
    for tname, y in x.groupby("size", observed=True):
        em, er = y["V3"] - y["actual"], y["ln_pe"] - y["actual"]
        tiers.append({"市值分層": tname, "市值中位_億美元": y["mc"].median() / 1e8, "n": len(y), "本益比不變": er.abs().median(),
                      "模型": em.abs().median(), "OOS_R2": 1 - np.sum(np.minimum(em ** 2, 4)) / np.sum(np.minimum(er ** 2, 4))})
    tiers = pd.DataFrame(tiers)
    say("\n== 12 個月｜依市值分層（V3，全期）")
    say(tiers.set_index("市值分層").round(3).to_string())

    # 80% 區間：S&P 500 的誤差分位數（broad_bands.csv）套到中小型股夠不夠寬？改用中小型股自己的誤差分位數呢？
    # 中小型股的區間只用選模期（2021–2023）的誤差畫，在保留期（2024–2026）驗涵蓋率。
    bb = pd.read_csv(os.path.join(RES, "broad_bands.csv")).set_index("h")
    x = p[p["actual"].notna() & p["V1"].notna() & p["ln_pe"].notna()]
    e = x["actual"] - x["V1"]
    band = []
    for h in H:
        sel = (x["h"] == h) & (x["month"] <= "2023-12-31")
        hold = (x["h"] == h) & (x["month"] >= "2024-01-01")
        a, b = e[sel].quantile([0.1, 0.9])
        cov = lambda lo, hi: float(((e[hold] >= lo) & (e[hold] <= hi)).mean())
        band.append({"h": h, "n_選模期": int(sel.sum()), "q10": a, "q90": b, "n_保留期": int(hold.sum()),
                     "中小型股區間涵蓋率_保留期": cov(a, b), "S&P500區間涵蓋率_保留期": cov(bb.loc[h, "q10"], bb.loc[h, "q90"]),
                     "S&P500_q10": bb.loc[h, "q10"], "S&P500_q90": bb.loc[h, "q90"]})
    band = pd.DataFrame(band)
    say("\n== 80% 區間（實際 − 預測的 ln 分位數；V1）：S&P 500 的區間 vs 中小型股自己的區間，保留期涵蓋率")
    say(band.set_index("h").round(3).to_string())
    sc.to_csv(os.path.join(RES, "small_scores.csv"), index=False, float_format="%.6f")
    tiers.to_csv(os.path.join(RES, "small_tiers.csv"), index=False, float_format="%.6f")
    band.to_csv(os.path.join(RES, "small_bands.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "small.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
