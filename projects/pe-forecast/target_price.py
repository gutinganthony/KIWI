#!/usr/bin/env python3
"""給你的 EPS，算 h 個月後的本益比與股價區間（README §15）。

    python3 target_price.py MU --eps 60                 # 12 個月後（那時已公布的最近四季）EPS $60
    python3 target_price.py MU --eps 60 --eps2 75       # 另外給再下一年的 EPS（只有 12 個月用得到，通常比較準）
    python3 target_price.py MU --eps 50,60,70           # 悲觀／基準／樂觀：每個情境一列，另給合併的區間
    python3 target_price.py MU --eps-growth 0.4 --h 24  # 用 EPS 成長率（相對目前最近四季）
    python3 target_price.py MU --eps-growth -0.3,0,0.3  # 負的也可以（悲觀情境）
    python3 target_price.py MU --eps 60 --h 18          # 其他距離：6、12、18、24、36 個月

EPS 的口徑：GAAP 稀釋 EPS，「目標日那天已經公布的最近四季」加總（和報價網站的 trailing 本益比一樣）。
非 GAAP（調整後）EPS 通常比 GAAP 高；直接輸入會讓本益比偏低、股價不受影響（股價幾乎不看你的 EPS，見 §15.3）。
資料：results/now_all.csv（now_run.py）、results/cond_model.json（cond_fit.py）。不是投資建議。
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import cond                                     # noqa: E402

RES = os.path.join(HERE, "results")


def reported_through(period_end, target, lag_days=45):
    """目標日那天大概已經公布到哪一季（季末 + 45 天內公布；年報可能晚到 60–75 天）。"""
    q = pd.Timestamp(period_end)
    while q + pd.DateOffset(months=3) + pd.Timedelta(days=lag_days) <= target:
        q = q + pd.DateOffset(months=3)
    return q


PROBS = np.array([0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0])


def neg_values(argv):
    """讓負數開頭的值也能用（--eps-growth -0.3,0,0.3、--eps -0.5,1）：argparse 會把它們當成選項名稱。"""
    out, i = [], 0
    while i < len(argv):
        if argv[i] in ("--eps", "--eps-growth", "--eps2") and i + 1 < len(argv) and re.match(r"^-[\d.]", argv[i + 1]):
            out.append(f"{argv[i]}={argv[i + 1]}")
            i += 2
        else:
            out.append(argv[i])
            i += 1
    return out


def _knots(r):
    """一個情境的 ln 股價分布：80%、50% 區間端點與中位（尾巴在 80% 區間外再放寬 0.6 倍寬度，示意，不是保證）。"""
    l = np.log([r["px_lo80"], r["px_lo50"], r["px"], r["px_hi50"], r["px_hi80"]])
    span = l[4] - l[0]
    return np.concatenate([[l[0] - 0.6 * span], l, [l[4] + 0.6 * span]])


def mixture(rows, ps=(0.1, 0.25, 0.5, 0.75, 0.9)):
    """多個 EPS 情境等權合併：分段線性分布的平均 CDF，用二分法求分位數（和網頁一樣的算法）。"""
    ks = [_knots(r) for r in rows]
    cdf = lambda x: np.mean([np.interp(x, k, PROBS) for k in ks])
    out = []
    for p in ps:
        lo, hi = min(k[0] for k in ks), max(k[-1] for k in ks)
        for _ in range(80):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if cdf(mid) < p else (lo, mid)
        out.append(float(np.exp((lo + hi) / 2)))
    return np.array(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--eps", default=None, help="h 個月後那時已公布的最近四季 EPS（可用逗號給多個情境）")
    ap.add_argument("--eps-growth", default=None, help="EPS 成長率（相對目前最近四季；可用逗號給多個）")
    ap.add_argument("--eps2", type=float, default=None, help="再下一年的 EPS（只有 --h 12 用得到）")
    ap.add_argument("--h", type=int, default=12, choices=list(cond.HORIZONS))
    a = ap.parse_args(neg_values(sys.argv[1:]))
    d = pd.read_csv(os.path.join(RES, "now_all.csv"), parse_dates=["period_end", "price_date"])
    model = json.load(open(os.path.join(RES, "cond_model.json")))
    t = a.ticker.upper().replace(".", "-")
    hit = d[(d["ticker"] == t) | d["aliases"].fillna("").str.split().apply(lambda s: t in s)]
    if hit.empty:
        sys.exit(f"找不到 {t}（results/now_all.csv 只有有季報的美股）")
    row = hit.iloc[0].to_dict()
    eps0, px = float(row["eps0"]), float(row["px"])
    if a.eps:
        eps_list = [float(x) for x in a.eps.split(",")]
    elif a.eps_growth:
        if eps0 <= 0:
            sys.exit("目前最近四季是虧損，成長率沒有意義；請用 --eps 直接給 EPS。")
        eps_list = [eps0 * (1 + float(x)) for x in a.eps_growth.split(",")]
    else:
        sys.exit("請給 --eps 或 --eps-growth")
    target = pd.Timestamp(row["price_date"]) + pd.DateOffset(months=a.h)
    thru = reported_through(row["period_end"], target)
    print(f"{row['ticker']}　{row['name']}")
    print(f"  今天（{pd.Timestamp(row['price_date']).date()}）：股價 {px:,.2f}、最近四季 EPS {eps0:,.2f}"
          f"（季末 {pd.Timestamp(row['period_end']).date()}）、本益比 {px / eps0 if eps0 > 0 else float('nan'):,.1f}")
    print(f"  目標日 {target.date()}：那時大概已公布到 {thru.date()} 那一季 → 你的 EPS 應該是"
          f" {(thru - pd.DateOffset(months=9)).strftime('%Y-%m')} ～ {thru.strftime('%Y-%m')} 這四季的合計（GAAP 稀釋）")
    res = []
    for e in eps_list:
        o = cond.predict_now(row, e, a.h, model, eps2=a.eps2)
        if o is None:
            coe_px = px * np.exp((float(row["y10"]) + model["erp"]) * a.h / 12)
            print(f"  EPS {e}：虧損或 0，本益比沒有定義。股價只能參考「照資金成本漲」≈ {coe_px:,.0f}；"
                  "回測裡目標日虧損的公司，股價誤差比有盈餘的大 50–65%（results/cond_coverage.csv）。")
            continue
        o["eps"] = e
        res.append(o)
    if not res:
        return
    o0 = res[0]
    print(f"\n  {a.h} 個月後｜模型 {o0['model']}（{'也用了再下一年 EPS' if o0['model'] == 'xs2' else '只用這一年的 EPS'}）"
          f"｜區間寬度看股價波動：過去 36 個月年化 {o0['vol']:.0%}{'' if o0['vol_known'] else '（沒有資料，用 S&P 500 中位數）'}"
          f"，是 S&P 500 中位波動股票的 {o0['width']:.2f} 倍")
    print("  EPS      本益比（中位）  本益比 50%／80% 區間          股價（中位）  股價 50% 區間          股價 80% 區間")
    for o in res:
        print(f"  {o['eps']:>7,.2f}  {o['pe']:>10.1f}     {o['pe_lo50']:6.1f}–{o['pe_hi50']:<6.1f}／{o['pe_lo80']:6.1f}–{o['pe_hi80']:<6.1f}"
              f"  {o['px']:>10,.0f}   {o['px_lo50']:>8,.0f}–{o['px_hi50']:<8,.0f}  {o['px_lo80']:>8,.0f}–{o['px_hi80']:<8,.0f}")
    if len(res) > 1:
        q = mixture(res)
        print(f"  合併 {len(res)} 個情境（等權）：股價中位 {q[2]:,.0f}、50% 區間 {q[1]:,.0f}–{q[3]:,.0f}、80% 區間 {q[0]:,.0f}–{q[4]:,.0f}")
    o = res[len(res) // 2]
    unch = px / eps0 * o["eps"] if eps0 > 0 else float("nan")
    coe = px * np.exp(o["mk"])
    print(f"\n  對照（EPS {o['eps']:,.2f}）：「本益比不變」股價 {unch:,.0f}（本益比 {px / eps0 if eps0 > 0 else float('nan'):.1f}）；"
          f"「股價照資金成本漲」{coe:,.0f}（本益比 {coe / o['eps']:.1f}）；模型 {o['px']:,.0f}（相對大盤的調整 {np.exp(o['rel']) - 1:+.1%}）")
    bt, cv = model["backtest"]["保留期"]["xs"][str(a.h)], model["coverage"]
    print(f"  回測（S&P 500，EPS 完全正確時）：{a.h} 個月股價／本益比的中位誤差 {bt['err']:.3f}（ln；保留期 2022 以後，"
          f"一半的實際值落在預測的 {np.exp(-bt['err']):.2f}–{np.exp(bt['err']):.2f} 倍之間）；80% 區間實測涵蓋 "
          f"{cv['選模期'][str(a.h)]['cover80']:.0%}（預測起點 2015–2021）／{cv['保留期'][str(a.h)]['cover80']:.0%}（2022 以後）")
    print("  讀法：EPS 已知時，股價幾乎不隨 EPS 變（盈餘變化多半早就在今天的股價裡），本益比 ≈ 股價 ÷ 你的 EPS。"
          "\n        你的 EPS 若和市場共識不同，那個差距股價可能會反映一部分——模型用的是歷史平均反應，不是你的判斷。")


if __name__ == "__main__":
    main()
