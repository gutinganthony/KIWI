#!/usr/bin/env python3
"""poly-observer 離線自測：不碰網路，餵 fixtures 驗證分類與報告產生。

用法（在 projects/poly-observer 下）：
    python3 tests/test_offline.py
"""

import json
import sys
import tempfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

import analyze  # noqa: E402
import verify_smart_money as vsm  # noqa: E402
import track_wallet  # noqa: E402
import simulate_copy  # noqa: E402
import shadow_bot  # noqa: E402

FIXTURES = TESTS_DIR / "fixtures"
SNAP_DATE = "2026-07-01"  # fixtures 的時間軸終點（recent-30d 視窗右端）

EXPECTED = {
    "wallet_consistent.json": "consistent_winner",
    "wallet_one_hit.json": "one_hit",
    "wallet_mm_bot.json": "mm_bot_like",
    "wallet_insufficient.json": "insufficient_data",
    "wallet_dormant.json": "dormant",
}

checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        print(f"FAIL: {msg}")
        raise AssertionError(msg)
    print(f"  ok: {msg}")


def test_classification():
    print("[1] 分類器：4 個 fixture 逐一分類")
    for fname, expected in EXPECTED.items():
        wallet = json.loads((FIXTURES / fname).read_text(encoding="utf-8"))
        metrics = vsm.compute_metrics(wallet, SNAP_DATE)
        label, reasons = vsm.classify(metrics)
        ok(label == expected,
           f"{fname} → {label}（預期 {expected}）reasons={reasons[:1]}")
    return


def test_metrics_sanity():
    print("[2] 指標 sanity：consistent fixture 的各項數值")
    wallet = json.loads((FIXTURES / "wallet_consistent.json").read_text(encoding="utf-8"))
    m = vsm.compute_metrics(wallet, SNAP_DATE)
    ok(m["pnl_source"] == "curve", f"pnl_source=curve（{m['pnl_source']}）")
    ok(m["total_pnl"] == 13000, f"total_pnl=13000（{m['total_pnl']}）")
    ok(m["active_months"] == 4, f"active_months=4（{m['active_months']}）")
    ok(m["positive_month_ratio"] == 1.0, f"正月比率=1.0（{m['positive_month_ratio']}）")
    ok(m["trades_per_month"] == 6.0, f"頻率=6.0 筆/月（{m['trades_per_month']}）")
    ok(m["max_drawdown_pct"] is not None and m["max_drawdown_pct"] < 0.5,
       f"回撤 <50%（{m['max_drawdown_pct']}）")
    ok(m["top_category"] == "politics", f"主類別=politics（{m['top_category']}）")
    ok(m["avg_hold_hours"] is not None and m["avg_hold_hours"] > 1,
       f"平均持有 >1 小時（{m['avg_hold_hours']}）")

    one_hit = json.loads((FIXTURES / "wallet_one_hit.json").read_text(encoding="utf-8"))
    mo = vsm.compute_metrics(one_hit, SNAP_DATE)
    ok(mo["top_category"] == "esports", f"one_hit 主類別=esports（{mo['top_category']}）")
    ok(mo["max_drawdown_pct"] is not None and mo["max_drawdown_pct"] > 0.9,
       f"one_hit 回撤 >90%（{mo['max_drawdown_pct']}）")

    bot = json.loads((FIXTURES / "wallet_mm_bot.json").read_text(encoding="utf-8"))
    mb = vsm.compute_metrics(bot, SNAP_DATE)
    ok(mb["pnl_source"] == "activity_approx" and mb["low_confidence"],
       f"mm_bot 走 activity 近似＋低信心旗標（{mb['pnl_source']}）")


