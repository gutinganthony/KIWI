"""funnel.py — 台股投信×營收動能三層漏斗（資格關卡 → 否決關卡 → 等權評分）。

讀 data/state/（fetch_twse.py 維護），輸出：
  data/candidates_latest.json   候選清單（schema 與美股管線完全一致，monitor 統一讀取）
  data/meta_latest.json         端點健康＋降級/TODO 誠實標註＋漏斗統計

核心函數皆為純函數（吃 state dict＋cfg dict），tests/ 離線餵 fixture 驗證。
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import config

BASE = Path(__file__).resolve().parent
STATE_DIR = BASE / "data" / "state"
DATA_DIR = BASE / "data"


# ---------------------------------------------------------------------------
# 設定與狀態載入
# ---------------------------------------------------------------------------

def default_cfg() -> dict:
    """把 config 模組常數收成 dict，測試可覆寫個別鍵。"""
    return {k: getattr(config, k) for k in dir(config) if k.isupper()}


def load_json(path: Path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def load_state() -> dict:
    trust = load_json(STATE_DIR / "trust_history.json", {"days": {}, "names": {}})
    close = load_json(STATE_DIR / "latest_close.json", {"date": None, "close": {}, "value": {}})
    return {
        "trust_days": trust.get("days", {}),
        "names": trust.get("names", {}),
        "turnover_days": load_json(STATE_DIR / "turnover_history.json", {"days": {}}).get("days", {}),
        "revenue_months": load_json(STATE_DIR / "revenue_history.json", {"months": {}}).get("months", {}),
        "close": close.get("close", {}),
        "close_date": close.get("date"),
        "shares_out": load_json(STATE_DIR / "shares_outstanding.json", {}),
        "veto_lists": load_json(STATE_DIR / "veto_lists.json",
                                {"date": None, "punish": [], "attention": [], "pledge_ratio": {}}),
        "fetch_meta": load_json(STATE_DIR / "fetch_meta.json", {"endpoint_health": {}}),
    }


# ---------------------------------------------------------------------------
# 第一層｜資格關卡
# ---------------------------------------------------------------------------

def latest_two_yoy(revenue_months: dict, ticker: str):
    """該股最近兩個月的 YoY → (本月yoy, 上月yoy)；缺一回 None。"""
    yms = sorted(ym for ym, data in revenue_months.items() if ticker in data)
    if not yms:
        return None, None
    cur = revenue_months[yms[-1]][ticker].get("yoy")
    prev = revenue_months[yms[-2]][ticker].get("yoy") if len(yms) >= 2 else None
    return cur, prev


def trust_streak(trust_days: dict, ticker: str, as_of: str) -> tuple[int, str]:
    """截至 as_of 的連續買超日數與連買段起始日（含 as_of；as_of 必為買超日才呼叫）。"""
    days = sorted(d for d in trust_days if d <= as_of)
    streak, start = 0, as_of
    for d in reversed(days):
        if trust_days[d].get(ticker, 0) > 0:
            streak += 1
            start = d
        else:
            break
    return streak, start


def is_first_buy(trust_days: dict, ticker: str, streak_start: str, lookback: int) -> bool:
    """本次連買段之前的 lookback 個交易日內，無任何投信買超日 → 首次買超。"""
    prior = sorted(d for d in trust_days if d < streak_start)[-lookback:]
    return all(trust_days[d].get(ticker, 0) <= 0 for d in prior)


def qualify(state: dict, cfg: dict, as_of: str) -> tuple[list, dict]:
    """第一層資格關卡。回傳 (qualified 清單, 統計)。

    條件（全部同時成立才入池——FinLab 組合條件的實作）：
      1. 當日投信買賣超 > 0
      2. 近 QUAL_WINDOW_DAYS 日累計買超 ≥ 股數門檻 或 金額門檻（OR）
      3. 月營收 YoY > 0
      4. YoY 加速：本月 YoY > 上月 YoY（上月 YoY 缺（史料未累積）→ 不入池並計數）
    """
    trust_days = state["trust_days"]
    close = state["close"]
    today_net = trust_days.get(as_of, {})
    window_days = sorted(d for d in trust_days if d <= as_of)[-cfg["QUAL_WINDOW_DAYS"]:]

    qualified, stats = [], {"raw_filings": 0, "chip_pass": 0, "accel_unknown": 0}
    for ticker, net in sorted(today_net.items()):
        stats["raw_filings"] += 1
        if net <= 0:
            continue
        cum = sum(trust_days[d].get(ticker, 0) for d in window_days)
        px = close.get(ticker)
        shares_ok = cum >= cfg["MIN_3D_NET_BUY_SHARES"]
        value_ok = px is not None and cum * px >= cfg["MIN_3D_NET_BUY_VALUE_TWD"]
        if not (shares_ok or value_ok):
            continue
        stats["chip_pass"] += 1
        yoy, yoy_prev = latest_two_yoy(state["revenue_months"], ticker)
        if yoy is None or yoy <= 0:
            continue
        if yoy_prev is None:
            stats["accel_unknown"] += 1  # 史料不足，無法判加速 → 誠實不入池
            continue
        if yoy <= yoy_prev:
            continue
        streak, streak_start = trust_streak(trust_days, ticker, as_of)
        qualified.append({
            "ticker": ticker,
            "net_today": int(net),
            "cum_net": int(cum),
            "cum_value_twd": cum * px if px is not None else None,
            "close": px,
            "yoy": yoy,
            "yoy_prev": yoy_prev,
            "accel": yoy - yoy_prev,
            "streak": streak,
            "streak_start": streak_start,
        })
    return qualified, stats


# ---------------------------------------------------------------------------
# 第二層｜否決關卡（一票否決）
# ---------------------------------------------------------------------------

def avg_turnover(turnover_days: dict, ticker: str, as_of: str, window: int):
    days = sorted(d for d in turnover_days if d <= as_of)[-window:]
    vals = [turnover_days[d][ticker] for d in days if ticker in turnover_days[d]]
    return (sum(vals) / len(vals)) if vals else None


def in_january_window(as_of: str, cfg: dict) -> bool:
    """1 月作帳反轉窗（config 開關）：1/1–1/15 不進新倉。"""
    if not cfg["JANUARY_NO_NEW_ENTRY"]:
        return False
    dt = datetime.strptime(as_of, "%Y-%m-%d")
    return dt.month == 1 and dt.day <= cfg["JANUARY_WINDOW_LAST_DAY"]


def apply_vetoes(qualified: list, state: dict, cfg: dict, as_of: str) -> tuple[list, dict]:
    """否決關卡。回傳 (存活清單, {否決原因: 檔數})。"""
    veto_lists = state["veto_lists"]
    punish = set(veto_lists.get("punish", []))
    attention = set(veto_lists.get("attention", []))
    pledge = veto_lists.get("pledge_ratio", {})
    jan_window = in_january_window(as_of, cfg)

    survivors, reasons = [], {}

    def veto(reason):
        reasons[reason] = reasons.get(reason, 0) + 1

    # 系統性缺失降級：成交額 state 完全為空＝數據源整體故障（非個股問題），
    # 此時流動性關不生效並記 warning，避免單一數據源故障把全部合格事件否決光。
    # 個股層級查無（其他股有數據）仍照 VETO_UNKNOWN_TURNOVER 保守否決。
    turnover_available = bool(state["turnover_days"])
    if not turnover_available:
        reasons["turnover_gate_inactive_source_down"] = 0

    for c in qualified:
        t = c["ticker"]
        if jan_window:
            veto("january_window")           # 作帳反轉窗：一律不進新倉
            continue
        if t in punish:
            veto("punish_list")
            continue
        if t in attention:
            veto("attention_list")
            continue
        if pledge.get(t, 0) > cfg["PLEDGE_VETO_RATIO"]:
            veto("pledge_ratio")
            continue
        if turnover_available:
            avg = avg_turnover(state["turnover_days"], t, as_of, cfg["TURNOVER_AVG_WINDOW"])
            if avg is None:
                if cfg["VETO_UNKNOWN_TURNOVER"]:
                    veto("turnover_unknown")
                    continue
            elif avg < cfg["MIN_AVG_DAILY_TURNOVER_TWD"]:
                veto("turnover_floor")
                continue
        survivors.append(c)
    return survivors, reasons


# ---------------------------------------------------------------------------
# 第三層｜等權評分（每項 0–2 分；DeMiguel 1/N，不做權重最適化）
# ---------------------------------------------------------------------------

def score_candidate(c: dict, state: dict, cfg: dict) -> tuple[int, dict]:
    shares_out = state["shares_out"].get(c["ticker"])
    mcap = shares_out * c["close"] if (shares_out and c["close"]) else None

    # (1) 營收 YoY 加速幅度
    accel_pts = 2 if c["accel"] >= cfg["SCORE_ACCEL_2PT"] else (
        1 if c["accel"] >= cfg["SCORE_ACCEL_1PT"] else 0)

    # (2) 投信買超強度：連續天數 +1、金額/市值比 +1（市值不可得退化用金額門檻）
    strength_pts = 1 if c["streak"] >= cfg["SCORE_CONSEC_DAYS"] else 0
    if mcap and c["cum_value_twd"] is not None:
        if c["cum_value_twd"] / mcap >= cfg["SCORE_NETBUY_MCAP_RATIO"]:
            strength_pts += 1
    elif c["cum_value_twd"] is not None and c["cum_value_twd"] >= cfg["SCORE_NETBUY_VALUE_TWD"]:
        strength_pts += 1
    strength_pts = min(strength_pts, 2)

    # (3) 小型股帶（市值不可得 → 0，誠實不給分）
    if mcap is None:
        smallcap_pts = 0
    elif mcap < cfg["SMALLCAP_2PT_MCAP_TWD"]:
        smallcap_pts = 2
    elif mcap < cfg["SMALLCAP_1PT_MCAP_TWD"]:
        smallcap_pts = 1
    else:
        smallcap_pts = 0

    # (4) 近 60 交易日首次買超
    first_pts = 2 if is_first_buy(state["trust_days"], c["ticker"],
                                  c["streak_start"], cfg["FIRST_BUY_LOOKBACK_DAYS"]) else 0

    breakdown = {
        "revenue_accel": accel_pts,
        "trust_strength": strength_pts,
        "small_cap": smallcap_pts,
        "first_time_buy": first_pts,
    }
    return sum(breakdown.values()), breakdown


# ---------------------------------------------------------------------------
# 輸出組裝（schema 契約：美股專屬欄位置 null、台股專屬放 tw_fields）
# ---------------------------------------------------------------------------

def build_output(state: dict, cfg: dict, as_of: str | None = None,
                 now_utc: str | None = None) -> tuple[dict, dict]:
    """跑完整漏斗 → (candidates_latest dict, meta_latest dict)。純函數。"""
    generated_at = now_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    trust_days = state["trust_days"]
    as_of = as_of or (max(trust_days) if trust_days else None)

    degradations, todo = [], []
    # v0 誠實標註：接不到/沒接的數據源
    todo.append("tpex_otc_not_wired: v0 只做上市（TWSE），上櫃 TPEx 未接線")
    todo.append("director_transfer_not_wired: 董監申讓申報無 OpenAPI dataset（MOPS 無官方 API），"
                "否決關卡此項未接線")
    health = state["fetch_meta"].get("endpoint_health", {})

    def unhealthy(name):
        h = health.get(name)
        return h is None or not h.get("ok")

    if unhealthy("punish_list"):
        degradations.append("punish_list_unavailable: 處置股清單取數失敗/未取，該否決不生效")
    if unhealthy("attention_list"):
        degradations.append("attention_list_unavailable: 注意股清單取數失敗/未取，該否決不生效")
    if unhealthy("pledge_t187ap11_L") or not state["veto_lists"].get("pledge_ratio"):
        degradations.append("pledge_data_unavailable: 董監質押比取數失敗/欄位不符，質押否決不生效")
    if not state["shares_out"]:
        degradations.append("shares_outstanding_unavailable: 市值不可得，小型股/買超強度市值項退化")

    if as_of is None:
        # 完全無投信資料（端點全掛的首跑）：輸出空殼＋誠實 meta，不 crash
        stats = {"raw_filings": 0, "qualified_events": 0, "post_veto": 0, "final_candidates": 0}
        candidates_doc = {
            "generated_at": generated_at,
            "scan_window_days": cfg["QUAL_WINDOW_DAYS"],
            "funnel_stats": stats,
            "candidates": [],
        }
        meta = _build_meta(generated_at, None, stats, {}, degradations
                           + ["no_trust_data: 投信買賣超狀態為空（端點失敗且無既有狀態）"],
                           todo, health, cfg, january=False)
        return candidates_doc, meta

    qualified, qstats = qualify(state, cfg, as_of)
    survivors, veto_reasons = apply_vetoes(qualified, state, cfg, as_of)
    if qstats["accel_unknown"]:
        degradations.append(
            f"revenue_prev_month_missing: {qstats['accel_unknown']} 檔通過籌碼關但無上月 YoY"
            "（月營收史料未累積滿 2 期），無法判加速，誠實不入池")

    scored = []
    for c in survivors:
        score, breakdown = score_candidate(c, state, cfg)
        scored.append((score, c, breakdown))
    # 排序：總分 desc → 3 日買超金額 desc（缺金額用股數）→ 代號 asc（穩定可重現）
    scored.sort(key=lambda x: (-x[0],
                               -(x[1]["cum_value_twd"] if x[1]["cum_value_twd"] is not None
                                 else x[1]["cum_net"]),
                               x[1]["ticker"]))
    top = scored[: cfg["TOP_N"]]

    candidates = []
    for score, c, breakdown in top:
        candidates.append({
            "ticker": c["ticker"],
            "company": state["names"].get(c["ticker"], ""),
            "cluster_size": None,      # 美股專屬（內部人集群人數）→ 台股置 null
            "insiders": None,          # 美股專屬（內部人名單）→ 台股置 null
            "total_buy_usd": None,     # 美股專屬（買入金額 USD）→ 台股置 null
            "tw_fields": {
                "trust_net_buy_shares": c["net_today"],
                "trust_consecutive_days": c["streak"],
                "revenue_yoy": c["yoy"],
                "revenue_yoy_accel": round(c["accel"], 2),
            },
            "score": score,
            "score_breakdown": breakdown,
            "first_filing_date": c["streak_start"],
            "entry_price_ref": c["close"],
        })

    stats = {
        "raw_filings": qstats["raw_filings"],
        "qualified_events": len(qualified),
        "post_veto": len(survivors),
        "final_candidates": len(candidates),
    }
    candidates_doc = {
        "generated_at": generated_at,
        "scan_window_days": cfg["QUAL_WINDOW_DAYS"],
        "funnel_stats": stats,
        "candidates": candidates,
    }
    meta = _build_meta(generated_at, as_of, stats, veto_reasons, degradations, todo,
                       health, cfg, january=in_january_window(as_of, cfg))
    return candidates_doc, meta


def _build_meta(generated_at, as_of, stats, veto_reasons, degradations, todo,
                health, cfg, january) -> dict:
    warnings = []
    if stats["post_veto"] < cfg["FUNNEL_STARVED_BELOW"]:
        warnings.append(f"funnel_starved: 否決後候選 {stats['post_veto']} < "
                        f"{cfg['FUNNEL_STARVED_BELOW']}（設計文件§3：考慮放寬資格關卡、靠評分消化）")
    if stats["post_veto"] > cfg["FUNNEL_BROKEN_ABOVE"]:
        warnings.append(f"funnel_gate_suspect: 否決後候選 {stats['post_veto']} > "
                        f"{cfg['FUNNEL_BROKEN_ABOVE']}（檢查資格關卡是否失效）")
    return {
        "generated_at": generated_at,
        "market": "TW",
        "pipeline": "tw-funnel",
        "as_of_trading_day": as_of,
        "endpoint_health": health,
        "funnel_stats": stats,
        "veto_reasons": veto_reasons,
        "january_window_active": january,
        "degradations": degradations,
        "todo_not_wired": todo,
        "warnings": warnings,
        "notes": [
            "純唯讀觀察，無下單；不構成投資建議",
            "組合條件（投信買超×營收動能）唯一公開回測為 FinLab 樣本內 +33.9%/yr、"
            "MDD -45.5%——期望值不可直接引用，Phase 2 需 walk-forward 樣本外驗證",
        ],
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def main() -> int:
    state = load_state()
    candidates_doc, meta = build_output(state, default_cfg())
    save_json(DATA_DIR / "candidates_latest.json", candidates_doc)
    save_json(DATA_DIR / "meta_latest.json", meta)
    s = candidates_doc["funnel_stats"]
    print(f"漏斗完成 as_of={meta['as_of_trading_day']}: raw={s['raw_filings']} → "
          f"qualified={s['qualified_events']} → post_veto={s['post_veto']} → "
          f"final={s['final_candidates']}")
    if meta["degradations"]:
        print(f"降級 {len(meta['degradations'])} 項（誠實標註於 meta_latest.json）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
