#!/usr/bin/env python3
"""hyper-observer 離線自測：不碰網路，餵 fixtures 驗證永續分類、報告產生、
track dossier 與 fetch 的 leaderboard 失敗退回 seeds 分支。

用法（在 projects/hyper-observer 下）：
    python3 tests/test_offline.py
"""

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

import config  # noqa: E402
import classify  # noqa: E402
import track_wallet  # noqa: E402
import fetch  # noqa: E402
import scan_universe  # noqa: E402
import hyper_shadow  # noqa: E402

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


def _ms(year, month, day=1):
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp() * 1000)


def _pnl_window(pnl_points, vlm):
    """由 [(ms, pnl), ...] 組一個 perpAllTime portfolio 視窗（accountValueHistory 同步造）。"""
    return [["perpAllTime", {
        "accountValueHistory": [[ts, str(v + 5000)] for ts, v in pnl_points],
        "pnlHistory": [[ts, str(v)] for ts, v in pnl_points],
        "vlm": str(vlm),
    }]]


def _pos(coin="BTC", szi="0.5", lev=5):
    return {"type": "oneWay", "position": {
        "coin": coin, "szi": szi, "entryPx": "60000", "positionValue": "30000",
        "unrealizedPnl": "1000", "leverage": {"type": "cross", "value": lev},
        "liquidationPx": "50000", "marginUsed": "6000", "maxLeverage": 50,
        "cumFunding": {"allTime": "10.0"}}}


def test_bugfix_metrics_and_classify():
    print("[bugfix] BUG1 崩跌封頂 / BUG2 MM攔截 / BUG3 截斷贏家 / BUG4 缺資料 / Wynn 仍 blowup")

    # BUG 1：小正峰值($15k，勉強過 min_peak)→深負(-$1.5M)，drop/peak 應被封頂 <= 1.0（不再爆量）
    w_crash = {"address": "0xa000000000000000000000000000000000000001",
               "clearinghouseState": {"assetPositions": []},
               "portfolio": _pnl_window([(_ms(2026, 1), 0), (_ms(2026, 3), 15000),
                                         (_ms(2026, 5), -1500000)], vlm="2000000"),
               "userFills": [], "userFunding": []}
    mc = classify.compute_metrics(w_crash, SNAP_DATE)
    ok(mc["max_single_day_crash_pct"] is not None and mc["max_single_day_crash_pct"] <= 1.0,
       f"BUG1 單步崩跌封頂 <=1.0（{mc['max_single_day_crash_pct']}，未封頂為 ~101）")
    ok(mc["max_drawdown_pct"] is not None and mc["max_drawdown_pct"] <= 1.0,
       f"BUG1 峰值回撤同步封頂 <=1.0（{mc['max_drawdown_pct']}）")

    # BUG 2：巨量($4B)、量/PnL=200(>=50)、PnL 正(+$20M) 但做市商 → wash_suspect（非 choppy/winner）
    w_mm = {"address": "0xb000000000000000000000000000000000000002",
            "clearinghouseState": {"assetPositions": []},
            "portfolio": _pnl_window(
                [(_ms(2026, 1), 0), (_ms(2026, 2), 5000000), (_ms(2026, 3), 10000000),
                 (_ms(2026, 4), 8000000), (_ms(2026, 5), 15000000), (_ms(2026, 6), 20000000)],
                vlm="4000000000"),
            "userFills": [
                {"coin": "BTC", "px": "50000", "sz": "0.001", "side": "B",
                 "time": _ms(2026, 6, 20), "closedPnl": "45.0", "dir": "Close Long"},
                {"coin": "BTC", "px": "50000", "sz": "0.001", "side": "A",
                 "time": _ms(2026, 6, 21), "closedPnl": "-45.8", "dir": "Close Short"}],
            "userFunding": []}
    mm = classify.compute_metrics(w_mm, SNAP_DATE)
    lbl_mm, why_mm = classify.classify(mm)
    ok(mm["vlm_to_pnl_ratio"] is not None and mm["vlm_to_pnl_ratio"] >= config.MM_MIN_VLM_TO_PNL,
       f"BUG2 量/PnL 比 {mm['vlm_to_pnl_ratio']} >= {config.MM_MIN_VLM_TO_PNL}")
    ok(lbl_mm == "wash_suspect",
       f"BUG2 做市商($28M 型)判 wash_suspect（{lbl_mm}）不進 choppy/winner；{why_mm[:1]}")

    # BUG 3：portfolio 曲線明確獲利(+$5M、dd<40%、span 長、正月比高)，但 n_fills 達截斷上限(2000)、
    # profit_factor 低(<1.3) → 不因 pf 硬否決，仍判 consistent_winner
    fills = []
    for i in range(1000):
        t = _ms(2026, 6, 1) + i * 7200 * 1000  # 每對相隔，close 較 open 晚 1h（avg_hold>=0.1）
        fills.append({"coin": "BTC", "px": "60000", "sz": "0.01", "side": "B",
                      "time": t, "closedPnl": "0.0", "dir": "Open Long"})
        fills.append({"coin": "BTC", "px": "60000", "sz": "0.01", "side": "A",
                      "time": t + 3600 * 1000,
                      "closedPnl": ("10.0" if i % 2 == 0 else "-12.0"), "dir": "Close Long"})
    w_trunc = {"address": "0xc000000000000000000000000000000000000003",
               "clearinghouseState": {"assetPositions": [_pos()],
                                      "marginSummary": {"accountValue": "5000000"}},
               "portfolio": _pnl_window(
                   [(_ms(2026, 1), 0), (_ms(2026, 2), 800000), (_ms(2026, 3), 1300000),
                    (_ms(2026, 4), 1100000), (_ms(2026, 5), 2400000), (_ms(2026, 6), 3600000),
                    (_ms(2026, 7), 5000000)], vlm="50000000"),
               "userFills": fills, "userFunding": []}
    mt = classify.compute_metrics(w_trunc, SNAP_DATE)
    lbl_t, why_t = classify.classify(mt)
    ok(mt["n_fills"] == 2000 and mt["n_fills_truncated"] is True,
       f"BUG3 fills 達截斷上限（n_fills={mt['n_fills']}, truncated={mt['n_fills_truncated']}）")
    ok(mt["profit_factor"] is not None and mt["profit_factor"] < config.CONSISTENT_MIN_PROFIT_FACTOR,
       f"BUG3 截斷樣本 pf 低於門檻（{mt['profit_factor']} < {config.CONSISTENT_MIN_PROFIT_FACTOR}）")
    ok(lbl_t == "consistent_winner",
       f"BUG3 截斷但曲線獲利 → consistent_winner（{lbl_t}），pf 未硬否決；{why_t[-1:]}")

    # BUG 4：portfolio 曲線缺失（空 pnlHistory）＋無 liquidation，即使成交 10 筆 → insufficient_data
    w_missing = {"address": "0xd000000000000000000000000000000000000004",
                 "clearinghouseState": {"assetPositions": []},
                 "portfolio": [["perpAllTime", {"accountValueHistory": [], "pnlHistory": [],
                                                "vlm": "0"}]],
                 "userFills": [{"coin": "SOL", "px": "150", "sz": "2", "side": "B",
                                "time": _ms(2026, 6, i % 27 + 1), "closedPnl": "5.0",
                                "dir": "Close Long"} for i in range(10)],
                 "userFunding": []}
    mmiss = classify.compute_metrics(w_missing, SNAP_DATE)
    lbl_x, _ = classify.classify(mmiss)
    ok(mmiss["pnl_source"] is None and mmiss["n_fills"] == 10,
       f"BUG4 無 portfolio 曲線但成交 10 筆（pnl_source={mmiss['pnl_source']}）")
    ok(lbl_x == "insufficient_data",
       f"BUG4 缺曲線＋無強平 → insufficient_data（{lbl_x}），不進 choppy")

    # Wynn ground-truth：靠 had_liquidation（＋高 dd）仍判 blowup_risk，不靠爆量崩跌%
    wynn = json.loads((FIXTURES / "wallet_blowup.json").read_text(encoding="utf-8"))
    mwynn = classify.compute_metrics(wynn, SNAP_DATE)
    lbl_w, _ = classify.classify(mwynn)
    ok(mwynn["had_liquidation"] is True and mwynn["max_single_day_crash_pct"] <= 1.0,
       f"Wynn had_liquidation＝True 且崩跌%已封頂（crash={mwynn['max_single_day_crash_pct']}）")
    ok(lbl_w == "blowup_risk", f"Wynn ground-truth 仍 blowup_risk（{lbl_w}）")


