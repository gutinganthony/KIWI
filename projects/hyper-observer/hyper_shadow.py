#!/usr/bin/env python3
"""hyper-observer hyper_shadow：Hyperliquid 影子實測（唯讀、絕不下單）。

用法（在 projects/hyper-observer 下）：
    python3 hyper_shadow.py [--address 0x…] [--duration-min 30] [--poll-sec 5]
        [--out-dir data/shadow]

對準跟單調查唯一通過可跟性判定的候選錢包（--address 預設 config.TRACKED_WALLETS 中
label 含 "scan-best-candidate" 者，即 0x8bae35…）。其主戰場是 HIP-3 builder 部署的
小眾永續市場（coin 名形如 "xyz:META"、"@166"）——流動性深度是可跟性的最後問號：

Phase 1（主角）：深度剖面。目標市場集 = 當前持倉幣種 ∪ 近 30 天活躍幣種 top N。
    對每市場抓 l2Book，記錄 best bid/ask、spread%、兩側前 N 檔累計名目，並以
    walk-the-book 估算 $1k/$5k/$20k 市價單滑點（吃幾檔、均價偏離 mid 幾 %，雙側）。
    開班與收班各採一次（市場狀態變化對照）。低頻標的短班未必碰到新交易，
    深度數據卻每班都能採——這才是每班必得的主資料。
Phase 2（配菜）：新成交監測。輪詢 userFills 去重偵測新 fill，偵測到立即抓該 coin 的
    l2Book，記錄 fill px vs 當下 best bid/ask/mid、detect_lag、$1k 跟單的預估均價與
    劣化 %。目標戶 30 日僅 ~32 個部位事件，整班零新成交是預期常態、不算失敗。

⚠️ 誠實聲明（同段文字也印在每份摘要頂部）：
- 本工具**純唯讀**：只 POST Hyperliquid 公開免金鑰 info API 的查詢 type
  （l2Book / userFills / clearinghouseState / allMids，見 info_body 的白名單硬限），
  不下單、不簽章、無私鑰、無錢包連線，絕不碰 exchange endpoint。
- 深度剖面是**時點快照**，非成交保證；滑點估算基於當下簿面 walk-the-book，
  實盤可能更差（快照後簿面會變、撤單/搶跑/資金費未計）。
- 低頻標的的延遲/劣化樣本需**多班累積**才有統計意義，單班零樣本屬預期。
- detect_lag 受輪詢間隔（--poll-sec）下限影響，是實際可達延遲的**上界**；
  且 fill 的 time 是伺服器時間，本機（runner）時鐘可能有 ±數秒偏移。
- 不構成投資建議。

魯棒性：任何請求失敗記 log 繼續跑；book 抓不到記 book_unavailable；main 永遠 exit 0
（讓 CI 後續 commit-back 步驟能落地）。網路呼叫皆可注入（http_post / sleep_fn / now_fn
參數化）供離線測試。
"""

import argparse
import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import classify
import config

BASE_DIR = Path(__file__).resolve().parent
ADDR_RE = re.compile(r"0x[0-9a-fA-F]{40}")

HONESTY_LINES = [
    "⚠️ 誠實聲明：本工具**純唯讀**——只 POST Hyperliquid 公開 info API 的查詢",
    "（l2Book/userFills/clearinghouseState/allMids 白名單），不下單、不簽章、無私鑰、",
    "無錢包連線，絕不碰 exchange endpoint。",
    "",
    "⚠️ 數據性質：深度剖面是**時點快照**、非成交保證；滑點估算基於當下簿面 walk-the-book，",
    "實盤可能更差（快照後簿面會變、撤單/搶跑/資金費未計）。低頻標的的延遲/劣化樣本需",
    "**多班累積**才有統計意義，單班零新成交屬預期。detect_lag 受輪詢間隔下限影響，是實際",
    "可達延遲的**上界**，且含本機/伺服器時鐘差 ±數秒。不構成投資建議。",
]


def default_address():
    """config.TRACKED_WALLETS 中 label 含 SHADOW_DEFAULT_LABEL_SUBSTR 的第一個地址。

    找不到（名單改動）→ 退回名單最後一項；名單空 → 空字串（main 會擋下、仍 exit 0）。
    """
    for w in config.TRACKED_WALLETS:
        if config.SHADOW_DEFAULT_LABEL_SUBSTR in str(w.get("label") or ""):
            return str(w.get("address") or "")
    if config.TRACKED_WALLETS:
        return str(config.TRACKED_WALLETS[-1].get("address") or "")
    return ""


# ---------------------------------------------------------------------------
# HTTP 層（POST 公開 info API 的唯讀查詢；type 白名單硬限）
# ---------------------------------------------------------------------------

