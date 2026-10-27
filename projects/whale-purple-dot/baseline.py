#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紫點 vs「同一天隨便買」── 等權隨機基準
=====================================

加權指數是市值加權（台積電一檔就占很大比重），2024～2026 的 AI 行情裡一般個股本來就大幅落後指數，
所以「贏不贏加權指數」分不出紫點有沒有用。這支程式回答的是：

    同一天進場、同一天出場，紫點挑出來的股票，有沒有比「母體裡全部股票等權平均」好？

做法：對 trades CSV 的每一筆交易，取同一組（進場日開盤 → 出場日收盤）在母體所有股票上的平均報酬
（扣同樣的來回成本），當作那筆交易的基準。排除 jump_flag 的交易，母體股票若在該區間有跳價也排除。

  python baseline.py whale_out/trades_2026-07_any_purple_v0_h60_slNone_tsNone.csv
  python baseline.py whale_out/trades_*.csv            # 一次比很多份
  python baseline.py --minvol 3000 whale_out/trades_*_v3000_*.csv
        # 有均量門檻的回測要用同樣門檻的母體比（入選當天 20 日均量 ≥ N 張的股票），不然比到的是「大型股 vs 全部」

只讀 whale_cache/ 裡已下載的 K 線（請先跑過 whale_purple_dot.py backtest）。
"""

import argparse
import csv
import glob
import json
import os
import statistics
import sys
from collections import defaultdict

from whale_purple_dot import CONFIG


def load_cache(cache_dir):
    """每個代號取資料最長的那份快取 → {code: {date: (open, close, idx)}}, {code: [closes]}, {code: [20日均量(張)]}"""
    best = {}
    for fn in glob.glob(os.path.join(cache_dir, "*.json")):
        base = os.path.basename(fn)
        if base.startswith(("^", "universe_")):
            continue
        code = base.split(".")[0]
        size = os.path.getsize(fn)
        if code not in best or size > best[code][1]:
            best[code] = (fn, size)
    px, closes, vol20 = {}, {}, {}
    for code, (fn, _) in best.items():
        try:
            with open(fn, encoding="utf-8") as fh:
                rows = json.load(fh)
        except ValueError:
            continue
        px[code] = {r["time"]: (r["open"], r["close"], i) for i, r in enumerate(rows)}
        closes[code] = [r["close"] for r in rows]
        v = [r["volume"] or 0 for r in rows]
        vol20[code] = [sum(v[max(0, i - 19): i + 1]) / len(v[max(0, i - 19): i + 1]) / 1000 for i in range(len(v))]
    return px, closes, vol20


def has_jump(cl, i0, i1, jump_pct):
    return any(abs(cl[k] / cl[k - 1] - 1) * 100 > jump_pct for k in range(max(1, i0), i1 + 1))


def universe_ret(px, closes, vol20, d0, d1, cost, jump_pct, minvol, memo):
    key = (d0, d1, minvol)
    if key in memo:
        return memo[key]
    rs = []
    for code, m in px.items():
        a, b = m.get(d0), m.get(d1)
        if not a or not b or not a[0]:
            continue
        if minvol and (a[2] < 1 or vol20[code][a[2] - 1] < minvol):   # 入選日（進場前一根）的均量
            continue
        if has_jump(closes[code], a[2], b[2], jump_pct):
            continue
        rs.append((b[1] / a[0] - 1) * 100 - cost)
    memo[key] = statistics.mean(rs) if rs else None
    return memo[key]


def analyze(path, px, closes, vol20, cfg, minvol, memo):
    trades = [t for t in csv.DictReader(open(path, encoding="utf-8-sig"))
              if not t["exit_reason"].startswith("未平倉") and t.get("jump_flag", "0") != "1"]
    rows = []
    for t in trades:
        u = universe_ret(px, closes, vol20, t["entry_date"], t["exit_date"], cfg["COST_ROUNDTRIP_PCT"], cfg["JUMP_PCT"], minvol, memo)
        if u is not None:
            rows.append((t, float(t["ret_pct"]), u))
    if not rows:
        print(f"\n{os.path.basename(path)}：沒有可比的交易"); return
    ex = [r - u for _, r, u in rows]
    print(f"\n{os.path.basename(path)}" + (f"　（母體限 20 日均量 ≥{minvol} 張）" if minvol else ""))
    print(f"  筆數 {len(rows)}　紫點平均 {statistics.mean(r for _, r, _ in rows):+.2f}%　"
          f"同期等權母體平均 {statistics.mean(u for _, _, u in rows):+.2f}%")
    print(f"  超額（紫點 − 母體）：平均 {statistics.mean(ex):+.2f}pp　中位 {statistics.median(ex):+.2f}pp　"
          f"贏母體比例 {sum(1 for x in ex if x > 0) / len(ex) * 100:.1f}%")
    # 按進場日彙總：每天的紫點平均 vs 母體 → 天數才比較接近獨立樣本
    by_day = defaultdict(list)
    for t, r, u in rows:
        by_day[t["entry_date"]].append(r - u)
    day_ex = [statistics.mean(v) for v in by_day.values()]
    se = statistics.stdev(day_ex) / len(day_ex) ** 0.5 if len(day_ex) > 1 else float("nan")
    print(f"  依進場日彙總 {len(day_ex)} 天：平均超額 {statistics.mean(day_ex):+.2f}pp（±{se:.2f} 標準誤，天與天的持有期仍重疊，只是粗估）　"
          f"超額為正的天數 {sum(1 for x in day_ex if x > 0) / len(day_ex) * 100:.1f}%")
    by_kind = defaultdict(list)
    for t, r, u in rows:
        by_kind[t["kind"]].append(r - u)
    print("  依場景（平均超額 / 中位超額 / 筆數）：")
    for k in sorted(by_kind):
        v = by_kind[k]
        print(f"    {k:<10} {statistics.mean(v):+6.2f}pp　{statistics.median(v):+6.2f}pp　{len(v):>5}")
    by_year = defaultdict(list)
    for t, r, u in rows:
        by_year[t["entry_date"][:4]].append(r - u)
    print("  依進場年份平均超額：" + "　".join(f"{y} {statistics.mean(v):+.2f}pp({len(v)})" for y, v in sorted(by_year.items())))


def main():
    ap = argparse.ArgumentParser(description="紫點 vs 同期等權母體")
    ap.add_argument("trades", nargs="+", help="trades CSV（可用萬用字元）")
    ap.add_argument("--minvol", type=int, default=0, help="母體只算入選當天 20 日均量 ≥ N 張的股票")
    a = ap.parse_args()
    paths = []
    for x in a.trades:
        paths += sorted(glob.glob(x))
    if not paths:
        print(__doc__); sys.exit(1)
    cfg = dict(CONFIG)
    print("讀取快取 K 線…", file=sys.stderr)
    px, closes, vol20 = load_cache(cfg["CACHE_DIR"])
    print(f"母體 {len(px)} 檔", file=sys.stderr)
    memo = {}
    for p in paths:
        analyze(p, px, closes, vol20, cfg, a.minvol, memo)


if __name__ == "__main__":
    main()
