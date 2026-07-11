#!/usr/bin/env python3
"""hyper-observer scan_universe：全量排行榜 → 「可跟畫像」候選過濾器（純離線）。

用法（在 projects/hyper-observer 下）：
    python3 scan_universe.py --raw data/tmp/leaderboard_raw_2026-07-10.json \
        [--max-candidates 120] [--out data/scan/candidates_2026-07-10.json]

動機：兩平台排行榜「頂端」已實證全是不可跟的（爆倉/做市/刷量/高頻）。本工具從
leaderboard 原始回應的**全量**（~40k 錢包）中，用「可跟畫像」過濾出中段與榜外的
方向性贏家候選，交給 fetch.py --wallets-file 深抓、classify.py --label scan 評判。

過濾漏斗（門檻全在 config.py 的 SCAN_*，已用 2026-07-10 全量檔離線校準）：
1. allTime pnl >= SCAN_MIN_ALLTIME_PNL          （已證明的贏家）
2. month pnl >= SCAN_MIN_MONTH_PNL 且 week pnl >= SCAN_MIN_WEEK_PNL（仍在賺，非過氣/粉塵）
3. SCAN_MIN_VLM_TO_PNL <= allTime vlm/pnl <= SCAN_MAX_VLM_TO_PNL（反做市/刷量；
   下限同時排除 vlm≈0 的 vault/HLP 型收益——那種 pnl 不是方向性交易、跟不到）
4. allTime roi >= SCAN_MIN_ALLTIME_ROI          （方向性交易者 roi 不趨近 0）
5. accountValue 在 [SCAN_MIN_ACCOUNT, SCAN_MAX_ACCOUNT]（排除粉塵與巨鯨）
6. 排除排行榜前 SCAN_EXCLUDE_TOP_N 列（每日 top-N 管線已掃過；重用
   fetch.extract_addresses，語意與每日管線完全一致）

輸出：candidates json（地址＋四窗指標＋分數，<200KB）＋ stdout 漏斗摘要。
純離線、純唯讀：本腳本不發任何網路請求，不含下單、簽章、私鑰功能。
"""

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import config
import fetch  # 重用 extract_addresses：top-N 排除語意與每日 fetch 管線一致

BASE_DIR = Path(__file__).resolve().parent
WINDOWS = ("day", "week", "month", "allTime")
EPS = 1e-9


# ---------------------------------------------------------------------------
# 原始檔解析
# ---------------------------------------------------------------------------

def load_rows(raw):
    """leaderboard 原始資料 → rows list。防禦性接受三種形狀：
    原生 API 回應 {"leaderboardRows": [...]}、fetch.py 的 dump 包一層 {"raw": {...}}、
    或直接就是 list。解析不到回空 list，不 crash。"""
    if isinstance(raw, dict):
        inner = raw.get("raw")
        if isinstance(inner, (dict, list)):
            return load_rows(inner)
        for key in ("leaderboardRows", "leaderboard", "rows", "data"):
            if isinstance(raw.get(key), list):
                return raw[key]
        return []
    if isinstance(raw, list):
        return raw
    return []


def parse_row(row):
    """單列 → {address, account_value, windows: {name: {pnl, roi, vlm}}}。

    數值是字串要轉 float；缺地址、缺任一視窗、或數值壞掉 → 回 None（列入漏斗淘汰）。
    """
    if not isinstance(row, dict):
        return None
    addr = row.get("ethAddress")
    if not isinstance(addr, str) or not fetch.ADDR_RE.fullmatch(addr.strip()):
        return None
    try:
        account_value = float(row.get("accountValue"))
    except (TypeError, ValueError):
        return None
    windows = {}
    for item in row.get("windowPerformances") or []:
        if (isinstance(item, (list, tuple)) and len(item) == 2
                and isinstance(item[0], str) and isinstance(item[1], dict)):
            try:
                windows[item[0]] = {k: float(item[1].get(k)) for k in ("pnl", "roi", "vlm")}
            except (TypeError, ValueError):
                return None
    if not all(w in windows for w in WINDOWS):
        return None
    return {"address": addr.strip().lower(), "account_value": account_value,
            "windows": windows}


# ---------------------------------------------------------------------------
# 過濾漏斗與綜合分數
# ---------------------------------------------------------------------------

def default_thresholds():
    """呼叫時讀 config（而非 import 時固化），讓測試覆寫 config 也生效。"""
    return {
        "min_alltime_pnl": config.SCAN_MIN_ALLTIME_PNL,
        "min_month_pnl": config.SCAN_MIN_MONTH_PNL,
        "min_week_pnl": config.SCAN_MIN_WEEK_PNL,
        "min_vlm_to_pnl": config.SCAN_MIN_VLM_TO_PNL,
        "max_vlm_to_pnl": config.SCAN_MAX_VLM_TO_PNL,
        "min_alltime_roi": config.SCAN_MIN_ALLTIME_ROI,
        "min_account": config.SCAN_MIN_ACCOUNT,
        "max_account": config.SCAN_MAX_ACCOUNT,
        "exclude_top_n": config.SCAN_EXCLUDE_TOP_N,
    }


