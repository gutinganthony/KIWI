#!/usr/bin/env python3
"""hyper-observer 離線自測：不碰網路，餵 fixtures 驗證永續分類、報告產生、
track dossier 與 fetch 的 leaderboard 失敗退回 seeds 分支。

用法（在 projects/hyper-observer 下）：
    python3 tests/test_offline.py
"""

import json
import sys
import tempfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

import config  # noqa: E402
import classify  # noqa: E402
import track_wallet  # noqa: E402
import fetch  # noqa: E402

FIXTURES = TESTS_DIR / "fixtures"
SNAP_DATE = "2026-07-01"  # fixtures 的時間軸終點（idle 視窗右端）

EXPECTED = {
    "wallet_consistent.json": "consistent_winner",
    "wallet_blowup.json": "blowup_risk",
    "wallet_wash.json": "wash_suspect",
    "wallet_insufficient.json": "insufficient_data",
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
    print("[1] 永續分類器：4 個 fixture 逐一分類（四類皆覆蓋）")
    for fname, expected in EXPECTED.items():
        wallet = json.loads((FIXTURES / fname).read_text(encoding="utf-8"))
        metrics = classify.compute_metrics(wallet, SNAP_DATE)
        label, reasons = classify.classify(metrics)
        ok(label == expected,
           f"{fname} → {label}（預期 {expected}）reasons={reasons[:1]}")


def test_metrics_sanity():
    print("[2] 指標 sanity：consistent 與 blowup fixture 的關鍵數值")
    w = json.loads((FIXTURES / "wallet_consistent.json").read_text(encoding="utf-8"))
    m = classify.compute_metrics(w, SNAP_DATE)
    ok(m["pnl_source"] == "portfolio_curve", f"pnl_source=portfolio_curve（{m['pnl_source']}）")
    ok(m["portfolio_window"] == "perpAllTime", f"取用 perpAllTime 視窗（{m['portfolio_window']}）")
    ok(m["total_pnl"] == 50000.0, f"total_pnl=50000（{m['total_pnl']}）")
    ok(m["active_months"] == 5, f"active_months=5（{m['active_months']}）")
    ok(m["positive_month_ratio"] == 1.0, f"正月比率=1.0（{m['positive_month_ratio']}）")
    ok(m["profit_factor"] is not None and m["profit_factor"] >= 1.3,
       f"profit factor >=1.3（{m['profit_factor']}）")
    ok(m["current_max_leverage"] == 8.0, f"目前最高槓桿=8x（{m['current_max_leverage']}）")
    ok(m["top_coin"] == "BTC", f"主力幣=BTC（{m['top_coin']}）")
    ok(m["span_days"] == 144.0, f"活躍跨度=144 天（{m['span_days']}）")
    ok(m["had_liquidation"] is False, "consistent 無強平紀錄")
    ok(m["max_drawdown_pct"] is not None and m["max_drawdown_pct"] < 0.4,
       f"回撤 <40%（{m['max_drawdown_pct']}）")
    ok(m["n_open_positions"] == 2, f"目前 2 個未平倉部位（{m['n_open_positions']}）")

    wb = json.loads((FIXTURES / "wallet_blowup.json").read_text(encoding="utf-8"))
    mb = classify.compute_metrics(wb, SNAP_DATE)
    ok(mb["had_liquidation"] is True, "Wynn fixture 偵測到 liquidation")
    ok(mb["current_max_leverage"] == 40.0, f"Wynn 目前槓桿=40x（{mb['current_max_leverage']}）")
    ok(mb["max_single_day_crash_pct"] is not None and mb["max_single_day_crash_pct"] > 0.9,
       f"Wynn 單步崩跌 >90%（{mb['max_single_day_crash_pct']}）")
    lbl, _ = classify.classify(mb)
    ok(lbl == "blowup_risk", f"Wynn fixture 判 blowup_risk（{lbl}）")

    ww = json.loads((FIXTURES / "wallet_wash.json").read_text(encoding="utf-8"))
    mw = classify.compute_metrics(ww, SNAP_DATE)
    ok(mw["vlm_to_pnl_ratio"] is not None and mw["vlm_to_pnl_ratio"] >= 500,
       f"wash fixture 量/PnL 比極端（{mw['vlm_to_pnl_ratio']}）")


def test_reports(tmp):
    print("[3] classify 報告產生：組 snapshot → md/json 落地＋ground-truth 校驗")
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
            {"name": "leaderboard", "ok": False, "status": 403,
             "error": "HTTP 403; body=blocked",
             "url": "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard"},
            {"name": "clearinghouseState[0x1111…]", "ok": True, "status": 200,
             "url": "https://api.hyperliquid.xyz/info"},
            {"name": "portfolio[0x1111…]", "ok": True, "status": 200,
             "url": "https://api.hyperliquid.xyz/info"},
        ]}), encoding="utf-8")

    report_dir = tmp / "reports"
    payload = classify.run_verification(snap_dir, report_dir)

    md_path = report_dir / f"verification_{SNAP_DATE}.md"
    json_path = report_dir / f"verification_{SNAP_DATE}.json"
    ok(md_path.is_file() and md_path.stat().st_size > 500, f"md 報告存在且非空（{md_path.name}）")
    reparsed = json.loads(json_path.read_text(encoding="utf-8"))
    ok(reparsed["classification_counts"] == payload["classification_counts"],
       "json 報告可重新解析且計數一致")
    expected_counts = {"consistent_winner": 1, "blowup_risk": 1,
                       "wash_suspect": 1, "insufficient_data": 1}
    ok(payload["classification_counts"] == expected_counts,
       f"分類統計={expected_counts}（實際 {payload['classification_counts']}）")
    gt = payload["ground_truth"]
    ok(len(gt) == 1 and gt[0]["ok"] and gt[0]["actual"] == "blowup_risk",
       "ground-truth 種子（James Wynn）如預期分類為 blowup_risk")
    ok("弱存在" in payload["verdict"], f"裁決=弱存在（1 個 winner）：{payload['verdict']}")
    md_text = md_path.read_text(encoding="utf-8")
    for section in ("端點健康", "分類統計", "consistent_winner 明細",
                    "Ground-truth 校驗", "裁決", "倖存者偏差", "刷量", "槓桿", "純唯讀"):
        ok(section in md_text, f"md 含「{section}」段/聲明")
    return snap_dir


