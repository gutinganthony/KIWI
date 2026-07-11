#!/usr/bin/env python3
"""us-funnel 離線自測：不碰網路，餵手造 Form 4 fixtures 驗證解析、三層漏斗、
輸出契約 schema 與前瞻報酬回填邏輯。

用法（在 projects/us-funnel 下）：
    python3 tests/test_offline.py
"""

import json
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

import config  # noqa: E402
import fetch_edgar  # noqa: E402
import funnel  # noqa: E402
import track_performance as track  # noqa: E402

FIXTURES = TESTS_DIR / "fixtures"
TODAY = date(2026, 7, 10)  # fixtures 的時間軸基準

checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        print(f"FAIL: {msg}")
        raise AssertionError(msg)
    print(f"  ok: {msg}")


def _read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def _daily_rows(start, end, close_fn, volume=100000.0):
    """[(date_str, close, volume)]，start~end 每日一筆（含週末，簡化）。"""
    rows, d = [], start
    while d <= end:
        rows.append((d.strftime("%Y-%m-%d"), close_fn(d), volume))
        d += timedelta(days=1)
    return rows


# ---------------------------------------------------------------------------
# [1] 每日索引解析
# ---------------------------------------------------------------------------

IDX_SAMPLE = """Description: Daily Index of EDGAR Dissemination Feed by Form Type
Form Type   Company Name         CIK     Date Filed  File Name
---------------------------------------------------------------------------
10-K        Foo Corp             123     20260707    edgar/data/123/0000000123-26-000001.txt
4           Acme Robotics Corp   1111111 20260707    edgar/data/1111111/0001111111-26-000123.txt
4/A         Bar Inc              456     20260707    edgar/data/456/0000000456-26-000002.txt
424B5       Baz Inc              789     20260707    edgar/data/789/0000000789-26-000003.txt
4           Delta Fund 4         999     2026-07-07  edgar/data/999/0000000999-26-000004.txt
"""


def test_daily_index():
    print("[1] 每日索引解析：只收 form type 恰為 '4'（排除 4/A、424B5、10-K）")
    rows = fetch_edgar.parse_daily_index(IDX_SAMPLE)
    ok(len(rows) == 2, f"5 行索引 → 2 筆 Form 4（{len(rows)}）")
    ok(rows[0]["cik"] == "1111111" and rows[0]["path"].endswith("000123.txt"),
       "第一筆：CIK 與 path 正確")
    ok(rows[1]["company"] == "Delta Fund 4" and rows[1]["cik"] == "999",
       "公司名含數字（Delta Fund 4）不誤切 CIK；日期 YYYY-MM-DD 格式也容忍")


# ---------------------------------------------------------------------------
# [2] Form 4 XML 解析（含 SGML 全文擷取、10b5-1 checkbox、職稱）
# ---------------------------------------------------------------------------

def test_parse_form4():
    print("[2] Form 4 解析：SGML 擷取 / issuer / owner / P/S 交易 / 10b5-1")
    xml = fetch_edgar.extract_ownership_xml(_read("form4_submission.txt"))
    ok(xml is not None and xml.startswith("<ownershipDocument"),
       "SGML 全文 → ownershipDocument XML 擷取成功")
    cfo = fetch_edgar.parse_form4_xml(xml)
    ok(cfo["ticker"] == "ACME" and cfo["company"] == "Acme Robotics Corp",
       f"issuer 解析（{cfo['ticker']} / {cfo['company']}）")
    ok(cfo["issuer_cik"] == "1111111", f"issuerCik 去前導零（{cfo['issuer_cik']}）")
    ok(cfo["ten_b5_1"] is False, "aff10b5One=0 → ten_b5_1=False")
    ok(len(cfo["owners"]) == 1 and cfo["owners"][0]["title"] == "Chief Financial Officer",
       f"reportingOwner 職稱（{cfo['owners'][0]['title']}）")
    ok(cfo["owners"][0]["off"] == 1 and cfo["owners"][0]["dir"] == 0,
       "isOfficer/isDirector 旗標")
    tx = cfo["transactions"]
    ok(len(tx) == 1 and tx[0]["code"] == "P", "transactionCode=P")
    ok(tx[0]["shares"] == 10000.0 and tx[0]["price"] == 12.34,
       f"shares/price（{tx[0]['shares']}/{tx[0]['price']}）")

    plan = fetch_edgar.parse_form4_xml(_read("form4_beta_plan_p.xml"))
    ok(plan["ten_b5_1"] is True, "aff10b5One=1 → ten_b5_1=True（10b5-1 計畫單）")

    sell = fetch_edgar.parse_form4_xml(_read("form4_acme_dir_s.xml"))
    ok(sell["transactions"][0]["code"] == "S", "賣出單 transactionCode=S")
    ok(sell["owners"][0]["title"] == "Director",
       "無 officerTitle 的董事 → title 預設 Director")


