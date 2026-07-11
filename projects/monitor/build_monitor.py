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
SIZE_LIMIT = 1_000_000   # 產物大小哨兵（bytes）


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
        "positions": [
            {k: clean(p.get(k)) for k in (
                "coin", "side", "leverage_value", "leverage_type",
                "position_value", "entry_px", "unrealized_pnl")}
            for p in (dossier.get("open_positions") or [])
        ],
    }
    months = sorted(out["monthly_pnl"])
    out["monthly_range"] = f"{months[0]} ～ {months[-1]}" if months else ""

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
