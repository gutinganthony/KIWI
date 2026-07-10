#!/usr/bin/env python3
"""poly-observer shadow_bot：影子跟單觀測器（唯讀、絕不下單）。

用法（在 projects/poly-observer 下）：
    python3 shadow_bot.py [--address 0x…] [--duration-min 40] [--poll-sec 4] [--out-dir data/shadow]

目的：即時盯住目標錢包的新 TRADE 事件，偵測到的**當下**立刻抓該市場訂單簿，
記錄「跟單者此刻進場會成交在什麼價位」——實測偵測延遲（detect_lag）與
進場價劣化（adverse_drift），作為「要不要建真錢執行層」的實證閘門。

⚠️ 誠實聲明（沿 simulate_copy 風格；同段文字也印在每份摘要頂部）：
- 本工具只測「進場價劣化與延遲」，**不測完整損益**——出場價與市場結局未知，
  不能由本資料推論跟單能否獲利。
- 本工具**不執行任何交易**：不下單、不簽章、無私鑰、無錢包連線，
  只對 Polymarket 公開 read-only 端點發 HTTP GET。
- detect_lag 受輪詢間隔（--poll-sec，預設 4s）下限影響：真 bot 可用 websocket
  更快，故本測值是實際可達延遲的**上界**。
- activity 的 timestamp 是鏈上/伺服器時間，本機（runner）時鐘可能有偏移，
  detect_lag 可能含 ±數秒的系統時鐘差。
- 不構成投資建議。

魯棒性：任何請求失敗記 log 繼續跑；訂單簿抓不到記 book_unavailable；
main 永遠 exit 0（讓 CI 後續 commit-back 步驟能落地）。
網路呼叫皆可注入（http_get / sleep_fn / now_fn 參數化）供離線測試。
"""

import argparse
import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import config

BASE_DIR = Path(__file__).resolve().parent
ADDR_RE = re.compile(r"0x[0-9a-fA-F]{40}")

HONESTY_LINES = [
    "⚠️ 誠實聲明：本工具只測「進場價劣化與延遲」，**不測完整損益**（出場價與市場結局未知），",
    "不能由本資料推論跟單能否獲利。本工具不執行任何交易：不下單、不簽章、無私鑰，",
    "只對公開 read-only 端點發 HTTP GET。detect_lag 受輪詢間隔下限影響——真 bot 可用",
    "websocket 更快，故本測值是實際可達延遲的**上界**。不構成投資建議。",
    "",
    "⚠️ 時鐘註記：activity 的 timestamp 是鏈上/伺服器時間，本機（runner）時鐘可能有偏移，",
    "detect_lag 可能含 ±數秒的系統時鐘差，數值請當量級參考、不要當精確值。",
]


# ---------------------------------------------------------------------------
# HTTP 層（urllib、UA、timeout、重試——沿 probe_leaderboard / fetch 風格）
# ---------------------------------------------------------------------------

def http_get_json(url, timeout=config.HTTP_TIMEOUT, retries=config.HTTP_RETRIES,
                  sleep_fn=time.sleep):
    """GET url → (data, error)。成功 error=None；失敗 data=None、error=最後錯誤字串。

    純唯讀：只發 GET（urllib.request.Request 不帶 data/method），不含任何寫入操作。
    """
    last_error = None
    for attempt in range(1 + retries):
        if attempt > 0:
            backoff = config.HTTP_BACKOFFS[min(attempt - 1, len(config.HTTP_BACKOFFS) - 1)]
            sleep_fn(backoff)
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": config.USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", "replace")
            return json.loads(body), None
        except urllib.error.HTTPError as exc:
            snippet = ""
            try:
                snippet = exc.read().decode("utf-8", "replace")[: config.ERROR_BODY_SNIPPET_LEN]
            except Exception:
                pass
            last_error = f"HTTP {exc.code}; body={snippet}"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    return None, last_error


# ---------------------------------------------------------------------------
# 純函式：去重、書解析、衍生指標、統計（離線可測）
# ---------------------------------------------------------------------------