def test_final_bugfix_A_B():
    print("[final] 修正A 回撤 min_peak 閘（殺早期小峰值假象）/ 修正B 強平次數取代有無")

    # (a) 早期小峰值($15k)→深負(-$1.5M)→大額正 PnL(+$50M，一度 40M→35M 真實回撤 12.5%)。
    # 修正A：早期 dip 因 running peak 遠低於全期峰值 10% 而不計入，dd 只反映真實 12.5% 回撤，
    # 非爆量、非假 100%；且大額淨正、已復原 → 不得判 blowup。
    w_recover = {"address": "0xe000000000000000000000000000000000000005",
                 "clearinghouseState": {"assetPositions": []},
                 "portfolio": _pnl_window(
                     [(_ms(2026, 1, 1), 0), (_ms(2026, 2, 1), 15000),
                      (_ms(2026, 3, 1), -1500000), (_ms(2026, 4, 1), 3000000),
                      (_ms(2026, 5, 1), 8000000), (_ms(2026, 6, 1), 40000000),
                      (_ms(2026, 6, 20), 35000000), (_ms(2026, 7, 1), 50000000)],
                     vlm="30000000"),
                 "userFills": [], "userFunding": []}
    mr = classify.compute_metrics(w_recover, SNAP_DATE)
    lbl_r, why_r = classify.classify(mr)
    ok(mr["max_drawdown_pct"] is not None and mr["max_drawdown_pct"] < 0.40,
       f"修正A dd 合理、不受早期 dip 污染、非爆量（{mr['max_drawdown_pct']}，未修為 1.0）")
    ok(mr["current_drawdown_pct"] is not None and mr["current_drawdown_pct"] < 0.10,
       f"修正A 現值已復原到峰值附近（current_drawdown={mr['current_drawdown_pct']}）")
    ok(lbl_r != "blowup_risk",
       f"修正A 大額淨正、已復原錢包不因假回撤判 blowup（{lbl_r}）；{why_r[:1]}")

    # (b) n_liquidations>=3（反覆爆倉）→ blowup，即使淨正、回撤溫和、槓桿不極端（只靠條件 1）
    liq_fills = [{"coin": "BTC", "px": "60000", "sz": "0.1", "side": "A",
                  "time": _ms(2026, 3 + i, 1), "closedPnl": "-5000.0", "dir": "Close Long",
                  "liquidation": {"liquidatedUser": "0xe00", "markPx": "60000",
                                  "method": "market"}} for i in range(4)]
    w_multiliq = {"address": "0xe000000000000000000000000000000000000006",
                  "clearinghouseState": {"assetPositions": [_pos(lev=10)]},
                  "portfolio": _pnl_window(
                      [(_ms(2026, 1), 0), (_ms(2026, 2), 5000), (_ms(2026, 3), 12000),
                       (_ms(2026, 4), 9000), (_ms(2026, 5), 15000), (_ms(2026, 6), 11000)],
                      vlm="2000000"),
                  "userFills": liq_fills, "userFunding": []}
    mml = classify.compute_metrics(w_multiliq, SNAP_DATE)
    lbl_ml, why_ml = classify.classify(mml)
    ok(mml["n_liquidations"] >= config.BLOWUP_MIN_LIQUIDATIONS,
       f"修正B 反覆爆倉計數 n_liquidations={mml['n_liquidations']} >= {config.BLOWUP_MIN_LIQUIDATIONS}")
    ok(lbl_ml == "blowup_risk",
       f"修正B 反覆爆倉 → blowup_risk（{lbl_ml}）；{why_ml[:1]}")

    # (c) 單次強平(n_liquidations==1)但強獲利、低回撤、槓桿合理 → 不判 blowup，走 consistent_winner；
    # metrics 保留 had_liquidation/n_liquidations，明細揭露「曾強平 N 次」，不隱藏風險
    oneliq_fills = [
        {"coin": "BTC", "px": "60000", "sz": "0.5", "side": "B", "time": _ms(2026, 1, 10),
         "closedPnl": "0.0", "dir": "Open Long"},
        {"coin": "BTC", "px": "66000", "sz": "0.5", "side": "A", "time": _ms(2026, 2, 10),
         "closedPnl": "30000.0", "dir": "Close Long"},
        {"coin": "ETH", "px": "3000", "sz": "5", "side": "B", "time": _ms(2026, 3, 10),
         "closedPnl": "0.0", "dir": "Open Long"},
        {"coin": "ETH", "px": "3200", "sz": "5", "side": "A", "time": _ms(2026, 4, 10),
         "closedPnl": "10000.0", "dir": "Close Long"},
        {"coin": "SOL", "px": "150", "sz": "10", "side": "A", "time": _ms(2026, 5, 10),
         "closedPnl": "-8000.0", "dir": "Close Long",
         "liquidation": {"liquidatedUser": "0xe00", "markPx": "150", "method": "market"}},
        {"coin": "BTC", "px": "64000", "sz": "0.5", "side": "B", "time": _ms(2026, 6, 1),
         "closedPnl": "0.0", "dir": "Open Long"},
        {"coin": "BTC", "px": "70000", "sz": "0.5", "side": "A", "time": _ms(2026, 6, 20),
         "closedPnl": "12000.0", "dir": "Close Long"}]
    w_oneliq = {"address": "0xe000000000000000000000000000000000000007",
                "clearinghouseState": {"assetPositions": [_pos(lev=8)],
                                       "marginSummary": {"accountValue": "80000"}},
                "portfolio": _pnl_window(
                    [(_ms(2026, 1), 0), (_ms(2026, 2), 30000), (_ms(2026, 3), 35000),
                     (_ms(2026, 4), 45000), (_ms(2026, 5), 40000), (_ms(2026, 6), 52000)],
                    vlm="500000"),
                "userFills": oneliq_fills, "userFunding": []}
    mol = classify.compute_metrics(w_oneliq, SNAP_DATE)
    lbl_ol, why_ol = classify.classify(mol)
    ok(mol["n_liquidations"] == 1 and mol["had_liquidation"] is True,
       f"修正B 單次強平於 metrics 揭露（n_liquidations={mol['n_liquidations']}, "
       f"had_liquidation={mol['had_liquidation']}）")
    ok(lbl_ol == "consistent_winner",
       f"修正B 單次強平但強獲利低回撤 → 不判 blowup、走 consistent_winner（{lbl_ol}）；{why_ol[:1]}")
    md = classify.build_markdown(
        SNAP_DATE, [{"metrics": mol, "classification": lbl_ol, "reasons": why_ol}],
        None, [], "test")
    ok("曾強平 1 次" in md,
       "consistent_winner 明細揭露『曾強平 N 次』註記（不隱藏風險）")


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


