#!/usr/bin/env python3
"""hyper-observer classify：Hyperliquid 永續「聰明錢存在性」檢驗（一次性報告）。

用法：
    python3 classify.py --snapshot data/snapshots/{date} [--report-dir data/reports]
        [--label scan]   # 掃描報告模式：檔名 scan_verification_{date}.md/json，
                         # winner 明細加「可跟」欄、裁決改兩級（winner N，其中 followable M）

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
import re
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


def max_drawdown_pct(series, min_peak):
    """峰值回撤占 peak 的比例（封頂於 1.0）。series = 依時間排序的累積 PnL 值。

    回撤語意上不超過 100%（把 peak 全數吐光即 1.0）。曲線跌破 0 時 (peak-val)/peak > 1，
    若 peak 又只是勉強過 0 的小正值就會爆成天文數字（觀測到 dd=7,802,892%），純屬除以小 peak
    的假象。故每步以 min(1.0, ·) 封頂，讓 dd 成為 [0,1] 的「峰值吐回比例」，與門檻語意一致。

    修正 A：只在 running peak >= min_peak 時才累計回撤。min_peak 取
    max(DD_MIN_PEAK_ABS, DD_MIN_PEAK_FRACTION × 全期峰值)，殺掉「早期小峰值→短暫負值」的假象
    （早期 $100 小峰值的 dip 因 peak 遠低於門檻而不計入）；running peak 從未達門檻回 None。
    """
    peak, worst, counted = None, 0.0, False
    for val in series:
        if peak is None or val > peak:
            peak = val
        if peak is not None and peak >= min_peak:
            counted = True
            worst = max(worst, min(1.0, (peak - val) / peak))
    return worst if counted else None


def max_single_day_crash_pct(points, min_peak):
    """最大單步崩跌（占 running peak 的比例，封頂於 1.0），只在 peak >= min_peak 時計算。

    用來抓 James Wynn 型「$100M → $900」單日崩塌；PnL≈0 的刷量戶因 peak 太小而不計，
    避免小額波動被誤判崩跌。

    BUG 1：當 peak 只是勉強過 min_peak 的小正值、下一步崩進深負，drop/peak 會爆成 284%、
    1586%（觀測值），這其實是「小正峰值→大負」的虧損戶、非槓桿崩塌。崩跌%語意上不超過
    100%，故每步以 min(1.0, drop/peak) 封頂；崩塌判據改以峰值回撤 max_drawdown_pct 為主。
    """
    peak, worst = None, 0.0
    for i, (_, val) in enumerate(points):
        if peak is None or val > peak:
            peak = val
        if i > 0 and peak is not None and peak >= min_peak:
            drop = points[i - 1][1] - val
            if drop > 0:
                worst = max(worst, min(1.0, drop / peak))
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
    # userFills 被 info API 截斷（近端窗）→ profit_factor/realized_win_rate 樣本偏誤大（BUG 3）
    fills_truncated = n_fills >= config.MAX_USER_FILLS
    positions = parse_positions(wallet.get("clearinghouseState"))
    acct = account_summary(wallet.get("clearinghouseState"))

    # --- PnL 曲線衍生指標 ---
    if pnl_points:
        pnl_source = "portfolio_curve"
        total_pnl = pnl_points[-1][1] - pnl_points[0][1]
        monthly = monthly_from_curve(pnl_points)
        peak_pnl = max(v for _, v in pnl_points)
        # 修正 A：回撤/崩跌共用的最小 peak 閘 = max(絕對地板, 全期峰值的固定比例)
        dd_min_peak = max(config.DD_MIN_PEAK_ABS, config.DD_MIN_PEAK_FRACTION * peak_pnl)
        dd = max_drawdown_pct([v for _, v in pnl_points], dd_min_peak)
        crash = max_single_day_crash_pct(pnl_points, dd_min_peak)
        # current_drawdown_pct：現值較全期峰值回落的比例（「近全損 vs 已復原」的判別信號）。
        # 只在峰值夠大（>= dd_min_peak）時有意義，否則回 None（避免小峰值假象）。
        final_pnl = pnl_points[-1][1]
        current_dd = (min(1.0, (peak_pnl - final_pnl) / peak_pnl)
                      if peak_pnl is not None and peak_pnl >= dd_min_peak else None)
    else:
        pnl_source = None
        total_pnl, monthly, dd, crash, peak_pnl, current_dd = None, {}, None, 0.0, None, None

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
    # 修正 B：由 fills 統計強平「次數」（is_liquidation 已寬鬆比對 dir/欄位含 'liquidat'），
    # 取代舊的「有無」布林。had_liquidation 保留供揭露，n_liquidations 供反覆爆倉判據。
    n_liquidations = sum(1 for f in fills if f["is_liquidation"])
    had_liquidation = n_liquidations > 0
    coin_counts = Counter(f["coin"] for f in fills if f["coin"])
    top_coin = coin_counts.most_common(1)[0][0] if coin_counts else None
    # 近 30 天成交筆數（≈每月交易頻率，followable 判定用）。userFills 只回近端 2000 筆，
    # 但「近 30 天」正好落在近端窗，此計數準確；若 30 天內就超過 2000 筆截斷，
    # 計數 =2000 遠超 SCAN_FOLLOWABLE_MAX_FREQ，判「不可跟」方向正確。
    n_fills_last_30d = sum(1 for f in fills
                           if f["ts"] is not None and f["ts"] >= end_ts - 30 * DAY_SEC)

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
        "current_drawdown_pct": round(current_dd, 4) if current_dd is not None else None,
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
        "n_fills_truncated": fills_truncated,
        "n_fills_last_30d": n_fills_last_30d,
        "had_liquidation": had_liquidation,
        "n_liquidations": n_liquidations,
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
    """回傳 (label, reasons)。門檻全在 config.py。順序：安全性優先（爆倉/資料不足/刷量早判）。"""
    has_curve = m["pnl_source"] == "portfolio_curve"
    lev = m.get("current_max_leverage")
    dd = m.get("max_drawdown_pct")
    cur_dd = m.get("current_drawdown_pct")
    span = m.get("span_days")
    n_liq = m.get("n_liquidations") or 0

    # 修正 B：反覆爆倉（>= BLOWUP_MIN_LIQUIDATIONS 次）＝真高風險硬事實，最高優先，即使
    # portfolio 缺失也照判（如 James Wynn 194 次）。單次歷史強平（1..2）不再強制 blowup，往下走
    # 正常分類（consistent/wash/choppy），風險於 metrics 的 n_liquidations/had_liquidation 揭露。
    if n_liq >= config.BLOWUP_MIN_LIQUIDATIONS:
        return "blowup_risk", [
            f"userFills 出現 {n_liq} 次強平 >= {config.BLOWUP_MIN_LIQUIDATIONS}（反覆爆倉，真高風險）"]

    # insufficient_data（BUG 4）：portfolio 曲線缺失（pnl_source 無、回撤/跨度皆無）→ 無 total_pnl/
    # dd/月度序列等核心信號可算，不得進 choppy/winner/blowup（除非上面反覆爆倉硬事實）。
    if not has_curve or (dd is None and span is None):
        return "insufficient_data", [
            "無 portfolio PnL 曲線（pnl_source 缺失或回撤/跨度皆無），核心信號不足以分類"]
    if not m["monthly_pnl"] and m["n_fills"] < config.MIN_FILLS_FOR_CLASSIFICATION:
        return "insufficient_data", ["無月度 PnL 序列且成交紀錄不足"]

    # blowup_risk（曲線衍生）：極端槓桿＋大回撤（條件 3），或峰值回撤大且「現值仍近全損」（條件 2）。
    # 修正 A/B：條件 2 以修正 A 後（加了 min_peak 閘）的峰值回撤為主，並要求 current_drawdown 亦大
    # （現值較峰值仍深陷、未復原）才判 blowup——避免大額淨正、深回撤後完全復原的錢包（如 +$181M
    # HFT，其歷史回撤真實但已回到峰值附近）被假回撤誤判、藏起真正候選贏家。
    # 條件 3 的極端槓桿本身即前瞻爆倉風險，故照舊只看槓桿＋回撤、不看是否復原。
    if (lev is not None and lev >= config.BLOWUP_EXTREME_LEVERAGE
            and dd is not None and dd >= config.BLOWUP_DRAWDOWN_PCT):
        return "blowup_risk", [
            f"目前槓桿 {lev:.0f}x >= {config.BLOWUP_EXTREME_LEVERAGE:.0f}x 且回撤 "
            f"{dd:.0%} >= {config.BLOWUP_DRAWDOWN_PCT:.0%}"]
    if (dd is not None and dd >= config.BLOWUP_DRAWDOWN_PCT
            and cur_dd is not None and cur_dd >= config.BLOWUP_DRAWDOWN_PCT):
        return "blowup_risk", [
            f"峰值回撤 {dd:.0%} >= {config.BLOWUP_DRAWDOWN_PCT:.0%} 且現值較峰值回落 "
            f"{cur_dd:.0%} >= {config.BLOWUP_DRAWDOWN_PCT:.0%}（近全損、未復原）"]

    # wash_suspect / mm_like（BUG 2）：做市商/高量低效戶——巨量且 量/PnL 比高，即使 PnL 為正
    # 也非方向性 alpha，須在 consistent 檢查之前攔下（否則被丟進 choppy 或誤混進 winner）。
    vlm = m.get("vlm")
    vpr = m.get("vlm_to_pnl_ratio")
    if (vlm is not None and vlm >= config.MM_MIN_VLM
            and vpr is not None and vpr >= config.MM_MIN_VLM_TO_PNL):
        return "wash_suspect", [
            f"量 ${vlm:,.0f} >= ${config.MM_MIN_VLM:,.0f} 且 量/PnL 比 {vpr:,.0f} >= "
            f"{config.MM_MIN_VLM_TO_PNL:,.0f}（做市商/高量低效，非方向性贏家，不可跟）"]
    # 既有 wash（純刷量／對敲：巨量但 PnL≈0）
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
    if span is not None and span < config.ONE_HIT_MIN_SPAN_DAYS:
        return "one_hit", [f"活躍跨度 {span:.0f} 天 < {config.ONE_HIT_MIN_SPAN_DAYS}"]
    total, best = m.get("total_pnl"), m.get("best_month_pnl")
    if (total is not None and total > 0 and best is not None
            and best > config.ONE_HIT_BEST_MONTH_SHARE * total):
        return "one_hit", [
            f"最佳月 {best:,.0f} > {config.ONE_HIT_BEST_MONTH_SHARE:.0%} × 總 PnL {total:,.0f}"]

    # consistent_winner 核心條件（非 wash/blowup、槓桿合理、風險調整後仍穩定獲利）。
    # BUG 3：portfolio 曲線指標（跨度/總PnL/回撤/正月比）為主；profit_factor 僅在 fills 未截斷時
    # 作硬條件——fills 截斷（n>=MAX_USER_FILLS）時 pf 只反映近端偏誤樣本，降級為低信心參考，不硬否決。
    pf = m.get("profit_factor")
    ratio = m.get("positive_month_ratio")
    fills_truncated = m.get("n_fills_truncated")
    core_checks = {
        f"活動跨度 {span} 天 >= {config.CONSISTENT_MIN_SPAN_DAYS}":
            span is not None and span >= config.CONSISTENT_MIN_SPAN_DAYS,
        f"總 PnL {total} > {config.CONSISTENT_MIN_TOTAL_PNL:,.0f}":
            total is not None and total > config.CONSISTENT_MIN_TOTAL_PNL,
        f"回撤 {dd} < {config.CONSISTENT_MAX_DRAWDOWN_PCT:.0%} peak":
            dd is not None and dd < config.CONSISTENT_MAX_DRAWDOWN_PCT,
        f"目前槓桿 {lev} <= {config.CONSISTENT_MAX_LEVERAGE:.0f}x":
            lev is None or lev <= config.CONSISTENT_MAX_LEVERAGE,
        f"正月比率 {ratio} >= {config.CONSISTENT_MIN_POSITIVE_MONTH_RATIO}":
            ratio is not None and ratio >= config.CONSISTENT_MIN_POSITIVE_MONTH_RATIO,
    }
    if not fills_truncated:
        core_checks[f"profit factor {pf} >= {config.CONSISTENT_MIN_PROFIT_FACTOR}"] = (
            pf is not None and pf >= config.CONSISTENT_MIN_PROFIT_FACTOR)
    if all(core_checks.values()):
        reasons = [k for k in core_checks]
        if fills_truncated:
            reasons.append(
                f"（fills 截斷 n>={config.MAX_USER_FILLS}，profit factor {pf} 樣本偏誤大，"
                f"僅供低信心參考，不硬否決）")
        return "consistent_winner", reasons
    return "choppy", [k for k, ok in core_checks.items() if not ok] or ["不符合任何特定型態"]


CLASS_ORDER = ["consistent_winner", "blowup_risk", "wash_suspect", "one_hit",
               "dormant", "choppy", "insufficient_data"]


def followability(m):
    """consistent_winner 之上的「可跟性」判定（真錢跟單的機械可行性）。回 (ok, reasons)。

    三條件（門檻在 config SCAN_FOLLOWABLE_*）：
    - 頻率：近 30 天成交 <= MAX_FREQ（頻率太高，跟單延遲下根本跟不上）
    - 持倉：平均持倉 >= MIN_HOLD_H（太短來不及進場就已平倉）
    - 槓桿：目前任一部位 <= MAX_LEVERAGE（跟高槓桿等於跟著賭爆倉）
    avg_hold_hours 估不出（無 Open/Close 可配對）→ 保守判不可跟（無法驗證 ≠ 通過）。
    """
    reasons = []
    freq = m.get("n_fills_last_30d")
    if freq is None:
        reasons.append("近 30 天成交筆數缺失，頻率無法驗證")
    elif freq > config.SCAN_FOLLOWABLE_MAX_FREQ:
        reasons.append(f"頻率過高：近 30 天 {freq} 筆 > {config.SCAN_FOLLOWABLE_MAX_FREQ}")
    hold = m.get("avg_hold_hours")
    if hold is None:
        reasons.append("平均持倉時間估不出（無 Open/Close 成交可配對），保守判不可跟")
    elif hold < config.SCAN_FOLLOWABLE_MIN_HOLD_H:
        reasons.append(f"持倉過短：平均 {hold:.1f}h < {config.SCAN_FOLLOWABLE_MIN_HOLD_H:.0f}h")
    lev = m.get("current_max_leverage")
    if lev is not None and lev > config.SCAN_FOLLOWABLE_MAX_LEVERAGE:
        reasons.append(f"槓桿過高：目前 {lev:.0f}x > {config.SCAN_FOLLOWABLE_MAX_LEVERAGE:.0f}x")
    return (not reasons), reasons


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


def build_markdown(date, results, meta, ground_truth, verdict, label=None):
    counts = defaultdict(int)
    for r in results:
        counts[r["classification"]] += 1
    total_wallets = len(results)
    scan_mode = label == "scan"

    if scan_mode:
        header = [
            f"# Hyperliquid 廣域可跟錢包掃描 — {date}",
            "",
            "> 純唯讀掃描報告。宇宙來自**全量排行榜以「可跟畫像」過濾出的候選**（中段與榜外，",
            "> 非僅榜頂），倖存者偏差較 top-N 輕，但過濾以歷史窗績效為準，**仍有回望偏差**；",
            "> 存在性 ≠ 未來獲利、≠ 跟得到。followable 為機械可行性判定，非投資建議。",
            "",
        ]
    else:
        header = [
            f"# Hyperliquid 永續聰明錢存在性檢驗 — {date}",
            "",
            "> 純唯讀分析報告。宇宙取自今日 leaderboard（＋seeds），**有倖存者偏差＋刷量污染**；",
            "> 本檢驗證明的是「存在性」，非「跟得到」。前瞻持續性需觀察器累積數據驗證。",
            "",
        ]
    lines = header + [
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
        follow_col = " 可跟 |" if scan_mode else ""
        follow_sep = "---|" if scan_mode else ""
        lines += [f"| 地址 | 總 PnL | 峰值回撤 | profit factor | 目前槓桿 | 主力幣 | 活躍天 |{follow_col}",
                  f"|---|---:|---:|---:|---:|---|---:|{follow_sep}"]
        for r in sorted(winners, key=lambda x: -(x["metrics"]["total_pnl"] or 0)):
            m = r["metrics"]
            # 風險揭露：consistent_winner 若曾被強平，明細標「曾強平 N 次」，不隱藏風險。
            liq_note = (f"（⚠️ 曾強平 {m.get('n_liquidations')} 次）"
                        if m.get("n_liquidations") else "")
            follow_cell = ""
            if scan_mode:
                fol = r.get("followable") or {}
                if fol.get("ok"):
                    follow_cell = " ✅ |"
                else:
                    why = "；".join(fol.get("reasons") or ["未判定"]).replace("|", "\\|")
                    follow_cell = f" ❌ {why} |"
            lines.append(
                f"| `{m['address']}`{liq_note} | ${_fmt(m['total_pnl'])} "
                f"| {_fmt(m['max_drawdown_pct'], '.0%')} "
                f"| {_fmt(m['profit_factor'], ',.2f')} "
                f"| {_fmt(m['current_max_leverage'], ',.0f')}x "
                f"| {m['top_coin'] or '—'} | {_fmt(m['span_days'], ',.0f')} |{follow_cell}")
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

    n_followable = sum(1 for r in winners if (r.get("followable") or {}).get("ok"))
    bias_bullet = (
        "- **回望偏差**：宇宙來自全量排行榜以歷史窗績效過濾（非僅榜頂，倖存者偏差較輕），"
        "但「過去可跟畫像」仍是回望篩選；存在性 ≠ 未來獲利。"
        if scan_mode else
        "- **倖存者偏差**：宇宙取自今日 leaderboard（＋seeds），只看得到現在還在榜上的贏家。")
    verdict_head = [f"consistent_winner 數量：**{counts.get('consistent_winner', 0)}**"]
    if scan_mode:
        verdict_head.append(f"其中 followable（可跟）數量：**{n_followable}**")
    lines += ["", "## 5. 裁決", "",
              *verdict_head, "",
              f"**{verdict}**", "",
              "限制與醒目聲明：",
              bias_bullet,
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


def decide_scan_verdict(n_winners, n_followable):
    """掃描模式兩級裁決：consistent_winner N 個，其中 followable M 個。"""
    base = f"consistent_winner {n_winners} 個，其中 followable {n_followable} 個"
    if n_followable >= config.VERDICT_STRONG_MIN_WINNERS:
        return base + "（可跟的方向性贏家在中段/榜外存在；前瞻持續性仍需逐日觀察驗證）"
    if n_followable >= 1:
        return base + "（僅少數可跟候選，證據不足，需持續觀察）"
    if n_winners >= 1:
        return base + "（有贏家但無一通過可跟性判定——頻率/持倉/槓桿不符跟單條件）"
    return base + "（本次掃描未發現可跟的方向性贏家）"


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


def run_verification(snapshot_dir, report_dir, label=None):
    """核心進入點（tests 直接呼叫）。回傳完整結果 dict 並寫出 md/json。

    label="scan"：掃描報告模式——檔名 scan_verification_{date}.md/json（date 取目錄名裡的
    YYYY-MM-DD，容納 {date}-scan 目錄），winner 加 followable 判定、裁決改兩級。
    """
    snapshot_dir = Path(snapshot_dir)
    report_dir = Path(report_dir)
    dir_name = snapshot_dir.name
    m_date = re.match(r"\d{4}-\d{2}-\d{2}", dir_name)
    date = m_date.group(0) if m_date else dir_name
    scan_mode = label == "scan"
    wallets, meta, load_errors = load_snapshot(snapshot_dir)

    results = []
    for w in wallets:
        try:
            m = compute_metrics(w, date)
            cls, reasons = classify(m)
        except Exception as exc:  # 單錢包炸掉不影響整體
            m = {"address": str(w.get("address", "?")).lower()}
            cls, reasons = "insufficient_data", [f"指標計算例外：{exc}"]
        rec = {"metrics": m, "classification": cls, "reasons": reasons}
        if cls == "consistent_winner":
            f_ok, f_reasons = followability(m)
            rec["followable"] = {"ok": f_ok, "reasons": f_reasons}
        results.append(rec)

    counts = defaultdict(int)
    for r in results:
        counts[r["classification"]] += 1
    n_winners = counts.get("consistent_winner", 0)
    n_followable = sum(1 for r in results if (r.get("followable") or {}).get("ok"))
    ground_truth = check_ground_truth(results)
    verdict = (decide_scan_verdict(n_winners, n_followable) if scan_mode
               else decide_verdict(n_winners))

    payload = {
        "date": date,
        "label": label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_dir": str(snapshot_dir),
        "verdict": verdict,
        "classification_counts": dict(counts),
        "followable_count": n_followable,
        "wallets": {r["metrics"].get("address", f"unknown_{i}"): r
                    for i, r in enumerate(results)},
        "ground_truth": ground_truth,
        "endpoint_health_summary": summarize_endpoint_health(meta),
        "snapshot_load_errors": load_errors,
    }

    report_dir.mkdir(parents=True, exist_ok=True)
    prefix = "scan_verification" if scan_mode else "verification"
    md_path = report_dir / f"{prefix}_{date}.md"
    json_path = report_dir / f"{prefix}_{date}.json"
    md_path.write_text(build_markdown(date, results, meta, ground_truth, verdict,
                                      label=label),
                       encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"[classify] wallets={len(results)} winners={n_winners}"
          + (f" followable={n_followable}" if scan_mode else ""))
    print(f"[classify] report: {md_path}")
    print(f"[classify] json:   {json_path}")
    print(f"[classify] verdict: {verdict}")
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description="Hyperliquid perp smart-money existence check")
    parser.add_argument("--snapshot", required=True,
                        help="snapshot 目錄，例：data/snapshots/2026-07-10")
    parser.add_argument("--report-dir", default=str(BASE_DIR / "data" / "reports"))
    parser.add_argument("--label", default=None, choices=["scan"],
                        help="scan：掃描報告模式（scan_verification_{date}、可跟欄、兩級裁決）")
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
    run_verification(snapshot_dir, report_dir, label=args.label)
    return 0


if __name__ == "__main__":
    sys.exit(main())
