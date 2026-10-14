#!/usr/bin/env python3
"""README §25.0：鏡像的 Stooq 日股價，2022-12-19 之後的除息有沒有做股利還原——逐筆用 Yahoo 原始收盤價核對。

    python3 research/stooq_div_check.py --hj <hanumantjain data 目錄> --raw <Yahoo 5 年日線目錄（d5_<代號>.json）> > results/stooq_div_check.txt

Yahoo chart（range=5y、interval=1d）的 close 只做分割還原（原始價）。Stooq 的還原價 A(t)＝P(t) × Π_{有還原的除息 d > t}(1 − y_d)，
所以 r(t)＝A(t) ÷ P(t) 只在「有還原的除息日」跳一階：跳幅 ≈ 1 − y_d。逐筆量 (1 − r_前 ÷ r_後) ÷ y_d（前後各 3 個交易日的中位數）：
≈ 1 → 這筆有還原；≈ 0 → 沒有。大多數公司 2022-12-19（含）以前的都有、之後的都沒有；少數公司之後仍持續（或只還原特別股利）。
產出：
  data/stooq_div_adjusted.csv：2022-12-19 以後、Stooq 仍有還原的除息（ticker, ex_date）——build_broad.py 會把它們也反推
  data/stooq_div_full.csv：之後的除息 ≥ 80% 都有還原的公司——pef/data.py（68 家科技股面板，用季報股利、沒有除息日）整家照舊全部反推
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUT = pd.Timestamp("2022-12-20")                         # 不含：12-19（含）以前的除息，Stooq 都有還原
END = pd.Timestamp("2025-09-09")                         # 鏡像的 Stooq 到這天


def stooq(hj, t):
    p = os.path.join(hj, "sp500_stooq_ohcl", f"{t.lower().replace('.', '-')}.us.txt")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p)
    d.columns = [c.strip("<>").lower() for c in d.columns]
    d["date"] = pd.to_datetime(d["date"].astype(str), format="%Y%m%d")
    return d.set_index("date")["close"].sort_index()


def yahoo(raw, t):
    p = os.path.join(raw, f"d5_{t.replace('.', '-')}.json")
    if not os.path.exists(p) or os.path.getsize(p) < 2000:
        return None
    try:
        c = json.load(open(p))["chart"]["result"][0]
        return pd.Series(c["indicators"]["quote"][0]["close"], index=pd.to_datetime(c["timestamp"], unit="s").normalize()).dropna()
    except (KeyError, TypeError, IndexError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hj", required=True)
    ap.add_argument("--raw", required=True)
    a = ap.parse_args()
    uni = pd.read_csv(os.path.join(HERE, "data", "universe_sp500.csv"))
    ca = pd.read_csv(os.path.join(a.hj, "sp500_corporate_actions_yfinance.csv"), parse_dates=["ex_date"])
    dv = ca[(ca["event_type"] == "dividend") & (ca["ex_date"] >= CUT - pd.DateOffset(days=60)) & (ca["ex_date"] <= END)].dropna(subset=["cash_amount"])
    rows, tick = [], []
    for t in uni["ticker"]:
        s, y = stooq(a.hj, t), yahoo(a.raw, t)
        g = dv[dv["symbol"] == t]
        if s is None or y is None or g.empty:
            continue
        r = (s / y.reindex(s.index)).dropna()
        r = r[(r.index >= CUT - pd.DateOffset(days=90)) & (r.index <= END)]
        if len(r) < 100:
            continue
        tick.append(t)
        for ex, D in zip(g["ex_date"], g["cash_amount"]):
            bef, aft = r[r.index < ex].iloc[-3:], r[r.index >= ex].iloc[:3]
            pb = y[y.index < ex]
            if len(bef) < 2 or len(aft) < 2 or pb.empty or not D > 0:
                continue
            yd = float(D) / float(pb.iloc[-1])
            if yd < 0.001:
                continue
            adj = (1 - float(bef.median()) / float(aft.median())) / yd
            rows.append(dict(ticker=t, ex_date=ex, y=yd, 還原比例=adj, 有還原=adj > 0.5))
    d = pd.DataFrame(rows)
    pre = d[d["ex_date"] < CUT]
    post = d[d["ex_date"] >= CUT]
    pd.set_option("display.width", 200)
    print(f"核對 {len(tick)} 家、{len(d):,} 筆除息（2022-10～2025-09；Stooq ÷ Yahoo 原始收盤的跳幅 ÷ 股息殖利率）")
    print(f"  2022-12-19（含）以前：{pre['有還原'].mean():.1%} 有還原（{len(pre)} 筆）；之後：{post['有還原'].mean():.1%} 有還原（{len(post)} 筆）")
    wk = post.assign(週=post["ex_date"].dt.to_period("W").astype(str)).groupby("週")["有還原"].mean()
    print("  之後逐週有還原的比例（前 8 週）：" + "、".join(f"{k[:10]} {v:.0%}" for k, v in wk.head(8).items()))
    adj_post = post[post["有還原"]]
    by = post.groupby("ticker")["有還原"].agg(["mean", "sum", "size"])
    full = by[by["mean"] >= 0.8].index.tolist()
    part = by[(by["sum"] > 0) & (by["mean"] < 0.8)]
    print(f"\n之後仍有還原的除息：{len(adj_post)} 筆、{adj_post['ticker'].nunique()} 家；其中之後的除息 ≥ 80% 都有還原（持續還原）：{len(full)} 家")
    print("  持續還原：" + "、".join(full))
    print("  只有部分還原（例：只還原特別股利）：" + "、".join(f"{t}（{int(r['sum'])}／{int(r['size'])}）" for t, r in part.iterrows()))
    adj_post[["ticker", "ex_date"]].assign(ex_date=adj_post["ex_date"].dt.date).to_csv(os.path.join(HERE, "data", "stooq_div_adjusted.csv"), index=False)
    pd.DataFrame({"ticker": full}).to_csv(os.path.join(HERE, "data", "stooq_div_full.csv"), index=False)


if __name__ == "__main__":
    main()