def test_scan_universe(tmp):
    print("[6] scan_universe：載入形狀/漏斗遞減/候選>0/分數排序/schema/top-N 排除")
    raw = json.loads((FIXTURES / "lb_sample.json").read_text(encoding="utf-8"))
    rows = scan_universe.load_rows(raw)
    ok(len(rows) == 500, f"fixture 解析 500 列（{len(rows)}）")
    wrapped = {"endpoint_tried": [], "addresses": [], "raw": raw}
    ok(len(scan_universe.load_rows(wrapped)) == 500,
       "接受 fetch dump 包一層 raw 的形狀")
    ok(scan_universe.load_rows(None) == [] and scan_universe.load_rows({"x": 1}) == [],
       "垃圾/None 輸入回空 list，不 crash")

    # 放寬門檻（fixture 只有排行榜頂端 500 列，生產門檻下幾乎全滅）驗證漏斗機制
    relaxed = {"min_alltime_pnl": 100_000.0, "min_month_pnl": 0.0, "min_week_pnl": 0.0,
               "min_vlm_to_pnl": 0.0, "max_vlm_to_pnl": 100.0, "min_alltime_roi": 0.01,
               "min_account": 20_000.0, "max_account": 1e9, "exclude_top_n": 0}
    cands, funnel = scan_universe.filter_candidates(rows, relaxed)
    stage_names = ["total_rows", "parsed_valid", "alltime_pnl", "still_winning",
                   "vlm_to_pnl_band", "alltime_roi", "account_band", "exclude_top_n"]
    ok(list(funnel.keys()) == stage_names, f"漏斗階段齊全且有序（{list(funnel.keys())}）")
    vals = [funnel[k] for k in stage_names]
    ok(all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1)),
       f"漏斗各階段單調遞減（{vals}）")
    ok(len(cands) > 0, f"放寬門檻下候選數 > 0（{len(cands)}）")
    ok(len({c['address'] for c in cands}) == len(cands), "候選地址不重複")
    ok(all("score" in c and "vlm_to_pnl" in c for c in cands), "候選皆含 score 與 vlm_to_pnl")

    # top-N 排除：把整份 fixture 都列為「已掃過」→ 候選歸零
    all_excluded = dict(relaxed, exclude_top_n=500)
    cands0, funnel0 = scan_universe.filter_candidates(rows, all_excluded)
    ok(len(cands0) == 0 and funnel0["exclude_top_n"] == 0,
       f"exclude_top_n=500 時候選歸零（{len(cands0)}）")

    # 生產門檻（config SCAN_*）：漏斗仍單調，不 crash（頂端 500 列可為 0 候選）
    _, funnel_prod = scan_universe.filter_candidates(rows)
    vals_prod = [funnel_prod[k] for k in stage_names]
    ok(all(vals_prod[i] >= vals_prod[i + 1] for i in range(len(vals_prod) - 1)),
       f"生產門檻漏斗單調遞減（{vals_prod}）")

    # build_output：排序正確、截斷生效、schema 齊全
    out = scan_universe.build_output(cands, funnel, 5, "2026-07-01", "fixture")
    scores = [c["score"] for c in out["candidates"]]
    ok(scores == sorted(scores, reverse=True), f"候選依分數遞減排序（{scores}）")
    ok(out["n_candidates"] == min(5, len(cands)) == len(out["candidates"]),
       f"max-candidates 截斷生效（{out['n_candidates']}）")
    for key in ("date", "generated_at", "source", "thresholds", "funnel",
                "n_candidates", "candidates"):
        ok(key in out, f"輸出 schema 含 {key}")
    c0 = out["candidates"][0]
    ok(all(k in c0 for k in ("address", "score", "account_value", "vlm_to_pnl", "windows"))
       and all(w in c0["windows"] for w in ("day", "week", "month", "allTime")),
       "候選條目含地址＋四窗指標＋分數")

    # main() 端到端：讀 fixture → 寫檔（生產門檻，候選數可為 0）
    out_path = tmp / "scan" / "candidates_e2e.json"
    rc = scan_universe.main(["--raw", str(FIXTURES / "lb_sample.json"),
                             "--out", str(out_path)])
    ok(rc == 0 and out_path.is_file(), "scan_universe main 端到端跑通並落檔")
    reparsed = json.loads(out_path.read_text(encoding="utf-8"))
    ok(reparsed["funnel"]["total_rows"] == 500
       and out_path.stat().st_size < 200 * 1024,
       f"輸出可重新解析且 <200KB（{out_path.stat().st_size} bytes）")


