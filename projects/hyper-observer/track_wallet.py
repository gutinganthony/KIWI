#!/usr/bin/env python3
"""hyper-observer track_wallet：單錢包深度追蹤器（唯讀 dossier）。

用法（在 projects/hyper-observer 下）：
    python3 track_wallet.py --address 0x.. [--snapshot data/snapshots/YYYY-MM-DD]

像追蹤一個交易員一樣持續盯一個永續錢包：讀當日 snapshot 的原始資料，
算出身分/目前持倉（方向・槓桿・強平價・未實現PnL）/portfolio 績效/近 N 筆成交，
並與上次快照比對偵測「新開倉/平倉」，逐日落地 dossier（人讀 md ＋機器 json）與 timeline.jsonl。

持久化：把該錢包原始 snapshot 複製到 data/tracked/{addr}/latest_raw.json，
讓 tracked 錢包的原始資料在每日 prune data/snapshots/*/wallets 後仍存在，供未來模擬器用。

純唯讀分析：所有 parse/指標/分類邏輯重用 classify 的函式（import，非複製）。
不含任何下單、私鑰、簽章、錢包連線程式碼；不構成投資建議。跟單模擬器為下一個里程碑。
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import config
import classify

BASE_DIR = Path(__file__).resolve().parent
ADDR_LEN = 42


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

    positions = classify.parse_positions(wallet.get("clearinghouseState"))
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
        f"- 帳戶淨值：${_fmt(m.get('account_value'))}",
        "",
        "## 2. 目前持倉",
        "",
        f"持倉名目總值：**${_fmt(dossier['position_value'])}**"
        f"（未實現 PnL ${_fmt(dossier['unrealized_pnl'])}，"
        f"{dossier['n_open_positions']} 個未平倉部位）",
        "",
    ]
    if dossier["open_positions"]:
        lines += ["| 幣 | 方向 | 槓桿 | 進場價 | 強平價 | 未實現PnL | 名目 |",
                  "|---|---|---:|---:|---:|---:|---:|"]
        for p in sorted(dossier["open_positions"],
                        key=lambda x: -(x["position_value"] or 0)):
            lev = f"{_fmt(p['leverage_value'], ',.0f')}x" + (
                f" {p['leverage_type']}" if p["leverage_type"] else "")
            lines.append(
                f"| {p['coin'] or '—'} | {p['side'] or '—'} | {lev} "
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

    lines += ["", "## 5. 新開倉/平倉偵測", ""]
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

    lines += ["", "> 純唯讀觀察，不執行任何交易。", ""]
    return "\n".join(lines)


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
        "unrealized_pnl": dossier["unrealized_pnl"],
        "n_open_positions": dossier["n_open_positions"],
        "new_positions_count": len(new_positions),
        "classification": dossier["classification"],
    }
    with timeline_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[track] {addr} class={dossier['classification']} "
          f"pos={dossier['n_open_positions']} new={len(new_positions)} source={source}")
    print(f"[track] dossier: {md_path}")
    return dossier


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Hyperliquid single-wallet deep tracker (read-only)")
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
