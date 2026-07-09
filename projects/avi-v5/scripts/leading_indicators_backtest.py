#!/usr/bin/env python3
"""Short-horizon leading-indicator backtest — which signals actually predict
SPY/QQQ forward 1/5/10/20-day returns?

Motivation: user asked whether AIR-TRF implied funding spread ("AXW") leads the
market. Real AIR-TRF history is paywalled (CME DataMine), so this script backtests
every locally-available candidate leading indicator with the same statistical
discipline as dip_combo_backtest.py (declustered events, bootstrap CIs, BH-FDR
across the whole test grid, in/out-of-sample split), and ranks them. The funding-
spread proxy slot (VVIX/VIX + credit) is marked as such — proxy, not the real thing.

Data (local CSVs, see data/README.md):
  SPY/QQQ/SMH/SOXX/HYG  yahoo-style daily OHLC+AdjClose  (1993/1999/2000/2001/2007 → 2020-04)
  VIX.csv               CBOE daily                        (1990 → 2025-02 local; fresh copy 1990→2026-07 passable via --vix)
  VVIX.csv              CBOE daily                        (2006 → 2025-02)
  cri_history.csv       CRI score + sub-indicators        (1996 → 2020-04)
  tsi_history.csv       TSI score + sub-indicators        (2006 → 2020-04)

Outputs: printed ranking tables + JSON dump for the report.

Usage:
  python3 scripts/leading_indicators_backtest.py                # full run
  python3 scripts/leading_indicators_backtest.py --fast         # fewer bootstrap draws
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "backtest"

HORIZONS = [1, 5, 10, 20]
DECLUSTER_GAP = 21          # trading days between counted extreme events
EXTREME_Q = 0.10            # top/bottom decile = "extreme" signal
OOS_SPLIT = "2012-12-31"    # in-sample ≤ split < out-of-sample
SEED = 42


# ── data loading ──────────────────────────────────────────────────────────────

def load_yahoo(name):
    df = pd.read_csv(DATA / f"{name}.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    out = df[[col]].rename(columns={col: name})
    out[f"{name}_close"] = df["Close"]
    out[f"{name}_low"] = df["Low"]
    out[f"{name}_high"] = df["High"]
    return out


def load_cboe(path, value_names):
    """CBOE csvs use M/D/YYYY dates and varying headers; grab first matching col."""
    df = pd.read_csv(path)
    df.columns = [c.strip().upper() for c in df.columns]
    date_col = "DATE"
    df[date_col] = pd.to_datetime(df[date_col], format="mixed")
    df = df.set_index(date_col).sort_index()
    for v in value_names:
        if v in df.columns:
            return df[[v]].astype(float)
    raise ValueError(f"{path}: none of {value_names} in {list(df.columns)}")


def build_panel(vix_path=None):
    spy = load_yahoo("SPY")
    qqq = load_yahoo("QQQ")
    smh = load_yahoo("SMH")
    hyg = load_yahoo("HYG")

    vix = load_cboe(vix_path or (DATA / "VIX.csv"), ["VIX CLOSE", "CLOSE", "VIX"])
    vix.columns = ["VIX"]
    vvix = load_cboe(DATA / "VVIX.csv", ["VVIX"])
    vvix.columns = ["VVIX"]

    cri = pd.read_csv(DATA / "cri_history.csv", parse_dates=["date"]).set_index("date")
    tsi = pd.read_csv(DATA / "tsi_history.csv", parse_dates=["date"]).set_index("date")
    cri = cri.add_prefix("cri_")
    tsi = tsi[["score"]].rename(columns={"score": "tsi_score"})

    panel = spy.join([qqq, smh, hyg, vix, vvix, cri, tsi], how="left")
    # trading calendar = SPY days
    panel = panel[~panel["SPY"].isna()]
    return panel


# ── indicator construction (all values known at close of day t) ──────────────

def pct_rank(s, window):
    return s.rolling(window, min_periods=window // 2).rank(pct=True)


def build_indicators(p):
    ind = pd.DataFrame(index=p.index)
    spy = p["SPY"]

    # volatility complex
    ind["vix_level_pctl"] = pct_rank(p["VIX"], 252 * 3)
    ind["vix_chg_5d"] = p["VIX"].pct_change(5)
    ind["vvix_level_pctl"] = pct_rank(p["VVIX"], 252 * 3)
    ind["vvix_vix_ratio"] = p["VVIX"] / p["VIX"]
    ind["vvix_vix_ratio_pctl"] = pct_rank(ind["vvix_vix_ratio"], 252 * 3)

    # credit lead (funding-stress proxy leg 1)
    hyg_r5 = p["HYG"].pct_change(5)
    spy_r5 = spy.pct_change(5)
    ind["credit_rel_5d"] = hyg_r5 - spy_r5          # negative = credit underperforming

    # cross-asset leadership
    ind["smh_rs_20d"] = p["SMH"].pct_change(20) - spy.pct_change(20)
    ind["qqq_rs_20d"] = p["QQQ"].pct_change(20) - spy.pct_change(20)

    # trend/mean-reversion baselines
    ma200 = spy.rolling(200).mean()
    ind["spy_dist_200dma"] = spy / ma200 - 1
    ind["spy_mom_10d"] = spy.pct_change(10)
    delta = spy.diff()
    up = delta.clip(lower=0).rolling(14).mean()
    dn = (-delta.clip(upper=0)).rolling(14).mean()
    rs = up / dn.replace(0, np.nan)
    ind["spy_rsi_14"] = 100 - 100 / (1 + rs)
    hi252 = spy.rolling(252).max()
    ind["spy_drawdown"] = spy / hi252 - 1

    # engineered scores (already 0-100)
    ind["cri_score"] = p["cri_score"]
    for c in ["vix_term_structure", "vix_spike", "momentum_collapse",
              "intraday_selloff", "distribution_days"]:
        ind[f"cri_{c}"] = p[f"cri_{c}"]
    ind["tsi_score"] = p["tsi_score"]

    # funding-stress PROXY composite (not the real AIR-TRF spread):
    # rich vol-of-vol + weak credit + hot momentum = crowded leverage
    z = lambda s: (s - s.rolling(756, min_periods=378).mean()) / s.rolling(756, min_periods=378).std()
    ind["lev_stress_proxy"] = (
        z(ind["vvix_vix_ratio"]).clip(-4, 4)
        - z(ind["credit_rel_5d"]).clip(-4, 4)
    )
    return ind


# ── stats machinery ───────────────────────────────────────────────────────────

def spearman_ic(sig, fwd):
    m = sig.notna() & fwd.notna()
    if m.sum() < 100:
        return np.nan, 0
    return pd.Series(sig[m]).corr(pd.Series(fwd[m]), method="spearman"), int(m.sum())


def block_bootstrap_ic_pvalue(sig, fwd, n_boot, block, rng):
    """Two-sided p for Spearman IC via moving-block permutation of y vs x.

    Speed trick: Spearman = Pearson on ranks, so rank once, then each draw is a
    cheap np.corrcoef on permuted rank vectors (identical distribution, ~50x faster
    than calling .corr(method='spearman') per draw)."""
    m = (sig.notna() & fwd.notna()).values
    x = sig.values[m].astype(float)
    y = fwd.values[m].astype(float)
    n = len(x)
    if n < 120:
        return np.nan
    rx = pd.Series(x).rank().values
    ry = pd.Series(y).rank().values
    rx = (rx - rx.mean()) / rx.std()
    ry = (ry - ry.mean()) / ry.std()
    obs = float(np.mean(rx * ry))
    cnt = 0
    n_blocks = int(np.ceil(n / block))
    for _ in range(n_boot):
        starts = rng.integers(0, n - block, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        r = float(np.mean(rx * ry[idx]))
        if abs(r) >= abs(obs):
            cnt += 1
    return (cnt + 1) / (n_boot + 1)


def decluster(dates, gap=DECLUSTER_GAP):
    kept = []
    last = None
    for d in dates:
        if last is None or (d - last).days > gap * 1.6:  # calendar approx of trading gap
            kept.append(d)
            last = d
    return kept


def event_study(sig, fwd, side, q, rng, n_boot, block):
    """Extreme-decile declustered events: mean fwd return vs bootstrap null."""
    m = sig.notna() & fwd.notna()
    s, f = sig[m], fwd[m]
    thr = s.quantile(1 - q) if side == "high" else s.quantile(q)
    ev = s.index[s >= thr] if side == "high" else s.index[s <= thr]
    ev = decluster(list(ev))
    if len(ev) < 8:
        return None
    ev_ret = f.loc[[d for d in ev if d in f.index]]
    base = f.mean()
    excess = ev_ret.mean() - base
    # bootstrap null: random declustered same-size event sets
    n = len(ev_ret)
    f_arr = f.values
    cnt = 0
    for _ in range(n_boot):
        idx = rng.choice(len(f_arr), size=n, replace=False)
        if abs(f_arr[idx].mean() - base) >= abs(excess):
            cnt += 1
    p = (cnt + 1) / (n_boot + 1)
    hit = float((ev_ret > 0).mean())
    return dict(n=n, mean_fwd=float(ev_ret.mean()), base=float(base),
                excess=float(excess), hit=hit, p=p)


def bh_fdr(pvals, alpha=0.10):
    """Benjamini-Hochberg; returns dict pval->reject bool by rank."""
    items = [(k, v) for k, v in pvals.items() if not np.isnan(v)]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    out = {}
    thresh_rank = 0
    for i, (k, v) in enumerate(items, 1):
        if v <= alpha * i / m:
            thresh_rank = i
    for i, (k, v) in enumerate(items, 1):
        out[k] = i <= thresh_rank
    return out


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--vix", default=None, help="override VIX csv (e.g. fresh 1990-2026 copy)")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()
    n_boot = 300 if args.fast else 2000
    rng = np.random.default_rng(SEED)

    panel = build_panel(vix_path=args.vix)
    ind = build_indicators(panel)

    # forward returns: signal known at close t → enter next close (t+1) → exit close t+1+h.
    # avoids same-close look-ahead.
    tgt = {}
    for h in HORIZONS:
        nxt = panel["SPY"].shift(-1)
        tgt[("SPY", h)] = panel["SPY"].shift(-(h + 1)) / nxt - 1
        nq = panel["QQQ"].shift(-1)
        tgt[("QQQ", h)] = panel["QQQ"].shift(-(h + 1)) / nq - 1

    results = []
    pgrid = {}
    for name in ind.columns:
        sig = ind[name]
        first = sig.first_valid_index()
        for (asset, h) in [(a, h) for a in ["SPY", "QQQ"] for h in HORIZONS]:
            fwd = tgt[(asset, h)]
            ic_all, n_all = spearman_ic(sig, fwd)
            # in / out of sample
            insm = sig.index <= OOS_SPLIT
            ic_in, n_in = spearman_ic(sig[insm], fwd[insm])
            ic_out, n_out = spearman_ic(sig[~insm], fwd[~insm])
            block = max(5, 2 * h)
            p_ic = block_bootstrap_ic_pvalue(sig, fwd, n_boot=max(300, n_boot // 4),
                                             block=block, rng=rng)
            row = dict(indicator=name, asset=asset, h=h, start=str(first.date()) if first is not None else None,
                       n=n_all, ic=None if np.isnan(ic_all) else round(float(ic_all), 4),
                       ic_in=None if np.isnan(ic_in) else round(float(ic_in), 4),
                       ic_out=None if np.isnan(ic_out) else round(float(ic_out), 4),
                       p_ic=None if np.isnan(p_ic) else round(float(p_ic), 4))
            for side in ["high", "low"]:
                es = event_study(sig, fwd, side, EXTREME_Q, rng,
                                 n_boot=max(400, n_boot // 2), block=block)
                if es:
                    row[f"{side}_n"] = es["n"]
                    row[f"{side}_excess"] = round(es["excess"] * 100, 3)   # in %
                    row[f"{side}_hit"] = round(es["hit"], 3)
                    row[f"{side}_p"] = round(es["p"], 4)
                    pgrid[(name, asset, h, side)] = es["p"]
            results.append(row)

    # FDR across the entire event-study grid (the honest multiple-testing control)
    rejects = bh_fdr(pgrid, alpha=0.10)
    for row in results:
        for side in ["high", "low"]:
            key = (row["indicator"], row["asset"], row["h"], side)
            if key in rejects:
                row[f"{side}_fdr_pass"] = bool(rejects[key])

    df = pd.DataFrame(results)

    # ── print ranking: significant extreme-signal effects that survive FDR ────
    print("=" * 100)
    print("A) 極端訊號事件研究（十分位、去叢集 21 交易日、BH-FDR 10% 全網格校正）— 只列過 FDR 者")
    print("=" * 100)
    cols = ["indicator", "asset", "h", "start"]
    hits = []
    for _, r in df.iterrows():
        for side in ["high", "low"]:
            if r.get(f"{side}_fdr_pass") is True:
                hits.append(dict(indicator=r["indicator"], asset=r["asset"], h=r["h"],
                                 side=side, n=r[f"{side}_n"],
                                 excess_pct=r[f"{side}_excess"], hit=r[f"{side}_hit"],
                                 p=r[f"{side}_p"], start=r["start"]))
    hits_df = pd.DataFrame(hits)
    if len(hits_df):
        hits_df = hits_df.sort_values(["indicator", "asset", "h"])
        print(hits_df.to_string(index=False))
    else:
        print("（無任何組合通過 FDR）")

    print()
    print("=" * 100)
    print("B) 資訊係數 IC（Spearman，全樣本 + 樣本內/外）— 依 |IC(20d,SPY)| 排序前 15")
    print("=" * 100)
    b = df[(df.asset == "SPY") & (df.h == 20)].copy()
    b["absic"] = b["ic"].abs()
    b = b.sort_values("absic", ascending=False).head(15)
    print(b[["indicator", "n", "ic", "ic_in", "ic_out", "p_ic"]].to_string(index=False))

    out_path = args.json_out or "/tmp/leading_indicators_results.json"
    with open(out_path, "w") as fh:
        json.dump(dict(results=results,
                       fdr_hits=hits,
                       config=dict(horizons=HORIZONS, extreme_q=EXTREME_Q,
                                   decluster_gap=DECLUSTER_GAP, oos_split=OOS_SPLIT,
                                   n_boot=n_boot)), fh, indent=1, default=str)
    print(f"\nJSON saved → {out_path}")


if __name__ == "__main__":
    sys.exit(main())
