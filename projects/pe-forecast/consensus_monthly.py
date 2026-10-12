#!/usr/bin/env python3
"""每月一次的共識快照與累積面板（README §20.6）。

    python3 consensus_monthly.py                 # 每月跑一次（約 12 分鐘）：存兩份快照 → 記下當時的校正係數 → 更新累積面板 → 印出進度
    python3 consensus_monthly.py --skip-fetch    # 不抓新資料，只用已存的快照重建面板與進度
    python3 consensus_monthly.py --reestimate    # 用累積的面板對答案（不夠時說明還差什麼）→ results/consensus_monthly.txt
    python3 consensus_monthly.py --selftest --cache <lab_orbit 暫存目錄>
                                                 # 用 I/B/E/S 歷史共識（OSAP）模擬一份面板，確認對答案的程式算得對（應接近 README §18.3）

為什麼要每月存：Yahoo 只給「今天」的共識，歷史共識要自己存。累積一年以上之後可以做兩件現在做不到的事：
  ① 驗證「下一財年」的校正（§19.1 的假設：同一個校正係數也用在下一財年，訓練資料只有本財年）——每月記下當時模型給的係數，
    年報公布後直接對答案，這是完全沒看過答案的檢驗；
  ② 用真正的共識（而不是代理）重估「市場已預期的成長」的 β（§16.1、§18.3）。
面板（data/consensus_panel.csv.gz；每檔每個月留最新一份）：
  asof、symbol、px（股價）、ttm（GAAP 最近四季，Yahoo）、mrq（最近一季）、last_fy（最近已公布的年度）、
  fy0_end／c0（本財年結束日／共識）、fy1_end／c1（下一財年）、n0、n1（分析師人數）、d90_0、d90_1（90 天前的共識）、
  street_ttm（調整後最近四季）、cf（當時模型給的共識校正係數，沒有＝空白）、y10（當月 10 年期）。
對答案時「實際」也來自面板本身：某財年結束後第一份 mrq 落在年度結束日 ±20 天的快照，它的 GAAP 最近四季就是該年度 EPS；
12 個月後的股價與 EPS 也取 12 個月後（±20 天）的那份快照。
"""
import argparse
import glob
import io
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import consensus, eps_correct, orbit                # noqa: E402

SNAP = os.path.join(HERE, "data", "consensus_snapshots")
PANEL = os.path.join(HERE, "data", "consensus_panel.csv.gz")
RES = os.path.join(HERE, "results")
TOL = 20
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def fetch():
    import consensus_snapshot as CS
    d = consensus.snapshot()
    if len(d):
        p = consensus.save_snapshot(d, SNAP)
        print(f"全部類股：{len(d):,} 檔 → {os.path.relpath(p, HERE)}")
    CS.detail()


def corrections(date):
    """今天的共識校正係數（和網頁同一套算法），存成 correction_<日期>.csv；之後拿來對答案。"""
    det = sorted(glob.glob(os.path.join(SNAP, f"yahoo_detail_{date}.csv.gz")))
    scr = sorted(glob.glob(os.path.join(SNAP, f"yahoo_{date}.csv.gz")))
    if not det:
        return None
    q = pd.read_csv(det[-1], parse_dates=["last_fy", "mrq"]).drop_duplicates("symbol").set_index("symbol")
    s = pd.read_csv(scr[-1]).drop_duplicates("symbol").set_index("symbol") if scr else pd.DataFrame()
    n = pd.read_csv(os.path.join(RES, "now_all.csv"))
    n["sym"] = n["ticker"].map(consensus.yahoo_symbol)
    rows = []
    for r in n[n["sym"].isin(q.index)].to_dict("records"):
        big = bool(r["in_sp500"]) or bool(r.get("in_ndx"))
        x = q.loc[r["sym"]]
        if pd.isna(x.get("last_fy")) or not (x.get("0y_avg") and x["0y_avg"] > 0):
            continue
        r2 = dict(r)                                      # 和網頁（make_orbit_page.py）同一套：快照股價＋refresh_eps 的最近四季
        sr = s.loc[r["sym"]].to_dict() if r["sym"] in s.index else None
        if sr is not None and sr.get("currency") == "USD" and pd.notna(sr.get("regularMarketPrice")):
            r2["px"] = float(sr["regularMarketPrice"])
        snap_time = pd.Timestamp(sr["asof_utc"]).tz_localize(None) if sr is not None and pd.notna(sr.get("asof_utc")) else pd.Timestamp(date)
        rf = consensus.refresh_eps(r, sr, snap_time, mrq=x["mrq"] if pd.notna(x.get("mrq")) else None)
        r2["eps0"] = rf["eps0"]
        cr = eps_correct.for_ticker(r["ticker"], r2, x["0y_avg"], x["last_fy"] + pd.DateOffset(months=12), x.get("0y_d30"),
                                    x.get("0y_d90"), x["last_fy"], today=pd.Timestamp(date), scope="big" if big else "small")
        if cr is not None:
            rows.append(dict(symbol=r["sym"], cf=round(cr["factor"], 5), cf_tree=round(cr["factor_tree"], 5), lead=round(cr["feats"]["lead"], 2),
                             scope="big" if big else "small"))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(SNAP, f"correction_{date}.csv"), index=False)
    return out