def test_reports(tmp):
    print("[3] verify 報告產生：組 snapshot 目錄 → md/json 落地")
    snap_dir = tmp / "snapshots" / SNAP_DATE
    wallets_dir = snap_dir / "wallets"
    wallets_dir.mkdir(parents=True)
    for fname in EXPECTED:
        wallet = json.loads((FIXTURES / fname).read_text(encoding="utf-8"))
        (wallets_dir / f"{wallet['address']}.json").write_text(
            json.dumps(wallet, ensure_ascii=False), encoding="utf-8")
    (snap_dir / "meta.json").write_text(json.dumps({
        "date": SNAP_DATE,
        "endpoint_health": [
            {"name": "leaderboard[1m]", "ok": True, "status": 200,
             "url": "https://lb-api.polymarket.com/leaderboard?window=1m&rankType=pnl&limit=50"},
            {"name": "pnl[0x3333…]", "ok": False, "status": 404, "error": "HTTP 404; body=not found",
             "url": "https://user-pnl-api.polymarket.com/user-pnl?user_address=0x3333&interval=all&fidelity=1d"},
        ]}), encoding="utf-8")

    report_dir = tmp / "reports"
    payload = vsm.run_verification(snap_dir, report_dir)

    md_path = report_dir / f"verification_{SNAP_DATE}.md"
    json_path = report_dir / f"verification_{SNAP_DATE}.json"
    ok(md_path.is_file() and md_path.stat().st_size > 500, f"md 報告存在且非空（{md_path.name}）")
    reparsed = json.loads(json_path.read_text(encoding="utf-8"))
    ok(reparsed["classification_counts"] == payload["classification_counts"],
       "json 報告可重新解析且計數一致")
    expected_counts = {"consistent_winner": 1, "one_hit": 1, "dormant": 1,
                       "mm_bot_like": 1, "insufficient_data": 1}
    ok(payload["classification_counts"] == expected_counts,
       f"分類統計={expected_counts}")
    gt = payload["ground_truth"]
    ok(len(gt) == 1 and gt[0]["ok"] and gt[0]["actual"] == "dormant",
       "ground-truth 種子（xdd07070）如預期分類為 dormant")
    ok("弱存在" in payload["verdict"], f"裁決=弱存在（1 個 winner）：{payload['verdict']}")
    md_text = md_path.read_text(encoding="utf-8")
    for section in ("端點健康", "分類統計", "consistent_winner 明細",
                    "Ground-truth 校驗", "裁決", "倖存者偏差"):
        ok(section in md_text, f"md 含「{section}」段")
    return snap_dir, report_dir


def test_analyze(tmp, snap_dir, report_dir):
    print("[4] analyze 觀察器：首日 initialized ＋ watchlist 落地")
    watchlist_path = tmp / "watchlist.json"
    daily_path, watchlist = analyze.run_analyze(snap_dir, report_dir, watchlist_path)
    ok(watchlist is not None, "analyze 正常執行（讀到 verification json）")
    active = [a for a, e in watchlist.items() if e.get("active")]
    ok(active == ["0x1111111111111111111111111111111111111111"],
       f"watchlist active=consistent fixture（{active}）")
    daily_text = daily_path.read_text(encoding="utf-8")
    ok("initialized" in daily_text, "首日報告含 initialized")
    ok(len(watchlist[active[0]]["history"]) == 1, "history 有 1 筆逐日快照")


