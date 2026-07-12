#!/usr/bin/env python3
"""驗證「LFI 節流閥」對 Serenity 型高 beta 標的的擇時價值（先驗證、不加）。

問題：Serenity watchlist 清一色高 beta AI 供應鏈小型股。如果在「LFI（槓桿融資
擁擠度）高檔」時進場、vs「低檔」時進場，前瞻報酬有沒有顯著差別？若有，節流閥
（高檔只進首批、低檔放大批次）才值得放進篩選器。

資料限制：真實 Serenity 標的（JEM/Towa/Kokusai…日台小型股）在雲端抓不到、
本地也沒有歷史。因此用**高 beta AI-半導體代理籃**（SMH/SOXX/NVDA/MU，全在
data/backtest，1996/2000/2001→2020-04，且它們就是 Serenity 書的 beta 母體）
做代理驗證。這是「方向性證據」，非真標的——真標的驗證需資料橋補齊（見 §infra）。

方法（沿用 leading_indicators_backtest 的紀律）：
  - LFI = lev_stress_proxy 的分位數（同 dashboard 第四錶）
  - 事件：LFI 進入高檔（>=80 分位）/ 低檔（<=20 分位），各自去叢集 21 交易日
  - 比較兩組進場後 20/60 日的前瞻報酬（代理籃平均），對「無條件基準」求超額
  - bootstrap p、樣本內外（2012-12-31 切）、對每個標的重複
輸出：印出對照表 + JSON。

用法：python3 scripts/serenity_throttle_validation.py [--fast]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "backtest"
sys.path.insert(0, str(ROOT / "src"))
from lfi import compute_lfi_series  # noqa: E402

PROXY = ["SMH", "SOXX", "NVDA", "MU"]   # 高 beta AI-半導體代理籃
HORIZONS = [20, 60]
HIGH_Q, LOW_Q = 80, 20
DECLUSTER = 21
OOS = "2012-12-31"
SEED = 42


def load_close(name):
    df = pd.read_csv(DATA / f"{name}.csv")
    df.columns = [c.strip() for c in df.columns]
    dcol = next((c for c in df.columns if c.lower() == "date"), df.columns[0])
    df[dcol] = pd.to_datetime(df[dcol], format="mixed")
    df = df.set_index(dcol).sort_index()
    up = {c.upper(): c for c in df.columns}
    for cand in ("Adj Close", "CLOSE", "Close", "VIX CLOSE", "VVIX"):
        if cand in df.columns:
            return df[cand].astype(float)
        if cand.upper() in up:
            return df[up[cand.upper()]].astype(float)
    return df.iloc[:, -1].astype(float)


def decluster(idx, gap=DECLUSTER):
    kept, last = [], None
    for d in idx:
        if last is None or (d - last).days > gap * 1.4:
            kept.append(d); last = d
    return kept


def fwd_ret(price, h):
    nxt = price.shift(-1)
    return price.shift(-(h + 1)) / nxt - 1


def event_excess(lfi_pctl, fwd, side, rng, n_boot):
    thr = HIGH_Q if side == "high" else LOW_Q
    ev = lfi_pctl.index[lfi_pctl >= thr] if side == "high" else lfi_pctl.index[lfi_pctl <= thr]
    ev = [d for d in decluster(list(ev)) if d in fwd.index and not np.isnan(fwd.loc[d])]
    if len(ev) < 8:
        return None
    er = fwd.loc[ev]
    base = fwd.mean()
    excess = er.mean() - base
    f = fwd.dropna().values
    n = len(er)
    cnt = sum(abs(rng.choice(f, n, replace=False).mean() - base) >= abs(excess) for _ in range(n_boot))
    return dict(n=n, mean=float(er.mean()), base=float(base), excess=float(excess),
                hit=float((er > 0).mean()), p=(cnt + 1) / (n_boot + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--json-out", default="/tmp/serenity_throttle.json")
    args = ap.parse_args()
    n_boot = 400 if args.fast else 3000
    rng = np.random.default_rng(SEED)

    spy = load_close("SPY"); hyg = load_close("HYG")
    vvix = load_close("VVIX"); vix = load_close("VIX")
    lfi = compute_lfi_series(spy, hyg, vvix, vix)["lfi_pctl"].dropna()

    proxies = {t: load_close(t) for t in PROXY}
    # 等權代理籃日報酬 → 累積價格（對齊 LFI 交易日）
    rets = pd.DataFrame({t: p.pct_change() for t, p in proxies.items()})
    basket_ret = rets.mean(axis=1)
    basket = (1 + basket_ret).cumprod()

    rows = []
    for label, series in [("BASKET(等權)", basket)] + [(t, proxies[t]) for t in PROXY]:
        for h in HORIZONS:
            fwd = fwd_ret(series, h)
            common = lfi.index.intersection(fwd.index)
            l = lfi.loc[common]
            for side in ["high", "low"]:
                for tag, mask in [("ALL", slice(None)), ("IS", l.index <= OOS), ("OOS", l.index > OOS)]:
                    ll = l[mask] if tag != "ALL" else l
                    ff = fwd.loc[ll.index]
                    es = event_excess(ll, ff, side, rng, n_boot if tag == "ALL" else max(400, n_boot // 3))
                    if es:
                        rows.append(dict(asset=label, h=h, side=side, sample=tag, **{k: round(v, 4) for k, v in es.items()}))

    df = pd.DataFrame(rows)
    # 主結果：BASKET, ALL sample
    print("=" * 92)
    print("節流閥驗證：LFI 高檔(>=80) vs 低檔(<=20) 進場後，高beta代理籃的前瞻報酬")
    print("（excess = 事件組平均 − 無條件基準；正=優於平均，負=劣於平均）")
    print("=" * 92)
    main_rows = df[(df.asset == "BASKET(等權)")].copy()
    for _, r in main_rows.iterrows():
        arrow = "↑優" if r.excess > 0 else "↓劣"
        sig = "★" if r.p < 0.05 else ("·" if r.p < 0.15 else " ")
        print(f"  [{r['sample']:3s}] {r.side.upper():4s} h={int(r.h):2d}d  n={int(r.n):3d}  "
              f"事件均={r['mean']*100:+6.2f}%  基準={r.base*100:+6.2f}%  "
              f"超額={r.excess*100:+6.2f}% {arrow}  hit={r.hit:.0%}  p={r.p:.3f} {sig}")

    print("\n逐標的（ALL 樣本，h=20）：")
    for _, r in df[(df.sample == "ALL") & (df.h == 20)].sort_values(["asset", "side"]).iterrows():
        if r.asset == "BASKET(等權)":
            continue
        print(f"  {r.asset:5s} {r.side.upper():4s}  超額={r.excess*100:+6.2f}%  hit={r.hit:.0%}  p={r.p:.3f}")

    # 節流閥的核心命題：high 進場劣於 low 進場？量化「差值」
    print("\n" + "=" * 92)
    print("節流閥核心命題檢定：LFI 低檔進場 − 高檔進場 的報酬差（BASKET, ALL）")
    print("=" * 92)
    for h in HORIZONS:
        hi = main_rows[(main_rows.side == "high") & (main_rows.h == h) & (main_rows["sample"] == "ALL")]
        lo = main_rows[(main_rows.side == "low") & (main_rows.h == h) & (main_rows["sample"] == "ALL")]
        if len(hi) and len(lo):
            spread = (lo.iloc[0]["mean"] - hi.iloc[0]["mean"]) * 100
            print(f"  h={h:2d}d：低檔進場均 {lo.iloc[0]['mean']*100:+.2f}% vs 高檔 {hi.iloc[0]['mean']*100:+.2f}% "
                  f"→ 節流閥價值 ≈ {spread:+.2f} 個百分點/{h}日")

    json.dump(rows, open(args.json_out, "w"), indent=1, default=str)
    print(f"\nJSON → {args.json_out}")


if __name__ == "__main__":
    main()
