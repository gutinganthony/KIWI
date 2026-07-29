#!/usr/bin/env python3
"""記憶體產業數據資料橋（在 GitHub Actions runner 上跑）。

目的：補齊 `hbm_bit_split.py` 需要的三個輸入——
  ρ = HBM 佔 DRAM 營收比重（法說會揭露）
  k = HBM 每位元 ASP 溢價（報價機構）
  r = trade ratio（技術常數，變動慢）
以及追蹤 Δs 用的「HBM 位元成長 vs 總位元成長」gap。

為什麼需要橋：雲端 session 對 trendforce.com／investors.micron.com／
idc.com／counterpointresearch.com／semianalysis.com 全部 CONNECT 403
（實測 2026-07-29，curl 與 WebFetch 皆然）。Actions runner 不受此限。

⚠️ **誠實預期**：這些站是否對 runner 開放**未經驗證**（不像 Yahoo Finance
有既有成功案例）。若產出檔內全是 403，代表此路不通 → 退回 Mac 手動。
本腳本的價值在於「自動試一次、把結果留檔」，而不是保證成功。

用法：python3 scripts/fetch_memory_sources.py [--force]
Exit code 恆為 0——best-effort 側掛任務，絕不可弄壞宿主 job。
"""

import argparse
import html
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ext" / "memory_sources"
FRESH_SECONDS = 3 * 86400
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# 目標：名稱 → (URL, 這個來源能提供什麼輸入)
SOURCES = {
    "trendforce_press": ("https://www.trendforce.com/presscenter/news",
                         "合約價、HBM 佔比、位元供給預估 → k 與 g_total"),
    "micron_ir": ("https://investors.micron.com/news-releases",
                  "HBM 營收佔比 ρ、位元成長指引 → ρ 與 g_hbm_bits"),
    "micron_sec": ("https://www.sec.gov/cgi-bin/browse-edgar"
                   "?action=getcompany&CIK=MU&type=10-Q&dateb=&owner=include&count=5",
                   "10-Q 原文（SEC EDGAR 為美國政府站，最可能通）"),
}
# 關鍵字：抓回頁面後只留含這些詞的段落，避免整頁塞爆檔案
KEYWORDS = ("HBM", "bit supply", "bit growth", "DRAM", "wafer", "contract price",
            "位元", "晶圓", "合約價")


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en,zh;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    for enc in ("utf-8", "cp950", "big5"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def strip_tags(s):
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?i)</(tr|p|div|li|h[1-6])>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t　]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


def relevant_lines(text, limit=120):
    """只留含關鍵字的行——把整頁壓成有用的幾十行。"""
    hits = [ln.strip() for ln in text.split("\n")
            if len(ln.strip()) > 20 and any(k.lower() in ln.lower() for k in KEYWORDS)]
    return hits[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / "memory_inputs.md"
    if not args.force and out_path.exists() and \
            (time.time() - out_path.stat().st_mtime) < FRESH_SECONDS:
        print("memory_sources: 檔案仍新鮮（<3d），跳過")
        return 0

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    parts = ["# 記憶體產業數據抓取（供 hbm_bit_split.py 使用）",
             f"\n> 由 `fetch_memory_sources.py` 在 Actions runner 抓取"
             f"（雲端 session 對這些站 403）。時間：{now}",
             "\n> **要找的三個數字**：ρ＝HBM 佔 DRAM 營收比重｜k＝HBM 每位元 ASP 溢價｜"
             "r＝trade ratio；外加 HBM 位元成長 vs 總位元成長的 gap。\n"]
    ok = 0
    for name, (url, purpose) in SOURCES.items():
        parts.append(f"\n## {name}\n- 用途：{purpose}\n- URL：{url}\n")
        try:
            lines = relevant_lines(strip_tags(get(url)))
            if lines:
                parts.append("```\n" + "\n".join(lines) + "\n```\n")
                ok += 1
                print(f"✅ {name}: {len(lines)} 行相關內容")
            else:
                parts.append("⚠️ 抓到頁面但無關鍵字命中（可能是 JS 渲染或版面改變）。\n")
                print(f"⚠️ {name}: 無關鍵字命中")
        except Exception as e:  # noqa: BLE001
            parts.append(f"⚠️ 抓取失敗：{type(e).__name__}: {e}\n")
            print(f"⚠️ {name} 失敗：{type(e).__name__}: {e}")
        time.sleep(1.5)

    parts.append("\n## 下一步\n"
                 "若上面取得 ρ／k／位元成長，改 `scripts/hbm_bit_split.py` 的 ASSUMPTIONS "
                 "或直接呼叫 `wafer_share_from_revenue_share(ρ, k, r)` 與 "
                 "`delta_s_from_growth_gap(g_hbm, g_total, s0, r)` 重跑。\n")
    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"memory_sources: {ok}/{len(SOURCES)} 成功 → {out_path.name} @ {now}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
