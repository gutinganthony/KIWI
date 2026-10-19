#!/usr/bin/env python3
"""
leverage_exit_optimizer.py — 平常槓桿幾倍、什麼時候降槓桿、什麼時候全出，哪個組合最好？

網格：平常槓桿 L ∈ {1, 1.25, 1.5, 1.75, 1.8, 2} × 降槓桿方式（降到 1 倍；B 段觸發一律全出）：
  不降（只留 B 段）／A 原版（CRI≥50）／A 改版（CRI≥50 且對照台 ≥35）／對照台 ≥35／
  跌破 200 日線／波動度（20 日實現波動 > 長期中位數時按比例縮）
評分：全期、最近 10/5 年、滾動 10 年勝率、訓練期 1997–2011 選、測試期 2012–2026 驗，
以及借款利差 0.5% vs 1.5% 的敏感度、1987 型單日 −20.5% 的壓力測試。
與 rule3_horizon_analysis.py 同一套假設（收盤訊號、隔日換倉、每日重設槓桿、現金＝^IRX、每次換倉 0.1%）。

用法：python scripts/leverage_exit_optimizer.py [--cache DIR]
輸出：data/backtest/leverage_exit_optimizer.json
"""
import argparse, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from risk_board_backtest import build_board, hysteresis, COST  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "backtest", "leverage_exit_optimizer.json")
START = "1997-01-02"
SPLIT = "2012-01-01"
LEVELS = [1.0, 1.25, 1.5, 1.75, 1.8, 2.0]
CRASH_1987 = -0.205


def run(w, ret, cash, spread):
    w = pd.Series(w, index=ret.index).shift(1).fillna(1.0)
    borrow = np.clip(w - 1, 0, None) * (cash + spread / 252)
    return w * ret + np.clip(1 - w, 0, None) * cash - borrow - w.diff().abs().fillna(0) * COST, w


