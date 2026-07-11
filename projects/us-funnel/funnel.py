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
   集群人數 / 買入總額帶 / CFO>CEO 職稱 / 市值帶（micro/small=2、mid=1、large=0、
   無數據=0）/ 下跌後買入。
4. 風險分級（beta × 市值雙維度，只對否決關 survivors 計算）：
   市值＝EDGAR company facts 流通股數 × 最新收盤；beta＝對 SPY 近 1 年日報酬 OLS 斜率。
   檔分與加總規則見 config「風險分級」節；任一維無數據 → 保守計分＋data_gap=True。

輸入：data/events/form4_*.json（fetch_edgar.py 產出）。
輸出契約（monitor 網頁依 schema 讀取，鍵名不可改）：
data/candidates_latest.json =
    {"generated_at","scan_window_days","funnel_stats":{"raw_filings","qualified_events",
     "post_veto","final_candidates"},"candidates":[{"ticker","company","cluster_size",
     "insiders":[{"name","title"}],"total_buy_usd","score","score_breakdown",
     "first_filing_date","entry_price_ref",
     "risk":{"level","data_gap","beta","mcap_usd","mcap_band","beta_band"}}]}

網路使用：只對「已通過資格關卡」的少數 issuer 抓價格日線（主 Stooq → 備 Yahoo chart，
供流動性否決＋dip 評分＋beta）、對 survivors 抓 EDGAR company facts（市值），
價格源/EDGAR 故障→優雅降級（跳過相應檢查、走 None 保守分級、記 meta），不 crash。
純唯讀，無任何下單。
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config
from fetch_edgar import Meta, fetch_shares_outstanding, update_meta, write_json
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
            "cik": ev.get("cik"),  # issuer CIK（風險分級查 company facts 用）
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
    survivors, counts = {}, {"penny": 0, "sell_offset": 0, "illiquid": 0,
                             "fund_issuer": 0, "routine_wave": 0}
    for ticker, c in clusters.items():
        name_u = (c.get("company") or "").upper()
        if any(kw in name_u for kw in config.VETO_FUND_NAME_KEYWORDS):
            counts["fund_issuer"] += 1   # 基金/ETF/信託的內部人申報：非股票訊號
            continue
        n_owners = len(c["owners"])
        per_insider = (c["total_buy_usd"] / n_owners) if n_owners else 0.0
        if (n_owners > config.VETO_MAX_CLUSTER_SIZE
                or per_insider < config.VETO_MIN_BUY_PER_INSIDER_USD):
            counts["routine_wave"] += 1  # 例行申報潮偽裝集群（TSM 31 人型）
            continue
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


def score_mcap(mcap_usd):
    """市值帶評分（自此版啟用；市值＝company facts 流通股數 × 最新收盤）：
    micro/small（<$2B）=2、mid（$2B–10B）=1、large（>$10B）=0；None（無數據）=0。
    刻意不用「成交股數×價格」冒充市值——那是成交額不是市值。
    """
    if mcap_usd is None:
        return 0
    band = mcap_risk_band(mcap_usd)
    if band in ("micro", "small"):
        return 2
    if band == "mid":
        return 1
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


def score(cluster, mcap_usd=None):
    breakdown = {
        "cluster": score_cluster_size(len(cluster["owners"])),
        "buy_usd": score_buy_usd(cluster["total_buy_usd"]),
        "title": score_title(cluster),
        "mcap": score_mcap(mcap_usd),
        "dip": score_dip(cluster),
    }
    return sum(breakdown.values()), breakdown


# ---------------------------------------------------------------------------
# 風險分級（beta × 市值雙維度；規則常數在 config「風險分級」節，
# monitor 頁「風險分級劃分方法」備註文字須與此處一致）
# ---------------------------------------------------------------------------

def compute_beta(rows, spy_rows, lookback=None, min_overlap=None):
    """對 SPY 的 OLS beta = cov(r_i, r_spy) / var(r_spy)；數據不足 → None。純函式。

    rows / spy_rows = [(date_str, close, volume), ...] 升冪。各取近 lookback 個交易日，
    按「兩序列共同交易日」對齊後算相鄰日報酬；有效重疊（成對報酬數）< min_overlap
    或 var(r_spy)=0 → None。
    """
    lookback = config.BETA_LOOKBACK_ROWS if lookback is None else lookback
    min_overlap = config.BETA_MIN_OVERLAP_DAYS if min_overlap is None else min_overlap
    if not rows or not spy_rows:
        return None
    closes = {d: c for d, c, _ in rows[-(lookback + 1):] if c and c > 0}
    spy_closes = {d: c for d, c, _ in spy_rows[-(lookback + 1):] if c and c > 0}
    common = sorted(set(closes) & set(spy_closes))
    if len(common) < min_overlap + 1:
        return None
    r_i, r_spy = [], []
    for prev, cur in zip(common, common[1:]):
        r_i.append(closes[cur] / closes[prev] - 1.0)
        r_spy.append(spy_closes[cur] / spy_closes[prev] - 1.0)
    n = len(r_spy)
    if n < min_overlap:
        return None
    mean_i = sum(r_i) / n
    mean_spy = sum(r_spy) / n
    var_spy = sum((x - mean_spy) ** 2 for x in r_spy) / n
    if var_spy <= 0:
        return None
    cov = sum((a - mean_i) * (b - mean_spy) for a, b in zip(r_i, r_spy)) / n
    return cov / var_spy


