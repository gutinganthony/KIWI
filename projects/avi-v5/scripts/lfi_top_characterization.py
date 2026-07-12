#!/usr/bin/env python3
"""LFI 見頂特徵統計：LFI 到多少以上 → 幾天/幾週後市場見頂 → 跌幅多大 → 維持多久。

回答使用者問題 #2：以 LFI（槓桿融資擁擠度，dashboard 第四錶）為條件，量化
「事件後市場多久見頂、跌幅深度、下跌持續時間、回復時間」的平均數 AND 中位數。

資料現實（誠實交代，見報告 §資料）：LFI 四原料中 VVIX(2006)、HYG(2007) 才誕生，
加上 3 年 z 暖機 → 真 LFI 最早只能到 **2009-04**。1998/2008 用此公式無法觸及。
本腳本用「本地 backtest CSV + data/ext」拼接出 2009-2026 的最長真 LFI（~17 年、
涵蓋 2011/2015/2018Q4/2020/2022/2025/2026 約 7 次大頂）。

事件定義：LFI_pctl 由 <T 上穿 ≥T（rising crossing，抓「擁擠正在堆積」的時刻），
去叢集 GAP 交易日。對每個事件：
  - days_to_top：event 起 W_TOP 天內 SPY 收盤最高點的位移（= 見頂需時）
  - drawdown   ：該頂點起 W_DD 天內最低收盤 / 頂點 − 1（= 跌幅深度）
  - duration   ：頂點到谷底的交易日數（= 下跌維持多久）
  - recovery   ：谷底回到頂點價位的交易日數（W_REC 內未回復記為 >W_REC）
輸出各門檻（80/85/90/95）的 事件數 n、命中率（後續跌 ≥5%/≥10%）、
以及上述四項的 平均數/中位數，並對照「隨機日」無條件基準。

用法：python3 scripts/lfi_top_characterization.py [--pickle <spliced.pkl>]
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "backtest"
sys.path.insert(0, str(ROOT / "src"))
from lfi import compute_lfi_series  # noqa: E402

THRESHOLDS = [80, 85, 90, 95]
GAP = 21          # 去叢集交易日
W_TOP = 63        # 找頂窗（~3 個月）
W_DD = 189        # 頂點後找谷窗（~9 個月）
W_REC = 378       # 回復窗（~1.5 年）
SEED = 42


def cboe(path, cands):
    df = pd.read_csv(path); df.columns = [c.strip().upper() for c in df.columns]
    df["DATE"] = pd.to_datetime(df["DATE"], format="mixed")
    df = df.set_index("DATE").sort_index()
    for v in cands:
        if v in df.columns:
            return df[v].astype(float)
    return df.iloc[:, -1].astype(float)


def yhoo(path):
    df = pd.read_csv(path); dc = [c for c in df.columns if c.lower() == "date"][0]
    df[dc] = pd.to_datetime(df[dc]); df = df.set_index(dc).sort_index()
    return (df["Adj Close"] if "Adj Close" in df.columns else df["Close"]).astype(float)


def load_spliced(pickle_path):
    if pickle_path and Path(pickle_path).exists():
        d = pickle.load(open(pickle_path, "rb"))
        return d["spy"], d["lfi"]
    raise SystemExit("需要先產生 spliced pickle（見 scratchpad 準備步驟）或改用 --pickle")


def decluster(idx, gap=GAP):
    kept, last = [], None
    for d in idx:
        if last is None or (d - last).days > gap * 1.4:
            kept.append(d); last = d
    return kept


def characterize(spy, lfi, thr):
    """回傳事件層級 DataFrame。"""
    common = spy.index.intersection(lfi.index)
    p = lfi.loc[common]; s = spy.loc[common]
    above = p >= thr
    crossings = p.index[above & ~above.shift(1, fill_value=False)]  # <T → >=T 上穿
    events = decluster(list(crossings))
    rows = []
    arr = s.values
    dates = list(s.index)
    pos = {d: i for i, d in enumerate(dates)}
    n = len(arr)
    for d in events:
        i = pos[d]
        top_hi = min(i + W_TOP, n - 1)
        if top_hi <= i:
            continue
        top_off = int(np.argmax(arr[i:top_hi + 1]))
        top_i = i + top_off
        top_px = arr[top_i]
        dd_hi = min(top_i + W_DD, n - 1)
        if dd_hi <= top_i:
            continue
        tr_off = int(np.argmin(arr[top_i:dd_hi + 1]))
        tr_i = top_i + tr_off
        tr_px = arr[tr_i]
        drawdown = tr_px / top_px - 1.0
        duration = tr_i - top_i
        # recovery：谷底後回到 top_px
        rec_hi = min(tr_i + W_REC, n - 1)
        rec = np.nan
        seg = arr[tr_i:rec_hi + 1]
        hit = np.where(seg >= top_px)[0]
        if len(hit):
            rec = int(hit[0])
        rows.append(dict(event=str(d.date()), lfi=round(float(p.loc[d]), 1),
                         days_to_top=top_off, drawdown=drawdown,
                         duration=duration, recovery=rec if not np.isnan(rec) else np.nan,
                         top=str(dates[top_i].date()), trough=str(dates[tr_i].date())))
    return pd.DataFrame(rows)


def baseline_maxdd(spy, lfi, rng, n_draw=4000):
    """無條件基準：隨機日之後 W_TOP→W_DD 期間的典型跌幅（同定義）＋命中率。"""
    common = spy.index.intersection(lfi.index)
    s = spy.loc[common]; arr = s.values; n = len(arr)
    dds = []
    for _ in range(n_draw):
        i = rng.integers(0, n - W_TOP - W_DD - 1)
        top_i = i + int(np.argmax(arr[i:i + W_TOP + 1]))
        tr = arr[top_i:top_i + W_DD + 1]
        dds.append(tr.min() / arr[top_i] - 1)
    dds = np.array(dds)
    return dict(mean=dds.mean(), median=np.median(dds),
                hit5=float((dds <= -0.05).mean()), hit10=float((dds <= -0.10).mean()))


def decile_view(spy, lfi):
    """逐日觀點：把每一天按 LFI 分十等分，看各分位「往後同窗最大回落」的中位/平均。
    比事件穿越法更能顯示『LFI 越高 → 跌幅是否越大』的單調關係（或缺乏之）。"""
    common = spy.index.intersection(lfi.index)
    s = spy.loc[common]; p = lfi.loc[common]
    arr = s.values; n = len(arr)
    fwd_dd = np.full(n, np.nan)
    for i in range(n - W_TOP - W_DD - 1):
        top_i = i + int(np.argmax(arr[i:i + W_TOP + 1]))
        tr = arr[top_i:top_i + W_DD + 1]
        fwd_dd[i] = tr.min() / arr[top_i] - 1
    dfd = pd.DataFrame({"lfi": p.values, "dd": fwd_dd}).dropna()
    dfd["bucket"] = pd.cut(dfd["lfi"], bins=[0, 20, 40, 60, 80, 90, 101],
                           labels=["0-20", "20-40", "40-60", "60-80", "80-90", "90-100"],
                           right=False)
    g = dfd.groupby("bucket", observed=True)["dd"]
    return g.agg(["count", "mean", "median",
                  lambda x: (x <= -0.05).mean(), lambda x: (x <= -0.10).mean()])


def fmt(v, pct=False, d=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "  --"
    return f"{v*100:+.{d}f}%" if pct else f"{v:.{d}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pickle", default="/tmp/claude-0/-home-user-KIWI/c150ed96-6dc7-5c63-a2f3-cdfcfbc2155e/scratchpad/lfi_long.pkl")
    ap.add_argument("--json-out", default="/tmp/lfi_top_char.json")
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)

    spy, lfi = load_spliced(args.pickle)
    print(f"樣本：LFI {lfi.index[0].date()} → {lfi.index[-1].date()}（n={len(lfi)} 交易日）")
    b = baseline_maxdd(spy, lfi, rng)
    b_mean, b_med = b["mean"], b["median"]
    print(f"無條件基準（隨機日後同窗最大回落）：平均 {b_mean*100:+.1f}%　中位 {b_med*100:+.1f}%"
          f"　｜跌≥5%={b['hit5']*100:.0f}%　跌≥10%={b['hit10']*100:.0f}%\n")

    print("=" * 104)
    print(f"{'門檻':>4} {'事件n':>5} {'跌≥5%':>6} {'跌≥10%':>7} │ "
          f"{'見頂需時(交易日)':>16} │ {'跌幅深度':>14} │ {'下跌維持(交易日)':>16} │ {'回復(交易日)':>12}")
    print(f"{'':>4} {'':>5} {'命中率':>6} {'命中率':>7} │ {'平均 / 中位':>16} │ {'平均 / 中位':>14} │ {'平均 / 中位':>16} │ {'平均 / 中位':>12}")
    print("-" * 104)
    out = {}
    for thr in THRESHOLDS:
        df = characterize(spy, lfi, thr)
        if len(df) == 0:
            print(f"{thr:>4}  （無事件）"); continue
        n = len(df)
        hit5 = (df.drawdown <= -0.05).mean()
        hit10 = (df.drawdown <= -0.10).mean()
        censored = int((df.days_to_top >= W_TOP).sum())  # 見頂需時被 63d 窗截斷的次數
        dtt_m, dtt_md = df.days_to_top.mean(), df.days_to_top.median()
        dd_m, dd_md = df.drawdown.mean(), df.drawdown.median()
        dur_m, dur_md = df.duration.mean(), df.duration.median()
        rec = df.recovery.dropna()
        rec_m = rec.mean() if len(rec) else np.nan
        rec_md = rec.median() if len(rec) else np.nan
        rec_note = "" if len(rec) == n else f"({n-len(rec)}次未回復)"
        print(f"{thr:>4} {n:>5} {hit5*100:>5.0f}% {hit10*100:>6.0f}% │ "
              f"{dtt_m:>6.0f} / {dtt_md:>4.0f}      │ "
              f"{fmt(dd_m,1,1):>6} / {fmt(dd_md,1,1):>6} │ "
              f"{dur_m:>6.0f} / {dur_md:>4.0f}      │ "
              f"{fmt(rec_m,0,0):>5}/{fmt(rec_md,0,0):>4} {rec_note}")
        out[thr] = dict(n=n, hit5=round(float(hit5), 3), hit10=round(float(hit10), 3),
                        days_to_top_censored=censored,
                        days_to_top_mean=round(float(dtt_m), 1), days_to_top_median=float(dtt_md),
                        drawdown_mean=round(float(dd_m), 4), drawdown_median=round(float(dd_md), 4),
                        duration_mean=round(float(dur_m), 1), duration_median=float(dur_md),
                        recovery_mean=None if np.isnan(rec_m) else round(float(rec_m), 1),
                        recovery_median=None if np.isnan(rec_md) else float(rec_md),
                        events=df.to_dict("records"))
    print("=" * 104)
    print("註：見頂需時=事件後至 SPY 局部高點的交易日；跌幅=該高點→後續最低收盤；"
          "下跌維持=高點→谷底交易日；回復=谷底回到高點價位交易日。5交易日≈1週。")

    # 見頂需時的截斷警告：多少事件的「頂」落在 63d 窗邊界（=真頂更晚，見頂需時被低估）
    print("\n見頂需時截斷檢查（頂落在 +63d 窗邊界 = 市場仍在漲、真頂更晚）：")
    for thr in THRESHOLDS:
        o = out.get(thr)
        if o:
            print(f"  LFI≥{thr}：{o['days_to_top_censored']}/{o['n']} 事件被截斷 "
                  f"（{o['days_to_top_censored']/o['n']*100:.0f}%）→ 見頂需時是「下限」不是精確值")

    # 逐日分位觀點（單調性檢定）
    dv = decile_view(spy, lfi)
    print("\n" + "=" * 84)
    print("逐日分位觀點：把每日按 LFI 分桶 → 往後同窗『最大回落』（單調性檢定）")
    print("=" * 84)
    print(f"{'LFI 桶':>8} {'天數':>6} {'跌幅平均':>9} {'跌幅中位':>9} {'跌≥5%':>7} {'跌≥10%':>7}")
    for bkt, r in dv.iterrows():
        print(f"{str(bkt):>8} {int(r['count']):>6} {r['mean']*100:>+8.1f}% {r['median']*100:>+8.1f}% "
              f"{r.iloc[3]*100:>6.0f}% {r.iloc[4]*100:>6.0f}%")
    print(f"{'(基準)':>8} {'--':>6} {b_mean*100:>+8.1f}% {b_med*100:>+8.1f}% "
          f"{b['hit5']*100:>6.0f}% {b['hit10']*100:>6.0f}%")

    # 逐事件明細（≥90）
    df90 = characterize(spy, lfi, 90)
    if len(df90):
        print("\n── LFI≥90 逐事件明細 ──")
        for _, r in df90.iterrows():
            print(f"  {r.event} (LFI {r.lfi:.0f}) → 頂 {r.top}(+{int(r.days_to_top)}d) "
                  f"跌 {r.drawdown*100:+.1f}% 至 {r.trough} 歷 {int(r.duration)}d "
                  f"回復 {int(r.recovery) if not np.isnan(r.recovery) else '>窗'}d")

    import json
    json.dump({"sample": [str(lfi.index[0].date()), str(lfi.index[-1].date()), len(lfi)],
               "baseline_maxdd_mean": round(float(b_mean), 4), "baseline_maxdd_median": round(float(b_med), 4),
               "by_threshold": out}, open(args.json_out, "w"), indent=1, default=str)
    print(f"\nJSON → {args.json_out}")


if __name__ == "__main__":
    main()
