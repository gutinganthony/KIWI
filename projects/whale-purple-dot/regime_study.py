#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紫點 × 市場狀態 ── 先判斷「現在是什麼盤」，再看哪種紫點有用
===========================================================

  python regime_study.py --start 2016-01-01 --split 2021-01-01

先跑過 `whale_purple_dot.py backtest --start 同一天`（K 線在 whale_cache/），產業別在 whale_cache/industry.json。

所有狀態都只用「入選日當天收盤以前」的資料算，沒有前視。

市場狀態（四個維度，每天一個值）
--------------------------------
1. 大盤趨勢（加權指數）
     多頭：MA60 > MA200 且 收盤 > MA60
     空頭：MA60 < MA200 且 收盤 < MA60
     盤整：其他
2. 市場寬度：收盤站上自己 MA60 的股票比例　弱 <35%／中 35～65%／強 >65%
3. 大小型輪動：加權指數 60 日報酬 − 全部股票等權 60 日報酬
     >+5pp 權值股主導／<-5pp 中小型主導／其間 均衡
4. 資金往哪個產業（每檔所屬產業，只算 ≥10 檔的產業）
     產業強弱：產業等權 60 日報酬在所有產業的排名　前 1/3 強／中／後 1/3 弱
     產業資金：產業成交值占全市場比重，近 20 日平均 ÷ 近 120 日平均　>1.2 流入／<0.8 流出／其間 持平

交易：每顆紫點獨立進場（隔天開盤），兩種出場
     H60：持有 60 日收盤賣
     MA60：持有滿 20 日後收盤跌破 MA60 → 隔天開盤賣；最長 250 日
超額＝交易報酬 − 同期全部股票等權指數報酬（扣同樣成本）。