def build_panel():
    rt = pd.read_csv(os.path.join(HERE, "data", "rates_monthly.csv"), parse_dates=["month_end"])
    rt["ym"] = rt["month_end"].dt.strftime("%Y-%m")
    y10 = rt.set_index("ym")["DGS10"] / 100
    rows = []
    for f in sorted(glob.glob(os.path.join(SNAP, "yahoo_detail_*.csv.gz"))):
        date = os.path.basename(f)[len("yahoo_detail_"):-len(".csv.gz")]
        q = pd.read_csv(f, parse_dates=["last_fy", "mrq"]).drop_duplicates("symbol")
        scr = [g for g in sorted(glob.glob(os.path.join(SNAP, "yahoo_2*.csv.gz")))
               if abs((pd.Timestamp(os.path.basename(g)[6:16]) - pd.Timestamp(date)).days) <= 5]
        s = pd.read_csv(scr[-1]).drop_duplicates("symbol")[["symbol", "regularMarketPrice", "epsTrailingTwelveMonths", "currency"]] if scr else None
        cf = os.path.join(SNAP, f"correction_{date}.csv")
        c = pd.read_csv(cf)[["symbol", "cf"]] if os.path.exists(cf) else None
        x = q.rename(columns={"0y_avg": "c0", "+1y_avg": "c1", "0y_n": "n0", "+1y_n": "n1", "0y_d90": "d90_0", "+1y_d90": "d90_1"})
        x = x[["symbol", "last_fy", "mrq", "street_ttm", "c0", "c1", "n0", "n1", "d90_0", "d90_1"]].copy()
        x["asof"] = pd.Timestamp(date)
        if s is not None:
            x = x.merge(s.rename(columns={"regularMarketPrice": "px", "epsTrailingTwelveMonths": "ttm"}), on="symbol", how="left")
        x = x.merge(c, on="symbol", how="left") if c is not None else x.assign(cf=np.nan)
        rows.append(x)
    if not rows:
        return pd.DataFrame()
    p = pd.concat(rows, ignore_index=True)
    p["fy0_end"] = p["last_fy"] + pd.DateOffset(months=12)
    p["fy1_end"] = p["last_fy"] + pd.DateOffset(months=24)
    p["ym"] = p["asof"].dt.strftime("%Y-%m")
    p["y10"] = p["ym"].map(y10).fillna(y10.iloc[-1])
    p = p.sort_values("asof").drop_duplicates(["symbol", "ym"], keep="last")
    p.to_csv(PANEL, index=False, float_format="%.6g", compression={"method": "gzip", "mtime": 0})
    return p


def actual_fy(p):
    """面板自己找年度實際值：年度結束後第一份 mrq 落在結束日 ±20 天的快照 → 它的 GAAP 最近四季。回傳 {(symbol, 年度結束日): EPS}。"""
    out = {}
    z = p.dropna(subset=["mrq", "ttm"]).sort_values("asof")
    for r in z.itertuples():
        for e in (r.mrq,):
            key = (r.symbol, pd.Timestamp(e).normalize())
            if key not in out:
                out[key] = r.ttm
    return out


def match_fy(act, sym, e):
    if pd.isna(e):
        return None
    for k in range(-TOL, TOL + 1):
        v = act.get((sym, (pd.Timestamp(e) + pd.Timedelta(days=k)).normalize()))
        if v is not None:
            return v
    return None


