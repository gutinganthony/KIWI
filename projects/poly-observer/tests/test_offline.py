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

FIXTURES = TESTS_DIR / "fixtures"
SNAP_DATE = "2026-07-01"  # fixtures 的時間軸終點（recent-30d 視窗右端）

EXPECTED = {
    "wallet_consistent.json": "consistent_winner",
    "wallet_one_hit.json": "one_hit",
    "wallet_mm_bot.json": "mm_bot_like",
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
    expected_counts = {"consistent_winner": 1, "one_hit": 1,
                       "mm_bot_like": 1, "insufficient_data": 1}
    ok(payload["classification_counts"] == expected_counts,
       f"分類統計={expected_counts}")
    gt = payload["ground_truth"]
    ok(len(gt) == 1 and gt[0]["ok"] and gt[0]["actual"] == "one_hit",
       "ground-truth 種子（xdd07070）如預期分類為 one_hit")
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


def main():
    with tempfile.TemporaryDirectory(prefix="poly-observer-test-") as td:
        tmp = Path(td)
        test_classification()
        test_metrics_sanity()
        snap_dir, report_dir = test_reports(tmp)
        test_analyze(tmp, snap_dir, report_dir)
    print(f"ALL TESTS PASSED ({checks} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
