#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紫點出場規則研究 ── 同一批紫點進場，比較幾十種出場規則
=====================================================

  python exit_study.py --start 2021-11-01                 # 過去 5 年、全部紫點
  python exit_study.py --start 2021-11-01 --minvol 1000   # 只取入選日 20 日均量 ≥1000 張
  python exit_study.py --start 2021-11-01 --rule 2026-08 --split 2024-05-01

先跑過一次 `whale_purple_dot.py backtest --start 同一天`，K 線才會在 whale_cache/（這支只讀快取，不重抓）。

做法（跟 whale_purple_dot.py 的回測差在哪，請讀）
------------------------------------------------
* 進場：每一顆紫點都獨立算一筆（入選隔天開盤買），不因「這檔還在持有」而跳過。
  這樣不同出場規則比的是「同一批進場」，出場規則不會反過來改變進場名單。
* 出場：條件型出場（停損、移動停損、停利、指標）一律「當天收盤觸發 → 隔天開盤賣」，不偷看；
  到期出場用到期當天收盤。來回成本同 CONFIG（0.585%）。
* 「最好」不看每筆平均報酬（抱越久、牛市裡平均一定越高），看「投組」：
  每天把所有持有中的部位等權平均 → 日報酬 → 年化報酬、Sharpe、最大回撤，
  並跟「全部股票每天等權」的母體投組（有 --minvol 時母體也套同門檻）以及加權指數比。
  投組沒有部位上限（同時常持有上百檔），是理想化的等權，只用來比較規則之間的相對好壞。