# ---------------------------------------------------------------------------
# [3] 事件檔組裝（buys 逐筆、sells 按 issuer 聚合）
# ---------------------------------------------------------------------------

def _parsed(name, acc):
    text = _read(name)
    xml = fetch_edgar.extract_ownership_xml(text) or text
    return (acc, fetch_edgar.parse_form4_xml(xml))


def build_fixture_events():
    day1 = fetch_edgar.build_day_events(
        "2026-07-07", [_parsed("form4_submission.txt", "acc-cfo")], 1, 0, True)
    day2 = fetch_edgar.build_day_events(
        "2026-07-08", [_parsed("form4_acme_ceo_p.xml", "acc-ceo"),
                       _parsed("form4_beta_plan_p.xml", "acc-beta")], 2, 0, True)
    day3 = fetch_edgar.build_day_events(
        "2026-07-09", [_parsed("form4_acme_dir_s.xml", "acc-s")], 1, 0, True)
    return day1, day2, day3


def test_build_events():
    print("[3] 事件檔組裝：buys 逐筆保留、sells 聚合、10b5-1 旗標跟隨")
    day1, day2, day3 = build_fixture_events()
    ok(len(day1["buys"]) == 1 and day1["buys"][0]["usd"] == 123400.0,
       f"CFO 買入 usd=123400（{day1['buys'][0]['usd']}）")
    ok(len(day2["buys"]) == 2, "day2 兩筆買入（CEO + BETA 計畫單）")
    beta = next(b for b in day2["buys"] if b["ticker"] == "BETA")
    ok(beta["p10b51"] is True, "BETA 買入帶 p10b51=True")
    ok(len(day3["buys"]) == 0 and len(day3["sells"]) == 1, "day3 只有賣出聚合")
    ok(day3["sells"][0]["usd"] == 25000.0 and day3["sells"][0]["n_tx"] == 1,
       f"ACME 賣出聚合 25000（{day3['sells'][0]['usd']}）")


# ---------------------------------------------------------------------------
# [4] 三層漏斗：資格（集群、10b5-1）→ 否決（仙股/賣出對沖/流動性）→ 評分排序
# ---------------------------------------------------------------------------

def _buy(ticker, company, owner_cik, name, title, dir_, off, shares, price,
         filed, usd=None):
    return {"acc": f"acc-{owner_cik}", "filed": filed, "date": filed,
            "cik": ticker.lower(), "ticker": ticker, "company": company,
            "owners": [{"cik": owner_cik, "name": name, "title": title,
                        "dir": dir_, "off": off}],
            "shares": shares, "price": price,
            "usd": usd if usd is not None else round(shares * price, 2),
            "p10b51": False}