def test_scan_report(tmp):
    print("[7] classify --label scan：檔名/可跟欄/兩級裁決/followable 判定")
    snap_dir = tmp / "snapshots" / f"{SNAP_DATE}-scan"
    wallets_dir = snap_dir / "wallets"
    wallets_dir.mkdir(parents=True)

    # 可跟 winner：wallet_consistent（近 30 天 2 筆、hold 340.8h、槓桿 8x）
    w_ok = json.loads((FIXTURES / "wallet_consistent.json").read_text(encoding="utf-8"))
    (wallets_dir / f"{w_ok['address']}.json").write_text(
        json.dumps(w_ok, ensure_ascii=False), encoding="utf-8")

    # 不可跟 winner：BUG3 型高頻戶（2000 筆、hold 1h）——曲線獲利判 winner 但頻率/持倉不可跟
    fills = []
    for i in range(1000):
        t = _ms(2026, 6, 1) + i * 7200 * 1000
        fills.append({"coin": "BTC", "px": "60000", "sz": "0.01", "side": "B",
                      "time": t, "closedPnl": "0.0", "dir": "Open Long"})
        fills.append({"coin": "BTC", "px": "60000", "sz": "0.01", "side": "A",
                      "time": t + 3600 * 1000,
                      "closedPnl": ("10.0" if i % 2 == 0 else "-12.0"), "dir": "Close Long"})
    w_hf = {"address": "0xf000000000000000000000000000000000000008",
            "clearinghouseState": {"assetPositions": [_pos()],
                                   "marginSummary": {"accountValue": "5000000"}},
            "portfolio": _pnl_window(
                [(_ms(2026, 1), 0), (_ms(2026, 2), 800000), (_ms(2026, 3), 1300000),
                 (_ms(2026, 4), 1100000), (_ms(2026, 5), 2400000), (_ms(2026, 6), 3600000),
                 (_ms(2026, 7), 5000000)], vlm="50000000"),
            "userFills": fills, "userFunding": []}
    (wallets_dir / f"{w_hf['address']}.json").write_text(
        json.dumps(w_hf, ensure_ascii=False), encoding="utf-8")

    report_dir = tmp / "reports-scan"
    payload = classify.run_verification(snap_dir, report_dir, label="scan")

    ok(payload["date"] == SNAP_DATE,
       f"{SNAP_DATE}-scan 目錄名正確抽出日期（{payload['date']}）")
    md_path = report_dir / f"scan_verification_{SNAP_DATE}.md"
    json_path = report_dir / f"scan_verification_{SNAP_DATE}.json"
    ok(md_path.is_file() and json_path.is_file(),
       f"scan 報告檔名 scan_verification_{SNAP_DATE}.md/json（區別於每日報告）")
    ok(payload["classification_counts"].get("consistent_winner") == 2,
       f"兩個 winner（{payload['classification_counts']}）")

    rec_ok = payload["wallets"][w_ok["address"]]
    rec_hf = payload["wallets"][w_hf["address"]]
    ok(rec_ok["followable"]["ok"] is True,
       f"低頻長持倉 winner 判可跟（{rec_ok['followable']}）")
    ok(rec_hf["followable"]["ok"] is False
       and any("頻率過高" in r for r in rec_hf["followable"]["reasons"])
       and any("持倉過短" in r for r in rec_hf["followable"]["reasons"]),
       f"高頻 winner 判不可跟＋原因含頻率/持倉（{rec_hf['followable']['reasons']}）")
    ok(rec_hf["metrics"]["n_fills_last_30d"] > config.SCAN_FOLLOWABLE_MAX_FREQ,
       f"n_fills_last_30d 指標落地（{rec_hf['metrics']['n_fills_last_30d']}）")
    ok(payload["followable_count"] == 1, f"followable 計數=1（{payload['followable_count']}）")
    ok("其中 followable 1 個" in payload["verdict"]
       and "consistent_winner 2 個" in payload["verdict"],
       f"兩級裁決（{payload['verdict']}）")

    md_text = md_path.read_text(encoding="utf-8")
    ok("| 可跟 |" in md_text.replace(" 可跟 |", "| 可跟 |", 1) or "可跟" in md_text,
       "winner 明細表含「可跟」欄")
    ok("✅" in md_text and "❌" in md_text, "可跟欄同時出現 ✅ 與 ❌")
    ok("回望偏差" in md_text and "廣域可跟錢包掃描" in md_text,
       "scan 報告開頭聲明改寫（回望偏差、非僅榜頂）")

    # 每日模式不受影響：同 snapshot 以預設 label 跑 → 檔名照舊、無可跟欄
    daily_dir = tmp / "reports-daily-check"
    classify.run_verification(snap_dir, daily_dir)
    daily_md = (daily_dir / f"verification_{SNAP_DATE}.md").read_text(encoding="utf-8")
    ok("可跟" not in daily_md and "倖存者偏差" in daily_md,
       "預設（每日）模式報告不含可跟欄、聲明照舊")


def test_fetch_wallets_file(tmp):
    print("[8] fetch：--wallets-file 解析/去重/seeds 永留＋leaderboard 摘要不含 raw")
    meta = fetch.Meta()
    cand_path = tmp / "candidates.json"
    cand_path.write_text(json.dumps({"candidates": [
        {"address": "0xAABBcc0000000000000000000000000000000001", "score": 1.0},
        {"address": "0xaabbcc0000000000000000000000000000000001"},
        {"address": "0xaabbcc0000000000000000000000000000000002"},
        {"address": "not-an-address"},
    ]}), encoding="utf-8")
    addrs = fetch.load_wallets_file(cand_path, meta)
    ok(addrs == ["0xaabbcc0000000000000000000000000000000001",
                 "0xaabbcc0000000000000000000000000000000002"],
       f"candidates json → 小寫去重地址、壞地址剔除（{addrs}）")

    plain_path = tmp / "plain.json"
    plain_path.write_text(json.dumps(
        ["0xaabbcc0000000000000000000000000000000003"]), encoding="utf-8")
    ok(fetch.load_wallets_file(plain_path, meta)
       == ["0xaabbcc0000000000000000000000000000000003"], "純地址 list 形狀也可解析")
    ok(fetch.load_wallets_file(tmp / "missing.json", meta) == []
       and any("wallets-file 讀取失敗" in n for n in meta.notes),
       "缺檔回空清單＋記 note，不 crash")

    seeds = ["0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6",
             "0x5b5d51203a0f9079f8aeb098a6523a13f298c060"]
    uni = fetch.build_universe(seeds, addrs, 3)
    ok(uni[:2] == seeds and len(uni) == 3,
       f"--wallets-file 宇宙仍 seeds 永留＋上限截斷（{len(uni)}）")

    summ = fetch.leaderboard_summary(
        {"leaderboardRows": [{"ethAddress": f"0x{i:040x}"} for i in range(3)]},
        ["0x" + "0" * 40], "data/tmp/leaderboard_raw_x.json")
    ok("raw" not in summ and summ["n_rows_total"] == 3,
       f"版控 leaderboard.json 摘要不含 raw（keys={sorted(summ)}）")
    summ_none = fetch.leaderboard_summary(None, [], None)
    ok("raw" not in summ_none and summ_none["n_rows_total"] == 0,
       "端點失敗（raw=None）摘要也不含 raw")


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


