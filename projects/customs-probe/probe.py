#!/usr/bin/env python3
"""台灣海關細碼數據探測 v2 — 針對 v1 發現重寫。

v1 發現（data/customs-probe/report.json）：
  - g0v 2013 配方的 `GA03` 已不存在；/APGA/GA03 與 /APGA/GA35 都只回入口殼頁
  - 真實選單：GA30 綜合查詢 / GA31 輔助查詢 / GA29 統計表 / GA28 互動式圖表
  - 站台為 Struts2 + jqGrid + APGAJSESSIONID session（資料走 AJAX 回 JSON）
  - runner 可正常存取 portal.sw.nat.gov.tw（200）；cuswebo 回 403

v2 策略：session-aware 逐頁 dump GA30/31/29/28，自動抽出 form 欄位與 jqGrid 資料端點，
找到端點就試打並 dump 回應。全程 best-effort，永不 raise。
"""
import datetime, json, os, re, time
import requests
from bs4 import BeautifulSoup

OUT = "data/customs-probe"
os.makedirs(OUT, exist_ok=True)
BASE = "https://portal.sw.nat.gov.tw"

S = requests.Session()
S.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

report = {"generated_utc": datetime.datetime.utcnow().isoformat()+"Z", "version": 2, "steps": [], "findings": {}}

def log(name, **kw):
    e = {"name": name, **kw}; report["steps"].append(e)
    print("[step]", json.dumps(e, ensure_ascii=False)[:400]); return e

def save(name, content):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f: f.write(content)
    return p

def get(name, url, **kw):
    try:
        r = S.get(url, timeout=45, **kw); save(f"{name}.html", r.text)
        log(f"GET {name}", url=url, status=r.status_code, bytes=len(r.text))
        return r
    except Exception as e:
        log(f"GET {name}", url=url, error=repr(e)); return None

def dissect(name, html):
    """抽出 form 欄位、jqGrid/ajax 端點、可疑 action。"""
    s = BeautifulSoup(html, "lxml")
    out = {"forms": [], "grid_urls": [], "actions": [], "selects": {}}
    for f in s.find_all("form"):
        fields = []
        for i in f.find_all(["input", "select", "textarea"]):
            nm = i.get("name")
            if not nm: continue
            item = {"tag": i.name, "type": i.get("type"), "name": nm, "value": i.get("value")}
            if i.name == "select":
                opts = [(o.get("value"), o.get_text(strip=True)) for o in i.find_all("option")][:15]
                item["options"] = opts; out["selects"][nm] = opts
            fields.append(item)
        out["forms"].append({"action": f.get("action"), "method": f.get("method"), "id": f.get("id"), "fields": fields})
    # jqGrid / ajax 端點
    for pat in [r'url\s*:\s*["\']([^"\']+)["\']', r'editurl\s*:\s*["\']([^"\']+)["\']',
                r'\$\.(?:post|get|ajax)\s*\(\s*["\']([^"\']+)["\']', r'action\s*=\s*["\'](/APGA/[^"\']+)["\']']:
        for m in re.findall(pat, html):
            if m and m not in out["grid_urls"] and not m.endswith((".js",".css",".png",".gif")):
                out["grid_urls"].append(m)
    for m in set(re.findall(r'/APGA/[A-Za-z0-9_!]+(?:_[A-Z]+)?', html)):
        if m not in out["actions"]: out["actions"].append(m)
    report["findings"][name] = out
    log(f"DISSECT {name}", forms=len(out["forms"]),
        field_names=[fl["name"] for fm in out["forms"] for fl in fm["fields"]][:25],
        grid_urls=out["grid_urls"][:12], actions=sorted(out["actions"])[:25])
    return out

def main():
    # 1) 先打首頁建立 session
    get("v2_home", f"{BASE}/APGA/")
    time.sleep(1)
    # 2) 逐頁 dump 真實查詢頁
    pages = {"GA30": "綜合查詢", "GA31": "輔助查詢", "GA29": "統計表", "GA28": "互動式圖表"}
    found = {}
    for pid in pages:
        r = get(f"v2_{pid}", f"{BASE}/APGA/{pid}")
        if r and r.status_code == 200:
            found[pid] = dissect(pid, r.text)
        time.sleep(2)

    # 3) 對每個發現的端點試打（GET 與 POST 各一），dump 回應供診斷
    tried = 0
    for pid, d in found.items():
        for u in d["grid_urls"][:4]:
            if tried >= 8: break
            url = u if u.startswith("http") else BASE + (u if u.startswith("/") else f"/APGA/{u}")
            tag = f"v2_{pid}_ep{tried}"
            try:
                r = S.post(url, data={"_search": "false", "rows": "50", "page": "1"}, timeout=45)
                save(f"{tag}_post.txt", r.text[:200000])
                log(f"POST {tag}", url=url, status=r.status_code, bytes=len(r.text),
                    looks_json=r.text.strip()[:1] in "{[", sample=r.text.strip()[:200])
            except Exception as e:
                log(f"POST {tag}", url=url, error=repr(e))
            tried += 1
            time.sleep(2)

    report["verdict"] = {
        "pages_ok": list(found.keys()),
        "next": "看 findings 的 form 欄位與 grid_urls；確定端點+參數後 v3 正式拉 17 碼 × 13 月",
    }
    save("report_v2.json", json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report["verdict"], ensure_ascii=False))

if __name__ == "__main__":
    main()
