#!/usr/bin/env python3
"""hyper-observer track_wallet：單錢包深度追蹤器（唯讀 dossier）。

用法（在 projects/hyper-observer 下）：
    python3 track_wallet.py --address 0x.. [--snapshot data/snapshots/YYYY-MM-DD]

像追蹤一個交易員一樣持續盯一個永續錢包：讀當日 snapshot 的原始資料，
算出身分/目前持倉（方向・槓桿・強平價・未實現PnL）/portfolio 績效/近 N 筆成交，
並與上次快照比對偵測「新開倉/平倉」，逐日落地 dossier（人讀 md ＋機器 json）與 timeline.jsonl。
timeline 每列另含**多場所資金分布**（現貨 spot_value_usd、全場所總值、各 dex 淨值、非原生
占比；現貨為每日抓取），dossier §7/§8 由此呈現資金分布與「資金流向趨勢」（收手中／重新
進場／持平／資料累積中——僅描述觀察到的資金流向，不構成投資建議）。同日重跑不重複 append。

持久化：把該錢包原始 snapshot 複製到 data/tracked/{addr}/latest_raw.json，
讓 tracked 錢包的原始資料在每日 prune data/snapshots/*/wallets 後仍存在，供未來模擬器用。

全維度診斷探測（run_diagnostic，dossier 之後執行、失敗不影響 dossier）：
回答「資金到哪去了、有沒有轉出到別的地址」。起因是同一份原始資料自相矛盾——
clearinghouseState 說 0 持倉/$0 淨值，但 portfolio 說帳戶淨值數百萬、近 30 天 2000+ 筆
成交且主力幣是 `xyz:SNDK` 這種 HIP-3 builder 部署市場。根因：clearinghouseState 不帶
`dex` 參數時只看原生永續 dex。診斷依序查 perpDexs → 原生/各 builder dex clearinghouseState
→ spotClearinghouseState → userNonFundingLedgerUpdates（判斷有無外轉/搬家）→ portfolio
→ userFills，落地 diagnostic_{date}.json/.md 並給出裁決。

純唯讀分析：所有 parse/指標/分類邏輯重用 classify 的函式（import，非複製）。
不含任何下單、私鑰、簽章、錢包連線程式碼；不構成投資建議。跟單模擬器為下一個里程碑。
"""

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import config
import classify
import fetch

BASE_DIR = Path(__file__).resolve().parent
ADDR_LEN = 42
DAY_SEC = 86400


def _position_key(p):
    """持倉去重/比對用的穩定鍵：coin + 方向（oneWay 下每 coin 至多一倉）。"""
    coin = p.get("coin") or ""
    side = p.get("side") or ""
    return f"{coin}:{side}" if coin else ""


def _label_for(addr):
    for w in config.TRACKED_WALLETS:
        if str(w.get("address", "")).lower() == addr.lower():
            return w.get("label", "")
    return ""


# ---------------------------------------------------------------------------
# dossier 計算
# ---------------------------------------------------------------------------

def compute_dossier(wallet, date):
    """由單錢包原始 snapshot 算出 dossier（不含新開倉 delta，那需前次狀態）。"""
    addr = str(wallet.get("address", "")).lower()
    metrics = classify.compute_metrics(wallet, date)
    classification, reasons = classify.classify(metrics)
    # 決策頻率複核：升級後 followability（頻率以「部位事件數」判，fills 數僅參考）。
    # tracked 錢包不論分類一律出判定，讓 dossier 直接落地可跟性結論。
    follow_ok, follow_reasons = classify.followability(metrics)

    # 持倉一律取「原生＋各 builder dex」聯集（HIP-3 盲點修正）——只讀原生
    # clearinghouseState 會讓 xyz 這類 builder dex 的部位在 dossier/timeline/監控頁
    # 全部消失（實測 0x8bae35：xyz 有 3 個部位、名目 $1.0M，原生卻是 0）。
    # 舊 snapshot 無 clearinghouseStateByDex → 函式自動退回原生，數值與修正前一致。
    positions, _positions_by_dex = classify.parse_positions_by_dex(wallet)
    position_value = round(sum(p["position_value"] for p in positions
                               if p["position_value"] is not None), 2)
    unrealized_pnl = round(sum(p["unrealized_pnl"] for p in positions
                               if p["unrealized_pnl"] is not None), 2)

    fills = classify.parse_fills(wallet.get("userFills"))
    timeline = []
    for f in fills[-20:]:
        timeline.append({
            "time": (datetime.fromtimestamp(f["ts"], tz=timezone.utc).isoformat()
                     if f["ts"] is not None else None),
            "coin": f["coin"],
            "dir": f["dir"] or f["side"],
            "px": f["px"],
            "sz": f["sz"],
            "closed_pnl": (round(f["closed_pnl"], 2)
                           if f["closed_pnl"] is not None else None),
            "is_liquidation": f["is_liquidation"],
        })

    return {
        "address": addr,
        "label": _label_for(addr),
        "snapshot_date": date,
        "classification": classification,
        "classification_reasons": reasons,
        "followable": {"ok": follow_ok, "reasons": follow_reasons},
        "metrics": metrics,
        "position_value": position_value,
        "unrealized_pnl": unrealized_pnl,
        "n_open_positions": len(positions),
        "open_positions": positions,
        "recent_fills": timeline,
    }


