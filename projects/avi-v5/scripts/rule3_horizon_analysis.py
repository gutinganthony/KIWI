#!/usr/bin/env python3
"""
rule3_horizon_analysis.py — 規則 3B 在 5 年／10 年尺度能不能贏買進持有？為什麼回撤小、Sharpe 高，年化卻輸？

一、期間：最近 5 年、最近 10 年、全期，以及「所有滾動 5 年／10 年區間」（每月起算一次）的勝率。
二、拆解規則 3B 輸掉的年化：
   ① 現金拖累：場外期間 S&P 的報酬 vs 國庫券利息
   ② 進出價差：每次「出場價 vs 回場價」的累積（正＝買回更便宜）
   ③ 錯過的大漲日／避開的大跌日
   ④ 波動拖累：幾何年化 ≈ 算術年化 − σ²/2
   ⑤ 交易成本
三、「更有效使用」的變體：更快回場、只減一半、平常 1.25×／1.5× 槓桿（借款成本＝國庫券＋0.5%）出事全出。
與 risk_board_backtest.py 同一套資料與假設（收盤訊號、隔日換倉、現金＝^IRX、每次進出 0.1%）。

用法：python scripts/rule3_horizon_analysis.py [--cache DIR]
輸出：data/backtest/rule3_horizon_analysis.json
"""
import argparse, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from risk_board_backtest import build_board, hysteresis, COST  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "backtest", "rule3_horizon_analysis.json")
START = "1997-01-02"
SPREAD = 0.005 / 252          # 槓桿借款利差


def run(w, ret, cash, lev_cost=True):
    """w：每日目標曝險（可 >1）。回傳每日報酬序列。收盤訊號 → 次日部位。"""
    w = pd.Series(w, index=ret.index).shift(1).fillna(1.0)
    borrow = np.clip(w - 1, 0, None) * (cash + (SPREAD if lev_cost else 0))
    r = w * ret + np.clip(1 - w, 0, None) * cash - borrow - w.diff().abs().fillna(0) * COST
    return r, w


def stats(r):
    eq = (1 + r).cumprod()
    yrs = (r.index[-1] - r.index[0]).days / 365.25
    return {"cagr": round((eq.iloc[-1] ** (1 / yrs) - 1) * 100, 2),
            "mdd": round((eq / eq.cummax() - 1).min() * 100, 1),
            "vol": round(r.std() * np.sqrt(252) * 100, 1)}


