#!/usr/bin/env python3
"""SEC EDGAR 資料橋的離線測試（不需網路）。

為什麼需要：這座橋只能在 GitHub Actions runner 上真跑（雲端 session 對
data.sec.gov 一律 403），所以「解析邏輯對不對」在雲端無法用真流量驗證。
本測試用假的 SEC 回應把 `get()` 換掉，驗證純解析邏輯。

用法：python3 tests/test_sec_bridge.py    （直接執行，非 pytest）
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch_sec_filings as s  # noqa: E402

TICKERS = json.dumps({
    "0": {"cik_str": 723125, "ticker": "MU", "title": "Micron Technology, Inc."},
    "1": {"cik_str": 1013488, "ticker": "FORM", "title": "FormFactor, Inc."},
}).encode()

SUBS = json.dumps({"filings": {"recent": {
    "form": ["8-K", "10-Q", "4", "10-K", "8-K"],
    "accessionNumber": ["0000723125-26-000101", "0000723125-26-000088",
                        "0000723125-26-000077", "0000723125-25-000050",
                        "0000723125-25-000040"],
    "filingDate": ["2026-07-20", "2026-06-25", "2026-06-20", "2025-10-10", "2025-09-01"],
    "reportDate": ["2026-07-18", "2026-05-29", "2026-06-18", "2025-08-28", "2025-08-30"],
    "primaryDocument": ["mu-8k.htm", "mu-10q.htm", "xslF345X03/wf.xml",
                        "mu-10k.htm", "mu-8k2.htm"],
}}}).encode()

BODY = (b"<html><body><p>We have entered into long-term agreements with certain "
        b"customers, including take-or-pay commitments that establish a price floor "
        b"through 2030.</p><script>junk()</script><p>Customer prepayment totaling "
        b"$22.0 billion was received.</p></body></html>")


def fake_get(url, timeout=30):
    if "company_tickers" in url:
        return TICKERS
    if "submissions" in url:
        return SUBS
    return BODY


def main():
    s.get = fake_get
    fails = []

    ciks = s.resolve_ciks(["MU", "FORM", "NOSUCH"])
    if ciks.get("MU", (None,))[0] != 723125:
        fails.append(f"CIK 解析錯誤：{ciks}")
    if "NOSUCH" in ciks:
        fails.append("不存在的 ticker 不該出現在結果裡")

    rows, newest = s.fetch_filings("MU", 723125, "Micron Technology, Inc.")
    forms = [r["form"] for r in rows]
    if forms != ["8-K", "10-Q", "10-K", "8-K"]:
        fails.append(f"申報過濾錯誤（Form 4 應被濾掉）：{forms}")
    want = "/723125/000072312526000088/mu-10q.htm"
    if not newest.get("10-Q", {}).get("url", "").endswith(want):
        fails.append(f"10-Q URL 組裝錯誤：{newest.get('10-Q', {}).get('url')}")

    ex = s.extract_excerpts("MU", newest["10-Q"])
    kws = {e["keyword"] for e in ex}
    for need in ("take-or-pay", "long-term agreement", "customer prepayment"):
        if need not in kws:
            fails.append(f"關鍵詞漏抓：{need}")
    if any("junk()" in e["excerpt"] for e in ex):
        fails.append("<script> 內容未被剝除")

    if fails:
        print("❌ 失敗：")
        for f in fails:
            print("  -", f)
        return 1
    print(f"✅ 全部通過（CIK 解析／申報過濾／URL 組裝／{len(kws)} 個關鍵詞節錄／HTML 剝除）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
