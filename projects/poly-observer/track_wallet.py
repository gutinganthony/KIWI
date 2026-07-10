#!/usr/bin/env python3
"""poly-observer track_wallet：單錢包深度追蹤器（唯讀 dossier）。

用法（在 projects/poly-observer 下）：
    python3 track_wallet.py --address 0x.. [--snapshot data/snapshots/YYYY-MM-DD]

像追蹤一個交易員一樣持續盯一個錢包：讀當日 snapshot 的原始資料，
算出身分/持倉/績效/交易輪廓，並與上次快照比對偵測「新建倉/平倉」，
逐日落地 dossier（人讀 md ＋機器 json）與 timeline.jsonl。

持久化：把該錢包的原始 snapshot 複製到 data/tracked/{addr}/latest_raw.json，
讓 tracked 錢包的原始資料在每日 prune data/snapshots/*/wallets 後仍存在，供 simulate_copy 用。

純唯讀分析：所有指標/分類邏輯重用 verify_smart_money 的 parse/compute 函式（import，非複製）。
不含任何下單、私鑰、簽章、錢包連線程式碼；不構成投資建議。
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


# ---------------------------------------------------------------------------
# 持倉解析（防禦性欄位多形；positions 端點回應形狀不固定）
# ---------------------------------------------------------------------------

def parse_positions(raw):
    """positions 端點原始回應 → 正規化未平倉部位清單。

    回傳 [{title, slug, outcome, size, current_value, avg_price, cash_pnl, condition_id}]。
    欄位缺失一律回 None，不臆造。
    """
    if raw is None:
        return []
    if isinstance(raw, dict):
        for key in ("data", "positions", "results"):
            if isinstance(raw.get(key), list):
                raw = raw[key]
                break
        else:
            return []
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        def pick(keys, cast=None):
            for k in keys:
                if k in item and item[k] is not None:
                    val = item[k]
                    if cast is None:
                        return val
                    conv = vsm._to_float(val)
                    if conv is not None:
                        return conv
            return None

        out.append({
            "title": str(pick(("title", "question", "market", "eventTitle")) or ""),
            "slug": str(pick(("slug", "eventSlug", "marketSlug")) or ""),
            "outcome": str(pick(("outcome", "outcomeName", "side", "position")) or ""),
            "size": pick(("size", "shares", "quantity"), cast=float),
            "current_value": pick(("currentValue", "value", "currentVal",
                                   "positionValue"), cast=float),
            "avg_price": pick(("avgPrice", "averagePrice", "avg_price",
                               "entryPrice"), cast=float),
            "cash_pnl": pick(("cashPnl", "cashPnL", "pnl", "unrealizedPnl"), cast=float),
            "condition_id": str(pick(("conditionId", "condition_id", "asset",
                                      "tokenId")) or ""),
        })
    return out


def _position_key(p):
    """持倉去重/比對用的穩定鍵：優先 slug，退回 condition_id。"""
    return p.get("slug") or p.get("condition_id") or ""


def _label_for(addr):
    for w in config.TRACKED_WALLETS:
        if str(w.get("address", "")).lower() == addr.lower():
            return w.get("label", "")
    return ""


# ---------------------------------------------------------------------------
# dossier 計算
# ---------------------------------------------------------------------------

def compute_dossier(wallet, date):
    """由單錢包原始 snapshot 算出 dossier（不含新建倉 delta，那需前次狀態）。"""
    addr = str(wallet.get("address", "")).lower()
    metrics = vsm.compute_metrics(wallet, date)
    classification, reasons = vsm.classify(metrics)

    positions = parse_positions(wallet.get("positions"))
    position_value = round(sum(p["current_value"] for p in positions
                               if p["current_value"] is not None), 2)

    events = vsm.parse_activity_events(wallet.get("activity"))
    timeline = []
    for e in events[-20:]:
        timeline.append({
            "time": (datetime.fromtimestamp(e["ts"], tz=timezone.utc).isoformat()
                     if e["ts"] is not None else None),
            "title": e["title"],
            "side": e["side"] or e["type"],
            "price": e["price"],
            "usdc": round(e["usdc"], 2) if e["usdc"] is not None else None,
        })

    return {
        "address": addr,
        "label": _label_for(addr),
        "snapshot_date": date,
        "classification": classification,
        "classification_reasons": reasons,
        "metrics": metrics,
        "position_value": position_value,
        "n_open_positions": len(positions),
        "open_positions": positions,
        "recent_trades": timeline,
    }


def diff_positions(tracked_dir, positions, date):
    """與上次快照的持倉 slug 集合比對，回傳 (new, disappeared, initialized)。跑完更新 prev_positions.json。"""
    prev_path = tracked_dir / "prev_positions.json"
    cur_keys = [k for k in (_position_key(p) for p in positions) if k]
    cur_set = set(cur_keys)
    cur_titles = {_position_key(p): p.get("title", "") for p in positions if _position_key(p)}

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
        new_positions = [{"key": k, "title": cur_titles.get(k, "")}
                         for k in sorted(cur_set - prev_keys)]
        disappeared = [{"key": k, "title": prev_titles.get(k, "")}
                       for k in sorted(prev_keys - cur_set)]

    prev_path.parent.mkdir(parents=True, exist_ok=True)
    prev_path.write_text(json.dumps(
        {"date": date, "position_keys": sorted(cur_set), "position_titles": cur_titles},
        ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return new_positions, disappeared, initialized


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


def build_markdown(dossier, new_positions, disappeared, initialized):
    m = dossier["metrics"]
    addr = dossier["address"]
    lines = [
        f"# 錢包深度追蹤 dossier — {addr}",
        "",
        f"> 純唯讀追蹤報告（{dossier['snapshot_date']}）。像追蹤一個交易員一樣逐日盯這個錢包。",
        "> 不含任何下單/簽章/金鑰；不構成投資建議。",
        "",
        "## 1. 身分",
        "",
        f"- 地址：`{addr}`",
        f"- 標籤：{dossier['label'] or '—'}",
        f"- 目前分類：**{dossier['classification']}**",
        f"- 分類理由：{'；'.join(dossier['classification_reasons'][:3]) or '—'}",
        "",
        "## 2. 目前持倉",
        "",
        f"持倉總值：**${_fmt(dossier['position_value'])}**（{dossier['n_open_positions']} 個未平倉部位）",
        "",
    ]
    if dossier["open_positions"]:
        lines += ["| 市場 | 方向 | size | 現值 | 均價 |",
                  "|---|---|---:|---:|---:|"]
        for p in sorted(dossier["open_positions"],
                        key=lambda x: -(x["current_value"] or 0)):
            title = (p["title"] or p["slug"] or "—").replace("|", "\\|")[:60]
            lines.append(
                f"| {title} | {p['outcome'] or '—'} | {_fmt(p['size'], ',.0f')} "
                f"| ${_fmt(p['current_value'])} | {_fmt(p['avg_price'], '.3f')} |")
    else:
        lines.append("（目前無未平倉部位）")

    lines += ["", "## 3. 績效", "",
              f"- 總 PnL：${_fmt(m.get('total_pnl'))}",
              f"- 近 30 天 PnL：${_fmt(m.get('recent_30d_pnl'))}",
              f"- 正月比率：{_fmt(m.get('positive_month_ratio'), '.0%')}",
              f"- 峰值回撤：{_fmt(m.get('max_drawdown_pct'), '.0%')}",
              f"- PnL 資料來源：{m.get('pnl_source') or '—'}"
              + ("（⚠️ 低信心，activity 現金流近似）" if m.get("low_confidence") else ""),
              "", "月度 PnL 序列：", ""]
    monthly = m.get("monthly_pnl") or {}
    if monthly:
        lines += ["| 月份 | PnL |", "|---|---:|"]
        for mon, val in monthly.items():
            lines.append(f"| {mon} | ${_fmt(val)} |")
    else:
        lines.append("（無月度序列）")

    lines += ["", "## 4. 交易輪廓", "",
              f"- 交易頻率：{_fmt(m.get('trades_per_month'), ',.1f')} 筆/月"
              f"（近 {m.get('n_trades', 0)} 筆"
              + ("，⚠️ activity 已截斷、頻率為下限估計" if m.get("activity_truncated") else "")
              + "）",
              f"- 主類別：{m.get('top_category') or '—'}"
              f"（{_fmt(m.get('top_category_share'), '.0%')}）", ""]
    counts = m.get("category_counts") or {}
    if counts:
        lines += ["類別分布：",
                  "| 類別 | 筆數 |", "|---|---:|"]
        for cat, n in sorted(counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {cat} | {n} |")
    lines += ["", "近 20 筆交易 timeline：", ""]
    if dossier["recent_trades"]:
        lines += ["| 時間 | 市場 | 動作 | price | usdcSize |",
                  "|---|---|---|---:|---:|"]
        for t in dossier["recent_trades"]:
            title = (t["title"] or "—").replace("|", "\\|")[:50]
            when = (t["time"][:10] if t["time"] else "—")
            lines.append(
                f"| {when} | {title} | {t['side'] or '—'} "
                f"| {_fmt(t['price'], '.3f')} | ${_fmt(t['usdc'])} |")
    else:
        lines.append("（無交易紀錄）")

    lines += ["", "## 5. 新建倉/平倉偵測", ""]
    if initialized:
        lines.append("**initialized** — 首次追蹤，無前次持倉可比對（下次執行起偵測異動）。")
    else:
        lines.append(f"本次新增持倉：{len(new_positions)} 個")
        for p in new_positions:
            lines.append(f"- 🟢 新建倉：{p['title'] or p['key']}")
        lines.append(f"\n本次消失持倉：{len(disappeared)} 個")
        for p in disappeared:
            lines.append(f"- ⚪ 已平倉/消失：{p['title'] or p['key']}")
        if not new_positions and not disappeared:
            lines.append("（與上次快照相比無持倉異動）")

    lines += ["", "> 純唯讀觀察，不執行任何交易。", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def load_wallet_raw(snapshot_dir, tracked_dir, addr):
    """優先讀 snapshot 的 wallets/{addr}.json；缺則讀持久化的 latest_raw.json。

    回傳 (wallet_dict, source)；都沒有回 (None, None)。
    source in {"snapshot", "persisted"}。
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


