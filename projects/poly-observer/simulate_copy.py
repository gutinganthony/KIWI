#!/usr/bin/env python3
"""poly-observer simulate_copy：跟單成本模擬器（唯讀紙上計算）。

用法（在 projects/poly-observer 下）：
    python3 simulate_copy.py --address 0x.. [--snapshot data/snapshots/YYYY-MM-DD] [--bankroll 10000]

目的：用一個錢包的**實際成交紀錄**，估算「一個跟單者照抄它會淨得多少」，把
延遲/滑點/本金限制三種摩擦成本量化，作為投入真錢前的證據層。

⚠️ 這是純紙上模擬：
- 延遲與滑點皆為**假設參數、非實測**（見 config.SIM_*）。
- 錢包 activity 被截斷在 1500 筆，只覆蓋最近一段窗口，**非全期**。
- 不構成投資建議。本工具**不執行任何交易**，只做算術。

⚠️ 誠實性閘門（simulate() 的 reliable 旗標）：
- Polymarket 輸的部位不產生 REDEEM（只有贏了領獎才有），且短窗只涵蓋數小時，
  用 activity 重建的已實現 PnL 會系統性高估（贏家倖存者偏誤＋結算/買入錯配的幽靈利潤）。
- 偵測到不可靠時（視窗過短且截斷、幽靈市場主導、對照示警、結算全為贏家），
  報告會**明白拒答**、隱藏捕獲率、不印任何「淨正/可獲利」結論。錢包基準只累計完整
  round-trip 市場（排除只結算-無買入的幽靈進帳），已實現 PnL 標註為「上界」。

解析邏輯重用 verify_smart_money 的 parse_activity_events / parse_pnl_curve（import，非複製）。
不含任何下單、私鑰、簽章、錢包連線程式碼。
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import config
import verify_smart_money as vsm

BASE_DIR = Path(__file__).resolve().parent
ADDR_LEN = 42


def _clamp_price(p):
    return min(max(p, 0.01), 0.99)


def _group_key(event):
    """逐市場分組鍵：優先 condition_id（穩定），退回 slug。"""
    return event.get("condition_id") or event.get("slug") or ""


# ---------------------------------------------------------------------------
# 錢包實際成交重建（同窗原始已實現 PnL）
# ---------------------------------------------------------------------------

def reconstruct_markets(events):
    """把事件依市場分組，分類 BUY/SELL/REDEEM。

    回傳 dict: market_key -> {"title","slug","buys":[...],"sells":[...],"redeems":[...]}。
    每個 buy/sell 帶 price/shares/usdc/ts；redeem 帶 shares/usdc/ts（結算金額）。
    """
    markets = {}
    for e in events:
        key = _group_key(e)
        if not key:
            continue
        mk = markets.setdefault(key, {
            "title": e["title"], "slug": e["slug"],
            "buys": [], "sells": [], "redeems": [],
        })
        if not mk["title"] and e["title"]:
            mk["title"] = e["title"]
        typ = e["type"]
        if e["side"] == "BUY":
            mk["buys"].append(e)
        elif e["side"] == "SELL":
            mk["sells"].append(e)
        elif "REDEEM" in typ or "REWARD" in typ or "CLAIM" in typ or "CONVERT" in typ:
            mk["redeems"].append(e)
        # 其他型別（未知）忽略
    return markets


def _shares_of(ev, fallback_price=None):
    """事件的 shares：優先 shares，退回 usdc/price。"""
    if ev.get("shares") is not None:
        return ev["shares"]
    p = ev.get("price") or fallback_price
    if p:
        return ev["usdc"] / p
    return 0.0


def market_wallet_pnl(mk):
    """錢包在該市場的原始已實現現金流 PnL：SELL＋REDEEM 回收 − BUY 成本。

    回傳 (cost, recovered, pnl, bought_shares, is_closed)；只有有 SELL 或 REDEEM 才算 closed。
    """
    cost = sum(b["usdc"] for b in mk["buys"])
    bought_shares = sum(_shares_of(b) for b in mk["buys"])
    recovered = sum(s["usdc"] for s in mk["sells"]) + sum(r["usdc"] for r in mk["redeems"])
    is_closed = bool(mk["sells"] or mk["redeems"])
    return cost, recovered, recovered - cost, bought_shares, is_closed


def market_exit_value_per_share(mk, friction):
    """該市場「每 token-share」的出場價值（含摩擦）。

    - SELL：一股換得 sell_price 美元；跟單者受摩擦 → price×(1−friction)（夾 [0.01,0.99]）。
    - REDEEM：一股結算 = 該筆 payout，屬鏈上結算、**不受滑點/延遲影響**。
    回傳 (exit_per_share_follower, exit_per_share_wallet, total_exit_shares)；無出場回 None。
    """
    fric_recovered, raw_recovered, exit_shares = 0.0, 0.0, 0.0
    for s in mk["sells"]:
        price = s["price"] if s["price"] is not None else (
            s["usdc"] / s["shares"] if s.get("shares") else 0.0)
        shares = _shares_of(s, fallback_price=price)
        fric_recovered += shares * _clamp_price(price * (1 - friction))
        raw_recovered += shares * price
        exit_shares += shares
    for r in mk["redeems"]:
        payout = r["usdc"]
        shares = _shares_of(r, fallback_price=1.0)  # 結算假設 $1/股
        fric_recovered += payout
        raw_recovered += payout
        exit_shares += shares
    if exit_shares <= 0:
        return None
    return fric_recovered / exit_shares, raw_recovered / exit_shares, exit_shares


# ---------------------------------------------------------------------------
# 跟單者模擬
# ---------------------------------------------------------------------------

def _plan_buys(events, markets, mode, bankroll):
    """依全域時間序處理所有 BUY，決定每筆跟單者投入額（本金限制）。

    投入額只跟 mode/bankroll 有關、與滑點情境無關，故只算一次。
    回傳 (plan, copied_buys, missed_buys)；plan: market_key -> [(invest, wallet_price)]。
    """
    plan = {}
    remaining = bankroll
    copied_buys = missed_buys = 0
    buy_events = [e for e in events if e["side"] == "BUY" and _group_key(e)]
    buy_events.sort(key=lambda e: (e["ts"] is None, e["ts"] or 0))
    for e in buy_events:
        if mode == "fixed":
            invest = min(config.SIM_FIXED_USD, remaining)
        else:  # proportional
            invest = min(bankroll * config.SIM_PROP_FRACTION, remaining)
        if invest <= 0.005:  # 本金用完 → 漏跟
            missed_buys += 1
            continue
        price = e["price"] if e["price"] is not None else (
            e["usdc"] / e["shares"] if e.get("shares") else None)
        if price is None or price <= 0:
            missed_buys += 1
            continue
        plan.setdefault(_group_key(e), []).append((invest, price))
        remaining -= invest
        copied_buys += 1
    return plan, copied_buys, missed_buys


def _follower_pnl(invest, wallet_price, friction, exit_per_share):
    """單筆跟單買入的 PnL：以較差進場價買、以（含摩擦）出場價值結算。"""
    entry = _clamp_price(wallet_price * (1 + friction))
    shares = invest / entry
    recovered = shares * exit_per_share
    return recovered - invest


def simulate_scenario(events, markets, mode, scenario, bankroll):
    """單一（情境 × 模式）格：回傳一格的跟單者結果 dict。"""
    friction = config.SIM_SLIPPAGE_SCENARIOS[scenario] + config.SIM_LATENCY_EXTRA_SLIPPAGE
    plan, copied_buys, missed_buys = _plan_buys(events, markets, mode, bankroll)

    net_pnl = 0.0
    net_pnl_zero_fric = 0.0
    invested = 0.0
    wins = markets_copied = 0
    for key, buys in plan.items():
        mk = markets[key]
        exit_f = market_exit_value_per_share(mk, friction)
        exit_0 = market_exit_value_per_share(mk, 0.0)
        if exit_f is None:  # 開倉未結算 → 不計入已實現
            continue
        eps_follower = exit_f[0]
        eps_wallet = exit_0[1]
        market_pnl = 0.0
        market_pnl_zero = 0.0
        market_cost = 0.0
        for invest, wprice in buys:
            market_cost += invest
            market_pnl += _follower_pnl(invest, wprice, friction, eps_follower)
            market_pnl_zero += _follower_pnl(invest, wprice, 0.0, eps_wallet)
        net_pnl += market_pnl
        net_pnl_zero_fric += market_pnl_zero
        invested += market_cost
        markets_copied += 1
        if market_pnl > 0:
            wins += 1

    roi = (net_pnl / invested) if invested > 0 else None
    friction_total = net_pnl_zero_fric - net_pnl
    avg_friction = (friction_total / copied_buys) if copied_buys else None
    win_rate = (wins / markets_copied) if markets_copied else None
    return {
        "scenario": scenario,
        "mode": mode,
        "friction_per_side": round(friction, 4),
        "follower_net_pnl": round(net_pnl, 2),
        "follower_invested": round(invested, 2),
        "follower_roi": round(roi, 4) if roi is not None else None,
        "avg_friction_per_trade": round(avg_friction, 4) if avg_friction is not None else None,
        "missed_buys": missed_buys,
        "copied_buys": copied_buys,
        "n_markets_copied": markets_copied,
        "win_rate": round(win_rate, 3) if win_rate is not None else None,
    }


# ---------------------------------------------------------------------------
# 錢包同窗基準與 sanity check
# ---------------------------------------------------------------------------

def curve_window_delta(points, first_ts, last_ts):
    """pnl 曲線在 [first_ts, last_ts] 窗內的淨變動（同窗對照 sanity check）。"""
    if not points or first_ts is None or last_ts is None:
        return None
    baseline = points[0][1]
    for ts, val in points:
        if ts <= first_ts:
            baseline = val
        else:
            break
    endval = points[0][1]
    for ts, val in points:
        if ts <= last_ts:
            endval = val
    return endval - baseline


def simulate(wallet, snapshot_date, bankroll=None):
    """核心進入點（tests 直接呼叫）。回傳完整模擬結果 dict。"""
    if bankroll is None:
        bankroll = config.SIM_BANKROLL
    addr = str(wallet.get("address", "")).lower()
    events = vsm.parse_activity_events(wallet.get("activity"))
    markets = reconstruct_markets(events)

    ts_list = [e["ts"] for e in events if e["ts"] is not None]
    first_ts = min(ts_list) if ts_list else None
    last_ts = max(ts_list) if ts_list else None
    n_trades = sum(1 for e in events if e["side"] in ("BUY", "SELL"))
    n_redeems = sum(1 for e in events
                    if e["side"] not in ("BUY", "SELL")
                    and ("REDEEM" in e["type"] or "REWARD" in e["type"]
                         or "CLAIM" in e["type"] or "CONVERT" in e["type"]))

    # 視窗長度與頻率（防除零）
    if first_ts is not None and last_ts is not None and last_ts > first_ts:
        window_hours = (last_ts - first_ts) / 3600.0
    else:
        window_hours = 0.0
    trades_per_hour = n_trades / max(window_hours, 1e-9)

    # 市場三分類 + 錢包基準（★只用 round-trip 市場，排除幽靈利潤）
    # roundtrip：有 buys 且有出場（sells 或 redeems）——唯一可信的已實現往返
    # settle_only：有出場但無 buys——結算的是視窗前建的倉，payout 被誤當 cost=0 的純利潤（幽靈）
    # open_only：有 buys 無出場——尚未結算
    wallet_cost = wallet_recovered = 0.0
    excluded_settle_only_proceeds = 0.0
    n_roundtrip = n_settle_only = n_open_only = 0
    losing_redeem_count = 0
    for mk in markets.values():
        cost, recovered, _pnl, _, _ = market_wallet_pnl(mk)
        has_buys = bool(mk["buys"])
        has_exit = bool(mk["sells"] or mk["redeems"])
        for r in mk["redeems"]:
            if r["usdc"] < 1.0:   # ~$0 payout = 輸掉的結算（真實鏈上罕見：輸家多半不領獎）
                losing_redeem_count += 1
        if has_buys and has_exit:
            n_roundtrip += 1
            wallet_cost += cost
            wallet_recovered += recovered
        elif has_exit and not has_buys:
            n_settle_only += 1
            excluded_settle_only_proceeds += recovered
        elif has_buys and not has_exit:
            n_open_only += 1
    # realized 為「上界」：只看得到贏的往返，輸家未計入（見 unreliable_reasons(d)）
    wallet_realized = wallet_recovered - wallet_cost
    wallet_roi = (wallet_realized / wallet_cost) if wallet_cost > 0 else None

    # sanity check：重建 PnL vs 曲線同窗變動
    points = vsm.parse_pnl_curve(wallet.get("pnl"))
    curve_delta = curve_window_delta(points, first_ts, last_ts)
    divergence = None
    if curve_delta is not None:
        gap = abs(wallet_realized - curve_delta)
        if gap > max(0.5 * abs(curve_delta), 500.0):
            divergence = (f"重建已實現 PnL ${wallet_realized:,.0f} 與曲線同窗變動 "
                          f"${curve_delta:,.0f} 落差 ${gap:,.0f}，超出容忍；"
                          f"可能因開倉未結算部位、部分平倉或 REDEEM 未涵蓋，解讀從嚴。")

    # ---- 可靠性閘門（在算 matrix 前）----
    truncated = bool(wallet.get("activity_truncated"))
    reasons = []
    if truncated and window_hours < config.SIM_MIN_WINDOW_HOURS:
        reasons.append(
            f"activity 截斷且視窗僅 {window_hours:.0f} 小時 < {config.SIM_MIN_WINDOW_HOURS} 小時")
    if n_settle_only > config.SIM_SETTLE_ONLY_RATIO * n_roundtrip:
        reasons.append(
            f"結算-only 市場 {n_settle_only} 遠多於完整 round-trip {n_roundtrip}，幽靈利潤主導")
    if divergence:
        reasons.append("重建 PnL 與 pnl 曲線同窗變動落差超容忍")
    if n_redeems >= 10 and losing_redeem_count == 0:
        reasons.append(
            "結算事件全為贏家（輸家不產生 REDEEM），重建已實現 PnL 為上界、不可信")
    reliable = (len(reasons) == 0)

    matrix = {}
    for scenario in config.SIM_SLIPPAGE_SCENARIOS:
        matrix[scenario] = {}
        for mode in config.SIM_COPY_MODES:
            cell = simulate_scenario(events, markets, mode, scenario, bankroll)
            # 捕獲率：以「每投入 $1 的報酬率（ROI）」為可比基準，非絕對額（本金規模差幾百倍）
            if wallet_roi is not None and abs(wallet_roi) > 1e-9 and cell["follower_roi"] is not None:
                cap = round(cell["follower_roi"] / wallet_roi, 3)
            else:
                cap = None
            cell["capture_rate"] = cap
            # 防呆：不可靠、或捕獲率 > 1.0（跟單者贏過被跟者，物理上不可能）→ 標記為偏誤，報告不印數字
            cell["capture_biased"] = (not reliable) or (cap is not None and cap > 1.0)
            matrix[scenario][mode] = cell

    return {
        "address": addr,
        "snapshot_date": snapshot_date,
        "bankroll": bankroll,
        "reliable": reliable,
        "unreliable_reasons": reasons,
        "coverage": {
            "first_date": (datetime.fromtimestamp(first_ts, tz=timezone.utc).strftime("%Y-%m-%d")
                           if first_ts else None),
            "last_date": (datetime.fromtimestamp(last_ts, tz=timezone.utc).strftime("%Y-%m-%d")
                          if last_ts else None),
            "n_events": len(events),
            "n_trades": n_trades,
            "n_redeems": n_redeems,
            "window_hours": round(window_hours, 2),
            "trades_per_hour": round(trades_per_hour, 3),
            "n_markets_roundtrip": n_roundtrip,
            "n_markets_settle_only": n_settle_only,
            "n_markets_open_only": n_open_only,
            "losing_redeem_count": losing_redeem_count,
            "activity_truncated": truncated,
        },
        "wallet_window": {
            "cost": round(wallet_cost, 2),
            "recovered": round(wallet_recovered, 2),
            "realized_pnl": round(wallet_realized, 2),
            "realized_is_upper_bound": True,
            "roi": round(wallet_roi, 4) if wallet_roi is not None else None,
            "curve_delta": round(curve_delta, 2) if curve_delta is not None else None,
            "curve_divergence_warning": divergence,
            "excluded_settle_only_proceeds": round(excluded_settle_only_proceeds, 2),
        },
        "matrix": matrix,
    }


# ---------------------------------------------------------------------------
# 報告產生
# ---------------------------------------------------------------------------

def _fmt(val, spec=",.2f"):
    if val is None:
        return "—"
    try:
        return format(val, spec)
    except (TypeError, ValueError):
        return str(val)


def _capture_cell(c):
    """捕獲率的誠實顯示：偏誤時不印數字，改標「—（資料偏誤）」。"""
    if c.get("capture_biased"):
        return "—（資料偏誤）"
    return _fmt(c["capture_rate"], ".0%")


def build_markdown(result):
    cov = result["coverage"]
    ww = result["wallet_window"]
    reliable = result.get("reliable", True)
    tph = cov.get("trades_per_hour") or 0.0
    lines = [
        f"# 跟單成本模擬 — {result['address']}",
        "",
        "> **⚠️ 紙上模擬聲明**",
        "> - 這是紙上計算：延遲與滑點皆為**假設參數、非實測**（見 config.SIM_*）。",
        f"> - 錢包 activity 上限 1500 筆，本模擬僅覆蓋 **{cov['first_date']} ～ {cov['last_date']}** "
        f"（{cov['n_events']} 筆事件、{cov['n_trades']} 筆交易、{cov['n_redeems']} 筆結算），"
        f"{'⚠️ 已截斷，' if cov['activity_truncated'] else ''}**僅代表最近一段窗口、非全期**。",
        "> - 不構成投資建議。本工具**不執行任何交易**，只做算術。",
        "",
    ]

    # 不可靠時：報告最上方插入醒目拒答區塊
    if not reliable:
        lines += ["## ⚠️ 本窗無法可靠模擬跟單損益", ""]
        for r in result.get("unreliable_reasons", []):
            lines.append(f"- {r}")
        lines += ["",
                  "> 以下矩陣僅供診斷、數字不可作為獲利依據。",
                  ""]

    lines += [
        "## 1. 錢包同窗基準（已實現，上界）",
        "",
        f"- 完整 round-trip 市場：{cov['n_markets_roundtrip']}（"
        f"另有 {cov['n_markets_settle_only']} 個只結算-無買入的幽靈市場已排除、"
        f"{cov['n_markets_open_only']} 個開倉未結算）",
        f"- 投入成本（僅 round-trip）：${_fmt(ww['cost'])}",
        f"- 回收（賣出＋結算）：${_fmt(ww['recovered'])}",
        f"- **同窗已實現 PnL（上界，輸家未計入）：${_fmt(ww['realized_pnl'])}**"
        f"（ROI {_fmt(ww['roi'], '.1%')}）",
        f"- 已排除的 settle-only 幽靈進帳（不計入基準）：${_fmt(ww['excluded_settle_only_proceeds'])}",
        f"- pnl 曲線同窗變動（對照）：${_fmt(ww['curve_delta'])}",
    ]
    if ww["curve_divergence_warning"]:
        lines.append(f"- ⚠️ **對照示警**：{ww['curve_divergence_warning']}")
    else:
        lines.append("- ✅ 重建與曲線同窗變動一致（在容忍範圍內）")

    lines += ["", "## 2. 情境 × 模式 矩陣", "",
              "每格：跟單者 ROI（每投入 $1 報酬率） / 捕獲率（跟單 ROI ÷ 錢包同窗 ROI） / "
              f"淨 PnL（on ${_fmt(result['bankroll'], ',.0f')} 本金）",
              "",
              "| 情境（單邊摩擦） | fixed | proportional |",
              "|---|---|---|"]
    fric = {s: config.SIM_SLIPPAGE_SCENARIOS[s] + config.SIM_LATENCY_EXTRA_SLIPPAGE
            for s in config.SIM_SLIPPAGE_SCENARIOS}
    for scenario in config.SIM_SLIPPAGE_SCENARIOS:
        cells = []
        for mode in config.SIM_COPY_MODES:
            c = result["matrix"][scenario][mode]
            cells.append(f"ROI {_fmt(c['follower_roi'], '.1%')} / "
                         f"捕獲 {_capture_cell(c)} / "
                         f"${_fmt(c['follower_net_pnl'], ',.0f')}")
        lines.append(f"| {scenario}（±{fric[scenario]:.0%}） | {cells[0]} | {cells[1]} |")

    lines += ["", "細項（漏跟/勝率/平均摩擦）：", "",
              "| 情境 | 模式 | 跟到筆數 | 漏跟筆數 | 勝率 | 每單平均摩擦 $ |",
              "|---|---|---:|---:|---:|---:|"]
    for scenario in config.SIM_SLIPPAGE_SCENARIOS:
        for mode in config.SIM_COPY_MODES:
            c = result["matrix"][scenario][mode]
            lines.append(
                f"| {scenario} | {mode} | {c['copied_buys']} | {c['missed_buys']} "
                f"| {_fmt(c['win_rate'], '.0%')} | ${_fmt(c['avg_friction_per_trade'])} |")

    # 白話結論
    lines += ["", "## 3. 白話結論", ""]
    if not reliable:
        # 不可靠：絕不出現「淨正 ✅」或「可跟/獲利」字樣，改給結構性結論
        sec_per_order = (3600.0 / tph) if tph > 0 else None
        lines.append(
            f"- 本窗**無法可靠評估跟單損益**（見開頭拒答區塊），下列僅為結構性事實：")
        lines.append(
            f"- 交易頻率：約 **{tph:.1f} 筆/小時**；完整 round-trip 市場 "
            f"{cov['n_markets_roundtrip']} 個 vs 只結算-無買入的幽靈市場 "
            f"{cov['n_markets_settle_only']} 個。")
        if sec_per_order is not None:
            lines.append(
                f"- 此錢包每 **{sec_per_order:.0f} 秒**就有新單，"
                f"單一短窗的重建 PnL 只看得到贏的往返；需**多日累積快照**才能可靠評估。")
        lines.append("")
        lines.append("> 摩擦必然侵蝕 edge，且輸家部位不產生 REDEEM——本窗數字系統性高估，"
                     "**不可作為投入真錢的依據**。")
    elif ww["roi"] is None or ww["realized_pnl"] == 0:
        lines.append("錢包同窗無正的已實現基準（可能全開倉或資料不足），本窗無法給出可靠捕獲率結論。")
    else:
        opt = result["matrix"]["optimistic"]["fixed"]
        best_capture = opt.get("capture_rate")
        if best_capture is not None and not opt.get("capture_biased"):
            lines.append(
                f"- 在**最樂觀**情境（fixed）下，跟單者能保留錢包 edge 的約 "
                f"**{_fmt(best_capture, '.0%')}**（捕獲率）。")
        pess = result["matrix"]["pessimistic"]["fixed"]
        for scen_name, cell in (("最樂觀", opt), ("最悲觀", pess)):
            pnl_mark = "淨正 ✅" if (cell["follower_net_pnl"] or 0) > 0 else "淨負 ❌"
            lines.append(
                f"- {scen_name}（fixed）：淨 PnL ${_fmt(cell['follower_net_pnl'], ',.0f')} "
                f"on ${_fmt(result['bankroll'], ',.0f')} → {pnl_mark}"
                f"（漏跟 {cell['missed_buys']} 筆）")
        lines.append("")
        lines.append("> 摩擦必然侵蝕 edge：跟單者 ROI 恆低於錢包同窗 ROI；本金有限時高頻錢包會大量漏跟。"
                     "此為紙上估計，實盤延遲/滑點/流動性可能更差。")

    # 頻率 × 延遲可行性（reliable 與否都印）
    lines += ["", "## 頻率 × 延遲可行性", "",
              f"- 錢包交易頻率：約 **{tph:.1f} 筆/小時**。"]
    for name, sec in config.SIM_LATENCY_SCENARIOS_SEC.items():
        added = tph * sec / 3600.0
        lines.append(
            f"- 延遲 {sec}s（{name}）內錢包平均新增 **{added:.1f}** 筆單——"
            f"你偵測到訊號、下單成交前，這些單早已成交；你跟到的是"
            f"**還沒被搶完、價格較差**的那批（逆選擇）。")

    lines += ["", "> 純唯讀紙上模擬，不執行任何交易、不構成投資建議。", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def load_wallet_raw(snapshot_dir, tracked_dir, addr):
    """優先讀 snapshot 的 wallets/{addr}.json；缺則讀 track_wallet 持久化的 latest_raw.json。"""
    snap_path = Path(snapshot_dir) / "wallets" / f"{addr}.json"
    if snap_path.exists():
        try:
            return json.loads(snap_path.read_text(encoding="utf-8")), "snapshot"
        except Exception as exc:
            print(f"[sim] snapshot 錢包檔解析失敗（{snap_path}）：{exc}", file=sys.stderr)
    persisted = Path(tracked_dir) / "latest_raw.json"
    if persisted.exists():
        try:
            return json.loads(persisted.read_text(encoding="utf-8")), "persisted"
        except Exception as exc:
            print(f"[sim] 持久化錢包檔解析失敗（{persisted}）：{exc}", file=sys.stderr)
    return None, None


def run_simulate(address, snapshot_dir, tracked_root, bankroll=None):
    """核心進入點（含落地）。回傳 result dict；缺資料回 None。"""
    addr = str(address).strip().lower()
    date = Path(snapshot_dir).name
    tracked_dir = Path(tracked_root) / addr
    tracked_dir.mkdir(parents=True, exist_ok=True)

    wallet, source = load_wallet_raw(snapshot_dir, tracked_dir, addr)
    if wallet is None:
        print(f"[sim] {addr} 無可用原始資料（snapshot 與 latest_raw.json 皆缺），略過。")
        return None

    result = simulate(wallet, date, bankroll=bankroll)
    result["raw_source"] = source

    md_path = tracked_dir / f"copy_sim_{date}.md"
    json_path = tracked_dir / f"copy_sim_{date}.json"
    md_path.write_text(build_markdown(result), encoding="utf-8")
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    ww = result["wallet_window"]
    cov = result["coverage"]
    print(f"[sim] {addr} window={cov['first_date']}~{cov['last_date']} "
          f"({cov['window_hours']:.1f}h, {cov['trades_per_hour']:.1f} trades/h) "
          f"reliable={result['reliable']} "
          f"wallet_realized(upper-bound)=${ww['realized_pnl']:,.0f} roi={ww['roi']}")
    if not result["reliable"]:
        print(f"[sim] ⚠️ 不可靠，本窗無法可靠模擬跟單損益；原因：")
        for r in result["unreliable_reasons"]:
            print(f"[sim]     - {r}")
    print(f"[sim] report: {md_path}")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Polymarket copy-trade cost simulator (read-only paper calc)")
    parser.add_argument("--address", required=True, help="0x 錢包地址")
    parser.add_argument("--snapshot", default=None,
                        help="snapshot 目錄；預設 data/snapshots/{今日UTC}")
    parser.add_argument("--bankroll", type=float, default=config.SIM_BANKROLL)
    parser.add_argument("--tracked-dir", default=str(BASE_DIR / "data" / "tracked"))
    args = parser.parse_args(argv)

    addr = args.address.strip().lower()
    if len(addr) != ADDR_LEN or not addr.startswith("0x"):
        print(f"[sim] 地址格式可疑：{args.address}", file=sys.stderr)

    if args.snapshot:
        snapshot_dir = Path(args.snapshot)
        if not snapshot_dir.is_absolute():
            cand = BASE_DIR / snapshot_dir
            snapshot_dir = cand if cand.exists() else snapshot_dir
    else:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        snapshot_dir = BASE_DIR / "data" / "snapshots" / today

    tracked_root = Path(args.tracked_dir)
    if not tracked_root.is_absolute():
        tracked_root = BASE_DIR / tracked_root

    run_simulate(addr, snapshot_dir, tracked_root, bankroll=args.bankroll)
    return 0  # 唯讀模擬器：永遠 exit 0


if __name__ == "__main__":
    sys.exit(main())
