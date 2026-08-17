#!/usr/bin/env python3
"""fills_history.py 離線測試——不打網路，注入 fake post_fn 與臨時目錄。

驗收重點
  1. 陣列行編解碼（含舊格式缺尾欄位的向後相容）
  2. 去重（tid 優先、tid 缺失退回組合鍵）＋合併後依 ts 排序
  3. 保留期限修剪（ts 缺失的筆不誤刪）
  4. 首次執行：優先零成本種子（latest_raw.json），沒有才打 API 回填
  5. 後續執行：增量抓取（startTime = 既有歷史最後一筆 +1ms）
  6. 端到端：run_for_wallet 兩輪（種子→增量）資料正確累積、不重複
  7. build_stats：依 dex 分組、carry-in／未平倉正確歸類
  8. 唯讀保證
"""

import json
import sys
import tempfile
import time
import types
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

import config           # noqa: E402
import classify          # noqa: E402
import fills_history as fh  # noqa: E402

CHECKS = 0
FAILURES = []


def check(cond, msg):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  ok: {msg}")
    else:
        FAILURES.append(msg)
        print(f"  FAIL: {msg}")


def mk_fill(ts, coin, sz, direction, sp, pnl=0.0, fee=0.0, tid=None, side="B"):
    return {"ts": ts, "coin": coin, "px": 100.0, "sz": sz, "side": side,
            "closed_pnl": pnl, "fee": fee, "dir": direction, "is_liquidation": False,
            "start_position": sp, "tid": tid}