def test_aggregate_events():
    print("[9] fills→部位事件聚合：方向鍵/gap 合併/notional/closedPnl/排序/衍生指標")
    t0 = _ms(2026, 6, 10)
    minute = 60 * 1000

    def raw(coin, px, sz, side, t, pnl, d):
        return {"coin": coin, "px": px, "sz": sz, "side": side,
                "time": t, "closedPnl": pnl, "dir": d}

    raw_fills = []
    # BTC Open Long 5 筆，間隔 10 分鐘（<60min）→ 1 事件
    for i in range(5):
        raw_fills.append(raw("BTC", "60000", "0.1", "B",
                             t0 + i * 10 * minute, "0.0", "Open Long"))
    # ETH Open Short 4 筆：前 2 筆間隔 30 分，隔 90 分（>60min）再 2 筆 → 跨 gap 分 2 事件
    eth0 = t0 + 5 * minute
    for dt in (0, 30 * minute, 120 * minute, 130 * minute):
        raw_fills.append(raw("ETH", "3000", "1", "A", eth0 + dt, "0.0", "Open Short"))
    # 數小時後 BTC Close Long 3 筆，間隔 5 分鐘 → 1 事件（方向鍵異於 Open Long，不合併）
    btc_close0 = t0 + 240 * minute
    for i in range(3):
        raw_fills.append(raw("BTC", "61000", "0.1", "A",
                             btc_close0 + i * 5 * minute, "100.0", "Close Long"))

    fills = classify.parse_fills(raw_fills)
    ok(len(fills) == 12, f"fixture 共 12 筆 fills（{len(fills)}）")
    events = classify.aggregate_fills_to_events(fills, gap_minutes=60)
    ok(len(events) == 4, f"聚合成 4 個部位事件（{len(events)}）")
    starts = [e["start_ts"] for e in events]
    ok(starts == sorted(starts), "事件清單按 start_ts 排序")
    ok([e["n_fills"] for e in events] == [5, 2, 2, 3],
       f"各事件 n_fills=[5,2,2,3]（{[e['n_fills'] for e in events]}）")
    ok([e["direction"] for e in events]
       == ["open long", "open short", "open short", "close long"],
       f"方向鍵由 dir 正規化（{[e['direction'] for e in events]}）")
    ok(abs(events[0]["total_notional"] - 30000.0) < 1e-6,
       f"BTC Open Long 事件 notional=Σ|px×sz|=30000（{events[0]['total_notional']}）")
    ok(abs(events[1]["total_notional"] - 6000.0) < 1e-6
       and abs(events[2]["total_notional"] - 6000.0) < 1e-6,
       "ETH Open Short 兩事件 notional 各 6000")
    ok(abs(events[3]["total_notional"] - 18300.0) < 1e-6,
       f"BTC Close Long 事件 notional=18300（{events[3]['total_notional']}）")
    ok(abs(events[3]["total_closed_pnl"] - 300.0) < 1e-6,
       f"BTC Close Long 事件 closedPnl 加總=300（{events[3]['total_closed_pnl']}）")

    # dir 缺失 → 退回 (coin, side) 鍵
    no_dir = classify.parse_fills([
        raw("SOL", "150", "1", "B", t0, "0.0", ""),
        raw("SOL", "150", "1", "B", t0 + 10 * minute, "0.0", ""),
        raw("SOL", "150", "1", "A", t0 + 20 * minute, "0.0", ""),
    ])
    ev_sol = classify.aggregate_fills_to_events(no_dir, gap_minutes=60)
    ok(len(ev_sol) == 2 and {e["direction"] for e in ev_sol} == {"B", "A"},
       f"dir 缺失退回 side 鍵（{[(e['direction'], e['n_fills']) for e in ev_sol]}）")

    # 衍生指標：4 事件全落在 30 天窗內；start 序列 gap = [5min, 2h, 1h55m]
    end_ts = (t0 / 1000.0) + 5 * 86400
    stats = classify.compute_event_metrics(fills, end_ts)
    ok(stats["n_events"] == 4 and stats["n_events_last_30d"] == 4,
       f"n_events=4 且 30 日事件數=4（{stats['n_events_last_30d']}）")
    ok(stats["n_events_last_30d_est"] == 4,
       f"未截斷 → 外推值 == 實測值（{stats['n_events_last_30d_est']}）")
    ok(stats["median_fills_per_event"] == 2.5,
       f"median 每事件 fills=2.5（{stats['median_fills_per_event']}）")
    ok(stats["median_event_notional"] == 12150.0,
       f"median 事件名目=12150（{stats['median_event_notional']}）")
    ok(stats["median_gap_between_events_hours"] == 1.92
       and stats["p90_gap_between_events_hours"] == 2.0,
       f"事件間隔 median=1.92h、p90=2.0h（{stats['median_gap_between_events_hours']}/"
       f"{stats['p90_gap_between_events_hours']}）")


def test_followability_events():
    print("[10] followability 升級：頻率以 30 日部位事件數判定，fills 數僅參考不否決")
    base = {"n_fills_last_30d": 800, "n_events_last_30d": 40,
            "avg_hold_hours": 250.0, "current_max_leverage": 3.0}
    ok(base["n_fills_last_30d"] > config.SCAN_FOLLOWABLE_MAX_FREQ,
       f"前提：fills 800 > 舊 fills 門檻 {config.SCAN_FOLLOWABLE_MAX_FREQ}（舊制會否決）")
    ok_flag, reasons = classify.followability(base)
    ok(ok_flag is True and reasons == [],
       f"30 日 fills 800 但事件 40 <= {config.FOLLOWABLE_MAX_EVENTS_30D} → "
       f"頻率條件通過（reasons={reasons}）")

    too_many = dict(base, n_events_last_30d=200)
    ok_flag2, reasons2 = classify.followability(too_many)
    ok(ok_flag2 is False
       and any("頻率過高" in r and "部位事件" in r for r in reasons2),
       f"事件 200 > {config.FOLLOWABLE_MAX_EVENTS_30D} → 不通過（{reasons2}）")
    ok(any("fills 800" in r for r in reasons2), "否決理由同時揭露 fills 數（僅參考）")

    missing = dict(base, n_events_last_30d=None)
    ok_flag3, reasons3 = classify.followability(missing)
    ok(ok_flag3 is False and any("事件數缺失" in r for r in reasons3),
       "事件數缺失 → 保守判不可跟（無法驗證 ≠ 通過）")


def test_truncation_extrapolation():
    print("[12] 截斷防洗白：fills 截斷切進 30 天窗 → 事件數外推，真高頻不被洗白")
    minute = 60 * 1000
    t0 = _ms(2026, 6, 25)
    raw_fills = []
    for b in range(100):  # 100 叢 × 20 筆 = 2000 筆（截斷上限）；叢距 1.5h（>60min 各自成事件）
        base = t0 + b * 90 * minute
        for j in range(20):
            raw_fills.append({"coin": "BTC", "px": "60000", "sz": "0.01", "side": "B",
                              "time": base + j * minute, "closedPnl": "0.0",
                              "dir": "Open Long"})
    fills = classify.parse_fills(raw_fills)
    ok(len(fills) == config.MAX_USER_FILLS,
       f"fixture 2000 筆 = 截斷上限（{len(fills)}）")
    end_ts = datetime(2026, 7, 2, tzinfo=timezone.utc).timestamp()
    stats = classify.compute_event_metrics(fills, end_ts)
    ok(stats["n_events_last_30d"] == 100,
       f"截斷窗實測 30 日事件 100 個（{stats['n_events_last_30d']}；直接用會洗白過門檻）")
    ok(stats["events_30d_coverage_days"] == 7.0,
       f"30 天窗 fills 覆蓋僅 7 天（{stats['events_30d_coverage_days']}）")
    ok(stats["n_events_last_30d_est"] == 429,
       f"外推 30 日事件 = round(100×30/7) = 429（{stats['n_events_last_30d_est']}）")
    metrics = dict(stats, n_fills_last_30d=2000, avg_hold_hours=48.0,
                   current_max_leverage=3.0)
    ok_flag, reasons = classify.followability(metrics)
    ok(ok_flag is False and any("頻率過高" in r and "外推" in r for r in reasons),
       f"外推後頻率仍過高 → 不可跟，真高頻不被截斷窗洗白（{reasons}）")


