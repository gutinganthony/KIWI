"""tw-funnel 離線自測：fixture 解析、資格關卡、否決關卡、評分排序、輸出契約、tracking 回填。

完全離線（不碰網路、不需 requests）。結尾印 ALL TESTS PASSED (N checks)。
"""

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config  # noqa: E402
import fetch_data  # noqa: E402
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
    date, net, names = fetch_data.parse_t86_openapi(fixture("t86_openapi.json"))
    ok(date == "2026-07-10", "t86 openapi：民國日期 1150710 → 2026-07-10")
    ok(net == {"1101": 300_000, "1102": -100_000}, "t86 openapi：買賣超解析（零值排除）")
    ok(names.get("1101") == "台泥", "t86 openapi：名稱解析")

    date, net, names = fetch_data.parse_t86_rwd(fixture("t86_rwd.json"))
    ok(date == "2026-07-10" and net == {"2330": 2_500_000}, "t86 rwd 備援：日期+買賣超解析")

    close, value = fetch_data.parse_stock_day_all(fixture("stock_day_all.json"))
    ok(close["2330"] == 1050.0 and value["1101"] == 350_000_000, "STOCK_DAY_ALL：收盤/成交額")
    ok("0050" not in close, "STOCK_DAY_ALL：'--' 收盤價排除")

    months = fetch_data.parse_revenue(fixture("revenue.json"))
    ok(list(months) == ["2026-06"], "營收：民國年月 11506 → 2026-06")
    ok(months["2026-06"]["1101"]["yoy"] == 11.11, "營收：去年同月增減(%) 解析")
    ok("9998" not in months["2026-06"], "營收：空 YoY 排除")

    shares = fetch_data.parse_shares_outstanding(fixture("company_basic.json"))
    ok(shares["1101"] == 7_500_000_000, "基本資料：已發行普通股數")
    ok(shares["2330"] == 25_930_380_458, "基本資料：缺股數欄 → 實收資本額/10 退化")

    pledge = fetch_data.parse_pledge(fixture("pledge.json"))
    ok(pledge == {"1101": 0.6, "2330": 0.05}, "質押：設質/持股比率")
    ok(fetch_data.parse_pledge([{"公司代號": "1101", "持股比率": "12%"}]) == {},
       "質押：欄位假設不成立 → 空 dict（誠實降級）")


# ---------------------------------------------------------------------------
# 1b. FinMind 主源：回應包裝、四個 dataset 解析、先篩後逐檔、狀態合併
# ---------------------------------------------------------------------------

def test_finmind_envelope():
    payload = fixture("finmind_institutional.json")
    rows = fetch_data.finmind_unwrap(payload)
    ok(isinstance(rows, list) and len(rows) == 6,
       "FinMind 包裝：msg=success/status=200 → 取出 data list")
    ok(fetch_data.finmind_unwrap({"msg": "success", "status": 200, "data": []}) == [],
       "FinMind 包裝：成功但無資料 → 空 list（假日語意，與失敗有別）")
    ok(fetch_data.finmind_unwrap(
        {"msg": "Your usage is more than free quota.", "status": 402, "data": []}) is None,
       "FinMind 包裝：msg 非 success（額度用盡）→ None（視為硬失敗）")
    ok(fetch_data.finmind_unwrap({"msg": "success", "status": 200}) is None,
       "FinMind 包裝：缺 data 欄 → None")
    ok(fetch_data.finmind_unwrap(None) is None and fetch_data.finmind_unwrap([1]) is None,
       "FinMind 包裝：非 dict（HTML 阻擋頁解析物等）→ None")


