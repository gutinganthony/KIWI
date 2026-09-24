"""走動式回測：每年 1 月重估一次，只用當時看得到的資料，預測接下來 12 個月每個月底的
6／12／24／36 個月後本益比。與三條「舊思維」基準線比較。
"""
import numpy as np
import pandas as pd

from .features import attach_future
from .forecast import PEForecaster
from .stats import spearman

HORIZONS = (6, 12, 24, 36)
METHODS = {"模型（報酬＝資金成本）": "lnpe_hat_{h}", "模型（報酬＝過去10年中位）": "lnpe_hist_{h}",
           "模型（股價不動）": "lnpe_flat_{h}", "隨機漫步": "b_rw", "歷史均值(5y)": "b_hist", "同業中位數": "b_peer"}
SELECT = ("2015-01-01", "2021-12-31")     # 選模期：所有規格決策只看這段
HOLDOUT = ("2022-01-01", "2026-12-31")    # 保留期：不參與任何選擇


def baselines(panel):
    """舊思維的三條基準線（在 t 時點就能算）。"""
    df = panel[["ticker", "month", "ln_pe", "sector"]].copy()
    df["b_rw"] = df["ln_pe"]                                              # 未來 PE = 今天 PE
    df["b_hist"] = df.groupby("ticker")["ln_pe"].transform(lambda s: s.rolling(60, min_periods=24).mean())
    df["b_peer"] = df.groupby(["sector", "month"])["ln_pe"].transform("median")
    return df[["ticker", "month", "b_rw", "b_hist", "b_peer"]]


def run(panel, start_year=2015, end=None, fc_kwargs=None, verbose=True):
    fc_kwargs = fc_kwargs or {}
    end = pd.Timestamp(end) if end else panel["month_end"].max()
    preds, fits = [], []
    for year in range(start_year, end.year + 1):
        asof = pd.Timestamp(f"{year}-01-01") - pd.Timedelta(days=1)
        fc = PEForecaster(**fc_kwargs).fit(panel, asof)
        win = panel[(panel["month_end"] > asof) & (panel["month_end"] <= min(asof + pd.DateOffset(months=12), end))]
        win = win[win["sigma"].notna() & win["m_bar"].notna() & (win["mc"] > 0)]
        if win.empty:
            continue
        p = fc.predict(win, HORIZONS)
        p["fit_year"] = year
        preds.append(p)
        fits.append(dict(year=year, **{f"n_E{k}": fc.E.coef[k]["n"] for k in (4, 12)},
                         **{f"gamma_{h}": round(fc.diag[h]["gamma"], 3) for h in HORIZONS},
                         **{f"mu_hist_{h}": round(fc.diag[h]["mu_hist"], 3) for h in HORIZONS}))
        if verbose:
            print(f"  {year}: γ12={fc.diag[12]['gamma']:+.3f}  過去10年中位12月報酬={fc.diag[12]['mu_hist']:+.3f}  預測列={len(win)}")
    return pd.concat(preds, ignore_index=True), pd.DataFrame(fits)


def joined(panel, pred, h):
    f = attach_future(panel, h)[["ticker", "month", f"ln_pe_f{h}", f"ep_f{h}", f"ni_ttm_f{h}", f"mc_f{h}",
                                 "ln_pe", "ep", "sector"]]
    return pred.drop(columns=["mc", "ni_ttm"]).merge(f, on=["ticker", "month"]).merge(baselines(panel), on=["ticker", "month"])


