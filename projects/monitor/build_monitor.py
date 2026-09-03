#!/usr/bin/env python3
"""聰明錢系統監控 — 聚合建置腳本。

讀取各管線的公開產出（hyper-observer / hyper-shadow / poly-observer /
poly-shadow / us-funnel / tw-funnel），聚合成單一 data dict，嵌入
template.html 的 <script id="monitor-data" type="application/json">，
輸出完整自包含的 docs/monitor/index.html（無外部 fetch/CDN 依賴）。

每個數據源都 try/except：缺失 → available:False → 頁面顯示「建置中」佔位。
只使用 Python 標準函式庫。
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

HL_ADDR = "0x8bae3527e5a33fa0cf184f37bc112d071463ab6d"
POLY_11M = "0x2005d16a84ceefa912d4e380cd32e7ff827875ea"

MAX_CANDIDATES = 20      # 候選表最多列出筆數（控制產物大小）
MAX_POSITIONS = 40       # 前瞻表現表最多列出筆數
MAX_VENUES = 24          # 資金分布表最多列出場所數（控制產物大小）
SIZE_LIMIT = 1_000_000   # 產物大小哨兵（bytes）

# HyperCore → HyperEVM 跨層轉移的系統地址前綴：0x20…00 + token index。
# 送到這類地址＝資金跨層到「同一擁有者」的 HyperEVM 地址，不是轉給第三方。
CROSS_LAYER_PREFIX = "0x2000000000000000000000000000000000"

NATIVE_KEYS = ("native", "", "perp", "hyperliquid", "none")  # by_dex 裡代表原生的鍵
VENUE_NATIVE = "原生"
VENUE_SPOT = "現貨"


# ── 小工具 ─────────────────────────────────────────────────────────

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def latest_file(pattern):
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def clean(v):
    """NaN/Inf → None（json.dumps allow_nan=False 會炸）。"""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def fnum(v):
    """任何東西 → float 或 None（不炸）。"""
    if isinstance(v, bool) or v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if (math.isnan(f) or math.isinf(f)) else f


def fint(v):
    f = fnum(v)
    return None if f is None else int(f)


def share_of(part, total):
    """占比，分母 0/None/缺失 一律回 None（防呆，絕不 ZeroDivisionError）。"""
    p, t = fnum(part), fnum(total)
    if p is None or t is None or t == 0:
        return None
    return p / t


# ── 多場所（multi-venue）視圖 ───────────────────────────────────────
# HIP-3 builder dex 與現貨都掛在**同一個錢包地址**下（不是另一個錢包）。
# 原生 clearinghouseState（不帶 dex）對 builder 市場全盲 → 只看聚合持倉會誤判「無持倉」。

def position_venue(p):
    """由 position dict 推導所屬場所短標籤。"""
    dex = p.get("dex")
    if dex not in (None, "", "native"):
        return str(dex)
    coin = str(p.get("coin") or "")
    if coin.startswith("@"):          # @166 之類＝現貨市場代號
        return VENUE_SPOT
    if ":" in coin:                   # xyz:META＝builder dex 前綴
        return coin.split(":", 1)[0] or VENUE_NATIVE
    return VENUE_NATIVE


def clean_position(p):
    out = {k: clean(p.get(k)) for k in (
        "coin", "side", "leverage_value", "leverage_type",
        "position_value", "entry_px", "unrealized_pnl")}
    out["venue"] = position_venue(p)
    return out


def latest_diagnostic(tracked):
    """目錄下最新一份 diagnostic_*.json（週期性產物，不保證每日）→ (dict, date)。"""
    path = latest_file(os.path.join(tracked, "diagnostic_*.json"))
    if not path:
        return None, None
    try:
        diag = load_json(path)
    except Exception:
        return None, None
    date = diag.get("date")
    if not date:
        base = os.path.basename(path)
        date = base[len("diagnostic_"):-len(".json")] or None
    return diag, date


def _is_cross_layer(dest):
    """destination 是否為 HyperCore→HyperEVM 系統地址（同一擁有者跨層）。"""
    return isinstance(dest, str) and dest.lower().startswith(CROSS_LAYER_PREFIX)


def _by_dex_value(v):
    """by_dex 的值可能是純數字，也可能是 {account_value:…, n_positions:…}。"""
    if isinstance(v, dict):
        return (fnum(v.get("account_value")),
                fint(v.get("n_positions")),
                fnum(v.get("position_value")))
    return fnum(v), None, None


def build_venues(metrics, diag, diag_date):
    """組出「資金分布（多場所）」區塊。任何欄位缺失 → 優雅降級，不炸。

    來源優先序：dossier 的 account_value_by_dex（每日產物）→ diagnostic 的
    funds（週期性產物，額外提供現貨與名目）。兩者都缺 → available:False。
    """
    out = {"available": False, "rows": [], "zero_venues": [],
           "diagnostic_date": None, "sources": []}
    metrics = metrics or {}
    funds = (diag or {}).get("funds") or {}

    # venue_id → row（native/spot 用固定 id，builder dex 用 dex 名）
    acc = {}

    def row(vid, kind, name):
        r = acc.get(vid)
        if r is None:
            r = acc[vid] = {"id": vid, "kind": kind, "name": name,
                            "account_value": None, "n_positions": None,
                            "notional": None, "share": None}
        return r

    # ① dossier: account_value_by_dex / account_value_native / dexs_with_positions
    by_dex = metrics.get("account_value_by_dex")
    if isinstance(by_dex, dict) and by_dex:
        out["sources"].append("dossier")
        for k, v in by_dex.items():
            key = str(k or "").strip()
            is_native = key.lower() in NATIVE_KEYS
            vid = "native" if is_native else key
            r = row(vid, "native" if is_native else "builder",
                    "原生永續 dex" if is_native else "builder dex " + key)
            av, npos, ntl = _by_dex_value(v)
            r["account_value"] = av
            if npos is not None:
                r["n_positions"] = npos
            if ntl is not None:
                r["notional"] = ntl
    av_native = fnum(metrics.get("account_value_native"))
    if av_native is not None:
        r = row("native", "native", "原生永續 dex")
        if r["account_value"] is None:
            r["account_value"] = av_native
        out["sources"].append("dossier")
    # 現貨：優先用 dossier 的每日抓取值（classify.spot_value_usd），
    # 比週期性 diagnostic 新；下方 ② 只在此處為 None 時才回填。
    spot_daily = fnum(metrics.get("spot_value_usd"))
    if spot_daily is not None:
        r = row("spot", "spot", "現貨 spot")
        r["account_value"] = spot_daily
        toks = metrics.get("spot_tokens")
        if isinstance(toks, list) and r["n_positions"] is None:
            r["n_positions"] = len(toks)
        if any((t or {}).get("estimated") for t in (toks or []) if isinstance(t, dict)):
            out["spot_estimated"] = True
        out["sources"].append("dossier")
    n_native = fint(metrics.get("n_open_positions_native"))
    if n_native is not None and "native" in acc and acc["native"]["n_positions"] is None:
        acc["native"]["n_positions"] = n_native
    for d in (metrics.get("dexs_with_positions") or []):
        key = str(d or "").strip()
        if not key:
            continue
        is_native = key.lower() in NATIVE_KEYS
        row("native" if is_native else key, "native" if is_native else "builder",
            "原生永續 dex" if is_native else "builder dex " + key)

    # ② diagnostic: funds.native / funds.builder_dex / funds.spot（含名目與現貨）
    if funds:
        out["sources"].append("diagnostic")
        out["diagnostic_date"] = diag_date
        nat = funds.get("native") or {}
        if nat:
            r = row("native", "native", "原生永續 dex")
            if r["account_value"] is None:
                r["account_value"] = fnum(nat.get("account_value"))
            if r["n_positions"] is None:
                r["n_positions"] = fint(nat.get("n_positions"))
            if r["notional"] is None:
                r["notional"] = fnum(nat.get("position_value"))
        for name, v in (funds.get("builder_dex") or {}).items():
            key = str(name or "").strip()
            if not key:
                continue
            r = row(key, "builder", "builder dex " + key)
            av, npos, ntl = _by_dex_value(v)
            if r["account_value"] is None:
                r["account_value"] = av
            if r["n_positions"] is None:
                r["n_positions"] = npos
            if r["notional"] is None:
                r["notional"] = ntl
        spot = funds.get("spot") or {}
        spot_usd = fnum(funds.get("spot_usd"))
        if spot_usd is None:
            spot_usd = fnum(spot.get("usd_total_est"))
        if spot_usd is not None or spot:
            r = row("spot", "spot", "現貨 spot")
            # 每日 dossier 值優先——診斷是週期性產物，不可覆蓋較新的每日值
            if r["account_value"] is None:
                r["account_value"] = spot_usd
            if r["n_positions"] is None:
                r["n_positions"] = fint(spot.get("n_nonzero"))
            r["notional"] = None      # 現貨無「名目」概念
            if spot.get("estimated"):
                out["spot_estimated"] = True

    if not acc:
        return out

    # ③ 合計與占比（分母 0/缺失 → share=None，前端顯示「—」）
    # 合計一律用「表內各列之和」，保證表格自洽（占比加總＝100%）；
    # diagnostic 的 total_usd 只當交叉檢查（來源日期可能與 dossier 不同）。
    vals = [r["account_value"] for r in acc.values() if r["account_value"] is not None]
    total = sum(vals) if vals else None
    out["total_usd_diagnostic"] = clean(fnum(funds.get("total_usd")))

    def sort_key(r):
        kind_order = {"native": 0, "builder": 1, "spot": 2}[r["kind"]]
        return (kind_order, -(r["account_value"] or 0), r["id"])

    rows = sorted(acc.values(), key=sort_key)
    for r in rows:
        r["share"] = share_of(r["account_value"], total)

    # 零餘額 builder dex 併成一行說明（查過但沒錢），主表只留有訊號的場所
    def is_signal(r):
        return (r["kind"] != "builder"
                or (r["account_value"] or 0) != 0
                or (r["n_positions"] or 0) != 0)

    out["zero_venues"] = [r["id"] for r in rows if not is_signal(r)]
    out["rows"] = [r for r in rows if is_signal(r)][:MAX_VENUES]

    native_usd = (acc.get("native") or {}).get("account_value")
    bv = [r["account_value"] for r in rows
          if r["kind"] == "builder" and r["account_value"] is not None]
    builder_usd = sum(bv) if bv else None
    spot_usd = (acc.get("spot") or {}).get("account_value")
    nv = [v for v in (builder_usd, spot_usd) if v is not None]
    non_native = sum(nv) if nv else None
    non_native_share = share_of(non_native, total)

    nz = [r["n_positions"] for r in rows
          if r["kind"] != "spot" and r["n_positions"] is not None]
    n_total = sum(nz) if nz else None
    ntl_total = [r["notional"] for r in rows if r["notional"] is not None]

    out.update({
        "available": True,
        "sources": sorted(set(out["sources"])),
        "total_usd": clean(total),
        "native_usd": clean(native_usd),
        "builder_usd": clean(builder_usd),
        "spot_usd": clean(spot_usd),
        "non_native_usd": clean(non_native),
        "non_native_share": clean(non_native_share),
        "n_positions_total": n_total,
        "notional_total": clean(sum(ntl_total)) if ntl_total else None,
        "n_builder_dexs": sum(1 for r in rows if r["kind"] == "builder"),
    })

    # 非原生占比高 → 明確告訴使用者「主要活動不在原生 dex」
    if non_native_share is not None and non_native_share >= 0.5:
        out["non_native_alert"] = (
            "主要活動不在原生 dex：非原生資金（builder dex ＋ 現貨）"
            f"{_usd(non_native)} 占總資產 {_usd(total)} 的 "
            f"{non_native_share * 100:.1f}%。"
            "只查原生永續 dex（不帶 dex 參數的 clearinghouseState）會看成「無持倉、$0 淨值」。"
        )
    return out


def _usd(v):
    return "—" if v is None else f"${v:,.0f}"


def build_flows(diag, diag_date):
    """資金流動：跨層轉出（同一擁有者 HyperCore→HyperEVM）／真外轉／最後成交距今。"""
    out = {"available": False}
    if not diag:
        return out
    ledger = diag.get("ledger") or {}
    trading = diag.get("trading") or {}
    if not ledger and not trading:
        return out

    rows = ledger.get("rows") or []
    cross_n = cross_usd = 0
    ext_n = ext_usd = 0.0
    for r in rows:
        if not isinstance(r, dict):
            continue
        usd = fnum(r.get("usd")) or 0.0
        if _is_cross_layer(r.get("destination")):
            cross_n += 1
            cross_usd += usd
        elif str(r.get("type") or "").lower().startswith("send"):
            ext_n += 1
            ext_usd += usd

    # hyper-observer 若日後補上明確欄位就優先採用（前向相容）
    cross_usd = fnum(ledger.get("cross_layer_out_usd"))if ledger.get(
        "cross_layer_out_usd") is not None else cross_usd
    cross_n = fint(ledger.get("cross_layer_n")) if ledger.get(
        "cross_layer_n") is not None else cross_n
    declared_ext = fnum(ledger.get("external_out_usd"))
    if declared_ext is not None:
        ext_usd = max(ext_usd, declared_ext) if ext_usd else declared_ext

    by_type = ledger.get("by_type") or {}
    out = {
        "available": True,
        "date": diag_date,
        "window_days": fint(diag.get("ledger_window_days")),
        "cross_layer_usd": clean(cross_usd),
        "cross_layer_n": int(cross_n or 0),
        "external_out_usd": clean(ext_usd),
        "external_out_n": int(ext_n or 0),
        "unknown_usd": clean(ledger.get("unknown_usd")),
        "internal_usd": clean(ledger.get("internal_usd")),
        "vault_out_usd": clean(ledger.get("vault_out_usd")),
        "ledger_n": fint(ledger.get("n_total")),
        "by_type": {str(k): fint((v or {}).get("n")) for k, v in by_type.items()
                    if isinstance(v, dict)},
        "days_since_last_fill": clean(fnum(trading.get("days_since_last_fill"))),
        "last_fill_iso": trading.get("last_fill_iso"),
        "n_fills_7d": fint(trading.get("n_fills_7d")),
        "fills_by_venue": {str(k): fint(v)
                           for k, v in (trading.get("by_venue") or {}).items()},
        "verdict": diag.get("verdict"),
    }
    fv = out["fills_by_venue"]
    tot = sum(v for v in fv.values() if v)
    nat = fv.get("native") or 0
    out["fills_total"] = tot or None
    out["fills_non_native"] = (tot - nat) if tot else None
    out["fills_non_native_share"] = share_of(out["fills_non_native"], tot)
    return out


# ── §1 HL 持續贏家 ─────────────────────────────────────────────────

def collect_hl(root):
    tracked = os.path.join(root, "projects", "hyper-observer", "data", "tracked", HL_ADDR)
    out = {"available": False, "placeholder": "HL 追蹤管線建置中——dossier 尚未產出。"}
    try:
        dossier = load_json(latest_file(os.path.join(tracked, "dossier_*.json")))
    except Exception:
        return out

    m = dossier.get("metrics", {}) or {}
    out = {
        "available": True,
        "address": dossier.get("address", HL_ADDR),
        "label": dossier.get("label"),
        "classification": dossier.get("classification"),
        "snapshot_date": dossier.get("snapshot_date"),
        "position_value": clean(dossier.get("position_value")),
        "unrealized_pnl": clean(dossier.get("unrealized_pnl")),
        "metrics": {k: clean(m.get(k)) for k in (
            "total_pnl", "peak_pnl", "max_drawdown_pct", "current_drawdown_pct",
            "profit_factor", "realized_win_rate", "avg_win", "avg_loss",
            "avg_hold_hours", "n_events_last_30d", "median_event_notional",
            "account_value", "n_fills_truncated", "positive_month_ratio",
            "current_max_leverage", "has_extreme_leverage", "n_liquidations",
            "span_days",
        )},
        "monthly_pnl": {k: clean(v) for k, v in (m.get("monthly_pnl") or {}).items()},
        "positions": [clean_position(p) for p in (dossier.get("open_positions") or [])],
        "positions_source": "dossier",
        "positions_date": dossier.get("snapshot_date"),
    }
    months = sorted(out["monthly_pnl"])
    out["monthly_range"] = f"{months[0]} ～ {months[-1]}" if months else ""

    # 多場所視圖（同一地址的原生永續／builder dex／現貨）
    diag, diag_date = latest_diagnostic(tracked)
    out["venues"] = build_venues(m, diag, diag_date)
    out["flows"] = build_flows(diag, diag_date)

    # dossier 的 open_positions 只涵蓋原生永續 dex；若它是空的而診斷抓到
    # builder dex 部位，改用診斷的部位清單（並標明來源與資料日期）。
    if not out["positions"]:
        dpos = ((diag or {}).get("funds") or {}).get("positions") or []
        if dpos:
            out["positions"] = [clean_position(p) for p in dpos[:MAX_POSITIONS]]
            out["positions_source"] = "diagnostic"
            out["positions_date"] = diag_date
    # 持倉表自身的名目/未實現合計（dossier 的 position_value/unrealized_pnl
    # 只涵蓋原生永續 dex，與多場所持倉不可混用）
    def _psum(key):
        vals = [fnum(p.get(key)) for p in out["positions"]]
        vals = [v for v in vals if v is not None]
        return clean(sum(vals)) if vals else None
    out["positions_notional"] = _psum("position_value")
    out["positions_unrealized_pnl"] = _psum("unrealized_pnl")

    # timeline：前瞻追蹤的觀測日數
    timeline_days, timeline_rows = set(), 0
    try:
        with open(os.path.join(tracked, "timeline.jsonl"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                timeline_rows += 1
                try:
                    timeline_days.add(json.loads(line).get("date"))
                except Exception:
                    pass
    except Exception:
        pass
    out["timeline_days"] = len(timeline_days)
    out["timeline_rows"] = timeline_rows

    # 影子深度實測
    out["shadow"] = collect_hl_shadow(root)
    # 掃描裁決
    out["scan"] = collect_hl_scan(root)
    # 部位回合聚合（依場所勝率/賠率，每日成交歷史累積的產物）
    out["fills_history"] = collect_hl_fills_history(root)
    # 證據閘門記分板
    out["gates"] = build_gates(out)
    return out


def collect_hl_shadow(root):
    sdir = os.path.join(root, "projects", "hyper-observer", "data", "shadow", HL_ADDR)
    try:
        summary = load_json(latest_file(os.path.join(sdir, "summary_*.json")))
        sess = summary["sessions"][-1]
        rt = sess.get("roundtrip_1k_pct") or {}
        nf = sess.get("new_fills") or {}
        return {
            "available": True,
            "date": sess.get("date"),
            "started_utc": sess.get("started_utc"),
            "main_market": rt.get("coin") or sess.get("main_market"),
            "roundtrip_1k_pct": clean(rt.get("value")),
            "polls": clean(sess.get("polls")),
            "n_targets": len(sess.get("targets") or []),
            "new_fills_detected": clean((nf.get("n_detected"))),
            "degradation_n": clean(((nf.get("copy_1k_degradation_pct") or {}).get("n"))),
        }
    except Exception:
        return {"available": False, "placeholder": "影子採樣尚未產出。"}


def collect_hl_scan(root):
    rdir = os.path.join(root, "projects", "hyper-observer", "data", "reports")
    try:
        scan = load_json(latest_file(os.path.join(rdir, "scan_verification_*.json")))
        return {
            "available": True,
            "date": scan.get("date"),
            "generated_at": scan.get("generated_at"),
            "verdict": scan.get("verdict"),
            "followable_count": clean(scan.get("followable_count")),
            "classification_counts": scan.get("classification_counts") or {},
        }
    except Exception:
        return {"available": False}


# ── 部位回合聚合（fills_history.py 每日累積，突破 userFills 單次 2000 筆上限）──
# 逐筆算勝率會被「一次平倉拆成幾十筆部分成交」污染成假數字（同回合的部分成交
# 符號全同）；fills_history_stats.json 已用 aggregate_round_trips 的 flat→flat
# 真實回合算好勝率/賠率，這裡只是原樣揭露，不重算。依 dex 前綴分組（"native"＝
# 原生永續），讓使用者一眼看出「哪個場所才是他真正的優勢」。

def _round_trip_group(s):
    if not isinstance(s, dict):
        return None
    return {k: clean(s.get(k)) for k in (
        "n_round_trips", "win_rate", "net_pnl", "profit_factor", "payoff_ratio",
        "avg_win", "avg_loss", "best_win", "worst_loss", "worst_loss_share_of_profit",
        "n_open_positions", "open_positions_realized_pnl", "carry_in_pnl",
    )}


def collect_hl_fills_history(root):
    path = os.path.join(root, "projects", "hyper-observer", "data", "tracked",
                        HL_ADDR, "fills_history_stats.json")
    try:
        s = load_json(path)
    except Exception:
        return {"available": False,
               "placeholder": "成交歷史累積尚未產出（fills_history.py 排程每日 23:15 UTC 執行）。"}
    by_dex = {dex: g for dex, g in
              ((k, _round_trip_group(v)) for k, v in (s.get("by_dex") or {}).items())
              if g is not None}
    return {
        "available": True,
        "generated_at": s.get("generated_at"),
        "n_fills_total": fint(s.get("n_fills_total")),
        "span_days": clean(s.get("span_days")),
        "earliest_fill": s.get("earliest_fill"),
        "latest_fill": s.get("latest_fill"),
        "is_high_frequency": bool(s.get("is_high_frequency")),
        "retention_days": fint(s.get("retention_days")),
        "overall": _round_trip_group(s.get("overall")),
        "by_dex": by_dex,
    }


def build_gates(hl):
    """證據閘門記分板：pass=✅ / pending=⏳ / fail=❌，附一行證據細節。"""
    m = hl["metrics"]
    gates = []

    def gate(name, status, detail):
        gates.append({"name": name, "status": status, "detail": detail})

    def pct(v):
        return "—" if v is None else f"{v * 100:.1f}%"

    ok = hl.get("classification") == "consistent_winner"
    gate("持續贏家", "pass" if ok else "fail",
         f"分類 {hl.get('classification')}・正月比率 {pct(m.get('positive_month_ratio'))}"
         f"・最大回撤 {pct(m.get('max_drawdown_pct'))}")

    ev = m.get("n_events_last_30d")
    gate("頻率", "pass" if (ev is not None and ev > 0) else "pending",
         f"30 日事件 {ev if ev is not None else '—'} 次"
         f"・中位名目 ${(m.get('median_event_notional') or 0):,.0f}")

    npos = len(hl.get("positions") or [])
    hold = m.get("avg_hold_hours")
    gate("持倉", "pass" if npos > 0 else "pending",
         f"目前 {npos} 檔・平均持有 {hold:.0f}h" if hold is not None else f"目前 {npos} 檔")

    lev = m.get("current_max_leverage")
    lev_ok = lev is not None and lev <= 20 and not m.get("has_extreme_leverage")
    gate("槓桿", "pass" if lev_ok else ("fail" if lev is not None else "unknown"),
         f"目前 {lev}x・清算 {m.get('n_liquidations', '—')} 次")

    sh = hl.get("shadow") or {}
    if sh.get("available") and sh.get("roundtrip_1k_pct") is not None:
        gate("深度", "pass",
             f"主力 {sh.get('main_market')} $1k 往返 {sh['roundtrip_1k_pct']}%")
    else:
        gate("深度", "pending", "影子深度樣本缺失——待下一班採樣")

    dn = sh.get("degradation_n") or 0
    gate("劣化", "pass" if dn >= 20 else "pending",
         f"實測劣化樣本 {dn} 筆（需 ≥20）——多班累積中" if dn < 20
         else f"實測劣化樣本 {dn} 筆")

    days = hl.get("timeline_days") or 0
    gate("前瞻", "pass" if days >= 14 else "pending",
         f"timeline 觀測 {days} 日（需 ≥14）——前瞻追蹤剛啟動" if days < 14
         else f"timeline 觀測 {days} 日")
    return gates


# ── Polymarket 一行狀態 ────────────────────────────────────────────

def collect_poly(root):
    base = os.path.join(root, "projects", "poly-observer", "data")
    out = {"available": False, "placeholder": "Polymarket 數據缺失。"}
    try:
        dossier = load_json(latest_file(
            os.path.join(base, "tracked", POLY_11M, "dossier_*.json")))
        m = dossier.get("metrics", {}) or {}
        out = {
            "available": True,
            "label": dossier.get("label"),
            "total_pnl": clean(m.get("total_pnl")),
            "snapshot_date": dossier.get("snapshot_date"),
            "reason": (f"月 {m.get('trades_per_month', 0):,.0f} 筆高頻連發、"
                       "幽靈利潤偏誤＋逆選擇，跟單損益無法可靠重建"),
        }
    except Exception:
        return out

    try:
        wl = load_json(os.path.join(base, "watchlist.json"))
        out["watchlist_total"] = len(wl)
        out["watchlist_active"] = sum(1 for v in wl.values() if v.get("active"))
    except Exception:
        out["watchlist_total"] = out["watchlist_active"] = None

    try:
        summary = load_json(latest_file(
            os.path.join(base, "shadow", POLY_11M, "summary_*.json")))
        stats = summary["sessions"][-1]["stats"]
        out["lag_median"] = clean(stats["detect_lag_sec"]["median"])
        out["lag_p90"] = clean(stats["detect_lag_sec"]["p90"])
        out["fillable_ratio"] = clean(stats.get("fillable_at_best_ratio"))
    except Exception:
        out["lag_median"] = out["lag_p90"] = out["fillable_ratio"] = None
    return out


# ── 美股/台股漏斗 ──────────────────────────────────────────────────

def clean_risk(r):
    """候選的 risk 欄（us-funnel 風險分級）→ 淨化 dict；舊數據無此欄 → None（前端顯示—）。"""
    if not isinstance(r, dict):
        return None
    return {k: clean(r.get(k)) for k in (
        "level", "data_gap", "beta", "mcap_usd", "mcap_band", "beta_band")}


def collect_funnel(root, project):
    base = os.path.join(root, "projects", project, "data")
    out = {"available": False,
           "placeholder": "管線建置中——首次掃描落地後本區塊自動出現。"}
    try:
        cand = load_json(os.path.join(base, "candidates_latest.json"))
    except Exception:
        return out

    fs = cand.get("funnel_stats") or {}
    out = {
        "available": True,
        "generated_at": cand.get("generated_at"),
        "funnel_stats": {k: clean(fs.get(k)) for k in (
            "raw_filings", "qualified_events", "post_veto", "final_candidates")},
        "candidates": [
            dict({k: clean(c.get(k)) for k in (
                "ticker", "company", "score", "first_filing_date", "entry_price_ref")},
                 risk=clean_risk(c.get("risk")))
            for c in (cand.get("candidates") or [])[:MAX_CANDIDATES]
        ],
    }
    try:
        perf = load_json(os.path.join(base, "performance_tracking.json"))
        out["performance"] = {
            "updated_at": perf.get("updated_at"),
            "positions": [
                {
                    "ticker": clean(p.get("ticker")),
                    "signal_date": clean(p.get("signal_date")),
                    "entry_price_ref": clean(p.get("entry_price_ref")),
                    "current_price": clean(p.get("current_price")),
                    "status": clean(p.get("status")),
                    "returns": {k: clean((p.get("returns") or {}).get(k))
                                for k in ("1w", "1m", "3m", "6m", "12m")},
                }
                for p in (perf.get("positions") or [])[:MAX_POSITIONS]
            ],
        }
    except Exception:
        out["performance"] = {"updated_at": None, "positions": []}

    try:
        out["meta"] = load_json(os.path.join(base, "meta_latest.json"))
    except Exception:
        out["meta"] = None
    return out


# ── §4 系統狀態板 ──────────────────────────────────────────────────

def _dossier_date(pattern):
    try:
        return load_json(latest_file(pattern)).get("snapshot_date")
    except Exception:
        return None


def _shadow_started(pattern):
    try:
        return load_json(latest_file(pattern))["sessions"][-1].get("started_utc")
    except Exception:
        return None


def collect_pipelines(root, hl, poly, us, tw, generated_at):
    """各管線「最後數據時間戳」。precision: datetime|date（date 只到日）。
    狀態燈由前端以觀看當下時間計算（頁面停更時 monitor-build 自己會轉紅）。"""

    def entry(pid, name, desc, schedule, ts, precision="datetime"):
        return {"id": pid, "name": name, "desc": desc, "schedule": schedule,
                "ts": ts, "precision": precision if ts else None}

    poly_tracked = os.path.join(root, "projects", "poly-observer", "data", "tracked")
    poly_dates = [d for d in (
        _dossier_date(os.path.join(poly_tracked, a, "dossier_*.json"))
        for a in (os.listdir(poly_tracked) if os.path.isdir(poly_tracked) else [])
    ) if d]

    return [
        entry("poly-observer", "poly-observer", "Polymarket 錢包每日快照＋分類",
              "每日 UTC 22:30（台北 06:30）",
              max(poly_dates) if poly_dates else None, "date"),
        entry("poly-shadow", "poly-shadow", "Polymarket 跟單延遲/深度實測（唯讀）",
              "每日三班 UTC 00:00 / 15:00 / 23:30",
              _shadow_started(os.path.join(
                  root, "projects", "poly-observer", "data", "shadow", POLY_11M,
                  "summary_*.json"))),
        entry("hyper-observer", "hyper-observer", "Hyperliquid 錢包每日快照＋全市場掃描",
              "每日 UTC 22:45（台北 06:45）",
              hl.get("snapshot_date") if hl.get("available") else None, "date"),
        entry("hyper-shadow", "hyper-shadow", "Hyperliquid 深度/劣化實測（唯讀）",
              "每日三班 UTC 02:30 / 10:30 / 18:30",
              (hl.get("shadow") or {}).get("started_utc")),
        entry("us-funnel", "us-funnel", "美股 Form 4 三層漏斗掃描",
              "每日 UTC 03:30（美東申報日後）",
              us.get("generated_at") if us.get("available") else None),
        entry("tw-funnel", "tw-funnel", "台股投信×營收三層漏斗掃描",
              "每日台北 17:45＋每月 10/11 加掃",
              tw.get("generated_at") if tw.get("available") else None),
        entry("monitor-build", "monitor-build", "本頁聚合建置",
              "每日兩班 UTC 04:15 / 10:15（美股班後/台股班後）",
              generated_at),
    ]


# ── 組裝與輸出 ─────────────────────────────────────────────────────

def build_data(root):
    generated_at = now_utc().isoformat(timespec="seconds")
    hl = collect_hl(root)
    poly = collect_poly(root)
    us = collect_funnel(root, "us-funnel")
    tw = collect_funnel(root, "tw-funnel")
    return {
        "generated_at": generated_at,
        "hl": hl,
        "poly": poly,
        "us_funnel": us,
        "tw_funnel": tw,
        "pipelines": collect_pipelines(root, hl, poly, us, tw, generated_at),
    }


def render(root, out_path, template_path=None):
    template_path = template_path or os.path.join(HERE, "template.html")
    with open(template_path, encoding="utf-8") as f:
        template = f.read()
    data = build_data(root)
    # </ 逃逸，避免 JSON 內容提前關閉 <script> 標籤
    blob = json.dumps(data, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).replace("</", "<\\/")
    html = template.replace("__MONITOR_DATA_JSON__", blob)
    if "__MONITOR_DATA_JSON__" in html:
        raise RuntimeError("模板佔位符替換失敗")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return data, len(html.encode("utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="聰明錢系統監控頁聚合建置")
    ap.add_argument("--repo-root", default=DEFAULT_ROOT)
    ap.add_argument("--out", default=None,
                    help="輸出路徑（預設 <repo-root>/docs/monitor/index.html）")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.repo_root)
    out_path = args.out or os.path.join(root, "docs", "monitor", "index.html")

    data, size = render(root, out_path)
    avail = {k: bool(data[k].get("available")) for k in
             ("hl", "poly", "us_funnel", "tw_funnel")}
    print(f"寫出 {out_path}（{size:,} bytes）")
    print(f"數據源可用性：{avail}")
    if size >= SIZE_LIMIT:
        print(f"錯誤：產物 {size:,} bytes >= {SIZE_LIMIT:,}（CI 哨兵上限）",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
