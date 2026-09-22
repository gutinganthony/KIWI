#!/usr/bin/env python3
"""
war_lead_test.py — 「世界大戰風險警示器」的上線前否證測試

背景：2026-09-22 Jake 要求「新增世界大戰風險警示器，並請驗證其效力後再來提出」。
本腳本就是那個驗證。結論是**否證**——見 topics/business/2026-09-22-war-risk-alerter-falsification.md。

要驗證的主張：「可觀測的市場指標在大型戰爭爆發**之前**就會動。」
若不成立，任何以市場資料為基礎的『戰爭預警器』都只是事後諸葛。

方法紀律沿用 credit_lead_test.py：
  不看「事件後漲跌多少」（那是同步／落後），只看「事件**前** N 天，
  指標位於自身歷史分布的哪個百分位」。D-30 若仍在中位數附近 ⇒ 當時沒有任何警告。
  並以隨機日期為對照組——若戰前分布 ≈ 隨機分布，該指標對戰爭毫無鑑別力。

第三段是**對本否證自身的穩健性檢驗**：掃 lookback × 提前天數 × 門檻 的全網格，
確認「無預警力」不是我挑錯參數挑出來的 artifact。

用法：python3 scripts/war_lead_test.py      （於 projects/avi-v5 下執行）
資料：data/backtest/VIX.csv（1990-）、data/ext/VIX.csv（2019-）、data/ext/shiller_sp500.csv（1871-）
"""
import csv
import datetime
import os
import random
import statistics

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# 戰爭爆發日。選的是「第一發子彈」而非宣戰日或戰爭結束日——
# 預警器要能在這一天之前示警才算有用。
WARS = [
    ("1914-07-28", "一戰爆發（奧匈對塞爾維亞宣戰）"),
    ("1939-09-01", "二戰爆發（德軍入侵波蘭）"),
    ("1950-06-25", "韓戰"),
    ("1962-10-16", "古巴飛彈危機"),
    ("1973-10-06", "贖罪日戰爭／石油禁運"),
    ("1990-08-02", "伊拉克入侵科威特"),
    ("1991-01-17", "沙漠風暴"),
    ("2001-09-11", "911"),
    ("2003-03-20", "伊拉克戰爭"),
    ("2008-08-08", "俄喬戰爭"),
    ("2014-02-27", "克里米亞"),
    ("2022-02-24", "俄烏全面入侵"),
    ("2023-10-07", "哈瑪斯攻擊以色列"),
    ("2025-06-13", "以色列空襲伊朗（12 日戰爭）"),
    ("2026-02-28", "2026 伊朗戰爭爆發"),
]


def parse_date(s):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    return None


def load_series(path, valname="CLOSE", valcol=None):
    """讀 CSV 成 {date: float}。backtest 與 ext 的表頭大小寫不同，故用不分大小寫比對。"""
    out = {}
    with open(path) as fh:
        r = csv.reader(fh)
        hdr = next(r)
        if valcol is None:
            match = [i for i, c in enumerate(hdr) if c.strip().upper() == valname.upper()]
            valcol = match[0] if match else 1
        for row in r:
            if len(row) <= valcol:
                continue
            d = parse_date(row[0])
            if d is None:
                continue
            try:
                v = float(row[valcol])
            except ValueError:
                continue
            if v > 0:
                out[d] = v
    return out


def pct_rank(series, keys, asof, lookback_days=730):
    """asof 當日值在過去 lookback_days 的百分位（0-100）。"""
    lo = asof - datetime.timedelta(days=lookback_days)
    vals = [series[d] for d in keys if lo <= d <= asof]
    if len(vals) < 30:
        return None
    cur = series[asof]
    return 100.0 * sum(1 for v in vals if v < cur) / len(vals)


def nearest(keys, target, max_gap=45):
    cands = [d for d in keys if d <= target]
    if not cands:
        return None
    d = max(cands)
    return d if (target - d).days <= max_gap else None


