#!/usr/bin/env python3
"""樣本外「領域」測試（README §4b）：模型只從 68 家科技股學，拿去預測能源、電力、軍工、TSLA。

需要 data/quarters_ext.csv（build_data.py --universe universe_ext.csv --tag _ext）。
輸出 results/ood.csv。約 30 秒。
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import backtest as bt   # noqa: E402
from pef.load import panel       # noqa: E402

pd.set_option("display.width", 250)


def main():
    df, _ = panel(include_ext=True)
    pred, _ = bt.run(df, start_year=2015, verbose=False)
    rows = []
    for sec in ["energy_oil", "power", "defense", "auto_tech"]:
        for h in (6, 12, 24):
            sc = bt.evaluate(df, pred, sectors=[sec], horizons=(h,))
            if sc.empty:
                continue
            a = sc.set_index("方法")
            rows.append(dict(產業=sec, h=h, n=int(a.loc["隨機漫步", "n"]), 公司=int(a.loc["隨機漫步", "公司數"]),
                             模型=a.loc["模型（報酬＝資金成本）", "中位絕對誤差"], 隨機漫步=a.loc["隨機漫步", "中位絕對誤差"],
                             歷史均值=a.loc["歷史均值(5y)", "中位絕對誤差"], 同業中位數=a.loc["同業中位數", "中位絕對誤差"],
                             方向命中=a.loc["模型（報酬＝資金成本）", "方向命中"]))
    r = pd.DataFrame(rows)
    r["模型vs隨機漫步"] = r["模型"] / r["隨機漫步"] - 1
    ext = df[~df["train"].astype(bool)]["ticker"].unique()
    e = bt.earnings_scores(df, pred[pred["ticker"].isin(ext)])
    r.to_csv(os.path.join(HERE, "results", "ood.csv"), index=False, float_format="%.4f")
    e.to_csv(os.path.join(HERE, "results", "ood_earnings.csv"), index=False, float_format="%.4f")
    print(r.round(3).to_string(index=False))
    print(e.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