def mcap_risk_band(mcap_usd):
    """市值 → 帶名：micro(<$300M) / small($300M–2B) / mid($2B–10B) / large(>$10B)；
    None → unknown。"""
    if mcap_usd is None:
        return "unknown"
    for threshold, _points, band in config.MCAP_RISK_BANDS:
        if mcap_usd < threshold:
            return band
    return config.MCAP_LARGE_BAND


def mcap_risk_points(mcap_usd):
    """市值檔分：<$300M=3、$300M–2B=2、$2B–10B=1、>$10B=0；None=3（保守）。"""
    if mcap_usd is None:
        return config.MCAP_NONE_POINTS
    for threshold, points, _band in config.MCAP_RISK_BANDS:
        if mcap_usd < threshold:
            return points
    return 0


def beta_risk_band(beta):
    """beta → 帶名：high(>1.3) / mid(0.8–1.3) / low(<0.8)；None → unknown。"""
    if beta is None:
        return "unknown"
    if beta > config.BETA_HIGH_MIN:
        return "high"
    if beta >= config.BETA_MID_MIN:
        return "mid"
    return "low"


def beta_risk_points(beta):
    """Beta 檔分：>1.3=2、0.8–1.3=1、<0.8=0；None=2（保守）。"""
    if beta is None:
        return config.BETA_NONE_POINTS
    band = beta_risk_band(beta)
    return {"high": 2, "mid": 1}.get(band, 0)


def assess_risk(mcap_usd, beta):
    """市值＋beta → 輸出契約的 risk dict（鍵名固定，monitor 依此讀取）。

    總分 = 市值檔分 + beta 檔分：≥4 → high、2–3 → medium、≤1 → low。
    任一維 None → 該維保守計分（市值=3、beta=2）且 data_gap=True。
    """
    total = mcap_risk_points(mcap_usd) + beta_risk_points(beta)
    if total >= config.RISK_HIGH_MIN_POINTS:
        level = "high"
    elif total >= config.RISK_MEDIUM_MIN_POINTS:
        level = "medium"
    else:
        level = "low"
    return {
        "level": level,
        "data_gap": mcap_usd is None or beta is None,
        "beta": None if beta is None else round(beta, 2),
        "mcap_usd": None if mcap_usd is None else round(mcap_usd),
        "mcap_band": mcap_risk_band(mcap_usd),
        "beta_band": beta_risk_band(beta),
    }


# ---------------------------------------------------------------------------
# 漏斗主流程（純函式；network 全部在注入的 price_fn 內）
# ---------------------------------------------------------------------------

def to_candidate(cluster, total_score, breakdown, risk):
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
        "risk": risk,
    }


def cluster_mcap(cluster, shares_fn):
    """survivor 市值 = 流通股數（company facts）× 最新收盤（price_rows 重用）；缺 → None。"""
    rows = cluster.get("price_rows")
    if shares_fn is None or not rows:
        return None
    shares = shares_fn(cluster.get("cik"))
    if not shares:
        return None
    last_close = rows[-1][1]
    if not last_close or last_close <= 0:
        return None
    return shares * last_close


def run_funnel(buys, sells, raw_filings, price_fn, top_n=None, shares_fn=None):
    """三層漏斗核心。回傳 (輸出 dict, veto_counts, skipped_checks)。

    shares_fn(cik) -> 流通股數|None：風險分級的市值來源，只對 survivors 呼叫；
    None（--no-network 等）→ 市值走 None 保守路徑。
    """
    top_n = config.TOP_N_CANDIDATES if top_n is None else top_n
    skipped_checks = []
    qualified = qualify(buys)
    survivors, veto_counts = veto(qualified, sells, price_fn, skipped_checks)
    # SPY 基準只抓一次（make_price_fetcher 有快取；無 survivors 時不抓）
    spy_rows = (price_fn(config.BETA_BENCHMARK_TICKER)
                if price_fn and survivors else None)
    scored = []
    for c in survivors.values():
        mcap = cluster_mcap(c, shares_fn)
        beta = compute_beta(c.get("price_rows"), spy_rows)
        total, breakdown = score(c, mcap_usd=mcap)
        scored.append(to_candidate(c, total, breakdown, assess_risk(mcap, beta)))
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
    shares_fn = (None if args.no_network
                 else (lambda cik: fetch_shares_outstanding(cik, meta)))
    output, veto_counts, skipped_checks = run_funnel(
        buys, sells, raw_filings, price_fn, shares_fn=shares_fn)
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
        "price_source_stats": meta.price_source_stats,
        "price_sources": meta.price_sources,
        "elapsed_sec": round(time.time() - started, 1),
        "endpoint_health": meta.endpoint_health,
        "errors": meta.errors,
    }
    try:
        update_meta(data_dir, "funnel", payload)
    except Exception as exc:
        print(f"[funnel] meta 寫入失敗：{exc}", file=sys.stderr)

    risk_summary = {}
    for c in output["candidates"]:
        r = c.get("risk") or {}
        key = (r.get("level") or "?") + ("(data_gap)" if r.get("data_gap") else "")
        risk_summary[key] = risk_summary.get(key, 0) + 1
    print("META " + json.dumps({"funnel_stats": output["funnel_stats"],
                                "veto_counts": veto_counts,
                                "skipped_checks": len(skipped_checks),
                                "risk_levels": risk_summary,
                                "elapsed_sec": payload["elapsed_sec"]},
                               ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