def stats(r, cash):
    eq = (1 + r).cumprod()
    yrs = (r.index[-1] - r.index[0]).days / 365.25
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    mdd = (eq / eq.cummax() - 1).min()
    ex = r - cash
    return {"cagr": round(cagr * 100, 2), "mdd": round(mdd * 100, 1),
            "vol": round(r.std() * np.sqrt(252) * 100, 1),
            "sharpe": round(ex.mean() / ex.std() * np.sqrt(252), 2),
            "calmar": round(cagr / -mdd, 3) if mdd < 0 else None,
            "worst_year": round(float(((1 + r).rolling(252).apply(np.prod, raw=True) - 1).min()) * 100, 1)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cache"); a = ap.parse_args()
    D, st, spy, ser = build_board(a.cache, live_cri=False)
    D = D[D.index >= START]
    idx = D.index
    f = lambda s: s.reindex(idx.union(s.index)).ffill().reindex(idx)
    ret = spy.pct_change().reindex(idx).fillna(0)
    cash = (f(ser["irx"]) / 100 / 252).fillna(0)
    bd, mad = np.nan_to_num(D["board"].values), D["ma"].values
    cri = np.nan_to_num(D["cri"].values)
    calm30 = pd.Series(bd < 30).rolling(10).sum().values == 10
    cri_calm = pd.Series(cri < 35).rolling(10).sum().values == 10
    out_b = hysteresis((bd >= 35) & (mad < 0), calm30 & (mad > 0)) < 0.5      # B 段：全出

    # 降槓桿狀態（True＝降到 1 倍）
    vol20 = ret.rolling(20).std() * np.sqrt(252)
    vol_med = float(vol20[idx < SPLIT].median())                              # 只用訓練期定中位數
    DELEV = {
        "不降（只留 B 段）": np.zeros(len(idx), bool),
        "A 原版：CRI≥50": hysteresis(cri >= 50, cri_calm) < 0.5,
        "A 改版：CRI≥50 且總分≥35": hysteresis((cri >= 50) & (bd >= 35), cri_calm | calm30) < 0.5,
        "總分≥35": hysteresis(bd >= 35, calm30) < 0.5,
        "跌破 200 日線": hysteresis(mad < 0, mad > 0) < 0.5,
        "波動度縮放": None,
        "200 日線＋波動度": None,
    }

    def weights(L, mode):
        if mode in ("波動度縮放", "200 日線＋波動度"):
            scale = np.clip(vol_med / vol20.values, 1 / L, 1.0)                # 最多縮到 1 倍
            w = np.nan_to_num(L * scale, nan=L)
            if mode == "200 日線＋波動度":
                w = np.where(DELEV["跌破 200 日線"], min(L, 1.0), w)
        else:
            w = np.where(DELEV[mode], min(L, 1.0), L)
        return np.where(out_b, 0.0, w)

    end = idx[-1]
    periods = {"全期": idx[0], "最近 10 年": end - pd.DateOffset(years=10), "最近 5 年": end - pd.DateOffset(years=5)}
    tr, te = idx < SPLIT, idx >= SPLIT
    bh, _ = run(np.ones(len(idx)), ret, cash, 0.005)
    bh_eq = (1 + bh).cumprod()
    starts = pd.Series(idx, index=idx).groupby([idx.year, idx.month]).first().values
    wins = []
    for s0 in starts:
        s0 = pd.Timestamp(s0); e0 = s0 + pd.DateOffset(years=10)
        if e0 > end:
            break
        wins.append((idx.searchsorted(s0), idx.searchsorted(e0) - 1))

    def roll10(eq):
        d = [(eq.iloc[j] / eq.iloc[i]) ** 0.1 - (bh_eq.iloc[j] / bh_eq.iloc[i]) ** 0.1 for i, j in wins]
        return round(float(np.mean(np.array(d) > 0)) * 100, 0), round(float(np.median(d)) * 100, 2)

    rows = []
    for L in LEVELS:
        for mode in DELEV:
            if L == 1.0 and mode != "不降（只留 B 段）":
                continue
            w = weights(L, mode)
            row = {"L": L, "mode": mode}
            for sp in (0.005, 0.015):
                r, ww = run(w, ret, cash, sp)
                tag = "" if sp == 0.005 else "_hicost"
                row["full" + tag] = stats(r, cash)
                if sp == 0.005:
                    for pn, a0 in periods.items():
                        m = r.index >= a0
                        row[pn] = stats(r[m], cash[m])
                    row["train"] = stats(r[tr], cash[tr]); row["test"] = stats(r[te], cash[te])
                    row["roll10_win"], row["roll10_median_pp"] = roll10((1 + r).cumprod())
                    row["switches"] = int((ww.diff().abs() > 0.2).sum())
                    row["avg_lev"] = round(float(ww.mean()), 2)
                    row["max_lev_share"] = round(float((ww >= L - 1e-9).mean()) * 100, 0)
                    row["stress_1987"] = round(L * CRASH_1987 * 100, 1)   # 滿槓桿時遇到 1987 型單日
                    eq = (1 + r).cumprod(); dd = eq / eq.cummax() - 1; t = dd.idxmin()
                    row["mdd_peak"], row["mdd_trough"] = eq[:t].idxmax().date().isoformat(), t.date().isoformat()
            rows.append(row)

    bh_row = {"L": 1.0, "mode": "買進持有", "full": stats(bh, cash), "train": stats(bh[tr], cash[tr]),
              "test": stats(bh[te], cash[te])}
    for pn, a0 in periods.items():
        m = bh.index >= a0; bh_row[pn] = stats(bh[m], cash[m])

    # 全期效率前緣：沒有任何其他組合「年化更高且回撤更小」
    for r in rows:
        r["pareto_full"] = not any(o["full"]["cagr"] > r["full"]["cagr"] and o["full"]["mdd"] > r["full"]["mdd"] for o in rows)
        r["pareto_test"] = not any(o["test"]["cagr"] > r["test"]["cagr"] and o["test"]["mdd"] > r["test"]["mdd"] for o in rows)

    # 選擇：訓練期在「回撤不超過買進持有」的前提下 CAGR 最高；再看它在測試期的表現
    def pick(key, budget):
        ok = [r for r in rows if r[key]["mdd"] >= budget]
        return max(ok, key=lambda r: r[key]["cagr"]) if ok else None
    picks = {}
    for b in (-25.0, -35.0, -45.0, bh_row["train"]["mdd"]):
        p = pick("train", b)
        if p:
            picks[f"訓練期回撤上限 {b:.0f}%"] = {"L": p["L"], "mode": p["mode"], "train": p["train"], "test": p["test"]}
    best_calmar_train = max(rows, key=lambda r: r["train"]["calmar"])
    picks["訓練期 Calmar 最高"] = {"L": best_calmar_train["L"], "mode": best_calmar_train["mode"],
                                   "train": best_calmar_train["train"], "test": best_calmar_train["test"]}

    # Kelly：以 B 段管控後 1 倍序列的超額報酬與波動推算最適槓桿
    r1, w1 = run(weights(1.0, "不降（只留 B 段）"), ret, cash, 0.005)
    inm = w1 > 0.5
    ex = (ret - cash)[inm]
    kelly = {"in_market_excess_ann": round(ex.mean() * 252 * 100, 2), "in_market_vol": round(ex.std() * np.sqrt(252) * 100, 1),
             "kelly_full": round(ex.mean() / ex.var(), 2)}
    exb = ret - cash
    kelly["bh_kelly_full"] = round(exb.mean() / exb.var(), 2)

    out = {"generated": pd.Timestamp.today().date().isoformat(), "period": [START, end.date().isoformat()],
           "split": SPLIT, "vol_median_train": round(vol_med * 100, 1), "buy_hold": bh_row,
           "grid": rows, "picks": picks, "kelly": kelly}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)

    print(f"買進持有 全期 {bh_row['full']}\n  訓練 {bh_row['train']}\n  測試 {bh_row['test']}")
    print(f"  10y {bh_row['最近 10 年']}  5y {bh_row['最近 5 年']}")
    hdr = "L     降槓桿方式                    全期年化 回撤  Sharpe Calmar | 10年年化 回撤 | 5年年化 回撤 | 滾10勝率 中位 | 訓練年化 回撤 | 測試年化 回撤 | 高成本年化 | 進出 平均槓桿"
    print(hdr)
    for r in rows:
        F, T10, T5, TR, TE, HC = r["full"], r["最近 10 年"], r["最近 5 年"], r["train"], r["test"], r["full_hicost"]
        print(f"{r['L']:<5} {r['mode']:28s} {F['cagr']:6.2f} {F['mdd']:6.1f} {F['sharpe']:5.2f} {F['calmar']:5.3f} | "
              f"{T10['cagr']:6.2f} {T10['mdd']:6.1f} | {T5['cagr']:6.2f} {T5['mdd']:6.1f} | {r['roll10_win']:4.0f}% {r['roll10_median_pp']:+5.2f} | "
              f"{TR['cagr']:6.2f} {TR['mdd']:6.1f} | {TE['cagr']:6.2f} {TE['mdd']:6.1f} | {HC['cagr']:6.2f} | {r['switches']:4d} {r['avg_lev']:.2f}")
    print("\n效率前緣（全期／測試期）＋最大回撤區間")
    for r in rows:
        if r["pareto_full"] or r["pareto_test"]:
            print(f"  {r['L']} {r['mode']:24s} 全期前緣={r['pareto_full']} 測試前緣={r['pareto_test']} 回撤 {r['mdd_peak']}→{r['mdd_trough']}")
    for r in rows:
        if r["mode"] in ("不降（只留 B 段）", "跌破 200 日線") :
            print(f"  MDD {r['L']} {r['mode']}: {r['full']['mdd']} {r['mdd_peak']}→{r['mdd_trough']} worst_year {r['full']['worst_year']}")
    print("\npicks:", json.dumps({k: (v["L"], v["mode"], v["train"]["cagr"], v["train"]["mdd"], v["test"]["cagr"], v["test"]["mdd"]) for k, v in picks.items()}, ensure_ascii=False))
    print("kelly:", kelly, "vol median", vol_med)


if __name__ == "__main__":
    main()
