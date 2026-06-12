"""
摸魚記市場數據自動抓取（在 GitHub Actions 上跑，不受本地網路限制）

抓取目標：
  1. 加權指數收盤（TWSE OpenAPI，官方、無需金鑰）
  2. 三大法人/外資買賣超（TWSE OpenAPI）
  3. VIXTWN（TAIFEX OpenAPI / MIS API，多候選端點）
  4. 大盤融資維持率（玩股網/HiStock 頁面解析，盡力而為）

輸出：personal/market-data/today.json（最新快照）
      personal/market-data/history.jsonl（逐日累積）
"""
import json
import re
import sys
import datetime
import urllib.request
import urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def fetch(url, timeout=20, headers=None, post_json=None, post_form=None):
    h = {"User-Agent": UA, "Accept": "application/json,text/html,*/*"}
    if headers:
        h.update(headers)
    data = None
    if post_json is not None:
        data = json.dumps(post_json).encode()
        h["Content-Type"] = "application/json"
    elif post_form is not None:
        data = urllib.parse.urlencode(post_form).encode()
        h["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, headers=h, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def try_fetch(name, url, parser, debug=False):
    raw = None
    try:
        raw = fetch(url)
        val = parser(raw)
        if val is not None:
            print(f"[OK]   {name}: {val}  ({url})")
            return val
        print(f"[MISS] {name}: parsed None  ({url})")
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {e}  ({url})")
    if debug and raw:
        print(f"       head: {raw[:300]!r}")
    return None


# ── 1. 加權指數（TWSE OpenAPI：每日市場成交資訊，含加權指數）
def parse_taiex(raw):
    rows = json.loads(raw)
    if not rows:
        return None
    last = rows[-1]
    # FMTQIK 欄位：Date, TradeVolume, TradeValue, Transaction, TAIEX, Change
    val = last.get("TAIEX") or last.get("發行量加權股價指數")
    return {"date_roc": last.get("Date"), "close": float(str(val).replace(",", ""))}


# ── 2. 三大法人買賣金額（TWSE rwd API：{"data": [[名稱, 買, 賣, 差額], ...]}）
def parse_bfi82u_rwd(raw):
    data = json.loads(raw)
    rows = data.get("data") or []
    out = {}
    for r in rows:
        if len(r) >= 4:
            name = str(r[0])
            diff = float(str(r[3]).replace(",", ""))
            out[name] = round(diff / 1e8, 2)  # 億元
    return out or None


def parse_bfi82u_openapi(raw):
    rows = json.loads(raw)
    out = {}
    for r in rows:
        name = r.get("Name", "")
        buy = float(str(r.get("TotalBuy", "0")).replace(",", "") or 0)
        sell = float(str(r.get("TotalSell", "0")).replace(",", "") or 0)
        out[name] = round((buy - sell) / 1e8, 2)  # 億元
    return out or None


# ── 3. VIXTWN：多候選端點，第一個成功的就用
def parse_vix_csv(raw):
    lines = [l for l in raw.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return None
    last = lines[-1].split(",")
    print(f"       CSV header: {lines[0][:120]}; last row: {last[:8]}")
    for cell in reversed(last):
        try:
            v = float(cell.strip().strip('"'))
            if 5 < v < 200:
                return {"value": v, "row": last[:4]}
        except ValueError:
            continue
    return None



def parse_taifex_openapi_vix(raw):
    data = json.loads(raw)
    if isinstance(data, list) and data:
        last = data[-1]
        for k in ("VIX", "vix", "Value", "TradingPrice", "Price", "收盤價"):
            if k in last:
                return {"value": float(str(last[k]).replace(",", "")),
                        "date": last.get("Date") or last.get("date")}
    return None


def parse_mis_volatility(raw):
    data = json.loads(raw)
    # MIS API 回傳結構未知，先把頂層 key 印出來幫助除錯
    print(f"       MIS keys: {list(data)[:10]}")
    q = data.get("RtData", {}).get("QuoteList") or data.get("QuoteList") or []
    for item in q:
        sym = str(item.get("SymbolID", "")) + str(item.get("DispCName", ""))
        if "VIX" in sym.upper() or "波動" in sym:
            for k in ("CLastPrice", "LastPrice", "CRefPrice"):
                if item.get(k):
                    return {"value": float(item[k]), "raw_symbol": sym}
    return None


def parse_html_number(pattern):
    def p(raw):
        m = re.search(pattern, raw)
        return float(m.group(1)) if m else None
    return p


def main():
    today = datetime.date.today().isoformat()
    print(f"=== 摸魚記 market data fetch {today} ===\n")

    taiex = try_fetch(
        "TAIEX", "https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK",
        parse_taiex)

    inst = (try_fetch(
        "三大法人(rwd)",
        "https://www.twse.com.tw/rwd/zh/fund/BFI82U?type=day&response=json",
        parse_bfi82u_rwd, debug=True)
        or try_fetch(
        "三大法人(openapi)", "https://openapi.twse.com.tw/v1/fund/BFI82U",
        parse_bfi82u_openapi, debug=True))

    # VIXTWN：TAIFEX 主站可達（上一輪 data_gov 回 'no such data' 證實），
    # 從 vixMinNew 頁面本體或其 ajax 端點挖數值
    vixtwn = None

    def parse_vix_page(raw):
        # 頁面上的 VIX 數值通常是 2 位數.2 位小數，先撈合理區間的數字
        ctx = []
        for m in re.finditer(r'(\d{1,3}\.\d{2})', raw):
            v = float(m.group(1))
            if 5 < v < 150:
                s = max(0, m.start() - 60)
                ctx.append((v, raw[s:m.end() + 30]))
        if ctx:
            print(f"       candidates: {[c[0] for c in ctx[:12]]}")
            for v, c in ctx[:6]:
                print(f"       ctx {v}: {c!r}")
        return None  # 偵察模式：先看頁面結構，下一輪鎖定

    try_fetch("TAIFEX vixMinNew 頁面",
              "https://www.taifex.com.tw/cht/7/vixMinNew", parse_vix_page)

    # 列出 data_gov 開放資料的可用 data_name
    try:
        raw = fetch("https://www.taifex.com.tw/data_gov/taifex_open_data.asp")
        names = re.findall(r'data_name=([A-Za-z0-9_]+)', raw)
        vixish = [n for n in set(names) if 'vix' in n.lower() or 'VIX' in n]
        print(f"[INFO] data_gov names total={len(set(names))}, "
              f"vix-related={vixish}, sample={sorted(set(names))[:30]}")
    except Exception as e:
        print(f"[INFO] data_gov listing failed: {type(e).__name__}: {e}")

    # MIS API：模仿瀏覽器 POST
    for path, body in [
        ("getQuoteListVolatility", {}),
        ("getQuoteList",
         {"MarketType": "0", "SymbolType": "I", "KindID": "1",
          "CID": "VIXTWN", "ExpireMonth": "", "RowSize": "全部",
          "PageNo": "", "SortColumn": "", "AscDesc": "A"}),
    ]:
        try:
            raw = fetch(f"https://mis.taifex.com.tw/futures/api/{path}",
                        post_json=body,
                        headers={"Referer":
                                 "https://mis.taifex.com.tw/futures/VolatilityQuotes/"})
            print(f"[INFO] MIS {path}: {raw[:400]!r}")
            data = json.loads(raw)
            q = (data.get("RtData") or {}).get("QuoteList") or []
            for item in q:
                ident = str(item.get("SymbolID", "")) + str(item.get("DispCName", ""))
                if "VIX" in ident.upper() or "波動" in ident:
                    for k in ("CLastPrice", "LastPrice", "CRefPrice"):
                        if item.get(k):
                            vixtwn = {"value": float(item[k]), "symbol": ident}
                            print(f"[OK]   VIXTWN(MIS): {vixtwn}")
                            break
                if vixtwn:
                    break
        except Exception as e:
            print(f"[INFO] MIS {path} failed: {type(e).__name__}: {e}")
        if vixtwn:
            break

    # 大盤融資維持率：HiStock 頁面沒有「維持率」字樣，改試其他來源
    margin = None
    margin_candidates = [
        ("富邦DJ 大盤資券",
         "https://fubon-ebrokerdj.fbs.com.tw/z/zg/zg_AG.djhtm",
         parse_html_number(r'維持率[^0-9]{0,80}?(1\d{2}\.\d{1,2})')),
        ("Goodinfo 融資融券",
         "https://goodinfo.tw/tw/ShowMarginChart.asp?STOCK_ID=%E5%8A%A0%E6%AC%8A%E6%8C%87%E6%95%B8&CHT_CAT=DATE",
         parse_html_number(r'維持率[^0-9]{0,80}?(1\d{2}\.\d{1,2})')),
    ]
    for name, url, parser in margin_candidates:
        margin = try_fetch(name, url, parser)
        if margin:
            break
    if margin is None:
        # 偵察：印出候選頁面中「維持率/融資」上下文
        for name, url in [("HiStock mt", "https://histock.tw/stock/three.aspx?m=mt"),
                          ("HiStock mg", "https://histock.tw/stock/three.aspx?m=mg")]:
            try:
                raw = fetch(url)
                hits = list(re.finditer(r'維持率|融資', raw))[:3]
                print(f"[INFO] {name}: len={len(raw)}, "
                      f"title={re.search(r'<title>(.*?)</title>', raw).group(1) if re.search(r'<title>(.*?)</title>', raw) else '?'}")
                for m in hits:
                    s = max(0, m.start() - 60)
                    print(f"       {name} ctx: {raw[s:m.end()+120]!r}")
            except Exception as e:
                print(f"[INFO] {name} failed: {type(e).__name__}")

    foreign_today = None
    if inst:
        for k, v in inst.items():
            if "外資" in k and "自營" not in k:
                foreign_today = v
                break

    data = {
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "date": today,
        "taiex": taiex,
        "vixtwn": vixtwn,
        "margin_maintenance_ratio": margin,
        "institutional_net_buy_yi": inst,
        "foreign_net_buy_today_yi": foreign_today,
        "sources": "TWSE OpenAPI / TAIFEX / wantgoo / histock via GitHub Actions",
    }

    out_dir = "personal/market-data"
    with open(f"{out_dir}/today.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(f"{out_dir}/history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"\n=== Saved to {out_dir}/today.json ===")
    ok = sum(1 for v in (taiex, inst, vixtwn, margin) if v)
    print(f"成功 {ok}/4 項")
    return 0


if __name__ == "__main__":
    sys.exit(main())