def synthetic_events():
    """GAMA（集群但賣出對沖 60%）、PENY（仙股）、DLTA（3 董事集群，乾淨）。"""
    buys = [
        _buy("GAMA", "Gamma Corp", "71", "Aaa", "Director", 1, 0, 5000, 10.0, "2026-07-07"),
        _buy("GAMA", "Gamma Corp", "72", "Bbb", "Director", 1, 0, 5000, 10.0, "2026-07-08"),
        _buy("GAMA", "Gamma Corp", "73", "Ccc", "Director", 1, 0, 5000, 10.0, "2026-07-08"),
        _buy("PENY", "Penny Mines", "81", "Ddd", "Director", 1, 0, 100000, 0.5, "2026-07-07"),
        _buy("PENY", "Penny Mines", "82", "Eee", "Director", 1, 0, 100000, 0.5, "2026-07-08"),
        _buy("DLTA", "Delta Industrials", "91", "Fff", "Director", 1, 0, 4000, 10.0, "2026-07-05"),
        _buy("DLTA", "Delta Industrials", "92", "Ggg", "Director", 1, 0, 4000, 10.0, "2026-07-06"),
        _buy("DLTA", "Delta Industrials", "93", "Hhh", "Director", 1, 0, 4000, 10.0, "2026-07-07"),
    ]
    sells = [{"cik": "gama", "ticker": "GAMA", "company": "Gamma Corp",
              "usd": 90000.0, "n_tx": 2}]
    return buys, sells


def make_price_fn(dlta_volume=100000.0, dlta_rows=True):
    """注入式價格源：ACME MA20=13.5（dip 深折）、DLTA MA20=9.5（無 dip）。"""
    june = date(2026, 6, 1)
    acme = _daily_rows(june, date(2026, 7, 7), lambda d: 13.5)
    dlta = _daily_rows(june, date(2026, 7, 7), lambda d: 9.5, volume=dlta_volume)
    table = {"ACME": acme, "DLTA": (dlta if dlta_rows else None)}

    def price_fn(ticker):
        return table.get(ticker)

    return price_fn


def run_fixture_funnel(price_fn):
    day1, day2, day3 = build_fixture_events()
    syn_buys, syn_sells = synthetic_events()
    buys = day1["buys"] + day2["buys"] + syn_buys
    sells = day3["sells"] + syn_sells
    return funnel.run_funnel(buys, sells, raw_filings=4, price_fn=price_fn)


def test_funnel():
    print("[4] 三層漏斗：集群偵測 / 10b5-1 過濾 / 否決 / 評分與排序")
    output, veto_counts, skipped = run_fixture_funnel(make_price_fn())
    stats = output["funnel_stats"]
    ok(stats["raw_filings"] == 4, f"raw_filings 透傳（{stats['raw_filings']}）")
    ok(stats["qualified_events"] == 4,
       f"資格關卡：ACME/GAMA/PENY/DLTA 成群=4（{stats['qualified_events']}）")
    tickers = [c["ticker"] for c in output["candidates"]]
    ok("BETA" not in tickers, "BETA 只有 10b5-1 計畫單 → 未成群（checkbox 過濾生效）")
    ok(veto_counts["penny"] == 1, f"PENY 仙股否決（{veto_counts['penny']}）")
    ok(veto_counts["sell_offset"] == 1,
       f"GAMA 賣出 90k > 買入 150k×50% → 否決（{veto_counts['sell_offset']}）")
    ok(stats["post_veto"] == 2 and stats["final_candidates"] == 2,
       f"否決後 2 檔（{stats['post_veto']}/{stats['final_candidates']}）")
    ok(tickers == ["ACME", "DLTA"], f"排序：ACME(7) > DLTA(3)（{tickers}）")

    acme = output["candidates"][0]
    ok(acme["cluster_size"] == 2 and len(acme["insiders"]) == 2,
       f"ACME 集群 2 人（CFO+CEO）（{acme['cluster_size']}）")
    ok(acme["total_buy_usd"] == 723400.0,
       f"ACME 買入總額 123400+600000=723400（{acme['total_buy_usd']}）")
    ok(acme["entry_price_ref"] == 12.0567,
       f"entry_price_ref=VWAP 723400/60000（{acme['entry_price_ref']}）")
    ok(acme["first_filing_date"] == "2026-07-07",
       f"first_filing_date 取最早申報日（{acme['first_filing_date']}）")
    bd = acme["score_breakdown"]
    ok(bd == {"cluster": 1, "buy_usd": 2, "title": 2, "mcap": 0, "dip": 2},
       f"ACME 分項：2人=1/≥500k=2/CFO=2/mcap N-A=0/深折=2（{bd}）")
    ok(acme["score"] == 7, f"ACME 總分 7（{acme['score']}）")

    dlta = output["candidates"][1]
    ok(dlta["score_breakdown"] == {"cluster": 2, "buy_usd": 1, "title": 0,
                                   "mcap": 0, "dip": 0},
       f"DLTA 分項：3人=2/120k=1/董事=0/0/價高於MA=0（{dlta['score_breakdown']}）")
    ok(dlta["score"] == 3, f"DLTA 總分 3（{dlta['score']}）")

    titles = sorted(i["title"] for i in acme["insiders"])
    ok(titles == ["Chief Executive Officer", "Chief Financial Officer"],
       f"insiders 職稱保留（{titles}）")


