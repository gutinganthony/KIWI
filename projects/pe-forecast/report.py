#!/usr/bin/env python3
"""把 README 用到的每一張表重新算一次（先跑 pe_forecast.py backtest）。輸出寫進 results/report.txt。"""
import io
import os
import sys
from contextlib import redirect_stdout

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import backtest as bt          # noqa: E402
from pef import value                   # noqa: E402
from pef.features import attach_future  # noqa: E402
from pef.forecast import PEForecaster, _inputs  # noqa: E402
from pef.load import panel              # noqa: E402

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
RES = os.path.join(HERE, "results")


def main():
    df, _ = panel()
    pred = pd.read_csv(os.path.join(RES, "predictions.csv.gz"), parse_dates=["month"])
    sc = pd.read_csv(os.path.join(RES, "scores.csv"))
    buf = io.StringIO()
    with redirect_stdout(buf):
        print("## 表 1：ln PE 中位絕對誤差（越小越好）")
        for per in ("全期", "選模期2015-21", "保留期2022-26"):
            t = sc[sc["期間"] == per].pivot(index="方法", columns="h", values="中位絕對誤差")
            n = sc[(sc["期間"] == per) & (sc["方法"] == "隨機漫步")].set_index("h")["n"]
            print(f"\n### {per}（n = {n.to_dict()}）\n", t.round(3).to_string())
        print("\n## 表 2：方向命中率（PE 會升還是降）")
        t = sc[sc["期間"] == "全期"].pivot(index="方法", columns="h", values="方向命中")
        print(t.round(3).to_string())
        print("\n## 表 3：盈餘預測誤差（占市值 pp；模型 vs 盈餘不變）")
        print(pd.read_csv(os.path.join(RES, "scores_earnings.csv")).round(3).to_string(index=False))
        print("\n## 表 4：分產業（h=12，全期）")
        s = pd.read_csv(os.path.join(RES, "scores_by_sector.csv"))
        s = s[s["h"] == 12].pivot(index="產業", columns="方法", values="中位絕對誤差")
        n = pd.read_csv(os.path.join(RES, "scores_by_sector.csv"))
        n = n[(n["h"] == 12) & (n["方法"] == "隨機漫步")].set_index("產業")[["n", "公司數"]]
        s = s.join(n)
        s["模型vs隨機漫步"] = s["模型（報酬＝資金成本）"] / s["隨機漫步"] - 1
        print(s[["公司數", "n", "模型（報酬＝資金成本）", "隨機漫步", "歷史均值(5y)", "同業中位數", "模型vs隨機漫步"]].round(3).to_string())
        print("\n## 表 5：本益比 12 個月變化的來源（Var 占比）")
        dec = pd.read_csv(os.path.join(RES, "decompose_12m.csv"))
        print(dec.groupby("sector")[["報酬波動", "盈餘成長波動", "盈餘占比"]].median().round(2).sort_values("盈餘占比", ascending=False).to_string())
        print(dec[dec["ticker"].isin(["MU", "WDC", "STX", "NVDA", "MSFT", "GOOGL", "META", "INTC", "AAPL", "AMAT"])].round(2).to_string(index=False))
        print("\n## 表 6：站在過去預測 2026-09 的本益比")
        base = bt.baselines(df)
        tgt = pd.Timestamp("2026-09-01")
        act = df[df["month"] == tgt].set_index("ticker")
        rows = []
        for t in act.index:
            r = {"公司": t, "2026-09 實際": act.loc[t, "pe"]}
            for h in (12, 24, 36):
                m = tgt - pd.DateOffset(months=h)
                p = pred[(pred["ticker"] == t) & (pred["month"] == m)]
                b = base[(base["ticker"] == t) & (base["month"] == m)]
                if len(p):
                    r[f"{h}m前 模型"] = np.exp(p[f"lnpe_hat_{h}"].iloc[0]) if p[f"ni_hat_{h}"].iloc[0] > 0 else np.nan
                    r[f"{h}m前 當時PE"] = np.exp(b["b_rw"].iloc[0])
                    r[f"{h}m前 5y均"] = np.exp(b["b_hist"].iloc[0])
            rows.append(r)
        x = pd.DataFrame(rows)
        print(x.round(1).to_string(index=False))
        y = np.log(x["2026-09 實際"])
        for h in (12, 24, 36):
            e = {c.split(" ")[1]: float(np.nanmedian(np.abs(np.log(x[c]) - y))) for c in x.columns if c.startswith(f"{h}m前")}
            print(f"  h={h} 中位誤差：", {k: round(v, 3) for k, v in e.items()})
        print("\n## 表 7：價值缺口能不能預測報酬（γ12，每年重估）")
        print(pd.read_csv(os.path.join(RES, "fits.csv"))[["year", "gamma_12", "mu_hist_12"]].to_string(index=False))
        implied_test(df, pred)
        dcf_cross_section(df)
        implied_timeline(df)
    txt = buf.getvalue()
    open(os.path.join(RES, "report.txt"), "w").write(txt)
    print(txt)


