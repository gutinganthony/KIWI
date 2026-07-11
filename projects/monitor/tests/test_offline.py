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


def main():
    tmp = tempfile.mkdtemp(prefix="monitor-test-")
    try:
        test_full_build(tmp)
        test_missing_sources(tmp)
        test_risk_rendering(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"ALL TESTS PASSED ({CHECKS} checks)")


if __name__ == "__main__":
    main()