def test_finmind_parsers():
    info_rows = fetch_data.finmind_unwrap(fixture("finmind_stock_info.json"))
    names, listed = fetch_data.parse_finmind_stock_info(info_rows)
    ok(names.get("1101") == "台泥" and names.get("2330") == "台積電",
       "TaiwanStockInfo：公司名解析")
    ok(listed == {"1101", "1102", "2330", "0050"}, "TaiwanStockInfo：上市集合（type=twse）")
    ok("6488" not in listed, "TaiwanStockInfo：type=tpex（上櫃）排除——v0 只做上市")
    ok("TAIEX" not in listed, "TaiwanStockInfo：非數字代號（指數）排除")

    rows = fetch_data.finmind_unwrap(fixture("finmind_institutional.json"))
    date, net = fetch_data.parse_finmind_institutional(rows)
    ok(date == "2026-07-10", "FinMind 法人：日期解析")
    ok(net == {"1101": 300_000, "1102": -100_000, "6488": 300_000},
       "FinMind 法人：只取 name 含 Investment_Trust、net=buy−sell、零值排除")
    _, net2 = fetch_data.parse_finmind_institutional(rows, listed=listed)
    ok(net2 == {"1101": 300_000, "1102": -100_000},
       "FinMind 法人：上市過濾（6488=tpex 排除）")

    price_rows = fetch_data.finmind_unwrap(fixture("finmind_price.json"))
    close, value = fetch_data.parse_finmind_price(price_rows)
    ok(close["2330"] == 1050.0 and value["1101"] == 350_000_000,
       "FinMind 價量：close/Trading_money 解析")
    ok("9998" not in close, "FinMind 價量：close=0（全日無成交）排除")
    close2, _ = fetch_data.parse_finmind_price(price_rows, listed=listed)
    ok("6488" not in close2 and "2330" in close2, "FinMind 價量：上市過濾")

    rev = fetch_data.parse_finmind_month_revenue(
        fetch_data.finmind_unwrap(fixture("finmind_month_revenue.json")))
    ok(rev == {"2025-05": 5_000_000, "2025-06": 7_200_000,
               "2026-05": 5_500_000, "2026-06": 8_640_000},
       "FinMind 月營收：revenue_year/revenue_month → YYYY-MM")
    months = fetch_data.yoy_from_revenue(rev)
    ok(months["2026-06"] == {"rev": 8_640_000, "yoy": 20.0}
       and months["2026-05"]["yoy"] == 10.0,
       "FinMind 月營收：YoY 自算（本月 20%、上月 10% → funnel 可判加速）")
    ok("2025-06" not in months and "2025-05" not in months,
       "FinMind 月營收：缺去年同期 → 該月不產 YoY（誠實不假造）")
    ok(fetch_data.yoy_from_revenue({"2026-06": 100.0, "2025-06": 0.0}) == {},
       "FinMind 月營收：去年同期 ≤0 → 不產 YoY（避免除零/失真）")