def implied_test(df, pred):
    """市場隱含長期淨利率，能不能預測 h 個月後的淨利率（超出『現在偏離歷史』的資訊）？"""
    print("\n## 表 8：市場隱含利潤率 → 未來利潤率")
    rows = []
    for h in (12, 24):
        f = attach_future(df, h)[["ticker", "month", f"ni_ttm_f{h}", f"rev_ttm_f{h}", "m_bar", "m_ttm"]]
        d = pred[["ticker", "month", "implied_m"]].merge(f, on=["ticker", "month"])
        d["m_act"] = d[f"ni_ttm_f{h}"] / d[f"rev_ttm_f{h}"]
        d = d[np.isfinite(d["m_act"]) & np.isfinite(d["implied_m"]) & d["m_bar"].notna() & d["m_ttm"].notna()]
        for per, (lo, hi) in (("選模期", bt.SELECT), ("保留期", bt.HOLDOUT)):
            x = d[(d["month"] >= lo) & (d["month"] <= hi)]
            y = (x["m_act"] - x["m_bar"]).clip(-0.5, 0.5).to_numpy()
            now = (x["m_ttm"] - x["m_bar"]).clip(-0.5, 0.5).to_numpy()
            imp = (x["implied_m"] - x["m_bar"]).clip(-0.5, 0.8).to_numpy()
            r2 = lambda X: 1 - np.var(y - X @ np.linalg.lstsq(X, y, rcond=None)[0]) / np.var(y)
            one = np.ones(len(x))
            up = x[(x["implied_m"] > 1.5 * x["m_bar"]) & (x["m_bar"] > 0.05)]
            dn = x[(x["implied_m"] < 0.67 * x["m_bar"]) & (x["m_bar"] > 0.05)]
            rows.append(dict(h=h, 期間=per, n=len(x), R2_只用現在偏離=r2(np.column_stack([one, now])),
                             R2_加市場隱含=r2(np.column_stack([one, now, imp])),
                             押注變高後真的高於歷史=float(np.mean(up["m_act"] > up["m_bar"])), n_高=len(up),
                             押注變差後真的低於歷史=float(np.mean(dn["m_act"] < dn["m_bar"])), n_差=len(dn)))
    print(pd.DataFrame(rows).round(3).to_string(index=False))


def dcf_cross_section(df):
    """用歷史利潤率的 DCF，能不能解釋同一天各公司本益比的高低？（ln PE 與 ln(V/淨利) 的相關）"""
    print("\n## 表 9：DCF（歷史利潤率）vs 橫斷面本益比：相關係數")
    rows = []
    for asof in ("2017-12-31", "2020-12-31", "2023-12-31", "2025-12-31"):
        fc = PEForecaster(two_stage=False).fit(df, asof)
        lo = pd.Timestamp(asof) - pd.DateOffset(months=11)
        x = df[(df["month_end"] > lo) & (df["month_end"] <= asof) & df["sigma"].notna() & df["m_bar"].notna()
               & (df["ni_ttm"] > 0)].groupby("ticker").tail(1)
        args = _inputs(x, fc.E1.predict(x))
        lnpe = np.log(x["mc"] / x["ni_ttm"]).to_numpy()
        r = {"時點": asof, "n": len(x)}
        for H in (1, 3, 5, 8, 12):
            V, _ = value.intrinsic(*args, dict(theta0=0.05, theta1=0.0, H=H, g_inf=0.03), s=0)
            r[f"H={H}"] = float(np.corrcoef(lnpe, np.log(V) - np.log(x["ni_ttm"].to_numpy()))[0, 1])
        peer = x.groupby("sector")["pe"].transform("median")
        r["同業中位數"] = float(np.corrcoef(lnpe, np.log(peer))[0, 1])
        rows.append(r)
    print(pd.DataFrame(rows).round(2).to_string(index=False))


def implied_timeline(df, tickers=("MU", "STX", "WDC"),
                     months=("2017-06", "2018-06", "2019-06", "2020-06", "2021-06", "2022-06",
                             "2023-06", "2024-06", "2025-06", "2026-09")):
    """記憶體：每個時點（只用當時資料）市場隱含的長期淨利率，對照 24 個月後的實際淨利率。"""
    print("\n## 表 10：記憶體的市場隱含長期淨利率時間序列")
    f24 = attach_future(df, 24)[["ticker", "month", "ni_ttm_f24", "rev_ttm_f24"]]
    rows = []
    for t in tickers:
        for m in months:
            r = df[(df["ticker"] == t) & (df["month"] == pd.Timestamp(m + "-01")) & df["sigma"].notna()]
            if r.empty:
                continue
            fc = PEForecaster().fit(df, r["month_end"].iloc[0])
            p = fc.predict(r, (12,)).iloc[0]
            fut = f24[(f24["ticker"] == t) & (f24["month"] == pd.Timestamp(m + "-01"))]
            m24 = (fut["ni_ttm_f24"] / fut["rev_ttm_f24"]).iloc[0] if len(fut) else np.nan
            rows.append({"公司": t, "時點": m, "PE": "虧損" if r["ni_ttm"].iloc[0] <= 0 else round(float(r["pe"].iloc[0]), 1),
                         "TTM淨利率": f"{r['m_ttm'].iloc[0]:.1%}", "5年中位": f"{r['m_bar'].iloc[0]:.1%}",
                         "市場隱含長期": f"{p['implied_m']:.1%}", "隱含/歷史": f"{p['implied_m'] / r['m_bar'].iloc[0]:.2f}x",
                         "24個月後實際": "—" if not np.isfinite(m24) else f"{m24:.1%}"})
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
