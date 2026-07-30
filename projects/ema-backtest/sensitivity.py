#!/usr/bin/env python3
"""敏感度檢查：回測結論對「實作自由度」有多脆弱。

策略本身只定義了訊號，沒定義成交時點、成本、資料起點怎麼處理。這些自由度
會不會把結論翻盤，是「能不能真的拿去交易」的核心問題——如果換個合理假設
結論就反轉，那這個策略的優勢是實作假象，不是市場結構。

檢查三項:
  1. enter_on_warmup（資料起點邊界處理）對 1–24 個月窗的影響
  2. 成交時點：次日開盤 vs 當日收盤
  3. 交易成本：0 / 5 / 10 / 25 bps 單邊

用法: python3 sensitivity.py --prices /tmp/prices
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from ema_backtest import run_backtest
from run_report import WINDOWS, analyse, load_csv, pct, ratio, summarise


def load_all(pdir: Path):
    out = []
    for p in sorted(pdir.glob("*.csv")):
        loaded = load_csv(p)
        if loaded:
            out.append(loaded)
    return out


def variant(data, **kw):
    return [analyse(sym, d, o, c, **kw) for sym, d, o, c in data]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    args = ap.parse_args()

    data = load_all(Path(args.prices))
    print(f"載入 {len(data)} 檔\n")

    # ---- 1. 資料起點邊界 ----------------------------------------------
    print("=" * 72)
    print("1. enter_on_warmup（資料起點邊界）對各窗的影響")
    print("=" * 72)
    worst = 0.0
    for sym, d, o, c in data:
        a = run_backtest(d, o, c, enter_on_warmup=True)["equity"]
        b = run_backtest(d, o, c, enter_on_warmup=False)["equity"]
        n = len(d)
        for label, months in WINDOWS:
            from run_report import months_before

            cut = months_before(d[-1], months)
            idx = [i for i, x in enumerate(d) if x >= cut]
            if not idx or idx[0] < 50 or d[0] > cut:
                continue
            i0 = idx[0]
            ra = a[n - 1] / a[i0] - 1
            rb = b[n - 1] / b[i0] - 1
            worst = max(worst, abs(ra - rb))
    print(f"所有標的 × 所有窗，兩種設定的報酬最大差異: {worst*100:.6f} 個百分點")
    print("→ 差異為 0 即代表回測窗完全不受資料起點處理影響（結論穩健）\n")

    # ---- 2. 成交時點 ---------------------------------------------------
    print("=" * 72)
    print("2. 成交時點：次日開盤（無 look-ahead）vs 當日收盤（樂觀）")
    print("=" * 72)
    nx = variant(data, fill="next_open")
    cl = variant(data, fill="close")
    print(f"{'窗':<5} {'次日開盤':>12} {'當日收盤':>12} {'差異':>12}")
    for label, _ in WINDOWS:
        sn, sc = summarise(nx, label), summarise(cl, label)
        if not sn or not sc:
            continue
        a, b = sn["median_strat_return"], sc["median_strat_return"]
        print(f"{label:<5} {pct(a):>12} {pct(b):>12} {pct(b-a):>12}")
    print("→ 差異大 = 績效有相當比例來自「訊號當根就能成交」這個不現實的假設\n")

    # ---- 3. 交易成本 ---------------------------------------------------
    print("=" * 72)
    print("3. 交易成本敏感度（單邊 bps，含手續費＋滑價）")
    print("=" * 72)
    costs = [0, 5, 10, 25]
    runs = {c: variant(data, cost_bps=c) for c in costs}
    header = f"{'窗':<5}" + "".join(f"{str(c)+'bps':>11}" for c in costs) + f"{'勝過B&H@10bps':>15}"
    print(header)
    for label, _ in WINDOWS:
        line = f"{label:<5}"
        for c in costs:
            s = summarise(runs[c], label)
            line += f"{pct(s['median_strat_return']) if s else 'n/a':>11}"
        s10 = summarise(runs[10], label)
        line += f"{ratio(s10['pct_beat_bh']) if s10 else 'n/a':>15}"
        print(line)
    print("\n→ 交易數越多的標的，成本侵蝕越嚴重；看 25bps 一欄是否仍為正")


if __name__ == "__main__":
    main()