def trade_key(ev):
    """去重鍵：有 transactionHash 用 (tx,asset,side,size)（同一 tx 可含多筆成交），
    否則退回 (timestamp,asset,side,size) 組合。"""
    asset = str(ev.get("asset"))
    side = str(ev.get("side"))
    size = str(ev.get("size"))
    tx = ev.get("transactionHash")
    if tx:
        return ("tx", str(tx), asset, side, size)
    return ("fields", str(ev.get("timestamp")), asset, side, size)


def detect_new_trades(activity, seen):
    """從 activity 事件列表挑出未見過的 TRADE 事件。

    就地把新鍵加入 seen 集合，回傳新事件列表（非 TRADE 型別一律忽略）。
    """
    out = []
    for ev in activity or []:
        if not isinstance(ev, dict):
            continue
        if str(ev.get("type", "")).upper() != "TRADE":
            continue
        key = trade_key(ev)
        if key in seen:
            continue
        seen.add(key)
        out.append(ev)
    return out


def _to_float(val):
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def parse_book(book):
    """解析 CLOB /book 回應（bids/asks 為 [{price,size}…]，值多為字串）。

    不假設排序：best_bid 取最高買價、best_ask 取最低賣價。
    回傳 dict(best_bid, best_ask, mid, spread, bid_depth_usd, ask_depth_usd)；
    兩側皆解析不出 → None。單側缺 → 該側欄位為 None。
    """
    if not isinstance(book, dict):
        return None

    def levels(side):
        out = []
        for lv in book.get(side) or []:
            if not isinstance(lv, dict):
                continue
            p, s = _to_float(lv.get("price")), _to_float(lv.get("size"))
            if p is not None and s is not None and p > 0 and s >= 0:
                out.append((p, s))
        return out

    bids, asks = levels("bids"), levels("asks")
    if not bids and not asks:
        return None
    best_bid = max(bids, key=lambda t: t[0]) if bids else None
    best_ask = min(asks, key=lambda t: t[0]) if asks else None
    mid = spread = None
    if best_bid and best_ask:
        mid = round((best_bid[0] + best_ask[0]) / 2.0, 6)
        spread = round(best_ask[0] - best_bid[0], 6)
    return {
        "best_bid": best_bid[0] if best_bid else None,
        "best_ask": best_ask[0] if best_ask else None,
        "mid": mid,
        "spread": spread,
        "bid_depth_usd": round(best_bid[0] * best_bid[1], 2) if best_bid else None,
        "ask_depth_usd": round(best_ask[0] * best_ask[1], 2) if best_ask else None,
    }


def follower_metrics(side, px_wallet, book_summary):
    """衍生欄位：跟單者此刻進場的成交價與劣化幅度。

    BUY 吃 best_ask、SELL 砸 best_bid。adverse_drift 定義為「正值＝對跟單者更差」：
    BUY 為 (entry−px_wallet)/px_wallet（買更貴），SELL 取反向（賣更便宜）。
    depth_at_best / fillable_usd_at_best＝跟單方向那側第一檔的 size×price 美元深度。
    """
    out = {"follower_entry_px": None, "adverse_drift": None,
           "depth_at_best": None, "fillable_usd_at_best": None}
    if not book_summary:
        return out
    side = str(side or "").upper()
    if side == "BUY":
        entry, depth = book_summary.get("best_ask"), book_summary.get("ask_depth_usd")
    elif side == "SELL":
        entry, depth = book_summary.get("best_bid"), book_summary.get("bid_depth_usd")
    else:
        return out
    out["follower_entry_px"] = entry
    out["depth_at_best"] = depth
    out["fillable_usd_at_best"] = depth
    px_wallet = _to_float(px_wallet)
    if entry is not None and px_wallet and px_wallet > 0:
        raw = (entry - px_wallet) / px_wallet
        out["adverse_drift"] = round(raw if side == "BUY" else -raw, 6)
    return out