def sharpe(r, cash):
    ex = r - cash
    return round(ex.mean() / ex.std() * np.sqrt(252), 2) if ex.std() else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cache"); a = ap.parse_args()
    D, st, spy, ser = build_board(a.cache, live_cri=False)
    D = D[D.index >= START]
    idx = D.index
    f = lambda s: s.reindex(idx.union(s.index)).ffill().reindex(idx)
    ret = spy.pct_change().reindex(idx).fillna(0)
    cash = (f(ser["irx"]) / 100 / 252).fillna(0)
    bd, mad = np.nan_to_num(D["board"].values), D["ma"].values
    calm30 = pd.Series(bd < 30).rolling(10).sum().values == 10
    r3 = hysteresis((bd >= 35) & (mad < 0), calm30 & (mad > 0))

    S = {
        "買進持有": np.ones(len(idx)),
        "只看 200 日線": hysteresis(mad < 0, mad > 0),
        "規則 3B（現行）": r3,
        "3B＋快速回場（站回 200 日線就回）": hysteresis((bd >= 35) & (mad < 0), mad > 0),
        "3B 只減一半（出場時留 50%）": np.where(r3 > 0.5, 1.0, 0.5),
        "3B＋平常 1.25 倍": np.where(r3 > 0.5, 1.25, 0.0),
        "3B＋平常 1.5 倍": np.where(r3 > 0.5, 1.5, 0.0),
        "買進持有 1.25 倍": np.full(len(idx), 1.25),
    }
    # 規則 3 完整版套在槓桿組合上：平常 1.5 倍；A 段（CRI≥50，直到連續 10 日 <35）降回 1 倍；B 段全出
    cri = np.nan_to_num(D["cri"].values)
    a_def = hysteresis(cri >= 50, pd.Series(cri < 35).rolling(10).sum().values == 10) < 0.5
    S["規則 3 A＋B（平常 1.5 倍）"] = np.where(r3 < 0.5, 0.0, np.where(a_def, 1.0, 1.5))
    R = {k: run(w, ret, cash) for k, w in S.items()}

    end = idx[-1]
    periods = {"最近 5 年": end - pd.DateOffset(years=5), "最近 10 年": end - pd.DateOffset(years=10),
               "最近 15 年": end - pd.DateOffset(years=15), "全期 1997–2026": idx[0]}
    table = {}
    for k, (r, w) in R.items():
        table[k] = {}
        for pn, a0 in periods.items():
            m = r.index >= a0
            s = stats(r[m]); s["sharpe"] = sharpe(r[m], cash[m])
            s["out_pct"] = round(float((w[m] < 0.999).mean()) * 100, 0)
            s["switches"] = int((w[m].diff().abs() > 0.25).sum())
            table[k][pn] = s

    # 滾動區間勝率（每月第一個交易日起算）
    starts = pd.Series(idx, index=idx).groupby([idx.year, idx.month]).first().values
    roll = {}
    eqs = {k: (1 + r).cumprod() for k, (r, _) in R.items()}
    for yrs in (5, 10):
        res = {}
        for k in S:
            if k == "買進持有":
                continue
            wins, diffs, mdd_better = 0, [], 0
            n = 0
            for s0 in starts:
                s0 = pd.Timestamp(s0); e0 = s0 + pd.DateOffset(years=yrs)
                if e0 > end:
                    break
                i0 = idx.searchsorted(s0); i1 = idx.searchsorted(e0) - 1
                def cg(eq):
                    return (eq.iloc[i1] / eq.iloc[i0]) ** (1 / yrs) - 1
                def mdd(eq):
                    seg = eq.iloc[i0:i1 + 1]; return (seg / seg.cummax() - 1).min()
                d = cg(eqs[k]) - cg(eqs["買進持有"])
                diffs.append(d); wins += d > 0; n += 1
                mdd_better += mdd(eqs[k]) > mdd(eqs["買進持有"])
            res[k] = {"windows": n, "beat_bh_pct": round(wins / n * 100, 0),
                      "median_diff_pp": round(float(np.median(diffs)) * 100, 2),
                      "worst_diff_pp": round(float(np.min(diffs)) * 100, 2),
                      "best_diff_pp": round(float(np.max(diffs)) * 100, 2),
                      "smaller_mdd_pct": round(mdd_better / n * 100, 0)}
        roll[f"{yrs} 年"] = res

    # 拆解：規則 3B 為什麼年化輸
    def decompose(a0):
        m = idx >= a0
        rr, ww = R["規則 3B（現行）"]; rb, _ = R["買進持有"]
        rr, ww, rb, re, cs = rr[m], ww[m], rb[m], ret[m], cash[m]
        out = ww < 0.5
        yrs = (re.index[-1] - re.index[0]).days / 365.25
        spx_out = float((1 + re[out]).prod()); cash_out = float((1 + cs[out]).prod())
        # 每筆進出
        w_ = pd.Series(r3, index=idx)[m]
        ch = w_.diff().fillna(0)
        px = D["spx"][m]
        exits = list(px.index[ch < 0]); entries = list(px.index[ch > 0])
        trades = []
        for o in exits:
            nxt = [e for e in entries if e > o]
            back = nxt[0] if nxt else px.index[-1]
            trades.append((o, back, px[back] / px[o] - 1))
        gain = [t for t in trades if t[2] < 0]; loss = [t for t in trades if t[2] >= 0]
        # 大漲／大跌日
        rk = re.sort_values()
        top20 = rk.index[-20:]; bot20 = rk.index[:20]
        geo_bh = stats(rb)["cagr"]; geo_r3 = stats(rr)["cagr"]
        ari_bh = rb.mean() * 252 * 100; ari_r3 = rr.mean() * 252 * 100
        return {
            "years": round(yrs, 1), "out_pct": round(float(out.mean()) * 100, 1),
            "cagr_bh": geo_bh, "cagr_r3": geo_r3, "gap_pp": round(geo_r3 - geo_bh, 2),
            "spx_return_while_out_ann": round((spx_out ** (252 / max(1, out.sum())) - 1) * 100, 1) if out.sum() else None,
            "cash_return_while_out_ann": round((cash_out ** (252 / max(1, out.sum())) - 1) * 100, 1) if out.sum() else None,
            "missed_vs_cash_total_pct": round((spx_out / cash_out - 1) * 100, 1),
            "trades": len(trades), "trades_bought_back_cheaper": len(gain), "trades_bought_back_higher": len(loss),
            "avg_cheaper_pct": round(float(np.mean([t[2] for t in gain])) * 100, 1) if gain else None,
            "avg_higher_pct": round(float(np.mean([t[2] for t in loss])) * 100, 1) if loss else None,
            "net_timing_pct": round((float(np.prod([1 / (1 + t[2]) for t in trades])) - 1) * 100, 1) if trades else 0,
            "top20_up_days_missed": int(out.reindex(top20).sum()), "worst20_days_avoided": int(out.reindex(bot20).sum()),
            "arith_bh": round(ari_bh, 2), "arith_r3": round(ari_r3, 2),
            "vol_drag_bh": round((rb.std() * np.sqrt(252)) ** 2 / 2 * 100, 2),
            "vol_drag_r3": round((rr.std() * np.sqrt(252)) ** 2 / 2 * 100, 2),
            "cost_pp_per_year": round(len(trades) * 2 * COST / yrs * 100, 2),
            "trade_list": [(t[0].date().isoformat(), t[1].date().isoformat(), round(t[2] * 100, 1)) for t in trades],
        }
    dec = {pn: decompose(a0) for pn, a0 in periods.items()}

    out = {"generated": pd.Timestamp.today().date().isoformat(), "period": [START, end.date().isoformat()],
           "table": table, "rolling": roll, "decompose_rule3b": dec}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)

    for pn in periods:
        print(f"\n== {pn} ==")
        for k in S:
            s = table[k][pn]
            print(f"  {k:30s} 年化 {s['cagr']:6.2f}%  回撤 {s['mdd']:6.1f}%  波動 {s['vol']:5.1f}%  Sharpe {s['sharpe']}  場外 {s['out_pct']:.0f}%  進出 {s['switches']}")
    for yk, res in roll.items():
        print(f"\n== 滾動 {yk} 區間（每月起算） ==")
        for k, v in res.items():
            print(f"  {k:30s} 贏的比例 {v['beat_bh_pct']:.0f}%（{v['windows']} 個）  中位差 {v['median_diff_pp']:+.2f}pp  最差 {v['worst_diff_pp']:+.2f}  最好 {v['best_diff_pp']:+.2f}  回撤較小 {v['smaller_mdd_pct']:.0f}%")
    for pn, d in dec.items():
        print(f"\n== 拆解 {pn} ==")
        print({k: v for k, v in d.items() if k != "trade_list"})


if __name__ == "__main__":
    main()