def test_funnel_liquidity_and_degradation():
    print("[5] 流動性否決與價格源降級")
    _, veto_counts, _ = run_fixture_funnel(make_price_fn(dlta_volume=1000.0))
    ok(veto_counts["illiquid"] == 1,
       f"DLTA 日均成交額 9.5k < 200k → 否決（{veto_counts['illiquid']}）")

    output, veto_counts, skipped = run_fixture_funnel(make_price_fn(dlta_rows=False))
    ok("liquidity:DLTA" in skipped and veto_counts["illiquid"] == 0,
       f"DLTA 價格抓不到 → 流動性檢查跳過不否決（skipped={skipped}）")
    ok("DLTA" in [c["ticker"] for c in output["candidates"]], "DLTA 降級後仍放行")

    output, _, skipped = run_fixture_funnel(None)  # --no-network 路徑
    ok(len(skipped) == 2, f"無網路：兩檔流動性檢查皆跳過（{len(skipped)}）")
    acme = output["candidates"][0]
    ok(acme["score_breakdown"]["dip"] == 0, "無價格 → dip=0 不給分")


# ---------------------------------------------------------------------------
# [6] 輸出契約 schema（鍵名必須與 monitor 契約完全一致）
# ---------------------------------------------------------------------------

CANDIDATES_TOP_KEYS = {"generated_at", "scan_window_days", "funnel_stats", "candidates"}
FUNNEL_STATS_KEYS = {"raw_filings", "qualified_events", "post_veto", "final_candidates"}
CANDIDATE_KEYS = {"ticker", "company", "cluster_size", "insiders", "total_buy_usd",
                  "score", "score_breakdown", "first_filing_date", "entry_price_ref"}
INSIDER_KEYS = {"name", "title"}
TRACKING_TOP_KEYS = {"updated_at", "positions"}
POSITION_KEYS = {"ticker", "signal_date", "entry_price_ref", "current_price",
                 "returns", "status"}
RETURN_KEYS = {"1w", "1m", "3m", "6m", "12m"}


