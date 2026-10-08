#!/usr/bin/env python3
"""osap_fetch.py — Open Source Asset Pricing（Chen & Zimmermann）公開的 I/B/E/S 共識訊號 → S&P 500 面板。

一行重現：  cd projects/pe-forecast && python3 osap_fetch.py
需要：     pip install --user openassetpricing   （只借用它的 Google Drive 資料夾解析器；下載自己做，不碰 WRDS）

選項：
  --raw-dir DIR    原始下載檔放哪（不可信資料，不進 repo）。預設 $OSAP_RAW_DIR，
                   否則本 session 的 scratchpad/osap_raw，否則 ~/.cache/kiwi_osap_raw
  --release 202510 OSAP 版本（openassetpricing.urls 裡的 releaseYYYYMM_url）
  --refresh        已下載的原始檔也重抓
  --wait-min N     Drive 回「Quota exceeded」時每 5 分鐘重試，最多等 N 分鐘（預設 0＝不等，直接失敗）
  --download-only / --splits-only   只跑下載 OSAP／只抓 Yahoo 分割

流程：
 1. openassetpricing 的 Drive 解析器 → release 資料夾裡 SignalDoc.csv 與個別訊號 CSV 的檔案 ID
 2. 下載 SignalDoc、FEPS、AnalystRevision、fgr5yrLag、Mom12m、Mom6m（不請求 Price/Size/STreversal——那三個要 WRDS）
 3. permno → ticker：用我們的月底股價算與 OSAP 同定義的 Mom12m／Mom6m，逐 ticker 找相關最高的 permno
 4. Yahoo 分割事件 → 每月分割係數，FEPS（I/B/E/S statsumu，未分割調整）換成今天的股數口徑
 5. 輸出 data/osap/：feps_sp500.csv.gz、permno_map.csv、signal_doc_excerpt.csv、spot_check.csv
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = DATA / "osap"

SIGNALS = ["FEPS", "AnalystRevision", "fgr5yrLag", "Mom12m", "Mom6m"]
# 2025.10 release 的檔案 ID（2026-10-08 由 openassetpricing 解析器取得）；套件解析失敗時備用
FALLBACK_IDS = {"202510": {
    "SignalDoc": "1rdi0jTPSA6xtn6TpQAMT5WyEczQ1gK59",
    "FEPS": "17Tk0mfShWxqrXxI7XddRq9gMtp5FCtBG",
    "AnalystRevision": "1lJLXcLSNl93plXGCZs8_RdYHevWOsaYE",
    "fgr5yrLag": "1ufnwhKY6K8E59jNvgynl8MbOXqeJgVFk",
    "Mom12m": "1K2IDDXDQjKN9XHj3H4LvnjevOS3SIsgc",
    "Mom6m": "1IZC9q0e71UW7Yr55I4mEek7tGPFbP-hf",
}}
SPOT = ["AAPL", "MSFT", "NVDA", "MU", "AMZN", "GOOGL", "META", "JPM", "XOM", "KO"]
YM_MIN = 200901          # 輸出只留 2009 年以後
MIN_OVERLAP = 36         # 配對至少重疊 36 個月
MIN_CORR = 0.95          # 相關係數門檻
UA = "Mozilla/5.0"       # 請求 header 只放這個；不帶任何個資


def default_raw_dir():
    if os.environ.get("OSAP_RAW_DIR"):
        return Path(os.environ["OSAP_RAW_DIR"])
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if sid:
        sp = Path(f"/tmp/claude-0/-home-user-KIWI/{sid}/scratchpad")
        if sp.is_dir():
            return sp / "osap_raw"
    return Path.home() / ".cache" / "kiwi_osap_raw"


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


# ───────────────────────── 1–2. OSAP 下載 ─────────────────────────

class DriveQuota(RuntimeError):
    pass


def resolve_ids(release, raw_dir, refresh):
    cache = raw_dir / f"ids_{release}.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text())
    try:
        from openassetpricing import urls
        from openassetpricing.gdrive_parse import _get_name_id_map
        m, s = _get_name_id_map(getattr(urls, f"release{release}_url"))
        ids = {"SignalDoc": m.filter(m["name"] == "SignalDoc.csv")["file_id"][0].split("id=")[1]}
        for k in SIGNALS:
            x = s.filter(s["signal"] == k)["file_id"]
            if len(x):
                ids[k] = x[0].split("id=")[1]
    except Exception as e:  # 套件沒裝或 Drive 頁面改版
        if release not in FALLBACK_IDS:
            raise
        print(f"  [ids] openassetpricing 解析失敗（{type(e).__name__}: {str(e)[:80]}），用內建的 {release} 檔案 ID")
        ids = dict(FALLBACK_IDS[release])
    cache.write_text(json.dumps(ids, indent=1))
    return ids


def drive_download(sess, fid, dest):
    """公開 Drive 檔 → dest。大檔的病毒掃描確認頁自動跳過；配額用完丟 DriveQuota。"""
    r = sess.get("https://drive.usercontent.google.com/download",
                 params={"id": fid, "export": "download", "confirm": "t"}, stream=True, timeout=120)
    r.raise_for_status()
    if "text/html" in r.headers.get("content-type", ""):
        html = r.text
        if "Quota exceeded" in html or "Too many users" in html:
            raise DriveQuota(fid)
        import bs4  # openassetpricing 的相依套件
        form = bs4.BeautifulSoup(html, "html.parser").select_one("#download-form")
        if form is None:
            raise RuntimeError(f"Drive 回了看不懂的 HTML（{fid}）")
        q = {i["name"]: i["value"] for i in form.find_all("input", attrs={"type": "hidden"})}
        time.sleep(0.6)
        r = sess.get(form["action"], params=q, stream=True, timeout=120)
        r.raise_for_status()
        if "text/html" in r.headers.get("content-type", ""):
            if "Quota exceeded" in r.text:
                raise DriveQuota(fid)
            raise RuntimeError(f"Drive 確認頁之後仍是 HTML（{fid}）")
    tmp = dest.with_suffix(dest.suffix + ".part")
    n = 0
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            f.write(chunk)
            n += len(chunk)
    with open(tmp, "rb") as f:
        head = f.read(64)
    if head.lstrip().startswith(b"<"):
        tmp.unlink()
        raise RuntimeError(f"下載到的不是 CSV（{fid}）")
    tmp.rename(dest)
    return n


def download_all(release, raw_dir, refresh, wait_min):
    rel = raw_dir / release
    rel.mkdir(parents=True, exist_ok=True)
    ids = resolve_ids(release, raw_dir, refresh)
    missing = [k for k in SIGNALS if k not in ids]
    if missing:
        print(f"  [warn] release {release} 沒有這些訊號：{missing}")
    names = ["SignalDoc"] + [k for k in SIGNALS if k in ids]
    sess = session()
    deadline = time.time() + wait_min * 60
    while True:
        todo = [k for k in names if refresh or not (rel / f"{k}.csv").exists()]
        quota = []
        for k in todo:
            try:
                n = drive_download(sess, ids[k], rel / f"{k}.csv")
                print(f"  [dl] {k}.csv  {n / 1e6:.1f} MB")
            except DriveQuota:
                quota.append(k)
            time.sleep(0.6)
        refresh = False
        if not quota:
            return {k: rel / f"{k}.csv" for k in names}
        if time.time() + 300 > deadline:
            raise SystemExit(
                f"[失敗] Google Drive 對 OSAP 檔回「Quota exceeded」（{', '.join(quota)}）。這是檔案擁有者的下載配額，"
                f"不是本機被擋；稍後重跑，或加 --wait-min 120 讓它每 5 分鐘重試。已下載的檔會留在 {rel}")
        print(f"  [{time.strftime('%H:%M')}] Drive 配額用完：{quota}，5 分鐘後重試", flush=True)
        time.sleep(300)


def load_signal(path, name, ym_min):
    d = pd.read_csv(path, engine="pyarrow")
    d.columns = [c.strip() for c in d.columns]
    col = name if name in d.columns else [c for c in d.columns if c not in ("permno", "yyyymm")][0]
    d = d[["permno", "yyyymm", col]].rename(columns={col: name})
    d = d[(d["yyyymm"] >= ym_min) & d[name].notna()]
    return d.astype({"permno": "int64", "yyyymm": "int64", name: "float64"})


def signal_doc(path):
    doc = pd.read_csv(path, dtype=str, keep_default_na=False)
    doc = doc[doc["Acronym"].isin(SIGNALS)]
    keep = [c for c in ["Acronym", "Cat.Signal", "Cat.Data", "LongDescription", "Detailed Definition",
                        "Authors", "Year", "Journal", "SampleStartYear", "SampleEndYear"] if c in doc.columns]
    return doc[keep] if keep else doc


# ───────────────────────── 3. permno ↔ ticker 配對 ─────────────────────────

def ym_add(ym, k):
    y, m = divmod(ym, 100)
    t = y * 12 + (m - 1) + k
    return (t // 12) * 100 + t % 12 + 1


def ym_range(a, b):
    out = [a]
    while out[-1] < b:
        out.append(ym_add(out[-1], 1))
    return out


def masked_corr(A, B):
    """A：na×T、B：nb×T（NaN＝缺）。回傳兩兩重疊月份的 Pearson 相關與重疊月數。"""
    Ma, Mb = np.isfinite(A).astype(float), np.isfinite(B).astype(float)
    A0, B0 = np.where(Ma > 0, A, 0.0), np.where(Mb > 0, B, 0.0)
    n = Ma @ Mb.T
    sx, sy = A0 @ Mb.T, Ma @ B0.T
    sxx, syy, sxy = (A0 ** 2) @ Mb.T, Ma @ (B0 ** 2).T, A0 @ B0.T
    with np.errstate(divide="ignore", invalid="ignore"):
        cov = sxy - sx * sy / n
        vx, vy = sxx - sx ** 2 / n, syy - sy ** 2 / n
        r = cov / np.sqrt(vx * vy)
    r[(n < 3) | ~np.isfinite(r)] = np.nan
    return r, n


def our_momentum(prices, grid, lag):
    """OSAP 定義：Mom12m＝(1+r_{t-1})…(1+r_{t-11})−1＝P_{t-1}/P_{t-12}−1；Mom6m＝P_{t-1}/P_{t-6}−1（跳過當月）。
    lag＝額外往前挪的月數（0＝照定義），只用來驗證日期對齊。"""
    W = prices.pivot(index="ticker", columns="ym", values="px").reindex(columns=grid)
    m12 = W.shift(1 + lag, axis=1) / W.shift(12 + lag, axis=1) - 1
    m6 = W.shift(1 + lag, axis=1) / W.shift(6 + lag, axis=1) - 1
    return m12, m6


def match_permnos(prices, mom12, mom6):
    ym_lo = int(prices["ym"].min())
    grid = ym_range(ym_lo, int(min(prices["ym"].max(), mom12["yyyymm"].max())))
    O12 = mom12[mom12["yyyymm"].isin(grid)].pivot(index="permno", columns="yyyymm", values="Mom12m").reindex(columns=grid)
    O6 = mom6[mom6["yyyymm"].isin(grid)].pivot(index="permno", columns="yyyymm", values="Mom6m").reindex(columns=grid)
    O12 = O12[O12.notna().sum(axis=1) >= MIN_OVERLAP]
    O6 = O6.reindex(O12.index)

    # 日期對齊驗證：抽查名單上各種 lag 的中位相關
    lag_tab = {}
    for lag in (-1, 0, 1):
        m12, _ = our_momentum(prices, grid, lag)
        sub = m12.reindex([t for t in SPOT if t in m12.index])
        r, n = masked_corr(sub.to_numpy(float), O12.to_numpy(float))
        r[n < MIN_OVERLAP] = np.nan
        lag_tab[lag] = float(np.nanmedian(np.nanmax(r, axis=1)))
    best_lag = max(lag_tab, key=lag_tab.get)
    print("  [對齊] 抽查 10 家的最佳相關中位數（lag 0＝照 SignalDoc 定義）：",
          ", ".join(f"lag {k:+d}: {v:.4f}" for k, v in lag_tab.items()), f"→ 用 lag {best_lag:+d}")

    m12, m6 = our_momentum(prices, grid, best_lag)
    r12, n12 = masked_corr(m12.to_numpy(float), O12.to_numpy(float))
    r12[n12 < MIN_OVERLAP] = np.nan
    permnos = O12.index.to_numpy()
    rows = []
    for i, t in enumerate(m12.index):
        row = r12[i]
        if not np.isfinite(row).any():
            rows.append(dict(ticker=t, permno=np.nan, corr=np.nan, n_overlap=0, second_best_corr=np.nan,
                             second_permno=np.nan, corr6=np.nan, mad12=np.nan, coverage=np.nan))
            continue
        order = np.argsort(-np.nan_to_num(row, nan=-9))
        j, j2 = order[0], order[1]
        a6 = m6.iloc[i].to_numpy(float)
        b6 = O6.iloc[j].to_numpy(float)
        c6, _ = masked_corr(a6[None, :], b6[None, :])
        a12, b12 = m12.iloc[i].to_numpy(float), O12.iloc[j].to_numpy(float)
        ok = np.isfinite(a12) & np.isfinite(b12)
        ours_n = int(np.isfinite(a12).sum())
        rows.append(dict(ticker=t, permno=int(permnos[j]), corr=row[j], n_overlap=int(n12[i, j]),
                         second_best_corr=row[j2] if np.isfinite(row[j2]) else np.nan,
                         second_permno=int(permnos[j2]), corr6=float(c6[0, 0]),
                         mad12=float(np.median(np.abs(a12[ok] - b12[ok]))),
                         coverage=n12[i, j] / max(ours_n, 1)))
    M = pd.DataFrame(rows)
    M["ok"] = (M["corr"] >= MIN_CORR) & (M["n_overlap"] >= MIN_OVERLAP)
    # 同一個 permno 被兩個 ticker 配到 → 只留相關高的
    dup = M[M["ok"]].sort_values("corr", ascending=False).duplicated("permno", keep="first")
    M["conflict"] = False
    M.loc[dup[dup].index, ["ok", "conflict"]] = [False, True]
    notes = []
    for _, x in M.iterrows():
        nt = []
        if not np.isfinite(x["corr"]):
            nt.append("OSAP 找不到重疊≥36 個月的 permno")
        elif not x["ok"] and not x["conflict"]:
            nt.append(f"最佳相關 {x['corr']:.3f} < {MIN_CORR}，不採用")
        if x["conflict"]:
            nt.append("permno 已被相關更高的 ticker 配走，不採用")
        if np.isfinite(x["second_best_corr"]) and x["second_best_corr"] >= MIN_CORR:
            nt.append(f"次佳 permno {int(x['second_permno'])} 相關也有 {x['second_best_corr']:.3f}"
                      f"（多半是同公司另一股別或前身）")
        if x["ok"] and np.isfinite(x["corr6"]) and x["corr6"] < MIN_CORR:
            nt.append(f"Mom6m 相關只有 {x['corr6']:.3f}")
        if x["ok"] and x["coverage"] < 0.8:
            nt.append(f"只覆蓋我們動能月份的 {x['coverage']:.0%}（可能換過 permno）")
        notes.append("；".join(nt))
    M["note"] = notes
    M.loc[M["ticker"] == "GOOGL", "note"] = (M.loc[M["ticker"] == "GOOGL", "note"] +
                                            "；GOOGL＝Class A（GOOG＝Class C 是另一個 permno，2014-04 起）").str.lstrip("；")
    return M, best_lag


# ───────────────────────── 4. Yahoo 分割 ─────────────────────────

def yahoo_splits(tickers, raw_dir, refresh):
    d = raw_dir / "yahoo_splits"
    d.mkdir(parents=True, exist_ok=True)
    sess = session()
    rows, fail = [], []
    for t in tickers:
        sym = str(t).upper().replace(".", "-")
        f = d / f"{sym}.json"
        if refresh or not f.exists():
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=max&interval=1mo&events=split"
            for attempt in range(3):
                try:
                    r = sess.get(url, timeout=30)
                except requests.RequestException:
                    r = None
                time.sleep(0.6)
                if r is not None and r.status_code == 200:
                    f.write_bytes(r.content)
                    break
                if r is not None and r.status_code == 404:
                    break
                time.sleep(5 * (attempt + 1))
        if not f.exists():
            fail.append(t)
            continue
        try:
            res = json.loads(f.read_text())["chart"]["result"][0]
        except Exception:
            fail.append(t)
            continue
        for ev in (res.get("events") or {}).get("splits", {}).values():
            num, den = float(ev.get("numerator") or 0), float(ev.get("denominator") or 0)
            if num > 0 and den > 0 and abs(num / den - 1) > 1e-9:
                dt = pd.Timestamp(int(ev["date"]), unit="s", tz="UTC").tz_convert("America/New_York").tz_localize(None)
                rows.append(dict(ticker=t, date=dt.normalize(), ratio=num / den))
    S = pd.DataFrame(rows, columns=["ticker", "date", "ratio"]).sort_values(["ticker", "date"])
    return S, fail


def statpers(ym):
    """I/B/E/S 月度彙總的統計日：每月第三個星期五的前一天（星期四）。"""
    first = pd.Timestamp(year=ym // 100, month=ym % 100, day=1)
    fri = 1 + (4 - first.weekday()) % 7
    return first + pd.Timedelta(days=fri + 14 - 1 - 1)


def split_months(S, feps_by_ticker):
    """每次分割「第一個反映新股數的 FEPS 月份」：分割日 ≤ 當月統計日 → 當月，否則下個月；
    再用 FEPS 本身的跳動驗證（跳動倍數 ≈ 1/分割倍數的月份），規則月份明顯不對時改用資料月份。"""
    out, stat = [], {"rule": 0, "data_override": 0, "no_check": 0}
    for _, s in S.iterrows():
        ym0 = s["date"].year * 100 + s["date"].month
        rule = ym0 if s["date"] <= statpers(ym0) else ym_add(ym0, 1)
        first = rule
        f = feps_by_ticker.get(s["ticker"])
        lr = np.log(s["ratio"])
        if f is not None and abs(lr) >= np.log(1.25):
            def jump(c):
                a, b = f.get(ym_add(c, -1)), f.get(c)
                if a is None or b is None or not (a > 0 and b > 0):
                    return np.nan
                return abs(np.log(b / a) + lr)
            cands = [ym_add(rule, k) for k in (-1, 0, 1)]
            errs = [jump(c) for c in cands]
            if np.isfinite(errs).any():
                k = int(np.nanargmin(errs))
                e_rule = errs[1]
                if k != 1 and errs[k] < 0.3 * abs(lr) and not (np.isfinite(e_rule) and e_rule < 0.5 * abs(lr)):
                    first = cands[k]
                    stat["data_override"] += 1
                else:
                    stat["rule"] += 1
            else:
                stat["no_check"] += 1
        else:
            stat["no_check"] += 1
        out.append(first)
    S = S.copy()
    S["first_ym"] = out
    return S, stat


def split_factor(S, keys):
    """keys：ticker, yyyymm。回傳之後所有分割倍數的乘積（今天口徑 ÷ 當時口徑）。"""
    fac = np.ones(len(keys))
    g = S.groupby("ticker")
    tick = keys["ticker"].to_numpy()
    ym = keys["yyyymm"].to_numpy()
    for t, s in g:
        m = tick == t
        if not m.any():
            continue
        f = np.ones(m.sum())
        for fy, r in zip(s["first_ym"], s["ratio"]):
            f = np.where(ym[m] < fy, f * r, f)
        fac[m] = f
    return fac


# ───────────────────────── 5. 抽查 ─────────────────────────

def fy_eps_table(q):
    """季報 → 每家公司每個會計年度的 GAAP 稀釋 EPS（今天股數口徑，四季 ni/sh_now 加總）。
    會計年度底：申報最慢的季末月份（10-K 比 10-Q 晚）。"""
    q = q.copy()
    q["eps"] = q["ni"] / q["sh_now"]
    q["lag"] = (q["filed"] - q["period_end"]).dt.days
    q["pm"] = q["period_end"].dt.month
    out = {}
    for t, g in q.groupby("ticker"):
        g = g.sort_values("period_end").dropna(subset=["eps"])
        if len(g) < 4:
            continue
        fm = g.groupby("pm")["lag"].median().idxmax()
        ends = g[g["pm"] == fm]["period_end"]
        rows = []
        for e in ends:
            w = g[(g["period_end"] > e - pd.Timedelta(days=360)) & (g["period_end"] <= e)]
            if len(w) == 4:
                rows.append((e, w["eps"].sum()))
        out[t] = rows
    return out


def fy1_eps(fy, t, ym):
    """FY1＝統計日前 30 天之後才結束的第一個會計年度（大致就是 I/B/E/S 當月的 FY1）。"""
    sp = statpers(ym) - pd.Timedelta(days=30)
    for e, v in fy.get(t, []):
        if e >= sp:
            return e, v
    return None, np.nan


# ───────────────────────── main ─────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw-dir", type=Path, default=None)
    ap.add_argument("--release", default="202510")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--wait-min", type=float, default=0)
    ap.add_argument("--download-only", action="store_true")
    ap.add_argument("--splits-only", action="store_true")
    a = ap.parse_args()
    raw = (a.raw_dir or default_raw_dir()).resolve()
    raw.mkdir(parents=True, exist_ok=True)
    print(f"[osap_fetch] release {a.release}  raw dir: {raw}")

    prices = pd.read_csv(DATA / "prices_monthly_sp500.csv", parse_dates=["month"])
    prices["ym"] = prices["month"].dt.year * 100 + prices["month"].dt.month
    tickers = sorted(prices["ticker"].unique())

    if a.splits_only:
        S, fail = yahoo_splits(tickers, raw, a.refresh)
        print(f"  [splits] {len(S)} 筆分割事件、{S['ticker'].nunique()} 家；抓不到：{fail}")
        return
    files = download_all(a.release, raw, a.refresh, a.wait_min)
    if a.download_only:
        print("  [dl] 完成：", ", ".join(f"{k} {p.stat().st_size / 1e6:.0f}MB" for k, p in files.items()))
        return

    OUT.mkdir(parents=True, exist_ok=True)
    doc = signal_doc(files["SignalDoc"])
    doc.to_csv(OUT / "signal_doc_excerpt.csv", index=False)
    for _, x in doc.iterrows():
        print(f"  [doc] {x['Acronym']}: {x.get('LongDescription', '')} | {str(x.get('Detailed Definition', ''))[:160]}")

    print("  [load] 讀 OSAP 訊號 …", flush=True)
    sig = {k: load_signal(files[k], k, 200001) for k in SIGNALS if k in files}
    for k, d in sig.items():
        print(f"    {k}: {len(d):,} 列（2000 年起）、{d['permno'].nunique():,} 個 permno、{d['yyyymm'].min()}～{d['yyyymm'].max()}")

    # 3. 配對
    M, best_lag = match_permnos(prices, sig["Mom12m"], sig["Mom6m"])
    ok = M[M["ok"]]
    print(f"  [配對] 成功 {len(ok)}／{len(tickers)} 家（{len(ok) / len(tickers):.1%}）；"
          f"相關中位數 {ok['corr'].median():.4f}，最低 {ok['corr'].min():.4f}")
    cols = ["ticker", "permno", "corr", "n_overlap", "second_best_corr", "note",
            "second_permno", "corr6", "mad12", "coverage", "ok"]
    Mo = M[cols].copy()
    Mo["permno"] = Mo["permno"].astype("Int64")
    Mo.round({"corr": 4, "second_best_corr": 4, "corr6": 4, "mad12": 4, "coverage": 3}).to_csv(
        OUT / "permno_map.csv", index=False)

    # 4. FEPS 面板
    base = sig["FEPS"].rename(columns={"FEPS": "feps_raw"})
    for k, c in (("AnalystRevision", "analyst_revision"), ("fgr5yrLag", "fgr5y")):
        if k in sig:
            base = base.merge(sig[k].rename(columns={k: c}), on=["permno", "yyyymm"], how="outer")
        else:
            base[c] = np.nan
    pm = ok[["ticker", "permno"]].astype({"permno": "int64"})
    F = pm.merge(base, on="permno", how="inner")
    F = F[F["yyyymm"] >= YM_MIN].sort_values(["ticker", "yyyymm"]).reset_index(drop=True)

    S, fail = yahoo_splits(sorted(pm["ticker"]), raw, a.refresh)
    feps_by = {t: dict(zip(g["yyyymm"], g["feps_raw"])) for t, g in F.dropna(subset=["feps_raw"]).groupby("ticker")}
    S, sstat = split_months(S, feps_by)
    print(f"  [分割] Yahoo：{len(S)} 筆分割、{S['ticker'].nunique()} 家（抓不到：{fail or '無'}）；"
          f"月份判定：規則 {sstat['rule']}、FEPS 跳動改判 {sstat['data_override']}、無法驗證 {sstat['no_check']}")
    F["split_factor"] = split_factor(S, F[["ticker", "yyyymm"]])
    F["feps"] = F["feps_raw"] / F["split_factor"]

    # 分割調整診斷：相鄰月份 FEPS 跳超過 2.5 倍的次數（調整前 vs 後）
    def big_jumps(col):
        g = F.dropna(subset=[col])
        g = g[g[col] > 0]
        prev = g.groupby("ticker")[col].shift(1)
        same = g.groupby("ticker")["yyyymm"].shift(1).map(lambda v: ym_add(int(v), 1) if pd.notna(v) else -1) == g["yyyymm"]
        return int((np.abs(np.log(g[col] / prev)) > np.log(2.5))[same].sum())
    print(f"  [診斷] 相鄰月份 FEPS 跳 >2.5 倍：調整前 {big_jumps('feps_raw')} 次 → 調整後 {big_jumps('feps')} 次")

    # Yahoo 分割 vs 季報 split_fac（2009 年起的累積倍數）交叉核對
    q = pd.read_csv(DATA / "quarters_sp500.csv", parse_dates=["period_end", "filed", "avail"])
    q09 = q[q["period_end"] >= "2009-01-01"].sort_values("period_end").groupby("ticker").first()
    mism = []
    for t in pm["ticker"]:
        if t not in q09.index:
            continue
        e = q09.loc[t, "period_end"]
        y = S[(S["ticker"] == t) & (S["date"] > e)]["ratio"].prod()
        sf = q09.loc[t, "split_fac"]
        if np.isfinite(sf) and sf > 0 and abs(np.log(y / sf)) > 0.05:
            mism.append(f"{t}(Yahoo {y:g} vs 季報 {sf:g})")
    print(f"  [核對] Yahoo 累積分割 vs 季報 split_fac 不一致：{len(mism)} 家 {mism[:12]}")

    outc = ["ticker", "permno", "yyyymm", "feps_raw", "split_factor", "feps", "analyst_revision", "fgr5y"]
    F = F[outc]
    F.to_csv(OUT / "feps_sp500.csv.gz", index=False, float_format="%.6g", compression="gzip")

    # 5. 抽查
    fy = fy_eps_table(q)
    spot = []
    for t in SPOT:
        r = M[M["ticker"] == t]
        if r.empty:
            continue
        r = r.iloc[0]
        d = {"ticker": t, "permno": r["permno"], "corr": round(r["corr"], 4),
             "second_best_corr": round(r["second_best_corr"], 4), "ok": bool(r["ok"])}
        for ym in (201501, 202301):
            v = F[(F["ticker"] == t) & (F["yyyymm"] == ym)]
            d[f"feps_{ym}"] = float(v["feps"].iloc[0]) if len(v) else np.nan
            e, g = fy1_eps(fy, t, ym)
            d[f"gaap_fy_{ym}"] = g
            d[f"fye_{ym}"] = e.date().isoformat() if e is not None else ""
            d[f"ratio_{ym}"] = d[f"feps_{ym}"] / g if np.isfinite(g) and g != 0 else np.nan
        spot.append(d)
    SP = pd.DataFrame(spot)
    SP.to_csv(OUT / "spot_check.csv", index=False, float_format="%.4g")

    # AAPL / NVDA 逐年：每年 1 月的 FEPS vs 當年 GAAP EPS
    for t in ("AAPL", "NVDA"):
        line = []
        for y in range(2010, 2026):
            ym = y * 100 + 1
            v = F[(F["ticker"] == t) & (F["yyyymm"] == ym)]
            if not len(v):
                continue
            e, g = fy1_eps(fy, t, ym)
            line.append(f"{y}:{v['feps'].iloc[0]:.2f}/{g:.2f}(×{v['split_factor'].iloc[0]:g})")
        print(f"  [分割抽查] {t} 1 月 FEPS/GAAP（×分割係數）：" + " ".join(line))

    sz = (OUT / "feps_sp500.csv.gz").stat().st_size
    print(f"  [輸出] {OUT / 'feps_sp500.csv.gz'}：{len(F):,} 列、{F['ticker'].nunique()} 家、"
          f"{F['yyyymm'].min()}～{F['yyyymm'].max()}、{sz / 1e6:.2f} MB")
    print(f"  [輸出] FEPS 非空 {F['feps'].notna().sum():,}、analyst_revision 非空 {F['analyst_revision'].notna().sum():,}、"
          f"fgr5y 非空 {F['fgr5y'].notna().sum():,}；每家 FEPS 最後月份中位數 "
          f"{int(F.dropna(subset=['feps']).groupby('ticker')['yyyymm'].max().median())}")
    print(f"  [輸出] {OUT / 'permno_map.csv'}：配對成功 {len(ok)}／{len(tickers)}（{len(ok) / len(tickers):.1%}）")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(SP[["ticker", "permno", "corr", "second_best_corr", "feps_201501", "gaap_fy_201501",
                  "feps_202301", "gaap_fy_202301"]].to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
