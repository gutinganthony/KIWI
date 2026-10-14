#!/usr/bin/env python3
"""README §24.7：用成長定價回頭驗證 S&P 500、Nasdaq-100——12、24 個月前預估今天（2026-10-12）的本益比

    python3 research/growth_lookback.py > results/growth_lookback.txt     # 先跑 research/case_broad.py（sp500 與 ndx）

讀 results/case_broad.csv（S&P 500）與 results/case_ndx.csv（Nasdaq-100）。起點：12 個月＝2025-10-02、24 個月＝2024-09-19
（Yahoo 有歷史 forward 本益比的兩天）；成長定價用走動式係數（只用目標日在起點那年以前的 I/B/E/S 配對）。
比較（中位 |ln 本益比誤差|、誤差在 ±20% 內的比例、80% 區間實際涵蓋率）：
  事前（只用起點當時的資料）：本益比不變｜軌道（分析師 forward EPS × 共識係數；24 個月另附不外推）｜
      成長定價（目標日成長預期＝今天的成長率延一年）｜成長定價（成長預期回歸：a ＋ λ × 今天的成長預期，12 個月 λ 約 0.16、24 個月約 0.09）｜
      分組（科技三組用成長定價（回歸）、非科技用軌道＝網頁「自動」在只有範例共識時的規則）
  猜對 EPS（看模型本身的上限）：軌道（EPS_a＝今天的實際值）｜成長定價（EPS_a＝實際、目標日的成長預期＝今天的共識未來 12 個月 × 係數）
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "results")
BIG = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "AVGO", "TSLA", "NFLX", "AMD", "MU", "ORCL", "COST", "TSM", "ASML", "PLTR"]
COLS = [("本益比不變", "誤差_本益比不變", None),
        ("事前｜軌道", "誤差_分析師校正", "區間_軌道事前"),
        ("事前｜軌道不外推", "誤差_改善版", "區間_軌道改善版"),
        ("事前｜成長定價", "成長定價_事前", "區間_成長事前"),
        ("事前｜成長定價（回歸）", "成長定價_事前回歸", "區間_成長事前回歸"),
        ("事前｜分組（科技成長定價、非科技軌道）", "分組_事前", "區間_分組事前"),
        ("猜對｜軌道", "誤差_EPS猜對", "區間_軌道猜對"),
        ("猜對｜成長定價", "成長定價_猜中市場預期", "區間_成長猜對")]


def table(d, idx):
    d = d.copy()
    tech = d["組別"] != "非科技"                         # 網頁「自動」在只有範例共識時的規則（README §24.7）
    d["分組_事前"] = d["成長定價_事前回歸"].where(tech, d["誤差_分析師校正"])
    d["區間_分組事前"] = d["區間_成長事前回歸"].where(tech, d["區間_軌道事前"])
    rows = []
    for h, nm in ((12, "B"), (24, "A")):
        g0 = d[d["情境"].str.startswith(nm)]
        g0 = g0[g0[[c for _, c, _ in COLS]].notna().all(axis=1)]
        for lab, m in (("全部", g0.index), ("科技", g0.index[g0["組別"] != "非科技"]), ("半導體類", g0.index[g0["組別"] == "半導體／設備／記憶體"]),
                       ("非科技", g0.index[g0["組別"] == "非科技"]), ("EPS 變化 > ±50%", g0.index[g0["EPS變化"].abs() > np.log(1.5)])):
            g = g0.loc[m]
            if len(g) < 5:
                continue
            r = dict(指數=idx, h=h, 樣本=lab, n=len(g))
            for k, c, b in COLS:
                if h == 12 and "不外推" in k:
                    continue
                e = g[c]
                r[k] = float(np.median(np.abs(e)))
                r[k + "｜±20%"] = float(np.mean(np.abs(np.exp(e) - 1) <= 0.2))
                r[k + "｜偏差"] = float(np.median(e))
                if b:
                    r[k + "｜80%涵蓋"] = float(g[b].astype(float).mean())
            r["事前：成長定價（回歸）勝軌道的公司比例"] = float(np.mean(g["成長定價_事前回歸"].abs() < g["誤差_分析師校正"].abs()))
            r["猜對：成長定價勝軌道的公司比例"] = float(np.mean(g["成長定價_猜中市場預期"].abs() < g["誤差_EPS猜對"].abs()))
            rows.append(r)
    return pd.DataFrame(rows)


def main():
    sp = pd.read_csv(os.path.join(RES, "case_broad.csv"))
    nd = pd.read_csv(os.path.join(RES, "case_ndx.csv"))
    t = pd.concat([table(sp, "S&P 500"), table(nd, "Nasdaq-100")], ignore_index=True)
    t.to_csv(os.path.join(RES, "growth_lookback_scores.csv"), index=False, float_format="%.6f")
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 60)
    print("起點：12 個月＝2025-10-02、24 個月＝2024-09-19；目標日 2026-10-12。只有今天還在、兩端 EPS > 0 的公司（倖存者偏差）。")
    print("\n== 1. 中位 |ln 本益比誤差|（0.20 ≈ 差 20%）")
    keys = [k for k, _, _ in COLS]
    print(t[["指數", "h", "樣本", "n"] + [k for k in keys if k in t]].round(3).to_string(index=False))
    print("\n== 2. 誤差在實際 ±20% 內的比例")
    print(t[["指數", "h", "樣本"] + [k + "｜±20%" for k in keys if k + "｜±20%" in t]].round(2).to_string(index=False))
    print("\n== 3. 80% 區間實際涵蓋率（目標 80%）")
    print(t[["指數", "h", "樣本"] + [k + "｜80%涵蓋" for k in keys if k + "｜80%涵蓋" in t]].round(2).to_string(index=False))
    print("\n== 4. 中位偏差（ln(預測 ÷ 實際)；負＝預測的本益比太低）")
    print(t[["指數", "h", "樣本"] + [k + "｜偏差" for k in keys if k + "｜偏差" in t]].round(3).to_string(index=False))
    print("\n== 5. 逐家比：成長定價比軌道準的公司比例")
    print(t[["指數", "h", "樣本", "事前：成長定價（回歸）勝軌道的公司比例", "猜對：成長定價勝軌道的公司比例"]].round(2).to_string(index=False))
    print("\n== 6. 大型股：預測的本益比 vs 實際（倍）")
    al = pd.concat([sp.assign(指數="S&P 500"), nd.assign(指數="Nasdaq-100")])
    al = al[al["股票"].isin(BIG)].drop_duplicates(["股票", "情境"]).sort_values(["情境", "股票"], ascending=[False, True])
    pe = lambda c: al["實際本益比"] * np.exp(al[c])      # noqa: E731
    show = pd.DataFrame({"股票": al["股票"], "情境": al["情境"].str[:1].map({"B": "12 個月", "A": "24 個月"}), "起點本益比": al["起點本益比"],
                         "實際": al["實際本益比"], "事前軌道": pe("誤差_分析師校正"), "事前成長定價（回歸）": pe("成長定價_事前回歸"),
                         "猜對軌道": pe("誤差_EPS猜對"), "猜對成長定價": pe("成長定價_猜中市場預期")})
    print(show.round(1).to_string(index=False))
    show.to_csv(os.path.join(RES, "growth_lookback_big.csv"), index=False, float_format="%.4f")


if __name__ == "__main__":
    main()
