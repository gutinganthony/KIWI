#!/usr/bin/env python3
"""讀取本地日線 CSV → 跑 EMA20/50 交叉回測 → 產出 1/3/6/12/24 個月績效表。

不碰網路。價格 CSV 由 fetch_prices.py（在 GitHub Actions runner 上）產出。

用法:
  python3 run_report.py --prices data/prices --out results
  python3 run_report.py --prices ../avi-v5/data/ext --out results/smoke   # 煙霧測試
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date
from pathlib import Path

import numpy as np

from ema_backtest import max_drawdown, run_backtest, window_metrics

WINDOWS = [("1M", 1), ("3M", 3), ("6M", 6), ("12M", 12), ("24M", 24)]


# --------------------------------------------------------------------------
def months_before(d: date, months: int) -> date:
    """d 往前推 n 個月（月底日不存在時退到該月最後一天）。"""
    y, m = d.year, d.month - months
    while m <= 0:
        m += 12
        y -= 1
    day = d.day
    while day > 0:
        try:
            return date(y, m, day)
        except ValueError:
            day -= 1
    raise ValueError("unreachable")


def load_csv(path: Path):
    """回傳 (symbol, dates[list[date]], open[np], close[np])。

    支援兩種欄位配置:
      - auto_adjust 後的 Date,Open,High,Low,Close,Volume（fetch_prices.py 產出）
      - Yahoo 原始 Date,Open,High,Low,Close,Adj Close,Volume
        → 用 AdjClose/Close 比例把 Open 一併調整，確保開盤/收盤同一套除權息基準
    """
    dates, op, cl = [], [], []
    with path.open(newline="") as f:
        rd = csv.DictReader(f)
        cols = {c.lower().replace(" ", ""): c for c in (rd.fieldnames or [])}
        if "date" not in cols or "close" not in cols or "open" not in cols:
            return None
        adj_col = cols.get("adjclose")
        for row in rd:
            try:
                d = date.fromisoformat(row[cols["date"]][:10])
                o = float(row[cols["open"]])
                c = float(row[cols["close"]])
            except (ValueError, TypeError, KeyError):
                continue
            if not (math.isfinite(o) and math.isfinite(c)) or c <= 0 or o <= 0:
                continue
            if adj_col:
                try:
                    a = float(row[adj_col])
                    if math.isfinite(a) and a > 0:
                        o *= a / c
                        c = a
                except (ValueError, TypeError):
                    pass
            dates.append(d)
            op.append(o)
            cl.append(c)
    if len(dates) < 60:
        return None
    order = np.argsort(np.array(dates))
    dates = [dates[i] for i in order]
    return path.stem, dates, np.array(op)[order], np.array(cl)[order]


# --------------------------------------------------------------------------
def analyse(symbol, dates, op, cl, cost_bps=0.0, fill="next_open", slow_warmup=50):
    sim = run_backtest(dates, op, cl, fill=fill, cost_bps=cost_bps)
    eq, im, tr = sim["equity"], sim["in_market"], sim["trades"]
    last = dates[-1]
    n = len(dates)

    rec = {
        "symbol": symbol,
        "first_date": dates[0].isoformat(),
        "last_date": last.isoformat(),
        "bars": n,
        "currently_long": bool(im[-1]),
        "full_sample": {
            "strat_return": float(eq[-1] - 1.0),
            "bh_return": float(cl[-1] / cl[0] - 1.0),
            "strat_mdd": max_drawdown(eq),
            "bh_mdd": max_drawdown(cl),
            "n_trades": len(tr),
            "exposure": float(np.mean(im)),
        },
        "windows": {},
    }

    # 逐年拆解：用來判斷「全樣本優勢」是可重複的，還是靠某一兩年撐起來的。
    # 這是「能不能真的拿去交易」最關鍵的一張表——全樣本數字漂亮但只有一年
    # 貢獻全部超額，等於沒有優勢。
    years = sorted({d.year for d in dates})
    for y in years:
        ridx = [i for i, d in enumerate(dates) if d.year == y]
        if len(ridx) < 60 or ridx[0] < slow_warmup:
            continue
        m = window_metrics(eq, cl, im, tr, ridx[0], ridx[-1])
        if m:
            m.pop("bars", None)
            rec.setdefault("annual", {})[str(y)] = m

    for label, months in WINDOWS:
        cutoff = months_before(last, months)
        # 資料起點晚於窗起點 → 這檔根本沒有這個窗的歷史。若照算會把「上市
        # 至今」偽裝成「過去 24 個月」，是最容易產生假數字的地方，直接留空。
        # 另外要求 warm-up：窗起點前需有 slow(50) 根資料，否則窗內訊號不可信。
        idx = [i for i, d in enumerate(dates) if d >= cutoff]
        if not idx or len(idx) < 15 or dates[0] > cutoff or idx[0] < slow_warmup:
            rec["windows"][label] = {}
            continue
        m = window_metrics(eq, cl, im, tr, idx[0], n - 1)
        if m:
            m["start_date"] = dates[idx[0]].isoformat()
        rec["windows"][label] = m
    return rec


# --------------------------------------------------------------------------
def pct(x, nd=1):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "n/a"
    return f"{x*100:+.{nd}f}%"


def ratio(x, nd=0):
    """比例（勝率、在場比例）——不加正負號。"""
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "n/a"
    return f"{x*100:.{nd}f}%"


def render_table(records, window_label, top=0):
    rows = []
    for r in records:
        w = r["windows"].get(window_label) or {}
        if not w:
            continue
        rows.append((r["symbol"], w))
    rows.sort(key=lambda t: t[1]["excess"], reverse=True)
    note = ""
    if top and len(rows) > 2 * top:
        note = f"（共 {len(rows)} 檔，只列超額最高/最低各 {top} 檔）"
        rows = rows[:top] + [("…", None)] + rows[-top:]
    out = [
        f"### {window_label} {note}",
        "",
        "| 標的 | 策略報酬 | 買入持有 | 超額 | 策略MDD | B&H MDD | 交易數 | 勝率 | 在場比例 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for sym, w in rows:
        if w is None:
            out.append("| … | | | | | | | | |")
            continue
        out.append(
            f"| {sym} | {pct(w['strat_return'])} | {pct(w['bh_return'])} | "
            f"{pct(w['excess'])} | {pct(w['strat_mdd'])} | {pct(w['bh_mdd'])} | "
            f"{w['n_trades']} | {ratio(w['win_rate'])} | {w['exposure']*100:.0f}% |"
        )
    return "\n".join(out)


def summarise(records, window_label):
    """跨標的彙總——回答「這策略整體有沒有效」，而不是挑幾檔好看的講。"""
    ws = [r["windows"].get(window_label) for r in records]
    ws = [w for w in ws if w]
    if not ws:
        return None
    sr = np.array([w["strat_return"] for w in ws])
    bh = np.array([w["bh_return"] for w in ws])
    ex = np.array([w["excess"] for w in ws])
    smdd = np.array([w["strat_mdd"] for w in ws])
    bmdd = np.array([w["bh_mdd"] for w in ws])
    nt = np.array([w["n_trades"] for w in ws])
    wr = np.array([w["win_rate"] for w in ws])
    return {
        "n": len(ws),
        "median_strat_return": float(np.median(sr)),
        "median_bh_return": float(np.median(bh)),
        "mean_excess": float(np.mean(ex)),
        "median_excess": float(np.median(ex)),
        "pct_beat_bh": float(np.mean(ex > 0)),
        "pct_positive": float(np.mean(sr > 0)),
        "median_strat_mdd": float(np.median(smdd)),
        "median_bh_mdd": float(np.median(bmdd)),
        "pct_mdd_improved": float(np.mean(smdd > bmdd)),
        "median_n_trades": float(np.median(nt)),
        "median_win_rate": float(np.nanmedian(wr)) if np.any(np.isfinite(wr)) else float("nan"),
    }


def render_summary(records):
    out = [
        "## 跨標的彙總（中位數）",
        "",
        "| 窗 | 檔數 | 策略報酬 | 買入持有 | 平均超額 | 勝過B&H比例 | 策略MDD | B&H MDD | MDD較淺比例 | 交易數 | 單筆勝率 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for label, _ in WINDOWS:
        s = summarise(records, label)
        if not s:
            continue
        out.append(
            f"| {label} | {s['n']} | {pct(s['median_strat_return'])} | "
            f"{pct(s['median_bh_return'])} | {pct(s['mean_excess'])} | "
            f"{ratio(s['pct_beat_bh'])} | {pct(s['median_strat_mdd'])} | "
            f"{pct(s['median_bh_mdd'])} | {ratio(s['pct_mdd_improved'])} | "
            f"{s['median_n_trades']:.0f} | {ratio(s['median_win_rate'])} |"
        )
    return "\n".join(out)


def round_floats(obj, nd=6):
    """縮小 JSON 體積（3,000 檔時差很多），順便避免無意義的浮點尾數。"""
    if isinstance(obj, float):
        return None if not math.isfinite(obj) else round(obj, nd)
    if isinstance(obj, dict):
        return {k: round_floats(v, nd) for k, v in obj.items()}
    if isinstance(obj, list):
        return [round_floats(v, nd) for v in obj]
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cost-bps", type=float, default=0.0)
    ap.add_argument("--fill", default="next_open", choices=["next_open", "close"])
    ap.add_argument("--tag", default="results", help="輸出檔名前綴")
    ap.add_argument("--top", type=int, default=0,
                    help=">0 時 markdown 表格只列超額最高/最低各 N 檔")
    args = ap.parse_args()

    pdir = Path(args.prices)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    records, skipped = [], []
    for p in sorted(pdir.glob("*.csv")):
        loaded = load_csv(p)
        if loaded is None:
            skipped.append(p.name)
            continue
        records.append(analyse(*loaded, cost_bps=args.cost_bps, fill=args.fill))

    payload = {
        "generated_at": date.today().isoformat(),
        "params": {
            "fast": 20, "slow": 50, "fill": args.fill,
            "cost_bps_per_side": args.cost_bps, "long_only": True, "weight": 1.0,
        },
        "n_symbols": len(records),
        "skipped": skipped,
        "summary": {lb: summarise(records, lb) for lb, _ in WINDOWS},
        "records": records,
    }
    tag = args.tag or "results"
    (out / f"{tag}.json").write_text(
        json.dumps(round_floats(payload), separators=(",", ":"))
    )

    md = [
        f"# EMA20/50 交叉回測結果（{len(records)} 檔）",
        "",
        f"成交假設：{args.fill}　單邊成本：{args.cost_bps} bps　"
        f"產生日期：{payload['generated_at']}",
        "",
        render_summary(records),
        "",
    ]
    for label, _ in WINDOWS:
        md.append(render_table(records, label, top=args.top))
        md.append("")
    (out / f"{tag}.md").write_text("\n".join(md))

    print(f"{len(records)} symbols → {out}/{tag}.json  (skipped: {len(skipped)})")
    for label, _ in WINDOWS:
        s = summarise(records, label)
        if s:
            print(f"  {label}: 中位策略 {pct(s['median_strat_return'])} vs "
                  f"B&H {pct(s['median_bh_return'])}, "
                  f"勝過B&H {ratio(s['pct_beat_bh'])}, "
                  f"中位MDD {pct(s['median_strat_mdd'])} vs {pct(s['median_bh_mdd'])}")


if __name__ == "__main__":
    main()
