#!/usr/bin/env python3
"""README §22.5：分析師只給到「本財年」時，24 個月後的 EPS 要怎麼外推？（I/B/E/S 歷史，2012–2022 起點）

    python3 research/eps_extension.py --build <lab_eps_correction.py 的 L.build pickle> > results/eps_extension.txt

起因（§22.2）：2024-09 起點把分析師 forward EPS 再乘一次「隱含年成長」外推到 24 個月，S&P 500 的 EPS 中位高估 23%。
這裡用 I/B/E/S 歷史（OSAP FEPS＝本財年共識）檢驗外推規則，目標＝24 個月後已公布的最近四季 GAAP EPS（eps_f24）：
  FY1 原樣｜FY1 × 隱含成長^k（隱含成長＝FY1 ÷ 今天 EPS，截在 0.7–1.5；k＝0.25、0.5、0.75、1）｜FY1 × (1 ＋ LTG)
起點：距離本財年年報 6–12 個月（FY1 大約就是「未來 12 個月」）、兩端 EPS > 0、起點前後沒有分割。
k 只在 2012–2017 起點挑，2018–2022 起點檢查。
"""
import argparse
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    a = ap.parse_args()
    d = pd.read_pickle(a.build)
    d = d[(d["month"] >= "2012-01-01") & (d["month"] <= "2022-09-01") & (d["lead"] >= 6) & (d["lead"] <= 12) & ~d["near_split"]
          & (d["eps0"] > 0) & (d["feps"] > 0) & (d["eps_f24"] > 0)].copy()
    g = (d["feps"] / d["eps0"]).clip(0.7, 1.5)
    act = np.log(d["eps_f24"])
    rules = {"FY1 原樣": d["feps"]}
    for k in (0.25, 0.5, 0.75, 1.0):
        rules[f"FY1 × 隱含成長^{k:g}"] = d["feps"] * g ** k
    ltg = (d["fgr5y"] / 100).clip(-0.3, 0.5) if "fgr5y" in d else pd.Series(np.nan, index=d.index)
    rules["FY1 × (1＋LTG)"] = d["feps"] * (1 + ltg)
    rows = []
    for per, lo, hi in (("2012–2017（挑 k）", "2012-01-01", "2017-12-31"), ("2018–2022（檢查）", "2018-01-01", "2022-12-31"), ("全部", "2012-01-01", "2022-12-31")):
        for grp in ("全部", "科技", "半導體／設備／記憶體"):
            m = (d["month"] >= lo) & (d["month"] <= hi)
            if grp == "科技":
                m &= d["grp"] != "other"
            elif grp != "全部":
                m &= d["grp"] == "cyclical"
            r = dict(期間=per, 組別=grp, n=int(m.sum()))
            for nm, pr in rules.items():
                e = np.log(pr[m]) - act[m]
                r[nm + "｜中位|誤差|"] = float(np.nanmedian(np.abs(e)))
                r[nm + "｜中位偏差"] = float(np.nanmedian(e))
            rows.append(r)
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(f"樣本：{len(d):,} 個公司月（S&P 500，起點 2012-01～2022-09，距離年報 6–12 個月）")
    print("\n== 24 個月後的 EPS：中位 |ln(預測 ÷ 實際)|（越小越好）")
    print(t[["期間", "組別", "n"] + [c for c in t.columns if c.endswith("中位|誤差|")]].round(3).to_string(index=False))
    print("\n== 中位偏差（正＝高估）")
    print(t[["期間", "組別"] + [c for c in t.columns if c.endswith("中位偏差")]].round(3).to_string(index=False))
    t.to_csv(os.path.join(HERE, "results", "eps_extension_scores.csv"), index=False, float_format="%.6f")


if __name__ == "__main__":
    main()