def test_output_schema():
    print("[6] 輸出契約 schema：candidates_latest 與 performance_tracking 鍵名")
    output, _, _ = run_fixture_funnel(make_price_fn())
    output = json.loads(json.dumps(output))  # 走一遍 JSON 序列化（真實輸出路徑）
    ok(set(output.keys()) == CANDIDATES_TOP_KEYS,
       f"candidates 頂層鍵（{sorted(output.keys())}）")
    ok(set(output["funnel_stats"].keys()) == FUNNEL_STATS_KEYS, "funnel_stats 鍵")
    ok(output["scan_window_days"] == 7, "scan_window_days=7")
    for c in output["candidates"]:
        ok(set(c.keys()) == CANDIDATE_KEYS, f"candidate 鍵（{c['ticker']}）")
        for i in c["insiders"]:
            ok(set(i.keys()) == INSIDER_KEYS, f"insider 鍵（{i['name']}）")

    tracking, _ = track.run_tracking(output, {"positions": []}, TODAY,
                                     lambda t: None)
    tracking = json.loads(json.dumps(tracking))
    ok(set(tracking.keys()) == TRACKING_TOP_KEYS, "tracking 頂層鍵")
    ok(len(tracking["positions"]) == 2, "兩檔候選皆開倉")
    for p in tracking["positions"]:
        ok(set(p.keys()) == POSITION_KEYS, f"position 鍵（{p['ticker']}）")
        ok(set(p["returns"].keys()) == RETURN_KEYS, f"returns 鍵（{p['ticker']}）")
        ok(all(v is None for v in p["returns"].values()) and p["status"] == "tracking",
           f"新倉 returns 全 null、status=tracking（{p['ticker']}）")


# ---------------------------------------------------------------------------
# [7] 前瞻報酬回填：窗口到期判定、假日順延、完結、去重
# ---------------------------------------------------------------------------

def test_tracking_backfill():
    print("[7] 報酬回填：1w/1m 已到期回填、3m+ 未到期留 null、假日順延、完結")

    def close_fn(d):
        if d >= date(2026, 6, 30):
            return 12.0
        if d >= date(2026, 6, 7):
            return 11.0
        return 10.0

    rows = _daily_rows(date(2026, 5, 31), date(2026, 7, 10), close_fn)
    pos = {"ticker": "ACME", "signal_date": "2026-05-31", "entry_price_ref": 10.0,
           "current_price": 0, "returns": {k: None for k in RETURN_KEYS},
           "status": "tracking"}
    track.update_position(pos, rows, TODAY)
    ok(pos["returns"]["1w"] == 0.1,
       f"1w：6/7 收盤 11 / entry 10 - 1 = 0.1（{pos['returns']['1w']}）")
    ok(pos["returns"]["1m"] == 0.2, f"1m：6/30 收盤 12 → 0.2（{pos['returns']['1m']}）")
    ok(pos["returns"]["3m"] is None and pos["returns"]["12m"] is None,
       "3m/12m 未到期 → null")
    ok(pos["current_price"] == 12.0, f"current_price=最新收盤（{pos['current_price']}）")
    ok(pos["status"] == "tracking", "未完結 → status=tracking")

    # 假日順延：1w 終點 6/7 無交易日 → 取 6/8
    rows_gap = [r for r in rows if r[0] != "2026-06-07"]
    pos2 = {"ticker": "ACME", "signal_date": "2026-05-31", "entry_price_ref": 10.0,
            "current_price": 0, "returns": {k: None for k in RETURN_KEYS},
            "status": "tracking"}
    track.update_position(pos2, rows_gap, TODAY)
    ok(pos2["returns"]["1w"] == 0.1, "窗口終點無交易日 → 順延次一交易日")

    # 已到期但序列尚無資料（數據延遲）→ 留 null 下輪重試
    rows_short = [r for r in rows if r[0] <= "2026-06-20"]
    pos3 = {"ticker": "ACME", "signal_date": "2026-05-31", "entry_price_ref": 10.0,
            "current_price": 0, "returns": {k: None for k in RETURN_KEYS},
            "status": "tracking"}
    track.update_position(pos3, rows_short, TODAY)
    ok(pos3["returns"]["1m"] is None, "1m 到期但序列缺尾段 → 留 null（下輪重試）")

    # 完結：訊號 13 個月前，全部窗口回填 → completed
    rows_full = _daily_rows(date(2025, 6, 1), date(2026, 7, 1), lambda d: 20.0)
    pos4 = {"ticker": "OLDY", "signal_date": "2025-06-01", "entry_price_ref": 10.0,
            "current_price": 0, "returns": {k: None for k in RETURN_KEYS},
            "status": "tracking"}
    track.update_position(pos4, rows_full, TODAY)
    ok(all(v == 1.0 for v in pos4["returns"].values()),
       f"五窗口全回填、各 +100%（{pos4['returns']}）")
    ok(pos4["status"] == "completed", "12m 回填 → status=completed")

    # entry_price_ref=0 防除零：不動
    pos5 = {"ticker": "ZERO", "signal_date": "2026-05-31", "entry_price_ref": 0,
            "current_price": 0, "returns": {k: None for k in RETURN_KEYS},
            "status": "tracking"}
    track.update_position(pos5, rows, TODAY)
    ok(all(v is None for v in pos5["returns"].values()), "entry=0 → 不計算（防除零）")