def test_chip_pool_and_state_merge():
    # 先篩後逐檔的候選池：與 funnel 籌碼關同判準（股數 OR 金額門檻、當日須買超）
    trust = {D1: {"1101": 300_000}, D2: {"1101": 300_000},
             D3: {"1101": 300_000, "2330": 30_000, "1102": 100_000, "1104": -600_000}}
    close = {"1101": 50.0, "2330": 2000.0, "1102": 30.0}
    pool = fetch_data.chip_pass_pool(trust, close, mk_cfg())
    ok(pool == ["2330", "1101"],
       f"候選池：1101 股數達標、2330 金額達標（6 千萬）；按買超市值排序（實得 {pool}）")
    ok("1102" not in pool and "1104" not in pool, "候選池：門檻不達/賣超排除")
    ok(fetch_data.chip_pass_pool({}, {}, mk_cfg()) == [], "候選池：無投信狀態 → 空池")
    # 無收盤價 → 金額門檻不可判，只用股數門檻（防禦）
    pool2 = fetch_data.chip_pass_pool({D3: {"2330": 30_000}}, {}, mk_cfg())
    ok(pool2 == [], "候選池：無收盤價 → 金額門檻不生效，僅剩股數門檻")

    # 月營收狀態合併：同月逐檔 update（FinMind 逐檔制），不整月覆蓋
    existing = {"2026-05": {"1101": {"rev": 1, "yoy": 5.0}},
                "2026-06": {"1101": {"rev": 2, "yoy": 12.0}}}
    merged = fetch_data.merge_revenue_months(
        existing, {"2026-06": {"2330": {"rev": 9, "yoy": 30.0}}}, keep=4)
    ok(merged["2026-06"] == {"1101": {"rev": 2, "yoy": 12.0},
                             "2330": {"rev": 9, "yoy": 30.0}},
       "營收合併：同月逐檔 update，不洗掉先前股票")
    ok(merged["2026-05"] == existing["2026-05"] and existing["2026-06"] == {
        "1101": {"rev": 2, "yoy": 12.0}}, "營收合併：不就地改動輸入 dict")
    trimmed = fetch_data.merge_revenue_months(
        merged, {"2026-07": {"1101": {"rev": 3, "yoy": 9.0}},
                 "2026-08": {"1101": {"rev": 3, "yoy": 9.0}}}, keep=2)
    ok(sorted(trimmed) == ["2026-07", "2026-08"], "營收合併：修剪只留最近 keep 個月")

    ok(fetch_data.month_start_n_ago("2026-07-10", 14) == "2025-05-01",
       "逐檔營收窗口起點：14 個月前月初（涵蓋上月 YoY 的去年同期）")
    ok(fetch_data.month_start_n_ago("2026-01-31", 1) == "2025-12-01",
       "月窗起點：跨年正確")


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
    s["turnover_days"] = {D3: {"9999": 99_000_000}}  # 源有數據、僅該股查無 → 個股層級保守否決
    sv, reasons = funnel.apply_vetoes(qualified, s, cfg, D3)
    ok(sv == [] and reasons == {"turnover_unknown": 1}, "個股成交額查無（源正常）→ 保守否決")

    s = copy.deepcopy(state)
    s["turnover_days"] = {}  # 源整體故障 → 流動性關降級不生效，事件放行＋記警示
    sv, reasons = funnel.apply_vetoes(qualified, s, cfg, D3)
    ok(len(sv) == 1 and "turnover_gate_inactive_source_down" in reasons,
       "成交額源整體故障 → 降級放行＋警示")

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
    # FinMind 主源設定（2026-07-10 起 TWSE 對 CI 海外 IP 阻擋 → FinMind 為主、TWSE 次源）
    ok(config.FINMIND_API_URL == "https://api.finmindtrade.com/api/v4/data",
       "FinMind 主源端點（v4 data）")
    ok(config.FINMIND_TOKEN_ENV == "FINMIND_TOKEN",
       "token 讀環境變數 FINMIND_TOKEN（可選；未設定＝匿名模式照樣能跑）")
    ok(config.FINMIND_DS_INSTITUTIONAL == "TaiwanStockInstitutionalInvestorsBuySell"
       and config.FINMIND_DS_MONTH_REVENUE == "TaiwanStockMonthRevenue"
       and config.FINMIND_DS_PRICE == "TaiwanStockPrice"
       and config.FINMIND_DS_STOCK_INFO == "TaiwanStockInfo",
       "FinMind 四個 dataset 名稱正確")
    ok(config.REVENUE_LOOKBACK_MONTHS >= 15,
       "逐檔營收窗 ≥15 月（本月＋上月 YoY 都需去年同期，+1 月吸收發布時滯）")
    ok(config.ERROR_BODY_SNIPPET_LEN == 150, "端點失敗記 body 前 150 字（診斷用）")
    # 無 token 額度守則：常態 ~53 req/日、最壞 1＋3＋3＋池上限 ≈ ~107 req/日
    worst = 1 + 2 * config.FINMIND_DAY_LOOKBACK + config.REVENUE_POOL_MAX
    ok(worst <= 150, f"最壞情境請求數 {worst} 在無 token 額度內（≤150/日）")
    ok(config.TRUST_HISTORY_KEEP_DAYS >= config.FIRST_BUY_LOOKBACK_DAYS,
       "投信歷史保留 ≥ 首次買超回看視窗")
    ok(config.TOP_N == 15, "預設輸出前 15 檔")
    src = Path(FIXTURES.parents[1], "config.py").read_text(encoding="utf-8") \
        + Path(FIXTURES.parents[1], "fetch_data.py").read_text(encoding="utf-8") \
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
    test_finmind_envelope()
    test_finmind_parsers()
    test_chip_pool_and_state_merge()
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