def build_row(ev, ts_detect_epoch, book_summary, book_error=None):
    """組一列 JSONL：錢包側＋偵測側＋市場側＋衍生欄位。"""
    ts_trade = None
    try:
        ts_trade = int(ev.get("timestamp"))
    except (TypeError, ValueError):
        pass
    book_summary = book_summary or {}
    row = {
        # 錢包側
        "ts_trade": ts_trade,
        "side": ev.get("side"),
        "px_wallet": _to_float(ev.get("price")),
        "usdc_size": _to_float(ev.get("usdcSize")),
        "title": ev.get("title"),
        "slug": ev.get("slug"),
        "asset": ev.get("asset"),
        "tx_hash": ev.get("transactionHash"),
        # 偵測側
        "ts_detect": datetime.fromtimestamp(ts_detect_epoch, timezone.utc)
        .isoformat(timespec="milliseconds"),
        "detect_lag_sec": (round(ts_detect_epoch - ts_trade, 2)
                           if ts_trade is not None else None),
        # 市場側
        "book_unavailable": not bool(book_summary),
        "book_error": book_error,
        "best_bid": book_summary.get("best_bid"),
        "best_ask": book_summary.get("best_ask"),
        "mid": book_summary.get("mid"),
        "spread": book_summary.get("spread"),
    }
    row.update(follower_metrics(ev.get("side"), ev.get("price"),
                                book_summary or None))
    return row


def median(values):
    """中位數；空列表回 None。"""
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return float(s[mid]) if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def percentile(values, q):
    """最近秩百分位（nearest-rank，q∈(0,100]）；空列表回 None。"""
    if not values:
        return None
    s = sorted(values)
    k = max(1, math.ceil(q / 100.0 * len(s)))
    return float(s[k - 1])


def _stat_block(values):
    return {"median": median(values), "p90": percentile(values, 90), "n": len(values)}


def summarize_rows(rows, fixed_usd=config.SIM_FIXED_USD):
    """session 統計：median/p90 detect_lag、分邊 adverse_drift、spread/深度、
    「固定 $fixed_usd 跟單在第一檔深度內可成交」比例（分母＝book 可用的列）。"""
    lags = [r["detect_lag_sec"] for r in rows if r.get("detect_lag_sec") is not None]
    drift_buy = [r["adverse_drift"] for r in rows
                 if r.get("side") == "BUY" and r.get("adverse_drift") is not None]
    drift_sell = [r["adverse_drift"] for r in rows
                  if r.get("side") == "SELL" and r.get("adverse_drift") is not None]
    with_book = [r for r in rows if not r.get("book_unavailable")]
    spreads = [r["spread"] for r in with_book if r.get("spread") is not None]
    depths = [r["depth_at_best"] for r in with_book if r.get("depth_at_best") is not None]
    fillable = [d for d in depths if d >= fixed_usd]
    return {
        "n_detected": len(rows),
        "n_book_ok": len(with_book),
        "n_book_unavailable": len(rows) - len(with_book),
        "detect_lag_sec": _stat_block(lags),
        "adverse_drift": {"BUY": _stat_block(drift_buy), "SELL": _stat_block(drift_sell)},
        "spread": {"median": median(spreads), "n": len(spreads)},
        "depth_at_best_usd": {"median": median(depths), "n": len(depths)},
        "fixed_copy_usd": fixed_usd,
        "fillable_at_best_ratio": (len(fillable) / len(depths)) if depths else None,
        "fillable_at_best_counts": {"fillable": len(fillable), "with_depth": len(depths)},
    }


# ---------------------------------------------------------------------------
# 報告
# ---------------------------------------------------------------------------

def _fmt(val, digits=4, suffix=""):
    if val is None:
        return "—"
    return f"{val:.{digits}f}{suffix}"


def _fmt_pct(val):
    return "—" if val is None else f"{val * 100:+.3f}%"