def info_body(info_type, address=None, coin=None):
    """組 info API 請求體（唯讀查詢）。type 不在白名單 → 直接 raise，制度性防呆。

    重要（HIP-3 市場 coin 命名慣例）：coin 一律**原樣傳遞** fills / 持倉裡的字串——
    Hyperliquid 對 builder 部署的永續市場用「dex 前綴」命名（如 "xyz:META"）或索引別名
    （如 "@166"），l2Book 請求體的 coin 就吃這些原始字串；不得改大小寫、去前綴或自行映射。
    """
    if info_type not in config.SHADOW_ALLOWED_INFO_TYPES:
        raise ValueError(f"info type 不在唯讀白名單 {config.SHADOW_ALLOWED_INFO_TYPES}："
                         f"{info_type}")
    body = {"type": info_type}
    if address is not None:
        body["user"] = address
    if coin is not None:
        body["coin"] = coin  # 原樣傳遞（builder 市場："xyz:META"、"@166"）
    return body


def http_post_info(body, timeout=config.HTTP_TIMEOUT, retries=config.HTTP_RETRIES,
                   sleep_fn=time.sleep):
    """POST config.INFO_URL → (data, error)。成功 error=None；失敗 data=None。

    純唯讀：只發免金鑰 info 查詢（body 的 type 已由 info_body 白名單硬限），
    不對任何 exchange endpoint 發請求、不含簽章與私鑰。
    """
    payload = json.dumps(body).encode("utf-8")
    last_error = None
    for attempt in range(1 + retries):
        if attempt > 0:
            backoff = config.HTTP_BACKOFFS[min(attempt - 1, len(config.HTTP_BACKOFFS) - 1)]
            sleep_fn(backoff)
        try:
            req = urllib.request.Request(config.INFO_URL, data=payload, headers={
                "Content-Type": "application/json",
                "User-Agent": config.USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8", "replace")
            return json.loads(text), None
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
# 純函式：解析、walk-the-book、去重、統計（離線可測）
# ---------------------------------------------------------------------------

def _to_float(val):
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def as_fill_list(data):
    """userFills 回應正規化成 list-of-dict（防禦：dict 包一層也接受）。"""
    if isinstance(data, list):
        return [f for f in data if isinstance(f, dict)]
    if isinstance(data, dict):
        for key in ("fills", "data", "userFills"):
            if isinstance(data.get(key), list):
                return [f for f in data[key] if isinstance(f, dict)]
    return []


def fill_key(f):
    """fill 去重鍵：tid（全域唯一）優先；缺則 hash＋欄位（同 tx 可含多筆成交）；
    再缺退回 (time, coin, side, sz) 組合。"""
    tid = f.get("tid")
    if tid is not None:
        return ("tid", str(tid))
    h = f.get("hash")
    if h:
        return ("hash", str(h), str(f.get("coin")), str(f.get("side")),
                str(f.get("sz")), str(f.get("time")))
    return ("fields", str(f.get("time")), str(f.get("coin")),
            str(f.get("side")), str(f.get("sz")))


def detect_new_fills(raw_fills, seen):
    """挑出未見過的 fill（就地把新鍵加入 seen），回傳新 fill 清單。"""
    out = []
    for f in raw_fills or []:
        if not isinstance(f, dict):
            continue
        key = fill_key(f)
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def active_coins(raw_fills, now_ts, window_days=None, top_n=None):
    """近 window_days 天各 coin 成交筆數。回 (top_n 清單 [(coin, n)], 完整 Counter)。

    coin 字串一律原樣保留（builder 市場名 "xyz:META"、"@166" 不得改寫）。
    """
    window_days = window_days or config.SHADOW_ACTIVE_WINDOW_DAYS
    top_n = top_n or config.SHADOW_TOP_COINS
    cutoff = now_ts - window_days * 86400
    counter = Counter()
    for f in raw_fills or []:
        if not isinstance(f, dict):
            continue
        ts = classify._norm_ts(f.get("time"))
        coin = f.get("coin")
        if ts is None or not coin:
            continue
        if ts >= cutoff:
            counter[str(coin)] += 1
    return counter.most_common(top_n), counter


def parse_l2book(raw, top_levels=None):
    """解析 info API l2Book 回應（官方格式：{coin, time, levels: [[bids],[asks]]}，
    每檔 {px, sz, n}、值為字串）。

    不假設排序：bids 依價由高到低、asks 由低到高自行排序。兩側皆空 → None。
    回 {bids, asks, best_bid, best_ask, mid, spread_pct, top_bid_notional_usd,
       top_ask_notional_usd}；單側缺 → 該側欄位 None。
    """
    if not isinstance(raw, dict):
        return None
    levels = raw.get("levels")
    if not isinstance(levels, list) or len(levels) < 2:
        return None

    def side_levels(lst):
        out = []
        if isinstance(lst, list):
            for lv in lst:
                if not isinstance(lv, dict):
                    continue
                px, sz = _to_float(lv.get("px")), _to_float(lv.get("sz"))
                if px is not None and sz is not None and px > 0 and sz > 0:
                    out.append((px, sz))
        return out

    bids = sorted(side_levels(levels[0]), key=lambda t: -t[0])
    asks = sorted(side_levels(levels[1]), key=lambda t: t[0])
    if not bids and not asks:
        return None
    best_bid = bids[0][0] if bids else None
    best_ask = asks[0][0] if asks else None
    mid = spread_pct = None
    if best_bid is not None and best_ask is not None:
        mid = (best_bid + best_ask) / 2.0
        if mid > 0:
            spread_pct = round((best_ask - best_bid) / mid * 100.0, 4)
    n = top_levels or config.SHADOW_BOOK_TOP_LEVELS
    return {
        "bids": bids,
        "asks": asks,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid": mid,
        "spread_pct": spread_pct,
        "top_bid_notional_usd": round(sum(p * s for p, s in bids[:n]), 2) if bids else None,
        "top_ask_notional_usd": round(sum(p * s for p, s in asks[:n]), 2) if asks else None,
    }


def parse_allmids(raw):
    """allMids 回應（{coin: "mid", …}）→ {coin: float}。

    註：HIP-3 builder dex 的市場（"xyz:META" 等）通常**不在**預設 allMids 映射裡
    （不帶 dex 參數只回主 dex），缺席屬預期——mid 以該市場自己的 l2Book 為準，
    此欄僅作交叉參考、缺了不影響深度剖面。
    """
    out = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            f = _to_float(v)
            if isinstance(k, str) and f is not None:
                out[k] = f
    return out


def walk_the_book(levels, notional_usd):
    """walk-the-book：市價單吃 notional_usd 美元名目要吃進幾檔、平均成交價多少。

    levels: [(px, sz), …]，須已按「最優價在前」排序（買方吃 asks 由低到高；
    賣方吃 bids 由高到低）。回 {target_usd, filled_usd, avg_px, levels_used, exhausted}；
    整本簿吃完仍不夠 → exhausted=True、avg_px 為已吃部分的均價；空簿 → avg_px None。
    """
    remaining = float(notional_usd)
    spent = 0.0
    size = 0.0
    used = 0
    for px, sz in levels or []:
        if remaining <= 1e-9:
            break
        cap = px * sz
        if cap <= 0:
            continue
        take = min(remaining, cap)
        spent += take
        size += take / px
        used += 1
        remaining -= take
    return {
        "target_usd": float(notional_usd),
        "filled_usd": round(spent, 2),
        "avg_px": (spent / size) if size > 0 else None,
        "levels_used": used,
        "exhausted": remaining > 1e-9,
    }


def slippage_profile(book, notionals=None):
    """雙側 walk-the-book 滑點剖面：{"buy": {"1000": {…}, …}, "sell": {…}}。

    dev_vs_mid_pct＝均價偏離 mid 的 %（正=對 taker 更差；買方高於 mid、賣方低於 mid）。
    """
    notionals = notionals or config.SHADOW_DEPTH_NOTIONALS
    mid = book.get("mid") if book else None
    out = {"buy": {}, "sell": {}}
    for side, levels in (("buy", (book or {}).get("asks") or []),
                         ("sell", (book or {}).get("bids") or [])):
        for n_usd in notionals:
            r = walk_the_book(levels, n_usd)
            dev = None
            if r["avg_px"] is not None and mid:
                raw = ((r["avg_px"] - mid) / mid) if side == "buy" else ((mid - r["avg_px"]) / mid)
                dev = round(raw * 100.0, 4)
            out[side][str(int(n_usd))] = {
                "avg_px": round(r["avg_px"], 10) if r["avg_px"] is not None else None,
                "levels_used": r["levels_used"],
                "filled_usd": r["filled_usd"],
                "exhausted": r["exhausted"],
                "dev_vs_mid_pct": dev,
            }
    return out


def follower_side(fill):
    """fill → 跟單者方向（"buy"/"sell"/None）。HL side："B"=買、"A"=賣；缺則由 dir 推。"""
    side = str(fill.get("side") or "").upper()
    if side.startswith("B"):
        return "buy"
    if side.startswith("A") or side.startswith("S"):
        return "sell"
    d = str(fill.get("dir") or "").lower()
    if ("open" in d and "long" in d) or ("close" in d and "short" in d):
        return "buy"
    if ("open" in d and "short" in d) or ("close" in d and "long" in d):
        return "sell"
    return None


def build_depth_row(pass_name, coin, ts_epoch, book, allmids_mid=None, book_error=None):
    """深度剖面 JSONL 一列（每市場、每班次 open/close 各一列）。"""
    row = {
        "kind": "depth_profile",
        "pass": pass_name,
        "coin": coin,  # 原始 coin 字串（builder 市場名不得改寫）
        "ts": datetime.fromtimestamp(ts_epoch, timezone.utc).isoformat(timespec="seconds"),
        "book_unavailable": book is None,
        "book_error": book_error,
        "best_bid": None, "best_ask": None, "mid": None, "spread_pct": None,
        "mid_allmids": allmids_mid,
        "top_bid_notional_usd": None, "top_ask_notional_usd": None,
        "slippage": None,
    }
    if book:
        row.update({
            "best_bid": book["best_bid"], "best_ask": book["best_ask"],
            "mid": book["mid"], "spread_pct": book["spread_pct"],
            "top_bid_notional_usd": book["top_bid_notional_usd"],
            "top_ask_notional_usd": book["top_ask_notional_usd"],
            "slippage": slippage_profile(book),
        })
    return row


def build_fill_row(fill, ts_detect_epoch, book, book_error=None):
    """新成交事件 JSONL 一列：錢包側＋偵測側＋當下簿面＋$1k 跟單估算。"""
    ts_fill = classify._norm_ts(fill.get("time"))
    px_fill = _to_float(fill.get("px"))
    f_side = follower_side(fill)
    copy_notional = config.SHADOW_DEPTH_NOTIONALS[0]
    row = {
        "kind": "fill_event",
        # 錢包側
        "coin": str(fill.get("coin") or ""),
        "side": fill.get("side"),
        "dir": fill.get("dir"),
        "px_fill": px_fill,
        "sz": _to_float(fill.get("sz")),
        "closed_pnl": _to_float(fill.get("closedPnl")),
        "ts_fill": ts_fill,
        # 偵測側
        "ts_detect": datetime.fromtimestamp(ts_detect_epoch, timezone.utc)
        .isoformat(timespec="milliseconds"),
        "detect_lag_sec": (round(ts_detect_epoch - ts_fill, 2)
                           if ts_fill is not None else None),
        # 市場側（偵測當下的簿面）
        "book_unavailable": book is None,
        "book_error": book_error,
        "best_bid": book["best_bid"] if book else None,
        "best_ask": book["best_ask"] if book else None,
        "mid": book["mid"] if book else None,
        "spread_pct": book["spread_pct"] if book else None,
        "follower_side": f_side,
        "side_top_notional_usd": ((book["top_ask_notional_usd"] if f_side == "buy"
                                   else book["top_bid_notional_usd"])
                                  if (book and f_side) else None),
        "copy_1k": None,
    }
    if book and f_side:
        levels = book["asks"] if f_side == "buy" else book["bids"]
        r = walk_the_book(levels, copy_notional)
        deg_fill = dev_mid = None
        if r["avg_px"] is not None:
            if px_fill and px_fill > 0:
                raw = ((r["avg_px"] - px_fill) / px_fill if f_side == "buy"
                       else (px_fill - r["avg_px"]) / px_fill)
                deg_fill = round(raw * 100.0, 4)
            if book["mid"]:
                rawm = ((r["avg_px"] - book["mid"]) / book["mid"] if f_side == "buy"
                        else (book["mid"] - r["avg_px"]) / book["mid"])
                dev_mid = round(rawm * 100.0, 4)
        row["copy_1k"] = {
            "target_usd": r["target_usd"],
            "avg_px": round(r["avg_px"], 10) if r["avg_px"] is not None else None,
            "levels_used": r["levels_used"],
            "filled_usd": r["filled_usd"],
            "exhausted": r["exhausted"],
            "degradation_vs_fill_pct": deg_fill,  # 正=比錢包成交價更差
            "dev_vs_mid_pct": dev_mid,
        }
    return row


def median(values):
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


def summarize_fill_rows(rows):
    """新成交事件統計：偵測數、book 可用數、detect_lag 與 $1k 劣化的 median/p90。"""
    lags = [r["detect_lag_sec"] for r in rows if r.get("detect_lag_sec") is not None]
    degs = [r["copy_1k"]["degradation_vs_fill_pct"] for r in rows
            if r.get("copy_1k") and r["copy_1k"].get("degradation_vs_fill_pct") is not None]
    return {
        "n_detected": len(rows),
        "n_book_ok": sum(1 for r in rows if not r.get("book_unavailable")),
        "detect_lag_sec": _stat_block(lags),
        "copy_1k_degradation_pct": _stat_block(degs),
    }


def _compact_depth(row):
    """深度剖面 JSONL 列 → summary json 用的精簡形。"""
    if row is None:
        return None
    sl = row.get("slippage") or {}

    def devs(side):
        return {k: (v or {}).get("dev_vs_mid_pct") for k, v in (sl.get(side) or {}).items()}

    return {
        "book_unavailable": row.get("book_unavailable"),
        "book_error": row.get("book_error"),
        "mid": row.get("mid"),
        "spread_pct": row.get("spread_pct"),
        "mid_allmids": row.get("mid_allmids"),
        "top_bid_notional_usd": row.get("top_bid_notional_usd"),
        "top_ask_notional_usd": row.get("top_ask_notional_usd"),
        "buy_dev_vs_mid_pct": devs("buy"),
        "sell_dev_vs_mid_pct": devs("sell"),
    }


# ---------------------------------------------------------------------------
# 報告
# ---------------------------------------------------------------------------

def _fmt(val, spec=",.2f"):
    if val is None:
        return "—"
    try:
        return format(val, spec)
    except (TypeError, ValueError):
        return str(val)


def _fmt_px(val):
    return "—" if val is None else f"{val:g}"


def _fmt_usd(val):
    return "—" if val is None else f"${val:,.0f}"


def _fmt_pct(val, signed=False):
    if val is None:
        return "—"
    return f"{val:+.3f}%" if signed else f"{val:.3f}%"


def _pair(devs_buy, devs_sell, key):
    return f"{_fmt_pct(devs_buy.get(key))}/{_fmt_pct(devs_sell.get(key))}"


def build_markdown_section(info):
    """單一 session 的 md 段落（同日多 session append 到同一份 summary md）。"""
    lines = [
        f"## Session {info['session_stamp']}（UTC）",
        "",
        f"- 參數：address=`{info['address']}`、duration={info['duration_min']} min、"
        f"poll={info['poll_sec']}s",
        f"- 請求健康：fills 輪詢 {info['polls']} 次（失敗 {info['fills_poll_failures']}）、"
        f"book 失敗 {info['book_failures']}、allMids 失敗 {info['allmids_failures']}、"
        f"429 退避 {info['rate_limited_backoffs']} 次；"
        f"baseline 略過既有成交 {info['baseline_seeded']} 筆",
    ]
    if info.get("discovery_errors"):
        lines.append("- ⚠️ 探索階段錯誤：" + "；".join(info["discovery_errors"])[:400])
    targets = info.get("targets") or []
    if targets:
        tdesc = "、".join(
            f"`{t['coin']}`（{'+'.join(t['sources'])}，30d fills {t['n_fills_30d']}）"
            for t in targets)
        lines.append(f"- 目標市場（持倉 ∪ 近 {config.SHADOW_ACTIVE_WINDOW_DAYS} 天活躍 "
                     f"top {config.SHADOW_TOP_COINS}）：{tdesc}")
    else:
        lines.append("- 目標市場：**無**（clearinghouseState/userFills 探索失敗或戶頭無活動）")

    # --- 深度剖面（主角）---
    lines += ["", "### 深度剖面（主角；開班/收班各一次，時點快照非成交保證）", ""]
    depth = info.get("depth") or {}
    keys = [str(int(n)) for n in config.SHADOW_DEPTH_NOTIONALS]
    if depth:
        head = ("| 市場 | 班次 | mid | spread% | 前5檔名目 買/賣 | "
                + " | ".join(f"${int(n) // 1000}k 買/賣" for n in config.SHADOW_DEPTH_NOTIONALS)
                + " | $1k 往返 |")
        lines += [head, "|---|---|---:|---:|---|" + "---|" * len(keys) + "---:|"]
        for coin, passes in depth.items():
            for pass_name in ("open", "close"):
                c = passes.get(pass_name)
                if c is None:
                    continue
                if c.get("book_unavailable"):
                    err = str(c.get("book_error") or "—").replace("|", "\\|")[:60]
                    lines.append(f"| `{coin}` | {pass_name} | ⚠️ book_unavailable | {err} | —"
                                 + " | —" * len(keys) + " | — |")
                    continue
                buy = c.get("buy_dev_vs_mid_pct") or {}
                sell = c.get("sell_dev_vs_mid_pct") or {}
                b1, s1 = buy.get(keys[0]), sell.get(keys[0])
                rt_cell = (_fmt_pct(round(b1 + s1, 4))
                           if b1 is not None and s1 is not None else "—")
                depth_pair = (f"{_fmt_usd(c.get('top_bid_notional_usd'))}/"
                              f"{_fmt_usd(c.get('top_ask_notional_usd'))}")
                cells = " | ".join(_pair(buy, sell, k) for k in keys)
                lines.append(f"| `{coin}` | {pass_name} | {_fmt_px(c.get('mid'))} "
                             f"| {_fmt_pct(c.get('spread_pct'))} | {depth_pair} "
                             f"| {cells} | {rt_cell} |")
    else:
        lines.append("（無深度剖面資料——無目標市場或 book 全數抓不到）")

    rt = info.get("roundtrip_1k_pct")
    if rt and rt.get("value") is not None:
        lines.append("")
        lines.append(
            f"- **$1k 跟單在主力市場 `{rt['coin']}` 的往返成本估算：{rt['value']:.3f}%**"
            f"（{rt['pass']} 快照；買入偏離 mid ＋ 賣出偏離 mid，含 spread 與吃檔滑點、"
            f"進出各一次；時點簿面估算，實盤可能更差）")
    else:
        lines += ["", "- $1k 往返成本估算：—（主力市場 book 不可用或無目標市場）"]

    # --- 新成交監測（配菜）---
    nf = info["new_fills"]
    lines += ["", "### 新成交監測（配菜）", ""]
    if nf["n_detected"] == 0:
        lines.append(
            "- 新成交：**0 筆**——**預期內**（目標戶為低頻交易者：30 日僅 ~32 個部位事件，"
            "短班大概率碰不到新交易；不算失敗，延遲/劣化樣本靠多班累積）")
        if info["polls"] and info["fills_poll_failures"] >= info["polls"]:
            lines.append("- ⚠️ 注意：本班 fills 輪詢全數失敗，0 筆亦可能是「抓不到」而非"
                         "「沒有」——見請求健康列")
    else:
        lag = nf["detect_lag_sec"]
        deg = nf["copy_1k_degradation_pct"]
        lines += [
            f"- 偵測 **{nf['n_detected']}** 筆新成交（book 可用 {nf['n_book_ok']}）",
            "",
            "| 指標 | median | p90 | n |",
            "|---|---|---|---|",
            f"| detect_lag（秒；輪詢上界＋時鐘差） | {_fmt(lag['median'], ',.2f')} | "
            f"{_fmt(lag['p90'], ',.2f')} | {lag['n']} |",
            f"| $1k 跟單劣化 vs fill px（%，正=更差） | {_fmt_pct(deg['median'], signed=True)} | "
            f"{_fmt_pct(deg['p90'], signed=True)} | {deg['n']} |",
        ]
    lines.append("")
    return "\n".join(lines)


def write_summary(out_dir, info):
    """落地 summary_{date}.md ＋ .json；同日多 session → md append 段落、json append sessions。"""
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
            [f"# Hyperliquid 影子實測 session 摘要 — `{info['address']}` — {date}", ""]
            + ["> " + (l if l else "") for l in HONESTY_LINES] + ["", ""])
        md_path.write_text(header + section, encoding="utf-8")
    return md_path, json_path


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def depth_profile_pass(pass_name, coins, http_post, sleep_fn, now_fn, counters, write_row):
    """對目標市場集抓一輪 l2Book（＋一次 allMids 交叉參考）。回 {coin: 深度列}。"""
    if not coins:
        return {}
    mids_raw, mids_err = http_post(info_body("allMids"))
    sleep_fn(config.HTTP_SLEEP_BETWEEN)
    allmids = parse_allmids(mids_raw) if mids_raw is not None else {}
    if mids_raw is None:
        counters["allmids_failures"] += 1
        print(f"[shadow] allMids 失敗（{pass_name}）：{mids_err}")
    rows = {}
    for coin in coins:
        # coin 原樣傳遞（HIP-3 builder 市場命名慣例："xyz:META"、"@166"——
        # 直接用 fills/持倉裡的原始字串，失敗記 book_unavailable 不 crash）
        raw, err = http_post(info_body("l2Book", coin=coin))
        sleep_fn(config.SHADOW_BOOK_SLEEP_SEC)
        book = parse_l2book(raw) if raw is not None else None
        book_error = None
        if book is None:
            counters["book_failures"] += 1
            book_error = err or "book JSON unparseable or both sides empty"
        row = build_depth_row(pass_name, coin, now_fn(), book,
                              allmids_mid=allmids.get(coin), book_error=book_error)
        write_row(row)
        rows[coin] = row
        print(f"[shadow] depth[{pass_name}] {coin}: "
              + (f"book_unavailable（{book_error}）" if book is None
                 else f"mid={_fmt_px(row['mid'])} spread%={_fmt_pct(row['spread_pct'])}"))
    return rows


def run_session(address, duration_min, poll_sec, out_root,
                http_post=None, sleep_fn=time.sleep, now_fn=time.time):
    """跑一個影子 session；回傳 session_info dict（含深度剖面與新成交統計）。

    http_post / sleep_fn / now_fn 可注入供離線測試；預設走真網路與真時鐘。
    """
    http_post = http_post or http_post_info
    address = address.lower()
    started = now_fn()
    start_dt = datetime.fromtimestamp(started, timezone.utc)
    stamp = start_dt.strftime("%Y%m%dT%H%M%SZ")
    date = start_dt.strftime("%Y-%m-%d")
    out_dir = Path(out_root) / address
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / f"session_{stamp}.jsonl"
    counters = {"book_failures": 0, "allmids_failures": 0}

    def write_row(row):
        with jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[shadow] start addr={address} duration={duration_min}min poll={poll_sec}s")
    print(f"[shadow] jsonl: {jsonl_path}")

    # --- Phase 1a：目標市場探索（當前持倉 ∪ 近 30 天活躍 top N；coin 字串原樣保留）---
    discovery_errors = []
    chs_raw, chs_err = http_post(info_body("clearinghouseState", address=address))
    sleep_fn(config.HTTP_SLEEP_BETWEEN)
    position_coins = []
    if chs_raw is None:
        discovery_errors.append(f"clearinghouseState: {chs_err}")
    else:
        try:
            position_coins = [p["coin"] for p in classify.parse_positions(chs_raw)
                              if p.get("coin")]
        except Exception as exc:
            discovery_errors.append(f"parse_positions: {type(exc).__name__}: {exc}")
    uf_raw, uf_err = http_post(info_body("userFills", address=address))
    sleep_fn(config.HTTP_SLEEP_BETWEEN)
    seed_fills = None
    if uf_raw is None:
        discovery_errors.append(f"userFills(seed): {uf_err}")
    else:
        seed_fills = as_fill_list(uf_raw)
    top_list, full_counter = active_coins(seed_fills or [], now_fn())
    by_coin = {}
    for coin in position_coins:
        by_coin[coin] = {"coin": coin, "sources": ["position"],
                         "n_fills_30d": int(full_counter.get(coin, 0))}
    for coin, n in top_list:
        if coin in by_coin:
            by_coin[coin]["sources"].append("active")
        else:
            by_coin[coin] = {"coin": coin, "sources": ["active"], "n_fills_30d": int(n)}
    targets = list(by_coin.values())
    coins = [t["coin"] for t in targets]
    main_market = max(targets, key=lambda t: t["n_fills_30d"])["coin"] if targets else None
    print(f"[shadow] targets({len(coins)}): {coins} main={main_market}")

    # baseline：探索用的 userFills 回應直接當 baseline（省一次請求）；
    # 探索失敗則由第一次成功輪詢 seed。
    seen = set()
    baseline_seeded = 0
    baseline_done = False
    if seed_fills is not None:
        baseline_seeded = len(detect_new_fills(seed_fills, seen))
        baseline_done = True
        print(f"[shadow] baseline seeded: {baseline_seeded} 筆既有成交")

    # --- Phase 1b：深度剖面（開班）---
    depth_rows = {}
    for coin, row in depth_profile_pass("open", coins, http_post, sleep_fn, now_fn,
                                        counters, write_row).items():
        depth_rows.setdefault(coin, {})["open"] = row

    # --- Phase 2：新成交監測（輪詢 userFills；低頻標的整班零新成交屬預期）---
    deadline = started + duration_min * 60.0
    fill_rows = []
    polls = fills_poll_failures = rate_limited = 0
    while now_fn() < deadline:
        data, err = http_post(info_body("userFills", address=address))
        polls += 1
        if data is None:
            fills_poll_failures += 1
            print(f"[shadow] fills poll #{polls} failed: {err}")
            if err and "429" in str(err):
                # rate limit 自癒：退避一段時間再繼續（見 config 權重註記）
                rate_limited += 1
                sleep_fn(config.SHADOW_RATE_LIMIT_COOLDOWN_SEC)
        else:
            new_fills = detect_new_fills(as_fill_list(data), seen)
            if not baseline_done:
                baseline_seeded = len(new_fills)
                baseline_done = True
                print(f"[shadow] baseline seeded (late): {baseline_seeded} 筆既有成交")
            else:
                for f in new_fills:
                    ts_detect = now_fn()
                    # coin 原樣傳遞（builder 市場："xyz:META"、"@166"）
                    braw, berr = http_post(info_body("l2Book", coin=str(f.get("coin") or "")))
                    sleep_fn(config.SHADOW_BOOK_SLEEP_SEC)
                    book = parse_l2book(braw) if braw is not None else None
                    book_error = None
                    if book is None:
                        counters["book_failures"] += 1
                        book_error = berr or "book JSON unparseable or both sides empty"
                    row = build_fill_row(f, ts_detect, book, book_error)
                    fill_rows.append(row)
                    write_row(row)
                    copy = row.get("copy_1k") or {}
                    print(f"[shadow] fill #{len(fill_rows)}: {row['coin']} "
                          f"{row['follower_side']} px_fill={row['px_fill']} "
                          f"lag={row['detect_lag_sec']}s "
                          f"copy1k_avg={copy.get('avg_px')} "
                          f"deg={copy.get('degradation_vs_fill_pct')}%")
        remaining = deadline - now_fn()
        if remaining <= 0:
            break
        sleep_fn(min(poll_sec, remaining))

    # --- Phase 1c：深度剖面（收班；與開班對照市場狀態變化）---
    for coin, row in depth_profile_pass("close", coins, http_post, sleep_fn, now_fn,
                                        counters, write_row).items():
        depth_rows.setdefault(coin, {})["close"] = row

    # 主力市場 $1k 往返成本（進出各一次滑點＋spread）：優先收班快照，缺退開班
    roundtrip = None
    key_1k = str(int(config.SHADOW_DEPTH_NOTIONALS[0]))
    if main_market:
        for pass_name in ("close", "open"):
            sl = ((depth_rows.get(main_market) or {}).get(pass_name) or {}).get("slippage")
            if not sl:
                continue
            b = (sl.get("buy", {}).get(key_1k) or {}).get("dev_vs_mid_pct")
            s = (sl.get("sell", {}).get(key_1k) or {}).get("dev_vs_mid_pct")
            if b is not None and s is not None:
                roundtrip = {"coin": main_market, "value": round(b + s, 4),
                             "pass": pass_name}
                break

    info = {
        "address": address,
        "session_stamp": stamp,
        "date": date,
        "started_utc": start_dt.isoformat(timespec="seconds"),
        "duration_min": duration_min,
        "poll_sec": poll_sec,
        "targets": targets,
        "main_market": main_market,
        "polls": polls,
        "fills_poll_failures": fills_poll_failures,
        "book_failures": counters["book_failures"],
        "allmids_failures": counters["allmids_failures"],
        "rate_limited_backoffs": rate_limited,
        "discovery_errors": discovery_errors,
        "baseline_seeded": baseline_seeded,
        "jsonl_file": jsonl_path.name,
        "depth": {coin: {p: _compact_depth(r) for p, r in passes.items()}
                  for coin, passes in depth_rows.items()},
        "roundtrip_1k_pct": roundtrip,
        "new_fills": summarize_fill_rows(fill_rows),
    }
    md_path, _ = write_summary(out_dir, info)
    print(f"[shadow] summary: {md_path}")
    print(f"[shadow] done: markets={len(coins)} new_fills={info['new_fills']['n_detected']} "
          f"polls={polls} poll_failed={fills_poll_failures} "
          f"book_failed={counters['book_failures']}")
    return info


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Hyperliquid read-only shadow observer（深度剖面＋新成交監測；絕不下單）")
    parser.add_argument("--address", default=None,
                        help="目標錢包（預設 config.TRACKED_WALLETS 中 label 含 "
                             f"'{config.SHADOW_DEFAULT_LABEL_SUBSTR}' 者）")
    parser.add_argument("--duration-min", type=float, default=config.SHADOW_DURATION_MIN)
    parser.add_argument("--poll-sec", type=float, default=config.SHADOW_POLL_SEC)
    parser.add_argument("--out-dir", default=str(BASE_DIR / "data" / "shadow"))
    args = parser.parse_args(argv)

    addr = (args.address or default_address()).strip().lower()
    if not ADDR_RE.fullmatch(addr):
        print(f"[shadow] 無效地址（仍 exit 0 不擋 CI）：{args.address!r}", file=sys.stderr)
        return 0
    out_root = Path(args.out_dir)
    if not out_root.is_absolute():
        out_root = BASE_DIR / out_root
    try:
        info = run_session(addr, args.duration_min, args.poll_sec, out_root)
        print("SHADOW_SUMMARY " + json.dumps({
            "address": info["address"], "date": info["date"],
            "targets": len(info["targets"]),
            "new_fills": info["new_fills"]["n_detected"],
            "polls": info["polls"],
            "fills_poll_failures": info["fills_poll_failures"],
            "book_failures": info["book_failures"],
        }, ensure_ascii=False))
    except Exception as exc:  # 永不 crash：CI 後續 commit-back 要能落地
        print(f"[shadow] 主流程例外（照樣 exit 0）：{type(exc).__name__}: {exc}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
