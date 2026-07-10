#!/usr/bin/env python3
"""leaderboard 端點探測（診斷用，暫時性）。

2026-07-10 實測發現 lb-api/data-api 的 /leaderboard 路徑已 404（API 改版），
本腳本在 CI 上把一整批候選 URL 打一輪，記錄 status＋body 開頭，
供主對話挑出現行端點後更新 config.py。找到後本腳本與 workflow 步驟即可移除。

純唯讀 GET，不含任何交易/金鑰功能。
"""

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import config

BODY_LEN = 300
SLEEP = 0.3

# 靜態候選（{window} 之類先寫死一組代表值）
BATTERY = [
    # 2026-07-10 研究查證的現行官方端點（應 200）
    "https://data-api.polymarket.com/v1/leaderboard?timePeriod=MONTH&orderBy=PNL&limit=50&category=OVERALL&offset=0",
    "https://data-api.polymarket.com/v1/leaderboard?timePeriod=ALL&orderBy=PNL&limit=50&category=OVERALL&offset=0",
    # lb-api 變體（已退役，應 404——留作回歸偵測）
    "https://lb-api.polymarket.com/leaderboard?window=1m&rankType=pnl&limit=50",
    "https://lb-api.polymarket.com/leaderboard?window=30d&rankType=pnl&limit=50",
    "https://lb-api.polymarket.com/leaderboard?timePeriod=1m&orderBy=pnl&limit=50",
    "https://lb-api.polymarket.com/pnl?window=1m&limit=50",
    "https://lb-api.polymarket.com/ranking?window=1m&rankType=pnl&limit=50",
    "https://lb-api.polymarket.com/v1/leaderboard?window=1m&rankType=pnl&limit=50",
    "https://lb-api.polymarket.com/v2/leaderboard?window=1m&rankType=pnl&limit=50",
    "https://lb-api.polymarket.com/",
    # data-api 變體
    "https://data-api.polymarket.com/v1/leaderboard?window=1m&rankType=pnl&limit=50",
    "https://data-api.polymarket.com/v2/leaderboard?window=1m&rankType=pnl&limit=50",
    "https://data-api.polymarket.com/leaderboard/pnl?window=1m&limit=50",
    "https://data-api.polymarket.com/rankings?window=1m&rankType=pnl&limit=50",
    "https://data-api.polymarket.com/traders/leaderboard?window=1m&limit=50",
    "https://data-api.polymarket.com/leaderboard",
    # gamma / 站內 API route
    "https://gamma-api.polymarket.com/leaderboard?window=1m&rankType=pnl&limit=50",
    "https://polymarket.com/api/leaderboard?window=1m&rankType=pnl&limit=50",
    # 替代宇宙來源：熱門市場 → 大持倉者
    "https://gamma-api.polymarket.com/markets?order=volume24hr&ascending=false&limit=5&closed=false",
    "https://gamma-api.polymarket.com/events?order=volume24hr&ascending=false&limit=3&closed=false",
]


def probe(url):
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read(4096).decode("utf-8", errors="replace")
            return {"url": url, "status": resp.status, "ok": True,
                    "body_head": body[:BODY_LEN],
                    "elapsed_sec": round(time.time() - started, 2)}
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(1024).decode("utf-8", errors="replace")
        except Exception:
            pass
        return {"url": url, "status": e.code, "ok": False,
                "body_head": body[:BODY_LEN],
                "elapsed_sec": round(time.time() - started, 2)}
    except Exception as e:  # URLError / timeout / JSON 之外的一切
        return {"url": url, "status": None, "ok": False,
                "body_head": f"{type(e).__name__}: {e}",
                "elapsed_sec": round(time.time() - started, 2)}


def main():
    results = []
    for url in BATTERY:
        r = probe(url)
        results.append(r)
        print(f"[{r['status']}] {url} -> {r['body_head'][:80]!r}")
        time.sleep(SLEEP)

    # 二階段：從 gamma markets 結果取 conditionId，探測 holders 端點
    for r in results:
        if "gamma-api.polymarket.com/markets" in r["url"] and r["ok"]:
            try:
                markets = json.loads(r["body_head"]) if len(r["body_head"]) < BODY_LEN \
                    else None
            except json.JSONDecodeError:
                markets = None
            # body_head 可能被截斷 → 重新完整抓一次
            if markets is None:
                req = urllib.request.Request(
                    r["url"], headers={"User-Agent": config.USER_AGENT})
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        markets = json.loads(resp.read().decode("utf-8"))
                except Exception:
                    markets = None
            cid = None
            if isinstance(markets, list):
                for mk in markets:
                    cid = (mk or {}).get("conditionId") or (mk or {}).get("condition_id")
                    if cid:
                        break
            if cid:
                for tmpl in [
                    f"https://data-api.polymarket.com/holders?market={cid}&limit=20",
                    f"https://data-api.polymarket.com/holders?conditionId={cid}&limit=20",
                ]:
                    hr = probe(tmpl)
                    results.append(hr)
                    print(f"[{hr['status']}] {tmpl} -> {hr['body_head'][:80]!r}")
                    time.sleep(SLEEP)
            break

    out_dir = Path(__file__).resolve().parent / "data" / "probe"
    out_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = out_dir / f"leaderboard_probe_{date}.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    n_ok = sum(1 for r in results if r["ok"])
    print(f"PROBE DONE: {n_ok}/{len(results)} ok -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