切換策略的驗證：在樣本內（--split 之前）學「哪個狀態下該做哪些場景」，
再原封不動套到樣本外；投組用 20 個位子、隨機挑 30 次（同 fi_strategy.py）。
"""

import argparse
import bisect
import json
import math
import os
import statistics
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta

import whale_purple_dot as W
from fi_strategy import BUY_FEE, SELL_FEE, pct, perf, simulate_portfolio

CFG = dict(W.CONFIG)
KCODE = {k: v.split()[0] for k, v in W.KIND_LABEL.items()}


# ════════════════════════════════════════════════════════════════════
# 子行程：逐檔交易＋橫斷面加總
# ════════════════════════════════════════════════════════════════════
def do_chunk(args):
    jobs, rule_version, start, end, jump_pct, industry = args
    trades, closes = [], {}
    # 橫斷面：日期 → [報酬和, 檔數, 站上MA60檔數, 有MA60檔數]；產業：(產業, 日期) → [報酬和, 檔數, 成交值]
    xs = defaultdict(lambda: [0.0, 0, 0, 0])
    xi = defaultdict(lambda: [0.0, 0, 0.0])
    for code, name, rows in jobs:
        n = len(rows)
        O = [r["open"] for r in rows]
        C = [r["close"] for r in rows]
        T = [r["time"] for r in rows]
        V = [r["volume"] or 0 for r in rows]
        ind = industry.get(code, "其他")
        jump = [False] + [abs(C[i] / C[i - 1] - 1) * 100 > jump_pct for i in range(1, n)]
        ma60 = W._sma(C, 60)
        for k in range(n):
            if k >= 1 and not jump[k]:
                r = C[k] / C[k - 1] - 1
                a = xs[T[k]]; a[0] += r; a[1] += 1
                b = xi[(ind, T[k])]; b[0] += r; b[1] += 1
            if ma60[k] is not None:
                a = xs[T[k]]; a[3] += 1
                if C[k] > ma60[k]:
                    a[2] += 1
            xi[(ind, T[k])][2] += C[k] * V[k]
        eye = W.whale_eye_v3(rows, rule_version)
        if not eye:
            continue
        vol20 = [sum(V[max(0, i - 19): i + 1]) / len(V[max(0, i - 19): i + 1]) / 1000 for i in range(n)]
        used = False
        for m in eye["launch"]:
            si = m["idx"]
            if T[si] < start or T[si] > end or si + 1 >= n:
                continue
            ei = si + 1
            px = O[ei]
            for xname in ("H60", "MA60"):
                hold = 60 if xname == "H60" else 250
                xidx = xpx = why = None
                for k in range(ei, min(ei + hold, n - 1) + 1):
                    if k - ei >= hold:
                        xidx, xpx, why = k, C[k], "到期"; break
                    if xname == "MA60" and k - ei >= 20 and ma60[k] is not None and C[k] < ma60[k] and k + 1 < n:
                        xidx, xpx, why = k + 1, O[k + 1], "跌破MA60"; break
                end_k = xidx if xidx is not None else n - 1
                if any(jump[k] for k in range(ei, end_k + 1)):
                    continue
                if xidx is None:
                    xidx, xpx, why = n - 1, C[n - 1], "未平倉"
                trades.append({"exit": xname, "code": code, "name": name, "ind": ind, "kind": KCODE[m["kind"]],
                               "signal_date": T[si], "entry_date": T[ei], "entry_px": px,
                               "exit_date": T[xidx], "exit_px": xpx, "exit_reason": why, "days": xidx - ei,
                               "ret": (xpx * (1 - SELL_FEE)) / (px * (1 + BUY_FEE)) * 100 - 100,
                               "vol20": round(vol20[si])})
                used = True
        if used:
            closes[code] = {"T": T, "O": O, "C": C}
    return trades, closes, dict(xs), dict(xi)


# ════════════════════════════════════════════════════════════════════
def sma_series(vals, n):
    out, s = [None] * len(vals), 0.0
    for i, v in enumerate(vals):
        s += v
        if i >= n:
            s -= vals[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def mean_or_nan(v):
    return statistics.mean(v) if v else float("nan")


def cell(v):
    """一格：平均超額(筆數)"""
    if not v:
        return f"{'·':>14}"
    return (f"{mean_or_nan(v):+.2f}({len(v)})" + ("*" if len(v) < 30 else "")).rjust(14)


def main():
    ap = argparse.ArgumentParser(description="紫點 × 市場狀態")
    ap.add_argument("--start", default="2016-01-01")
    ap.add_argument("--end")
    ap.add_argument("--split", default="2021-01-01", help="樣本內／樣本外切點")
    ap.add_argument("--rule", default=CFG["RULE_VERSION"], choices=["2026-07", "2026-08"])
    ap.add_argument("--slots", type=int, default=20)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    start, end = a.start, a.end or date.today().isoformat()
    fetch_start = (date.fromisoformat(start) - timedelta(days=800)).isoformat()
    fetch_end = min((date.fromisoformat(end) + timedelta(days=int(CFG["HOLD_DAYS"] * 1.6) + 5)).isoformat(), date.today().isoformat())

    with open(os.path.join(CFG["CACHE_DIR"], "industry.json"), encoding="utf-8") as fh:
        industry = json.load(fh)
    uni_list = [(c, [tk], name) for c, tk, name in W.fetch_universe(CFG)]
    data = W.load_many(uni_list, fetch_start, fetch_end, CFG)
    bench = {r["time"]: r["close"] for r in (W.fetch_daily(CFG["BENCHMARK"], fetch_start, fetch_end, CFG) or [])}
    items = [(c, d["name"], d["rows"]) for c, d in data.items()]
    nch = a.workers * 4
    trades, closes = [], {}
    xs = defaultdict(lambda: [0.0, 0, 0, 0])
    xi = defaultdict(lambda: [0.0, 0, 0.0])
    print(f"計算 {len(items)} 檔…", file=sys.stderr)
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        jobs = [(items[k::nch], a.rule, start, end, CFG["JUMP_PCT"], industry) for k in range(nch)]
        for tr, cl, s_, i_ in ex.map(do_chunk, jobs):
            trades += tr
            closes.update(cl)
            for d, v in s_.items():
                t = xs[d]
                for j in range(4):
                    t[j] += v[j]
            for key, v in i_.items():
                t = xi[key]
                for j in range(3):
                    t[j] += v[j]

    # ── 每日市場狀態 ──
    all_days = sorted(d for d in xs if xs[d][1] > 0)
    days = [d for d in all_days if start <= d <= end]
    uni_ret = {d: xs[d][0] / xs[d][1] for d in all_days}
    lvl, L = {}, 1.0
    for d in all_days:
        L *= 1 + uni_ret[d]; lvl[d] = L
    breadth = {d: xs[d][2] / xs[d][3] * 100 for d in all_days if xs[d][3] > 0}

    bd = sorted(bench)
    bc = [bench[d] for d in bd]
    m60, m200 = sma_series(bc, 60), sma_series(bc, 200)
    trend = {}
    for i, d in enumerate(bd):
        if m200[i] is None:
            continue
        if m60[i] > m200[i] and bc[i] > m60[i]:
            trend[d] = "多頭"
        elif m60[i] < m200[i] and bc[i] < m60[i]:
            trend[d] = "空頭"
        else:
            trend[d] = "盤整"
    twii_ret = {bd[k]: bc[k] / bc[k - 1] - 1 for k in range(1, len(bd))}
    size = {}
    for i, d in enumerate(bd):
        if i < 60 or bd[i - 60] not in lvl or d not in lvl:
            continue
        diff = (bc[i] / bc[i - 60] - lvl[d] / lvl[bd[i - 60]]) * 100
        size[d] = "權值股主導" if diff > 5 else ("中小型主導" if diff < -5 else "均衡")
    bstate = {d: ("弱" if v < 35 else ("強" if v > 65 else "中")) for d, v in breadth.items()}

    # 產業強弱／資金
    inds = sorted({k[0] for k in xi})
    big = [g for g in inds if sum(1 for c in industry.values() if c == g) >= 10]
    ind_lvl, ind_share = {}, {}
    tot_turn = {d: sum(xi[(g, d)][2] for g in inds if (g, d) in xi) for d in all_days}
    for g in big:
        L, lv, sh = 1.0, [], []
        for d in all_days:
            v = xi.get((g, d))
            if v and v[1]:
                L *= 1 + v[0] / v[1]
            lv.append(L)
            sh.append((v[2] / tot_turn[d]) if (v and tot_turn[d]) else 0.0)
        ind_lvl[g] = lv
        s20, s120 = sma_series(sh, 20), sma_series(sh, 120)
        ind_share[g] = [None if (s20[i] is None or s120[i] is None or s120[i] == 0) else s20[i] / s120[i] for i in range(len(sh))]
    pos = {d: i for i, d in enumerate(all_days)}
    ind_strength, ind_flow = {}, {}
    for i, d in enumerate(all_days):
        if i < 60:
            continue
        r60 = sorted(((ind_lvl[g][i] / ind_lvl[g][i - 60] - 1), g) for g in big)
        k = len(r60)
        for rank, (_, g) in enumerate(r60):
            ind_strength[(g, d)] = "弱" if rank < k / 3 else ("強" if rank >= 2 * k / 3 else "中")
        for g in big:
            f = ind_share[g][i]
            if f is not None:
                ind_flow[(g, d)] = "流入" if f > 1.2 else ("流出" if f < 0.8 else "持平")

    # ── 交易標註 ──
    for t in trades:
        d = t["signal_date"]
        k0 = bisect.bisect_left(all_days, t["entry_date"]) - 1
        l0, l1 = (lvl[all_days[k0]] if k0 >= 0 else None), lvl.get(t["exit_date"])
        t["ex"] = t["ret"] - ((l1 / l0 - 1) * 100 - CFG["COST_ROUNDTRIP_PCT"]) if (l0 and l1 and t["exit_reason"] != "未平倉") else None
        t["ex_ind"] = None   # 減「同產業等權」：扣掉產業本身的漲跌，看紫點在產業裡有沒有挑得比較好
        if t["ex"] is not None and t["ind"] in ind_lvl and k0 >= 0 and t["exit_date"] in pos:
            il = ind_lvl[t["ind"]]
            t["ex_ind"] = t["ret"] - ((il[pos[t["exit_date"]]] / il[k0] - 1) * 100 - CFG["COST_ROUNDTRIP_PCT"])
        t["trend"] = trend.get(d, "?")
        t["breadth"] = bstate.get(d, "?")
        t["size"] = size.get(d, "?")
        t["istr"] = ind_strength.get((t["ind"], d), "小產業")
        t["iflow"] = ind_flow.get((t["ind"], d), "小產業")
        t["period"] = "內" if d < a.split else "外"

    out = []
    P = out.append
    P(f"紫點 × 市場狀態　規則 {a.rule}　{start} ~ {end}　樣本內 < {a.split} ≤ 樣本外")
    P(f"可用股票 {len(items)} 檔　紫點交易（H60）{sum(1 for t in trades if t['exit'] == 'H60')} 筆　產業 {len(big)} 個（≥10 檔）")
    P("")
    P("【一、各市場狀態佔的時間，與該狀態下的大盤表現（年化）】")
    for nm, st in (("大盤趨勢", trend), ("市場寬度", bstate), ("大小型輪動", size)):
        P(f"  {nm}")
        for s in sorted({v for d, v in st.items() if d in set(days)}):
            ds = [d for d in days if st.get(d) == s]
            dd = set(ds)
            # 連續區段數
            segs, prev = 0, None
            for d in days:
                cur = st.get(d) == s
                if cur and not prev:
                    segs += 1
                prev = cur
            P(f"    {s:<6} {len(ds) / len(days) * 100:5.1f}% 的交易日（{segs} 段）　該狀態下 等權母體 年化 {(math.prod(1 + uni_ret[d] for d in ds) ** (245 / max(len(ds), 1)) - 1) * 100:+6.1f}%　"
              f"加權 年化 {(math.prod(1 + twii_ret.get(d, 0) for d in ds) ** (245 / max(len(ds), 1)) - 1) * 100:+6.1f}%")
    P("  （「該狀態下」是把屬於這個狀態的交易日串起來算；狀態是當天收盤才知道，這裡只是描述，不是可交易的報酬）")

    def table(xname, dim, title, sub=None, key="ex"):
        ks = sorted({t["kind"] for t in trades})
        states = sorted({t[dim] for t in trades if t["exit"] == xname and t["ex"] is not None and (sub is None or t["period"] == sub)})
        P(f"  {title}" + (f"（樣本{sub}）" if sub else "") + ("：平均超額 pp（筆數）" if key == "ex" else "：平均超額 **減同產業等權** pp（筆數）") + "；* = 少於 30 筆")
        P(f"    {'場景':<6}" + "".join(f"{s:>14}" for s in states))
        for k in ks + ["全部"]:
            row = []
            for s in states:
                v = [t[key] for t in trades if t["exit"] == xname and t[key] is not None and t[dim] == s
                     and (k == "全部" or t["kind"] == k) and (sub is None or t["period"] == sub)]
                row.append(cell(v))
            P(f"    {k:<6}" + "".join(row))

    for xname in ("H60", "MA60"):
        P("")
        P("═" * 100)
        P(f"出場 {xname}" + ("（持有 60 日）" if xname == "H60" else "（滿 20 日後跌破 MA60，最長 250 日）"))
        P("═" * 100)
        P("【二、場景 × 市場狀態】")
        for dim, title in (("trend", "大盤趨勢"), ("breadth", "市場寬度"), ("size", "大小型輪動"), ("istr", "所屬產業強弱"), ("iflow", "所屬產業資金")):
            table(xname, dim, title)
        table(xname, "istr", "所屬產業強弱", key="ex_ind")
        table(xname, "iflow", "所屬產業資金", key="ex_ind")
        P("")
        P("【三、穩定性：大盤趨勢 × 場景，樣本內 vs 樣本外】")
        table(xname, "trend", "大盤趨勢", "內")
        table(xname, "trend", "大盤趨勢", "外")
        table(xname, "istr", "所屬產業強弱", "內")
        table(xname, "istr", "所屬產業強弱", "外")

    # ── 切換策略（MA60 出場的交易，20 檔投組）──
    ma = [t for t in trades if t["exit"] == "MA60"]
    learned = {}
    for s in ("多頭", "盤整", "空頭"):
        ok = []
        for k in sorted({t["kind"] for t in ma}):
            v = [t["ex"] for t in ma if t["period"] == "內" and t["trend"] == s and t["kind"] == k and t["ex"] is not None]
            if len(v) >= 200 and statistics.mean(v) > 0.5:
                ok.append(k)
        learned[s] = ok
    strategies = [
        ("全部紫點（不分狀態）", lambda t: True),
        ("只做 F（不分狀態）", lambda t: t["kind"] == "F"),
        ("F，只在大盤多頭", lambda t: t["kind"] == "F" and t["trend"] == "多頭"),
        ("F，大盤非空頭", lambda t: t["kind"] == "F" and t["trend"] != "空頭"),
        ("F，所屬產業強勢", lambda t: t["kind"] == "F" and t["istr"] == "強"),
        ("F，所屬產業資金流入", lambda t: t["kind"] == "F" and t["iflow"] == "流入"),
        ("F，產業強勢＋大盤非空頭", lambda t: t["kind"] == "F" and t["istr"] == "強" and t["trend"] != "空頭"),
        ("F，市場寬度非弱", lambda t: t["kind"] == "F" and t["breadth"] != "弱"),
        ("全部紫點，產業強勢", lambda t: t["istr"] == "強"),
        ("樣本內學到的「狀態→場景」切換", lambda t: t["kind"] in learned.get(t["trend"], [])),
    ]
    periods = [("全期", days), ("樣本內", [d for d in days if d < a.split]), ("樣本外", [d for d in days if d >= a.split])]
    U = {nm: perf(ds, uni_ret) for nm, ds in periods}
    TW = {nm: perf(ds, twii_ret) for nm, ds in periods}
    P("")
    P("═" * 100)
    P(f"【四、依市場狀態切換的投組】MA60 出場、{a.slots} 個位子、同日訊號多於空位時隨機挑 {a.seeds} 次，取中位數；條件不符的日子不開新倉（已持有照規則出場）")
    P(f"  樣本內學到的切換表（樣本內平均超額 > +0.5pp 且 ≥200 筆的場景）：" + "　".join(f"{s}→{','.join(v) or '不做'}" for s, v in learned.items()))
    P("═" * 100)
    hdr = "".join(f"{nm + ' 年化':>12}{'Sharpe':>8}{'回撤':>8}" for nm, _ in periods)
    P(f"  {'策略':<28}{'訊號數':>8}" + hdr + f"{'外:贏母體':>10}")
    P(f"  {'全部股票等權':<28}{'':>8}" + "".join(f"{U[nm]['cagr']:>+11.1f}%{U[nm]['sharpe']:>8.2f}{U[nm]['mdd']:>7.1f}%" for nm, _ in periods))
    P(f"  {'加權指數':<28}{'':>8}" + "".join(f"{TW[nm]['cagr']:>+11.1f}%{TW[nm]['sharpe']:>8.2f}{TW[nm]['mdd']:>7.1f}%" for nm, _ in periods))
    # 不用紫點的對照：只靠「狀態」本身能做到多少（前一天收盤的狀態決定今天持有什麼）
    strong_ret, timing_ret, both_ret = {}, {}, {}
    for i, d in enumerate(all_days):
        if i == 0:
            continue
        pd_ = all_days[i - 1]
        gs = [g for g in big if ind_strength.get((g, pd_)) == "強"]
        sm = sum(xi[(g, d)][0] for g in gs if (g, d) in xi)
        cn = sum(xi[(g, d)][1] for g in gs if (g, d) in xi)
        strong_ret[d] = sm / cn if cn else uni_ret[d]
        bull = trend.get(pd_) not in ("空頭", None)
        timing_ret[d] = uni_ret[d] if bull else 0.0
        both_ret[d] = strong_ret[d] if bull else 0.0
    for nm_b, rb in (("［對照］強勢產業全部股票等權", strong_ret), ("［對照］大盤非空頭才持有全部股票", timing_ret),
                     ("［對照］強勢產業＋大盤非空頭", both_ret)):
        pb = {nm: perf(ds, rb) for nm, ds in periods}
        P(f"  {nm_b:<26}{'':>8}" + "".join(f"{pb[nm]['cagr']:>+11.1f}%{pb[nm]['sharpe']:>8.2f}{pb[nm]['mdd']:>7.1f}%" for nm, _ in periods))
    P("  （對照組每天換股、沒算成本，是偏樂觀的上限）")
    for nm_s, f in strategies:
        sel = [t for t in ma if f(t)]
        res = {nm: [] for nm, _ in periods}
        for seed in range(a.seeds):
            rt, _, _ = simulate_portfolio(sel, closes, days, a.slots, seed)
            for nm, ds in periods:
                res[nm].append(perf(ds, rt))
        med = {nm: {k: statistics.median(x[k] for x in res[nm]) for k in ("cagr", "sharpe", "mdd")} for nm, _ in periods}
        win_out = sum(1 for x in res["樣本外"] if x["cagr"] > U["樣本外"]["cagr"])
        P(f"  {nm_s:<26}{len(sel):>8}" + "".join(f"{med[nm]['cagr']:>+11.1f}%{med[nm]['sharpe']:>8.2f}{med[nm]['mdd']:>7.1f}%" for nm, _ in periods)
          + f"{win_out:>6}/{a.seeds}")
        # 逐筆超額也列出（不受投組隨機影響）
        e_in = [t["ex"] for t in sel if t["ex"] is not None and t["period"] == "內"]
        e_out = [t["ex"] for t in sel if t["ex"] is not None and t["period"] == "外"]
        P(f"  {'':<26}{'':>8}  逐筆平均超額 樣本內 {mean_or_nan(e_in):+.2f}pp（{len(e_in)}）　樣本外 {mean_or_nan(e_out):+.2f}pp（{len(e_out)}）")

    text = "\n".join(out)
    print(text)
    fn = os.path.join("results", f"regime_study_{a.rule}_{start}.txt")
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print(f"\n已存 {fn}", file=sys.stderr)


if __name__ == "__main__":
    main()