def test_track_wallet(tmp):
    print("[5] track_wallet：dossier 產生＋open positions 列出＋new-position delta＋timeline 落地")
    base = json.loads((FIXTURES / "wallet_consistent.json").read_text(encoding="utf-8"))
    addr = base["address"]
    # 注入兩個未平倉部位（既有 fixture 無 positions，以此驗證持倉列出路徑）
    base["positions"] = [
        {"title": "Will Trump win the 2028 Republican nomination?",
         "slug": "trump-2028-republican-nominee", "outcome": "Yes",
         "size": 700, "currentValue": 350.0, "avgPrice": 0.42, "conditionId": "cond-3c"},
        {"title": "Will the Senate pass the budget bill by August?",
         "slug": "senate-budget-bill-august", "outcome": "No",
         "size": 400, "currentValue": 264.0, "avgPrice": 0.55, "conditionId": "cond-4b"},
    ]
    snap_dir = tmp / "snapshots" / SNAP_DATE
    wallets_dir = snap_dir / "wallets"
    wallets_dir.mkdir(parents=True, exist_ok=True)
    (wallets_dir / f"{addr}.json").write_text(
        json.dumps(base, ensure_ascii=False), encoding="utf-8")
    tracked_root = tmp / "tracked"

    dossier = track_wallet.run_track_wallet(addr, snap_dir, tracked_root)
    ok(dossier is not None, "track_wallet 正常執行並回傳 dossier")
    ok(dossier["n_open_positions"] == 2, f"列出 2 個未平倉部位（{dossier['n_open_positions']}）")
    ok(dossier["initialized"] is True, "首次追蹤 new-position delta 標記 initialized")
    ok(dossier["classification"] == "consistent_winner",
       f"分類重用 verify.classify（{dossier['classification']}）")

    tdir = tracked_root / addr
    ok((tdir / f"dossier_{SNAP_DATE}.md").is_file()
       and (tdir / f"dossier_{SNAP_DATE}.json").is_file(), "dossier md/json 落地")
    ok((tdir / "latest_raw.json").is_file(), "原始資料持久化到 latest_raw.json")
    md_text = (tdir / f"dossier_{SNAP_DATE}.md").read_text(encoding="utf-8")
    ok("senate-budget-bill-august" in md_text or "Senate pass the budget" in md_text,
       "md dossier 含未平倉部位明細")
    timeline_lines = (tdir / "timeline.jsonl").read_text(encoding="utf-8").strip().splitlines()
    ok(len(timeline_lines) == 1, f"timeline.jsonl 落地 1 行（{len(timeline_lines)}）")
    row = json.loads(timeline_lines[0])
    ok(row["n_open_positions"] == 2 and row["new_positions_count"] == 0,
       "timeline 行含持倉數與新建倉數")

    # 第二次執行：改變持倉集合，驗證 new/disappeared delta（不再 initialized）
    base["positions"] = [
        base["positions"][0],  # 保留 trump（不變）
        {"title": "New market E", "slug": "new-market-e", "outcome": "Yes",
         "size": 100, "currentValue": 50.0, "avgPrice": 0.5, "conditionId": "cond-e"},
    ]
    (wallets_dir / f"{addr}.json").write_text(
        json.dumps(base, ensure_ascii=False), encoding="utf-8")
    dossier2 = track_wallet.run_track_wallet(addr, snap_dir, tracked_root)
    ok(dossier2["initialized"] is False, "第二次執行不再 initialized")
    new_keys = {p["key"] for p in dossier2["new_positions"]}
    gone_keys = {p["key"] for p in dossier2["disappeared_positions"]}
    ok("new-market-e" in new_keys, f"偵測到新建倉 new-market-e（{new_keys}）")
    ok("senate-budget-bill-august" in gone_keys,
       f"偵測到消失持倉 senate-budget-bill-august（{gone_keys}）")


def test_simulate_copy():
    print("[6] simulate_copy：錢包原始 PnL 手算對得上＋摩擦侵蝕＋情境單調（可靠案例）")
    wallet = json.loads((FIXTURES / "wallet_sim.json").read_text(encoding="utf-8"))
    result = simulate_copy.simulate(wallet, SNAP_DATE)

    # wallet_sim：7 天、未截斷、4 市場皆完整 round-trip、含明確輸贏 → 應可靠
    ok(result["reliable"] is True,
       f"wallet_sim 為可靠案例 reliable==True（reasons={result['unreliable_reasons']}）")

    ww = result["wallet_window"]
    # (a) 錢包已實現 PnL（只算 round-trip；4 市場全為 round-trip）：
    #     回收 220（A100+B10+C110+D0）− 成本 170（40+50+60+20）= 50
    ok(abs(ww["realized_pnl"] - 50.0) < 0.01,
       f"錢包同窗已實現 PnL=50（手算對照，只算 round-trip）：{ww['realized_pnl']}")
    ok(ww["curve_divergence_warning"] is None,
       "重建 PnL 與 pnl 曲線同窗變動一致（無示警）")
    ok(ww["roi"] is not None and ww["roi"] > 0, f"錢包同窗 ROI 為正（{ww['roi']}）")

    real_fixed = result["matrix"]["realistic"]["fixed"]
    # (b) 加滑點後跟單者 ROI（每投入 $1 報酬率）< 錢包同窗 ROI —— 摩擦必然侵蝕
    ok(real_fixed["follower_roi"] < ww["roi"],
       f"跟單者 ROI {real_fixed['follower_roi']} < 錢包 ROI {ww['roi']}（摩擦侵蝕）")

    opt = result["matrix"]["optimistic"]["fixed"]["follower_net_pnl"]
    pess = result["matrix"]["pessimistic"]["fixed"]["follower_net_pnl"]
    # (c) pessimistic 情境比 optimistic 差
    ok(pess < opt, f"pessimistic 淨 PnL {pess} < optimistic 淨 PnL {opt}")