def test_decision_frequency_dossier(tmp):
    print("[11] track dossier：決策頻率複核節＋升級後可跟性判定＋tracked 名單含 0x8bae35")
    base = json.loads((FIXTURES / "wallet_consistent.json").read_text(encoding="utf-8"))
    addr = base["address"]
    snap_dir = tmp / "snapshots-freq" / SNAP_DATE
    wallets_dir = snap_dir / "wallets"
    wallets_dir.mkdir(parents=True, exist_ok=True)
    (wallets_dir / f"{addr}.json").write_text(
        json.dumps(base, ensure_ascii=False), encoding="utf-8")
    tracked_root = tmp / "tracked-freq"

    dossier = track_wallet.run_track_wallet(addr, snap_dir, tracked_root)
    m = dossier["metrics"]
    ok(m.get("n_events_last_30d") is not None
       and m["n_events_last_30d"] <= m["n_fills_last_30d"],
       f"事件數 <= fills 數（{m['n_events_last_30d']} <= {m['n_fills_last_30d']}）")
    ok(dossier["followable"]["ok"] is True,
       f"wallet_consistent 升級後判可跟（{dossier['followable']}）")

    md_text = (tracked_root / addr / f"dossier_{SNAP_DATE}.md").read_text(encoding="utf-8")
    ok("決策頻率複核" in md_text and "部位事件" in md_text,
       "dossier 含「決策頻率複核（fills → 部位事件）」節")
    ok("升級後可跟性判定" in md_text and "✅" in md_text,
       "dossier 落地升級後可跟性判定結果＋原因")
    ok("median" in md_text and "p90" in md_text, "dossier 含事件間隔分布 median/p90")

    # 0x8bae35 本機無原始 fills，其複核結論由 CI track 步驟產出——確認名單含它即走同一程式路徑
    tracked_addrs = [str(w.get("address", "")).lower() for w in config.TRACKED_WALLETS]
    ok("0x8bae3527e5a33fa0cf184f37bc112d071463ab6d" in tracked_addrs,
       "TRACKED_WALLETS 含 scan-best-candidate-9M-lowdd（0x8bae35…，CI 自動產 dossier）")
    seeds = json.loads((PROJECT_DIR / "data" / "seeds.json").read_text(encoding="utf-8"))
    ok(any(str(w.get("address", "")).lower()
           == "0x8bae3527e5a33fa0cf184f37bc112d071463ab6d" for w in seeds["wallets"]),
       "seeds.json 亦含 0x8bae35（永遠納入宇宙）")


# ---------------------------------------------------------------------------
# hyper_shadow（影子實測）離線測試：純函式＋注入式 http 的完整 session
# ---------------------------------------------------------------------------

# walk-the-book fixture：asks 檔名目 3000 / 7035 / 12120 / 10200 / 10300（cum 3000/10035/22155）
SHADOW_ASKS = [(100.0, 30.0), (100.5, 70.0), (101.0, 120.0), (102.0, 100.0), (103.0, 100.0)]
SHADOW_BIDS = [(99.5, 40.0), (99.0, 80.0), (98.5, 120.0), (98.0, 100.0), (97.5, 100.0)]


def _l2book_raw(coin, bids, asks):
    """官方 l2Book 格式 fixture：{coin, time, levels: [[bids],[asks]]}，px/sz/n 為字串。"""
    return {"coin": coin, "time": 1720000000000, "levels": [
        [{"px": str(p), "sz": str(s), "n": 2} for p, s in bids],
        [{"px": str(p), "sz": str(s), "n": 3} for p, s in asks],
    ]}


def test_shadow_pure_functions():
    print("[12] hyper_shadow 純函式：walk-the-book 滑點／l2Book 解析／info body 白名單／fills 去重")

    # --- walk-the-book：$1k 吃 1 檔、$5k 吃 2 檔、$20k 吃 3 檔，均價正確 ---
    r1 = hyper_shadow.walk_the_book(SHADOW_ASKS, 1000)
    ok(r1["levels_used"] == 1 and abs(r1["avg_px"] - 100.0) < 1e-9,
       f"$1k 吃 1 檔、均價 100（{r1['levels_used']} 檔、{r1['avg_px']}）")
    ok(r1["exhausted"] is False and abs(r1["filled_usd"] - 1000.0) < 1e-6,
       f"$1k 全數成交、未吃穿（filled={r1['filled_usd']}）")
    r5 = hyper_shadow.walk_the_book(SHADOW_ASKS, 5000)
    exp5 = 5000.0 / (30.0 + 2000.0 / 100.5)
    ok(r5["levels_used"] == 2 and abs(r5["avg_px"] - exp5) < 1e-9,
       f"$5k 吃 2 檔、均價 {exp5:.6f}（{r5['levels_used']} 檔、{r5['avg_px']:.6f}）")
    r20 = hyper_shadow.walk_the_book(SHADOW_ASKS, 20000)
    exp20 = 20000.0 / (30.0 + 70.0 + 9965.0 / 101.0)
    ok(r20["levels_used"] == 3 and abs(r20["avg_px"] - exp20) < 1e-9,
       f"$20k 吃 3 檔、均價 {exp20:.6f}（{r20['levels_used']} 檔、{r20['avg_px']:.6f}）")
    total_book = sum(p * s for p, s in SHADOW_ASKS)  # 42655
    rbig = hyper_shadow.walk_the_book(SHADOW_ASKS, 100000)
    ok(rbig["exhausted"] is True and abs(rbig["filled_usd"] - total_book) < 1e-6
       and rbig["levels_used"] == 5,
       f"$100k 吃穿整本簿：exhausted、filled={rbig['filled_usd']}（簿總量 {total_book}）")
    ok(hyper_shadow.walk_the_book([], 1000)["avg_px"] is None, "空簿 → avg_px None")

    # --- l2Book 官方格式解析（builder 市場 coin 名原樣保留）---
    raw = _l2book_raw("xyz:META", SHADOW_BIDS, SHADOW_ASKS)
    book = hyper_shadow.parse_l2book(raw)
    ok(book is not None and book["best_bid"] == 99.5 and book["best_ask"] == 100.0,
       f"best bid/ask = 99.5/100.0（{book['best_bid']}/{book['best_ask']}）")
    exp_spread = 0.5 / 99.75 * 100.0
    ok(abs(book["spread_pct"] - round(exp_spread, 4)) < 1e-9,
       f"spread% = {exp_spread:.4f}（{book['spread_pct']}）")
    ok(book["top_bid_notional_usd"] == 43270.0 and book["top_ask_notional_usd"] == 42655.0,
       f"前 5 檔累計名目 買 43270 / 賣 42655（{book['top_bid_notional_usd']}/"
       f"{book['top_ask_notional_usd']}）")
    ok(hyper_shadow.parse_l2book({"levels": "nope"}) is None
       and hyper_shadow.parse_l2book(None) is None
       and hyper_shadow.parse_l2book({"levels": [[], []]}) is None,
       "壞形狀/空簿 l2Book → None（不 crash）")

    # --- 滑點剖面：dev_vs_mid 正負與量值（mid=99.75）---
    sl = hyper_shadow.slippage_profile(book)
    exp_buy_1k = round((100.0 - 99.75) / 99.75 * 100.0, 4)
    exp_sell_1k = round((99.75 - 99.5) / 99.75 * 100.0, 4)
    ok(abs(sl["buy"]["1000"]["dev_vs_mid_pct"] - exp_buy_1k) < 1e-9,
       f"$1k 買方偏離 mid = {exp_buy_1k}%（{sl['buy']['1000']['dev_vs_mid_pct']}%）")
    ok(abs(sl["sell"]["1000"]["dev_vs_mid_pct"] - exp_sell_1k) < 1e-9,
       f"$1k 賣方偏離 mid = {exp_sell_1k}%（{sl['sell']['1000']['dev_vs_mid_pct']}%）")
    ok(sl["buy"]["20000"]["levels_used"] == 3 and sl["buy"]["20000"]["dev_vs_mid_pct"] > exp_buy_1k,
       "$20k 買方吃 3 檔且偏離大於 $1k（名目越大滑點越深）")

    # --- info body 白名單＋builder coin 名原樣傳遞（HIP-3 命名慣例）---
    ok(hyper_shadow.info_body("l2Book", coin="xyz:META")
       == {"type": "l2Book", "coin": "xyz:META"},
       "l2Book 請求體對 'xyz:META' 原樣傳字串")
    ok(hyper_shadow.info_body("l2Book", coin="@166") == {"type": "l2Book", "coin": "@166"},
       "l2Book 請求體對 '@166' 原樣傳字串")
    ok(hyper_shadow.info_body("userFills", address="0xabc")
       == {"type": "userFills", "user": "0xabc"}, "userFills 請求體形狀正確")
    try:
        hyper_shadow.info_body("portfolio", address="0xabc")
        whitelist_raised = False
    except ValueError:
        whitelist_raised = True
    ok(whitelist_raised, "白名單外的 info type（portfolio）→ ValueError（唯讀邊界硬限）")

    # --- fills 去重（tid 優先；hash 次之；欄位組合墊底）---
    f_tid = {"tid": 111, "hash": "0xaaa", "coin": "@166", "side": "B", "sz": "10",
             "px": "1.5", "time": 1720000000000}
    f_hash = {"hash": "0xbbb", "coin": "@166", "side": "A", "sz": "5",
              "px": "1.5", "time": 1720000001000}
    f_fields = {"coin": "xyz:META", "side": "B", "sz": "3", "px": "9.9",
                "time": 1720000002000}
    seen = set()
    new = hyper_shadow.detect_new_fills([f_tid, f_tid, f_hash, f_fields], seen)
    ok(len(new) == 3, f"首輪去重：4 筆（含 1 重複）→ 3 筆新（{len(new)}）")
    again = hyper_shadow.detect_new_fills([f_tid, f_hash, f_fields], seen)
    ok(len(again) == 0, "次輪同批 fills → 0 筆新（tid/hash/欄位鍵皆命中）")
    f_tid2 = dict(f_tid, tid=222)
    ok(len(hyper_shadow.detect_new_fills([f_tid2], seen)) == 1, "新 tid → 偵測為新成交")

    # --- 近 30 天活躍幣種統計（coin 字串原樣保留）---
    now_ts = 1720000000.0
    fills = ([{"coin": "@166", "time": (now_ts - 86400) * 1000}] * 3
             + [{"coin": "xyz:META", "time": (now_ts - 5 * 86400) * 1000}] * 2
             + [{"coin": "BTC", "time": (now_ts - 40 * 86400) * 1000}] * 9)
    top, counter = hyper_shadow.active_coins(fills, now_ts)
    ok(top and top[0] == ("@166", 3) and counter.get("xyz:META") == 2,
       f"活躍 top：@166×3、xyz:META×2（{top}）")
    ok("BTC" not in counter, "40 天前的 fills 不入 30 天窗（BTC 排除）")

    # --- 預設地址解析（label 含 scan-best-candidate）---
    ok(hyper_shadow.default_address() == "0x8bae3527e5a33fa0cf184f37bc112d071463ab6d",
       f"預設 address = scan-best-candidate（{hyper_shadow.default_address()}）")


