#!/usr/bin/env python3
"""monitor 離線測試 — 用 repo 現有真實數據跑 build，驗證產出。

不觸網、不寫 docs/（輸出到暫存目錄）、不改動真實數據
（缺失數據源用「只複製部分數據源的暫存 repo-root」模擬，等效於暫時改名）。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import build_monitor  # noqa: E402

ROOT = build_monitor.DEFAULT_ROOT
CHECKS = 0


def check(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    print(f"  ok: {msg}")


def extract_data(html):
    m = re.search(
        r'<script id="monitor-data" type="application/json">(.*?)</script>',
        html, re.S)
    check(m is not None, "HTML 內含 monitor-data JSON 區塊")
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_full_build(tmp):
    print("[1] 真實數據完整 build")
    out = os.path.join(tmp, "full", "index.html")
    data, size = build_monitor.render(ROOT, out)
    check(os.path.isfile(out), "index.html 已產出")
    check(size < 1_000_000, f"產物 {size:,} bytes < 1MB")

    html = open(out, encoding="utf-8").read()
    check("聰明錢系統監控" in html, "含「聰明錢系統監控」標題")
    check("0x8bae35" in html, "含 0x8bae35 追蹤數據")
    for title in ("HL 持續贏家追蹤", "美股 Form 4 漏斗", "台股漏斗", "系統狀態板"):
        check(title in html, f"含區塊標題「{title}」")

    # 無外部依賴：不得有外連 script/css/img/fetch/CDN
    for pat, desc in [
        (r'(src|href)\s*=\s*["\']https?://', "無外部 src/href 引用"),
        (r'url\(\s*["\']?https?://', "CSS 無外部 url()"),
        (r'@import', "CSS 無 @import"),
        (r'\bfetch\s*\(', "JS 無 fetch()"),
        (r'XMLHttpRequest', "JS 無 XHR"),
    ]:
        check(re.search(pat, html) is None, desc)

    d = extract_data(html)
    check(d["hl"]["available"] is True, "HL 數據源可用")
    check(abs(d["hl"]["metrics"]["total_pnl"]) > 0, "HL total_pnl 有值")
    check(len(d["hl"]["gates"]) == 7, "證據閘門 7 項")
    check(len(d["hl"]["monthly_pnl"]) >= 6, "月度 PnL ≥6 個月")
    check(len(d["pipelines"]) == 7, "系統狀態板 7 條管線")
    mb = [p for p in d["pipelines"] if p["id"] == "monitor-build"][0]
    check(mb["ts"] == d["generated_at"], "monitor-build 時間戳＝generated_at")
    # us/tw funnel 缺檔時（並行 agent 建置中）為佔位；存在時必含 funnel_stats
    for k in ("us_funnel", "tw_funnel"):
        if d[k]["available"]:
            check("funnel_stats" in d[k], f"{k} 含 funnel_stats")
        else:
            check("placeholder" in d[k], f"{k} 缺檔 → 有佔位文案")
    check("允許 JavaScript" in html or "JavaScript" in html, "有 noscript 提示")


def test_missing_sources(tmp):
    print("[2] 缺失數據源模擬（部分複製 = 暫時改名等效）")
    # 只複製 poly-observer 數據；hyper/us/tw 缺失
    skel = os.path.join(tmp, "skel")
    src = os.path.join(ROOT, "projects", "poly-observer", "data")
    dst = os.path.join(skel, "projects", "poly-observer", "data")
    shutil.copytree(src, dst,
                    ignore=shutil.ignore_patterns("latest_raw.json", "*.jsonl",
                                                  "snapshots", "probe"))
    out = os.path.join(skel, "index.html")
    data, size = build_monitor.render(skel, out)
    html = open(out, encoding="utf-8").read()
    d = extract_data(html)
    check(d["hl"]["available"] is False, "hyper dossier 缺失 → hl.available=False")
    check("建置中" in d["hl"]["placeholder"], "HL 佔位含「建置中」")
    check(d["us_funnel"]["available"] is False
          and "建置中" in d["us_funnel"]["placeholder"], "us-funnel 佔位含「建置中」")
    check(d["tw_funnel"]["available"] is False
          and "建置中" in d["tw_funnel"]["placeholder"], "tw-funnel 佔位含「建置中」")
    check(d["poly"]["available"] is True, "poly 數據源獨立存活")
    check("建置中" in html, "頁面含「建置中」佔位")
    hyper_rows = [p for p in d["pipelines"] if p["id"] in
                  ("hyper-observer", "us-funnel", "tw-funnel")]
    check(all(p["ts"] is None for p in hyper_rows), "缺檔管線 ts=None（狀態燈紅）")

    print("[3] 全空 repo-root（所有數據源缺失）")
    empty = os.path.join(tmp, "empty")
    os.makedirs(empty)
    out2 = os.path.join(empty, "index.html")
    data2, _ = build_monitor.render(empty, out2)
    check(all(not data2[k]["available"]
              for k in ("hl", "poly", "us_funnel", "tw_funnel")),
          "全缺失時所有 available=False（build 不炸）")
    check("聰明錢系統監控" in open(out2, encoding="utf-8").read(),
          "全缺失時頁面仍完整產出")


def test_risk_rendering(tmp):
    print("[4] 美股風險欄：含 risk 假數據透傳＋渲染字串；舊數據無 risk 欄不炸")
    skel = os.path.join(tmp, "risk")
    ddir = os.path.join(skel, "projects", "us-funnel", "data")
    os.makedirs(ddir)
    cands = {
        "generated_at": "2026-07-11T03:45:00+00:00",
        "scan_window_days": 7,
        "funnel_stats": {"raw_filings": 100, "qualified_events": 5,
                         "post_veto": 3, "final_candidates": 3},
        "candidates": [
            {"ticker": "AAA", "company": "Alpha", "score": 7,
             "first_filing_date": "2026-07-08", "entry_price_ref": 10.0,
             "risk": {"level": "high", "data_gap": True, "beta": None,
                      "mcap_usd": None, "mcap_band": "unknown",
                      "beta_band": "unknown"}},
            {"ticker": "BBB", "company": "Beta Corp", "score": 5,
             "first_filing_date": "2026-07-07", "entry_price_ref": 20.0,
             "risk": {"level": "low", "data_gap": False, "beta": 0.55,
                      "mcap_usd": 52000000000, "mcap_band": "large",
                      "beta_band": "low"}},
            {"ticker": "CCC", "company": "Legacy Inc", "score": 4,
             "first_filing_date": "2026-07-06", "entry_price_ref": 5.0},
        ],
    }
    with open(os.path.join(ddir, "candidates_latest.json"), "w",
              encoding="utf-8") as f:
        json.dump(cands, f, ensure_ascii=False)
    out = os.path.join(skel, "index.html")
    data, _ = build_monitor.render(skel, out)
    html = open(out, encoding="utf-8").read()
    d = extract_data(html)

    us = d["us_funnel"]["candidates"]
    check(us[0]["risk"]["level"] == "high" and us[0]["risk"]["data_gap"] is True,
          "high(data_gap) 候選：risk 透傳完整")
    check(us[1]["risk"]["level"] == "low" and us[1]["risk"]["beta"] == 0.55
          and us[1]["risk"]["mcap_band"] == "large", "low 候選：beta/mcap_band 透傳")
    check(set(us[0]["risk"].keys()) ==
          {"level", "data_gap", "beta", "mcap_usd", "mcap_band", "beta_band"},
          "risk 鍵集合與 us-funnel 契約一致")
    check(us[2].get("risk") is None, "舊數據無 risk 欄 → None（build 不炸，前端顯示—）")
    check("<th>風險</th>" in html, "美股候選表含「風險」欄表頭")
    check("high:['高'" in html and "medium:['中'" in html and "low:['低'" in html,
          "高/中/低標籤與 semantic 色映射存在（JS 渲染）")
    check("風險分級劃分方法" in html, "含「風險分級劃分方法」備註標題")
    check("非基本面/違約風險評估" in html, "備註含免責一句")
    check("保守計分" in html and "加 <b>*</b>" in html,
          "備註含「數據不足一律保守計分＋加*」規則")


# ── 多場所（multi-venue）視圖 ───────────────────────────────────────
# fixture 為 diagnostic_2026-07-27.json（0x8bae…ab6d）必要片段的複本，
# 刻意「複製進測試」而非讀 repo 路徑：測試不得依賴 hyper-observer 產出。

HL_DIR = ("projects", "hyper-observer", "data", "tracked",
          build_monitor.HL_ADDR)

# 真實診斷片段（金額/欄位名逐字取自 diagnostic_2026-07-27.json）
DIAG_FIXTURE = {
    "address": build_monitor.HL_ADDR,
    "date": "2026-07-27",
    "ledger_window_days": 45,
    "dexs_detected": ["xyz", "flx", "vntl"],
    "trading": {
        "n_fills": 2000, "truncated": True,
        "last_fill_iso": "2026-07-23T18:28:43.930000+00:00",
        "days_since_last_fill": 3.31, "n_fills_7d": 844, "n_fills_30d": 2000,
        "by_venue": {"builder:xyz": 1766, "native": 120, "spot": 114},
    },
    "funds": {
        "native": {"n_positions": 0, "account_value": 0.0, "position_value": 0},
        "builder_dex": {
            "xyz": {"n_positions": 3, "account_value": 43542.00998,
                    "position_value": 1004536.91},
            "flx": {"n_positions": 0, "account_value": 0.0, "position_value": 0},
            "vntl": {"n_positions": 0, "account_value": 0.0, "position_value": 0},
        },
        "spot": {"n_nonzero": 3, "usd_stable": 4026524.58,
                 "usd_est_other": 48215.25, "usd_total_est": 4074739.83,
                 "estimated": True},
        "native_usd": 0.0, "builder_usd": 43542.01, "spot_usd": 4074739.83,
        "total_usd": 4118281.84, "non_native_usd": 4118281.84,
        "non_native_share": 1.0,
        "positions": [
            {"coin": "xyz:META", "szi": 1632.557, "side": "long",
             "entry_px": 640.567, "position_value": 980595.36205,
             "unrealized_pnl": -65166.955494, "leverage_value": 20.0,
             "leverage_type": "cross", "dex": "xyz"},
            {"coin": "xyz:GOOGL", "szi": 47.464, "side": "long",
             "entry_px": 328.825, "position_value": 15286.25584,
             "unrealized_pnl": -321.10288, "leverage_value": 10.0,
             "leverage_type": "cross", "dex": "xyz"},
            {"coin": "xyz:KIOXIA", "szi": 26.935, "side": "long",
             "entry_px": 408.418, "position_value": 8655.2929,
             "unrealized_pnl": -2345.456076, "leverage_value": 4.0,
             "leverage_type": "isolated", "dex": "xyz"},
        ],
        "n_positions_total": 3, "n_positions_native": 0,
        "n_positions_builder": 3, "known": True,
    },
    "ledger": {
        "n_total": 3, "n_in_window": 3, "n_kept": 3,
        "by_type": {"send": {"n": 3, "usd": 2500000.0, "direction": "unknown"}},
        "external_out_usd": 0.0, "external_in_usd": 0.0, "internal_usd": 0.0,
        "vault_out_usd": 0.0, "unknown_usd": 2500000.0,
        "rows": [
            # destination 0x2000…0000 ＝ HyperCore→HyperEVM 系統地址（同一擁有者跨層）
            {"time_iso": "2026-07-17T02:59:04.334000+00:00", "type": "send",
             "usd": 800000.0, "direction": "unknown", "token": "USDC",
             "destination": "0x2000000000000000000000000000000000000000"},
            {"time_iso": "2026-07-07T15:35:09.138000+00:00", "type": "send",
             "usd": 900000.0, "direction": "unknown", "token": "USDC",
             "destination": "0x2000000000000000000000000000000000000000"},
            {"time_iso": "2026-06-29T07:52:30.312000+00:00", "type": "send",
             "usd": 800000.0, "direction": "unknown", "token": "USDC",
             "destination": "0x2000000000000000000000000000000000000000"},
        ],
    },
    "verdict": "同地址換戰場（builder dex/現貨）",
}

DOSSIER_BASE = {
    "address": build_monitor.HL_ADDR,
    "label": "scan-best-candidate-9M-lowdd",
    "classification": "consistent_winner",
    "snapshot_date": "2026-07-27",
    "position_value": 0, "unrealized_pnl": 0.0,
    "n_open_positions": 3, "open_positions": [],
    "metrics": {
        "total_pnl": 9625689.72, "peak_pnl": 9700000.0,
        "max_drawdown_pct": 0.08, "current_drawdown_pct": 0.01,
        "profit_factor": 2.4, "realized_win_rate": 0.61,
        "avg_win": 5000.0, "avg_loss": -2000.0, "avg_hold_hours": 30.0,
        "n_events_last_30d": 40, "median_event_notional": 120000.0,
        "positive_month_ratio": 0.9, "current_max_leverage": 20.0,
        "has_extreme_leverage": False, "n_liquidations": 0, "span_days": 380,
        "monthly_pnl": {"2026-0%d" % i: 1000.0 * i for i in range(1, 8)},
    },
}


def _write_hl(skel, dossier, diag=None, diag_date="2026-07-27"):
    d = os.path.join(skel, *HL_DIR)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "dossier_%s.json" % dossier["snapshot_date"]),
              "w", encoding="utf-8") as f:
        json.dump(dossier, f, ensure_ascii=False)
    if diag is not None:
        with open(os.path.join(d, "diagnostic_%s.json" % diag_date),
                  "w", encoding="utf-8") as f:
            json.dump(diag, f, ensure_ascii=False)
    return d


def test_venues_full(tmp):
    print("[5] 多場所視圖：完整 by-dex ＋ diagnostic")
    skel = os.path.join(tmp, "venues-full")
    dossier = json.loads(json.dumps(DOSSIER_BASE))
    dossier["metrics"].update({
        "account_value": 43286.44,
        # "" ＝原生（hyper-observer classify 的原生鍵）
        "account_value_by_dex": {"": 0.0, "xyz": 43286.44, "flx": 0.0, "vntl": 0.0},
        "account_value_native": 0.0,
        "dexs_with_positions": ["xyz"],
        "n_open_positions_native": 0,
    })
    _write_hl(skel, dossier, DIAG_FIXTURE)
    out = os.path.join(skel, "index.html")
    build_monitor.render(skel, out)
    html = open(out, encoding="utf-8").read()
    d = extract_data(html)
    vn = d["hl"]["venues"]

    check(vn["available"] is True, "venues.available=True")
    ids = [r["id"] for r in vn["rows"]]
    check(ids == ["native", "xyz", "spot"],
          "場所列＝原生→builder dex→現貨（零餘額 dex 收進備註）")
    check(vn["zero_venues"] == ["flx", "vntl"], "零餘額 builder dex 收進 zero_venues")
    xyz = [r for r in vn["rows"] if r["id"] == "xyz"][0]
    check(xyz["n_positions"] == 3 and xyz["notional"] == 1004536.91,
          "xyz 列帶未平倉數 3 與名目 $1,004,536.91")
    spot = [r for r in vn["rows"] if r["id"] == "spot"][0]
    check(spot["account_value"] == 4074739.83 and spot["notional"] is None,
          "現貨列帶 spot_usd、名目為 None（現貨無名目概念）")
    check(vn["total_usd"] == round(0.0 + 43286.44 + 4074739.83, 2),
          "合計＝表內各列之和（表格自洽）")
    check(abs(sum(r["share"] for r in vn["rows"]) - 1.0) < 1e-9,
          "各列占比加總＝100%")
    check(vn["non_native_share"] == 1.0 and "主要活動不在原生 dex" in vn["non_native_alert"],
          "非原生占比高 → 產生「主要活動不在原生 dex」提示")
    check(vn["diagnostic_date"] == "2026-07-27", "記錄診斷資料日期供頁面標示")
    check(sorted(vn["sources"]) == ["diagnostic", "dossier"], "來源同時含 dossier 與 diagnostic")

    # 持倉：dossier open_positions 為空 → 退回診斷的多場所持倉，且每筆帶場所
    hp = d["hl"]["positions"]
    check(d["hl"]["positions_source"] == "diagnostic" and len(hp) == 3,
          "dossier open_positions 空 → 改用診斷持倉（3 檔）")
    check(all(p["venue"] == "xyz" for p in hp), "每筆持倉帶場所欄＝xyz")

    # 資金流動
    fl = d["hl"]["flows"]
    check(fl["available"] is True and fl["cross_layer_usd"] == 2500000.0
          and fl["cross_layer_n"] == 3,
          "跨層轉出 $2,500,000／3 筆（destination 為 0x2000…0000 系統地址）")
    check(fl["external_out_usd"] == 0.0 and fl["external_out_n"] == 0,
          "真外轉 $0／0 筆（未把跨層誤算成外轉）")
    check(fl["days_since_last_fill"] == 3.31 and fl["n_fills_7d"] == 844,
          "帶出最後成交距今 3.31 天與近 7 日成交數")
    check(fl["fills_non_native"] == 1880 and fl["fills_non_native_share"] == 0.94,
          "成交戰場分布：非原生 1880/2000（94%）")

    # 頁面渲染程式碼與字串
    for s in ("資金分布（多場所", "<th>場所</th>", "資金流動",
              "占總資產 %", "帳戶淨值 USD", "未平倉數",
              "<tr class=\"total\"><td>合計</td>", "診斷資料日期"):
        check(s in html, f"頁面含「{s}」")
    check("HyperCore → HyperEVM" in html and "資金仍屬同一擁有者" in html
          and "非轉給第三方" in html,
          "跨層轉出措辭精確（同一擁有者跨層，非轉給第三方）")
    check("真外轉" in html and "轉到他人地址" in html, "區分「真外轉」＝轉到他人地址")
    check("xyz" in html, "頁面含 builder dex 名稱 xyz")


def test_venues_legacy(tmp):
    print("[6] 舊格式 dossier（無 by_dex、無 diagnostic）→ 優雅降級")
    skel = os.path.join(tmp, "venues-legacy")
    dossier = json.loads(json.dumps(DOSSIER_BASE))
    dossier["metrics"]["account_value"] = 1234.5
    dossier["position_value"] = 5000.0
    dossier["unrealized_pnl"] = -12.5
    dossier["open_positions"] = [
        {"coin": "BTC", "side": "long", "leverage_value": 5, "leverage_type": "cross",
         "position_value": 5000.0, "entry_px": 60000.0, "unrealized_pnl": -12.5},
        {"coin": "abc:ETH", "side": "short", "leverage_value": 3, "leverage_type": "cross",
         "position_value": 800.0, "entry_px": 3000.0, "unrealized_pnl": 4.0},
        {"coin": "@166", "side": "long", "leverage_value": 1, "leverage_type": "cross",
         "position_value": 100.0, "entry_px": 1.0, "unrealized_pnl": 0.0},
    ]
    _write_hl(skel, dossier, diag=None)
    out = os.path.join(skel, "index.html")
    build_monitor.render(skel, out)
    html = open(out, encoding="utf-8").read()
    d = extract_data(html)

    check(d["hl"]["available"] is True, "舊格式 dossier 仍可用（build 不炸）")
    check(d["hl"]["venues"]["available"] is False,
          "無 by_dex 也無 diagnostic → venues.available=False（區塊隱藏）")
    check(d["hl"]["venues"]["rows"] == []
          and d["hl"]["venues"]["diagnostic_date"] is None,
          "降級時 rows 為空、診斷日期為 None")
    check(d["hl"]["flows"]["available"] is False,
          "無 diagnostic → flows.available=False（資金流動塊隱藏）")
    check("聰明錢系統監控" in html and "HL 持續贏家追蹤" in html,
          "降級時頁面仍完整產出")
    check(d["hl"]["positions_source"] == "dossier" and len(d["hl"]["positions"]) == 3,
          "持倉沿用 dossier open_positions")
    venues = [p["venue"] for p in d["hl"]["positions"]]
    check(venues == ["原生", "abc", "現貨"],
          "場所推導：無 dex 欄→原生、coin 前綴 abc:→abc、@166→現貨")
    check("<th>場所</th>" in html, "持倉表場所欄在降級時仍存在（值為推導結果）")


def test_venue_share_math(tmp):
    print("[7] 占比計算與分母 0 防呆")
    check(build_monitor.share_of(50, 200) == 0.25, "share_of(50,200)=0.25")
    check(build_monitor.share_of(1, 0) is None, "分母 0 → None（不炸、不 ZeroDivisionError）")
    check(build_monitor.share_of(1, None) is None, "分母缺失 → None")
    check(build_monitor.share_of(None, 100) is None, "分子缺失 → None")
    check(build_monitor.share_of(float("nan"), 100) is None, "NaN 分子 → None")

    # 全零場所（分母 0）：走完整 build，占比全 None，不得產出 NaN
    skel = os.path.join(tmp, "venues-zero")
    dossier = json.loads(json.dumps(DOSSIER_BASE))
    dossier["metrics"].update({
        "account_value": 0.0,
        "account_value_by_dex": {"": 0.0, "xyz": 0.0},
        "account_value_native": 0.0,
    })
    diag = json.loads(json.dumps(DIAG_FIXTURE))
    diag["funds"] = {
        "native": {"n_positions": 0, "account_value": 0.0, "position_value": 0},
        "builder_dex": {"xyz": {"n_positions": 0, "account_value": 0.0,
                                "position_value": 0}},
        "spot": {"n_nonzero": 0, "usd_total_est": 0.0, "estimated": False},
        "spot_usd": 0.0, "total_usd": 0.0, "positions": [],
    }
    _write_hl(skel, dossier, diag)
    out = os.path.join(skel, "index.html")
    build_monitor.render(skel, out)
    html = open(out, encoding="utf-8").read()
    d = extract_data(html)
    vn = d["hl"]["venues"]
    check(vn["available"] is True and vn["total_usd"] == 0.0,
          "全零場所：venues 仍可用、合計 0")
    check(all(r["share"] is None for r in vn["rows"]),
          "分母 0 → 每列占比 None（前端顯示「—」）")
    check(vn.get("non_native_alert") is None,
          "非原生占比無法計算 → 不發出誤導性提示")
    blob = re.search(r'<script id="monitor-data" type="application/json">(.*?)</script>',
                     html, re.S).group(1)
    check("NaN" not in blob and "Infinity" not in blob,
          "嵌入的 JSON 不含 NaN/Infinity（json.dumps allow_nan=False 會炸）")
    check(d["hl"]["positions"] == [] and d["hl"]["positions_notional"] is None,
          "無持倉時持倉合計為 None（不炸）")


def test_diagnostic_edge_cases(tmp):
    print("[8] 診斷資料殘缺/畸形 → 不炸")
    for name, diag in [
        ("空 dict", {}),
        ("只有 funds 殼", {"date": "2026-07-20", "funds": {}}),
        ("ledger 無 rows", {"date": "2026-07-20", "ledger": {"n_total": 0}}),
        ("欄位型別錯誤", {"date": "2026-07-20",
                          "funds": {"builder_dex": {"xyz": "壞掉的字串"},
                                    "spot": None},
                          "ledger": {"rows": ["不是 dict", None]},
                          "trading": {"days_since_last_fill": "n/a"}}),
    ]:
        skel = os.path.join(tmp, "diag-" + str(abs(hash(name)) % 99999))
        _write_hl(skel, json.loads(json.dumps(DOSSIER_BASE)), diag,
                  diag_date="2026-07-20")
        out = os.path.join(skel, "index.html")
        build_monitor.render(skel, out)
        html = open(out, encoding="utf-8").read()
        d = extract_data(html)
        check(d["hl"]["available"] is True and "聰明錢系統監控" in html,
              f"診斷「{name}」：build 不炸、頁面完整")
    # 最後一組（型別錯誤）另驗值被淨化
    check(d["hl"]["flows"]["days_since_last_fill"] is None,
          "非數字 days_since_last_fill → None")


def main():
    tmp = tempfile.mkdtemp(prefix="monitor-test-")
    try:
        test_full_build(tmp)
        test_missing_sources(tmp)
        test_risk_rendering(tmp)
        test_venues_full(tmp)
        test_venues_legacy(tmp)
        test_venue_share_math(tmp)
        test_diagnostic_edge_cases(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"ALL TESTS PASSED ({CHECKS} checks)")


if __name__ == "__main__":
    main()
