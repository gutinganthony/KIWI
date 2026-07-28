#!/usr/bin/env python3
"""SEC EDGAR 申報資料橋（在 GitHub Actions runner 上跑）。

為什麼需要這支：雲端 session 的 agent proxy 對 data.sec.gov 一律 403
（實測 2026-07-28：`curl https://data.sec.gov/submissions/CIK0000723125.json`
回 `CONNECT tunnel failed, response 403`）。但 Actions runner 不受此限
（同 yfinance／Polymarket data-api／irbank 的既有實證）。

解決的具體任務：
  ① 記憶體八因子判定的一手核對——**Micron SCA（take-or-pay）條款**
     現況全為二手來源、信心僅 45–55%。10-Q/10-K 原文是唯一權威來源。
     這條直接餵給 `skills/serenity/exit-playbook.md` §2.2：MU 的「價格地板」
     論點若在原文裡站不住，減碼順序（先 DRAM ETF、後 MU）就要重排。
  ② 持倉／候選美股的最新申報監控（8-K 突發事項、10-Q 季度）。

**輸出刻意用 CSV 而非 Markdown**：`update-dashboard.yml` 的 commit 段有
`git add projects/avi-v5/data/ext/*.csv`，寫成 CSV 就自動入版控、不必動 workflow。
（2026-07-27 的教訓：日本開示橋寫成 .md，不被 glob 涵蓋 → 抓了整天都隨 runner 回收消失。
新增任何資料橋前先問「落地路徑被哪個 git add 收走」。）

用法：python3 scripts/fetch_sec_filings.py [--force] [--ticker MU]
Exit code 恆為 0——best-effort 側掛任務，絕不可弄壞宿主 job。
"""

import argparse
import csv
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ext"
INDEX_CSV = OUT / "sec_filings.csv"
EXCERPT_CSV = OUT / "sec_excerpts.csv"

# SEC 要求 User-Agent 帶可聯絡的識別；沒帶會被擋。
UA = "KIWI-research jake.cz.jian@gmail.com"
TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"

# 追蹤標的。CIK 一律在 runner 上用官方對照表解析，**不硬編**
# （硬編 CIK 是典型的「看起來很合理但沒查證」錯誤來源）。
TARGETS = ["MU", "FORM", "PLAB", "RMBS", "SNDK"]
FORMS = {"10-Q", "10-K", "8-K"}
MAX_FILINGS = 12          # 每檔留最近 N 筆
FRESH_SECONDS = 3 * 86400

# 只對這些標的抓正文並做關鍵詞節錄（抓正文很貴，10-Q 可達數 MB）
EXCERPT_TARGETS = {"MU"}
EXCERPT_FORMS = {"10-Q", "10-K"}
KEYWORDS = [
    "take-or-pay", "long-term agreement", "capacity reservation",
    "customer prepayment", "supply agreement", "advance payment",
]
EXCERPT_CHARS = 320       # 每個命中前後各取多少字
MAX_EXCERPTS_PER_KW = 3


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Encoding": "gzip, deflate",
        "Host": url.split("/")[2],
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            import gzip
            raw = gzip.decompress(raw)
    return raw


def resolve_ciks(tickers):
    """用 SEC 官方對照表把 ticker 解析成 CIK。解析不到的回報但不中斷。"""
    data = json.loads(get(TICKER_MAP_URL).decode("utf-8"))
    lookup = {}
    for row in data.values():
        lookup[row["ticker"].upper()] = (int(row["cik_str"]), row["title"])
    out, missing = {}, []
    for t in tickers:
        if t.upper() in lookup:
            out[t] = lookup[t.upper()]
        else:
            missing.append(t)
    if missing:
        print(f"⚠️ 對照表查無 ticker：{', '.join(missing)}（可能已更名/下市，本輪跳過）")
    return out


def filing_url(cik, accession, primary_doc):
    acc = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{primary_doc}"


