#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F 強勢續攻（＋I 極端洗盤）紫點策略 ── 詳細回測
===============================================

  python fi_strategy.py                          # 2021-11-01 起、F＋I、兩種出場、5／10／20 檔投組
  python fi_strategy.py --kinds F --start 2021-11-01

兩層：
一、逐筆（每顆 F／I 紫點都算一筆，隔天開盤買）：報酬分布、勝率、賺賠比、持有天數、浮虧／浮盈、
    依年份／場景／出場原因／大盤多空／均量分組，以及相對同期「全部股票等權」的超額。
二、實際可操作的投組：只有 N 個位子（5／10／20），每天開盤把可用資金平均分給新訊號，
    同一檔同時只持有一筆；訊號比位子多時，依入選日 20 日均量由大到小優先。
    手續費 0.1425%×2、證交稅 0.3%（賣出）。逐日市值 → 年化、波動、Sharpe、最大回撤、逐年報酬，
    跟同期全部股票等權、加權指數比。

出場規則（兩種，都是收盤判斷）：
  MA60：持有滿 20 個交易日後，收盤跌破 60 日均線 → 隔天開盤賣；最長 250 個交易日到期以收盤賣
  H120：持有 120 個交易日到期，收盤賣

只讀 whale_cache/（請先跑 whale_purple_dot.py backtest --start 同一天）。
"""

import argparse
import bisect
import csv
import math
import os
import random
import statistics
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta

import whale_purple_dot as W

CFG = dict(W.CONFIG)
BUY_FEE, SELL_FEE = 0.001425, 0.001425 + 0.003
EXITS = {
    "MA60": {"hold": 250, "ma": 60, "min_hold": 20},
    "H120": {"hold": 120, "ma": None, "min_hold": 0},
}


def code_kind(kind):
    return W.KIND_LABEL[kind].split()[0]


# ════════════════════════════════════════════════════════════════════
# 每檔：F／I 紫點的逐筆交易（兩種出場）、收盤價、母體日報酬
# ════════════════════════════════════════════════════════════════════
def do_chunk(args):
    jobs, rule_version, start, end, kinds, jump_pct = args
    trades = {k: [] for k in EXITS}
    closes = {}
    uni = defaultdict(lambda: [0.0, 0])
    for code, name, rows in jobs:
        eye = W.whale_eye_v3(rows, rule_version)
        if not eye:
            continue
        n = len(rows)
        O = [r["open"] for r in rows]
        C = [r["close"] for r in rows]
        Lo = [r["low"] for r in rows]
        Hi = [r["high"] for r in rows]
        T = [r["time"] for r in rows]
        v = [r["volume"] or 0 for r in rows]
        vol20 = [sum(v[max(0, i - 19): i + 1]) / len(v[max(0, i - 19): i + 1]) / 1000 for i in range(n)]
        jump = [False] + [abs(C[i] / C[i - 1] - 1) * 100 > jump_pct for i in range(1, n)]
        ma60 = W._sma(C, 60)
        for k in range(1, n):
            if not jump[k]:
                u = uni[T[k]]; u[0] += C[k] / C[k - 1] - 1; u[1] += 1
        used = False
        for m in eye["launch"]:
            si = m["idx"]
            if T[si] < start or T[si] > end or si + 1 >= n or code_kind(m["kind"]) not in kinds:
                continue
            ei = si + 1
            px = O[ei]
            for xname, x in EXITS.items():
                xi = xpx = why = None
                lo, hi = px, px
                for k in range(ei, min(ei + x["hold"], n - 1) + 1):
                    lo, hi = min(lo, Lo[k]), max(hi, Hi[k])
                    if k - ei >= x["hold"]:
                        xi, xpx, why = k, C[k], "到期"; break
                    if x["ma"] and k - ei >= x["min_hold"] and ma60[k] is not None and C[k] < ma60[k] and k + 1 < n:
                        xi, xpx, why = k + 1, O[k + 1], "跌破MA60"; break
                end_k = xi if xi is not None else n - 1
                if any(jump[k] for k in range(ei, end_k + 1)):
                    continue
                if xi is None:
                    xi, xpx, why = n - 1, C[n - 1], "未平倉"
                trades[xname].append({
                    "code": code, "name": name, "kind": code_kind(m["kind"]),
                    "signal_date": T[si], "entry_date": T[ei], "entry_px": px,
                    "exit_date": T[xi], "exit_px": xpx, "exit_reason": why, "days": xi - ei,
                    "ret": (xpx * (1 - SELL_FEE)) / (px * (1 + BUY_FEE)) * 100 - 100,
                    "mae": (lo / px - 1) * 100, "mfe": (hi / px - 1) * 100,
                    "vol20": round(vol20[si]), "fast": round(m["fast"], 1), "slow": round(m["slow"], 1),
                })
                used = True
        if used:
            closes[code] = {"T": T, "O": O, "C": C}
    return trades, closes, dict(uni)


# ════════════════════════════════════════════════════════════════════
# 統計工具
# ════════════════════════════════════════════════════════════════════
def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    f = math.floor(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def perf(days, ret):
    eq, peak, mdd, rs = 1.0, 1.0, 0.0, []
    for d in days:
        r = ret.get(d, 0.0)
        rs.append(r)
        eq *= 1 + r
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    yrs = len(days) / 245
    cagr = (eq ** (1 / yrs) - 1) * 100 if yrs > 0 and eq > 0 else float("nan")
    vol = statistics.pstdev(rs) * math.sqrt(245) * 100 if len(rs) > 1 else float("nan")
    sharpe = statistics.mean(rs) * 245 * 100 / vol if vol and vol > 0 else float("nan")
    return {"cagr": cagr, "vol": vol, "sharpe": sharpe, "mdd": mdd * 100, "total": (eq - 1) * 100}


def line_stats(ts, ex=None):
    r = [t["ret"] for t in ts]
    if not r:
        return "（無）"
    w = [x for x in r if x > 0]; l = [x for x in r if x <= 0]
    pf = sum(w) / -sum(l) if l and sum(l) < 0 else float("inf")
    s = (f"{len(r):>5} 筆　勝率 {len(w) / len(r) * 100:5.1f}%　平均 {statistics.mean(r):+7.2f}%　中位 {statistics.median(r):+7.2f}%　"
         f"獲利因子 {pf:4.2f}　均持有 {statistics.mean(t['days'] for t in ts):5.1f} 日")
    if ex is not None:
        e = [ex[id(t)] for t in ts if ex.get(id(t)) is not None]
        if e:
            s += f"　vs母體 平均 {statistics.mean(e):+6.2f}pp 中位 {statistics.median(e):+6.2f}pp 贏母體 {sum(1 for x in e if x > 0) / len(e) * 100:4.1f}%"
    return s


# ════════════════════════════════════════════════════════════════════
# 有位子上限的投組
# ════════════════════════════════════════════════════════════════════
def simulate_portfolio(trades, closes, days, slots, seed=None):
    """trades：逐筆（已決定好進出場日與價）；依進場日排入 slots 個位子。
    同一天訊號比空位多時：seed=None → 均量大的優先；給 seed → 隨機挑（檢驗結果是不是靠排序規則）。
    回傳 (每日報酬, 實際交易, 每日持股數)"""
    by_entry = defaultdict(list)
    for t in trades:
        by_entry[t["entry_date"]].append(t)
    rnd = random.Random(seed)
    for d in sorted(by_entry):
        if seed is None:
            by_entry[d].sort(key=lambda t: -t["vol20"])
        else:
            rnd.shuffle(by_entry[d])
    idx = {c: {d: i for i, d in enumerate(v["T"])} for c, v in closes.items()}
    cash, held, taken = 1.0, [], []        # held: [trade, shares]
    eq_prev, ret, npos = 1.0, {}, {}

    def mark(d):
        val = cash
        for t, sh in held:
            c = closes[t["code"]]
            i = idx[t["code"]].get(d)
            if i is None:   # 該股當天沒資料（停牌）→ 用最近一個收盤
                k = bisect.bisect_right(c["T"], d) - 1
                i = max(k, 0)
            val += sh * c["C"][i]
        return val

    for d in days:
        # 1) 開盤：條件出場（隔天開盤賣）
        keep = []
        for t, sh in held:
            if t["exit_date"] == d and t["exit_reason"] == "跌破MA60":
                cash += sh * t["exit_px"] * (1 - SELL_FEE)
            else:
                keep.append((t, sh))
        held = keep
        # 2) 開盤：新訊號進場
        cands = [t for t in by_entry.get(d, []) if all(h[0]["code"] != t["code"] for h in held)]
        free = slots - len(held)
        if free > 0 and cands:
            eq_open = mark(d) if held else cash
            for t in cands[:free]:
                alloc = min(eq_open / slots, cash)
                if alloc <= 1e-9:
                    break
                sh = alloc / (t["entry_px"] * (1 + BUY_FEE))
                cash -= alloc
                held.append((t, sh))
                taken.append(t)
        # 3) 收盤：到期出場
        keep = []
        for t, sh in held:
            if t["exit_date"] == d and t["exit_reason"] == "到期":
                cash += sh * t["exit_px"] * (1 - SELL_FEE)
            else:
                keep.append((t, sh))
        held = keep
        eq = mark(d)
        ret[d] = eq / eq_prev - 1
        eq_prev = eq
        npos[d] = len(held)
    return ret, taken, npos


# ════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description="F／I 紫點策略詳細回測")
    ap.add_argument("--start", default="2021-11-01")
    ap.add_argument("--end")
    ap.add_argument("--kinds", default="F,I")
    ap.add_argument("--rule", default=CFG["RULE_VERSION"], choices=["2026-07", "2026-08"])
    ap.add_argument("--slots", default="5,10,20")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    kinds = {k.strip().upper() for k in a.kinds.split(",")}
    start, end = a.start, a.end or date.today().isoformat()
    fetch_start = (date.fromisoformat(start) - timedelta(days=800)).isoformat()
    fetch_end = min((date.fromisoformat(end) + timedelta(days=int(CFG["HOLD_DAYS"] * 1.6) + 5)).isoformat(), date.today().isoformat())

    uni_list = [(c, [tk], name) for c, tk, name in W.fetch_universe(CFG)]
    data = W.load_many(uni_list, fetch_start, fetch_end, CFG)
    bench = {r["time"]: r["close"] for r in (W.fetch_daily(CFG["BENCHMARK"], fetch_start, fetch_end, CFG) or [])}
    items = [(c, d["name"], d["rows"]) for c, d in data.items()]
    nch = a.workers * 4
    trades = {k: [] for k in EXITS}
    closes, uni = {}, defaultdict(lambda: [0.0, 0])
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for tr, cl, un in ex.map(do_chunk, [(items[k::nch], a.rule, start, end, kinds, CFG["JUMP_PCT"]) for k in range(nch)]):
            for k in EXITS:
                trades[k] += tr[k]
            closes.update(cl)
            for d, (s_, c_) in un.items():
                uni[d][0] += s_; uni[d][1] += c_

    all_days = sorted(uni)
    days = [d for d in all_days if start <= d <= end]
    uni_ret = {d: uni[d][0] / uni[d][1] for d in all_days}
    lvl, L = {}, 1.0
    for d in all_days:
        L *= 1 + uni_ret[d]; lvl[d] = L
    bd = sorted(bench)
    twii_ret = {bd[k]: bench[bd[k]] / bench[bd[k - 1]] - 1 for k in range(1, len(bd))}
    tw_ma200 = {}
    for k in range(len(bd)):
        if k >= 199:
            tw_ma200[bd[k]] = sum(bench[bd[j]] for j in range(k - 199, k + 1)) / 200

    out = []
    P = out.append
    P(f"F／I 紫點策略詳細回測　場景 {','.join(sorted(kinds))}　規則 {a.rule}　訊號期間 {start} ~ {end}")
    P(f"成本：買 {BUY_FEE * 100:.4f}%、賣 {SELL_FEE * 100:.4f}%（含證交稅）；排除疑似分割／減資跳價的交易")
    U, TW = perf(days, uni_ret), perf(days, twii_ret)
    P(f"對照（同期）：全部股票等權 年化 {U['cagr']:+.1f}%　回撤 {U['mdd']:.1f}%　Sharpe {U['sharpe']:.2f}　總報酬 {U['total']:+.0f}%")
    P(f"　　　　　　　加權指數　　 年化 {TW['cagr']:+.1f}%　回撤 {TW['mdd']:.1f}%　Sharpe {TW['sharpe']:.2f}　總報酬 {TW['total']:+.0f}%")

    for xname, ts in trades.items():
        closed = [t for t in ts if t["exit_reason"] != "未平倉"]
        exm = {}
        for t in closed:
            k0 = bisect.bisect_left(all_days, t["entry_date"]) - 1
            l0, l1 = (lvl[all_days[k0]] if k0 >= 0 else None), lvl.get(t["exit_date"])
            if l0 and l1:
                exm[id(t)] = t["ret"] - ((l1 / l0 - 1) * 100 - CFG["COST_ROUNDTRIP_PCT"])
        P("")
        P("═" * 100)
        P(f"出場 {xname}：" + ("持有滿 20 日後收盤跌破 MA60 → 隔天開盤賣；最長 250 日" if xname == "MA60" else "持有 120 個交易日，到期收盤賣"))
        P("═" * 100)
        P(f"【一、逐筆（每顆紫點獨立）】已平倉 {len(closed)} 筆，未平倉 {len(ts) - len(closed)} 筆")
        P("  全部　" + line_stats(closed, exm))
        r = [t["ret"] for t in closed]
        w = [x for x in r if x > 0]; l = [x for x in r if x <= 0]
        P(f"  平均獲利 {statistics.mean(w):+.2f}%　平均虧損 {statistics.mean(l):+.2f}%　賺賠比 {statistics.mean(w) / -statistics.mean(l):.2f}")
        P("  報酬分位數：" + "　".join(f"P{int(q * 100)} {pct(r, q):+.1f}%" for q in (0.05, 0.10, 0.25, 0.5, 0.75, 0.90, 0.95)))
        P("  報酬區間：" + "　".join(f"{lab} {sum(1 for x in r if lo_ <= x < hi_) / len(r) * 100:.1f}%" for lab, lo_, hi_ in
                                ((" ≤-30%", -1e9, -30), ("-30~-10%", -30, -10), ("-10~0%", -10, 0), ("0~+10%", 0, 10),
                                 ("+10~+30%", 10, 30), ("+30~+100%", 30, 100), ("≥+100%", 100, 1e9))))
        mae = [t["mae"] for t in closed]; mfe = [t["mfe"] for t in closed]
        P(f"  持有期間最深浮虧（盤中低）：中位 {statistics.median(mae):+.1f}%　P10 {pct(mae, 0.10):+.1f}%　≤-20% 的有 {sum(1 for x in mae if x <= -20) / len(mae) * 100:.1f}%")
        P(f"  持有期間最大浮盈（盤中高）：中位 {statistics.median(mfe):+.1f}%　P90 {pct(mfe, 0.90):+.1f}%　（賣出時平均吐回 {statistics.mean(t['mfe'] - t['ret'] for t in closed):.1f}pp）")
        P(f"  持有天數：中位 {statistics.median(t['days'] for t in closed):.0f}　P25 {pct([t['days'] for t in closed], .25):.0f}　P75 {pct([t['days'] for t in closed], .75):.0f}")
        P("  依出場原因：")
        for why in sorted({t["exit_reason"] for t in closed}):
            P(f"    {why:<8}" + line_stats([t for t in closed if t["exit_reason"] == why], exm))
        P("  依場景：")
        for k in sorted({t["kind"] for t in closed}):
            P(f"    {k}　　　　" + line_stats([t for t in closed if t["kind"] == k], exm))
        P("  依進場年份：")
        for y in sorted({t["entry_date"][:4] for t in closed}):
            P(f"    {y}　　" + line_stats([t for t in closed if t["entry_date"][:4] == y], exm))
        P("  依入選日大盤位置（加權指數 vs 200 日均線）：")
        up = [t for t in closed if t["signal_date"] in tw_ma200 and bench[t["signal_date"]] >= tw_ma200[t["signal_date"]]]
        dn = [t for t in closed if t["signal_date"] in tw_ma200 and bench[t["signal_date"]] < tw_ma200[t["signal_date"]]]
        P("    大盤多頭（≥MA200）" + line_stats(up, exm))
        P("    大盤空頭（<MA200）" + line_stats(dn, exm))
        P("  依入選日 20 日均量（張）：")
        for lab, lo_, hi_ in (("<300", 0, 300), ("300~1000", 300, 1000), ("1000~3000", 1000, 3000), ("3000~10000", 3000, 10000), ("≥10000", 10000, 1e12)):
            P(f"    {lab:<11}" + line_stats([t for t in closed if lo_ <= t["vol20"] < hi_], exm))
        P("  依入選日慢線位置：")
        for lab, lo_, hi_ in (("0~20", -1e9, 20), ("20~35", 20, 35), ("35~50", 35, 50), (">50（I）", 50, 1e9)):
            P(f"    {lab:<11}" + line_stats([t for t in closed if lo_ <= t["slow"] < hi_], exm))
        sig_per_month = defaultdict(int)
        for t in ts:
            sig_per_month[t["signal_date"][:7]] += 1
        sm = list(sig_per_month.values())
        P(f"  訊號頻率：每月中位 {statistics.median(sm):.0f} 顆（最少 {min(sm)}、最多 {max(sm)}），每個交易日平均 {len(ts) / len(days):.1f} 顆")
        best = sorted(closed, key=lambda t: -t["ret"])[:8]
        worst = sorted(closed, key=lambda t: t["ret"])[:8]
        P("  最好的 8 筆：" + "；".join(f"{t['code']}{t['name']} {t['entry_date']} {t['ret']:+.0f}%（{t['days']}日）" for t in best))
        P("  最差的 8 筆：" + "；".join(f"{t['code']}{t['name']} {t['entry_date']} {t['ret']:+.0f}%（{t['days']}日）" for t in worst))

        P("")
        P(f"【二、實際投組（位子上限，均量大的優先；起始 1 元）】")
        years = sorted({d[:4] for d in days})
        P(f"  {'':<14}{'年化':>8}{'波動':>8}{'Sharpe':>8}{'最大回撤':>9}{'總報酬':>9}{'交易數':>7}{'平均持股':>8}" + "".join(f"{y:>8}" for y in years))
        def yearly(rt):
            return "".join(f"{(math.prod(1 + rt.get(d, 0) for d in days if d[:4] == y) - 1) * 100:>+7.1f}%" for y in years)
        P(f"  {'全部股票等權':<12}{U['cagr']:>+7.1f}%{U['vol']:>7.1f}%{U['sharpe']:>8.2f}{U['mdd']:>8.1f}%{U['total']:>+8.0f}%{'':>7}{'':>8}" + yearly(uni_ret))
        P(f"  {'加權指數':<12}{TW['cagr']:>+7.1f}%{TW['vol']:>7.1f}%{TW['sharpe']:>8.2f}{TW['mdd']:>8.1f}%{TW['total']:>+8.0f}%{'':>7}{'':>8}" + yearly(twii_ret))
        for slots in [int(x) for x in a.slots.split(",")]:
            rt, taken, npos = simulate_portfolio(ts, closes, days, slots)
            pf = perf(days, rt)
            P(f"  {f'{slots} 檔投組':<12}{pf['cagr']:>+7.1f}%{pf['vol']:>7.1f}%{pf['sharpe']:>8.2f}{pf['mdd']:>8.1f}%{pf['total']:>+8.0f}%{len(taken):>7}{statistics.mean(npos.values()):>8.1f}" + yearly(rt))
            sims = [perf(days, simulate_portfolio(ts, closes, days, slots, seed)[0]) for seed in range(30)]
            cg = [x["cagr"] for x in sims]; md = [x["mdd"] for x in sims]; sp = [x["sharpe"] for x in sims]
            P(f"    {'隨機挑 30 次':<10} 年化 中位 {statistics.median(cg):+.1f}%（P10 {pct(cg, .1):+.1f}% ~ P90 {pct(cg, .9):+.1f}%，最差 {min(cg):+.1f}%）　"
              f"Sharpe 中位 {statistics.median(sp):.2f}　回撤 中位 {statistics.median(md):.1f}%（最差 {min(md):.1f}%）　"
              f"贏全部股票等權 {sum(1 for x in cg if x > U['cagr'])}/30 次、贏加權 {sum(1 for x in cg if x > TW['cagr'])}/30 次")
            if slots == 10:
                tk_closed = [t for t in taken if t["exit_reason"] != "未平倉"]
                P(f"    （10 檔投組實際做到的交易：{line_stats(tk_closed)}）")
                streak = mx = 0
                for t in sorted(tk_closed, key=lambda t: t["exit_date"]):
                    streak = streak + 1 if t["ret"] <= 0 else 0
                    mx = max(mx, streak)
                P(f"    依出場順序最長連續虧損 {mx} 筆")
                eq, peak, worst_dd_start, dd_days, cur = 1.0, 1.0, None, 0, 0
                for d in days:
                    eq *= 1 + rt[d]
                    if eq >= peak:
                        peak, cur = eq, 0
                    else:
                        cur += 1
                        dd_days = max(dd_days, cur)
                monthly = defaultdict(lambda: 1.0)
                for d in days:
                    monthly[d[:7]] *= 1 + rt[d]
                mr = [v - 1 for v in monthly.values()]
                P(f"    最長「未創新高」期間 {dd_days} 個交易日；月報酬為正的月份 {sum(1 for x in mr if x > 0) / len(mr) * 100:.0f}%，"
                  f"最好月 {max(mr) * 100:+.1f}%、最差月 {min(mr) * 100:+.1f}%")
                os.makedirs(CFG["OUT_DIR"], exist_ok=True)
                fn = os.path.join(CFG["OUT_DIR"], f"fi_portfolio10_{''.join(sorted(kinds))}_{a.rule}_{xname}_trades.csv")
                with open(fn, "w", newline="", encoding="utf-8-sig") as fh:
                    wr = csv.DictWriter(fh, fieldnames=list(taken[0].keys()))
                    wr.writeheader(); wr.writerows(taken)
        os.makedirs(CFG["OUT_DIR"], exist_ok=True)
        with open(os.path.join(CFG["OUT_DIR"], f"fi_all_{''.join(sorted(kinds))}_{a.rule}_{xname}_trades.csv"), "w", newline="", encoding="utf-8-sig") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(ts[0].keys()))
            wr.writeheader(); wr.writerows(sorted(ts, key=lambda t: (t["entry_date"], t["code"])))

    text = "\n".join(out)
    print(text)
    fn = os.path.join("results", f"fi_strategy_{''.join(sorted(kinds))}_{a.rule}_{start}.txt")
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print(f"\n已存 {fn}", file=sys.stderr)


if __name__ == "__main__":
    main()