class _FakeClock:
    def __init__(self, start=1720000000.0):
        self.t = start

    def now(self):
        return self.t

    def sleep(self, sec):
        self.t += max(0.0, float(sec))


class _ScriptedInfoAPI:
    """注入式 http_post：按 body['type'] 回應腳本資料；userFills 第 N 次呼叫起冒出新 fill。"""

    def __init__(self, chs, base_fills, books, mids, new_fill=None, new_fill_from_call=3):
        self.chs = chs
        self.base_fills = base_fills
        self.books = books
        self.mids = mids
        self.new_fill = new_fill
        self.new_fill_from_call = new_fill_from_call
        self.userfills_calls = 0
        self.book_requests = []

    def __call__(self, body):
        t = body.get("type")
        if t == "clearinghouseState":
            return self.chs, None
        if t == "allMids":
            return self.mids, None
        if t == "userFills":
            self.userfills_calls += 1
            fills = list(self.base_fills)
            if self.new_fill is not None and self.userfills_calls >= self.new_fill_from_call:
                fills = [self.new_fill] + fills
            return fills, None
        if t == "l2Book":
            coin = body.get("coin")
            self.book_requests.append(coin)  # 驗證 coin 原樣傳遞
            book = self.books.get(coin)
            return (book, None) if book is not None else (None, "HTTP 422; body=unknown coin")
        return None, f"unexpected type {t}"