def fetch_filings(ticker, cik, title):
    """回傳 (rows, newest_by_form)。rows 是要寫進 CSV 的申報索引。"""
    sub = json.loads(get(SUBMISSIONS_URL.format(cik=cik)).decode("utf-8"))
    recent = sub.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    rows, newest = [], {}
    for i, form in enumerate(forms):
        if form not in FORMS:
            continue
        if len(rows) >= MAX_FILINGS:
            break
        acc = recent["accessionNumber"][i]
        doc = recent.get("primaryDocument", [""] * len(forms))[i]
        url = filing_url(cik, acc, doc) if doc else ""
        row = {
            "ticker": ticker,
            "company": title,
            "cik": cik,
            "form": form,
            "filing_date": recent["filingDate"][i],
            "report_date": recent.get("reportDate", [""] * len(forms))[i],
            "accession": acc,
            "url": url,
        }
        rows.append(row)
        if form not in newest and url:
            newest[form] = row
    return rows, newest


def strip_html(raw):
    s = raw.decode("utf-8", errors="replace")
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#8217;", "'")
    return re.sub(r"\s+", " ", s)


def extract_excerpts(ticker, row):
    """抓申報正文、對 KEYWORDS 做上下文節錄。失敗回空清單。"""
    out = []
    try:
        text = strip_html(get(row["url"], timeout=60))
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ {ticker} {row['form']} 正文抓取失敗：{type(e).__name__}: {e}")
        return out
    low = text.lower()
    for kw in KEYWORDS:
        hits = 0
        for m in re.finditer(re.escape(kw.lower()), low):
            if hits >= MAX_EXCERPTS_PER_KW:
                break
            a = max(0, m.start() - EXCERPT_CHARS)
            b = min(len(text), m.end() + EXCERPT_CHARS)
            out.append({
                "ticker": ticker,
                "form": row["form"],
                "filing_date": row["filing_date"],
                "keyword": kw,
                "excerpt": text[a:b].strip(),
                "url": row["url"],
            })
            hits += 1
    print(f"   {ticker} {row['form']} {row['filing_date']}：命中 {len(out)} 段"
          f"（關鍵詞 {len({o['keyword'] for o in out})}/{len(KEYWORDS)}）")
    return out


def is_fresh(p):
    return p.exists() and (time.time() - p.stat().st_mtime) < FRESH_SECONDS


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--ticker", help="只抓單一 ticker（預設全抓）")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    if not args.force and is_fresh(INDEX_CSV):
        print("sec_filings：檔案仍新鮮（<3d），跳過")
        return 0

    tickers = [args.ticker.upper()] if args.ticker else TARGETS
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        ciks = resolve_ciks(tickers)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ CIK 對照表取得失敗，本輪放棄：{type(e).__name__}: {e}")
        return 0

    all_rows, all_excerpts = [], []
    for ticker, (cik, title) in ciks.items():
        try:
            rows, newest = fetch_filings(ticker, cik, title)
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ {ticker} 申報索引取得失敗：{type(e).__name__}: {e}")
            continue
        all_rows.extend(rows)
        print(f"✅ {ticker}（CIK {cik}）：{len(rows)} 筆申報")
        time.sleep(0.5)   # SEC 建議 <10 req/s，這裡遠低於上限

        if ticker in EXCERPT_TARGETS:
            for form in EXCERPT_FORMS:
                if form in newest:
                    all_excerpts.extend(extract_excerpts(ticker, newest[form]))
                    time.sleep(0.5)

    if not all_rows:
        print("⚠️ 一筆都沒抓到，不覆寫既有檔案（保留上一輪結果）")
        return 0

    for r in all_rows:
        r["fetched_at"] = now
    write_csv(INDEX_CSV, all_rows,
              ["ticker", "company", "cik", "form", "filing_date",
               "report_date", "accession", "url", "fetched_at"])
    print(f"→ {INDEX_CSV.name}（{len(all_rows)} 列）")

    if all_excerpts:
        for r in all_excerpts:
            r["fetched_at"] = now
        write_csv(EXCERPT_CSV, all_excerpts,
                  ["ticker", "form", "filing_date", "keyword",
                   "excerpt", "url", "fetched_at"])
        print(f"→ {EXCERPT_CSV.name}（{len(all_excerpts)} 段節錄）")
    else:
        print("⚠️ 無關鍵詞節錄——可能是正文抓取失敗，或該申報真的沒提 SCA 條款。"
              "兩者意義完全不同，判讀前先看上面的錯誤訊息。")

    print(f"sec_filings: {len(ciks)}/{len(tickers)} 標的完成 @ {now}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