def test_tracking_dedup():
    print("[8] 開倉去重：同 ticker 30 日內不重複、超過 30 日重新開倉")
    positions = [{"ticker": "ACME", "signal_date": "2026-06-30"}]
    ok(track.should_add(positions, "ACME", "2026-07-08") is False,
       "8 天前已開倉 → 不重複")
    ok(track.should_add(positions, "ACME", "2026-08-15") is True,
       "46 天 → 重新開倉")
    ok(track.should_add(positions, "DLTA", "2026-07-08") is True, "不同 ticker 不受限")

    cands = {"candidates": [
        {"ticker": "ACME", "first_filing_date": "2026-07-07", "entry_price_ref": 12.0},
        {"ticker": "DLTA", "first_filing_date": "2026-07-05", "entry_price_ref": 10.0},
    ]}
    existing = {"positions": [
        {"ticker": "ACME", "signal_date": "2026-07-01", "entry_price_ref": 11.0,
         "current_price": 0, "returns": {k: None for k in RETURN_KEYS},
         "status": "tracking"}]}
    tracking, stats = track.run_tracking(cands, existing, TODAY, lambda t: None)
    ok(stats["positions_new"] == 1 and len(tracking["positions"]) == 2,
       f"ACME 去重、DLTA 新增（new={stats['positions_new']}）")
    ok(stats["price_failed"] == 2, f"價格源全掛 → 記 price_failed（{stats['price_failed']}）")


# ---------------------------------------------------------------------------
# [9] 價格源解析與 symbol 轉換
# ---------------------------------------------------------------------------

STOOQ_SAMPLE = """Date,Open,High,Low,Close,Volume
2026-07-01,10.0,10.5,9.9,10.2,120000
2026-07-02,10.2,10.6,10.1,10.4,110000
2026-07-03,10.4,10.8,10.3,10.7,130000
2026-07-06,10.7,10.9,10.5,10.6,90000
2026-07-07,10.6,11.0,10.5,10.9,140000
"""


def test_price_source():
    print("[9] Stooq CSV 解析與 symbol 轉換")
    rows = track.parse_stooq_csv(STOOQ_SAMPLE)
    ok(rows is not None and len(rows) == 5, f"5 行 CSV 解析（{len(rows or [])}）")
    ok(rows[-1] == ("2026-07-07", 10.9, 140000.0), f"尾行 close/volume（{rows[-1]}）")
    ok(track.parse_stooq_csv("No data") is None, "'No data' 回應 → None")
    ok(track.parse_stooq_csv("") is None, "空回應 → None")
    ok(track.stooq_symbol("AAPL") == "aapl.us", "AAPL → aapl.us")
    ok(track.stooq_symbol("BRK.B") == "brk-b.us", "BRK.B → brk-b.us（class 股轉換）")
    adv = funnel.avg_dollar_volume(rows)
    ok(adv is not None and abs(adv - 1247800.0) < 1.0,
       f"日均成交額計算（{round(adv, 1)}）")


# ---------------------------------------------------------------------------
# [10] fetch_day 注入測試與 meta 合併
# ---------------------------------------------------------------------------