def test_track_wallet(tmp):
    print("[4] track_wallet：dossier 產生＋持倉列出（槓桿/強平價）＋initialized＋timeline 落地")
    base = json.loads((FIXTURES / "wallet_consistent.json").read_text(encoding="utf-8"))
    addr = base["address"]
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
       f"分類重用 classify.classify（{dossier['classification']}）")

    tdir = tracked_root / addr
    ok((tdir / f"dossier_{SNAP_DATE}.md").is_file()
       and (tdir / f"dossier_{SNAP_DATE}.json").is_file(), "dossier md/json 落地")
    ok((tdir / "latest_raw.json").is_file(), "原始資料持久化到 latest_raw.json")
    md_text = (tdir / f"dossier_{SNAP_DATE}.md").read_text(encoding="utf-8")
    ok("方向" in md_text and "槓桿" in md_text and "強平價" in md_text,
       "md dossier 持倉表含方向/槓桿/強平價欄")
    ok("40,000" in md_text or "3,400" in md_text, "md dossier 含具體強平價數值")
    timeline_lines = (tdir / "timeline.jsonl").read_text(encoding="utf-8").strip().splitlines()
    ok(len(timeline_lines) == 1, f"timeline.jsonl 落地 1 行（{len(timeline_lines)}）")
    row = json.loads(timeline_lines[0])
    ok(row["n_open_positions"] == 2 and row["new_positions_count"] == 0,
       "timeline 行含持倉數與新開倉數")

    # 第二次執行：改變持倉集合（ETH 空平掉、新開 SOL 多），驗證 new/disappeared delta
    base["clearinghouseState"]["assetPositions"] = [
        base["clearinghouseState"]["assetPositions"][0],  # 保留 BTC 多（不變）
        {"type": "oneWay", "position": {
            "coin": "SOL", "szi": "100", "entryPx": "150", "positionValue": "15000",
            "unrealizedPnl": "500", "leverage": {"type": "cross", "value": 6},
            "liquidationPx": "120", "marginUsed": "2500", "maxLeverage": 20,
            "cumFunding": {"allTime": "3.2"}}},
    ]
    (wallets_dir / f"{addr}.json").write_text(
        json.dumps(base, ensure_ascii=False), encoding="utf-8")
    dossier2 = track_wallet.run_track_wallet(addr, snap_dir, tracked_root)
    ok(dossier2["initialized"] is False, "第二次執行不再 initialized")
    new_keys = {p["key"] for p in dossier2["new_positions"]}
    gone_keys = {p["key"] for p in dossier2["disappeared_positions"]}
    ok("SOL:long" in new_keys, f"偵測到新開倉 SOL:long（{new_keys}）")
    ok("ETH:short" in gone_keys, f"偵測到消失持倉 ETH:short（{gone_keys}）")


def test_fetch_fallback():
    print("[5] fetch：leaderboard 端點失敗 → 退回只用 seeds＋記 meta，不 crash")
    meta = fetch.Meta()

    def failing_get(url, name, m):
        m.record(name, url, False, status=403, error="HTTP 403; body=blocked")
        return None, False

    raw, addrs = fetch.fetch_leaderboard(meta, get_fn=failing_get)
    ok(raw is None and addrs == [], f"leaderboard 失敗回傳空地址（addrs={addrs}）")
    ok(meta.requests_failed >= 1, f"失敗計入 meta（failed={meta.requests_failed}）")
    ok(any("退回只用 seeds" in n for n in meta.notes),
       "meta 記錄『退回只用 seeds』note")

    seeds = ["0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6",
             "0x5b5d51203a0f9079f8aeb098a6523a13f298c060"]
    universe = fetch.build_universe(seeds, addrs, config.DEFAULT_MAX_WALLETS)
    ok(universe == seeds, f"leaderboard 失敗時宇宙 = seeds（{universe}）")

    # 寬鬆地址解析：正常 leaderboard 形狀能抽出地址、垃圾輸入回空清單、seeds 永遠保留
    good = fetch.extract_addresses(
        {"leaderboardRows": [{"ethAddress": "0xABCabc0000000000000000000000000000000001",
                              "accountValue": "1000"}]})
    ok(good == ["0xabcabc0000000000000000000000000000000001"],
       f"寬鬆解析 leaderboardRows 抽出小寫地址（{good}）")
    ok(fetch.extract_addresses(None) == [] and fetch.extract_addresses({"x": 1}) == [],
       "垃圾/None leaderboard 回傳空清單，不 crash")
    merged = fetch.build_universe(seeds, ["0xabcabc0000000000000000000000000000000001"], 60)
    ok(merged[:2] == seeds and len(merged) == 3, f"seeds 永遠保留＋補入 lb 地址（{len(merged)}）")


def main():
    with tempfile.TemporaryDirectory(prefix="hyper-observer-test-") as td:
        tmp = Path(td)
        test_classification()
        test_metrics_sanity()
        test_reports(tmp)
        test_track_wallet(tmp)
        test_fetch_fallback()
    print(f"ALL TESTS PASSED ({checks} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
