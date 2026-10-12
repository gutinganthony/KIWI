#!/usr/bin/env python3
"""中小型股的 I/B/E/S 共識（OSAP FEPS）→ 面板口徑（README §20.3）。osap_fetch.py 的 S&P 500 版的延伸。

    python3 osap_small.py [--raw-dir DIR] [--refresh]     # 第一次約 25 分鐘（每檔抓一次 Yahoo 20 年月線＋分割事件）

步驟：
 1. Yahoo 20 年月線（含息還原收盤 adjclose、分割還原收盤 close、分割事件），每檔一次：raw/yahoo_small/<代號>.json
 2. permno 配對：和 S&P 500 版同一個方法——我們的 Mom12m（P_{t-1}/P_{t-12}−1，用 adjclose）和 OSAP 的 Mom12m 逐 permno 算相關，
    取最高者；門檻：相關 ≥ 0.95、重疊 ≥ 36 個月；兩檔配到同一個 permno 時留相關高的
 3. 口徑：I/B/E/S FEPS 是「當時」的每股數字（沒有分割還原）。
      今天口徑＝FEPS ÷（統計日之後所有分割倍數的乘積）
      面板口徑＝今天口徑 × f，f＝面板股價 ÷ Yahoo 分割還原收盤（同一個季末月份；面板的股數口徑由 市值 ÷ 股價 決定，
      有些公司的面板股價帶著 1.25 這類調整，f 會把它換回來）。f 依季末月份往前補到那一季的每個月。
輸出：data/osap/feps_small.csv.gz（ticker, yyyymm, feps_raw, feps, fgr5y, f_basis）、data/osap/permno_map_small.csv
不可信資料（下載檔）放在 raw dir，不進 repo；程式不執行它們，只用 pandas 讀。
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import osap_fetch as OF

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = DATA / "osap"


def fetch(tickers, raw, refresh):
    d = raw / "yahoo_small"
    d.mkdir(parents=True, exist_ok=True)
    sess = OF.session()
    miss = 0
    for i, t in enumerate(tickers):
        sym = str(t).upper().replace(".", "-")
        f = d / f"{sym}.json"
        if f.exists() and not refresh:
            continue
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=20y&interval=1mo&events=split"
        for attempt in range(3):
            try:
                r = sess.get(url, timeout=30)
            except Exception:                                 # noqa: BLE001
                r = None
            time.sleep(0.7)
            if r is not None and r.status_code == 200:
                f.write_bytes(r.content)
                break
            if r is not None and r.status_code == 404:
                break
            time.sleep(5 * (attempt + 1))
        if not f.exists():
            miss += 1
        if (i + 1) % 200 == 0:
            print(f"  [yahoo] {i + 1}/{len(tickers)}（抓不到 {miss}）", flush=True)
    return d


def parse(d, tickers):
    px, cl, sp = [], [], []
    for t in tickers:
        f = d / f"{str(t).upper().replace('.', '-')}.json"
        if not f.exists():
            continue
        try:
            res = json.loads(f.read_text())["chart"]["result"][0]
            ts = res["timestamp"]
            adj = res["indicators"]["adjclose"][0]["adjclose"]
            close = res["indicators"]["quote"][0]["close"]
        except Exception:                                     # noqa: BLE001
            continue
        dt = pd.to_datetime(pd.Series(ts), unit="s", utc=True).dt.tz_convert("America/New_York")
        ym = (dt.dt.year * 100 + dt.dt.month).to_numpy()
        x = pd.DataFrame({"ticker": t, "ym": ym, "px": pd.to_numeric(pd.Series(adj), errors="coerce").to_numpy(),
                          "close": pd.to_numeric(pd.Series(close), errors="coerce").to_numpy()})
        x = x[x["px"] > 0].drop_duplicates("ym", keep="last")
        gaps = np.diff([(v // 100) * 12 + v % 100 for v in x["ym"]])
        if len(gaps) and np.median(gaps) == 1:
            px.append(x)
        for ev in (res.get("events") or {}).get("splits", {}).values():
            num, den = float(ev.get("numerator") or 0), float(ev.get("denominator") or 0)
            if num > 0 and den > 0 and abs(num / den - 1) > 1e-9:
                when = pd.Timestamp(int(ev["date"]), unit="s", tz="UTC").tz_convert("America/New_York").tz_localize(None).normalize()
                sp.append(dict(ticker=t, date=when, ratio=num / den))
    P = pd.concat(px, ignore_index=True) if px else pd.DataFrame(columns=["ticker", "ym", "px", "close"])
    S = pd.DataFrame(sp, columns=["ticker", "date", "ratio"])
    return P, S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", type=Path, default=None)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--release", default="202510")
    a = ap.parse_args()
    raw = (a.raw_dir or OF.default_raw_dir()).resolve()
    u = pd.read_csv(DATA / "universe_small.csv")
    tickers = sorted(u["ticker"].dropna().unique())
    print(f"[osap_small] {len(tickers)} 檔；raw dir {raw}")
    d = fetch(tickers, raw, a.refresh)
    P, S = parse(d, tickers)
    print(f"  Yahoo 月線 {P['ticker'].nunique()} 檔、分割事件 {len(S)} 筆（{S['ticker'].nunique()} 檔）")

    files = {k: raw / a.release / f"{k}.csv" for k in ("FEPS", "Mom12m", "Mom6m", "fgr5yrLag")}
    sig = {k: OF.load_signal(p, k, 200001) for k, p in files.items() if p.exists()}
    # 對齊：抽 40 檔試 lag −1／0／+1
    grid = OF.ym_range(int(P["ym"].min()), int(min(P["ym"].max(), sig["Mom12m"]["yyyymm"].max())))
    O12, _ = OF._osap_wide(sig["Mom12m"], sig["Mom6m"], grid)
    spot = P["ticker"].drop_duplicates().sample(min(40, P["ticker"].nunique()), random_state=0)
    lag_tab = {}
    for lag in (-1, 0, 1):
        m12, _ = OF.our_momentum(P[P["ticker"].isin(spot)], grid, lag)
        r, n = OF.masked_corr(m12.to_numpy(float), O12.to_numpy(float))
        r[n < OF.MIN_OVERLAP] = np.nan
        lag_tab[lag] = float(np.nanmedian(np.nanmax(r, axis=1)))
    best = max(lag_tab, key=lag_tab.get)
    print("  [對齊] 抽查 40 檔的最佳相關中位數：", ", ".join(f"lag {k:+d}: {v:.4f}" for k, v in lag_tab.items()), f"→ lag {best:+d}")
    M = OF._corr_table(P[["ticker", "ym", "px"]], sig["Mom12m"], sig["Mom6m"], best)
    M["ok"] = (M["corr"] >= OF.MIN_CORR) & (M["n_overlap"] >= OF.MIN_OVERLAP)
    dup = M[M["ok"]].sort_values("corr", ascending=False).duplicated("permno", keep="first")
    M.loc[dup[dup].index, "ok"] = False
    ok = M[M["ok"]]
    print(f"  [配對] 成功 {len(ok)}／{len(tickers)}（{len(ok) / len(tickers):.1%}）；相關中位數 {ok['corr'].median():.4f}，最低 {ok['corr'].min():.4f}")
    OUT.mkdir(parents=True, exist_ok=True)
    keep = [c for c in ("ticker", "permno", "corr", "n_overlap", "second_best_corr", "second_permno", "corr6", "mad12", "ok") if c in M]
    M[keep].round(4).to_csv(OUT / "permno_map_small.csv", index=False)

    F = ok[["ticker", "permno"]].astype({"permno": "int64"}).merge(sig["FEPS"].rename(columns={"FEPS": "feps_raw"}), on="permno")
    if "fgr5yrLag" in sig:
        F = F.merge(sig["fgr5yrLag"].rename(columns={"fgr5yrLag": "fgr5y"}), on=["permno", "yyyymm"], how="left")
    F = F[F["yyyymm"] >= 201501].copy()
    # 今天口徑：÷ 統計日之後的分割倍數乘積
    F["stat"] = F["yyyymm"].map(OF.statpers)
    sp = {t: g for t, g in S.groupby("ticker")}
    F["after"] = [float(np.prod(sp[t].loc[sp[t]["date"] > s, "ratio"])) if t in sp else 1.0 for t, s in zip(F["ticker"], F["stat"])]
    F["feps_today"] = F["feps_raw"] / F["after"]
    # 面板口徑：f＝面板股價 ÷ Yahoo 分割還原收盤（季末月份），往前補到那一季的每個月
    pq = pd.read_csv(DATA / "prices_quarterly_small.csv", parse_dates=["month"])
    pq["ym"] = pq["month"].dt.year * 100 + pq["month"].dt.month
    fb = pq.merge(P[["ticker", "ym", "close"]], on=["ticker", "ym"], how="inner")
    fb["f_basis"] = fb["px"] / fb["close"]
    fb = fb[np.isfinite(fb["f_basis"]) & (fb["f_basis"] > 0)]
    fb["q"] = fb["month"].dt.to_period("Q")
    F["q"] = pd.to_datetime(F["yyyymm"].astype(str) + "01").dt.to_period("Q")
    F = F.merge(fb[["ticker", "q", "f_basis"]], on=["ticker", "q"], how="left")
    F["feps"] = F["feps_today"] * F["f_basis"]
    lf = np.log(fb["f_basis"])
    print(f"  [口徑] 面板 ÷ Yahoo：f 中位 {fb['f_basis'].median():.3f}；|ln f| > 0.05 的季 {(lf.abs() > 0.05).mean():.1%}（面板股價帶調整的公司）；"
          f"有面板口徑共識的列 {F['feps'].notna().mean():.0%}")
    out = F[F["feps"].notna()][["ticker", "yyyymm", "feps_raw", "feps", "fgr5y", "f_basis"]]
    out.to_csv(OUT / "feps_small.csv.gz", index=False, float_format="%.6g", compression={"method": "gzip", "mtime": 0})
    print(f"  → data/osap/feps_small.csv.gz：{len(out):,} 列、{out['ticker'].nunique()} 家（{out['yyyymm'].min()}～{out['yyyymm'].max()}）")


if __name__ == "__main__":
    main()
