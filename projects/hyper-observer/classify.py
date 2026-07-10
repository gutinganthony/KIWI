#!/usr/bin/env python3
"""hyper-observer classify：Hyperliquid 永續「聰明錢存在性」檢驗（一次性報告）。

用法：
    python3 classify.py --snapshot data/snapshots/{date} [--report-dir data/reports]

對 snapshot 內每個錢包，由 portfolio + userFills + clearinghouseState 計算永續專用指標
（用研究 §4 的風險調整 PnL / profit factor / 量-PnL 比 / 淨方向 / 槓桿 取代天真勝率），
然後按 config.py 的門檻分類：
    consistent_winner / blowup_risk / wash_suspect / one_hit / dormant /
    choppy / insufficient_data。

輸出：
- data/reports/verification_{date}.md   （人讀報告）
- data/reports/verification_{date}.json （機器可讀完整結果）

重要聲明：錢包宇宙取自「今日」leaderboard（＋seeds），天生有倖存者偏差；
且永續排行榜被空投刷量嚴重污染。本檢驗證明的是聰明錢的「存在性」，非「跟得到」。
純唯讀分析，不含任何下單、簽章、私鑰功能。
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import config

BASE_DIR = Path(__file__).resolve().parent
DAY_SEC = 86400
EPS = 1e-9


# ---------------------------------------------------------------------------
# 原始資料解析（防禦性：字串數值、ms/s 時戳、list-of-pairs / dict 多形）
# ---------------------------------------------------------------------------

def _to_float(val):
    """寬鬆轉 float；壞值回 None。"""
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _norm_ts(val):
    """時間戳正規化成 epoch 秒；壞值回 None。"""
    ts = _to_float(val)
    if ts is None:
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


def parse_portfolio(raw):
    """portfolio 原始回應 → {window_name: {accountValueHistory, pnlHistory, vlm}}。

    Hyperliquid 回 list-of-pairs：[["day", {...}], ["perpAllTime", {...}], ...]；
    也防禦 dict 形 {name: {...}}。
    """
    out = {}
    if isinstance(raw, list):
        for item in raw:
            if (isinstance(item, (list, tuple)) and len(item) == 2
                    and isinstance(item[0], str) and isinstance(item[1], dict)):
                out[item[0]] = item[1]
    elif isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, dict):
                out[k] = v
    return out


def pick_window(parsed):
    """選 config 指定的主視窗，缺則退回 fallback。回 (window_dict, window_name)。"""
    for name in (config.PORTFOLIO_PRIMARY_WINDOW, config.PORTFOLIO_FALLBACK_WINDOW):
        if isinstance(parsed.get(name), dict):
            return parsed[name], name
    return None, None


def parse_history(raw):
    """[[ts, val], ...]（val 可能是字串）→ 排序後 [(ts, float_val)]。"""
    points = []
    if not isinstance(raw, list):
        return points
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            ts = _norm_ts(item[0])
            val = _to_float(item[1])
            if ts is not None and val is not None:
                points.append((ts, val))
    points.sort(key=lambda x: x[0])
    return points


def parse_fills(raw):
    """userFills 原始回應 → 正規化成交清單。

    回 [{ts, coin, px, sz, side, closed_pnl, fee, dir, is_liquidation}]。
    注意：Hyperliquid 的 closedPnl 對贏和輸的平倉都有值（無贏家倖存者偏誤）。
    """
    if isinstance(raw, dict):
        for key in ("fills", "data", "userFills"):
            if isinstance(raw.get(key), list):
                raw = raw[key]
                break
        else:
            return []
    if not isinstance(raw, list):
        return []
    out = []
    for it in raw:
        if not isinstance(it, dict):
            continue
        d = str(it.get("dir") or "")
        is_liq = bool(it.get("liquidation")) or ("liquidat" in d.lower())
        out.append({
            "ts": _norm_ts(it.get("time")),
            "coin": str(it.get("coin") or ""),
            "px": _to_float(it.get("px")),
            "sz": _to_float(it.get("sz")),
            "side": str(it.get("side") or ""),
            "closed_pnl": _to_float(it.get("closedPnl")),
            "fee": _to_float(it.get("fee")),
            "dir": d,
            "is_liquidation": is_liq,
        })
    out.sort(key=lambda f: (f["ts"] is None, f["ts"] or 0))
    return out


def parse_positions(raw):
    """clearinghouseState 原始回應 → 正規化未平倉部位清單。

    回 [{coin, szi, side, entry_px, position_value, unrealized_pnl, leverage_value,
        leverage_type, liquidation_px, margin_used, max_leverage, cum_funding}]。
    欄位缺失一律回 None，不臆造。track_wallet.py 亦 import 使用（單一來源）。
    """
    if not isinstance(raw, dict):
        return []
    asset_positions = raw.get("assetPositions")
    if not isinstance(asset_positions, list):
        return []
    out = []
    for ap in asset_positions:
        if not isinstance(ap, dict):
            continue
        pos = ap.get("position") if isinstance(ap.get("position"), dict) else ap
        if not isinstance(pos, dict):
            continue
        szi = _to_float(pos.get("szi"))
        side = None
        if szi is not None:
            side = "long" if szi > 0 else ("short" if szi < 0 else "flat")
        lev = pos.get("leverage") if isinstance(pos.get("leverage"), dict) else {}
        cum = pos.get("cumFunding") if isinstance(pos.get("cumFunding"), dict) else {}
        out.append({
            "coin": str(pos.get("coin") or ""),
            "szi": szi,
            "side": side,
            "entry_px": _to_float(pos.get("entryPx")),
            "position_value": _to_float(pos.get("positionValue")),
            "unrealized_pnl": _to_float(pos.get("unrealizedPnl")),
            "leverage_value": _to_float(lev.get("value")),
            "leverage_type": str(lev.get("type") or "") or None,
            "liquidation_px": _to_float(pos.get("liquidationPx")),
            "margin_used": _to_float(pos.get("marginUsed")),
            "max_leverage": _to_float(pos.get("maxLeverage")),
            "cum_funding_all_time": _to_float(cum.get("allTime")),
        })
    return out


def account_summary(raw):
    """clearinghouseState → {account_value, total_ntl_pos, total_margin_used, withdrawable}。"""
    if not isinstance(raw, dict):
        return {"account_value": None, "total_ntl_pos": None,
                "total_margin_used": None, "withdrawable": None}
    summ = None
    for key in ("marginSummary", "crossMarginSummary"):
        if isinstance(raw.get(key), dict):
            summ = raw[key]
            break
    summ = summ or {}
    return {
        "account_value": _to_float(summ.get("accountValue")),
        "total_ntl_pos": _to_float(summ.get("totalNtlPos")),
        "total_margin_used": _to_float(summ.get("totalMarginUsed")),
        "withdrawable": _to_float(raw.get("withdrawable")),
    }


def total_funding(raw_funding):
    """userFunding → 資金費淨總額（usdc 加總）；解析不到回 None。"""
    if isinstance(raw_funding, dict):
        for key in ("fundings", "data"):
            if isinstance(raw_funding.get(key), list):
                raw_funding = raw_funding[key]
                break
        else:
            return None
    if not isinstance(raw_funding, list):
        return None
    total, seen = 0.0, False
    for it in raw_funding:
        if not isinstance(it, dict):
            continue
        delta = it.get("delta") if isinstance(it.get("delta"), dict) else it
        v = _to_float(delta.get("usdc")) if isinstance(delta, dict) else None
        if v is not None:
            total += v
            seen = True
    return total if seen else None


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


def max_drawdown_pct(series):
    """峰值回撤占 peak 的比例。series = 依時間排序的累積 PnL 值。"""
    peak, worst = None, 0.0
    for val in series:
        if peak is None or val > peak:
            peak = val
        if peak is not None and peak > EPS:
            worst = max(worst, (peak - val) / peak)
    return worst if peak is not None and peak > EPS else None


def max_single_day_crash_pct(points, min_peak):
    """最大單步崩跌（占 running peak 的比例），只在 peak >= min_peak 時計算。

    用來抓 James Wynn 型「$100M → $900」單日崩塌；PnL≈0 的刷量戶因 peak 太小而不計，
    避免小額波動被誤判崩跌。
    """
    peak, worst = None, 0.0
    for i, (_, val) in enumerate(points):
        if peak is None or val > peak:
            peak = val
        if i > 0 and peak is not None and peak >= min_peak:
            drop = points[i - 1][1] - val
            if drop > 0:
                worst = max(worst, drop / peak)
    return worst


def profit_factor_stats(fills):
    """由 closedPnl 算 profit factor / 平均獲利÷平均虧損 / 已實現勝率（僅供參考）。"""
    wins = [f["closed_pnl"] for f in fills
            if f["closed_pnl"] is not None and f["closed_pnl"] > 0]
    losses = [f["closed_pnl"] for f in fills
              if f["closed_pnl"] is not None and f["closed_pnl"] < 0]
    n_closed = len(wins) + len(losses)
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    if gross_loss < EPS:
        pf = 999.0 if gross_profit > EPS else None
    else:
        pf = gross_profit / gross_loss
    avg_win = (gross_profit / len(wins)) if wins else None
    avg_loss = (gross_loss / len(losses)) if losses else None
    win_rate = (len(wins) / n_closed) if n_closed else None
    return {
        "profit_factor": pf,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "realized_win_rate": win_rate,
        "n_closed_fills": n_closed,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
    }


def avg_hold_hours(fills):
    """由 dir 的 Open/Close 逐 coin FIFO 配對估平均持倉小時；配不到回 None。"""
    opens = defaultdict(list)
    holds = []
    for f in fills:
        if f["ts"] is None or not f["coin"]:
            continue
        d = f["dir"].lower()
        if "open" in d:
            opens[f["coin"]].append(f["ts"])
        elif "close" in d and opens[f["coin"]]:
            holds.append(f["ts"] - opens[f["coin"]].pop(0))
    if not holds:
        return None
    return (sum(holds) / len(holds)) / 3600.0


def net_direction_ratio(fills):
    """|買量-賣量| / (買量+賣量)。≈0 → 來回對敲無淨方向（刷量旗標）。配不到回 None。"""
    buy, sell = 0.0, 0.0
    for f in fills:
        if f["px"] is None or f["sz"] is None:
            continue
        notional = abs(f["px"] * f["sz"])
        if f["side"].upper().startswith("B"):
            buy += notional
        else:
            sell += notional
    total = buy + sell
    if total <= EPS:
        return None
    return abs(buy - sell) / total


def compute_metrics(wallet, snapshot_date):
    """由單一錢包 snapshot JSON 計算全部永續分類指標。

    wallet: fetch.py 落地的 {address, clearinghouseState, portfolio, userFills, userFunding, ...}
    snapshot_date: "YYYY-MM-DD"（idle 視窗的右端）
    """
    addr = str(wallet.get("address", "")).lower()
    try:
        end_ts = datetime.strptime(snapshot_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc).timestamp() + DAY_SEC
    except (TypeError, ValueError):
        end_ts = datetime.now(timezone.utc).timestamp()

    parsed_pf = parse_portfolio(wallet.get("portfolio"))
    window, window_name = pick_window(parsed_pf)
    pnl_points = parse_history(window.get("pnlHistory")) if window else []
    vlm = _to_float(window.get("vlm")) if window else None

    fills = parse_fills(wallet.get("userFills"))
    n_fills = len(fills)
    positions = parse_positions(wallet.get("clearinghouseState"))
    acct = account_summary(wallet.get("clearinghouseState"))

    # --- PnL 曲線衍生指標 ---
    if pnl_points:
        pnl_source = "portfolio_curve"
        total_pnl = pnl_points[-1][1] - pnl_points[0][1]
        monthly = monthly_from_curve(pnl_points)
        dd = max_drawdown_pct([v for _, v in pnl_points])
        crash = max_single_day_crash_pct(pnl_points, config.BLOWUP_MIN_PEAK_FOR_CRASH)
        peak_pnl = max(v for _, v in pnl_points)
    else:
        pnl_source = None
        total_pnl, monthly, dd, crash, peak_pnl = None, {}, None, 0.0, None

    pnl_months = {m for m, v in monthly.items() if abs(v) > 0.01}
    pos_ratio = None
    if pnl_months:
        pos_ratio = sum(1 for m in pnl_months if monthly[m] > 0) / len(pnl_months)
    best_month = max(monthly.values()) if monthly else None
    active_months = len(pnl_months)

    # --- 活躍跨度 / 閒置天數（PnL 曲線點 ∪ 成交時間）---
    fill_ts = [f["ts"] for f in fills if f["ts"] is not None]
    curve_ts = [ts for ts, _ in pnl_points]
    all_ts = fill_ts + curve_ts
    span_days = ((max(all_ts) - min(all_ts)) / DAY_SEC) if all_ts else None
    last_active = max(all_ts) if all_ts else None
    days_idle = ((end_ts - last_active) / DAY_SEC) if last_active is not None else None

    # --- 成交衍生指標 ---
    pf_stats = profit_factor_stats(fills)
    hold_h = avg_hold_hours(fills)
    net_dir = net_direction_ratio(fills)
    had_liquidation = any(f["is_liquidation"] for f in fills)
    coin_counts = Counter(f["coin"] for f in fills if f["coin"])
    top_coin = coin_counts.most_common(1)[0][0] if coin_counts else None

    # --- 量/PnL 比（刷量旗標）---
    vlm_to_pnl = None
    if vlm is not None and total_pnl is not None:
        vlm_to_pnl = vlm / max(abs(total_pnl), EPS)

    # --- clearinghouseState 衍生：目前槓桿/持倉/保證金模式 ---
    lev_values = [p["leverage_value"] for p in positions if p["leverage_value"] is not None]
    current_max_leverage = max(lev_values) if lev_values else None
    has_extreme_leverage = (current_max_leverage is not None
                            and current_max_leverage >= config.EXTREME_LEVERAGE_FLAG)
    margin_types = sorted({p["leverage_type"] for p in positions if p["leverage_type"]})

    return {
        "address": addr,
        "snapshot_date": snapshot_date,
        "pnl_source": pnl_source,
        "portfolio_window": window_name,
        "low_confidence": pnl_source is None,
        "total_pnl": round(total_pnl, 2) if total_pnl is not None else None,
        "peak_pnl": round(peak_pnl, 2) if peak_pnl is not None else None,
        "monthly_pnl": {m: round(v, 2) for m, v in sorted(monthly.items())},
        "active_months": active_months,
        "positive_month_ratio": round(pos_ratio, 3) if pos_ratio is not None else None,
        "best_month_pnl": round(best_month, 2) if best_month is not None else None,
        "max_drawdown_pct": round(dd, 4) if dd is not None else None,
        "max_single_day_crash_pct": round(crash, 4) if crash is not None else None,
        "span_days": round(span_days, 1) if span_days is not None else None,
        "days_idle": round(days_idle, 1) if days_idle is not None else None,
        "n_fills": n_fills,
        "profit_factor": round(pf_stats["profit_factor"], 3)
        if pf_stats["profit_factor"] is not None else None,
        "avg_win": round(pf_stats["avg_win"], 2) if pf_stats["avg_win"] is not None else None,
        "avg_loss": round(pf_stats["avg_loss"], 2) if pf_stats["avg_loss"] is not None else None,
        "realized_win_rate": round(pf_stats["realized_win_rate"], 3)
        if pf_stats["realized_win_rate"] is not None else None,
        "avg_hold_hours": round(hold_h, 3) if hold_h is not None else None,
        "net_direction_ratio": round(net_dir, 4) if net_dir is not None else None,
        "had_liquidation": had_liquidation,
        "top_coin": top_coin,
        "vlm": round(vlm, 2) if vlm is not None else None,
        "vlm_to_pnl_ratio": round(vlm_to_pnl, 2) if vlm_to_pnl is not None else None,
        "funding_total": (lambda x: round(x, 2) if x is not None else None)(
            total_funding(wallet.get("userFunding"))),
        "n_open_positions": len(positions),
        "current_max_leverage": current_max_leverage,
        "has_extreme_leverage": has_extreme_leverage,
        "margin_types": margin_types,
        "account_value": round(acct["account_value"], 2)
        if acct["account_value"] is not None else None,
        "fetch_errors": wallet.get("errors") or [],
    }


# ---------------------------------------------------------------------------
# 分類
# ---------------------------------------------------------------------------

def classify(m):
    """回傳 (label, reasons)。門檻全在 config.py。順序：安全性優先（爆倉/刷量早判）。"""
    has_curve = m["pnl_source"] == "portfolio_curve"

    # insufficient_data：無 PnL 曲線且成交太少 → 無從判斷
    if not has_curve and m["n_fills"] < config.MIN_FILLS_FOR_CLASSIFICATION:
        return "insufficient_data", [
            f"無 portfolio PnL 曲線且成交僅 {m['n_fills']} 筆 "
            f"(<{config.MIN_FILLS_FOR_CLASSIFICATION})"]
    if not m["monthly_pnl"] and m["n_fills"] < config.MIN_FILLS_FOR_CLASSIFICATION:
        return "insufficient_data", ["無月度 PnL 序列且成交紀錄不足"]

    # blowup_risk（優先於一切歷史型態：曾爆倉就是主導事實，高勝率無用）
    lev = m.get("current_max_leverage")
    dd = m.get("max_drawdown_pct")
    crash = m.get("max_single_day_crash_pct") or 0.0
    if m.get("had_liquidation"):
        return "blowup_risk", ["userFills 出現 liquidation（曾被強平）"]
    if crash >= config.BLOWUP_SINGLE_DAY_CRASH_PCT:
        return "blowup_risk", [
            f"PnL 曲線單步崩跌 {crash:.0%} >= {config.BLOWUP_SINGLE_DAY_CRASH_PCT:.0%}"]
    if (lev is not None and lev >= config.BLOWUP_EXTREME_LEVERAGE
            and dd is not None and dd >= config.BLOWUP_DRAWDOWN_PCT):
        return "blowup_risk", [
            f"目前槓桿 {lev:.0f}x >= {config.BLOWUP_EXTREME_LEVERAGE:.0f}x 且回撤 "
            f"{dd:.0%} >= {config.BLOWUP_DRAWDOWN_PCT:.0%}"]

    # wash_suspect（刷量／對敲：巨量但 PnL≈0，或無淨方向＋極短持倉高頻自成交）
    vlm = m.get("vlm")
    vpr = m.get("vlm_to_pnl_ratio")
    if (vlm is not None and vlm >= config.WASH_MIN_VLM
            and vpr is not None and vpr >= config.WASH_VLM_TO_PNL_RATIO):
        return "wash_suspect", [
            f"量 ${vlm:,.0f} 巨大且 量/PnL 比 {vpr:,.0f} >= "
            f"{config.WASH_VLM_TO_PNL_RATIO:,.0f}（巨量、PnL≈0）"]
    net = m.get("net_direction_ratio")
    hold = m.get("avg_hold_hours")
    if (net is not None and net <= config.WASH_NET_DIRECTION_MAX
            and hold is not None and hold < config.WASH_MAX_HOLD_HOURS
            and m["n_fills"] >= config.WASH_MIN_FILLS):
        return "wash_suspect", [
            f"淨方向 {net:.2%} <= {config.WASH_NET_DIRECTION_MAX:.0%} 且平均持倉 "
            f"{hold:.3f}h < {config.WASH_MAX_HOLD_HOURS}h 且高頻（{m['n_fills']} 筆）"]

    # dormant：閒置且目前無持倉 → 無單可跟
    idle = m.get("days_idle")
    if (idle is not None and idle > config.DORMANT_MAX_IDLE_DAYS
            and m["n_open_positions"] == 0):
        return "dormant", [
            f"閒置 {idle:.0f} 天 > {config.DORMANT_MAX_IDLE_DAYS} 且目前無持倉"]

    # one_hit：活躍太短，或單一最佳期主導
    span = m.get("span_days")
    if span is not None and span < config.ONE_HIT_MIN_SPAN_DAYS:
        return "one_hit", [f"活躍跨度 {span:.0f} 天 < {config.ONE_HIT_MIN_SPAN_DAYS}"]
    total, best = m.get("total_pnl"), m.get("best_month_pnl")
    if (total is not None and total > 0 and best is not None
            and best > config.ONE_HIT_BEST_MONTH_SHARE * total):
        return "one_hit", [
            f"最佳月 {best:,.0f} > {config.ONE_HIT_BEST_MONTH_SHARE:.0%} × 總 PnL {total:,.0f}"]

    # consistent_winner 核心條件（非 wash/blowup、槓桿合理、風險調整後仍穩定獲利）
    pf = m.get("profit_factor")
    ratio = m.get("positive_month_ratio")
    core_checks = {
        f"活動跨度 {span} 天 >= {config.CONSISTENT_MIN_SPAN_DAYS}":
            span is not None and span >= config.CONSISTENT_MIN_SPAN_DAYS,
        f"總 PnL {total} > {config.CONSISTENT_MIN_TOTAL_PNL:,.0f}":
            total is not None and total > config.CONSISTENT_MIN_TOTAL_PNL,
        f"回撤 {dd} < {config.CONSISTENT_MAX_DRAWDOWN_PCT:.0%} peak":
            dd is not None and dd < config.CONSISTENT_MAX_DRAWDOWN_PCT,
        f"profit factor {pf} >= {config.CONSISTENT_MIN_PROFIT_FACTOR}":
            pf is not None and pf >= config.CONSISTENT_MIN_PROFIT_FACTOR,
        f"目前槓桿 {lev} <= {config.CONSISTENT_MAX_LEVERAGE:.0f}x":
            lev is None or lev <= config.CONSISTENT_MAX_LEVERAGE,
        f"正月比率 {ratio} >= {config.CONSISTENT_MIN_POSITIVE_MONTH_RATIO}":
            ratio is not None and ratio >= config.CONSISTENT_MIN_POSITIVE_MONTH_RATIO,
    }
    if all(core_checks.values()):
        return "consistent_winner", [k for k in core_checks]
    return "choppy", [k for k, ok in core_checks.items() if not ok] or ["不符合任何特定型態"]


CLASS_ORDER = ["consistent_winner", "blowup_risk", "wash_suspect", "one_hit",
               "dormant", "choppy", "insufficient_data"]


# ---------------------------------------------------------------------------
# 報告產生
# ---------------------------------------------------------------------------

def summarize_endpoint_health(meta):
    """meta.json 的 endpoint_health（每請求一筆）→ 按 host+path 聚合。

    hyper 的 info 查詢皆打同一 URL，故 endpoint 名改用請求 name 的 type 前綴聚合。
    """
    groups = {}
    for rec in (meta or {}).get("endpoint_health", []):
        name = rec.get("name") or ""
        typ = name.split("[")[0] or "（未命名）"
        url = rec.get("url") or ""
        try:
            parts = urlsplit(url)
            host = f"{parts.netloc}{parts.path}"
        except ValueError:
            host = url[:60]
        key = f"{typ} @ {host}" if host else typ
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
    by_addr = {r["metrics"].get("address"): r for r in results}
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
        f"# Hyperliquid 永續聰明錢存在性檢驗 — {date}",
        "",
        "> 純唯讀分析報告。宇宙取自今日 leaderboard（＋seeds），**有倖存者偏差＋刷量污染**；",
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
        lines += ["| 地址 | 總 PnL | 峰值回撤 | profit factor | 目前槓桿 | 主力幣 | 活躍天 |",
                  "|---|---:|---:|---:|---:|---|---:|"]
        for r in sorted(winners, key=lambda x: -(x["metrics"]["total_pnl"] or 0)):
            m = r["metrics"]
            lines.append(
                f"| `{m['address']}` | ${_fmt(m['total_pnl'])} "
                f"| {_fmt(m['max_drawdown_pct'], '.0%')} "
                f"| {_fmt(m['profit_factor'], ',.2f')} "
                f"| {_fmt(m['current_max_leverage'], ',.0f')}x "
                f"| {m['top_coin'] or '—'} | {_fmt(m['span_days'], ',.0f')} |")
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
              "限制與醒目聲明：",
              "- **倖存者偏差**：宇宙取自今日 leaderboard（＋seeds），只看得到現在還在榜上的贏家。",
              "- **刷量污染**：Hyperliquid 空投以交易量計分，排行榜混雜大量 wash trading；"
              "本檢驗以量/PnL 比＋淨方向旗標排除疑似刷量戶，但無法百分百過濾。",
              "- **存在性 ≠ 跟得到**：本檢驗證明聰明錢的「存在性」，非「跟得到」——"
              "前瞻持續性需觀察器逐日累積數據驗證；跟單模擬器為下一個里程碑。",
              "- **槓桿風險**：永續高槓桿可造高勝率直到一次強平歸零（James Wynn 為活教材）；"
              "consistent_winner 已要求槓桿在合理範圍，但過往績效不保證未來不爆倉。",
              "- 標注低信心（low_confidence）的錢包缺 portfolio PnL 曲線，指標可信度較低。",
              "- 本工具**純唯讀**，只查公開 info API，不執行任何下單、簽章或錢包連線。", ""]
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
    """回傳 (wallets, meta, load_errors)。單檔壞掉跳過並記錄，不 crash。"""
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
    print(f"[classify] wallets={len(results)} winners={counts.get('consistent_winner', 0)}")
    print(f"[classify] report: {md_path}")
    print(f"[classify] json:   {json_path}")
    print(f"[classify] verdict: {verdict}")
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description="Hyperliquid perp smart-money existence check")
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
        print(f"[classify] snapshot 目錄不存在：{snapshot_dir}", file=sys.stderr)
        return 1
    run_verification(snapshot_dir, report_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