def run_track_wallet(address, snapshot_dir, tracked_root):
    """核心進入點（tests 可直接呼叫）。回傳 dossier dict；缺資料回 None。"""
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

    md_path = tracked_dir / f"dossier_{date}.md"
    json_path = tracked_dir / f"dossier_{date}.json"
    md_path.write_text(build_markdown(dossier, new_positions, disappeared, initialized),
                       encoding="utf-8")
    json_path.write_text(json.dumps(dossier, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    timeline_path = tracked_dir / "timeline.jsonl"
    row = {
        "date": date,
        "total_pnl": dossier["metrics"].get("total_pnl"),
        "position_value": dossier["position_value"],
        "n_open_positions": dossier["n_open_positions"],
        "new_positions_count": len(new_positions),
    }
    with timeline_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[track] {addr} class={dossier['classification']} "
          f"pos={dossier['n_open_positions']} new={len(new_positions)} source={source}")
    print(f"[track] dossier: {md_path}")
    return dossier


def main(argv=None):
    parser = argparse.ArgumentParser(description="Polymarket single-wallet deep tracker (read-only)")
    parser.add_argument("--address", required=True, help="0x 錢包地址")
    parser.add_argument("--snapshot", default=None,
                        help="snapshot 目錄；預設 data/snapshots/{今日UTC}")
    parser.add_argument("--tracked-dir", default=str(BASE_DIR / "data" / "tracked"))
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

    run_track_wallet(addr, snapshot_dir, tracked_root)
    return 0  # 唯讀觀察器：永遠 exit 0，讓 workflow 後續步驟能繼續


if __name__ == "__main__":
    sys.exit(main())