def score_candidate(cand):
    """綜合分數（越高越好）：month roi × ln(allTime pnl) / max(vlm/pnl, 1)。

    邏輯（簡單、單調、可解釋）：
    - month roi：近期動能為主軸——本次掃描要的是「現在還在賺」的方向性贏家；
    - × ln(allTime pnl)：全期獲利規模取對數加權，「已證明」程度加分但不讓巨額線性輾壓；
    - ÷ max(vlm/pnl, 1)：量/PnL 比越高越像高頻/做市（跟不到），懲罰之；<1 不再加成。
    """
    at = cand["windows"]["allTime"]
    mo = cand["windows"]["month"]
    vpr = at["vlm"] / max(at["pnl"], EPS)
    return mo["roi"] * math.log(max(at["pnl"], math.e)) / max(vpr, 1.0)


def filter_candidates(rows, thresholds=None):
    """過濾漏斗。回 (candidates, funnel)。

    candidates：通過全部條件的 parse_row dict（含 vlm_to_pnl、score，未排序未截斷）；
    funnel：各階段剩餘數的有序 dict（stdout 摘要與輸出 json 共用）。
    thresholds 可注入（測試用），缺項以 config 的 SCAN_* 補齊。
    """
    t = {**default_thresholds(), **(thresholds or {})}
    funnel = {"total_rows": len(rows)}

    parsed, seen = [], set()
    for row in rows:
        c = parse_row(row)
        if c is not None and c["address"] not in seen:
            seen.add(c["address"])
            parsed.append(c)
    funnel["parsed_valid"] = len(parsed)

    stage = [c for c in parsed
             if c["windows"]["allTime"]["pnl"] >= t["min_alltime_pnl"]]
    funnel["alltime_pnl"] = len(stage)

    stage = [c for c in stage
             if c["windows"]["month"]["pnl"] >= t["min_month_pnl"]
             and c["windows"]["week"]["pnl"] >= t["min_week_pnl"]]
    funnel["still_winning"] = len(stage)

    kept = []
    for c in stage:
        at = c["windows"]["allTime"]
        if at["vlm"] <= 0:
            continue
        vpr = at["vlm"] / max(at["pnl"], EPS)
        if t["min_vlm_to_pnl"] <= vpr <= t["max_vlm_to_pnl"]:
            c["vlm_to_pnl"] = round(vpr, 4)
            kept.append(c)
    stage = kept
    funnel["vlm_to_pnl_band"] = len(stage)

    stage = [c for c in stage
             if c["windows"]["allTime"]["roi"] >= t["min_alltime_roi"]]
    funnel["alltime_roi"] = len(stage)

    stage = [c for c in stage
             if t["min_account"] <= c["account_value"] <= t["max_account"]]
    funnel["account_band"] = len(stage)

    # 排除每日 top-N 管線已掃過的頂端地址（與 fetch 的 extract_addresses 同語意/同順序）
    top_addrs = set(fetch.extract_addresses(rows, limit=int(t["exclude_top_n"])))
    stage = [c for c in stage if c["address"] not in top_addrs]
    funnel["exclude_top_n"] = len(stage)

    for c in stage:
        c["score"] = round(score_candidate(c), 6)
    return stage, funnel


def build_output(candidates, funnel, max_candidates, date, source):
    """排序、截斷、組輸出 payload（<200KB：120 候選 × ~0.4KB ≈ 48KB）。"""
    ranked = sorted(candidates, key=lambda c: -c["score"])[:max_candidates]
    return {
        "date": date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "thresholds": default_thresholds(),
        "max_candidates": max_candidates,
        "funnel": funnel,
        "n_candidates": len(ranked),
        "candidates": [
            {"address": c["address"],
             "score": c["score"],
             "account_value": round(c["account_value"], 2),
             "vlm_to_pnl": c["vlm_to_pnl"],
             "windows": {w: {k: round(c["windows"][w][k], 4) for k in ("pnl", "roi", "vlm")}
                         for w in WINDOWS}}
            for c in ranked
        ],
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="全量 leaderboard →「可跟畫像」候選過濾（純離線、唯讀）")
    parser.add_argument("--raw", required=True,
                        help="leaderboard 原始檔路徑（fetch.py 落在 data/tmp/ 的 dump）")
    parser.add_argument("--max-candidates", type=int,
                        default=config.SCAN_DEFAULT_MAX_CANDIDATES)
    parser.add_argument("--out", default=None,
                        help="輸出 json；預設 data/scan/candidates_{UTC日期}.json")
    args = parser.parse_args(argv)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw_path = Path(args.raw)
    if not raw_path.is_absolute():
        cand = BASE_DIR / raw_path
        raw_path = cand if cand.exists() else raw_path
    out_path = Path(args.out) if args.out else (
        BASE_DIR / "data" / "scan" / f"candidates_{today}.json")
    if not out_path.is_absolute():
        out_path = BASE_DIR / out_path

    try:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[scan] 原始檔讀取失敗：{raw_path}：{exc}", file=sys.stderr)
        return 1

    rows = load_rows(raw)
    if not rows:
        print(f"[scan] 原始檔解析不到 leaderboard rows：{raw_path}", file=sys.stderr)
        return 1

    candidates, funnel = filter_candidates(rows)
    payload = build_output(candidates, funnel, args.max_candidates, today, args.raw)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    print("[scan] 過濾漏斗（各階段剩餘數）：")
    for name, n in funnel.items():
        print(f"[scan]   {name}: {n}")
    print(f"[scan]   → 綜合分數排序取前 {args.max_candidates}：{payload['n_candidates']} 個候選")
    print(f"[scan] 輸出：{out_path}（{out_path.stat().st_size / 1024:.0f} KB）")
    print("SCAN " + json.dumps({"n_candidates": payload["n_candidates"],
                                "funnel": funnel, "out": str(out_path)},
                               ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
