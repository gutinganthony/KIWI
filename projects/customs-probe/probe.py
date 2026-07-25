#!/usr/bin/env python3
"""一次性探測：台灣海關細碼月度出口數據的程式化可得性（GA03 / GA35 / cuswebo）。

設計哲學：本腳本在「無法預先測試目標站」的前提下編寫（開發環境出站被封鎖），
因此採探測模式——每一步都把原始回應完整 dump 到 data/customs-probe/，
成功則直接產出 series.csv，失敗則留下足夠的現場證據供遠端診斷後迭代。

目標：驗證「海關細碼數據選股法」的最後一個未測假設——
細碼級（6 位 HS）月度出口序列（2025-06 ~ 2026-06）能否自動取得。
GA03 配方源自 g0v ronnywang/portal.sw.nat.gov.tw（2013），現效性未知。
"""
import csv
import datetime
import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup

OUT = "data/customs-probe"
os.makedirs(OUT, exist_ok=True)

S = requests.Session()
S.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

# 目標細碼（6 位 HS）：光通訊 / 伺服器 / 記憶體 / 半設備 / 機器人零件 / PCB / 散熱電源
CODES = [
    "851762",  # 通訊設備（含光收發模組——待用 11 碼再細分）
    "900110",  # 光纖
    "854470",  # 光纜
    "854149",  # 光敏半導體（雷射二極體歸類候選之一）
    "847150",  # 處理單元（伺服器主機）
    "847330",  # 電腦零附件（含記憶體模組）
    "854232",  # 記憶體 IC
    "848620",  # 半導體製造設備
    "848690",  # 半導體設備零件
    "847950",  # 工業機器人
    "848340",  # 齒輪/滾珠螺桿（減速機）
    "850131",  # 直流馬達 ≤750W（伺服馬達候選）
    "853710",  # 控制盤/板 ≤1kV
    "853400",  # 印刷電路
    "841459",  # 風扇
    "841950",  # 熱交換器（液冷）
    "850440",  # 靜態變流器（電源供應器）
]
CODE_GROUP = ",".join(CODES)

# 月份範圍：2025-06 ~ 2026-06（民國 114/115 年）
MONTHS = [(2025, m) for m in range(6, 13)] + [(2026, m) for m in range(1, 7)]

report = {"generated_utc": datetime.datetime.utcnow().isoformat() + "Z", "steps": []}


def save(name, content):
    path = os.path.join(OUT, name)
    mode = "wb" if isinstance(content, bytes) else "w"
    with open(path, mode, **({} if mode == "wb" else {"encoding": "utf-8"})) as f:
        f.write(content)
    return path


def log_step(name, **kw):
    entry = {"name": name, **kw}
    report["steps"].append(entry)
    print(f"[step] {json.dumps(entry, ensure_ascii=False)[:300]}")
    return entry


def fetch(name, url, **kw):
    """GET 並 dump。永不 raise——失敗記錄後回 None。"""
    try:
        r = S.get(url, timeout=40, **kw)
        save(f"{name}.html", r.text)
        log_step(f"GET {name}", url=url, status=r.status_code, bytes=len(r.text))
        return r
    except Exception as e:  # noqa: BLE001 — 探測模式，全部吞掉記錄
        log_step(f"GET {name}", url=url, error=repr(e))
        return None


def parse_tables(html):
    """回傳 [ [row(list of cell text)] per table ]，僅保留 >=2 列的表。"""
    soup = BeautifulSoup(html, "lxml")
    out = []
    for t in soup.find_all("table"):
        rows = []
        for tr in t.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if len(rows) >= 2:
            out.append(rows)
    return out


def looks_like_data(html):
    """粗判：回應含任一目標碼 + 數字千分位 → 視為有效資料頁。"""
    hits = [c for c in CODES if c in html or f"{c[:4]}.{c[4:]}" in html]
    has_numbers = bool(re.search(r"\d{1,3}(,\d{3}){2,}", html))
    return hits, has_numbers