def fy_check(p, act):
    """① 本財年／下一財年：共識原樣 vs 乘上當時的校正係數，對年度實際 GAAP EPS 的中位 |ln 誤差|。"""
    rows = []
    for r in p.itertuples():
        for which, e, c in (("本財年", r.fy0_end, r.c0), ("下一財年", r.fy1_end, r.c1)):
            if not (pd.notna(c) and c > 0):
                continue
            a = match_fy(act, r.symbol, e)
            if a is None or not a > 0:
                continue
            rows.append(dict(年度=which, symbol=r.symbol, asof=r.asof, lead=(pd.Timestamp(e) - r.asof).days / 30.44,
                             raw=np.log(a / c), corr=np.log(a / (c * r.cf)) if pd.notna(r.cf) else np.nan))
    return pd.DataFrame(rows)


def beta_check(p, h=12, sector=None):
    """② 「市場已預期的成長」與「和共識的差距」（預期＋修正a）用真共識重估：12 個月後（±20 天）的快照當答案。"""
    sector = sector or {}
    z = p.dropna(subset=["px", "ttm"]).copy()
    idx = {s: g.set_index("asof") for s, g in z.groupby("symbol")}
    rows = []
    for r in z.itertuples():
        if not (r.ttm > 0 and r.px > 0 and pd.notna(r.c0) and r.c0 > 0):
            continue
        g = idx[r.symbol]
        tgt = r.asof + pd.DateOffset(months=h)
        fut = g[(g.index >= tgt - pd.Timedelta(days=TOL)) & (g.index <= tgt + pd.Timedelta(days=TOL))]
        if fut.empty:
            continue
        f = fut.iloc[0]
        if not (f["ttm"] > 0 and f["px"] > 0):
            continue
        k = r.cf if pd.notna(r.cf) else 1.0
        fy = {pd.Timestamp(r.fy0_end): r.c0 * k}
        if pd.notna(r.c1) and r.c1 > 0:
            fy[pd.Timestamp(r.fy1_end)] = r.c1 * k
        ca, _ = orbit.calendarize(fy, tgt, r.mrq, r.ttm, extrapolate=True)
        if ca is None or not ca > 0:
            continue
        y = np.log(f["px"] / r.px) - (r.y10 + 0.05) * h / 12
        rows.append(dict(symbol=r.symbol, month=r.asof.to_period("M").to_timestamp(), y=y, x_exp=np.log(ca / r.ttm),
                         x_gap=np.log(f["ttm"] / ca), grp=orbit.group_of(sector.get(r.symbol))))
    return pd.DataFrame(rows)


def fit_beta(d):
    from pef.stats import huber_ols
    out = {}
    for g, gg in list(d.groupby("grp")) + [("全部", d)]:
        if len(gg) < 300:
            out[g] = (None, len(gg))
            continue
        yy = gg["y"] - gg.groupby("month")["y"].transform("median")
        X = np.column_stack([gg[c].clip(-2, 2) - gg.groupby("month")[c].transform(lambda v: v.clip(-2, 2).median()) for c in ("x_exp", "x_gap")])
        out[g] = (huber_ols(X, yy.to_numpy(float)), len(gg))
    return out


def status(p):
    if p.empty:
        say("面板是空的：先跑一次 python3 consensus_monthly.py")
        return
    months = sorted(p["ym"].unique())
    say(f"累積面板：{len(months)} 個月份（{months[0]}～{months[-1]}）、{p['symbol'].nunique()} 檔、{len(p):,} 列；"
        f"有當時校正係數的列 {int(p['cf'].notna().sum()):,}")
    first = pd.Timestamp(months[0] + "-01")
    say(f"  ① 下一財年校正的驗證：要等年報公布。最早一批大約在 {(first + pd.DateOffset(months=13)):%Y-%m} 開始有答案，"
        f"累積到 200 組以上（約 {(first + pd.DateOffset(months=18)):%Y-%m}）才看得出結論")
    say(f"  ② 真共識重估 β：要 12 個月後的快照當答案，最早 {(first + pd.DateOffset(months=12)):%Y-%m}；"
        f"每類 300 組以上大約要到 {(first + pd.DateOffset(months=18)):%Y-%m}（每月都要存，漏掉的月份補不回來）")


