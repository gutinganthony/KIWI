#!/usr/bin/env python3
"""規格比較（README §4「所有試過的規格」）：用目前的程式重跑每一個候選規格。

所有規格決策只看選模期 2015–2021；保留期 2022–2026 一併列出但不參與選擇。
輸出 results/ablation.csv。約 1–2 分鐘。
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import backtest as bt                 # noqa: E402
from pef.earnings import MAR_X, REV_X           # noqa: E402
from pef.load import panel                      # noqa: E402

pd.set_option("display.width", 250)

BASE_R = [x for x in REV_X if x != "ep_c"]
BASE_M = [x for x in MAR_X if x != "ep_c"]
SPECS = {
    "E0 財報＋股價動能＋P/S": dict(rev_x=BASE_R, mar_x=BASE_M, two_stage=False),
    "E1 E0＋E/P": dict(two_stage=False),
    "E2 只有財報（不看股價）": dict(rev_x=["g_rev", "acc", "d_inv", "gm_slope"],
                            mar_x=["gap", "q_vs_ttm", "gm_slope", "d_inv"], two_stage=False),
    "E3 E1＋循環性交互作用": dict(rev_x=REV_X + ["grev_x_sig", "dinv_x_sig"],
                           mar_x=MAR_X + ["gap_x_sig", "gms_x_sig", "dinv_x_sig"], two_stage=False),
    "E1＋兩階段隱含利潤率（最終版）": dict(two_stage=True),
    "最終版，但報酬＝過去10年中位": dict(two_stage=True, mu_mode="hist"),
}


def main():
    df, _ = panel()
    s = df["sigma"].clip(0, 0.3) / 0.05                    # 循環性：利潤率波動（以 5pp 為單位）
    df["gap_x_sig"] = (df["m_ttm"] - df["m_bar"]) * s
    df["grev_x_sig"] = df["g_rev"] * s
    df["gms_x_sig"] = df["gm_slope"] * s
    df["dinv_x_sig"] = df["d_inv"] * s
    rows = []
    for name, kw in SPECS.items():
        pred, _ = bt.run(df, start_year=2015, fc_kwargs=kw, verbose=False)
        for per_name, per in (("選模期", bt.SELECT), ("保留期", bt.HOLDOUT)):
            sc = bt.evaluate(df, pred, period=per)
            a = sc[sc["方法"] == "模型（報酬＝資金成本）"].set_index("h")["中位絕對誤差"]
            r = sc[sc["方法"] == "隨機漫步"].set_index("h")["中位絕對誤差"]
            e = bt.earnings_scores(df, pred[(pred["month"] >= per[0]) & (pred["month"] <= per[1])]).set_index("h")
            rows.append({"規格": name, "期間": per_name, **{f"PE誤差h{h}": a[h] for h in a.index},
                         "PE誤差四距離平均": a.mean(), **{f"隨機漫步h{h}": r[h] for h in r.index},
                         **{f"盈餘誤差pp_h{h}": e.loc[h, "模型盈餘誤差pp"] for h in e.index}})
        print(f"  {name} 完成")
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(HERE, "results", "ablation.csv"), index=False, float_format="%.4f")
    show = out[["規格", "期間", "PE誤差h6", "PE誤差h12", "PE誤差h24", "PE誤差h36", "PE誤差四距離平均", "盈餘誤差pp_h24", "盈餘誤差pp_h36"]]
    print(show.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
