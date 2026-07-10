"""tw-funnel 離線自測：fixture 解析、資格關卡、否決關卡、評分排序、輸出契約、tracking 回填。

完全離線（不碰網路、不需 requests）。結尾印 ALL TESTS PASSED (N checks)。
"""

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config  # noqa: E402
import fetch_twse  # noqa: E402
import funnel  # noqa: E402
import track_performance as tp  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
checks = 0


def ok(cond, msg):
    global checks
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    checks += 1


def fixture(name):
    with open(FIXTURES / name, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 基準 cfg / state（測試自帶門檻，不依賴 config 常數日後調整）
# ---------------------------------------------------------------------------

def mk_cfg(**over):
    cfg = funnel.default_cfg()
    cfg.update({
        "QUAL_WINDOW_DAYS": 3,
        "MIN_3D_NET_BUY_SHARES": 500_000,
        "MIN_3D_NET_BUY_VALUE_TWD": 50_000_000,
        "MIN_AVG_DAILY_TURNOVER_TWD": 30_000_000,
        "TURNOVER_AVG_WINDOW": 20,
        "VETO_UNKNOWN_TURNOVER": True,
        "PLEDGE_VETO_RATIO": 0.50,
        "JANUARY_NO_NEW_ENTRY": True,
        "JANUARY_WINDOW_LAST_DAY": 15,
        "SCORE_ACCEL_1PT": 5.0,
        "SCORE_ACCEL_2PT": 15.0,
        "SCORE_CONSEC_DAYS": 3,
        "SCORE_NETBUY_MCAP_RATIO": 0.0005,
        "SCORE_NETBUY_VALUE_TWD": 100_000_000,
        "SMALLCAP_2PT_MCAP_TWD": 30e9,
        "SMALLCAP_1PT_MCAP_TWD": 100e9,
        "FIRST_BUY_LOOKBACK_DAYS": 60,
        "TOP_N": 15,
    })
    cfg.update(over)
    return cfg


D1, D2, D3 = "2026-07-08", "2026-07-09", "2026-07-10"


def mk_state(**over):
    state = {
        "trust_days": {}, "names": {}, "turnover_days": {}, "revenue_months": {},
        "close": {}, "close_date": D3, "shares_out": {},
        "veto_lists": {"date": None, "punish": [], "attention": [], "pledge_ratio": {}},
        "fetch_meta": {"endpoint_health": {}},
    }
    state.update(over)
    return state


def rich_state():
    """六檔情境：1101 全過；1102 YoY 負；1103 減速；1104 賣超；1105 量不足；1106 缺上月YoY。"""
    trust = {
        D1: {"1101": 300_000, "1103": 800_000},
        D2: {"1101": 300_000, "1103": 100_000, "1106": 700_000},
        D3: {"1101": 300_000, "1102": 600_000, "1103": 100_000,
             "1104": -100_000, "1105": 100_000, "1106": 700_000},
    }
    turnover = {d: {t: 60_000_000 for t in
                    ("1101", "1102", "1103", "1104", "1105", "1106")} for d in (D1, D2, D3)}
    revenue = {
        "2026-05": {"1101": {"rev": 7.5e6, "yoy": 5.0}, "1102": {"rev": 1e6, "yoy": 1.0},
                    "1103": {"rev": 2e6, "yoy": 15.0}},
        "2026-06": {"1101": {"rev": 8e6, "yoy": 12.0}, "1102": {"rev": 1e6, "yoy": -3.0},
                    "1103": {"rev": 2e6, "yoy": 10.0}, "1105": {"rev": 1e6, "yoy": 20.0},
                    "1106": {"rev": 3e6, "yoy": 8.0}},
    }
    close = {"1101": 50.0, "1102": 30.0, "1103": 40.0, "1104": 25.0,
             "1105": 20.0, "1106": 60.0}
    names = {"1101": "台泥", "1102": "亞泥", "1103": "嘉泥", "1104": "環泥",
             "1105": "幸福", "1106": "信大"}
    return mk_state(trust_days=trust, turnover_days=turnover, revenue_months=revenue,
                    close=close, names=names,
                    shares_out={"1101": 100_000_000})  # 市值 50 億 → 小型股帶


# ---------------------------------------------------------------------------
# 1. fixture 解析（fetch 端純函數）
# ---------------------------------------------------------------------------

def test_parsers():
    date, net, names = fetch_twse.parse_t86_openapi(fixture("t86_openapi.json"))
    ok(date == "2026-07-10", "t86 openapi：民國日期 1150710 → 2026-07-10")
    ok(net == {"1101": 300_000, "1102": -100_000}, "t86 openapi：買賣超解析（零值排除）")
    ok(names.get("1101") == "台泥", "t86 openapi：名稱解析")

    date, net, names = fetch_twse.parse_t86_rwd(fixture("t86_rwd.json"))
    ok(date == "2026-07-10" and net == {"2330": 2_500_000}, "t86 rwd 備援：日期+買賣超解析")

    close, value = fetch_twse.parse_stock_day_all(fixture("stock_day_all.json"))
    ok(close["2330"] == 1050.0 and value["1101"] == 350_000_000, "STOCK_DAY_ALL：收盤/成交額")
    ok("0050" not in close, "STOCK_DAY_ALL：'--' 收盤價排除")

    months = fetch_twse.parse_revenue(fixture("revenue.json"))
    ok(list(months) == ["2026-06"], "營收：民國年月 11506 → 2026-06")
    ok(months["2026-06"]["1101"]["yoy"] == 11.11, "營收：去年同月增減(%) 解析")
    ok("9998" not in months["2026-06"], "營收：空 YoY 排除")

    shares = fetch_twse.parse_shares_outstanding(fixture("company_basic.json"))
    ok(shares["1101"] == 7_500_000_000, "基本資料：已發行普通股數")
    ok(shares["2330"] == 25_930_380_458, "基本資料：缺股數欄 → 實收資本額/10 退化")

    pledge = fetch_twse.parse_pledge(fixture("pledge.json"))
    ok(pledge == {"1101": 0.6, "2330": 0.05}, "質押：設質/持股比率")
    ok(fetch_twse.parse_pledge([{"公司代號": "1101", "持股比率": "12%"}]) == {},
       "質押：欄位假設不成立 → 空 dict（誠實降級）")


# ---------------------------------------------------------------------------
# 2. 資格關卡：買超＋YoY 加速須同時成立
# ---------------------------------------------------------------------------

def test_qualification():
    state, cfg = rich_state(), mk_cfg()
    qualified, stats = funnel.qualify(state, cfg, D3)
    tickers = [q["ticker"] for q in qualified]
    ok(stats["raw_filings"] == 6, "raw_filings＝當日投信有動作 6 檔")
    ok(tickers == ["1101"], "只有 1101（買超達標＋YoY>0＋加速）入池")
    q = qualified[0]
    ok(q["cum_net"] == 900_000 and q["streak"] == 3 and q["streak_start"] == D1,
       "1101：3 日累計 90 萬股、連買 3 日、段起 D1")
    ok(abs(q["accel"] - 7.0) < 1e-9, "1101：加速幅度 12−5＝7pp")
    ok(stats["accel_unknown"] == 1, "1106 缺上月 YoY → accel_unknown 計數（誠實不入池）")

    # 只有籌碼、沒有營收加速 → 不入池（組合條件缺一不可）
    s2 = copy.deepcopy(state)
    s2["revenue_months"]["2026-06"]["1101"]["yoy"] = 4.0  # 減速
    ok([q["ticker"] for q in funnel.qualify(s2, cfg, D3)[0]] == [],
       "YoY 減速 → 買超再強也不入池")
    # 只有營收加速、籌碼不達標 → 不入池
    s3 = copy.deepcopy(state)
    s3["trust_days"][D3]["1101"] = 10_000
    s3["trust_days"][D2]["1101"] = 10_000
    s3["trust_days"][D1]["1101"] = 10_000
    ok([q["ticker"] for q in funnel.qualify(s3, cfg, D3)[0]] == [],
       "累計買超低於股數與金額門檻 → 不入池")
    # 金額門檻 OR：股數不達標但金額達標（高價股）
    s4 = copy.deepcopy(state)
    s4["trust_days"] = {D3: {"1101": 40_000}}
    s4["close"]["1101"] = 2000.0  # 4 萬股 × 2000 = 8 千萬 ≥ 5 千萬
    ok([q["ticker"] for q in funnel.qualify(s4, cfg, D3)[0]] == ["1101"],
       "股數不達標但金額達標 → OR 門檻入池")
    # 當日轉賣超 → 縱使 3 日累計仍達標也不入池
    s5 = copy.deepcopy(state)
    s5["trust_days"][D3]["1101"] = -50_000
    ok([q["ticker"] for q in funnel.qualify(s5, cfg, D3)[0]] == [],
       "當日買賣超 ≤0 → 不入池")


# ---------------------------------------------------------------------------
# 3. 否決關卡：處置/注意、質押、流動性、1 月窗開關
# ---------------------------------------------------------------------------

def test_vetoes():
    state, cfg = rich_state(), mk_cfg()
    qualified, _ = funnel.qualify(state, cfg, D3)

    sv, reasons = funnel.apply_vetoes(qualified, state, cfg, D3)
    ok([c["ticker"] for c in sv] == ["1101"] and reasons == {}, "基準情境：無否決")

    s = copy.deepcopy(state)
    s["veto_lists"]["punish"] = ["1101"]
    sv, reasons = funnel.apply_vetoes(qualified, s, cfg, D3)
    ok(sv == [] and reasons == {"punish_list": 1}, "處置股 → 一票否決")

    s = copy.deepcopy(state)
    s["veto_lists"]["pledge_ratio"] = {"1101": 0.62}
    sv, reasons = funnel.apply_vetoes(qualified, s, cfg, D3)
    ok(sv == [] and reasons == {"pledge_ratio": 1}, "董監質押 >50% → 一票否決")

    s = copy.deepcopy(state)
    s["turnover_days"] = {d: {"1101": 10_000_000} for d in (D1, D2, D3)}
    sv, reasons = funnel.apply_vetoes(qualified, s, cfg, D3)
    ok(sv == [] and reasons == {"turnover_floor": 1}, "日均成交額低於下限 → 否決")

    s = copy.deepcopy(state)
    s["turnover_days"] = {}
    sv, reasons = funnel.apply_vetoes(qualified, s, cfg, D3)
    ok(sv == [] and reasons == {"turnover_unknown": 1}, "成交額不可得 → 保守否決")

    # 1 月窗：開關開 → 上半月全否決；下半月/關閉 → 放行
    jan10, jan20 = "2027-01-10", "2027-01-20"
    ok(funnel.in_january_window(jan10, cfg) is True, "1/10 在作帳反轉窗內")
    ok(funnel.in_january_window(jan20, cfg) is False, "1/20 不在窗內")
    ok(funnel.in_january_window(jan10, mk_cfg(JANUARY_NO_NEW_ENTRY=False)) is False,
       "config 開關關閉 → 窗不生效")
    sv, reasons = funnel.apply_vetoes(qualified, state, cfg, jan10)
    ok(sv == [] and reasons == {"january_window": 1}, "1 月上半月 → 不進新倉")
    sv, _ = funnel.apply_vetoes(qualified, state, mk_cfg(JANUARY_NO_NEW_ENTRY=False), jan10)
    ok(len(sv) == 1, "開關關閉 → 1 月上半月照常放行")


# ---------------------------------------------------------------------------
# 4. 評分與排序
# ---------------------------------------------------------------------------

def test_scoring():
    state, cfg = rich_state(), mk_cfg()
    qualified, _ = funnel.qualify(state, cfg, D3)
    score, bd = funnel.score_candidate(qualified[0], state, cfg)
    # 1101：accel 7pp→1；連買3日+買超/市值 4500萬/50億=0.9%→2；市值50億<300億→2；
    # 60 日內首次買超（D1 之前無紀錄）→2 ⇒ 總分 7
    ok(bd == {"revenue_accel": 1, "trust_strength": 2, "small_cap": 2, "first_time_buy": 2},
       f"1101 評分明細（實得 {bd}）")
    ok(score == 7, "1101 總分 7")

    # 加速幅度分級
    c = dict(qualified[0], accel=20.0)
    ok(funnel.score_candidate(c, state, cfg)[1]["revenue_accel"] == 2, "加速 ≥15pp → 2 分")
    c = dict(qualified[0], accel=2.0)
    ok(funnel.score_candidate(c, state, cfg)[1]["revenue_accel"] == 0, "加速 <5pp → 0 分")

    # 非首次買超：段前 60 日內有買超日 → 0 分
    s = copy.deepcopy(state)
    s["trust_days"]["2026-06-20"] = {"1101": 50_000}
    ok(funnel.score_candidate(qualified[0], s, cfg)[1]["first_time_buy"] == 0,
       "60 日內曾買超 → 非首次，0 分")

    # 市值不可得 → 小型股 0 分、強度退化用金額門檻
    s = copy.deepcopy(state)
    s["shares_out"] = {}
    _, bd = funnel.score_candidate(qualified[0], s, cfg)
    ok(bd["small_cap"] == 0, "市值不可得 → 小型股帶 0 分（誠實不給分）")
    ok(bd["trust_strength"] == 1, "市值不可得＋金額 4500 萬 <1 億 → 強度僅連買 1 分")

    # 大市值 → 小型股 0 分
    s = copy.deepcopy(state)
    s["shares_out"] = {"1101": 4_000_000_000}  # 市值 2000 億
    ok(funnel.score_candidate(qualified[0], s, cfg)[1]["small_cap"] == 0,
       "市值 2000 億 → 小型股帶 0 分")


def test_ranking_and_topn():
    """三檔同過關卡：驗證 分數 desc → 3 日買超金額 desc 的排序與 TOP_N 截斷。"""
    trust = {D3: {"1101": 600_000, "1102": 600_000, "1103": 600_000}}
    revenue = {"2026-05": {"1101": {"rev": 1, "yoy": 5.0}, "1102": {"rev": 1, "yoy": 5.0},
                           "1103": {"rev": 1, "yoy": 5.0}},
               "2026-06": {"1101": {"rev": 1, "yoy": 25.0},   # accel 20 → 2 分
                           "1102": {"rev": 1, "yoy": 12.0},   # accel 7 → 1 分
                           "1103": {"rev": 1, "yoy": 12.0}}}  # accel 7 → 1 分
    close = {"1101": 50.0, "1102": 80.0, "1103": 40.0}  # 1102 買超金額 > 1103
    turnover = {D3: {t: 60_000_000 for t in ("1101", "1102", "1103")}}
    state = mk_state(trust_days=trust, revenue_months=revenue, close=close,
                     turnover_days=turnover)
    cfg = mk_cfg()
    doc, _ = funnel.build_output(state, cfg, now_utc="2026-07-10T10:00:00Z")
    order = [c["ticker"] for c in doc["candidates"]]
    ok(order == ["1101", "1102", "1103"], f"排序：分數 desc → 買超金額 desc（實得 {order}）")
    scores = [c["score"] for c in doc["candidates"]]
    ok(scores == sorted(scores, reverse=True), "分數單調不增")

    doc2, _ = funnel.build_output(state, mk_cfg(TOP_N=2), now_utc="2026-07-10T10:00:00Z")
    ok(len(doc2["candidates"]) == 2 and doc2["funnel_stats"]["final_candidates"] == 2,
       "TOP_N=2 → 只輸出前 2 檔")
    ok(doc2["funnel_stats"]["post_veto"] == 3, "post_veto 不受 TOP_N 截斷影響")


# ---------------------------------------------------------------------------
# 5. 輸出契約：鍵名與 monitor 統一 schema 完全一致
# ---------------------------------------------------------------------------

def test_output_schema():
    state, cfg = rich_state(), mk_cfg()
    doc, meta = funnel.build_output(state, cfg, now_utc="2026-07-10T10:00:00Z")

    ok(set(doc.keys()) == {"generated_at", "scan_window_days", "funnel_stats", "candidates"},
       "candidates_latest 頂層鍵名與契約完全一致")
    ok(set(doc["funnel_stats"].keys())
       == {"raw_filings", "qualified_events", "post_veto", "final_candidates"},
       "funnel_stats 鍵名與契約完全一致")
    c = doc["candidates"][0]
    ok(set(c.keys()) == {"ticker", "company", "cluster_size", "insiders", "total_buy_usd",
                         "tw_fields", "score", "score_breakdown", "first_filing_date",
                         "entry_price_ref"},
       "candidate 鍵名與契約完全一致")
    ok(set(c["tw_fields"].keys()) == {"trust_net_buy_shares", "trust_consecutive_days",
                                      "revenue_yoy", "revenue_yoy_accel"},
       "tw_fields 鍵名與契約完全一致")
    ok(c["cluster_size"] is None and c["insiders"] is None and c["total_buy_usd"] is None,
       "美股專屬欄位在台股置 null")
    ok(c["ticker"] == "1101" and c["company"] == "台泥" and c["entry_price_ref"] == 50.0
       and c["first_filing_date"] == D1, "候選內容正確（票/名/參考價/事件起日）")
    ok(doc["funnel_stats"] == {"raw_filings": 6, "qualified_events": 1,
                               "post_veto": 1, "final_candidates": 1},
       "漏斗統計數字正確")
    ok(json.dumps(doc, ensure_ascii=False), "輸出可 JSON 序列化")

    ok(meta["market"] == "TW" and meta["as_of_trading_day"] == D3, "meta：市場/交易日")
    ok(any("director_transfer_not_wired" in t for t in meta["todo_not_wired"])
       and any("tpex_otc_not_wired" in t for t in meta["todo_not_wired"]),
       "meta：董監申讓/上櫃 未接線誠實標註 TODO")
    ok(any("pledge_data_unavailable" in d for d in meta["degradations"]),
       "meta：質押數據不可得 → 質押否決不生效誠實標註")
    ok(any(w.startswith("funnel_starved") for w in meta["warnings"]),
       "meta：候選 <10 → 漏斗饑餓警告（設計文件 §3）")

    # 完全空狀態（端點全掛首跑）→ 空殼輸出＋誠實 meta，不 crash
    doc0, meta0 = funnel.build_output(mk_state(close_date=None), cfg,
                                      now_utc="2026-07-10T10:00:00Z")
    ok(doc0["candidates"] == [] and doc0["funnel_stats"]["raw_filings"] == 0,
       "空狀態 → 空候選＋零統計")
    ok(any("no_trust_data" in d for d in meta0["degradations"]), "空狀態 → meta 誠實標註")


# ---------------------------------------------------------------------------
# 6. tracking 回填：假價格序列驗 1w/1m 計算與 null
# ---------------------------------------------------------------------------

def test_tracking():
    tracking = {"updated_at": None,
                "windows_days": {"1w": 7, "1m": 30, "3m": 91, "6m": 182, "12m": 365},
                "positions": []}
    cand_doc = {"candidates": [
        {"ticker": "1101", "company": "台泥", "first_filing_date": D1,
         "entry_price_ref": 100.0, "score": 7},
        {"ticker": "1102", "company": "亞泥", "first_filing_date": D3,
         "entry_price_ref": None, "score": 3},   # 無參考價 → 永遠 null
    ]}
    added = tp.register_new_entries(tracking, cand_doc, D3)
    ok(added == 2 and len(tracking["positions"]) == 2, "新事件登記 2 筆")
    ok(tp.register_new_entries(tracking, cand_doc, D3) == 0,
       "同事件（ticker×first_filing_date）重跑不重複登記")
    e = tracking["positions"][0]
    ok(e["signal_date"] == D3 and e["returns"] == {w: None for w in
       ("1w", "1m", "3m", "6m", "12m")}, "登記時全窗 null")
    # monitor 統一契約（同美股）：positions 陣列＋這些鍵名
    for key in ("ticker", "signal_date", "entry_price_ref", "current_price",
                "status", "returns"):
        ok(key in e, f"position 含 monitor 契約鍵 '{key}'")

    # 未滿窗（+5 日）→ 不回填
    ok(tp.backfill(tracking, {"1101": 105.0}, "2026-07-15") == 0, "未滿 1w → 不回填")
    ok(e["current_price"] == 105.0 and e["current_price_date"] == "2026-07-15",
       "current_price 仍每日更新")
    # 滿 1w（+7 日）→ 填 1w，其餘 null
    ok(tp.backfill(tracking, {"1101": 103.0}, "2026-07-17") == 1, "滿 1w → 回填 1 窗")
    ok(e["returns"]["1w"] == 0.03 and e["returns"]["1m"] is None,
       "1w 報酬 = 103/100−1 = 3%；1m 仍 null")
    ok(e["return_fill_dates"]["1w"] == "2026-07-17", "回填日記錄")
    # 已填的窗不重算（用後續價格驗證不變）
    tp.backfill(tracking, {"1101": 200.0}, "2026-07-18")
    ok(e["returns"]["1w"] == 0.03, "已填窗不被後續價格覆寫")
    # 滿 1m（+31 日）→ 填 1m
    ok(tp.backfill(tracking, {"1101": 110.0}, "2026-08-10") == 1, "滿 1m → 回填 1m")
    ok(e["returns"]["1m"] == 0.10 and e["returns"]["3m"] is None, "1m=10%；3m 仍 null")
    # 當日無該票價格（停牌/下市）→ 維持 null，不 crash
    ok(tp.backfill(tracking, {}, "2026-10-15") == 0, "無價格 → 維持 null 之後重試")
    # 無 entry_price_ref 的事件永遠不回填
    e2 = tracking["positions"][1]
    tp.backfill(tracking, {"1102": 50.0}, "2027-08-01")
    ok(all(v is None for v in e2["returns"].values()) and e2["current_price"] == 50.0,
       "無參考價 → 全窗 null（誠實），但 current_price 照更新")
    ok(e["status"] == "tracking", "未滿全窗 → status=tracking")
    # 全窗補滿 → completed（拉到 12m 之後）
    tp.backfill(tracking, {"1101": 150.0}, "2027-07-20")
    ok(e["status"] == "completed" and all(v is not None for v in e["returns"].values()),
       "全窗回填 → status=completed")


# ---------------------------------------------------------------------------
# 7. config 完整性（workflow 依賴的常數都在）
# ---------------------------------------------------------------------------

def test_config_sanity():
    ok(config.PERFORMANCE_WINDOWS_DAYS == {"1w": 7, "1m": 30, "3m": 91, "6m": 182, "12m": 365},
       "追蹤視窗 1w/1m/3m/6m/12m")
    ok(config.DIRECTOR_TRANSFER_URL is None, "董監申讓 v0 未接線（None，誠實）")
    ok(config.TRUST_HISTORY_KEEP_DAYS >= config.FIRST_BUY_LOOKBACK_DAYS,
       "投信歷史保留 ≥ 首次買超回看視窗")
    ok(config.TOP_N == 15, "預設輸出前 15 檔")
    src = Path(FIXTURES.parents[1], "config.py").read_text(encoding="utf-8") \
        + Path(FIXTURES.parents[1], "fetch_twse.py").read_text(encoding="utf-8") \
        + Path(FIXTURES.parents[1], "funnel.py").read_text(encoding="utf-8") \
        + Path(FIXTURES.parents[1], "track_performance.py").read_text(encoding="utf-8")
    # 唯讀驗證：不得出現金鑰/下單類 code token（宣告句裡的中文「下單」不算）
    for bad in ("api_key", "apikey", "secret", "password", "private_key",
                "place_order", "createorder", "submit_order"):
        ok(bad not in src.lower(), f"原始碼無 '{bad}'（唯讀、無金鑰、無下單）")
    ok("requests.post" not in src and "requests.put" not in src
       and "requests.delete" not in src, "只有唯讀 GET，無任何寫入請求")


def main():
    test_parsers()
    test_qualification()
    test_vetoes()
    test_scoring()
    test_ranking_and_topn()
    test_output_schema()
    test_tracking()
    test_config_sanity()
    print(f"ALL TESTS PASSED ({checks} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