def reestimate(p, sector):
    act = actual_fy(p)
    fc = fy_check(p, act)
    say("\n== ① 年度實際 vs 共識（中位 |ln(實際 ÷ 共識)|）")
    if len(fc) < 50:
        say(f"  還不夠：目前只有 {len(fc)} 組有答案（要 200 組以上才下結論）")
    else:
        for w, g in fc.groupby("年度"):
            say(f"  {w}：n={len(g):,}；共識原樣 {np.median(np.abs(g['raw'])):.3f}；乘上當時的校正係數 {np.nanmedian(np.abs(g['corr'])):.3f}"
                f"（有係數的 {int(g['corr'].notna().sum()):,} 組）")
    bc = beta_check(p, sector=sector)
    say("\n== ② 用真共識重估 β（12 個月；預期＋修正a：市場已預期的成長、你和共識的差距）")
    if len(bc) < 300:
        say(f"  還不夠：目前只有 {len(bc)} 組有 12 個月後的答案（每類要 300 組以上）")
        return
    model = orbit.load_model(RES)
    prod = model["h"]["12"]["beta"]["預期＋修正a"]
    for g, (b, n) in fit_beta(bc).items():
        if b is None:
            say(f"  {orbit.GNAME.get(g, g)}：n={n}（不足 300）")
        else:
            pv = prod.get(g)
            say(f"  {orbit.GNAME.get(g, g)}：n={n:,}；β_預期 {b[0]:+.3f}、β_差距 {b[1]:+.3f}" + (f"（正式版 {pv[0]:+.3f}、{pv[1]:+.3f}）" if pv else ""))


def selftest(cache):
    """用 OSAP 的 I/B/E/S 本財年共識，把 S&P 500 面板做成「每月快照」的樣子，跑同一套對答案的程式。"""
    import lab_eps_correction as L
    d = L.build(cache)
    d = d[(d["month"] >= "2012-01-01") & ~d["near_split"]]
    p = pd.DataFrame({"symbol": d["ticker"], "asof": d["month"] + pd.offsets.MonthEnd(0), "px": d["px"], "ttm": d["eps0"],
                      "mrq": d["period_end"], "fy0_end": d["fy1"], "c0": d["feps"], "c1": np.nan, "fy1_end": pd.NaT,
                      "cf": np.nan, "y10": d["y10"]})
    p["ym"] = p["asof"].dt.strftime("%Y-%m")
    sector = d.drop_duplicates("ticker").set_index("ticker")["sector"].to_dict()
    act = actual_fy(p)
    fc = fy_check(p, act)
    say(f"自我檢驗（OSAP 模擬面板 2012–2024，{p['symbol'].nunique()} 家、{len(p):,} 列）")
    if len(fc):
        say(f"  ① 本財年共識原樣的中位 |ln(實際 ÷ 共識)| ＝ {np.median(np.abs(fc['raw'])):.3f}（n={len(fc):,}；"
            f"lab_eps_correction.py 同一個量是 0.144，口徑相近就算對）")
    bc = beta_check(p, sector=sector)
    res = fit_beta(bc)
    say(f"  ② 重估 β（n={len(bc):,}）：" + "；".join(f"{orbit.GNAME.get(g, g)} β_預期 {b[0]:+.3f}、β_差距 {b[1]:+.3f}（n={n:,}）"
                                                 for g, (b, n) in res.items() if b is not None))
    say("     README §18.3（真共識、每家每年一個起點）：全部 β_共識預期 0.045、β_差距 0.078；正式版（代理預期）非科技 0.013、0.079")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-fetch", action="store_true")
    ap.add_argument("--reestimate", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--cache", default=None)
    a = ap.parse_args()
    if a.selftest:
        if not a.cache:
            sys.exit("--selftest 要給 --cache（lab_orbit.py 的暫存目錄）")
        selftest(a.cache)
        open(os.path.join(RES, "consensus_monthly_selftest.txt"), "w").write(buf.getvalue())
        return
    if not a.skip_fetch and not a.reestimate:
        fetch()
        today = pd.Timestamp.now().strftime("%Y-%m-%d")
        c = corrections(today)
        print(f"今天的校正係數：{0 if c is None else len(c)} 檔 → data/consensus_snapshots/correction_{today}.csv")
    p = build_panel()
    status(p)
    if a.reestimate:
        n = pd.read_csv(os.path.join(RES, "now_all.csv"), usecols=["ticker", "sector"])
        reestimate(p, {consensus.yahoo_symbol(t): s for t, s in zip(n["ticker"], n["sector"])})
        open(os.path.join(RES, "consensus_monthly.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