def test_fetch_day_and_meta():
    print("[10] fetch_day 注入 get_fn / 索引 404 假日 / meta 節合併")
    submission = _read("form4_submission.txt")
    idx_line = ("4           Acme Robotics Corp   1111111 20260707    "
                "edgar/data/1111111/0001111111-26-000123.txt")

    def fake_get(url, name, meta, record_ok=True, sleep=None):
        if "daily-index" in url:
            meta.record(name, url, True, status=200, record_ok=True)
            return IDX_SAMPLE.splitlines()[0] + "\n---\n" + idx_line + "\n", 200, True
        meta.record(name, url, True, status=200, record_ok=record_ok)
        return submission, 200, True

    meta = fetch_edgar.Meta()
    day = fetch_edgar.fetch_day(date(2026, 7, 7), meta, 4000, get_fn=fake_get)
    ok(day is not None and day["raw_filings"] == 1 and len(day["buys"]) == 1,
       f"fetch_day：1 索引行 → 1 buy 事件（{day['raw_filings']}）")
    ok(day["complete"] is True, "2026-07-07 早已日結 → complete=True")

    def fake_404(url, name, meta, record_ok=True, sleep=None):
        meta.record(name, url, False, status=404, error="HTTP 404")
        return None, 404, False

    meta2 = fetch_edgar.Meta()
    day2 = fetch_edgar.fetch_day(date(2026, 7, 5), meta2, 4000, get_fn=fake_404)
    ok(day2 is None and not meta2.errors, "索引 404（假日）→ 跳過且不算 error")

    with tempfile.TemporaryDirectory() as tmp:
        fetch_edgar.update_meta(tmp, "fetch", {"raw_filings": 5, "errors": []})
        fetch_edgar.update_meta(tmp, "funnel", {"funnel_stats": {"post_veto": 2}})
        meta_out = json.loads((Path(tmp) / "meta_latest.json").read_text(encoding="utf-8"))
        ok(meta_out["fetch"]["raw_filings"] == 5 and
           meta_out["funnel"]["funnel_stats"]["post_veto"] == 2,
           "meta 各節合併互不覆蓋")
        ok("updated_at" in meta_out, "meta 含 updated_at")

    ok(fetch_edgar.index_is_complete(
        date(2026, 7, 9), datetime(2026, 7, 10, 3, 0, tzinfo=timezone.utc)) is False,
       "7/10 03:00 UTC：7/9 索引未日結")
    ok(fetch_edgar.index_is_complete(
        date(2026, 7, 9), datetime(2026, 7, 10, 3, 30, tzinfo=timezone.utc)) is True,
       "7/10 03:30 UTC（CI cron 時刻）：7/9 索引已日結")


# ---------------------------------------------------------------------------
# [11] 事件檔窗口載入
# ---------------------------------------------------------------------------

def test_load_events():
    print("[11] load_events：只載掃描窗內的日檔")
    day1, day2, day3 = build_fixture_events()
    old = fetch_edgar.build_day_events("2026-06-25", [], 7, 0, True)
    with tempfile.TemporaryDirectory() as tmp:
        for day in (day1, day2, day3, old):
            fetch_edgar.write_json(Path(tmp) / f"form4_{day['date']}.json", day)
        buys, sells, raw, days = funnel.load_events(tmp, TODAY, config.SCAN_WINDOW_DAYS)
        ok(days == 3, f"窗內 3 個日檔（6/25 排除）（{days}）")
        ok(raw == 4, f"raw_filings 加總 1+2+1=4（{raw}）")
        ok(len(buys) == 3 and len(sells) == 1, f"buys=3 sells=1（{len(buys)}/{len(sells)}）")


def main():
    tests = [test_daily_index, test_parse_form4, test_build_events, test_funnel,
             test_funnel_liquidity_and_degradation, test_output_schema,
             test_tracking_backfill, test_tracking_dedup, test_price_source,
             test_fetch_day_and_meta, test_load_events]
    for t in tests:
        t()
    print(f"\nALL TESTS PASSED ({checks} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