def diff_positions(tracked_dir, positions, date):
    """與上次快照的持倉集合比對，回傳 (new, disappeared, initialized)。跑完更新 prev_positions.json。"""
    prev_path = tracked_dir / "prev_positions.json"
    cur_keys = [k for k in (_position_key(p) for p in positions) if k]
    cur_set = set(cur_keys)
    cur_titles = {_position_key(p): (p.get("coin") or "")
                  for p in positions if _position_key(p)}

    prev = None
    if prev_path.exists():
        try:
            prev = json.loads(prev_path.read_text(encoding="utf-8"))
        except Exception:
            prev = None

    initialized = prev is None
    if initialized:
        new_positions, disappeared = [], []
    else:
        prev_keys = set(prev.get("position_keys", []))
        prev_titles = prev.get("position_titles", {})
        new_positions = [{"key": k, "coin": cur_titles.get(k, "")}
                         for k in sorted(cur_set - prev_keys)]
        disappeared = [{"key": k, "coin": prev_titles.get(k, "")}
                       for k in sorted(prev_keys - cur_set)]

    prev_path.parent.mkdir(parents=True, exist_ok=True)
    prev_path.write_text(json.dumps(
        {"date": date, "position_keys": sorted(cur_set), "position_titles": cur_titles},
        ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return new_positions, disappeared, initialized


# ---------------------------------------------------------------------------
# timeline.jsonl（逐日多場所資金分布 → 資金流向趨勢）
# ---------------------------------------------------------------------------
# 為什麼要每日落地資金分布：持倉只看得到「已派出去的錢」，現金水位（現貨 USDC）才更早
# 反映交易者態度——現金越堆越高＝收手，現金被派去當抵押品＝重新進場。單日快照看不出
# 方向，必須逐日累積才有趨勢。措辭只描述觀察到的資金流向，不給投資建議。

TREND_CASHING_OUT = "收手中（現金化＋資本外移）"
TREND_REENTERING = "重新進場"
TREND_FLAT = "持平"
TREND_ACCUMULATING = "資料累積中"


def read_timeline(path):
    """timeline.jsonl → rows list（依檔內順序＝時間序）。壞行/缺檔一律略過，不 crash。"""
    rows = []
    path = Path(path)
    if not path.exists():
        return rows
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return rows
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def timeline_row(dossier, new_positions):
    """組出當日 timeline 列：既有欄位＋多場所資金分布（現貨為每日抓取）。"""
    m = dossier.get("metrics") or {}
    by_dex = m.get("account_value_by_dex") or {}
    # 精簡：只留非零 dex（每天都寫一整排 $0 的 builder dex 只是把檔案撐大）
    by_dex_nonzero = {d: v for d, v in by_dex.items() if v}
    return {
        "date": dossier.get("snapshot_date"),
        "total_pnl": m.get("total_pnl"),
        "position_value": dossier.get("position_value"),
        "unrealized_pnl": dossier.get("unrealized_pnl"),
        "n_open_positions": dossier.get("n_open_positions"),
        "new_positions_count": len(new_positions),
        "classification": dossier.get("classification"),
        # 多場所資金分布（缺現貨資料時 spot/total/share 為 None，見 classify 註解）
        "spot_value_usd": m.get("spot_value_usd"),
        "total_value_all_venues": m.get("total_value_all_venues"),
        "account_value_by_dex": by_dex_nonzero,
        "non_native_share": m.get("non_native_share"),
    }


def append_timeline(path, row):
    """寫入當日列並回傳全部 rows。**同日重跑不重複 append**：同 date 的既有列就地覆寫
    （重跑代表當日資料有更新，保留最新一份即可；一日一列讓趨勢比較不被重複列扭曲）。
    """
    path = Path(path)
    rows = read_timeline(path)
    date = row.get("date")
    idx = next((i for i, r in enumerate(rows) if r.get("date") == date), None)
    if idx is not None:
        # 就地覆寫（含清掉本次改動之前可能已重複 append 的同日舊列），保持時間序
        rows = [r for r in rows if r.get("date") != date]
        rows.insert(idx, row)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                        encoding="utf-8")
        return rows
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    rows.append(row)
    return rows


def funds_trend(rows, days=None, threshold=None):
    """比較 timeline 最近 N 個資料點的現貨占比與總值 → 資金流向觀察（純敘述）。

    只採用同時有 spot_value_usd 與 total_value_all_venues 的列（缺現貨的舊列不參與）。
    判準（門檻 config.FUNDS_TREND_CHANGE_PCT）：
      現貨占比↑ 且 全場所總值↓        → 收手中（現金化＋資本外移）
      現貨占比↓ 且 持倉側資金/名目↑    → 重新進場
      變化未達門檻或方向不成型          → 持平
      有效資料點 < FUNDS_TREND_MIN_POINTS → 資料累積中
    「持倉側資金」= 全場所總值 − 現貨（＝原生＋builder 的抵押品），與 position_value
    （持倉名目）任一上升即算「錢被派出去交易」——名目可能全在 builder dex，而
    position_value 只涵蓋原生永續，故兩者取聯集判斷。
    """
    days = config.FUNDS_TREND_DAYS if days is None else days
    thr = config.FUNDS_TREND_CHANGE_PCT if threshold is None else threshold
    pts = [r for r in rows
           if isinstance(r, dict)
           and r.get("spot_value_usd") is not None
           and r.get("total_value_all_venues") is not None]
    pts = pts[-days:] if days and days > 0 else pts
    out = {"status": TREND_ACCUMULATING, "n_points": len(pts), "days": days,
           "threshold": thr, "first_date": None, "last_date": None,
           "spot_share_first": None, "spot_share_last": None,
           "spot_share_change": None, "total_first": None, "total_last": None,
           "total_change_pct": None, "perp_change_pct": None,
           "position_value_change_pct": None}
    if len(pts) < config.FUNDS_TREND_MIN_POINTS:
        return out

    first, last = pts[0], pts[-1]
    t_f, t_l = float(first["total_value_all_venues"]), float(last["total_value_all_venues"])
    s_f, s_l = float(first["spot_value_usd"]), float(last["spot_value_usd"])
    out["first_date"], out["last_date"] = first.get("date"), last.get("date")
    out["total_first"], out["total_last"] = round(t_f, 2), round(t_l, 2)
    if t_f <= 0 or t_l <= 0:
        return out  # 分母 0 防呆：占比無意義 → 維持「資料累積中」，不硬掰方向
    share_f, share_l = s_f / t_f, s_l / t_l
    out["spot_share_first"] = round(share_f, 4)
    out["spot_share_last"] = round(share_l, 4)
    out["spot_share_change"] = round(share_l - share_f, 4)
    out["total_change_pct"] = round((t_l - t_f) / t_f, 4)
    perp_f, perp_l = t_f - s_f, t_l - s_l
    if perp_f > 0:
        out["perp_change_pct"] = round((perp_l - perp_f) / perp_f, 4)
    pv_f = first.get("position_value")
    pv_l = last.get("position_value")
    if pv_f is not None and pv_l is not None and float(pv_f) > 0:
        out["position_value_change_pct"] = round((float(pv_l) - float(pv_f)) / float(pv_f), 4)

    share_chg = out["spot_share_change"]
    total_chg = out["total_change_pct"]
    deploy_up = ((out["perp_change_pct"] is not None and out["perp_change_pct"] >= thr)
                 or (out["position_value_change_pct"] is not None
                     and out["position_value_change_pct"] >= thr)
                 or (perp_f <= 0 and perp_l > 0))   # 從 0 抵押品變成有抵押品＝重新派錢
    if share_chg >= thr and total_chg <= -thr:
        out["status"] = TREND_CASHING_OUT
    elif share_chg <= -thr and deploy_up:
        out["status"] = TREND_REENTERING
    else:
        out["status"] = TREND_FLAT
    return out


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


def _fmt_px(val):
    """價格格式化：>=1 用千分位兩位小數；<1 保留有效小數（永續小幣可能 <1）。"""
    if val is None:
        return "—"
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    if v == 0:
        return "0"
    if abs(v) >= 1:
        return f"{v:,.2f}"
    return f"{v:,.6f}".rstrip("0").rstrip(".")


def build_markdown(dossier, new_positions, disappeared, initialized):
    m = dossier["metrics"]
    addr = dossier["address"]
    lines = [
        f"# 永續錢包深度追蹤 dossier — {addr}",
        "",
        f"> 純唯讀追蹤報告（{dossier['snapshot_date']}）。像追蹤一個交易員一樣逐日盯這個永續錢包。",
        "> 不含任何下單/簽章/金鑰/錢包連線；不構成投資建議。",
        "",
        "## 1. 身分",
        "",
        f"- 地址：`{addr}`",
        f"- 標籤：{dossier['label'] or '—'}",
        f"- 目前分類：**{dossier['classification']}**",
        f"- 分類理由：{'；'.join(dossier['classification_reasons'][:3]) or '—'}",
        f"- 帳戶淨值（原生＋builder dex，**不含現貨**）：${_fmt(m.get('account_value'))}"
        + (f"；含現貨的全場所總值 ${_fmt(m.get('total_value_all_venues'))}（見 §7）"
           if m.get("total_value_all_venues") is not None else "（現貨見 §7）"),
        "",
        "## 2. 目前持倉",
        "",
        f"持倉名目總值：**${_fmt(dossier['position_value'])}**"
        f"（未實現 PnL ${_fmt(dossier['unrealized_pnl'])}，"
        f"{dossier['n_open_positions']} 個未平倉部位）",
        "",
    ]
    if dossier["open_positions"]:
        lines += ["| 場所 | 幣 | 方向 | 槓桿 | 進場價 | 強平價 | 未實現PnL | 名目 |",
                  "|---|---|---|---:|---:|---:|---:|---:|"]
        for p in sorted(dossier["open_positions"],
                        key=lambda x: -(x["position_value"] or 0)):
            lev = f"{_fmt(p['leverage_value'], ',.0f')}x" + (
                f" {p['leverage_type']}" if p["leverage_type"] else "")
            # dex 空字串＝原生永續；其餘為 builder dex 名（如 xyz）
            venue = (p.get("dex") or "").strip() or "原生"
            lines.append(
                f"| {venue} | {p['coin'] or '—'} | {p['side'] or '—'} | {lev} "
                f"| {_fmt_px(p['entry_px'])} | {_fmt_px(p['liquidation_px'])} "
                f"| ${_fmt(p['unrealized_pnl'])} | ${_fmt(p['position_value'])} |")
    else:
        lines.append("（目前無未平倉部位）")

    lines += ["", "## 3. 績效（portfolio）", "",
              f"- 總 PnL：${_fmt(m.get('total_pnl'))}",
              f"- 峰值回撤：{_fmt(m.get('max_drawdown_pct'), '.0%')}",
              f"- profit factor：{_fmt(m.get('profit_factor'), ',.2f')}"
              f"（平均獲利 ${_fmt(m.get('avg_win'))} / 平均虧損 ${_fmt(m.get('avg_loss'))}）",
              f"- 已實現勝率（僅參考）：{_fmt(m.get('realized_win_rate'), '.0%')}",
              f"- 正月比率：{_fmt(m.get('positive_month_ratio'), '.0%')}",
              f"- 活躍跨度：{_fmt(m.get('span_days'), ',.0f')} 天"
              f"（閒置 {_fmt(m.get('days_idle'), ',.0f')} 天）",
              f"- 資金費累計：${_fmt(m.get('funding_total'))}",
              f"- PnL 資料來源：{m.get('pnl_source') or '—'}"
              + ("（⚠️ 低信心，缺 portfolio PnL 曲線）" if m.get("low_confidence") else ""),
              "", "月度 PnL 序列：", ""]
    monthly = m.get("monthly_pnl") or {}
    if monthly:
        lines += ["| 月份 | PnL |", "|---|---:|"]
        for mon, val in monthly.items():
            lines.append(f"| {mon} | ${_fmt(val)} |")
    else:
        lines.append("（無月度序列）")

    lines += ["", "## 4. 交易輪廓", "",
              f"- 成交筆數：{m.get('n_fills', 0)} 筆",
              f"- 主力幣：{m.get('top_coin') or '—'}",
              f"- 淨方向比：{_fmt(m.get('net_direction_ratio'), '.2%')}"
              "（≈0 疑對敲刷量）",
              f"- 平均持倉：{_fmt(m.get('avg_hold_hours'), ',.2f')} 小時",
              f"- 目前最高槓桿：{_fmt(m.get('current_max_leverage'), ',.0f')}x"
              + ("（⚠️ 極端槓桿）" if m.get("has_extreme_leverage") else ""),
              f"- 曾被強平：{'⚠️ 是' if m.get('had_liquidation') else '否'}",
              "", "近 20 筆成交 timeline：", ""]
    if dossier["recent_fills"]:
        lines += ["| 時間 | 幣 | 動作 | px | sz | closedPnl |",
                  "|---|---|---|---:|---:|---:|"]
        for t in dossier["recent_fills"]:
            when = (t["time"][:10] if t["time"] else "—")
            action = t["dir"] or "—"
            if t["is_liquidation"]:
                action += " 🔴強平"
            lines.append(
                f"| {when} | {t['coin'] or '—'} | {action} "
                f"| {_fmt_px(t['px'])} | {_fmt(t['sz'], ',g')} "
                f"| ${_fmt(t['closed_pnl'])} |")
    else:
        lines.append("（無成交紀錄）")

    lines += ["", "## 5. 決策頻率複核（fills → 部位事件）", "",
              "> fills ≠ 決策：一張大單在薄訂單簿會拆成多筆成交、分批建倉/出場也是同一個",
              f"> 交易決策。同幣種同方向、相鄰 fills 間隔 <= {config.AGG_EVENT_GAP_MINUTES} "
              "分鐘聚合為一「部位事件」，以事件數重算真實決策頻率。",
              "",
              f"- 近 30 天部位事件數：**{_fmt(m.get('n_events_last_30d'), ',.0f')}** 個"
              f"（vs fills {_fmt(m.get('n_fills_last_30d'), ',.0f')} 筆；"
              f"頻率門檻 <= {config.FOLLOWABLE_MAX_EVENTS_30D} 事件，fills 數僅參考）",
              f"- 30 天窗 fills 覆蓋：{_fmt(m.get('events_30d_coverage_days'), ',.1f')} 天"
              + (f"（fills 截斷，30 日事件外推 ≈ "
                 f"{_fmt(m.get('n_events_last_30d_est'), ',.0f')} 個，頻率判定用外推值）"
                 if m.get("n_events_last_30d_est") != m.get("n_events_last_30d") else ""),
              f"- 全 fills 窗事件數：{_fmt(m.get('n_events'), ',.0f')} 個"
              f"（fills 共 {_fmt(m.get('n_fills'), ',.0f')} 筆）",
              f"- median 每事件 fills：{_fmt(m.get('median_fills_per_event'), ',.1f')} 筆",
              f"- median 事件名目：${_fmt(m.get('median_event_notional'))}",
              f"- 事件間隔分布：median {_fmt(m.get('median_gap_between_events_hours'))} 小時"
              f"／p90 {_fmt(m.get('p90_gap_between_events_hours'))} 小時",
              ""]
    fol = dossier.get("followable") or {}
    if fol.get("ok"):
        lines.append("**升級後可跟性判定：✅ 通過** — 頻率（近 30 天部位事件數）、"
                     "平均持倉、槓桿三條件皆符合。")
    else:
        lines.append("**升級後可跟性判定：❌ 不通過**，原因：")
        for r in fol.get("reasons") or ["未判定"]:
            lines.append(f"- {r}")

    lines += ["", "## 6. 新開倉/平倉偵測", ""]
    if initialized:
        lines.append("**initialized** — 首次追蹤，無前次持倉可比對（下次執行起偵測異動）。")
    else:
        lines.append(f"本次新開倉：{len(new_positions)} 個")
        for p in new_positions:
            lines.append(f"- 🟢 新開倉：{p['coin'] or p['key']}")
        lines.append(f"\n本次消失持倉：{len(disappeared)} 個")
        for p in disappeared:
            lines.append(f"- ⚪ 已平倉/消失：{p['coin'] or p['key']}")
        if not new_positions and not disappeared:
            lines.append("（與上次快照相比無持倉異動）")

    lines += _funds_section(m)
    lines += _trend_section(dossier.get("funds_trend"))

    lines += ["", "> 純唯讀觀察，不執行任何交易。", ""]
    return "\n".join(lines)


def _funds_section(m):
    """dossier §7「資金分布（多場所）」——資料全部來自**每日** snapshot（含現貨）。"""
    lines = ["", "## 7. 資金分布（多場所）", "",
             "> 現貨（spot）與各 builder dex 皆為**每日抓取**（fetch.py 對 tracked 錢包查"
             "`spotClearinghouseState` ＋ 逐 dex `clearinghouseState`），不再依賴週期性診斷。",
             "> 現貨估值：USDC/USDH 類 1:1；其他 token 用 entryNtl 成本基礎粗估（標「估」）。",
             ""]
    by_dex = m.get("account_value_by_dex") or {}
    spot_usd = m.get("spot_value_usd")
    total = m.get("total_value_all_venues")

    def share(val):
        if val is None or not total:
            return "—"
        return f"{val / total:.1%}"

    lines += ["| 場所 | 帳戶淨值(USD) | 占比 |", "|---|---:|---:|"]
    native_av = by_dex.get("", m.get("account_value_native"))
    lines.append(f"| 原生永續 dex | ${_fmt(native_av)} | {share(native_av)} |")
    zero_dexs = []
    for dex, val in sorted((d, v) for d, v in by_dex.items() if d):
        if not val:   # 零餘額/查不到的 builder dex 併成一行（查過但沒錢，不佔表格）
            zero_dexs.append(dex)
            continue
        lines.append(f"| builder dex `{dex}` | ${_fmt(val)} | {share(val)} |")
    if spot_usd is None:
        lines.append("| 現貨 spot | —（本日未取得：非 tracked 錢包／查詢失敗／舊格式快照） | — |")
    else:
        lines.append(f"| 現貨 spot | ${_fmt(spot_usd)} | {share(spot_usd)} |")
    lines.append(f"| **合計（全場所）** | **${_fmt(total)}** | — |"
                 if total is not None else
                 "| **合計（全場所）** | **—（缺現貨資料，不以原生＋builder 冒充全場所總值）** | — |")
    if zero_dexs:
        lines += ["", f"查過但零餘額的 builder dex（{len(zero_dexs)} 個）："
                      + "、".join(f"`{d}`" for d in zero_dexs)]
    nn = m.get("non_native_share")
    if nn is not None:
        lines += ["", f"非原生（builder dex＋現貨）占比：**{nn:.1%}**"
                      "——占比高代表主要資金不在原生永續 dex。"]
    tokens = m.get("spot_tokens")
    if tokens:
        lines += ["", "現貨非零餘額（最多 10 筆）：", "",
                  "| 幣 | 數量 | USD |", "|---|---:|---:|"]
        for t in tokens:
            usd = (f"${_fmt(t.get('usd'))}" + ("（估）" if t.get("estimated") else "")
                   if t.get("usd") is not None else "—（無 entryNtl，無法估值）")
            lines.append(f"| {t.get('coin') or '—'} | {_fmt_qty(t.get('qty'))} | {usd} |")
    return lines


def _trend_section(trend):
    """dossier §8「資金流向趨勢」——逐日 timeline 的現貨占比／全場所總值變化（純觀察）。"""
    trend = trend or {"status": TREND_ACCUMULATING, "n_points": 0,
                      "days": config.FUNDS_TREND_DAYS}
    days = trend.get("days") or config.FUNDS_TREND_DAYS
    lines = ["", "## 8. 資金流向趨勢", "",
             f"> 比較 timeline 最近 {days} 個資料點的「現貨占比」與「全場所總值」。"
             f"變化 < {config.FUNDS_TREND_CHANGE_PCT:.0%} 視為持平；"
             f"有效資料點 < {config.FUNDS_TREND_MIN_POINTS} 個 → 資料累積中。",
             "",
             f"- 有效資料點：{trend.get('n_points', 0)} 個"
             + (f"（{trend.get('first_date')} → {trend.get('last_date')}）"
                if trend.get("first_date") else "")]
    if trend.get("spot_share_first") is not None:
        lines += [
            f"- 現貨占比：{trend['spot_share_first']:.1%} → {trend['spot_share_last']:.1%}"
            f"（{trend['spot_share_change'] * 100:+.1f} 個百分點）",
            f"- 全場所總值：${_fmt(trend.get('total_first'))} → ${_fmt(trend.get('total_last'))}"
            + (f"（{trend['total_change_pct']:+.1%}）"
               if trend.get("total_change_pct") is not None else ""),
        ]
        if trend.get("perp_change_pct") is not None:
            lines.append(f"- 持倉側資金（原生＋builder 抵押品）："
                         f"{trend['perp_change_pct']:+.1%}")
        if trend.get("position_value_change_pct") is not None:
            lines.append(f"- 原生持倉名目：{trend['position_value_change_pct']:+.1%}")
    lines += ["", f"**觀察：{trend.get('status')}**"]
    if trend.get("status") == TREND_ACCUMULATING:
        lines.append("（每日管線會持續累積現貨與各場所資金；點數足夠後這節才會給方向。）")
    lines += ["", "> 本節僅描述觀察到的資金流向，不是投資建議、不預測價格、不建議任何操作。"]
    return lines


# ---------------------------------------------------------------------------
# 全維度診斷探測（唯讀 info API：資金在哪／有無外轉／是否仍在交易）
# ---------------------------------------------------------------------------

# ledger（userNonFundingLedgerUpdates）的 delta.type → 資金流向語意。
# 「外轉」= 錢離開這個地址的控制（withdraw 到鏈上、轉給別的地址、進 vault）；
# 「內部」= 同一地址內換帳（perp ↔ spot 的 accountClassTransfer）——這正是
# 「換地址」與「同地址換戰場」的判別關鍵。
LEDGER_OUT_TYPES = ("withdraw",)                       # 一律視為外轉
LEDGER_TRANSFER_TYPES = ("internalTransfer", "spotTransfer",
                         "subAccountTransfer")          # 看 destination 決定進/出
LEDGER_VAULT_OUT_TYPES = ("vaultDeposit", "vaultCreate")
LEDGER_IN_TYPES = ("deposit", "vaultWithdraw", "vaultDistribution",
                   "rewardsClaim", "liquidation")
LEDGER_INTERNAL_TYPES = ("accountClassTransfer",)       # perp ↔ spot，同地址內部
# send/spotSend：destination 是「系統地址」→ HyperCore↔HyperEVM 跨層（同一擁有者）；
# 否則是真的轉給別的地址 → 外轉。**不得**再落到 unknown（那會讓報告說「無外轉紀錄」）。
LEDGER_SEND_TYPES = ("send", "spotSend")
# 現貨估值規則與 summarize_spot 已移到 classify.py（compute_metrics 每日也要用同一套估值）。
# 這裡只保留別名，讓既有呼叫端／測試不必改，且**不存在第二份實作**。
SPOT_USD_COINS = classify.SPOT_USD_COINS
summarize_spot = classify.summarize_spot


def diagnostic_info_body(info_type, address=None, dex=None, start_time_ms=None):
    """組診斷用 info API 請求體（唯讀查詢）。type 不在白名單 → raise，制度性防呆。

    dex 一律**原樣傳遞** perpDexs 回應裡的名稱（HIP-3 builder dex 名稱，如 "xyz"）；
    不得自行推測、改大小寫或硬編。
    """
    if info_type not in config.DIAGNOSTIC_ALLOWED_INFO_TYPES:
        raise ValueError(f"info type 不在唯讀白名單 {config.DIAGNOSTIC_ALLOWED_INFO_TYPES}："
                         f"{info_type}")
    body = {"type": info_type}
    if address is not None:
        body["user"] = address
    if dex is not None:
        body["dex"] = dex
    if start_time_ms is not None:
        body["startTime"] = int(start_time_ms)
    return body


class _Probe:
    """診斷探測器：包 fetch.http_post_info（沿用既有 timeout/重試/sleep 與 endpoint_health）。

    連續失敗 config.DIAGNOSTIC_ABORT_AFTER_FAILURES 次 → 進入 aborted，後續請求直接跳過。
    （雲端 session egress 被擋時快速降級成「資料不足」，不要 15 個請求各燒 3 次重試。）
    """

    def __init__(self, post_fn=None, meta=None):
        self.post_fn = post_fn or fetch.http_post_info
        self.meta = meta if meta is not None else fetch.Meta()
        self.consecutive_failures = 0
        self.aborted = False

    def get(self, info_type, name=None, **kw):
        if self.aborted:
            return None, False
        try:
            body = diagnostic_info_body(info_type, **kw)
        except ValueError as exc:  # 白名單擋下 → 記錄不 crash
            self.meta.note(f"診斷請求被白名單擋下：{exc}")
            return None, False
        try:
            data, ok = self.post_fn(body, name or info_type, self.meta)
        except Exception as exc:  # 任何 HTTP 層例外都不得中斷診斷
            self.meta.note(f"診斷請求例外（{name or info_type}）："
                           f"{type(exc).__name__}: {exc}")
            data, ok = None, False
        if ok:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= config.DIAGNOSTIC_ABORT_AFTER_FAILURES:
                self.aborted = True
                self.meta.note(f"連續 {self.consecutive_failures} 個請求失敗 → 中止診斷探測，"
                               "本次裁決標『資料不足』")
        return data, ok


def _iso(ts):
    """epoch 秒 → ISO 字串；None 回 None。"""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def _fmt_qty(val):
    """數量格式化（診斷 md 用）：避免 `,g` 把 4000000 印成 4e+06；小數保留有效位。"""
    if val is None:
        return "—"
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    spec = ",.4f" if abs(v) >= 1 else ",.8f"
    return format(v, spec).rstrip("0").rstrip(".") or "0"


def _venue_of(coin):
    """由 coin 命名判斷戰場：'xyz:SNDK' → builder dex 'xyz'；'@166' → 現貨；其餘 → 原生永續。"""
    c = str(coin or "")
    if ":" in c:
        return f"builder:{c.split(':', 1)[0]}"
    if c.startswith("@"):
        return "spot"
    return "native"


def _ledger_rows(raw):
    """userNonFundingLedgerUpdates 回應 → rows list（防禦多形：list 或包一層 dict）。"""
    if isinstance(raw, dict):
        for key in ("ledgerUpdates", "updates", "data"):
            if isinstance(raw.get(key), list):
                return raw[key]
        return []
    return raw if isinstance(raw, list) else []


def _ledger_amount_usd(delta):
    """delta → 美元金額（usdc / usdcValue / amount 依序取；取不到回 None）。"""
    for key in ("usdc", "usdcValue", "usdValue", "amount", "delta"):
        val = classify._to_float(delta.get(key))
        if val is not None:
            return abs(val)
    return None


def is_system_address(addr):
    """destination 是否為 Hyperliquid spot token 的「系統地址」（HyperCore ↔ HyperEVM 跨層）。

    判準（官方文件）：每個 spot token 都有一個系統地址＝第一個 byte 為 0x20、其餘為 0，
    末端以 big-endian 編碼 token index（token index 0 → `0x2000…0000`；
    token index 200 → `0x20000…00c8`）。**HYPE 例外**，系統地址為 `0x2222…2222`。
    實作：前綴 `0x20` ＋ 剩下 38 個 hex 去掉前導 0 後長度 <= 4 視為 token index。

    送到系統地址的款項進入「**同一位擁有者在 HyperEVM 上的同一地址**」，不是第三方，
    所以不可算成「轉出到其他地址」。
    來源：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/
          hypercore-less-than-greater-than-hyperevm-transfers
    """
    if not isinstance(addr, str):
        return False
    a = addr.strip().lower()
    if len(a) != 42 or not a.startswith("0x"):
        return False
    try:
        int(a[2:], 16)                     # 非 hex（含空字串）→ 不是地址
    except ValueError:
        return False
    if a == config.LEDGER_HYPE_SYSTEM_ADDR:
        return True
    if not a.startswith(config.LEDGER_SYSTEM_ADDR_PREFIX):
        return False
    body = a[len(config.LEDGER_SYSTEM_ADDR_PREFIX):]      # 前綴後的 38 個 hex
    return len(body.lstrip("0")) <= config.LEDGER_SYSTEM_ADDR_INDEX_MAX_HEX


def classify_ledger_updates(raw, self_address, cutoff_ts=None,
                            max_rows=None):
    """把非資金費帳變動分成「外轉 / 外入 / 同地址內部」並加總（判斷有無換地址的核心）。

    外轉 = withdraw、或 send/spotSend/internalTransfer/spotTransfer/subAccountTransfer 且
    destination 既不是自己也不是系統地址、或 vaultDeposit（錢進 vault，離開現貨/永續帳戶）。
    跨層 = 上述轉帳型 type 且 destination 是系統地址（HyperCore → HyperEVM，同一擁有者）
    ——單獨計 bridge_out，**不算外轉、也不算 unknown**（見 is_system_address）。
    內部 = accountClassTransfer（perp ↔ spot，同一地址換戰場，**不是**搬家）。
    unknown 只留真正判不出方向的 type（報告必須醒目警示，不可說成「沒有資金移動」）。
    """
    self_addr = str(self_address or "").lower()
    max_rows = config.DIAGNOSTIC_MAX_LEDGER_ROWS if max_rows is None else max_rows
    res = {
        "n_total": 0, "n_in_window": 0, "n_kept": 0,
        "by_type": {}, "external_out_usd": 0.0, "external_in_usd": 0.0,
        "internal_usd": 0.0, "vault_out_usd": 0.0, "bridge_out_usd": 0.0,
        "unknown_usd": 0.0,
        "external_out_rows": [], "bridge_out_rows": [], "unknown_rows": [],
        "internal_rows": [], "rows": [],
        "n_bridge_out": 0, "n_unknown": 0,
        "counterparties": {}, "parse_failed": False,
    }
    rows = _ledger_rows(raw)
    if raw is not None and not rows and not isinstance(raw, list):
        res["parse_failed"] = True
    res["n_total"] = len(rows)
    kept = []
    for it in rows:
        if not isinstance(it, dict):
            continue
        delta = it.get("delta") if isinstance(it.get("delta"), dict) else it
        ts = classify._norm_ts(it.get("time") or delta.get("time"))
        if cutoff_ts is not None and ts is not None and ts < cutoff_ts:
            continue
        res["n_in_window"] += 1
        dtype = str(delta.get("type") or "unknown")
        usd = _ledger_amount_usd(delta)
        dest = delta.get("destination") or delta.get("to") or delta.get("vault")
        dest = str(dest).lower() if isinstance(dest, str) else None
        # 方向判定
        if dtype in LEDGER_OUT_TYPES:
            direction = "out"
        elif dtype in LEDGER_VAULT_OUT_TYPES:
            direction = "vault_out"
        elif dtype in LEDGER_TRANSFER_TYPES or dtype in LEDGER_SEND_TYPES:
            if is_system_address(dest):
                direction = "bridge_out"     # HyperCore → HyperEVM，同一擁有者，非第三方
            elif dest is not None and dest == self_addr:
                direction = "in"
            else:
                direction = "out"            # 真的轉給別的地址
        elif dtype in LEDGER_INTERNAL_TYPES:
            direction = "internal"
        elif dtype in LEDGER_IN_TYPES:
            direction = "in"
        else:
            direction = "unknown"
        amount = usd or 0.0
        if direction == "out":
            res["external_out_usd"] += amount
        elif direction == "vault_out":
            res["vault_out_usd"] += amount
        elif direction == "bridge_out":
            res["bridge_out_usd"] += amount
        elif direction == "in":
            res["external_in_usd"] += amount
        elif direction == "internal":
            res["internal_usd"] += amount
        else:
            res["unknown_usd"] += amount
        bucket = res["by_type"].setdefault(
            dtype, {"n": 0, "usd": 0.0, "direction": direction})
        bucket["n"] += 1
        bucket["usd"] = round(bucket["usd"] + amount, 2)
        if direction != bucket["direction"]:
            bucket["direction"] = "mixed"
        row = {"time": ts, "time_iso": _iso(ts), "type": dtype,
               "usd": (round(usd, 2) if usd is not None else None),
               "direction": direction, "destination": dest,
               "token": delta.get("token"), "hash": it.get("hash")}
        kept.append(row)
        if direction in ("out", "vault_out"):
            res["external_out_rows"].append(row)
            if dest:
                res["counterparties"][dest] = round(
                    res["counterparties"].get(dest, 0.0) + amount, 2)
        elif direction == "bridge_out":
            # 不進 counterparties：系統地址不是「對手方」，是同一擁有者的 HyperEVM 側
            res["bridge_out_rows"].append(row)
            res["n_bridge_out"] += 1
        elif direction == "internal":
            res["internal_rows"].append(row)
        elif direction == "unknown":
            res["unknown_rows"].append(row)
            res["n_unknown"] += 1
    kept.sort(key=lambda r: (r["time"] is None, -(r["time"] or 0)))
    res["rows"] = kept[:max_rows]          # 體積控制：最多留 max_rows 筆（近的優先）
    res["n_kept"] = len(res["rows"])
    for key in ("external_out_rows", "bridge_out_rows", "unknown_rows", "internal_rows"):
        res[key].sort(key=lambda r: (r["time"] is None, -(r["time"] or 0)))
    res["external_out_rows"] = res["external_out_rows"][:50]
    res["bridge_out_rows"] = res["bridge_out_rows"][:50]
    res["unknown_rows"] = res["unknown_rows"][:20]
    res["internal_rows"] = res["internal_rows"][:20]
    for key in ("external_out_usd", "external_in_usd", "internal_usd",
                "vault_out_usd", "bridge_out_usd", "unknown_usd"):
        res[key] = round(res[key], 2)
    return res


def summarize_fills_activity(raw, now_ts, max_fills=None):
    """userFills → 最後成交時間、近 7/30 天筆數、幣種/戰場分布、最後 N 筆明細。"""
    max_fills = config.DIAGNOSTIC_MAX_FILLS if max_fills is None else max_fills
    fills = classify.parse_fills(raw)   # 已按時間排序（原始回應不保證有序）
    ts_list = [f["ts"] for f in fills if f["ts"] is not None]
    last_ts = max(ts_list) if ts_list else None
    coins = Counter(f["coin"] for f in fills if f["coin"])
    venues = Counter(_venue_of(f["coin"]) for f in fills if f["coin"])
    recent = []
    for f in fills[-max_fills:]:
        recent.append({"time_iso": _iso(f["ts"]), "coin": f["coin"],
                       "dir": f["dir"] or f["side"], "px": f["px"], "sz": f["sz"],
                       "closed_pnl": (round(f["closed_pnl"], 2)
                                      if f["closed_pnl"] is not None else None)})
    return {
        "n_fills": len(fills),
        "truncated": len(fills) >= config.MAX_USER_FILLS,
        "last_fill_ts": last_ts,
        "last_fill_iso": _iso(last_ts),
        "days_since_last_fill": (round((now_ts - last_ts) / DAY_SEC, 2)
                                 if last_ts is not None else None),
        "n_fills_7d": sum(1 for t in ts_list if t >= now_ts - 7 * DAY_SEC),
        "n_fills_30d": sum(1 for t in ts_list if t >= now_ts - 30 * DAY_SEC),
        "first_fill_iso": _iso(min(ts_list)) if ts_list else None,
        "top_coins": coins.most_common(8),
        "by_venue": dict(venues.most_common()),
        "recent_fills": recent,
    }


def summarize_portfolio_windows(raw):
    """portfolio → 每個視窗最新 accountValue / pnl / vlm（與 clearinghouseState 對照用）。"""
    parsed = classify.parse_portfolio(raw)
    out = {}
    for name, win in parsed.items():
        avh = classify.parse_history(win.get("accountValueHistory"))
        pnl = classify.parse_history(win.get("pnlHistory"))
        out[name] = {
            "account_value_last": (round(avh[-1][1], 2) if avh else None),
            "account_value_ts_iso": (_iso(avh[-1][0]) if avh else None),
            "pnl_last": (round(pnl[-1][1], 2) if pnl else None),
            "vlm": (lambda v: round(v, 2) if v is not None else None)(
                classify._to_float(win.get("vlm"))),
            "n_points": len(avh),
        }
    return out


def summarize_funds(native_state, by_dex_states, spot):
    """(a)「資金在哪」：原生 perp / 各 builder dex / 現貨 各多少美元。"""
    wallet_like = {"clearinghouseState": native_state,
                   "clearinghouseStateByDex": by_dex_states or {}}
    positions, by_dex = classify.parse_positions_by_dex(wallet_like)
    native = by_dex.get("", {"n_positions": 0, "account_value": None,
                             "position_value": 0.0})
    builder = {d: v for d, v in by_dex.items() if d}
    builder_usd = sum(v["account_value"] for v in builder.values()
                      if v["account_value"] is not None)
    spot_usd = (spot or {}).get("usd_total_est") or 0.0
    native_usd = native["account_value"] or 0.0
    total = native_usd + builder_usd + spot_usd
    return {
        "native": native,
        "builder_dex": builder,
        "spot": spot or {},
        "native_usd": round(native_usd, 2),
        "builder_usd": round(builder_usd, 2),
        "spot_usd": round(spot_usd, 2),
        "total_usd": round(total, 2),
        "non_native_usd": round(builder_usd + spot_usd, 2),
        "non_native_share": (round((builder_usd + spot_usd) / total, 4)
                             if total > 0 else None),
        "positions": positions,
        "n_positions_total": len(positions),
        "n_positions_native": native["n_positions"],
        "n_positions_builder": sum(v["n_positions"] for v in builder.values()),
    }


VERDICT_MOVED = "換地址"
VERDICT_SWITCHED = "同地址換戰場（builder dex/現貨）"
VERDICT_IDLE = "真的停手觀望"
VERDICT_UNKNOWN = "資料不足"
# 旗標（不是第五種裁決）：與上面四種併存，用「｜」串在裁決後面
VERDICT_FLAG_CAPITAL_OUT = "⚠️ 資本外移中"


def _no_outflow_at_all(ledger):
    """是否真的完全沒有「錢離開交易帳戶」的訊號。

    只有外轉、vault、跨層轉移、無法分類**四者全為 0** 時才可以說「無外轉紀錄」；
    否則就是有資金移動只是類別不同，報告不得說成「沒有」。
    """
    return all((ledger.get(k) or 0.0) <= 0 for k in
               ("external_out_usd", "vault_out_usd", "bridge_out_usd", "unknown_usd"))


def _outflow_summary_line(ledger):
    """帳變動離場訊號的一行誠實摘要（供裁決理由用；有 unknown 就明說無法分類）。"""
    parts = []
    for key, label in (("external_out_usd", "外轉他址"),
                       ("vault_out_usd", "進 vault"),
                       ("bridge_out_usd", "跨層轉移（HyperCore→HyperEVM，同一擁有者）"),
                       ("unknown_usd", "⚠️ 無法分類")):
        val = ledger.get(key) or 0.0
        if val > 0:
            parts.append(f"{label} ${val:,.2f}")
    return (f"近 {config.DIAGNOSTIC_LEDGER_DAYS} 天帳變動離場訊號："
            + ("、".join(parts) if parts else "無"))


def _bridge_out_flag(diag):
    """跨層轉移占比是否高到該掛「資本外移中」旗標 → (flagged, reason 或 None)。

    佔比＝bridge_out / (bridge_out + 目前總資產)；門檻 config.DIAGNOSTIC_BRIDGE_OUT_SHARE。
    這是**旗標**不是裁決：錢還是同一位擁有者的，但已離開 HyperCore 交易帳戶。
    """
    ledger = diag.get("ledger") or {}
    bridge = ledger.get("bridge_out_usd") or 0.0
    if bridge <= 0:
        return False, None
    total = (diag.get("funds") or {}).get("total_usd") or 0.0
    share = bridge / max(bridge + total, 1e-9)
    if share < config.DIAGNOSTIC_BRIDGE_OUT_SHARE:
        return False, None
    return True, (f"跨層轉移（HyperCore→HyperEVM，同一地址擁有者，非第三方）"
                  f"${bridge:,.2f}，占「現餘＋跨層轉移」{share:.0%}"
                  f"（≥ {config.DIAGNOSTIC_BRIDGE_OUT_SHARE:.0%} 門檻）"
                  "→ 資本正離開交易場（跨層/減倉）")


def decide_verdict(diag):
    """四裁決之一（＋跨層轉移占比高時加註「資本外移中」旗標）+ 理由清單。"""
    verdict, reasons = _decide_verdict_base(diag)
    flagged, reason = _bridge_out_flag(diag)
    if flagged:
        reasons = list(reasons) + [reason]
        verdict = f"{verdict}｜{VERDICT_FLAG_CAPITAL_OUT}"
    return verdict, reasons


def _decide_verdict_base(diag):
    """四種裁決之一 + 理由清單（純函式，供離線測試四情境）。

    判準順序（先安全性、後語意）：
    1. 關鍵查詢全失敗 → 資料不足（絕不用缺資料硬推結論）
    2. 45 天內外轉金額大且占比高 → 換地址
    3. 非原生（builder dex + 現貨）資金占多數，或持倉/成交主要在非原生 → 同地址換戰場
    4. 其餘（資金仍在原生、無外轉、近期無成交）→ 真的停手觀望
    """
    funds = diag.get("funds") or {}
    ledger = diag.get("ledger") or {}
    trading = diag.get("trading") or {}
    ok_map = diag.get("queries_ok") or {}
    reasons = []

    # 1. 資料不足：連資金面（clearinghouseState/spot）與帳變動都沒查到
    have_funds = ok_map.get("clearinghouseState_native") or ok_map.get(
        "spotClearinghouseState") or ok_map.get("clearinghouseState_dex")
    have_ledger = ok_map.get("userNonFundingLedgerUpdates")
    if not have_funds and not have_ledger:
        reasons.append("資金面（clearinghouseState/spot）與帳變動（ledger）查詢皆未成功，"
                       "無法判斷資金流向")
        return VERDICT_UNKNOWN, reasons

    out_usd = (ledger.get("external_out_usd") or 0.0) + (ledger.get("vault_out_usd") or 0.0)
    total_usd = funds.get("total_usd") or 0.0
    non_native = funds.get("non_native_usd") or 0.0

    # 2. 換地址：外轉金額同時過絕對門檻與占比門檻
    if have_ledger and out_usd >= config.DIAGNOSTIC_MOVEOUT_MIN_USD and out_usd >= (
            config.DIAGNOSTIC_MOVEOUT_SHARE * (total_usd + out_usd)):
        reasons.append(f"近 {config.DIAGNOSTIC_LEDGER_DAYS} 天外轉 ${out_usd:,.2f}"
                       f"（≥ ${config.DIAGNOSTIC_MOVEOUT_MIN_USD:,.0f} 且占「現餘＋外轉」"
                       f"{out_usd / max(total_usd + out_usd, 1e-9):.0%}）")
        if ledger.get("counterparties"):
            tops = sorted(ledger["counterparties"].items(), key=lambda kv: -kv[1])[:3]
            reasons.append("外轉對手方：" + "、".join(f"{a}（${u:,.2f}）" for a, u in tops))
        return VERDICT_MOVED, reasons

    # 3. 同地址換戰場：資金或活動主要在 builder dex／現貨
    venues = trading.get("by_venue") or {}
    non_native_fills = sum(n for v, n in venues.items() if v != "native")
    total_fills = sum(venues.values())
    fills_mostly_non_native = (total_fills > 0
                               and non_native_fills / total_fills >= 0.5)
    funds_mostly_non_native = (total_usd > 0 and non_native >= (
        config.DIAGNOSTIC_NON_NATIVE_SHARE * total_usd))
    if funds_mostly_non_native or (fills_mostly_non_native and non_native > 0):
        if funds_mostly_non_native:
            reasons.append(f"非原生資金 ${non_native:,.2f} 占總資產 ${total_usd:,.2f} 的"
                           f"{non_native / max(total_usd, 1e-9):.0%}"
                           f"（builder dex ${funds.get('builder_usd') or 0:,.2f}"
                           f"／現貨 ${funds.get('spot_usd') or 0:,.2f}）")
        if fills_mostly_non_native:
            reasons.append(f"成交戰場分布：非原生 {non_native_fills}/{total_fills} 筆"
                           f"（{non_native_fills / max(total_fills, 1):.0%}）")
        if have_ledger and out_usd <= 0:
            if _no_outflow_at_all(ledger):
                reasons.append(f"近 {config.DIAGNOSTIC_LEDGER_DAYS} 天無外轉紀錄"
                               f"（內部轉移 ${ledger.get('internal_usd') or 0:,.2f}）")
            else:
                reasons.append(_outflow_summary_line(ledger))
        return VERDICT_SWITCHED, reasons

    # 4. 其餘 → 停手觀望（附上依據；若原生仍有活動則明寫，避免誤導）
    idle_days = trading.get("days_since_last_fill")
    if idle_days is not None:
        reasons.append(f"最後成交距今 {idle_days:.2f} 天"
                       f"（判定門檻 {config.DIAGNOSTIC_IDLE_DAYS} 天）")
    else:
        reasons.append("查無成交時間戳")
    reasons.append(f"總資產 ${total_usd:,.2f}（原生 ${funds.get('native_usd') or 0:,.2f}）、"
                   f"未平倉 {funds.get('n_positions_total') or 0} 個")
    if have_ledger and out_usd <= 0:
        if _no_outflow_at_all(ledger):
            reasons.append(f"近 {config.DIAGNOSTIC_LEDGER_DAYS} 天無外轉紀錄")
        else:
            reasons.append(_outflow_summary_line(ledger))
    if idle_days is not None and idle_days < config.DIAGNOSTIC_IDLE_DAYS:
        reasons.append(f"註：距今 < {config.DIAGNOSTIC_IDLE_DAYS} 天內仍有成交，"
                       "「停手」僅指未見資金搬遷與非原生集中，不代表完全沒動作")
    return VERDICT_IDLE, reasons


def build_diagnostic_markdown(diag):
    """人可讀裁決 md：三問（資金在哪／有無外轉／是否仍在交易）＋末段一句裁決。"""
    funds = diag.get("funds") or {}
    ledger = diag.get("ledger") or {}
    trading = diag.get("trading") or {}
    pf = diag.get("portfolio_windows") or {}
    addr = diag.get("address", "")
    lines = [
        f"# 全維度診斷探測 — {addr}",
        "",
        f"> 純唯讀診斷（{diag.get('date')}，探測時間 {diag.get('probed_at')}）。",
        "> 只用 Hyperliquid 公開 info API 的查詢型 type；不含下單/簽章/金鑰/錢包連線。",
        "> 動機：clearinghouseState（不帶 dex）只看原生永續 dex，對 HIP-3 builder 市場全盲，"
        "導致「0 持倉、$0 淨值」與 portfolio 的百萬淨值自相矛盾。",
        "",
        "## 0. 探測結果總表",
        "",
        "| 查詢 | 成功 |",
        "|---|---|",
    ]
    for name, ok_flag in (diag.get("queries_ok") or {}).items():
        lines.append(f"| {name} | {'✅' if ok_flag else '❌'} |")
    if diag.get("dexs_detected") is not None:
        lines += ["", f"perpDexs 偵測到的 builder dex（查詢上限 {config.FETCH_MAX_DEXS}"
                      f" 個）：{', '.join(diag['dexs_detected']) or '（無/查詢失敗）'}"]
    if diag.get("aborted"):
        lines += ["", f"⚠️ 連續 {config.DIAGNOSTIC_ABORT_AFTER_FAILURES} 個請求失敗 → "
                      "探測提早中止（多半是本機/雲端 egress 被擋），下方數值不完整。"]

    # --- (a) 資金在哪 ---
    lines += ["", "## (a) 資金在哪？", "",
              "| 場所 | 帳戶淨值(USD) | 未平倉數 | 持倉名目(USD) |",
              "|---|---:|---:|---:|"]
    native = funds.get("native") or {}
    lines.append(f"| 原生永續 dex | ${_fmt(native.get('account_value'))} "
                 f"| {native.get('n_positions', 0)} "
                 f"| ${_fmt(native.get('position_value'))} |")
    for dex, v in sorted((funds.get("builder_dex") or {}).items()):
        lines.append(f"| builder dex `{dex}` | ${_fmt(v.get('account_value'))} "
                     f"| {v.get('n_positions', 0)} | ${_fmt(v.get('position_value'))} |")
    spot = funds.get("spot") or {}
    lines.append(f"| 現貨 spot | ${_fmt(spot.get('usd_total_est'))}"
                 f"{'（含估算）' if spot.get('estimated') else ''} "
                 f"| {spot.get('n_nonzero', 0)} 幣 | — |")
    if funds.get("known") is False:
        lines.append("| **合計** | **—（資金面查詢全失敗，$0 不可解讀為真的沒錢）** | — | — |")
    else:
        lines.append(f"| **合計** | **${_fmt(funds.get('total_usd'))}** "
                     f"| **{funds.get('n_positions_total', 0)}** | — |")
    if funds.get("non_native_share") is not None:
        lines += ["", f"非原生（builder dex＋現貨）占比：**{funds['non_native_share']:.1%}**"
                      f"（${_fmt(funds.get('non_native_usd'))} / ${_fmt(funds.get('total_usd'))}）"]
    if spot.get("balances"):
        lines += ["", "現貨非零餘額（估值：USDC 類 1:1；其他 token 用 entryNtl 成本基礎粗估）：", "",
                  "| 幣 | 數量 | USD |", "|---|---:|---:|"]
        for b in spot["balances"][:20]:
            usd = (f"${_fmt(b.get('usd'))}" + ("（估）" if b.get("usd_is_estimate") else "")
                   if b.get("usd") is not None else "—")
            lines.append(f"| {b['coin']} | {_fmt_qty(b['total'])} | {usd} |")
    if pf:
        lines += ["", "portfolio 各視窗最新帳戶淨值（與 clearinghouseState 對照）：", "",
                  "| 視窗 | accountValue | vlm |", "|---|---:|---:|"]
        for name in ("day", "week", "month", "allTime",
                     "perpDay", "perpWeek", "perpMonth", "perpAllTime"):
            if name in pf:
                lines.append(f"| {name} | ${_fmt(pf[name]['account_value_last'])} "
                             f"| ${_fmt(pf[name]['vlm'])} |")
        lines += ["", "> portfolio 的 accountValue 含全部場所（原生＋builder＋現貨），"
                      "perp* 視窗只含永續——兩者差額即「不在原生永續」的部分。"]
    if funds.get("positions"):
        lines += ["", "全部未平倉部位（含 builder dex）：", "",
                  "| dex | 幣 | 方向 | 槓桿 | 名目(USD) | 未實現PnL |",
                  "|---|---|---|---:|---:|---:|"]
        for p in sorted(funds["positions"], key=lambda x: -(x.get("position_value") or 0)):
            lines.append(f"| {p.get('dex') or '（原生）'} | {p.get('coin') or '—'} "
                         f"| {p.get('side') or '—'} | {_fmt(p.get('leverage_value'), ',.0f')}x "
                         f"| ${_fmt(p.get('position_value'))} "
                         f"| ${_fmt(p.get('unrealized_pnl'))} |")

    # --- (b) 有沒有轉出到其他地址 ---
    lines += ["", f"## (b) 有沒有轉出到其他地址？（近 {config.DIAGNOSTIC_LEDGER_DAYS} 天"
                  "非資金費帳變動）", ""]
    if not (diag.get("queries_ok") or {}).get("userNonFundingLedgerUpdates"):
        lines.append("❌ userNonFundingLedgerUpdates 查詢未成功——**無法判斷有無外轉**"
                     "（不以缺資料推論「沒有」）。")
    else:
        out_total = (ledger.get("external_out_usd") or 0.0) + (ledger.get("vault_out_usd") or 0.0)
        bridge_out = ledger.get("bridge_out_usd") or 0.0
        unknown_usd = ledger.get("unknown_usd") or 0.0
        lines += [f"- 視窗內帳變動筆數：{ledger.get('n_in_window', 0)}"
                  f"（回應共 {ledger.get('n_total', 0)} 筆，json 保留 {ledger.get('n_kept', 0)} 筆）",
                  f"- 外轉合計（withdraw／轉他址／進 vault）：**${_fmt(out_total)}**",
                  f"- 跨層轉移合計（HyperCore→HyperEVM，同一地址擁有者，非第三方）："
                  f"**${_fmt(bridge_out)}**",
                  f"- 外部入金合計：${_fmt(ledger.get('external_in_usd'))}",
                  f"- 同地址內部轉移（perp↔spot accountClassTransfer）："
                  f"**${_fmt(ledger.get('internal_usd'))}**",
                  f"- 無法分類的帳變動：**${_fmt(unknown_usd)}**", ""]
        if ledger.get("by_type"):
            lines += ["| type | 方向 | 筆數 | USD |", "|---|---|---:|---:|"]
            for t, v in sorted(ledger["by_type"].items(), key=lambda kv: -kv[1]["usd"]):
                lines.append(f"| {t} | {v['direction']} | {v['n']} | ${_fmt(v['usd'])} |")
            lines.append("")
        if ledger.get("external_out_rows"):
            lines += ["外轉明細（金額／時間／對手方——對手方以 API 回應的 destination 為準，"
                      "缺欄位則顯示 —）：", "",
                      "| 時間(UTC) | type | USD | 對手方 |", "|---|---|---:|---|"]
            for r in ledger["external_out_rows"]:
                lines.append(f"| {r['time_iso'] or '—'} | {r['type']} | ${_fmt(r['usd'])} "
                             f"| `{r['destination'] or '—'}` |")
        elif bridge_out > 0 or unknown_usd > 0:
            lines.append("查無 withdraw／轉到第三方地址／vault 存入紀錄——但這**不等於沒有"
                         "資金移動**，見下方跨層轉移／無法分類項。")
        if bridge_out > 0:
            lines += ["", f"### 跨層轉移（HyperCore→HyperEVM，同一擁有者）：**${_fmt(bridge_out)}**，"
                          f"{ledger.get('n_bridge_out', len(ledger.get('bridge_out_rows') or []))} 筆",
                      "",
                      "> destination 是 Hyperliquid 的 spot token **系統地址**"
                      "（第一個 byte 0x20、末端 big-endian 編 token index；HYPE 為 0x2222…2222），"
                      "款項進入**同一位擁有者在 HyperEVM 上的同一地址**，不是轉給第三方。",
                      "> 資金仍屬同一擁有者控制，但**已離開 HyperCore 交易帳戶**"
                      "（不再作為永續/現貨交易的抵押品）。",
                      "> 來源：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/"
                      "hyperevm/hypercore-less-than-greater-than-hyperevm-transfers", "",
                      "| 時間(UTC) | USD | token | destination（系統地址） |",
                      "|---|---:|---|---|"]
            for r in ledger.get("bridge_out_rows") or []:
                lines.append(f"| {r['time_iso'] or '—'} | ${_fmt(r['usd'])} "
                             f"| {r.get('token') or '—'} | `{r['destination'] or '—'}` |")
        if unknown_usd > 0:
            n_unknown = ledger.get("n_unknown", len(ledger.get("unknown_rows") or []))
            lines += ["", f"### ⚠️ 有 **${_fmt(unknown_usd)}** 無法分類的帳變動（{n_unknown} 筆）"
                          "——**不可解讀為無資金移動**", "",
                      "> 這些 type 不在已知分類表內，方向未確認；請人工核對 hash/destination "
                      "後再下結論，切勿當成「沒有外轉」。", "",
                      "| 時間(UTC) | type | USD | destination |", "|---|---|---:|---|"]
            for r in ledger.get("unknown_rows") or []:
                lines.append(f"| {r['time_iso'] or '—'} | {r['type']} | ${_fmt(r['usd'])} "
                             f"| `{r['destination'] or '—'}` |")
        if (out_total <= 0 and bridge_out <= 0 and unknown_usd <= 0
                and not ledger.get("external_out_rows")
                and not ledger.get("bridge_out_rows")):
            lines.append(f"**無外轉紀錄** — 近 {config.DIAGNOSTIC_LEDGER_DAYS} 天內查無任何 "
                         "withdraw／轉到其他地址／vault 存入／跨層轉移／無法分類的帳變動。")
        if ledger.get("internal_rows"):
            lines += ["", "同地址內部轉移（perp ↔ spot；這是「換戰場」而非「搬家」的證據）：", "",
                      "| 時間(UTC) | type | USD |", "|---|---|---:|"]
            for r in ledger["internal_rows"]:
                lines.append(f"| {r['time_iso'] or '—'} | {r['type']} | ${_fmt(r['usd'])} |")

    # --- (c) 是否仍在交易 ---
    lines += ["", "## (c) 是否仍在交易？", ""]
    if not (diag.get("queries_ok") or {}).get("userFills"):
        lines.append("❌ userFills 查詢未成功——無法判斷最後成交時間。")
    else:
        lines += [f"- 最後成交時間：**{trading.get('last_fill_iso') or '—'}**"
                  f"（距今 {_fmt(trading.get('days_since_last_fill'))} 天）",
                  f"- 近 7 天成交：**{trading.get('n_fills_7d', 0)}** 筆"
                  f"／近 30 天：**{trading.get('n_fills_30d', 0)}** 筆"
                  f"（回應共 {trading.get('n_fills', 0)} 筆"
                  f"{'，已達 API 截斷上限' if trading.get('truncated') else ''}）",
                  f"- 成交戰場分布：{trading.get('by_venue') or '—'}",
                  f"- 主力幣：{'、'.join(f'{c}×{n}' for c, n in (trading.get('top_coins') or [])[:5]) or '—'}",
                  f"- 目前持倉：{funds.get('n_positions_total', 0)} 個"
                  f"（原生 {funds.get('n_positions_native', 0)}／"
                  f"builder dex {funds.get('n_positions_builder', 0)}）", ""]
        if trading.get("recent_fills"):
            lines += [f"最後 {len(trading['recent_fills'])} 筆成交：", "",
                      "| 時間(UTC) | 幣 | 動作 | px | sz |", "|---|---|---|---:|---:|"]
            for f in trading["recent_fills"][::-1]:
                lines.append(f"| {f['time_iso'] or '—'} | {f['coin'] or '—'} "
                             f"| {f['dir'] or '—'} | {_fmt_px(f['px'])} "
                             f"| {_fmt_qty(f['sz'])} |")

    # --- 裁決 ---
    verdict = diag.get("verdict") or VERDICT_UNKNOWN
    lines += ["", "## 裁決", ""]
    for r in diag.get("verdict_reasons") or []:
        lines.append(f"- {r}")
    lines += ["", f"**裁決：{verdict}**", "",
              "> 純唯讀觀察，不執行任何交易；不構成投資建議。", ""]
    return "\n".join(lines)


def run_diagnostic(address, tracked_dir, date, post_fn=None, now_ms=None,
                   max_dexs=None):
    """全維度診斷探測：查 7 類唯讀 info 端點 → 落地 diagnostic_{date}.json/.md。

    永遠不 raise（呼叫端在 dossier 之後執行，診斷失敗不得影響 dossier）。
    回傳 diag dict；完全無法落地時回 None。
    """
    addr = str(address).strip().lower()
    tracked_dir = Path(tracked_dir)
    max_dexs = config.FETCH_MAX_DEXS if max_dexs is None else max_dexs
    now_ms = time.time() * 1000 if now_ms is None else now_ms
    now_ts = now_ms / 1000.0
    probe = _Probe(post_fn=post_fn)
    queries_ok = {}
    diag = {
        "address": addr, "label": _label_for(addr), "date": date,
        "probed_at": _iso(now_ts),
        "ledger_window_days": config.DIAGNOSTIC_LEDGER_DAYS,
        "queries_ok": queries_ok, "dexs_detected": [], "aborted": False,
    }
    try:
        # 1. perpDexs：先拿真實 dex 名稱清單（不硬編 "xyz"）
        dexs_raw, ok = probe.get("perpDexs", name="perpDexs")
        queries_ok["perpDexs"] = ok
        dex_names = fetch.parse_perp_dexs(
            dexs_raw, config.DEX_NAME_PRIORITY_SUBSTR, max_dexs) if ok else []
        diag["dexs_detected"] = dex_names

        # 2. 原生 clearinghouseState（基準對照）
        native_state, ok = probe.get("clearinghouseState", name="clearinghouseState[native]",
                                     address=addr)
        queries_ok["clearinghouseState_native"] = ok

        # 3. 每個 builder dex 各一次（核心：抵押品/持倉是否在 builder dex）
        by_dex_states, dex_ok_any = {}, False
        for dex in dex_names:
            state, ok = probe.get("clearinghouseState",
                                  name=f"clearinghouseState[{dex}]", address=addr, dex=dex)
            if ok:
                by_dex_states[dex] = state
                dex_ok_any = True
        queries_ok["clearinghouseState_dex"] = dex_ok_any
        diag["dexs_queried"] = sorted(by_dex_states)

        # 4. 現貨餘額（$4M 級資產可能整批在這）
        spot_raw, ok = probe.get("spotClearinghouseState", name="spotClearinghouseState",
                                 address=addr)
        queries_ok["spotClearinghouseState"] = ok
        spot = summarize_spot(spot_raw) if ok else {}

        # 5. 非資金費帳變動（判斷「有無換地址」的關鍵）
        start_ms = int(now_ms - config.DIAGNOSTIC_LEDGER_DAYS * DAY_SEC * 1000)
        ledger_raw, ok = probe.get("userNonFundingLedgerUpdates",
                                   name="userNonFundingLedgerUpdates",
                                   address=addr, start_time_ms=start_ms)
        queries_ok["userNonFundingLedgerUpdates"] = ok
        ledger = classify_ledger_updates(
            ledger_raw, addr, cutoff_ts=start_ms / 1000.0) if ok else {}

        # 6. portfolio（各視窗最新 accountValue，與 clearinghouseState 對照）
        pf_raw, ok = probe.get("portfolio", name="portfolio", address=addr)
        queries_ok["portfolio"] = ok
        diag["portfolio_windows"] = summarize_portfolio_windows(pf_raw) if ok else {}

        # 7. userFills（最後成交時間與幣種 → 是否真的停手）
        fills_raw, ok = probe.get("userFills", name="userFills", address=addr)
        queries_ok["userFills"] = ok
        diag["trading"] = summarize_fills_activity(fills_raw, now_ts) if ok else {}

        diag["funds"] = summarize_funds(native_state, by_dex_states, spot)
        # known=False 代表三個資金面查詢全掛：金額欄位是「查不到」而非「真的 $0」
        diag["funds"]["known"] = bool(queries_ok.get("clearinghouseState_native")
                                      or queries_ok.get("clearinghouseState_dex")
                                      or queries_ok.get("spotClearinghouseState"))
        diag["ledger"] = ledger
        diag["aborted"] = probe.aborted
        verdict, reasons = decide_verdict(diag)
        diag["verdict"] = verdict
        diag["verdict_reasons"] = reasons
    except Exception as exc:  # 診斷永不 crash（dossier 已落地，不能被拖垮）
        diag["error"] = f"{type(exc).__name__}: {exc}"
        diag.setdefault("funds", {})
        diag.setdefault("ledger", {})
        diag.setdefault("trading", {})
        diag["verdict"] = VERDICT_UNKNOWN
        diag["verdict_reasons"] = [f"診斷過程例外：{diag['error']}"]
        print(f"[diag] 例外（已降級為資料不足）：{diag['error']}", file=sys.stderr)

    diag["endpoint_health"] = probe.meta.endpoint_health
    diag["notes"] = probe.meta.notes
    diag["requests_ok"] = probe.meta.requests_ok
    diag["requests_failed"] = probe.meta.requests_failed

    try:
        tracked_dir.mkdir(parents=True, exist_ok=True)
        (tracked_dir / f"diagnostic_{date}.md").write_text(
            build_diagnostic_markdown(diag), encoding="utf-8")
        # 體積控制（CI commit-back 紀律，兩檔合計 <1MB）：ledger <=200 筆、fills 只留
        # 最後 20 筆＋統計、spot 只留非零餘額——皆已在上方 summarize_* 裁切。
        (tracked_dir / f"diagnostic_{date}.json").write_text(
            json.dumps(diag, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"[diag] 診斷檔寫入失敗：{exc}", file=sys.stderr)
        return diag
    print(f"[diag] {addr} verdict={diag.get('verdict')} "
          f"requests ok={diag['requests_ok']} failed={diag['requests_failed']}")
    print(f"[diag] diagnostic: {tracked_dir / f'diagnostic_{date}.md'}")
    return diag


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def load_wallet_raw(snapshot_dir, tracked_dir, addr):
    """優先讀 snapshot 的 wallets/{addr}.json；缺則讀持久化的 latest_raw.json。

    回傳 (wallet_dict, source)；都沒有回 (None, None)。source in {"snapshot","persisted"}。
    """
    snap_path = Path(snapshot_dir) / "wallets" / f"{addr}.json"
    if snap_path.exists():
        try:
            return json.loads(snap_path.read_text(encoding="utf-8")), "snapshot"
        except Exception as exc:
            print(f"[track] snapshot 錢包檔解析失敗（{snap_path}）：{exc}", file=sys.stderr)
    persisted = Path(tracked_dir) / "latest_raw.json"
    if persisted.exists():
        try:
            return json.loads(persisted.read_text(encoding="utf-8")), "persisted"
        except Exception as exc:
            print(f"[track] 持久化錢包檔解析失敗（{persisted}）：{exc}", file=sys.stderr)
    return None, None


def run_track_wallet(address, snapshot_dir, tracked_root, diagnostic=False,
                     diagnostic_post_fn=None, diagnostic_now_ms=None):
    """核心進入點（tests 可直接呼叫）。回傳 dossier dict；缺資料回 None。

    diagnostic=True → dossier 落地**之後**再跑 run_diagnostic（會發網路請求）。
    預設 False，讓離線測試與純分析路徑不碰網路；CLI（main）預設開啟，可用
    --no-diagnostic 關閉。診斷任何失敗都只記錄，不影響已落地的 dossier。
    """
    addr = str(address).strip().lower()
    date = Path(snapshot_dir).name
    tracked_dir = Path(tracked_root) / addr
    tracked_dir.mkdir(parents=True, exist_ok=True)

    wallet, source = load_wallet_raw(snapshot_dir, tracked_dir, addr)
    if wallet is None:
        print(f"[track] {addr} 無可用原始資料（snapshot 與 latest_raw.json 皆缺），略過。")
        return None

    # 持久化：只有讀到當日 snapshot 才覆蓋 latest_raw.json（避免用舊持久檔覆蓋自己）
    if source == "snapshot":
        try:
            (tracked_dir / "latest_raw.json").write_text(
                json.dumps(wallet, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[track] latest_raw.json 寫入失敗：{exc}", file=sys.stderr)

    dossier = compute_dossier(wallet, date)
    new_positions, disappeared, initialized = diff_positions(
        tracked_dir, dossier["open_positions"], date)
    dossier["new_positions"] = new_positions
    dossier["disappeared_positions"] = disappeared
    dossier["initialized"] = initialized
    dossier["raw_source"] = source

    # timeline 先寫（含當日資金分布），再組 md——md 的「資金流向趨勢」節要讀含當日的 timeline
    timeline_path = tracked_dir / "timeline.jsonl"
    rows = append_timeline(timeline_path, timeline_row(dossier, new_positions))
    trend = funds_trend(rows)
    dossier["funds_trend"] = trend

    md_path = tracked_dir / f"dossier_{date}.md"
    json_path = tracked_dir / f"dossier_{date}.json"
    md_path.write_text(build_markdown(dossier, new_positions, disappeared, initialized),
                       encoding="utf-8")
    json_path.write_text(json.dumps(dossier, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    print(f"[track] {addr} class={dossier['classification']} "
          f"pos={dossier['n_open_positions']} new={len(new_positions)} source={source}")
    print(f"[track] dossier: {md_path}")

    if diagnostic:
        # dossier 已完整落地；診斷是加值探測，失敗一律吞掉（含 KeyboardInterrupt 以外的
        # 任何例外），絕不讓它影響 dossier 或讓 exit code 變非 0。
        try:
            diag = run_diagnostic(addr, tracked_dir, date, post_fn=diagnostic_post_fn,
                                  now_ms=diagnostic_now_ms)
            if diag is not None:
                dossier["diagnostic_verdict"] = diag.get("verdict")
        except Exception as exc:
            print(f"[track] 診斷探測例外（dossier 不受影響）：{type(exc).__name__}: {exc}",
                  file=sys.stderr)
    return dossier


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Hyperliquid single-wallet deep tracker (read-only)")
    parser.add_argument("--address", required=True, help="0x 錢包地址")
    parser.add_argument("--snapshot", default=None,
                        help="snapshot 目錄；預設 data/snapshots/{今日UTC}")
    parser.add_argument("--tracked-dir", default=str(BASE_DIR / "data" / "tracked"))
    parser.add_argument("--no-diagnostic", action="store_true",
                        help="關閉 dossier 後的全維度診斷探測（預設開啟，約 15 個唯讀請求）")
    args = parser.parse_args(argv)

    addr = args.address.strip().lower()
    if len(addr) != ADDR_LEN or not addr.startswith("0x"):
        print(f"[track] 地址格式可疑：{args.address}", file=sys.stderr)

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

    dossier = run_track_wallet(addr, snapshot_dir, tracked_root,
                               diagnostic=not args.no_diagnostic)
    if dossier is None and not args.no_diagnostic:
        # 沒有 snapshot/latest_raw（dossier 無法產生）也要能單獨跑診斷——診斷資料
        # 全部來自即時 info API，不依賴 snapshot。
        date = Path(snapshot_dir).name
        run_diagnostic(addr, tracked_root / addr, date)
    return 0  # 唯讀觀察器：永遠 exit 0，讓 workflow 後續步驟能繼續


if __name__ == "__main__":
    sys.exit(main())