def test_shadow_session_offline(tmp):
    print("[13] hyper_shadow 離線 session：深度剖面（開/收班）＋新成交偵測延遲/劣化＋摘要落地")
    clock = _FakeClock()
    addr = "0x8bae3527e5a33fa0cf184f37bc112d071463ab6d"
    chs = {"assetPositions": [{"type": "oneWay", "position": {
        "coin": "xyz:META", "szi": "100", "entryPx": "10", "positionValue": "1000",
        "unrealizedPnl": "5", "leverage": {"type": "cross", "value": 3},
        "liquidationPx": "5", "marginUsed": "300", "maxLeverage": 10,
        "cumFunding": {"allTime": "1.0"}}}],
        "marginSummary": {"accountValue": "50000"}}
    base_ms = int((clock.t - 86400) * 1000)
    base_fills = [
        {"tid": 1, "coin": "@166", "side": "B", "px": "1.5", "sz": "100",
         "time": base_ms, "dir": "Open Long", "closedPnl": "0.0"},
        {"tid": 2, "coin": "@166", "side": "A", "px": "1.51", "sz": "100",
         "time": base_ms + 60000, "dir": "Close Long", "closedPnl": "1.0"},
    ]
    # @166 簿面：mid=1.5，$1k 買方一檔就吃得下（1.501×5000≈$7.5k）
    books = {
        "xyz:META": _l2book_raw("xyz:META", SHADOW_BIDS, SHADOW_ASKS),
        "@166": _l2book_raw("@166", [(1.499, 5000), (1.498, 10000)],
                            [(1.501, 5000), (1.502, 10000)]),
    }
    # 新 fill：時間 = 開班 +2s，偵測應在其後幾秒內（lag 小而非負大）
    new_fill = {"tid": 99, "coin": "@166", "side": "B", "px": "1.5", "sz": "666",
                "time": int((clock.t + 2) * 1000), "dir": "Open Long", "closedPnl": "0.0"}
    api = _ScriptedInfoAPI(chs, base_fills, books, {"BTC": "60000"},
                           new_fill=new_fill, new_fill_from_call=3)

    info = hyper_shadow.run_session(addr, duration_min=0.15, poll_sec=1.0,
                                    out_root=tmp / "shadow-ok", http_post=api,
                                    sleep_fn=clock.sleep, now_fn=clock.now)

    coins = [t["coin"] for t in info["targets"]]
    ok(set(coins) == {"xyz:META", "@166"},
       f"目標市場 = 持倉 ∪ 活躍（{coins}）")
    ok(info["main_market"] == "@166",
       f"主力市場 = 30d fills 最多者 @166（{info['main_market']}）")
    ok("xyz:META" in api.book_requests and "@166" in api.book_requests,
       "l2Book 請求體對 builder coin 名（xyz:META／@166）原樣傳字串")
    ok(info["baseline_seeded"] == 2, f"baseline 略過既有成交 2 筆（{info['baseline_seeded']}）")
    ok(info["new_fills"]["n_detected"] == 1,
       f"班內偵測 1 筆新成交（{info['new_fills']['n_detected']}）")

    out_dir = tmp / "shadow-ok" / addr
    jsonl = (out_dir / info["jsonl_file"]).read_text(encoding="utf-8").strip().splitlines()
    rows = [json.loads(l) for l in jsonl]
    depth_rows = [r for r in rows if r["kind"] == "depth_profile"]
    fill_rows = [r for r in rows if r["kind"] == "fill_event"]
    ok(len(depth_rows) == 4, f"深度剖面 2 市場 × 開/收班 = 4 列（{len(depth_rows)}）")
    ok({(r["coin"], r["pass"]) for r in depth_rows}
       == {("xyz:META", "open"), ("xyz:META", "close"), ("@166", "open"), ("@166", "close")},
       "深度剖面覆蓋兩市場的 open/close 班次")
    meta_open = next(r for r in depth_rows if r["coin"] == "xyz:META" and r["pass"] == "open")
    ok(meta_open["slippage"]["buy"]["20000"]["levels_used"] == 3,
       "深度列含 walk-the-book 剖面（xyz:META $20k 買 3 檔）")
    ok(meta_open["mid_allmids"] is None,
       "builder 市場不在預設 allMids 映射 → mid_allmids None（預期、不影響剖面）")

    ok(len(fill_rows) == 1, f"新成交事件 1 列（{len(fill_rows)}）")
    fr = fill_rows[0]
    ok(fr["coin"] == "@166" and fr["follower_side"] == "buy",
       f"fill 事件：@166 買方（{fr['coin']}/{fr['follower_side']}）")
    ok(fr["detect_lag_sec"] is not None and -5 <= fr["detect_lag_sec"] <= 30,
       f"detect_lag 合理（{fr['detect_lag_sec']}s）")
    exp_deg = round((1.501 - 1.5) / 1.5 * 100.0, 4)
    ok(fr["copy_1k"] and abs(fr["copy_1k"]["degradation_vs_fill_pct"] - exp_deg) < 1e-6,
       f"$1k 跟單劣化 = {exp_deg}%（{fr['copy_1k']['degradation_vs_fill_pct']}%）")

    exp_rt = round((1.501 - 1.5) / 1.5 * 100.0, 4) + round((1.5 - 1.499) / 1.5 * 100.0, 4)
    ok(info["roundtrip_1k_pct"] and info["roundtrip_1k_pct"]["coin"] == "@166"
       and abs(info["roundtrip_1k_pct"]["value"] - round(exp_rt, 4)) < 1e-6,
       f"$1k 往返成本 = 買賣偏離 mid 之和 ≈ {exp_rt:.4f}%（{info['roundtrip_1k_pct']}）")

    md = (out_dir / f"summary_{info['date']}.md").read_text(encoding="utf-8")
    ok("誠實聲明" in md and "時點快照" in md and "不構成投資建議" in md,
       "summary md 頂部含誠實聲明（快照非成交保證/不下單/非投資建議）")
    ok("xyz:META" in md and "@166" in md and "深度剖面" in md,
       "summary md 含兩市場的深度剖面表")
    ok("往返成本估算" in md, "summary md 含 $1k 主力市場往返成本估算")
    ok("新成交監測" in md and "1" in md, "summary md 含新成交監測節")


def test_shadow_all_requests_fail(tmp):
    print("[14] hyper_shadow 全請求失敗：優雅結束、summary 含錯誤計數、0 新成交標「預期內」")
    clock = _FakeClock()
    addr = "0x8bae3527e5a33fa0cf184f37bc112d071463ab6d"

    def dead_http(body):
        return None, "HTTP 403; body=blocked by proxy"

    info = hyper_shadow.run_session(addr, duration_min=0.05, poll_sec=1.0,
                                    out_root=tmp / "shadow-dead", http_post=dead_http,
                                    sleep_fn=clock.sleep, now_fn=clock.now)
    ok(info["targets"] == [] and len(info["discovery_errors"]) == 2,
       f"探索全失敗 → 無目標市場、錯誤 2 筆（{info['discovery_errors']}）")
    ok(info["polls"] >= 1 and info["fills_poll_failures"] == info["polls"],
       f"輪詢全數失敗被如實計數（{info['fills_poll_failures']}/{info['polls']}）")
    ok(info["new_fills"]["n_detected"] == 0, "0 筆新成交")

    out_dir = tmp / "shadow-dead" / addr
    md_path = out_dir / f"summary_{info['date']}.md"
    md = md_path.read_text(encoding="utf-8")
    ok("預期內" in md, "0 新成交的 summary md 含「預期內」字樣（低頻常態，不算失敗）")
    ok("輪詢全數失敗" in md, "輪詢全掛時 md 額外註明「抓不到 ≠ 沒有」")
    ok("探索階段錯誤" in md and "403" in md, "summary md 含探索錯誤計錄")

    # 同日第二個 session → json sessions append、md 段落 append
    clock.sleep(60)
    info2 = hyper_shadow.run_session(addr, duration_min=0.05, poll_sec=1.0,
                                     out_root=tmp / "shadow-dead", http_post=dead_http,
                                     sleep_fn=clock.sleep, now_fn=clock.now)
    payload = json.loads((out_dir / f"summary_{info2['date']}.json").read_text(encoding="utf-8"))
    ok(len(payload["sessions"]) == 2, f"同日兩 session → json append（{len(payload['sessions'])}）")
    md2 = md_path.read_text(encoding="utf-8")
    ok(md2.count("## Session") == 2, "同日兩 session → md append 兩段")
    ok(any("誠實聲明" in c for c in payload["caveats"]), "summary json 含 caveats 誠實聲明")


def main():
    with tempfile.TemporaryDirectory(prefix="hyper-observer-test-") as td:
        tmp = Path(td)
        test_classification()
        test_metrics_sanity()
        test_bugfix_metrics_and_classify()
        test_final_bugfix_A_B()
        test_reports(tmp)
        test_track_wallet(tmp)
        test_scan_universe(tmp)
        test_scan_report(tmp)
        test_fetch_wallets_file(tmp)
        test_fetch_fallback()
        test_aggregate_events()
        test_followability_events()
        test_truncation_extrapolation()
        test_decision_frequency_dossier(tmp)
        test_shadow_pure_functions()
        test_shadow_session_offline(tmp)
        test_shadow_all_requests_fail(tmp)
    print(f"ALL TESTS PASSED ({checks} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
