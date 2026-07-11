#!/usr/bin/env python3
"""poly-observer verify：聰明錢「存在性」檢驗（一次性報告）。

用法：
    python3 verify_smart_money.py --snapshot data/snapshots/{date} [--report-dir data/reports]

對 snapshot 內每個錢包計算：總 PnL、月度 PnL 序列、正月比率、峰值回撤、
交易頻率、類別集中度，然後按 config.py 的門檻分類：
mm_bot_like / one_hit / consistent_winner / degraded / choppy / insufficient_data。

輸出：
- data/reports/verification_{date}.md   （人讀報告）
- data/reports/verification_{date}.json （機器可讀完整結果）

重要聲明：錢包宇宙取自「今日」排行榜，天生有倖存者偏差；
本檢驗證明的是聰明錢的「存在性」，不代表「跟得到」。
純唯讀分析，不含任何下單、金鑰、簽章功能。
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import config

BASE_DIR = Path(__file__).resolve().parent
DAY_SEC = 86400
EPS = 1e-9


# ---------------------------------------------------------------------------
# 原始資料解析（防禦性：欄位名多形、ms/s 時戳、包層 dict）
# ---------------------------------------------------------------------------

def _norm_ts(val):
    """時間戳正規化成 epoch 秒；壞值回 None。"""
    try:
        ts = float(val)
    except (TypeError, ValueError):
        # ISO 字串防禦
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return None
        return None
    if ts > 1e12:  # 毫秒
        ts /= 1000.0
    if ts <= 0:
        return None
    return ts


def parse_pnl_curve(raw):
    """把 pnl 曲線原始回應解析成排序後的 [(ts, cumulative_pnl)]。"""
    if raw is None:
        return []
    if isinstance(raw, dict):
        for key in ("data", "history", "pnl", "points", "chart"):
            if isinstance(raw.get(key), list):
                raw = raw[key]
                break
        else:
            return []
    if not isinstance(raw, list):
        return []
    points = []
    for item in raw:
        ts, val = None, None
        if isinstance(item, dict):
            for k in ("t", "timestamp", "time", "ts", "date"):
                if k in item:
                    ts = _norm_ts(item[k])
                    break
            for k in ("p", "pnl", "value", "amount", "v", "y"):
                if k in item:
                    try:
                        val = float(item[k])
                    except (TypeError, ValueError):
                        val = None
                    break
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            ts = _norm_ts(item[0])
            try:
                val = float(item[1])
            except (TypeError, ValueError):
                val = None
        if ts is not None and val is not None:
            points.append((ts, val))
    points.sort(key=lambda x: x[0])
    return points


def parse_trades(raw_activity):
    """activity → 正規化交易清單 [{ts, side, usdc, title, slug, asset}]。

    只保留買賣（type 缺失時視為交易）；REDEEM/REWARD 等排除，
    因此由 activity 近似的 PnL 是現金流近似值（低信心）。
    """
    if raw_activity is None:
        return []
    if isinstance(raw_activity, dict):
        for key in ("data", "activity", "history", "results"):
            if isinstance(raw_activity.get(key), list):
                raw_activity = raw_activity[key]
                break
        else:
            return []
    trades = []
    for item in raw_activity:
        if not isinstance(item, dict):
            continue
        typ = str(item.get("type", "TRADE")).upper()
        side = str(item.get("side", "")).upper()
        if typ not in ("TRADE", "BUY", "SELL", "LIMIT_ORDER_FILL", "MARKET_ORDER_FILL"):
            continue
        if side not in ("BUY", "SELL"):
            side = typ if typ in ("BUY", "SELL") else ""
        ts = None
        for k in ("timestamp", "time", "ts", "createdAt", "created_at"):
            if k in item:
                ts = _norm_ts(item[k])
                break
        usdc = None
        for k in ("usdcSize", "usdc_size", "usdSize", "cash", "notional"):
            if k in item:
                try:
                    usdc = abs(float(item[k]))
                except (TypeError, ValueError):
                    usdc = None
                break
        if usdc is None:
            try:
                usdc = abs(float(item.get("price", 0)) * float(item.get("size", 0)))
            except (TypeError, ValueError):
                usdc = 0.0
        asset = (item.get("asset") or item.get("tokenId") or item.get("token_id")
                 or item.get("conditionId") or item.get("condition_id")
                 or item.get("slug") or "")
        trades.append({
            "ts": ts,
            "side": side,
            "usdc": usdc or 0.0,
            "title": str(item.get("title") or item.get("question") or ""),
            "slug": str(item.get("slug") or item.get("eventSlug") or ""),
            "asset": str(asset),
        })
    trades.sort(key=lambda t: (t["ts"] is None, t["ts"] or 0))
    return trades


def _to_float(val):
    """寬鬆轉 float；壞值回 None。"""
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def parse_activity_events(raw_activity):
    """activity → 完整事件清單（含 REDEEM），供 track_wallet 時間軸與 simulate_copy 重建用。

    與 parse_trades 的差異：保留每筆的 price / shares，且**不丟棄** REDEEM/REWARD/CLAIM，
    好讓跟單模擬器能重建進出與結算。回傳按時間排序的
    [{ts, type, side, price, shares, usdc, title, slug, condition_id}]。
    此函式是共用解析邏輯的單一來源，track_wallet.py 與 simulate_copy.py 皆 import 使用。
    """
    if raw_activity is None:
        return []
    if isinstance(raw_activity, dict):
        for key in ("data", "activity", "history", "results"):
            if isinstance(raw_activity.get(key), list):
                raw_activity = raw_activity[key]
                break
        else:
            return []
    if not isinstance(raw_activity, list):
        return []
    events = []
    for item in raw_activity:
        if not isinstance(item, dict):
            continue
        typ = str(item.get("type", "TRADE")).upper()
        side = str(item.get("side", "")).upper()
        if side not in ("BUY", "SELL"):
            side = typ if typ in ("BUY", "SELL") else ""
        ts = None
        for k in ("timestamp", "time", "ts", "createdAt", "created_at"):
            if k in item:
                ts = _norm_ts(item[k])
                break
        price = _to_float(item.get("price"))
        shares = None
        for k in ("size", "shares", "quantity", "amount"):
            if k in item and item[k] is not None:
                shares = _to_float(item[k])
                if shares is not None:
                    break
        usdc = None
        for k in ("usdcSize", "usdc_size", "usdSize", "cash", "notional"):
            if k in item and item[k] is not None:
                usdc = _to_float(item[k])
                if usdc is not None:
                    usdc = abs(usdc)
                    break
        if usdc is None and price is not None and shares is not None:
            usdc = abs(price * shares)
        cond = (item.get("conditionId") or item.get("condition_id")
                or item.get("slug") or item.get("eventSlug")
                or item.get("asset") or item.get("tokenId") or item.get("token_id") or "")
        events.append({
            "ts": ts,
            "type": typ,
            "side": side,
            "price": price,
            "shares": abs(shares) if shares is not None else None,
            "usdc": usdc if usdc is not None else 0.0,
            "title": str(item.get("title") or item.get("question") or ""),
            "slug": str(item.get("slug") or item.get("eventSlug") or ""),
            "condition_id": str(cond),
        })
    events.sort(key=lambda e: (e["ts"] is None, e["ts"] or 0))
    return events


# ---------------------------------------------------------------------------
# 指標計算
# ---------------------------------------------------------------------------

def _month_key(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m")


def monthly_from_curve(points):
    """曲線切月：每月 delta = 該月最後值 − 前月最後值（首月以曲線首值為基準）。"""
    if not points:
        return {}
    monthly_last = {}
    for ts, val in points:
        monthly_last[_month_key(ts)] = val  # points 已排序，後值覆蓋前值
    months = sorted(monthly_last)
    out, prev = {}, points[0][1]
    for m in months:
        out[m] = monthly_last[m] - prev
        prev = monthly_last[m]
    return out


def monthly_from_activity(trades):
    """activity 現金流近似：SELL 進、BUY 出，按月加總（低信心）。"""
    out = defaultdict(float)
    for t in trades:
        if t["ts"] is None:
            continue
        if t["side"] == "SELL":
            out[_month_key(t["ts"])] += t["usdc"]
        elif t["side"] == "BUY":
            out[_month_key(t["ts"])] -= t["usdc"]
    return dict(out)


def max_drawdown_pct(series):
    """峰值回撤占 peak 的比例。series = 依時間排序的累積 PnL 值。"""
    peak, worst = None, 0.0
    for val in series:
        if peak is None or val > peak:
            peak = val
        if peak is not None and peak > EPS:
            dd = (peak - val) / peak
            worst = max(worst, dd)
    return worst if peak is not None and peak > EPS else None


def recent_pnl(points, end_ts, days=30):
    """曲線最後值 − (end_ts − days) 之前最近一點的值。"""
    if not points:
        return None
    cutoff = end_ts - days * DAY_SEC
    baseline = points[0][1]
    for ts, val in points:
        if ts <= cutoff:
            baseline = val
        else:
            break
    return points[-1][1] - baseline


def recent_pnl_from_activity(trades, end_ts, days=30):
    cutoff = end_ts - days * DAY_SEC
    total, seen = 0.0, False
    for t in trades:
        if t["ts"] is None or t["ts"] < cutoff or t["ts"] > end_ts + DAY_SEC:
            continue
        seen = True
        total += t["usdc"] if t["side"] == "SELL" else -t["usdc"]
    return total if seen else 0.0


def avg_hold_hours(trades):
    """FIFO 配對同 asset 的 BUY→SELL，回傳平均持有小時；配不到回 None。"""
    buys = defaultdict(list)
    holds = []
    for t in trades:
        if t["ts"] is None or not t["asset"]:
            continue
        if t["side"] == "BUY":
            buys[t["asset"]].append(t["ts"])
        elif t["side"] == "SELL" and buys[t["asset"]]:
            holds.append(t["ts"] - buys[t["asset"]].pop(0))
    if not holds:
        return None
    return (sum(holds) / len(holds)) / 3600.0


def categorize(trades):
    """類別分桶＋top 類占比。回 (counts, top_category, top_share)。"""
    counts = defaultdict(int)
    for t in trades:
        text = f" {t['title']} {t['slug']} ".lower()
        bucket = config.FALLBACK_CATEGORY
        for cat, keywords in config.CATEGORY_KEYWORDS:
            if any(kw in text for kw in keywords):
                bucket = cat
                break
        counts[bucket] += 1
    if not counts:
        return {}, None, None
    top_cat = max(counts, key=lambda c: counts[c])
    total = sum(counts.values())
    return dict(counts), top_cat, counts[top_cat] / total


def compute_metrics(wallet, snapshot_date):
    """由單一錢包 snapshot JSON 計算全部分類指標。

    wallet: fetch.py 落地的 {address, activity, positions, value, pnl, ...}
    snapshot_date: "YYYY-MM-DD"（recent-30d 視窗的右端）
    """
    addr = str(wallet.get("address", "")).lower()
    try:
        end_ts = datetime.strptime(snapshot_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc).timestamp() + DAY_SEC
    except (TypeError, ValueError):
        end_ts = datetime.now(timezone.utc).timestamp()

    points = parse_pnl_curve(wallet.get("pnl"))
    trades = parse_trades(wallet.get("activity"))
    n_trades = len(trades)

    if points:
        pnl_source = "curve"
        monthly = monthly_from_curve(points)
        total_pnl = points[-1][1] - points[0][1]
        dd = max_drawdown_pct([v for _, v in points])
        recent30 = recent_pnl(points, end_ts)
        low_confidence = False
    elif n_trades:
        pnl_source = "activity_approx"
        monthly = monthly_from_activity(trades)
        total_pnl = sum(monthly.values()) if monthly else None
        cumulative, acc = [], 0.0
        for m in sorted(monthly):
            acc += monthly[m]
            cumulative.append(acc)
        dd = max_drawdown_pct(cumulative)
        recent30 = recent_pnl_from_activity(trades, end_ts)
        low_confidence = True
    else:
        pnl_source = None
        monthly, total_pnl, dd, recent30 = {}, None, None, None
        low_confidence = True

    # 活躍月 = |月度 PnL| 有感的月份 ∪ 有交易的月份
    pnl_months = {m for m, v in monthly.items() if abs(v) > 0.01}
    trade_months = {_month_key(t["ts"]) for t in trades if t["ts"] is not None}
    active_months = len(pnl_months | trade_months)

    pos_ratio = None
    if pnl_months:
        pos_ratio = sum(1 for m in pnl_months if monthly[m] > 0) / len(pnl_months)
    best_month = max(monthly.values()) if monthly else None

    freq = (n_trades / len(trade_months)) if trade_months else None
    counts, top_cat, top_share = categorize(trades)

    # 閒置天數：最後一筆交易與最後一次 PnL 變動，取較晚者距 snapshot 的天數
    last_trade_ts = max((t["ts"] for t in trades if t["ts"] is not None), default=None)
    last_move_ts = None
    if points:
        last_move_ts = points[0][0]
        final_val = points[-1][1]
        for i in range(len(points) - 1, 0, -1):
            if points[i - 1][1] != final_val:
                last_move_ts = points[i][0]
                break
    last_active_ts = max((ts for ts in (last_trade_ts, last_move_ts) if ts is not None),
                         default=None)
    days_idle = ((end_ts - last_active_ts) / DAY_SEC) if last_active_ts is not None else None

    # 實際活動跨度（天）：最早到最晚的 PnL 點/交易，防日曆月計數高估資歷
    first_trade_ts = min((t["ts"] for t in trades if t["ts"] is not None), default=None)
    first_ts_cands = [ts for ts in (first_trade_ts, points[0][0] if points else None)
                      if ts is not None]
    span_days = None
    if first_ts_cands and last_active_ts is not None:
        span_days = (last_active_ts - min(first_ts_cands)) / DAY_SEC

    # 目前持倉價值（value 端點：[{user, value}] 或 {value: x}；缺資料 → None）
    current_value = None
    raw_value = wallet.get("value")
    if isinstance(raw_value, list) and raw_value and isinstance(raw_value[0], dict):
        current_value = raw_value[0].get("value")
    elif isinstance(raw_value, dict):
        current_value = raw_value.get("value")
    try:
        current_value = float(current_value) if current_value is not None else None
    except (TypeError, ValueError):
        current_value = None

    return {
        "address": addr,
        "snapshot_date": snapshot_date,
        "pnl_source": pnl_source,
        "low_confidence": low_confidence,
        "total_pnl": round(total_pnl, 2) if total_pnl is not None else None,
        "monthly_pnl": {m: round(v, 2) for m, v in sorted(monthly.items())},
        "active_months": active_months,
        "positive_month_ratio": round(pos_ratio, 3) if pos_ratio is not None else None,
        "best_month_pnl": round(best_month, 2) if best_month is not None else None,
        "max_drawdown_pct": round(dd, 4) if dd is not None else None,
        "recent_30d_pnl": round(recent30, 2) if recent30 is not None else None,
        "n_trades": n_trades,
        "trade_months": len(trade_months),
        "trades_per_month": round(freq, 1) if freq is not None else None,
        "avg_hold_hours": (lambda h: round(h, 3) if h is not None else None)(avg_hold_hours(trades)),
        "category_counts": counts,
        "top_category": top_cat,
        "top_category_share": round(top_share, 3) if top_share is not None else None,
        "days_idle": round(days_idle, 1) if days_idle is not None else None,
        "current_value": round(current_value, 2) if current_value is not None else None,
        "span_days": round(span_days, 1) if span_days is not None else None,
        "activity_truncated": bool(wallet.get("activity_truncated")),
        "fetch_errors": wallet.get("errors") or [],
    }


# ---------------------------------------------------------------------------
# 分類
# ---------------------------------------------------------------------------

def classify(m):
    """回傳 (label, reasons)。門檻全在 config.py。"""
    reasons = []

    # insufficient_data：連近似月度序列都拼不出，或無曲線且交易太少
    if not m["monthly_pnl"]:
        return "insufficient_data", ["無 PnL 曲線且無可用交易紀錄"]
    if m["pnl_source"] != "curve" and m["n_trades"] < config.MIN_TRADES_FOR_CLASSIFICATION:
        return "insufficient_data", [
            f"無 PnL 曲線且交易僅 {m['n_trades']} 筆 (<{config.MIN_TRADES_FOR_CLASSIFICATION})"]

    # dormant：閒置超過門檻天數且目前持倉近零 → 無單可跟，優先於一切歷史型態。
    # value 缺資料（None）時不判 dormant，避免端點故障造成誤殺。
    idle, cur_val = m.get("days_idle"), m.get("current_value")
    if (idle is not None and idle > config.DORMANT_MAX_IDLE_DAYS
            and cur_val is not None and cur_val <= config.DORMANT_MAX_CURRENT_VALUE):
        return "dormant", [
            f"閒置 {idle:.0f} 天 > {config.DORMANT_MAX_IDLE_DAYS} 且持倉 ${cur_val:,.0f} "
            f"<= {config.DORMANT_MAX_CURRENT_VALUE:,.0f}"]

    # mm_bot_like
    freq = m["trades_per_month"]
    if freq is not None and freq > config.MM_BOT_TRADES_PER_MONTH:
        return "mm_bot_like", [f"頻率 {freq:.0f} 筆/月 > {config.MM_BOT_TRADES_PER_MONTH}"]
    hold = m["avg_hold_hours"]
    if hold is not None and hold < config.MM_BOT_MAX_AVG_HOLD_HOURS:
        return "mm_bot_like", [f"平均持有 {hold:.2f} 小時 < {config.MM_BOT_MAX_AVG_HOLD_HOURS}"]

    # one_hit
    if m["active_months"] < config.ONE_HIT_MIN_ACTIVE_MONTHS:
        return "one_hit", [f"活躍月數 {m['active_months']} < {config.ONE_HIT_MIN_ACTIVE_MONTHS}"]
    total, best = m["total_pnl"], m["best_month_pnl"]
    if (total is not None and total > 0 and best is not None
            and best > config.ONE_HIT_BEST_MONTH_SHARE * total):
        return "one_hit", [
            f"最佳月 {best:,.0f} > {config.ONE_HIT_BEST_MONTH_SHARE:.0%} × 總 PnL {total:,.0f}"]

    # consistent 核心條件
    ratio, dd = m["positive_month_ratio"], m["max_drawdown_pct"]
    lo, hi = config.CONSISTENT_FREQ_RANGE
    span = m.get("span_days")
    core_checks = {
        f"活躍月數 {m['active_months']} >= {config.CONSISTENT_MIN_ACTIVE_MONTHS}":
            m["active_months"] >= config.CONSISTENT_MIN_ACTIVE_MONTHS,
        f"活動跨度 {span} 天 >= {config.CONSISTENT_MIN_SPAN_DAYS}":
            span is not None and span >= config.CONSISTENT_MIN_SPAN_DAYS,
        f"正月比率 {ratio} >= {config.CONSISTENT_MIN_POSITIVE_MONTH_RATIO}":
            ratio is not None and ratio >= config.CONSISTENT_MIN_POSITIVE_MONTH_RATIO,
        f"總 PnL {total} > {config.CONSISTENT_MIN_TOTAL_PNL:,.0f}":
            total is not None and total > config.CONSISTENT_MIN_TOTAL_PNL,
        f"回撤 {dd} < {config.CONSISTENT_MAX_DRAWDOWN_PCT:.0%} peak":
            dd is not None and dd < config.CONSISTENT_MAX_DRAWDOWN_PCT,
        f"頻率 {freq} 在 {lo:.0f}–{hi:.0f} 筆/月":
            freq is not None and lo <= freq <= hi,
    }
    if all(core_checks.values()):
        recent = m["recent_30d_pnl"]
        if (recent is not None and total is not None and total > 0
                and recent < config.DEGRADED_RECENT_PNL_FRACTION * total):
            return "degraded", [
                f"符合 consistent 核心條件，但近 30 天 PnL {recent:,.0f} < "
                f"{config.DEGRADED_RECENT_PNL_FRACTION:.0%} × 總 PnL {total:,.0f}"]
        return "consistent_winner", [k for k in core_checks]
    reasons = [k for k, ok in core_checks.items() if not ok]
    return "choppy", reasons or ["不符合任何特定型態"]


CLASS_ORDER = ["consistent_winner", "degraded", "dormant", "one_hit", "mm_bot_like",
               "choppy", "insufficient_data"]


# ---------------------------------------------------------------------------
# 報告產生
# ---------------------------------------------------------------------------

def summarize_endpoint_health(meta):
    """meta.json 的 endpoint_health（每請求一筆）→ 按 host+path 聚合。"""
    groups = {}
    for rec in (meta or {}).get("endpoint_health", []):
        url = rec.get("url") or ""
        try:
            parts = urlsplit(url)
            key = f"{parts.netloc}{parts.path}"
        except ValueError:
            key = url[:60]
        g = groups.setdefault(key, {"endpoint": key, "ok": 0, "failed": 0,
                                    "sample_error": None})
        if rec.get("ok"):
            g["ok"] += 1
        else:
            g["failed"] += 1
            if g["sample_error"] is None:
                g["sample_error"] = f"status={rec.get('status')} {rec.get('error') or ''}".strip()
    return sorted(groups.values(), key=lambda g: g["endpoint"])


def check_ground_truth(results):
    """seeds 是否如預期分類。回傳 [{address, expected, actual, ok}]。"""
    out = []
    by_addr = {r["metrics"]["address"]: r for r in results}
    for addr, expected in config.GROUND_TRUTH_EXPECTED.items():
        rec = by_addr.get(addr.lower())
        actual = rec["classification"] if rec else None
        out.append({
            "address": addr.lower(),
            "expected": expected,
            "actual": actual,
            "ok": actual in expected,
            "note": None if rec else "snapshot 中無此錢包的資料（fetch 失敗或未列入宇宙）",
        })
    return out


def _fmt(val, spec=",.0f"):
    if val is None:
        return "—"
    try:
        return format(val, spec)
    except (TypeError, ValueError):
        return str(val)


def build_markdown(date, results, meta, ground_truth, verdict):
    counts = defaultdict(int)
    for r in results:
        counts[r["classification"]] += 1
    total_wallets = len(results)

    lines = [
        f"# Polymarket 聰明錢存在性檢驗 — {date}",
        "",
        "> 純唯讀分析報告。宇宙取自今日排行榜＋seeds，**有倖存者偏差**；",
        "> 本檢驗證明的是「存在性」，非「跟得到」。前瞻持續性需觀察器累積數據驗證。",
        "",
        "## 1. 端點健康",
        "",
        "| 端點 | 成功 | 失敗 | 失敗樣本 |",
        "|---|---:|---:|---|",
    ]
    health = summarize_endpoint_health(meta)
    if health:
        for g in health:
            err = (g["sample_error"] or "—").replace("|", "\\|")[:120]
            lines.append(f"| `{g['endpoint']}` | {g['ok']} | {g['failed']} | {err} |")
    else:
        lines.append("| （meta.json 缺失或無請求紀錄） | — | — | — |")

    lines += ["", "## 2. 分類統計", "",
              "| 分類 | 錢包數 | 佔比 |", "|---|---:|---:|"]
    for cls in CLASS_ORDER:
        n = counts.get(cls, 0)
        pct = f"{n / total_wallets:.0%}" if total_wallets else "—"
        lines.append(f"| {cls} | {n} | {pct} |")
    lines.append(f"| **合計** | **{total_wallets}** | |")

    lines += ["", "## 3. consistent_winner 明細", ""]
    winners = [r for r in results if r["classification"] == "consistent_winner"]
    if winners:
        lines += ["| 地址 | 總 PnL | 正月比率 | 峰值回撤 | 頻率(筆/月) | 主類別 | 低信心 |",
                  "|---|---:|---:|---:|---:|---|---|"]
        for r in sorted(winners, key=lambda x: -(x["metrics"]["total_pnl"] or 0)):
            m = r["metrics"]
            cat = f"{m['top_category']} ({_fmt(m['top_category_share'], '.0%')})" \
                if m["top_category"] else "—"
            lines.append(
                f"| `{m['address']}` | ${_fmt(m['total_pnl'])} "
                f"| {_fmt(m['positive_month_ratio'], '.0%')} "
                f"| {_fmt(m['max_drawdown_pct'], '.0%')} "
                f"| {_fmt(m['trades_per_month'], ',.1f')} "
                f"| {cat} | {'⚠️ 是' if m['low_confidence'] else '否'} |")
    else:
        lines.append("（本日無 consistent_winner）")

    lines += ["", "## 4. Ground-truth 校驗", ""]
    if ground_truth:
        for g in ground_truth:
            exp = " / ".join(g["expected"])
            if g["ok"]:
                lines.append(f"- ✅ `{g['address']}`：預期 {exp}，實際 **{g['actual']}** — 符合")
            else:
                lines.append(
                    f"- ❌ **【不符，分類器需檢查】** `{g['address']}`：預期 {exp}，"
                    f"實際 **{g['actual']}**"
                    + (f"（{g['note']}）" if g["note"] else ""))
    else:
        lines.append("（無 ground-truth 種子）")

    lines += ["", "## 5. 裁決", "",
              f"consistent_winner 數量：**{counts.get('consistent_winner', 0)}**", "",
              f"**{verdict}**", "",
              "限制與聲明：",
              "- 錢包宇宙取自今日排行榜（＋seeds），存在倖存者偏差：只看得到現在還在榜上的贏家。",
              "- 本檢驗證明的是聰明錢的「存在性」，不是「跟得到」——前瞻持續性需觀察器逐日累積數據驗證。",
              "- 標注低信心（low_confidence）的錢包，其 PnL 由 activity 現金流近似，僅供參考。",
              "- 本工具純唯讀，不執行任何交易。", ""]
    return "\n".join(lines)


def decide_verdict(n_winners):
    if n_winners >= config.VERDICT_STRONG_MIN_WINNERS:
        return "聰明錢存在（存在性檢驗通過；前瞻持續性需觀察器累積數據驗證）"
    if n_winners >= config.VERDICT_WEAK_MIN_WINNERS:
        return "弱存在（樣本內僅少數 consistent_winner，證據不足，需持續觀察）"
    return "未發現（本日樣本內沒有符合 consistent_winner 條件的錢包）"


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def load_snapshot(snapshot_dir):
    """回傳 (wallets, meta)。單檔壞掉跳過並記錄，不 crash。"""
    snapshot_dir = Path(snapshot_dir)
    wallets, load_errors = [], []
    wallets_dir = snapshot_dir / "wallets"
    if wallets_dir.is_dir():
        for f in sorted(wallets_dir.glob("*.json")):
            try:
                wallets.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception as exc:
                load_errors.append(f"{f.name}: {exc}")
    meta = None
    meta_path = snapshot_dir / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as exc:
            load_errors.append(f"meta.json: {exc}")
    return wallets, meta, load_errors


def run_verification(snapshot_dir, report_dir):
    """核心進入點（tests 直接呼叫）。回傳完整結果 dict 並寫出 md/json。"""
    snapshot_dir = Path(snapshot_dir)
    report_dir = Path(report_dir)
    date = snapshot_dir.name
    wallets, meta, load_errors = load_snapshot(snapshot_dir)

    results = []
    for w in wallets:
        try:
            m = compute_metrics(w, date)
            label, reasons = classify(m)
        except Exception as exc:  # 單錢包炸掉不影響整體
            m = {"address": str(w.get("address", "?")).lower()}
            label, reasons = "insufficient_data", [f"指標計算例外：{exc}"]
        results.append({"metrics": m, "classification": label, "reasons": reasons})

    counts = defaultdict(int)
    for r in results:
        counts[r["classification"]] += 1
    ground_truth = check_ground_truth(results)
    verdict = decide_verdict(counts.get("consistent_winner", 0))

    payload = {
        "date": date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_dir": str(snapshot_dir),
        "verdict": verdict,
        "classification_counts": dict(counts),
        "wallets": {r["metrics"].get("address", f"unknown_{i}"): r
                    for i, r in enumerate(results)},
        "ground_truth": ground_truth,
        "endpoint_health_summary": summarize_endpoint_health(meta),
        "snapshot_load_errors": load_errors,
    }

    report_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_dir / f"verification_{date}.md"
    json_path = report_dir / f"verification_{date}.json"
    md_path.write_text(build_markdown(date, results, meta, ground_truth, verdict),
                       encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"[verify] wallets={len(results)} winners={counts.get('consistent_winner', 0)}")
    print(f"[verify] report: {md_path}")
    print(f"[verify] json:   {json_path}")
    print(f"[verify] verdict: {verdict}")
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description="Polymarket smart-money existence check")
    parser.add_argument("--snapshot", required=True,
                        help="snapshot 目錄，例：data/snapshots/2026-07-10")
    parser.add_argument("--report-dir", default=str(BASE_DIR / "data" / "reports"))
    args = parser.parse_args(argv)

    snapshot_dir = Path(args.snapshot)
    if not snapshot_dir.is_absolute():
        cand = BASE_DIR / snapshot_dir
        snapshot_dir = cand if cand.exists() else snapshot_dir
    report_dir = Path(args.report_dir)
    if not report_dir.is_absolute():
        report_dir = BASE_DIR / report_dir

    if not snapshot_dir.is_dir():
        print(f"[verify] snapshot 目錄不存在：{snapshot_dir}", file=sys.stderr)
        return 1
    run_verification(snapshot_dir, report_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