def build_markdown_section(info):
    """單一 session 的 md 段落（同日多 session 時 append 到同一份 summary md）。"""
    st = info["stats"]
    lag, dr = st["detect_lag_sec"], st["adverse_drift"]
    fill = st["fillable_at_best_ratio"]
    fill_c = st["fillable_at_best_counts"]
    lines = [
        f"## Session {info['session_stamp']}（UTC）",
        "",
        f"- 參數：address=`{info['address']}`、duration={info['duration_min']} min、"
        f"poll={info['poll_sec']}s",
        f"- 輪詢 {info['polls']} 次；activity 失敗 {info['activity_failures']}、"
        f"book 失敗 {info['book_failures']}；baseline 略過既有交易 {info['baseline_seeded']} 筆",
        f"- 偵測筆數：**{st['n_detected']}**（book 可用 {st['n_book_ok']}、"
        f"不可用 {st['n_book_unavailable']}）",
        "",
        "| 指標 | median | p90 | n |",
        "|---|---|---|---|",
        f"| detect_lag（秒，含 ±數秒時鐘差） | {_fmt(lag['median'], 2)} | "
        f"{_fmt(lag['p90'], 2)} | {lag['n']} |",
        f"| adverse_drift BUY（正=買更貴） | {_fmt_pct(dr['BUY']['median'])} | "
        f"{_fmt_pct(dr['BUY']['p90'])} | {dr['BUY']['n']} |",
        f"| adverse_drift SELL（正=賣更便宜） | {_fmt_pct(dr['SELL']['median'])} | "
        f"{_fmt_pct(dr['SELL']['p90'])} | {dr['SELL']['n']} |",
        f"| spread | {_fmt(st['spread']['median'])} | — | {st['spread']['n']} |",
        f"| depth_at_best（USD） | {_fmt(st['depth_at_best_usd']['median'], 2)} | — | "
        f"{st['depth_at_best_usd']['n']} |",
        "",
        f"- ${st['fixed_copy_usd']:.0f} 固定跟單在第一檔深度內可成交比例："
        + ("—（無可用 book 資料）" if fill is None
           else f"{fill * 100:.1f}%（{fill_c['fillable']}/{fill_c['with_depth']}）"),
        "",
    ]
    return "\n".join(lines)


def write_summary(out_dir, info):
    """落地 summary_{date}.md ＋ .json；同日多 session → md append 段落、json append 進 sessions。"""
    date = info["date"]
    json_path = out_dir / f"summary_{date}.json"
    payload = {"date": date, "address": info["address"],
               "caveats": [l for l in HONESTY_LINES if l], "sessions": []}
    if json_path.exists():
        try:
            old = json.loads(json_path.read_text(encoding="utf-8"))
            if isinstance(old, dict) and isinstance(old.get("sessions"), list):
                payload = old
        except Exception as exc:
            print(f"[shadow] 舊 summary json 解析失敗，重建：{exc}")
    payload["sessions"].append(info)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    md_path = out_dir / f"summary_{date}.md"
    section = build_markdown_section(info)
    if md_path.exists():
        with md_path.open("a", encoding="utf-8") as fh:
            fh.write("\n" + section)
    else:
        header = "\n".join(
            [f"# 影子跟單 session 摘要 — `{info['address']}` — {date}", ""]
            + ["> " + (l if l else "") for l in HONESTY_LINES] + ["", ""])
        md_path.write_text(header + section, encoding="utf-8")
    return md_path, json_path


# ---------------------------------------------------------------------------
# 主迴圈
# ---------------------------------------------------------------------------

def fetch_book(asset, http_get, sleep_fn):
    """抓單一 token 的訂單簿並解析。回傳 (book_summary|None, error|None)。
    每次書請求後固定睡 config.SHADOW_BOOK_SLEEP_SEC 尊重 rate limit。"""
    if not asset:
        return None, "activity event has no asset (token id)"
    data, err = http_get(config.SHADOW_BOOK_URL.format(asset=asset))
    sleep_fn(config.SHADOW_BOOK_SLEEP_SEC)
    if data is None:
        return None, err
    parsed = parse_book(data)
    if parsed is None:
        return None, "book JSON unparseable or both sides empty"
    return parsed, None


