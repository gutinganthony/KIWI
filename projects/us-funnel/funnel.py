#!/usr/bin/env python3
"""us-funnel 漏斗：Form 4 事件 → 資格關卡 → 否決關卡 → 等權評分 → 候選前 N。

用法：
    python3 funnel.py [--no-network]

三層設計（依 topics/business/2026-07-10-us-tw-signal-funnel-design.md §1 定稿）：
1. 資格關卡（進場券）：transactionCode=P 自主買入、無 10b5-1 checkbox、
   7 日滾動窗內同 issuer ≥2 名不同 reportingOwner 買入（集群）。
   （CMP 2012 的 opportunistic/routine 分型需 ≥3 年逐人歷史，屬 Phase 2。）
2. 否決關卡（一票否決）：仙股（VWAP<$1）、同窗內部人賣出額 > 買入額 50%、
   近 20 交易日日均成交額低於下限（價格源缺數據時跳過此檢查並記 meta，不否決）。
3. 等權評分（每項 0–2 分，加總排名，取前 config.TOP_N_CANDIDATES）：
   集群人數 / 買入總額帶 / CFO>CEO 職稱 / 市值帶（v0 一律 N/A=0）/ 下跌後買入。

輸入：data/events/form4_*.json（fetch_edgar.py 產出）。
輸出契約（monitor 網頁依 schema 讀取，鍵名不可改）：
data/candidates_latest.json =
    {"generated_at","scan_window_days","funnel_stats":{"raw_filings","qualified_events",
     "post_veto","final_candidates"},"candidates":[{"ticker","company","cluster_size",
     "insiders":[{"name","title"}],"total_buy_usd","score","score_breakdown",
     "first_filing_date","entry_price_ref"}]}

網路使用：只對「已通過資格關卡」的少數 issuer 抓 Stooq 日線（流動性否決＋dip 評分），
價格源故障→優雅降級（跳過相應檢查、記 meta），不 crash。純唯讀，無任何下單。
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config
from fetch_edgar import Meta, update_meta, write_json
from track_performance import make_price_fetcher

BASE_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# 事件載入
# ---------------------------------------------------------------------------

def load_events(events_dir, today, window_days):
    """讀掃描窗內的事件檔 → (buys, sells, raw_filings, days_loaded)。

    窗口 = 今天往回 window_days 個日曆日（含）之申報日檔案。壞檔跳過不 crash。
    """
    cutoff = today - timedelta(days=window_days)
    buys, sells, raw_filings, days_loaded = [], [], 0, 0
    for f in sorted(Path(events_dir).glob("form4_*.json")):
        try:
            d = datetime.strptime(f.stem.replace("form4_", ""), "%Y-%m-%d").date()
        except ValueError:
            continue
        if d < cutoff or d > today:
            continue
        try:
            day = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        buys.extend(day.get("buys") or [])
        sells.extend(day.get("sells") or [])
        raw_filings += int(day.get("raw_filings") or 0)
        days_loaded += 1
    return buys, sells, raw_filings, days_loaded


# ---------------------------------------------------------------------------
# 第一層｜資格關卡（純函式）
# ---------------------------------------------------------------------------

def _owner_key(owner):
    return owner.get("cik") or owner.get("name") or ""


def qualify(buys):
    """P 買入事件 → 通過資格關卡的集群 dict（ticker → cluster）。

    過濾：10b5-1 勾選單、無效 ticker、非正股數/價格。
    集群：同 issuer（以 ticker 聚合）≥ config.CLUSTER_MIN_INSIDERS 名不同 owner。
    （事件窗本身即 7 日滾動窗——fetch 只保留窗內申報日，載入時再按日期截窗。）
    """
    by_ticker = {}
    for ev in buys:
        if ev.get("p10b51"):
            continue  # 10b5-1 計畫單：非自主決策，資格關卡直接排除
        ticker = (ev.get("ticker") or "").strip().upper()
        if ticker in config.INVALID_TICKERS:
            continue
        if not ev.get("shares") or not ev.get("price") or ev["price"] <= 0:
            continue
        c = by_ticker.setdefault(ticker, {
            "ticker": ticker, "company": ev.get("company") or "",
            "owners": {}, "total_buy_usd": 0.0, "total_shares": 0.0,
            "first_filing_date": ev.get("filed") or "",
        })
        for owner in ev.get("owners") or []:
            key = _owner_key(owner)
            if key and key not in c["owners"]:
                c["owners"][key] = {"name": owner.get("name") or "",
                                    "title": owner.get("title") or ""}
        c["total_buy_usd"] += ev.get("usd") or 0.0
        c["total_shares"] += ev.get("shares") or 0.0
        filed = ev.get("filed") or ""
        if filed and (not c["first_filing_date"] or filed < c["first_filing_date"]):
            c["first_filing_date"] = filed
    return {t: c for t, c in by_ticker.items()
            if len(c["owners"]) >= config.CLUSTER_MIN_INSIDERS}


# ---------------------------------------------------------------------------
# 第二層｜否決關卡
# ---------------------------------------------------------------------------

def cluster_vwap(cluster):
    if cluster["total_shares"] <= 0:
        return 0.0
    return cluster["total_buy_usd"] / cluster["total_shares"]


def avg_dollar_volume(rows, lookback=None):
    """近 lookback 個交易日的日均成交額（close×volume）；rows 不足回 None。"""
    lookback = config.DOLLAR_VOLUME_LOOKBACK_DAYS if lookback is None else lookback
    if not rows:
        return None
    tail = rows[-lookback:]
    if not tail:
        return None
    return sum(close * volume for _, close, volume in tail) / len(tail)


def veto(clusters, sells, price_fn, skipped_checks):
    """否決關卡：仙股 / 同窗賣出對沖 / 流動性下限。回傳 (survivors, veto_counts)。

    價格源抓不到該 ticker → 流動性檢查跳過（不否決）、記 skipped_checks——
    寧可放行待人工複核，不因數據源故障讓漏斗空轉。
    """
    sell_usd = {}
    for s in sells:
        key = (s.get("ticker") or "").strip().upper()
        sell_usd[key] = sell_usd.get(key, 0.0) + (s.get("usd") or 0.0)
    survivors, counts = {}, {"penny": 0, "sell_offset": 0, "illiquid": 0}
    for ticker, c in clusters.items():
        vwap = cluster_vwap(c)
        if vwap < config.VETO_MIN_PRICE_USD:
            counts["penny"] += 1
            continue
        if sell_usd.get(ticker, 0.0) > c["total_buy_usd"] * config.VETO_SELL_TO_BUY_RATIO:
            counts["sell_offset"] += 1  # 同窗內部人大額賣出：訊號自相矛盾
            continue
        rows = price_fn(ticker) if price_fn else None
        if rows is None:
            skipped_checks.append(f"liquidity:{ticker}")
        else:
            adv = avg_dollar_volume(rows)
            if adv is not None and adv < config.VETO_MIN_AVG_DOLLAR_VOLUME:
                counts["illiquid"] += 1
                continue
        c["price_rows"] = rows  # 留給第三層 dip 評分，避免重抓
        survivors[ticker] = c
    return survivors, counts


# ---------------------------------------------------------------------------
# 第三層｜等權評分（每項 0–2 分；DeMiguel 2009：等權是本樣本量下唯一有據的權重）
# ---------------------------------------------------------------------------

def _title_upper(cluster):
    return [o["title"].upper() for o in cluster["owners"].values()]


def score_cluster_size(n):
    return 2 if n >= config.SCORE_CLUSTER_STRONG else 1  # 資格關卡保證 n>=2


def score_buy_usd(total):
    if total >= config.SCORE_BUY_USD_BAND_2:
        return 2
    if total >= config.SCORE_BUY_USD_BAND_1:
        return 1
    return 0


def score_title(cluster):
    """CFO 在群 → 2；CEO 在群（無 CFO）→ 1（JFQA 2012：CFO 訊號 > CEO）。"""
    titles = _title_upper(cluster)
    if any(k in t for t in titles for k in config.CFO_TITLE_KEYWORDS):
        return 2
    if any(k in t for t in titles for k in config.CEO_TITLE_KEYWORDS):
        return 1
    return 0


def score_mcap(cluster):
    """市值帶：v0 無流通股數來源（Form 4 不含），一律 N/A → 0 分。

    Phase 2 接 EDGAR company facts（sharesOutstanding）後按 config.MCAP_SMALL_CAP_MAX
    給小型股加分。刻意不用「成交股數×價格」冒充市值——那是成交額不是市值。
    """
    return 0


def score_dip(cluster, ma_days=None):
    """下跌後買入：VWAP < 20 日均價 → 1；< 均價×0.9 → 2。無價格數據 → 0。

    均價用「first_filing_date 當日以前」最後 ma_days 個收盤（避免用到訊號後價格）；
    序列不足時退回全序列尾端。
    """
    ma_days = config.DIP_MA_DAYS if ma_days is None else ma_days
    rows = cluster.get("price_rows")
    if not rows:
        return 0
    ref_date = cluster.get("first_filing_date") or "9999-12-31"
    prior = [r for r in rows if r[0] <= ref_date] or rows
    tail = prior[-ma_days:]
    if len(tail) < ma_days:
        return 0  # 上市未滿 20 日等；數據不足不給分
    ma = sum(close for _, close, _ in tail) / len(tail)
    vwap = cluster_vwap(cluster)
    if ma <= 0 or vwap <= 0:
        return 0
    if vwap < ma * config.DIP_DEEP_DISCOUNT:
        return 2
    if vwap < ma:
        return 1
    return 0


def score(cluster):
    breakdown = {
        "cluster": score_cluster_size(len(cluster["owners"])),
        "buy_usd": score_buy_usd(cluster["total_buy_usd"]),
        "title": score_title(cluster),
        "mcap": score_mcap(cluster),
        "dip": score_dip(cluster),
    }
    return sum(breakdown.values()), breakdown


# ---------------------------------------------------------------------------
# 漏斗主流程（純函式；network 全部在注入的 price_fn 內）
# ---------------------------------------------------------------------------

def to_candidate(cluster, total_score, breakdown):
    """cluster → 輸出契約的 candidate 條目（鍵名固定，monitor 依此讀取）。"""
    return {
        "ticker": cluster["ticker"],
        "company": cluster["company"],
        "cluster_size": len(cluster["owners"]),
        "insiders": list(cluster["owners"].values()),
        "total_buy_usd": round(cluster["total_buy_usd"], 2),
        "score": total_score,
        "score_breakdown": breakdown,
        "first_filing_date": cluster["first_filing_date"],
        "entry_price_ref": round(cluster_vwap(cluster), 4),
    }


def run_funnel(buys, sells, raw_filings, price_fn, top_n=None):
    """三層漏斗核心。回傳 (輸出 dict, veto_counts, skipped_checks)。"""
    top_n = config.TOP_N_CANDIDATES if top_n is None else top_n
    skipped_checks = []
    qualified = qualify(buys)
    survivors, veto_counts = veto(qualified, sells, price_fn, skipped_checks)
    scored = []
    for c in survivors.values():
        total, breakdown = score(c)
        scored.append(to_candidate(c, total, breakdown))
    # 等權總分排序；同分以買入總額、再以 ticker 決定順（輸出穩定可重現）
    scored.sort(key=lambda x: (-x["score"], -x["total_buy_usd"], x["ticker"]))
    final = scored[:top_n]
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scan_window_days": config.SCAN_WINDOW_DAYS,
        "funnel_stats": {
            "raw_filings": raw_filings,
            "qualified_events": len(qualified),
            "post_veto": len(survivors),
            "final_candidates": len(final),
        },
        "candidates": final,
    }
    return output, veto_counts, skipped_checks


def main(argv=None):
    parser = argparse.ArgumentParser(description="Form 4 three-layer funnel (read-only)")
    parser.add_argument("--no-network", action="store_true",
                        help="不抓價格源（流動性檢查跳過、dip=0；供離線驗證）")
    args = parser.parse_args(argv)

    started = time.time()
    data_dir = BASE_DIR / "data"
    today = datetime.now(timezone.utc).date()
    meta = Meta()

    buys, sells, raw_filings, days_loaded = load_events(
        data_dir / "events", today, config.SCAN_WINDOW_DAYS)
    print(f"[funnel] window={config.SCAN_WINDOW_DAYS}d days_loaded={days_loaded} "
          f"buys={len(buys)} sell_issuers={len(sells)} raw_filings={raw_filings}")

    price_fn = None if args.no_network else make_price_fetcher(meta)
    output, veto_counts, skipped_checks = run_funnel(buys, sells, raw_filings, price_fn)
    try:
        write_json(data_dir / "candidates_latest.json", output)
    except Exception as exc:
        meta.error(f"candidates_latest.json 寫入失敗：{exc}")

    payload = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "days_loaded": days_loaded,
        "funnel_stats": output["funnel_stats"],
        "veto_counts": veto_counts,
        "skipped_checks": skipped_checks[:config.META_ERRORS_MAX],
        "requests_ok": meta.requests_ok,
        "requests_failed": meta.requests_failed,
        "elapsed_sec": round(time.time() - started, 1),
        "endpoint_health": meta.endpoint_health,
        "errors": meta.errors,
    }
    try:
        update_meta(data_dir, "funnel", payload)
    except Exception as exc:
        print(f"[funnel] meta 寫入失敗：{exc}", file=sys.stderr)

    print("META " + json.dumps({"funnel_stats": output["funnel_stats"],
                                "veto_counts": veto_counts,
                                "skipped_checks": len(skipped_checks),
                                "elapsed_sec": payload["elapsed_sec"]},
                               ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