def evaluate(panel, pred, horizons=HORIZONS, period=None, sectors=None):
    """每個 h 的評分表。只在「t+h 已發生、實際盈餘為正、所有方法都有預測」的共同樣本上比較。"""
    rows = []
    for h in horizons:
        d = joined(panel, pred, h)
        if period:
            d = d[(d["month"] >= period[0]) & (d["month"] <= period[1])]
        if sectors:
            d = d[d["sector"].isin(sectors)]
        y = d[f"ln_pe_f{h}"]
        cols = {k: v.format(h=h) for k, v in METHODS.items()}
        ok = y.notna()
        for c in cols.values():
            ok &= d[c].notna()
        dd = d[ok]
        if len(dd) < 30:
            continue
        for name, c in cols.items():
            e = dd[c] - dd[f"ln_pe_f{h}"]
            dirn = np.nan
            if c != "b_rw":
                dirn = float(np.mean(np.sign(dd[c] - dd["ln_pe"]) == np.sign(dd[f"ln_pe_f{h}"] - dd["ln_pe"])))
            rho = np.nanmedian([spearman(g[c].to_numpy(), g[f"ln_pe_f{h}"].to_numpy())
                                for _, g in dd.groupby("month") if len(g) >= 8]) if not sectors else np.nan
            rows.append(dict(h=h, 方法=name, n=len(dd), 公司數=dd["ticker"].nunique(),
                             中位絕對誤差=float(np.median(np.abs(e))), 平均絕對誤差=float(np.mean(np.abs(e))),
                             偏誤=float(np.median(e)), 方向命中=dirn, 橫斷面排序相關=rho))
    return pd.DataFrame(rows)


def ep_scores(panel, pred, horizons=HORIZONS):
    """盈餘殖利率 E/P（跨越零時連續）——包含虧損期間，不會因為盈餘接近零而爆掉。"""
    rows = []
    for h in horizons:
        d = joined(panel, pred, h)
        d = d[d[f"ep_f{h}"].notna() & d["ep"].notna() & d[f"ep_hat_{h}"].notna()]
        for name, c in {"模型（報酬＝資金成本）": f"ep_hat_{h}", "隨機漫步": "ep"}.items():
            e = (d[c] - d[f"ep_f{h}"]).clip(-1, 1)
            rows.append(dict(h=h, 方法=name, n=len(d), EP中位絕對誤差pp=100 * float(np.median(np.abs(e))),
                             EP平均絕對誤差pp=100 * float(np.mean(np.abs(e)))))
    return pd.DataFrame(rows)


def earnings_scores(panel, pred, horizons=HORIZONS):
    """模組 E 本身：盈餘預測誤差（以 t 時點市值標準化，= E/P 單位，跨越零也能比）。"""
    rows = []
    for h in horizons:
        d = joined(panel, pred, h)
        f = attach_future(panel, h)[["ticker", "month", "ni_ttm", "mc"]]
        d = d.merge(f, on=["ticker", "month"])
        d = d[d[f"ni_ttm_f{h}"].notna() & d[f"ni_hat_{h}"].notna() & d["ni_ttm"].notna()]
        e_m = (d[f"ni_hat_{h}"] - d[f"ni_ttm_f{h}"]) / d["mc"]
        e_n = (d["ni_ttm"] - d[f"ni_ttm_f{h}"]) / d["mc"]
        rows.append(dict(h=h, n=len(d), 模型盈餘誤差pp=100 * float(np.median(np.abs(e_m))),
                         不變假設盈餘誤差pp=100 * float(np.median(np.abs(e_n))),
                         模型較準比例=float(np.mean(np.abs(e_m) < np.abs(e_n)))))
    return pd.DataFrame(rows)


def decompose(panel, h=12):
    """每家公司：Δln PE = 報酬 − 盈餘成長。盈餘那一項占比越大，本益比越可預測。"""
    f = attach_future(panel, h)
    d = f[(f["ni_ttm"] > 0) & (f[f"ni_ttm_f{h}"] > 0) & (f["month"] >= "2012-01-01")].copy()
    d["ret"] = np.log(d[f"mc_f{h}"] / d["mc"])
    d["gro"] = np.log(d[f"ni_ttm_f{h}"] / d["ni_ttm"])
    rows = []
    for t, g in d.groupby("ticker"):
        if len(g) < 36:
            continue
        vr, vg = g["ret"].var(), g["gro"].var()
        rows.append(dict(ticker=t, sector=g["sector"].iloc[0], n=len(g), 報酬波動=np.sqrt(vr), 盈餘成長波動=np.sqrt(vg),
                         盈餘占比=vg / (vr + vg)))
    return pd.DataFrame(rows).sort_values("盈餘占比", ascending=False)