* 防過度擬合：以 --split 切兩段。前段（樣本內）挑出來的規則，要在後段（樣本外）也站得住才算數。
* 跳價（單日收盤漲跌 > JUMP_PCT，多半是沒還原的分割／減資）：該筆交易整筆排除；母體投組略過該股該日。
"""

import argparse
import math
import os
import statistics
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta

import whale_purple_dot as W

CFG = dict(W.CONFIG)


# ════════════════════════════════════════════════════════════════════
# 出場規則
# ════════════════════════════════════════════════════════════════════
def R(name, hold=60, stop=None, trail=None, tp=None, ind=None, min_hold=0):
    return {"name": name, "hold": hold, "stop": stop, "trail": trail, "tp": tp, "ind": ind, "min_hold": min_hold}


RULES = (
    [R(f"持有 {h} 日", hold=h) for h in (5, 10, 20, 40, 60, 90, 120, 250)]
    + [R(f"停損 {int(s * 100)}%＋60 日", stop=s) for s in (0.07, 0.10, 0.15, 0.20)]
    + [R(f"移動停損 {int(t * 100)}%＋{h} 日", trail=t, hold=h) for h in (60, 120, 250) for t in (0.10, 0.15, 0.20, 0.30)]
    + [R(f"停利 {int(p * 100)}%＋60 日", tp=p) for p in (0.15, 0.30, 0.50)]
    + [R("停利 30%＋停損 10%＋60 日", tp=0.30, stop=0.10)]
    + [R(f"紅色交叉（快線下穿慢線）＋{h} 日", ind="red", hold=h) for h in (60, 120, 250)]
    + [R("快線跌破 0＋120 日", ind="fast0", hold=120)]
    + [R("慢線兩日轉跌＋120 日", ind="slowdown", hold=120)]
    + [R("潮退訊號＋120 日", ind="tide", hold=120)]
    + [R(f"收盤跌破 MA{m}＋{h} 日", ind=f"ma{m}", hold=h) for m in (10, 20, 60) for h in (120, 250)]
    + [R("跌破 MA20（持有滿 5 日後）＋250 日", ind="ma20", hold=250, min_hold=5)]
    + [R("跌破 MA20＋停損 10%＋250 日", ind="ma20", stop=0.10, hold=250)]
    + [R("紅色交叉＋移動停損 20%＋250 日", ind="red", trail=0.20, hold=250)]
    # 指標出場太早觸發 → 持有滿 20 日後才啟用
    + [R("紅色交叉（滿 20 日後）＋250 日", ind="red", hold=250, min_hold=20)]
    + [R("潮退（滿 20 日後）＋250 日", ind="tide", hold=250, min_hold=20)]
    + [R("跌破 MA60（滿 20 日後）＋250 日", ind="ma60", hold=250, min_hold=20)]
    + [R("跌破 MA60（滿 20 日後）＋移動停損 25%＋250 日", ind="ma60", trail=0.25, hold=250, min_hold=20)]
)
KIND_CODE = {v.split()[0]: k for k, v in W.KIND_LABEL.items()}   # "A" → "twin_reversal"


# ════════════════════════════════════════════════════════════════════
# 每檔股票：指標、進場點、各規則的交易與每日報酬
# ════════════════════════════════════════════════════════════════════
def prep_chunk(args):
    """一批股票 → 各規則的交易清單＋依全域交易日累加的日報酬／部位數；母體日報酬加總。
    在子行程裡先累加好再回傳，避免把每檔每天的資料搬回主行程。"""
    jobs, cal, rule_version, start, end, minvol, jump_pct, kinds = args
    D = len(cal)
    acc = [([], [0.0] * D, [0] * D) for _ in RULES]
    uni_sum, uni_cnt = [0.0] * D, [0] * D
    for code, rows in jobs:
        prep_stock(rows, cal, rule_version, start, end, minvol, jump_pct, kinds, acc, uni_sum, uni_cnt)
    return acc, uni_sum, uni_cnt


def prep_stock(rows, cal, rule_version, start, end, minvol, jump_pct, kinds, acc, uni_sum, uni_cnt):
    eye = W.whale_eye_v3(rows, rule_version)
    if not eye:
        return
    n = len(rows)
    O = [r["open"] for r in rows]
    C = [r["close"] for r in rows]
    times = [r["time"] for r in rows]
    g = [cal[t] for t in times]          # 本檔第 k 根 → 全域交易日序號
    vols = [r["volume"] or 0 for r in rows]
    vol20 = [sum(vols[max(0, i - 19): i + 1]) / len(vols[max(0, i - 19): i + 1]) / 1000 for i in range(n)]
    jump = [False] + [abs(C[i] / C[i - 1] - 1) * 100 > jump_pct for i in range(1, n)]
    fast, slow = eye["fast"], eye["slow"]
    ma = {m: W._sma(C, m) for m in (10, 20, 60)}
    red = [False] * n
    tide = [False] * n
    bear, tide_f = eye["groups"][1], eye["groups"][5]
    for m in bear:
        red[m["idx"]] = True
    for m in tide_f:
        tide[m["idx"]] = True

    def ind_hit(kind, k):
        if kind == "red":
            return red[k]
        if kind == "tide":
            return tide[k]
        if kind == "fast0":
            return fast[k] is not None and fast[k - 1] is not None and fast[k] < 0 <= fast[k - 1]
        if kind == "slowdown":
            return slow[k] is not None and slow[k - 2] is not None and slow[k] - slow[k - 2] < 0
        if kind.startswith("ma"):
            m = ma[int(kind[2:])][k]
            return m is not None and C[k] < m
        return False

    entries = []
    for m in eye["launch"]:
        i = m["idx"]
        if times[i] < start or times[i] > end or i + 1 >= n:
            continue
        if minvol and vol20[i] < minvol:
            continue
        if kinds and m["kind"] not in kinds:
            continue
        entries.append((i, m["kind"]))

    cost = CFG["COST_ROUNDTRIP_PCT"] / 100
    for j, rule in enumerate(RULES):
        trades, daily, cnt = acc[j]           # daily／cnt：全域交易日 → 當日報酬加總／部位數
        for si, kind in entries:
            ei = si + 1
            px = O[ei]
            peak = px
            xi = xpx = why = None
            last = min(ei + rule["hold"], n - 1) if rule["hold"] else n - 1
            for k in range(ei, last + 1):
                c = C[k]
                peak = max(peak, c)
                if k - ei >= (rule["hold"] or 10 ** 9):
                    xi, xpx, why = k, c, "到期"; break
                trig = None
                if rule["stop"] is not None and c <= px * (1 - rule["stop"]):
                    trig = "停損"
                elif rule["trail"] is not None and c <= peak * (1 - rule["trail"]):
                    trig = "移動停損"
                elif rule["tp"] is not None and c >= px * (1 + rule["tp"]):
                    trig = "停利"
                elif rule["ind"] and k - ei >= rule["min_hold"] and ind_hit(rule["ind"], k):
                    trig = "指標"
                if trig and k + 1 < n:
                    xi, xpx, why = k + 1, O[k + 1], trig; break
            end_k = xi if xi is not None else n - 1
            if any(jump[k] for k in range(ei, end_k + 1)):
                continue
            # 每日報酬（進場日：開→收；中間：收→收；條件出場日：前收→開；到期日：收→收）
            for k in range(ei, end_k + 1):
                if k == ei:
                    r = C[k] / px - 1 - cost
                    if xi == ei:          # 不會發生（條件出場至少隔天），保險
                        r = xpx / px - 1 - cost
                elif xi is not None and k == xi:
                    r = xpx / C[k - 1] - 1
                else:
                    r = C[k] / C[k - 1] - 1
                daily[g[k]] += r
                cnt[g[k]] += 1
            if xi is None:
                trades.append((times[ei], None, C[n - 1] / px * 100 - 100 - cost * 100, n - 1 - ei, kind, "未平倉"))
            else:
                trades.append((times[ei], times[xi], xpx / px * 100 - 100 - cost * 100, xi - ei, kind, why))

    # 母體：每天每檔的日報酬（排除跳價；有 minvol 時只算前一天均量達標的）
    for k in range(1, n):
        if jump[k] or (minvol and vol20[k - 1] < minvol):
            continue
        uni_sum[g[k]] += C[k] / C[k - 1] - 1
        uni_cnt[g[k]] += 1


# ════════════════════════════════════════════════════════════════════
# 投組績效
# ════════════════════════════════════════════════════════════════════
def perf(days, ret):
    """days: 排序後的交易日；ret: {day: 日報酬}。回傳 (年化, 年化波動, Sharpe, 最大回撤, 總報酬)"""
    eq, peak, mdd = 1.0, 1.0, 0.0
    rs = []
    for d in days:
        r = ret.get(d, 0.0)
        rs.append(r)
        eq *= 1 + r
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    yrs = len(days) / 245
    cagr = eq ** (1 / yrs) - 1 if yrs > 0 and eq > 0 else float("nan")
    vol = statistics.pstdev(rs) * math.sqrt(245) if len(rs) > 1 else float("nan")
    sharpe = statistics.mean(rs) * 245 / vol if vol and vol > 0 else float("nan")
    return cagr * 100, vol * 100, sharpe, mdd * 100, (eq - 1) * 100


def main():
    ap = argparse.ArgumentParser(description="紫點出場規則研究")
    ap.add_argument("--start", default="2021-11-01")
    ap.add_argument("--end")
    ap.add_argument("--split", default="2024-05-01", help="樣本內／樣本外切點（依日期）")
    ap.add_argument("--rule", default=CFG["RULE_VERSION"], choices=["2026-07", "2026-08"])
    ap.add_argument("--minvol", type=int, default=0, help="只取入選日 20 日均量 ≥ N 張的紫點；母體同門檻")
    ap.add_argument("--kinds", help="只取這些場景的紫點，例 F,I（A～I）")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()

    start, end = a.start, a.end or date.today().isoformat()
    fetch_start = (date.fromisoformat(start) - timedelta(days=800)).isoformat()
    fetch_end = min((date.fromisoformat(end) + timedelta(days=int(CFG["HOLD_DAYS"] * 1.6) + 5)).isoformat(), date.today().isoformat())
    uni_list = [(c, [tk], name) for c, tk, name in W.fetch_universe(CFG)]
    print(f"讀快取 {len(uni_list)} 檔 {fetch_start} ~ {fetch_end}…", file=sys.stderr)
    data = W.load_many(uni_list, fetch_start, fetch_end, CFG)
    bench = {r["time"]: r["close"] for r in (W.fetch_daily(CFG["BENCHMARK"], fetch_start, fetch_end, CFG) or [])}

    cal_days = sorted({r["time"] for d in data.values() for r in d["rows"]})
    cal = {t: i for i, t in enumerate(cal_days)}
    D = len(cal_days)
    items = list(data.items())
    nchunk = a.workers * 4
    chunks = [[(c, d["rows"]) for c, d in items[k::nchunk]] for k in range(nchunk)]
    agg = [([], [0.0] * D, [0] * D) for _ in RULES]
    us, uc = [0.0] * D, [0] * D
    print(f"計算 {len(items)} 檔 × {len(RULES)} 種出場（{nchunk} 批）…", file=sys.stderr)
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        kinds = {KIND_CODE[k.strip().upper()] for k in a.kinds.split(",")} if a.kinds else None
        args = [(ch, cal, a.rule, start, end, a.minvol, CFG["JUMP_PCT"], kinds) for ch in chunks]
        for n_done, (acc, s_, c_) in enumerate(ex.map(prep_chunk, args), 1):
            print(f"  批 {n_done}/{nchunk}", file=sys.stderr)
            for j, (tr, dly, cnt) in enumerate(acc):
                agg[j][0].extend(tr)
                A, B = agg[j][1], agg[j][2]
                for i in range(D):
                    if cnt[i]:
                        A[i] += dly[i]; B[i] += cnt[i]
            for i in range(D):
                us[i] += s_[i]; uc[i] += c_[i]
    uni_sum = {cal_days[i]: us[i] for i in range(D) if uc[i]}
    uni_cnt = {cal_days[i]: uc[i] for i in range(D) if uc[i]}
    for j in range(len(RULES)):
        tr, A, B = agg[j]
        agg[j] = (tr, {cal_days[i]: A[i] for i in range(D) if B[i]}, {cal_days[i]: B[i] for i in range(D) if B[i]})

    days = sorted(d for d in uni_cnt if start <= d <= end)
    uni_ret = {d: uni_sum[d] / uni_cnt[d] for d in days}
    bdays = sorted(bench)
    twii_ret = {}
    for k in range(1, len(bdays)):
        twii_ret[bdays[k]] = bench[bdays[k]] / bench[bdays[k - 1]] - 1
    # 母體指數水位（交易層級的對照用）
    lvl, L = {}, 1.0
    for d in sorted(uni_cnt):
        L *= 1 + uni_sum[d] / uni_cnt[d]
        lvl[d] = L
    ldays = sorted(lvl)

    def lvl_before(d):   # 進場日前一個交易日的母體水位（＝入選日收盤）
        import bisect
        k = bisect.bisect_left(ldays, d) - 1
        return lvl[ldays[k]] if k >= 0 else None

    periods = [("全期", days), ("樣本內", [d for d in days if d < a.split]), ("樣本外", [d for d in days if d >= a.split])]
    tag = f"{a.rule}_v{a.minvol}_{start}" + (f"_k{a.kinds.replace(',', '')}" if a.kinds else "")
    lines = []
    P = lines.append
    P(f"紫點出場規則研究　規則 {a.rule}　{start} ~ {end}　入選均量 ≥{a.minvol} 張　場景 {a.kinds or '全部'}　樣本內／外切點 {a.split}")
    P(f"每顆紫點獨立進場（隔天開盤），條件出場＝收盤觸發隔天開盤賣，成本 {CFG['COST_ROUNDTRIP_PCT']}%，排除跳價交易")
    P("")
    P("【對照】" + "　".join(
        f"{nm}：母體等權 年化 {perf(ds, uni_ret)[0]:+.1f}% 回撤 {perf(ds, uni_ret)[3]:.1f}% Sharpe {perf(ds, uni_ret)[2]:.2f} ／ 加權 年化 {perf(ds, twii_ret)[0]:+.1f}% 回撤 {perf(ds, twii_ret)[3]:.1f}%"
        for nm, ds in periods))
    P("")
    hdr = ("規則", "筆數", "勝率", "平均", "中位", "均持有日", "vs母體平均", "vs母體中位",
           "全期年化", "Sharpe", "回撤", "超額年化", "內:超額年化", "內:Sharpe", "外:超額年化", "外:Sharpe")
    rows_out = []
    for j, rule in enumerate(RULES):
        trades, dsum, dcnt = agg[j]
        port = {d: dsum[d] / dcnt[d] for d in dcnt}
        closed = [t for t in trades if t[1] is not None]
        if not closed:
            continue
        rets = [t[2] for t in closed]
        exs = []
        for t in closed:
            l0, l1 = lvl_before(t[0]), lvl.get(t[1])
            if l0 and l1:
                exs.append(t[2] - ((l1 / l0 - 1) * 100 - CFG["COST_ROUNDTRIP_PCT"]))
        res = {}
        for nm, ds in periods:
            pc = perf(ds, port)
            uc = perf(ds, uni_ret)
            res[nm] = (pc, pc[0] - uc[0])
        rows_out.append((rule["name"], len(closed), sum(1 for x in rets if x > 0) / len(rets) * 100,
                         statistics.mean(rets), statistics.median(rets), statistics.mean(t[3] for t in closed),
                         statistics.mean(exs) if exs else float("nan"), statistics.median(exs) if exs else float("nan"),
                         res["全期"][0][0], res["全期"][0][2], res["全期"][0][3], res["全期"][1],
                         res["樣本內"][1], res["樣本內"][0][2], res["樣本外"][1], res["樣本外"][0][2]))

    def fmt(r):
        return (f"{r[0]:<26}{r[1]:>7}{r[2]:>7.1f}%{r[3]:>+8.2f}%{r[4]:>+8.2f}%{r[5]:>7.1f}"
                f"{r[6]:>+9.2f}{r[7]:>+9.2f}{r[8]:>+9.1f}%{r[9]:>7.2f}{r[10]:>8.1f}%{r[11]:>+9.1f}"
                f"{r[12]:>+10.1f}{r[13]:>8.2f}{r[14]:>+10.1f}{r[15]:>8.2f}")

    P("　".join(hdr))
    for r in rows_out:
        P(fmt(r))
    P("")
    P("（年化／回撤／Sharpe＝等權投組；超額年化＝投組年化 − 同期母體等權年化（pp）；vs母體＝每筆交易減同期母體指數報酬（pp））")
    best_in = sorted(rows_out, key=lambda r: -r[13])[:5]
    P("")
    P("【樣本內 Sharpe 前 5 名 → 樣本外表現】")
    for r in best_in:
        P(f"  {r[0]:<26} 內 Sharpe {r[13]:.2f}、超額年化 {r[12]:+.1f}pp　→　外 Sharpe {r[15]:.2f}、超額年化 {r[14]:+.1f}pp")
    best_ex = sorted(rows_out, key=lambda r: -r[12])[:5]
    P("【樣本內 超額年化 前 5 名 → 樣本外表現】")
    for r in best_ex:
        P(f"  {r[0]:<26} 內 {r[12]:+.1f}pp　→　外 {r[14]:+.1f}pp")

    # 幾個代表規則的逐年投組超額（看是不是只靠某一年）
    pick = ["持有 60 日", "持有 120 日", "持有 250 日", "移動停損 20%＋250 日", "跌破 MA60（滿 20 日後）＋250 日"]
    years = sorted({d[:4] for d in days})
    P("")
    P("【逐年：投組年化報酬 − 母體等權（pp）】" + "".join(f"{y:>9}" for y in years))
    P(f"  {'母體等權年化':<26}" + "".join(f"{perf([d for d in days if d[:4] == y], uni_ret)[0]:>+8.1f}%" for y in years))
    for j, rule in enumerate(RULES):
        if rule["name"] not in pick:
            continue
        _, dsum, dcnt = agg[j]
        port = {d: dsum[d] / dcnt[d] for d in dcnt}
        P(f"  {rule['name']:<26}" + "".join(
            f"{perf([d for d in days if d[:4] == y], port)[0] - perf([d for d in days if d[:4] == y], uni_ret)[0]:>+9.1f}" for y in years))

    # 基準規則（持有 60 日）依年份、依場景
    j60 = next(j for j, r in enumerate(RULES) if r["name"] == "持有 60 日")
    closed60 = [t for t in agg[j60][0] if t[1] is not None]
    P("")
    P("【持有 60 日：依進場年份】（vs母體＝每筆減同期母體等權指數）")
    by = defaultdict(list)
    for t in closed60:
        l0, l1 = lvl_before(t[0]), lvl.get(t[1])
        ex_ = t[2] - ((l1 / l0 - 1) * 100 - CFG["COST_ROUNDTRIP_PCT"]) if (l0 and l1) else None
        by[t[0][:4]].append((t[2], ex_))
    for y in sorted(by):
        v = by[y]
        r_ = [x for x, _ in v]
        e_ = [e for _, e in v if e is not None]
        P(f"  {y}　{len(v):>6} 筆　勝率 {sum(1 for x in r_ if x > 0) / len(r_) * 100:5.1f}%　平均 {statistics.mean(r_):+6.2f}%　中位 {statistics.median(r_):+6.2f}%　"
          f"vs母體 平均 {statistics.mean(e_):+6.2f}pp 中位 {statistics.median(e_):+6.2f}pp　贏母體 {sum(1 for e in e_ if e > 0) / len(e_) * 100:4.1f}%")
    P("【持有 60 日：依場景】")
    bk = defaultdict(list)
    for t in closed60:
        l0, l1 = lvl_before(t[0]), lvl.get(t[1])
        if l0 and l1:
            bk[W.KIND_LABEL[t[4]]].append((t[2], t[2] - ((l1 / l0 - 1) * 100 - CFG["COST_ROUNDTRIP_PCT"]), t[0] < a.split))
    for k in sorted(bk):
        v = bk[k]
        ins = [e for _, e, s in v if s]
        outs = [e for _, e, s in v if not s]
        P(f"  {k:<10}{len(v):>6} 筆　勝率 {sum(1 for x, _, _ in v if x > 0) / len(v) * 100:5.1f}%　vs母體 平均 {statistics.mean(e for _, e, _ in v):+6.2f}pp　"
          f"樣本內 {statistics.mean(ins) if ins else float('nan'):+6.2f}pp　樣本外 {statistics.mean(outs) if outs else float('nan'):+6.2f}pp")

    text = "\n".join(lines)
    print(text)
    os.makedirs("results", exist_ok=True)
    fn = os.path.join("results", f"exit_study_{tag}.txt")
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print(f"\n已存 {fn}", file=sys.stderr)


if __name__ == "__main__":
    main()
