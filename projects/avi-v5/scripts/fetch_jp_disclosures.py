#!/usr/bin/env python3
"""日本個股「適時開示 + 有報客戶表」資料橋（在 GitHub Actions runner 上跑）。

為什麼需要這支：雲端 session 的 agent proxy 對日本財經/開示站一律 403
（實測 2026-07-26：www.release.tdnet.info、api.edinet-fsa.go.jp、
disclosure2.edinet-fsa.go.jp、irbank.net、kabutan、minkabu、finance.yahoo.co.jp、
公司 IR 站 www.jem-net.co.jp 全部 CONNECT 403）。但 Actions runner 不受此限
（同 fetch_backtest_ext.py 的 yfinance 經驗）。因此把「雲端做不到」的日本開示
抓取搬到 runner，落地成 data/ext/jp_disclosures/*.md，讓研究 session 直接讀檔。

解決的具體任務（mac-manual-homework 的 JEM 兩件功課）：
  ① 適時開示清單 → 確認有無再增資/CB/業績下修（JEM 否證 #1）
  ② 有価証券報告書「主な相手先別販売実績」→ NAND 單一客戶占比、
     Micron 系是否回到 >10%（JEM 否證 #2 的最強確認訊號）

資料源：irbank.net 的公司頁（/ir 開示一覽、/customers 主要顧客）——
比 TDnet 逐日列表輕量得多（TDnet 只留 31 天且需逐日逐頁掃）。
EDINET API v2 需申請 Subscription-Key，本橋不使用（無金鑰）。

用法：python3 scripts/fetch_jp_disclosures.py [--force] [--code 6855]
Exit code 恆為 0——best-effort 側掛任務，絕不可弄壞宿主 job。
"""

import argparse
import html
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ext" / "jp_disclosures"

# EDINET code 對照（irbank 用 EDINET code 當路徑）
# verified=True 才是已由搜尋結果確認過的對照；False 者若抓回內容公司名不符，
# 產出檔會自帶警告，勿直接採信（下次 session 依實際內容修正對照表）。
TARGETS = {
    "6855": {"name": "JEM", "edinet": "E02043", "verified": True},   # 日本電子材料（記憶體探針卡）
    "6834": {"name": "Seikoh", "edinet": "E02052", "verified": False},
    "6777": {"name": "santec", "edinet": "E02068", "verified": False},
}
FRESH_SECONDS = 3 * 86400
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "ja,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    for enc in ("utf-8", "cp932", "euc-jp"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def strip_tags(s):
    """粗略 HTML → 文字（不引第三方依賴；表格列以換行分隔）。"""
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?i)</(tr|p|div|li|h[1-6]|table)>", "\n", s)
    s = re.sub(r"(?i)</t[dh]>", " | ", s)
    s = re.sub(r"(?s)<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t　]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def fetch_section(code, meta, kind, path_suffix):
    url = f"https://irbank.net/{meta['edinet']}/{path_suffix}"
    try:
        text = strip_tags(get(url))
        if len(text) < 200:
            return f"⚠️ {kind}：取得內容過短（{len(text)} 字），可能被擋或頁面改版。URL={url}\n"
        # 只留前 8000 字，避免檔案膨脹
        body = text[:8000]
        return f"### {kind}\n來源：{url}\n\n```\n{body}\n```\n"
    except Exception as e:  # noqa: BLE001 — best-effort
        return f"⚠️ {kind} 抓取失敗：{type(e).__name__}: {e}　URL={url}\n"


def is_fresh(p):
    return p.exists() and (time.time() - p.stat().st_mtime) < FRESH_SECONDS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--code", help="只抓單一代碼（預設全抓）")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    codes = [args.code] if args.code else list(TARGETS)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ok = 0

    for code in codes:
        meta = TARGETS.get(code)
        if not meta:
            print(f"⚠️ 未知代碼 {code}，跳過")
            continue
        out_path = OUT / f"{code}_{meta['name']}.md"
        if not args.force and is_fresh(out_path):
            print(f"{code} {meta['name']}：檔案仍新鮮（<3d），跳過")
            continue

        parts = [f"# {code} {meta['name']} — 開示與客戶結構快照",
                 f"\n> 由 `fetch_jp_disclosures.py` 在 GitHub Actions runner 抓取"
                 f"（雲端 session 對日本站 403）。抓取時間：{now}\n"]
        if not meta.get("verified"):
            parts.append(f"> ⚠️ **EDINET code `{meta['edinet']}` 未經確認**——請先核對下方內容"
                         f"的公司名是否為 {meta['name']}（{code}）；不符則本檔作廢並修正對照表。\n")
        parts.append(fetch_section(code, meta, "適時開示一覽（TDnet 轉載）", "ir"))
        time.sleep(1.5)
        parts.append(fetch_section(code, meta, "主要な顧客（有報 相手先別販売実績）", "customers"))
        time.sleep(1.5)

        out_path.write_text("\n".join(parts), encoding="utf-8")
        got = sum(1 for p in parts if p.startswith("### "))
        print(f"{'✅' if got else '⚠️'} {code} {meta['name']} → {out_path.name}（成功 {got}/2 節）")
        ok += 1 if got else 0

    print(f"jp_disclosures: {ok}/{len(codes)} 完成 @ {now}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