def run_session(address, duration_min, poll_sec, out_root,
                http_get=http_get_json, sleep_fn=time.sleep, now_fn=time.time):
    """跑一個影子 session；回傳 session_info dict（含統計）。

    http_get / sleep_fn / now_fn 可注入供離線測試；預設走真網路與真時鐘。
    """
    address = address.lower()
    started = now_fn()
    start_dt = datetime.fromtimestamp(started, timezone.utc)
    stamp = start_dt.strftime("%Y%m%dT%H%M%SZ")
    date = start_dt.strftime("%Y-%m-%d")
    out_dir = Path(out_root) / address
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / f"session_{stamp}.jsonl"

    activity_url = config.SHADOW_ACTIVITY_URL.format(addr=address)
    deadline = started + duration_min * 60.0
    seen = set()
    rows = []
    polls = activity_failures = book_failures = baseline_seeded = 0
    baseline_done = False

    print(f"[shadow] start addr={address} duration={duration_min}min poll={poll_sec}s")
    print(f"[shadow] jsonl: {jsonl_path}")
    while now_fn() < deadline:
        data, err = http_get(activity_url)
        polls += 1
        if data is None:
            activity_failures += 1
            print(f"[shadow] activity poll #{polls} failed: {err}")
        else:
            events = data if isinstance(data, list) else \
                (data.get("activity") or data.get("data") or []) if isinstance(data, dict) else []
            new_trades = detect_new_trades(events, seen)
            if not baseline_done:
                # 首次成功輪詢：把已存在的交易當 baseline，只跟蹤之後出現的新交易
                baseline_seeded = len(new_trades)
                baseline_done = True
                print(f"[shadow] baseline seeded: {baseline_seeded} pre-existing trades")
            else:
                for ev in new_trades:
                    ts_detect = now_fn()
                    book_summary, book_err = fetch_book(ev.get("asset"), http_get, sleep_fn)
                    if book_summary is None:
                        book_failures += 1
                    row = build_row(ev, ts_detect, book_summary, book_err)
                    rows.append(row)
                    with jsonl_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    print(f"[shadow] trade #{len(rows)}: {row['side']} "
                          f"px_wallet={row['px_wallet']} entry={row['follower_entry_px']} "
                          f"lag={row['detect_lag_sec']}s drift={row['adverse_drift']}")
        remaining = deadline - now_fn()
        if remaining <= 0:
            break
        sleep_fn(min(poll_sec, remaining))

    info = {
        "address": address,
        "session_stamp": stamp,
        "date": date,
        "started_utc": start_dt.isoformat(timespec="seconds"),
        "duration_min": duration_min,
        "poll_sec": poll_sec,
        "polls": polls,
        "activity_failures": activity_failures,
        "book_failures": book_failures,
        "baseline_seeded": baseline_seeded,
        "jsonl_file": jsonl_path.name,
        "stats": summarize_rows(rows),
    }
    md_path, json_path = write_summary(out_dir, info)
    print(f"[shadow] summary: {md_path}")
    print(f"[shadow] done: detected={info['stats']['n_detected']} polls={polls} "
          f"activity_failed={activity_failures} book_failed={book_failures}")
    return info


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Polymarket read-only shadow copy-trade observer（絕不下單）")
    parser.add_argument("--address", default=config.TRACKED_WALLETS[0]["address"],
                        help="目標錢包（預設 config.TRACKED_WALLETS[0]）")
    parser.add_argument("--duration-min", type=float, default=config.SHADOW_DURATION_MIN)
    parser.add_argument("--poll-sec", type=float, default=config.SHADOW_POLL_SEC)
    parser.add_argument("--out-dir", default=str(BASE_DIR / "data" / "shadow"))
    args = parser.parse_args(argv)

    addr = args.address.strip().lower()
    if not ADDR_RE.fullmatch(addr):
        print(f"[shadow] 無效地址（仍 exit 0 不擋 CI）：{args.address}", file=sys.stderr)
        return 0
    out_root = Path(args.out_dir)
    if not out_root.is_absolute():
        out_root = BASE_DIR / out_root
    try:
        info = run_session(addr, args.duration_min, args.poll_sec, out_root)
        print("SHADOW_SUMMARY " + json.dumps({
            "address": info["address"], "date": info["date"],
            "n_detected": info["stats"]["n_detected"], "polls": info["polls"],
            "activity_failures": info["activity_failures"],
            "book_failures": info["book_failures"],
        }, ensure_ascii=False))
    except Exception as exc:  # 永不 crash：CI 後續步驟要能落地
        print(f"[shadow] 主流程例外（照樣 exit 0）：{type(exc).__name__}: {exc}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