def ga03_post(tag, year, month, extra=None):
    """POST GA03_LIST 一次（單月、金額、按貨品）。回傳 (ok, html)。"""
    data = {
        "searchInfo.TypePort": "4",          # 出口
        "searchInfo.goodsType": "6",          # 6 位碼
        "searchInfo.goodsCodeGroup": CODE_GROUP,
        "searchInfo.StartYear": str(year),
        "searchInfo.StartMonth": str(month),
        "searchInfo.EndMonth": str(month),
        "searchInfo.Type": "rbMoney1",        # 金額（配方值；若無效由表單 dump 迭代）
        "searchInfo.GroupType": "rbByGood",
    }
    if extra:
        data.update(extra)
    try:
        r = S.post("https://portal.sw.nat.gov.tw/APGA/GA03_LIST", data=data, timeout=60)
        save(f"ga03_try_{tag}.html", r.text)
        hits, nums = looks_like_data(r.text)
        ok = r.status_code == 200 and hits and nums
        log_step(f"POST GA03 {tag}", status=r.status_code, bytes=len(r.text),
                 code_hits=hits[:5], has_numbers=nums, ok=ok, params_year=year)
        return ok, r.text
    except Exception as e:  # noqa: BLE001
        log_step(f"POST GA03 {tag}", error=repr(e))
        return False, ""


def main():
    # ── 1. 表單頁 dump（迭代的基礎：真實欄位名/選項都在這）──
    fetch("ga03_form", "https://portal.sw.nat.gov.tw/APGA/GA03")
    time.sleep(2)
    fetch("ga35_download", "https://portal.sw.nat.gov.tw/APGA/GA35")   # 整包下載區
    time.sleep(2)
    fetch("cuswebo_home", "https://publicinfo.trade.gov.tw/cuswebo/")  # 貿易署備援
    time.sleep(2)

    # ── 2. GA03 參數變體探測（單月樣本：2026-05）──
    variants = [
        ("roc", 115, 5, None),                                  # 民國年（最可能）
        ("west", 2026, 5, None),                                # 西元年
        ("roc_endyear", 115, 5, {"searchInfo.EndYear": "115"}), # 帶 EndYear 變體
    ]
    working = None
    for tag, y, m, extra in variants:
        ok, _ = ga03_post(f"probe_{tag}", y, m, extra)
        if ok:
            working = (tag, extra)
            break
        time.sleep(3)

    # ── 3. 若探測成功 → 全 13 個月正式拉取 + 解析成 CSV ──
    rows_out = []
    if working:
        tag, extra = working
        to_roc = (tag != "west")
        for (yy, mm) in MONTHS:
            y = yy - 1911 if to_roc else yy
            ok, html = ga03_post(f"pull_{yy}-{mm:02d}", y, mm, extra)
            if ok:
                for table in parse_tables(html):
                    for row in table:
                        joined = " ".join(row)
                        if any(c in joined or f"{c[:4]}.{c[4:]}" in joined for c in CODES):
                            rows_out.append([f"{yy}-{mm:02d}"] + row)
            time.sleep(3)
        if rows_out:
            with open(os.path.join(OUT, "series.csv"), "w", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerows([["month", "raw_cells..."]] + rows_out)
            log_step("series.csv", rows=len(rows_out))
    else:
        log_step("GA03 all variants failed", note="診斷靠 ga03_form.html + ga03_try_*.html；"
                 "下一步：從表單 dump 讀真實欄位名重寫參數，或改走 cuswebo/GA35")

    # ── 4. 總結 ──
    report["verdict"] = {
        "ga03_working_variant": working[0] if working else None,
        "series_rows": len(rows_out),
        "next": "series.csv 有料＝細碼自動化可行，進入回測；無料＝讀 dump 迭代參數",
    }
    save("report.json", json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report["verdict"], ensure_ascii=False))


if __name__ == "__main__":
    main()