def test_simulate_copy_unreliable():
    print("[7] simulate_copy：高頻截斷錢包（贏家倖存者偏誤）→ 誠實拒答")
    wallet = json.loads((FIXTURES / "wallet_hyperactive.json").read_text(encoding="utf-8"))
    result = simulate_copy.simulate(wallet, SNAP_DATE)

    # (a) 整體判定不可靠
    ok(result["reliable"] is False,
       f"高頻截斷錢包 reliable==False（{result['reliable']}）")

    reasons = "\n".join(result["unreliable_reasons"])
    # (b) 至少命中原因 (b) 幽靈利潤主導 與 (d) 結算全為贏家
    ok("幽靈利潤主導" in reasons,
       f"命中原因(b) 結算-only 幽靈利潤主導（{result['unreliable_reasons']}）")
    ok("輸家不產生 REDEEM" in reasons,
       f"命中原因(d) 結算全為贏家（{result['unreliable_reasons']}）")

    md = simulate_copy.build_markdown(result)
    # (c) 報告含「無法可靠模擬」且絕不含「淨正 ✅」
    ok("無法可靠模擬" in md, "報告含醒目拒答區塊「無法可靠模擬」")
    ok("淨正 ✅" not in md, "報告不含「淨正 ✅」（不誤導為可獲利）")
    # (d) 報告含固定的「頻率 × 延遲可行性」區塊
    ok("頻率 × 延遲可行性" in md, "報告含「頻率 × 延遲可行性」區塊")

    # capture 防呆：不可靠 → 每格 capture 皆標記偏誤、md 印「—（資料偏誤）」
    all_biased = all(result["matrix"][s][m]["capture_biased"]
                     for s in ("optimistic", "realistic", "pessimistic")
                     for m in ("fixed", "proportional"))
    ok(all_biased, "不可靠時所有格 capture_biased==True")
    ok("—（資料偏誤）" in md, "md 的捕獲率格印「—（資料偏誤）」")


def test_shadow_dedup():
    print("[8] shadow_bot：新交易去重（重複 activity 只記一次、非 TRADE 忽略）")
    ev_tx = {"type": "TRADE", "transactionHash": "0xaaa", "timestamp": 1751328000,
             "asset": "111", "side": "BUY", "size": 100, "price": 0.5}
    ev_no_tx = {"type": "TRADE", "timestamp": 1751328005, "asset": "222",
                "side": "SELL", "size": 50, "price": 0.6}  # 無 txhash → 組合鍵
    redeem = {"type": "REDEEM", "timestamp": 1751328010, "asset": "333", "size": 10}
    seen = set()
    first = shadow_bot.detect_new_trades([ev_tx, ev_no_tx, redeem], seen)
    ok(len(first) == 2, f"首輪偵測 2 筆 TRADE（{len(first)}），REDEEM 不計")
    second = shadow_bot.detect_new_trades([ev_tx, ev_no_tx, redeem], seen)
    ok(second == [], f"重複餵同一列表 → 0 筆新交易（{len(second)}）")
    ev_later = dict(ev_no_tx, timestamp=1751328099)  # 組合鍵欄位改變 → 新交易
    third = shadow_bot.detect_new_trades([ev_tx, ev_no_tx, ev_later], seen)
    ok(len(third) == 1 and third[0]["timestamp"] == 1751328099,
       f"時間戳不同的無 txhash 交易視為新（{len(third)}）")


def test_shadow_book_and_drift():
    print("[9] shadow_bot：book 解析＋adverse_drift 方向正確")
    book = json.loads((FIXTURES / "book_sample.json").read_text(encoding="utf-8"))
    parsed = shadow_bot.parse_book(book)
    # fixture 兩側刻意不排序：best_bid=最高買價 0.55、best_ask=最低賣價 0.57
    ok(parsed["best_bid"] == 0.55 and parsed["best_ask"] == 0.57,
       f"best_bid=0.55 / best_ask=0.57（{parsed['best_bid']}/{parsed['best_ask']}）")
    ok(abs(parsed["mid"] - 0.56) < 1e-9 and abs(parsed["spread"] - 0.02) < 1e-9,
       f"mid=0.56、spread=0.02（{parsed['mid']}/{parsed['spread']}）")
    ok(abs(parsed["bid_depth_usd"] - 165.0) < 0.01
       and abs(parsed["ask_depth_usd"] - 114.0) < 0.01,
       f"第一檔 USD 深度 bid=165 / ask=114（{parsed['bid_depth_usd']}/{parsed['ask_depth_usd']}）")
    ok(shadow_bot.parse_book({"bids": [], "asks": []}) is None
       and shadow_bot.parse_book("garbage") is None, "空書/垃圾輸入 → None")

    # BUY：跟單者吃 best_ask，錢包成交 0.55 → drift=(0.57-0.55)/0.55>0＝買更貴
    buy = shadow_bot.follower_metrics("BUY", 0.55, parsed)
    ok(buy["follower_entry_px"] == 0.57, f"BUY 進場價=best_ask（{buy['follower_entry_px']}）")
    ok(abs(buy["adverse_drift"] - 0.036364) < 1e-6,
       f"BUY adverse_drift=+3.64%（{buy['adverse_drift']}）")
    ok(abs(buy["depth_at_best"] - 114.0) < 0.01
       and buy["fillable_usd_at_best"] == buy["depth_at_best"],
       f"BUY depth 取 ask 側第一檔（{buy['depth_at_best']}）")

    # SELL：跟單者砸 best_bid，錢包成交 0.57 → drift 取反向後 >0＝賣更便宜
    sell = shadow_bot.follower_metrics("SELL", 0.57, parsed)
    ok(sell["follower_entry_px"] == 0.55, f"SELL 進場價=best_bid（{sell['follower_entry_px']}）")
    ok(abs(sell["adverse_drift"] - 0.035088) < 1e-6,
       f"SELL adverse_drift=+3.51%（{sell['adverse_drift']}）")
    ok(abs(sell["depth_at_best"] - 165.0) < 0.01,
       f"SELL depth 取 bid 側第一檔（{sell['depth_at_best']}）")

    none_case = shadow_bot.follower_metrics("BUY", 0.55, None)
    ok(all(v is None for v in none_case.values()), "book 不可用 → 衍生欄位全 None")