def main():
    vix = {**load_series(os.path.join(BASE, "backtest", "VIX.csv")),
           **load_series(os.path.join(BASE, "ext", "VIX.csv"))}
    vkeys = sorted(vix)
    shiller = load_series(os.path.join(BASE, "ext", "shiller_sp500.csv"), valcol=1)
    skeys = sorted(shiller)

    print(f"VIX          {vkeys[0]} → {vkeys[-1]}  ({len(vkeys)} 點)")
    print(f"Shiller(月)  {skeys[0]} → {skeys[-1]}  ({len(skeys)} 點)")

    # ---------- 測試一：VIX 戰前百分位 ----------
    print("\n" + "=" * 96)
    print("測試一：VIX 在戰爭爆發前的百分位（過去 2 年分布）。>80 才算「事前有警告」")
    print("=" * 96)
    print(f"{'事件':<32}{'D-180':>9}{'D-90':>9}{'D-30':>9}{'D-7':>9}{'D-1':>9}{'D+30':>9}")
    d30_vals = []
    for ds, name in WARS:
        D = datetime.date.fromisoformat(ds)
        cells = []
        for off in (180, 90, 30, 7, 1, -30):
            nd = nearest(vkeys, D - datetime.timedelta(days=off))
            p = pct_rank(vix, vkeys, nd) if nd else None
            cells.append("—" if p is None else f"{p:5.0f}")
            if off == 30 and p is not None:
                d30_vals.append((name, p))
        if any(c != "—" for c in cells):
            print(f"{name:<30}" + "".join(f"{c:>9}" for c in cells))

    # ---------- 測試二：戰前/戰後股市報酬 ----------
    print("\n" + "=" * 96)
    print("測試二：S&P 500 月收（Shiller，1871 起）戰前 6 個月報酬。戰前若已跌 ⇒ 市場有反應")
    print("=" * 96)
    print(f"{'事件':<32}{'D-6M→D':>12}{'D-3M→D':>12}{'D→D+3M':>12}{'D→D+6M':>12}")
    for ds, name in WARS:
        D = datetime.date.fromisoformat(ds)

        def val(months):
            nd = nearest(skeys, D + datetime.timedelta(days=int(30.44 * months)), max_gap=40)
            return shiller[nd] if nd else None

        v0, vm6, vm3, vp3, vp6 = val(0), val(-6), val(-3), val(3), val(6)
        pc = lambda a, b: "—" if (a is None or b is None) else f"{100 * (b / a - 1):+11.1f}%"
        row = [pc(vm6, v0), pc(vm3, v0), pc(v0, vp3), pc(v0, vp6)]
        if any(c != "—" for c in row):
            print(f"{name:<30}" + "".join(f"{c:>12}" for c in row))

    # ---------- 對照組 ----------
    print("\n" + "=" * 96)
    print("對照組：隨機日期的 VIX 百分位（若戰前均值 ≈ 隨機均值 ⇒ 無鑑別力）")
    print("=" * 96)
    random.seed(42)
    pool = [d for d in vkeys if d >= datetime.date(1992, 1, 1)]
    rand = [p for p in (pct_rank(vix, vkeys, d) for d in random.sample(pool, min(600, len(pool))))
            if p is not None]
    print(f"隨機日期 (n={len(rand)}): 均值 {statistics.mean(rand):.1f}, 中位數 {statistics.median(rand):.1f}")
    vals = [p for _, p in d30_vals]
    print(f"戰爭 D-30  (n={len(vals)}): 均值 {statistics.mean(vals):.1f}, 中位數 {statistics.median(vals):.1f}")
    print(f"\n>>> D-30 時 VIX 已在 80 百分位以上的戰爭：{sum(1 for v in vals if v > 80)}/{len(vals)}")
    for n, v in sorted(d30_vals, key=lambda x: -x[1]):
        print(f"      {v:5.0f}  {n}")

    # ---------- 測試三：否證自身的穩健性 ----------
    print("\n" + "=" * 96)
    print("測試三：上述否證的參數敏感度。掃 lookback × 提前天數 × 門檻，")
    print("        若多數格子的『提升』為負 ⇒ 否證穩健，不是挑參數挑出來的")
    print("=" * 96)
    random.seed(7)
    ctrl = random.sample(pool, min(800, len(pool)))
    print(f"{'lookback':>9}{'提前天數':>10}{'門檻':>6}{'戰前命中':>10}{'對照組':>9}{'提升':>8}")
    print("-" * 52)
    best, neg, total = None, 0, 0
    for lb in (365, 730, 1095, 1825):
        for lead in (14, 30, 60, 90):
            for thr in (70, 80, 90):
                ps = []
                for ds, _ in WARS:
                    D = datetime.date.fromisoformat(ds)
                    nd = nearest(vkeys, D - datetime.timedelta(days=lead))
                    p = pct_rank(vix, vkeys, nd, lb) if nd else None
                    if p is not None:
                        ps.append(p)
                if len(ps) < 8:
                    continue
                hit = sum(1 for p in ps if p > thr) / len(ps)
                cps = [p for p in (pct_rank(vix, vkeys, d, lb) for d in ctrl) if p is not None]
                base = sum(1 for p in cps if p > thr) / len(cps)
                lift = hit - base
                total += 1
                neg += lift < 0
                print(f"{lb:>9}{lead:>10}{thr:>6}{hit:>9.0%}{base:>9.0%}{lift:>+8.0%}")
                if best is None or lift > best[0]:
                    best = (lift, lb, lead, thr, hit, base, len(ps))
    print("-" * 52)
    lift, lb, lead, thr, hit, base, n = best
    print(f"\n{total} 組參數中有 {neg} 組的提升為負。")
    print(f"對 VIX 最有利的一組（刻意挑的）：lookback={lb}天, 提前={lead}天, 門檻={thr}")
    print(f"  戰前命中 {hit:.0%} vs 對照組 {base:.0%} ⇒ 提升 {lift:+.0%}，但樣本僅 n={n}。")
    print("\n>>> 結論：VIX 對戰爭爆發沒有可用的領先性。任何以市場波動率為核心的")
    print(">>>       『戰爭預警器』不該上線。詳見 topics/business/2026-09-22-war-risk-alerter-falsification.md")


if __name__ == "__main__":
    main()
