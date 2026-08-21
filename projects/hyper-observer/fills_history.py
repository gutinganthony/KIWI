#!/usr/bin/env python3
"""每日成交歷史累積器（唯讀）——突破 userFills 單次 2000 筆上限。

背景（2026-08-11，對追蹤錢包 0x8bae35 分析 xyz 股票部位時踩到的限制）
  userFills／userFillsByTime 單次最多回 2000 筆，高頻標的幾天內就吃光這個上限。
  當時只能算出 10.2 天的樣本，完整回合只有 4 個——樣本量小到下不了「長期勝率」
  這種結論。這支腳本每天對 config.TRACKED_WALLETS 做「增量」抓取（只抓上次歷史
  之後的新成交），逐日累積出遠超單次窗口的樣本。

儲存設計
  data/tracked/{addr}/fills_history.jsonl —— 每行一筆成交，**陣列格式**（非
  dict）省空間：欄位順序見 FILL_ROW_FIELDS，用 _fill_to_row/_row_to_fill 轉換。
  保留 config.FILLS_HISTORY_RETENTION_DAYS 天（預設 180 天＝約 6 個月），到期直接
  捨棄——這是刻意的取捨：不做月結彙總，換取實作簡單；180 天遠超過「兩週後看長期
  勝率」的原始需求，若之後真的需要更長，屆時再加彙總層。
  data/tracked/{addr}/fills_history_stats.json —— 上面那份歷史的聚合統計快照
  （全體＋依 dex 前綴分組的 round_trip_stats），給人看／給其他腳本讀，不必碰
  jsonl 本體。

首次執行的種子來源（依序）
  1. 同目錄下 fetch.py 已產出的 latest_raw.json（今天的每日快照）——**零額外請求**。
  2. 沒有的話才打 API 回填 FILLS_HISTORY_BACKFILL_DAYS 天。

去重：以 tid（Hyperliquid 的成交 id）為鍵；tid 缺失時退回
  (ts, coin, px, sz, dir) 組合鍵。

唯讀保證：只 POST config.INFO_URL 的 userFillsByTime 查詢。無下單、無簽章、
無私鑰，不引用交易端點。

用法（在 projects/hyper-observer 下）：
  python3 fills_history.py                       # 對所有 TRACKED_WALLETS 各跑一次
  python3 fills_history.py --address 0x...        # 只跑一個
  python3 fills_history.py --query --address 0x... [--dex xyz]
                                                    # 只讀本地歷史印統計，不打網路
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import classify   # noqa: E402
import config     # noqa: E402
import fetch      # noqa: E402

HISTORY_FILENAME = "fills_history.jsonl"
STATS_FILENAME = "fills_history_stats.json"

# jsonl 每行的欄位順序（陣列格式，省去重複的 key 名稱）。新增欄位一律加在**尾端**，
# 讀舊行時缺的欄位補 None——這樣才能在不打散既有歷史檔的前提下擴充格式。
FILL_ROW_FIELDS = ("ts", "coin", "px", "sz", "side", "closed_pnl", "fee", "dir",
                   "is_liquidation", "start_position", "tid")


def _fill_to_row(fill):
    return [fill.get("ts"), fill.get("coin"), fill.get("px"), fill.get("sz"),
            fill.get("side"), fill.get("closed_pnl"), fill.get("fee"), fill.get("dir"),
            1 if fill.get("is_liquidation") else 0, fill.get("start_position"),
            fill.get("tid")]


def _row_to_fill(row):
    row = list(row) + [None] * (len(FILL_ROW_FIELDS) - len(row))  # 舊格式缺尾欄位補 None
    d = dict(zip(FILL_ROW_FIELDS, row))
    d["is_liquidation"] = bool(d["is_liquidation"])
    return d


def _fill_key(fill):
    """去重鍵：tid 優先；缺失（理論上不會，防禦用）退回內容組合鍵。"""
    if fill.get("tid") is not None:
        return ("tid", fill["tid"])
    return ("k", fill.get("ts"), fill.get("coin"), fill.get("px"),
            fill.get("sz"), fill.get("dir"))


# ---------------------------------------------------------------------------
# 歷史檔讀寫
# ---------------------------------------------------------------------------

def load_history(path):
    """回 (fills, max_ts)。檔案不存在或整段是空的 → ([], None)。

    壞掉的單行（可能寫到一半被中斷）直接跳過，不讓一行壞資料毀掉整份歷史。
    """
    if not os.path.exists(path):
        return [], None
    fills = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, list) or len(row) < 2:
                continue
            fills.append(_row_to_fill(row))
    ts_vals = [f["ts"] for f in fills if f["ts"] is not None]
    return fills, (max(ts_vals) if ts_vals else None)


def save_history(path, fills):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for f in fills:
            fh.write(json.dumps(_fill_to_row(f), separators=(",", ":")) + "\n")
    os.replace(tmp, path)


def merge_and_dedupe(existing, new_fills):
    """回 (merged_sorted, n_added)。以 _fill_key 去重，結果依 ts 排序。"""
    seen = {_fill_key(f) for f in existing}
    added = [f for f in new_fills if _fill_key(f) not in seen]
    merged = existing + added
    merged.sort(key=lambda f: (f["ts"] is None, f["ts"] or 0))
    return merged, len(added)


def trim_retention(fills, now_sec, retention_days):
    """回 (kept, n_dropped)。ts 缺失的筆保留（無法判斷該不該丟，不臆造捨棄）。"""
    cutoff = now_sec - retention_days * 86400
    kept = [f for f in fills if f["ts"] is None or f["ts"] >= cutoff]
    return kept, len(fills) - len(kept)


# ---------------------------------------------------------------------------
# 抓取（種子／增量）
# ---------------------------------------------------------------------------

def seed_fills(addr, data_dir, meta, post_fn=None):
    """首次執行的種子來源。回 (fills, note, hit_cap)。

    優先用同目錄的 latest_raw.json（fetch.py 今天已抓過，零額外請求）；
    沒有才打 API 回填 config.FILLS_HISTORY_BACKFILL_DAYS 天。
    """
    raw_path = os.path.join(data_dir, "latest_raw.json")
    if os.path.exists(raw_path):
        try:
            with open(raw_path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (ValueError, OSError):
            raw = None
        if isinstance(raw, dict) and raw.get("userFills"):
            fills = classify.parse_fills(raw["userFills"])
            return fills, f"種子來自 latest_raw.json（{len(fills)} 筆，零額外請求）", False
    raw_fills, hit_cap = fetch.fetch_fills_since(
        addr, meta, post_fn=post_fn, days=config.FILLS_HISTORY_BACKFILL_DAYS,
        page_cap=config.FILLS_HISTORY_PAGE_CAP)
    fills = classify.parse_fills(raw_fills)
    note = (f"回填 {config.FILLS_HISTORY_BACKFILL_DAYS} 天"
           f"（{len(fills)} 筆{'，觸及分頁上限，可能不完整' if hit_cap else ''}）")
    return fills, note, hit_cap


def incremental_fills(addr, since_ts, meta, post_fn=None):
    """回 (fills, note, hit_cap)。since_ts 為既有歷史最後一筆的 ts（epoch 秒）。"""
    start_ms = int((since_ts + 0.001) * 1000)
    raw_fills, hit_cap = fetch.fetch_fills_since(
        addr, meta, post_fn=post_fn, start_ms=start_ms,
        page_cap=config.FILLS_HISTORY_PAGE_CAP)
    fills = classify.parse_fills(raw_fills)
    note = (f"增量抓取（{len(fills)} 筆新成交"
           f"{'，觸及分頁上限，這段時間可能有遺漏' if hit_cap else ''}）")
    return fills, note, hit_cap


# ---------------------------------------------------------------------------
# 統計（依 dex 前綴分組 + 全體）
# ---------------------------------------------------------------------------

def _dex_of(coin):
    """coin → dex 前綴（"xyz:SKHX" → "xyz"；原生無前綴 → "native"）。"""
    return coin.split(":", 1)[0] if ":" in coin else "native"


def build_stats(fills, generated_at=None):
    """歷史成交 → 統計快照（全體＋依 dex 分組）。純函式，供離線測試。"""
    round_trips, open_positions, carry_in = classify.aggregate_round_trips(fills)
    ts_vals = [f["ts"] for f in fills if f["ts"] is not None]
    span_days = ((max(ts_vals) - min(ts_vals)) / 86400) if len(ts_vals) >= 2 else 0.0

    def group_stats(pred):
        rt = [e for e in round_trips if pred(e["coin"])]
        op = [e for e in open_positions if pred(e["coin"])]
        ci_pnl = sum(v["pnl"] for c, v in carry_in.items() if pred(c))
        s = classify.round_trip_stats(rt)
        s["n_open_positions"] = len(op)
        s["open_positions_realized_pnl"] = round(sum(e["pnl"] for e in op), 2)
        s["carry_in_pnl"] = round(ci_pnl, 2)
        return s

    dexes = sorted({_dex_of(f["coin"]) for f in fills})
    by_dex = {d: group_stats(lambda c, d=d: _dex_of(c) == d) for d in dexes}

    return {
        "generated_at": generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_fills_total": len(fills),
        "span_days": round(span_days, 1),
        "earliest_fill": (time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(min(ts_vals)))
                          if ts_vals else None),
        "latest_fill": (time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(max(ts_vals)))
                        if ts_vals else None),
        "overall": group_stats(lambda c: True),
        "by_dex": by_dex,
    }


def save_stats(path, stats):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_for_wallet(addr, data_dir, meta, post_fn=None, now_sec=None):
    """回 stats dict。data_dir＝該錢包的 data/tracked/{addr} 目錄。"""
    now_sec = now_sec if now_sec is not None else time.time()
    hist_path = os.path.join(data_dir, HISTORY_FILENAME)
    stats_path = os.path.join(data_dir, STATS_FILENAME)

    existing, max_ts = load_history(hist_path)
    if not existing:
        new_fills, note, _ = seed_fills(addr, data_dir, meta, post_fn=post_fn)
    else:
        new_fills, note, _ = incremental_fills(addr, max_ts, meta, post_fn=post_fn)

    merged, n_added = merge_and_dedupe(existing, new_fills)
    meta.note(f"{addr[:10]}… {note}｜新增 {n_added} 筆（去重後）")

    stats = build_stats(merged)
    save_stats(stats_path, stats)

    trimmed, n_dropped = trim_retention(merged, now_sec, config.FILLS_HISTORY_RETENTION_DAYS)
    if n_dropped:
        meta.note(f"{addr[:10]}… 修剪 {n_dropped} 筆超過 "
                  f"{config.FILLS_HISTORY_RETENTION_DAYS} 天保留期的舊成交")
    save_history(hist_path, trimmed)
    return stats


def print_summary(addr, stats):
    ov = stats["overall"]
    print(f"[fills_history] {addr}")
    print(f"  歷史樣本：{stats['n_fills_total']} 筆成交、跨度 {stats['span_days']:.1f} 天"
         f"（{stats['earliest_fill']} ～ {stats['latest_fill']}）")
    wr = "?" if ov["win_rate"] is None else f"{ov['win_rate']:.1%}"
    pf = "?" if ov["profit_factor"] is None else f"{ov['profit_factor']:.2f}"
    print(f"  全體：{ov['n_round_trips']} 個完整回合｜勝率 {wr}｜獲利因子 {pf}｜"
         f"淨損益 ${ov['net_pnl']:,.0f}")
    for dex, s in sorted(stats["by_dex"].items()):
        wr = "?" if s["win_rate"] is None else f"{s['win_rate']:.1%}"
        print(f"  [{dex}] {s['n_round_trips']} 回合｜勝率 {wr}｜"
             f"淨損益(回合) ${s['net_pnl']:,.0f}｜未平倉 {s['n_open_positions']} 個"
             f"（已實現 ${s['open_positions_realized_pnl']:,.0f}）｜"
             f"carry-in ${s['carry_in_pnl']:,.0f}")


def main(argv=None):
    p = argparse.ArgumentParser(description="每日成交歷史累積（唯讀）")
    p.add_argument("--address", default="", help="只跑這個地址（省略＝所有 TRACKED_WALLETS）")
    p.add_argument("--query", action="store_true",
                   help="只讀本地既有歷史印統計，不打網路（除錯／臨時查詢用）")
    p.add_argument("--dex", default="", help="配合 --query：只印這個 dex 分組")
    args = p.parse_args(argv)

    wallets = config.TRACKED_WALLETS
    if args.address:
        wallets = [w for w in wallets if w["address"].lower() == args.address.lower()]
        if not wallets:
            wallets = [{"address": args.address, "label": "(ad-hoc)"}]

    meta = fetch.Meta()
    for w in wallets:
        addr = w["address"]
        data_dir = os.path.join("data", "tracked", addr)
        if args.query:
            hist_path = os.path.join(data_dir, HISTORY_FILENAME)
            fills, _ = load_history(hist_path)
            if not fills:
                print(f"[fills_history] {addr}：本地無歷史（尚未跑過或已被修剪殆盡）")
                continue
            stats = build_stats(fills)
        else:
            os.makedirs(data_dir, exist_ok=True)
            stats = run_for_wallet(addr, data_dir, meta)
        if args.dex:
            s = stats["by_dex"].get(args.dex)
            if s is None:
                print(f"[fills_history] {addr}：無 {args.dex} 場所的歷史資料")
            else:
                print(f"[fills_history] {addr} [{args.dex}]: {json.dumps(s, ensure_ascii=False)}")
        else:
            print_summary(addr, stats)

    print(f"[fills_history] requests_ok={meta.requests_ok} requests_failed={meta.requests_failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