def test_shadow_summary_stats():
    print("[10] shadow_bot：摘要統計 median/p90/可成交比例正確")
    rows = []
    for i in range(1, 11):  # 奇數 BUY、偶數 SELL；depth 30..300
        rows.append({"detect_lag_sec": float(i),
                     "side": "BUY" if i % 2 else "SELL",
                     "adverse_drift": 0.01 * i, "spread": 0.02,
                     "depth_at_best": 30.0 * i, "fillable_usd_at_best": 30.0 * i,
                     "book_unavailable": False})
    rows.append({"detect_lag_sec": 11.0, "side": "BUY", "adverse_drift": None,
                 "spread": None, "depth_at_best": None,
                 "fillable_usd_at_best": None, "book_unavailable": True})
    st = shadow_bot.summarize_rows(rows, fixed_usd=50.0)
    ok(st["n_detected"] == 11 and st["n_book_ok"] == 10 and st["n_book_unavailable"] == 1,
       f"計數：11 偵測 / 10 book 可用 / 1 不可用（{st['n_detected']}/{st['n_book_ok']}）")
    lag = st["detect_lag_sec"]
    ok(lag["median"] == 6.0 and lag["p90"] == 10.0 and lag["n"] == 11,
       f"lag median=6.0、p90=10.0（nearest-rank）（{lag['median']}/{lag['p90']}）")
    b, s = st["adverse_drift"]["BUY"], st["adverse_drift"]["SELL"]
    ok(abs(b["median"] - 0.05) < 1e-9 and abs(b["p90"] - 0.09) < 1e-9 and b["n"] == 5,
       f"BUY drift median=0.05、p90=0.09、n=5（{b['median']}/{b['p90']}/{b['n']}）")
    ok(abs(s["median"] - 0.06) < 1e-9 and abs(s["p90"] - 0.10) < 1e-9 and s["n"] == 5,
       f"SELL drift median=0.06、p90=0.10、n=5（{s['median']}/{s['p90']}/{s['n']}）")
    ok(abs(st["spread"]["median"] - 0.02) < 1e-9
       and abs(st["depth_at_best_usd"]["median"] - 165.0) < 1e-9,
       f"spread median=0.02、depth median=165（{st['spread']['median']}/"
       f"{st['depth_at_best_usd']['median']}）")
    ok(abs(st["fillable_at_best_ratio"] - 0.9) < 1e-9,
       f"$50 固定跟單第一檔可成交比例=0.9（depth 30 那筆不足）（{st['fillable_at_best_ratio']}）")
    empty = shadow_bot.summarize_rows([])
    ok(empty["n_detected"] == 0 and empty["detect_lag_sec"]["median"] is None
       and empty["fillable_at_best_ratio"] is None, "空 session 統計全 None、不 crash")


class _FakeClock:
    """離線假時鐘：sleep 直接推進時間，不真等。"""

    def __init__(self, start=1751328000.0):  # 2025-07-01T00:00:00Z
        self.t = start

    def now(self):
        return self.t

    def sleep(self, sec):
        self.t += sec


