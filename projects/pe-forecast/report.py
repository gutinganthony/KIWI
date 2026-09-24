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
    txt = buf.getvalue()
    open(os.path.join(RES, "report.txt"), "w").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
