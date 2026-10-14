#!/usr/bin/env python3
"""README §25 的表格（markdown）：從 results/long_backtest_rows.csv.gz、bbg_consensus_scores.csv、long_index_scores.csv 產生。

    python3 research/long_summary.py > results/long_summary.md
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "results")


def med(e):
    e = e.dropna()
    return float(np.median(np.abs(e))) if len(e) else np.nan


def fmt(v, best=False):
    if not np.isfinite(v):
        return "—"
    s = f"{v:.3f}"
    return f"**{s}**" if best else s


def row(lab, n, vals, ex_keys):
    """vals：{名稱: 值}；事前方法（ex_keys）裡最小的加粗。"""
    ex = {k: v for k, v in vals.items() if k in ex_keys and np.isfinite(v)}
    b = min(ex, key=ex.get) if ex else None
    return f"| {lab} | {n:,} | " + " | ".join(fmt(v, k == b) for k, v in vals.items()) + " |"


def firm(o):
    out = []
    for h in (12, 24):
        oc = "O" if h == 12 else "O_n"
        cols = [("U", "本益比不變"), (oc, "軌道" if h == 12 else "軌道（不外推）"), ("Gr", "成長定價（回歸）"), ("O_or", "猜對：軌道"), ("GA", "猜對：成長定價")]
        ex = ["本益比不變", cols[1][1], "成長定價（回歸）"]
        out.append(f"\n**{h} 個月：逐年（起點年份）中位 |ln 本益比誤差|**（2017 年起＝走動式係數、嚴格事前；之前＝全期係數，標 ＊）\n")
        out.append("| 起點年份 | n | " + " | ".join(nm for _, nm in cols) + " |")
        out.append("|---|---|" + "---|" * len(cols))
        W = o[(o["h"] == h) & (o["mode"] == "wf")]
        P = o[(o["h"] == h) & (o["mode"] == "prod")]
        for Y in sorted(P["year"].unique()):
            g = W[W["year"] == Y]
            tag = ""
            if len(g) < 15:
                g, tag = P[P["year"] == Y], "＊"
            out.append(row(f"{Y}{tag}", len(g), {nm: med(g[c]) for c, nm in cols}, ex))
        out.append(f"\n**{h} 個月：依組別**\n")
        out.append("| 樣本 | n | " + " | ".join(nm for _, nm in cols) + " |")
        out.append("|---|---|" + "---|" * len(cols))
        for lab, D in (("嚴格事前（走動式）", W), ("全期係數", P)):
            for grp in ("科技", "非科技"):
                g = D[(D["grp"] != "非科技") == (grp == "科技")]
                yrs = f"{g['year'].min()}–{g['year'].max()}"
                out.append(row(f"{lab}，{grp}（{yrs}）", len(g), {nm: med(g[c]) for c, nm in cols}, ex))
        # 市場環境（全期係數，全部組別）
        out.append(f"\n**{h} 個月：依市場環境**（全期係數；大盤倍數＝面板的大盤本益比在這段期間的變化）\n")
        out.append("| 環境 | n | " + " | ".join(nm for _, nm in cols) + " |")
        out.append("|---|---|" + "---|" * len(cols))
        P = P.assign(m=pd.cut(P["mkt_dpe"], [-9, -0.1, 0.1, 9], labels=["大盤本益比收縮（< −10%）", "大盤本益比持平", "大盤本益比擴張（> +10%）"]),
                     e=pd.cut(P["epsg"].abs(), [0, 0.25, 0.5, 9], labels=["個股 EPS 變化 < 25%", "25–50%", "> 50%"], include_lowest=True))
        for c_ in ("m", "e"):
            for k, g in P.groupby(c_, observed=True):
                out.append(row(str(k), len(g), {nm: med(g[c]) for c, nm in cols}, ex))
        cov = {k: float(W[c].dropna().astype(float).mean()) for c, k in (("bO", "軌道"), ("bGr", "成長定價（回歸）"), ("bO_or", "猜對：軌道"), ("bGA", "猜對：成長定價"))}
        w20 = {nm: float(np.mean(np.abs(np.exp(W[c].dropna()) - 1) <= 0.2)) for c, nm in cols}
        out.append(f"\n走動式係數的 80% 區間實際涵蓋（區間分位數用全樣本校準）：" + "、".join(f"{k} {v:.0%}" for k, v in cov.items())
                   + "；誤差在 ±20% 內：" + "、".join(f"{k} {v:.0%}" for k, v in w20.items()) + "。")
    return out


def bbg():
    s = pd.read_csv(os.path.join(RES, "bbg_consensus_scores.csv"))
    out = ["\n**Bloomberg 共識、每個月一個起點（走動式係數）：中位 |ln 本益比誤差|**\n"]
    cols = ["本益比不變", "軌道（延一年）", "軌道（第二年＝分析師）", "軌道不外推", "成長定價（回歸）", "成長定價（第二年＝分析師）", "猜對：軌道", "猜對：成長定價"]
    ex = cols[:6]
    out.append("| 樣本 | n | " + " | ".join(cols) + " |")
    out.append("|---|---|" + "---|" * len(cols))
    for h in (12, 24):
        for grp in ("科技", "非科技"):
            r = s[(s["h"] == h) & (s["年"] == "全部") & (s["組"] == grp)].iloc[0]
            out.append(row(f"{h} 個月，{grp}", int(r["n"]), {c: float(r[c]) if pd.notna(r[c]) else np.nan for c in cols}, ex))
    return out


def index():
    s = pd.read_csv(os.path.join(RES, "long_index_scores.csv"))
    cols = ["本益比不變", "軌道", "成長定價", "成長定價（指數係數）", "猜對：軌道", "猜對：成長定價", "猜對：成長定價（指數係數）"]
    out = ["\n**S&P 500 指數（Shiller），每個月一個起點：中位 |ln 本益比誤差|**\n",
           "| 期間 | 起點數 | " + " | ".join(cols) + " | 實際本益比變化（中位 ln） |", "|---|---|" + "---|" * (len(cols) + 1)]
    for h in (12, 24):
        for r in s[s["h"] == h].itertuples(index=False):
            d = r._asdict()
            vals = {c: float(s.loc[(s["h"] == h) & (s["期間"] == d["期間"]), c].iloc[0]) for c in cols}
            out.append(row(f"{h} 個月，{d['期間']}", int(d["起點數"]), vals, cols[:4])[:-1] + f"| {d['實際本益比變化中位']:+.2f} |")
    return out


def main():
    o = pd.read_csv(os.path.join(RES, "long_backtest_rows.csv.gz"))
    print("\n".join(firm(o) + bbg() + index()))


if __name__ == "__main__":
    main()