def _make_fake_http(book, first_activity, later_activity):
    state = {"calls": 0}

    def fake(url, **kwargs):
        if "activity" in url:
            state["calls"] += 1
            return (first_activity if state["calls"] == 1 else later_activity), None
        return book, None

    return fake


def test_shadow_session(tmp):
    print("[11] shadow_bot：run_session 端到端（注入 http/時鐘）——baseline、去重、摘要落地")
    addr = "0x" + "ab" * 20
    book = json.loads((FIXTURES / "book_sample.json").read_text(encoding="utf-8"))
    ev_base = {"type": "TRADE", "transactionHash": "0xbase", "timestamp": 1751327990,
               "asset": "1234567890", "side": "BUY", "size": 100, "price": 0.54,
               "usdcSize": 54.0, "title": "Sample game", "slug": "sample-game"}
    ev_new = {"type": "TRADE", "transactionHash": "0xnew", "timestamp": 1751328002,
              "asset": "1234567890", "side": "BUY", "size": 200, "price": 0.55,
              "usdcSize": 110.0, "title": "Sample game", "slug": "sample-game"}
    clock = _FakeClock()
    out_root = tmp / "shadow"
    info = shadow_bot.run_session(
        addr, duration_min=0.5, poll_sec=4, out_root=out_root,
        http_get=_make_fake_http(book, [ev_base], [ev_base, ev_new]),
        sleep_fn=clock.sleep, now_fn=clock.now)
    ok(info["baseline_seeded"] == 1, f"首輪既有交易進 baseline 不記錄（{info['baseline_seeded']}）")
    ok(info["stats"]["n_detected"] == 1,
       f"跨多輪輪詢只偵測 1 筆新交易（去重生效）（{info['stats']['n_detected']}）")
    sdir = out_root / addr
    jsonl_lines = (sdir / f"session_{info['session_stamp']}.jsonl").read_text(
        encoding="utf-8").strip().splitlines()
    ok(len(jsonl_lines) == 1, f"JSONL 恰好 1 列（{len(jsonl_lines)}）")
    row = json.loads(jsonl_lines[0])
    ok(row["side"] == "BUY" and row["follower_entry_px"] == 0.57
       and abs(row["adverse_drift"] - 0.036364) < 1e-6,
       f"列含衍生欄位：entry=0.57、drift=+3.64%（{row['follower_entry_px']}）")
    ok(row["detect_lag_sec"] == 2.0,
       f"detect_lag=偵測時刻−鏈上時戳=2.0s（{row['detect_lag_sec']}）")
    md_path = sdir / "summary_2025-07-01.md"
    md = md_path.read_text(encoding="utf-8")
    ok("不測完整損益" in md and "時鐘" in md, "summary md 頂部含誠實聲明＋時鐘偏移註記")
    ok("固定跟單在第一檔深度內可成交比例：100.0%" in md,
       "depth 114 ≥ $50 → 可成交比例 100%")

    # 同日第二個 session：md append 段落、json append 進 sessions
    info2 = shadow_bot.run_session(
        addr, duration_min=0.2, poll_sec=4, out_root=out_root,
        http_get=_make_fake_http(book, [ev_base, ev_new], [ev_base, ev_new]),
        sleep_fn=clock.sleep, now_fn=clock.now)
    ok(info2["stats"]["n_detected"] == 0 and info2["baseline_seeded"] == 2,
       f"第二 session 全數進 baseline、0 偵測（{info2['baseline_seeded']}）")
    md2 = md_path.read_text(encoding="utf-8")
    ok(md2.count("## Session") == 2, f"同日多 session → md append 段落（{md2.count('## Session')}）")
    payload = json.loads((sdir / "summary_2025-07-01.json").read_text(encoding="utf-8"))
    ok(len(payload["sessions"]) == 2 and payload["sessions"][1]["stats"]["n_detected"] == 0,
       f"summary json 累積 2 個 session（{len(payload['sessions'])}）")


def main():
    with tempfile.TemporaryDirectory(prefix="poly-observer-test-") as td:
        tmp = Path(td)
        test_classification()
        test_metrics_sanity()
        snap_dir, report_dir = test_reports(tmp)
        test_analyze(tmp, snap_dir, report_dir)
        test_track_wallet(tmp)
        test_simulate_copy()
        test_simulate_copy_unreliable()
        test_shadow_dedup()
        test_shadow_book_and_drift()
        test_shadow_summary_stats()
        test_shadow_session(tmp)
    print(f"ALL TESTS PASSED ({checks} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
