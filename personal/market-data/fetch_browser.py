"""
用 headless 瀏覽器抓 JS 動態載入的數據（在 GitHub Actions 上跑）：
  1. VIXTWN：期交所 MIS 波動率指數報價頁
  2. 大盤融資維持率：HiStock / 玩股網

把結果合併進 personal/market-data/today.json
"""
import json
import re
import sys

from playwright.sync_api import sync_playwright

OUT = "personal/market-data/today.json"


def grab_vixtwn(page):
    page.goto("https://mis.taifex.com.tw/futures/VolatilityQuotes/",
              wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(3000)
    text = page.inner_text("body")
    print(f"[VIX page] body length={len(text)}")
    # 找 VIXTWN 字樣附近的數值
    m = re.search(r'(?:VIXTWN|臺指選擇權波動率指數|波動率指數)[\s\S]{0,200}?(\d{1,3}\.\d{2})',
                  text)
    if m:
        return float(m.group(1))
    # 退一步：印出含數字的前幾行幫除錯
    lines = [l for l in text.splitlines() if re.search(r'\d{1,3}\.\d{2}', l)]
    print(f"[VIX page] numeric lines sample: {lines[:10]}")
    return None


def grab_margin(page):
    for url in ("https://histock.tw/stock/three.aspx?m=mg",
                "https://www.wantgoo.com/stock/margin-trading/market-price/taiex"):
        try:
            page.goto(url, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(3000)
            text = page.inner_text("body")
            m = re.search(r'維持率[\s\S]{0,120}?(1\d{2}\.\d{1,2})', text)
            if m:
                print(f"[margin] {url} → {m.group(1)}")
                return float(m.group(1))
            hits = [l.strip() for l in text.splitlines() if "維持率" in l]
            print(f"[margin] {url}: no match; 維持率 lines: {hits[:5]}")
        except Exception as e:
            print(f"[margin] {url} failed: {type(e).__name__}: {e}")
    return None


def main():
    with open(OUT, encoding="utf-8") as f:
        data = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/126.0 Safari/537.36")
        try:
            vix = grab_vixtwn(page)
            if vix:
                data["vixtwn"] = {"value": vix, "source": "TAIFEX MIS (browser)"}
                print(f"[OK] VIXTWN = {vix}")
        except Exception as e:
            print(f"[FAIL] VIXTWN: {type(e).__name__}: {e}")
        try:
            margin = grab_margin(page)
            if margin:
                data["margin_maintenance_ratio"] = margin
                print(f"[OK] 維持率 = {margin}")
        except Exception as e:
            print(f"[FAIL] 維持率: {type(e).__name__}: {e}")
        browser.close()

    # 外資當日買賣超（從 fetch.py 已寫入的三大法人資料挑出）
    inst = data.get("institutional_net_buy_yi") or {}
    for k, v in inst.items():
        if k.startswith("外資及陸資"):
            data["foreign_net_buy_today_yi"] = v
            break

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("merged →", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