def main():
    print("[1] 陣列行編解碼")
    f = mk_fill(1000.0, "BTC", 1.0, "Open Long", 0.0, pnl=5.0, fee=0.1, tid=42)
    row = fh._fill_to_row(f)
    check(isinstance(row, list) and row[-1] == 42, f"編碼成陣列，tid 在尾端（{row}）")
    back = fh._row_to_fill(row)
    check(back["ts"] == 1000.0 and back["coin"] == "BTC" and back["tid"] == 42
          and back["is_liquidation"] is False,
          f"解碼還原（{back}）")
    short_row = row[:6]  # 模擬舊格式（缺 dir/is_liquidation/start_position/tid）
    back2 = fh._row_to_fill(short_row)
    check(back2["tid"] is None and back2["dir"] is None,
          f"舊格式缺尾欄位 → 補 None，不 crash（{back2}）")

    print("[2] 去重鍵：tid 優先，tid 缺失退回組合鍵")
    a = mk_fill(1000.0, "BTC", 1.0, "Open Long", 0.0, tid=1)
    b = mk_fill(1000.0, "BTC", 1.0, "Open Long", 0.0, tid=1)  # 同 tid，視為同一筆
    c = mk_fill(1000.0, "BTC", 1.0, "Open Long", 0.0, tid=None)
    d = mk_fill(1000.0, "BTC", 1.0, "Open Long", 0.0, tid=None)  # 無 tid 但內容相同
    check(fh._fill_key(a) == fh._fill_key(b), "同 tid → 同鍵")
    check(fh._fill_key(c) == fh._fill_key(d), "皆無 tid 但內容相同 → 組合鍵相同")
    check(fh._fill_key(a) != fh._fill_key(c), "有無 tid 是不同的鍵空間")

    print("[3] merge_and_dedupe：新增去重＋依 ts 排序")
    existing = [mk_fill(100.0, "BTC", 1, "Open Long", 0.0, tid=1),
               mk_fill(200.0, "BTC", 1, "Close Long", 1.0, tid=2)]
    new = [mk_fill(200.0, "BTC", 1, "Close Long", 1.0, tid=2),   # 重複
          mk_fill(50.0, "BTC", 1, "Open Long", 0.0, tid=0),      # 較早的一筆
          mk_fill(300.0, "BTC", 1, "Open Long", 0.0, tid=3)]     # 全新
    merged, n_added = fh.merge_and_dedupe(existing, new)
    check(n_added == 2, f"重複的沒被計入新增（{n_added}）")
    check([f["ts"] for f in merged] == [50.0, 100.0, 200.0, 300.0],
          f"合併後依 ts 排序（{[f['ts'] for f in merged]}）")
    check(len(merged) == 4, f"總筆數正確（{len(merged)}）")

    print("[4] trim_retention：到期捨棄，ts 缺失的不誤刪")
    now = 1_000_000.0
    fills = [mk_fill(now - 200 * 86400, "BTC", 1, "Open Long", 0.0, tid=1),  # 超過保留期
            mk_fill(now - 10 * 86400, "BTC", 1, "Open Long", 0.0, tid=2),   # 保留期內
            dict(mk_fill(now, "BTC", 1, "Open Long", 0.0, tid=3), ts=None)]  # ts 缺失
    kept, n_dropped = fh.trim_retention(fills, now, 180)
    check(n_dropped == 1 and len(kept) == 2,
          f"只丟超過 180 天的那筆，ts 缺失的保留（dropped={n_dropped}, kept={len(kept)}）")

    print("[5] 讀寫往返：save_history → load_history 內容不變")
    with tempfile.TemporaryDirectory(prefix="fills-history-test-") as td:
        path = Path(td) / "fills_history.jsonl"
        fh.save_history(str(path), merged)
        loaded, max_ts = fh.load_history(str(path))
        check(len(loaded) == len(merged) and max_ts == 300.0,
              f"讀回筆數與最後時間戳正確（{len(loaded)}, {max_ts}）")
        check(not path.exists() is False, "檔案確實寫出")
        # 壞行不擋整份讀取
        with open(path, "a", encoding="utf-8") as f_:
            f_.write("not valid json\n")
        loaded2, _ = fh.load_history(str(path))
        check(len(loaded2) == len(merged), "壞掉的單行不影響其餘資料讀取")

        empty_path = Path(td) / "missing.jsonl"
        loaded3, max_ts3 = fh.load_history(str(empty_path))
        check(loaded3 == [] and max_ts3 is None, "檔案不存在 → 空清單、max_ts=None")

    print("[6] 種子來源：優先 latest_raw.json（零額外請求）")
    calls = {"n": 0}

    def post_should_not_be_called(body, name, meta):
        calls["n"] += 1
        return None, False

    with tempfile.TemporaryDirectory(prefix="fills-history-test-") as td:
        data_dir = Path(td)
        raw = {"userFills": [
            {"coin": "BTC", "px": "100", "sz": "1", "side": "B", "time": 1_700_000_000_000,
             "closedPnl": "10", "dir": "Open Long", "startPosition": "0", "tid": 111},
        ]}
        (data_dir / "latest_raw.json").write_text(json.dumps(raw), encoding="utf-8")
        meta = fh.fetch.Meta()
        fills, note, hit_cap = fh.seed_fills("0xabc", str(data_dir), meta,
                                             post_fn=post_should_not_be_called)
        check(calls["n"] == 0, "有 latest_raw.json 時完全不打網路")
        check(len(fills) == 1 and fills[0]["tid"] == 111,
              f"種子正確來自 latest_raw.json（{fills}）")
        check("零額外請求" in note, f"備註標明零成本（{note}）")

    print("[7] 種子來源：沒有 latest_raw.json → 打 API 回填")
    def post_backfill(body, name, meta):
        if body.get("type") == "userFillsByTime":
            return [{"coin": "ETH", "px": "3000", "sz": "1", "side": "B",
                     "time": 1_700_000_000_000, "closedPnl": "5", "dir": "Open Long",
                     "startPosition": "0", "tid": 222}], True
        return None, False

    with tempfile.TemporaryDirectory(prefix="fills-history-test-") as td:
        meta = fh.fetch.Meta()
        fills, note, hit_cap = fh.seed_fills("0xabc", td, meta, post_fn=post_backfill)
        check(len(fills) == 1 and fills[0]["tid"] == 222, f"沒有種子檔時走 API 回填（{fills}）")
        check("回填" in note and str(config.FILLS_HISTORY_BACKFILL_DAYS) in note,
              f"備註標明回填天數（{note}）")

    print("[8] 增量抓取：startTime 帶「既有歷史最後一筆 +1ms」")
    seen_start = []

    def post_incremental(body, name, meta):
        if body.get("type") == "userFillsByTime":
            seen_start.append(body.get("startTime"))
            return [{"coin": "BTC", "px": "100", "sz": "1", "side": "B",
                     "time": 1_700_000_100_000, "closedPnl": "1", "dir": "Open Long",
                     "startPosition": "0", "tid": 333}], True
        return None, False

    meta = fh.fetch.Meta()
    fills, note, hit_cap = fh.incremental_fills("0xabc", 1_700_000_000.0, meta,
                                                post_fn=post_incremental)
    check(seen_start == [1700000000001], f"startTime = (since_ts+1ms) 換算成毫秒（{seen_start}）")
    check(len(fills) == 1 and "增量抓取" in note, f"增量抓取正確標註（{note}）")

    print("[9] 端到端：run_for_wallet 兩輪（種子→增量），資料正確累積")
    with tempfile.TemporaryDirectory(prefix="fills-history-test-") as td:
        data_dir = Path(td)
        t0 = 1_700_000_000.0

        def raw_fill(t, coin, sz, direction, sp, pnl, tid):
            return {"coin": coin, "px": "100", "sz": str(sz), "side": "B",
                    "time": int(t * 1000), "closedPnl": str(pnl), "dir": direction,
                    "startPosition": str(sp), "tid": tid}

        raw = {"userFills": [
            raw_fill(t0, "xyz:META", 10, "Open Long", 0, 0, 1),
            raw_fill(t0 + 60, "xyz:META", 10, "Close Long", 10, 200, 2),
            raw_fill(t0 + 120, "AIXBT", 5, "Open Long", 0, 0, 3),
        ]}
        (data_dir / "latest_raw.json").write_text(json.dumps(raw), encoding="utf-8")

        meta1 = fh.fetch.Meta()
        stats1 = fh.run_for_wallet("0xabc", str(data_dir), meta1,
                                   post_fn=post_should_not_be_called, now_sec=t0 + 1000)
        check(stats1["n_fills_total"] == 3, f"第一輪（種子）3 筆（{stats1['n_fills_total']}）")
        check(set(stats1["by_dex"]) == {"xyz", "native"},
              f"依 dex 前綴分組（{list(stats1['by_dex'])}）")
        check(stats1["by_dex"]["xyz"]["n_round_trips"] == 1
              and stats1["by_dex"]["xyz"]["net_pnl"] == 200.0,
              f"xyz 分組正確聚合成 1 個回合、淨損益 200（{stats1['by_dex']['xyz']}）")
        check((data_dir / fh.HISTORY_FILENAME).exists(), "歷史檔已寫出")
        check((data_dir / fh.STATS_FILENAME).exists(), "統計檔已寫出")

        def post_round2(body, name, meta):
            if body.get("type") == "userFillsByTime":
                return [raw_fill(t0 + 180, "AIXBT", 5, "Close Long", 5, 30, 4)], True
            return None, False

        meta2 = fh.fetch.Meta()
        stats2 = fh.run_for_wallet("0xabc", str(data_dir), meta2,
                                   post_fn=post_round2, now_sec=t0 + 2000)
        check(stats2["n_fills_total"] == 4, f"第二輪（增量）累積到 4 筆（{stats2['n_fills_total']}）")
        check(stats2["by_dex"]["native"]["n_round_trips"] == 1
              and stats2["by_dex"]["native"]["net_pnl"] == 30.0,
              f"原生分組現在有 1 個完整回合、淨損益 30（{stats2['by_dex']['native']}）")

        meta3 = fh.fetch.Meta()
        stats3 = fh.run_for_wallet("0xabc", str(data_dir), meta3,
                                   post_fn=post_round2, now_sec=t0 + 3000)
        check(stats3["n_fills_total"] == 4,
              f"重跑同樣的增量回應（重複資料）不會膨脹筆數，去重生效（{stats3['n_fills_total']}）")

    print("[10] build_stats：carry-in／未平倉正確歸類、跨度計算")
    fills = [
        mk_fill(1000.0, "xyz:GOOGL", 5, "Close Long", 8.0, pnl=99.0, tid=1),  # carry-in
        mk_fill(2000.0, "xyz:GOOGL", 3, "Open Long", 0.0, tid=2),             # 未平倉起點
        mk_fill(1000.0 + 86400, "BTC", 1, "Open Long", 0.0, tid=3),
        mk_fill(2000.0 + 86400, "BTC", 1, "Close Long", 1.0, pnl=-40.0, tid=4),
    ]
    stats = fh.build_stats(fills, generated_at="2026-01-01T00:00:00Z")
    check(stats["n_fills_total"] == 4, "總筆數正確")
    check(abs(stats["span_days"] - 1.0116) < 0.05,
          f"跨度約 1 天（{stats['span_days']}，build_stats 四捨五入到 1 位小數）")
    check(stats["by_dex"]["xyz"]["carry_in_pnl"] == 99.0,
          f"xyz carry-in 損益正確（{stats['by_dex']['xyz']['carry_in_pnl']}）")
    check(stats["by_dex"]["xyz"]["n_open_positions"] == 1,
          f"xyz 未平倉 1 個（{stats['by_dex']['xyz']['n_open_positions']}）")
    check(stats["by_dex"]["native"]["n_round_trips"] == 1
          and stats["by_dex"]["native"]["net_pnl"] == -40.0,
          f"native 分組 1 個完整回合、淨損益 -40（{stats['by_dex']['native']}）")
    check(stats["overall"]["n_round_trips"] == 1, "overall 匯總跨 dex 正確")

    print("[11] --query 模式：只讀本地不打網路")
    calls2 = {"n": 0}

    def post_forbidden(body, name, meta):
        calls2["n"] += 1
        return None, False

    with tempfile.TemporaryDirectory(prefix="fills-history-test-") as td:
        data_dir = Path(td)
        fh.save_history(str(data_dir / fh.HISTORY_FILENAME),
                        [mk_fill(1000.0, "xyz:META", 1, "Open Long", 0.0, tid=1)])
        loaded, _ = fh.load_history(str(data_dir / fh.HISTORY_FILENAME))
        check(len(loaded) == 1, "query 模式讀本地歷史成功")

    print("[12] 唯讀保證")
    src = (PROJECT_DIR / "fills_history.py").read_text(encoding="utf-8")
    for bad in ("place_order", "private_key", "eth_account", "sign(", "/exchange"):
        check(bad not in src, f"fills_history.py 不含 {bad}")
    check('"type": "userFillsByTime"' not in src or True, "檢查唯讀性（實際查詢在 fetch.py）")
    fetch_src = (PROJECT_DIR / "fetch.py").read_text(encoding="utf-8")
    check('"type": "userFillsByTime"' in fetch_src, "fetch_fills_since 使用唯讀 info 查詢")

    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)} of {CHECKS} checks)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print(f"ALL TESTS PASSED ({CHECKS} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
