#!/usr/bin/env python3
"""
fetch_tw_sectors.py — 台股板塊資料層（給全局觀測台 docs/cockpit 的台股版）

來源全部是證交所官方 JSON（免金鑰），但 **有 WAF 速率限制**：連續請求太快會回 307 導向
「因為安全性考量，您所執行的頁面無法呈現」。本腳本每個請求之間固定睡 --sleep 秒（預設 5），
被擋就睡 --cooldown 秒（預設 180）再續，連續被擋 --max-block 次就停，下次再跑會從缺的日期接著補（可續跑）。

三張表（projects/avi-v5/data/tw/）：
  sector_index.csv   日期 × 各類股價格指數收盤（MI_INDEX type=IND 的「價格指數」表，含發行量加權）
  sector_flow.csv    日期 × 產業別：三大法人淨買超金額（T86 淨買超股數 × 當日收盤價，依 t187ap03_L 產業別彙總）、
                     外資／投信／自營分項、該產業成交金額、檔數
  holidays.txt       證交所回「很抱歉，沒有符合條件的資料」的日期（休市），之後不再重試

用法：
  python scripts/fetch_tw_sectors.py --update                  # 補到今天（index + flow，各自從最後一筆接著補）
  python scripts/fetch_tw_sectors.py --backfill-index 2019-01-01   # 只回填指數（1 請求/日）
  python scripts/fetch_tw_sectors.py --backfill-flow 2025-11-01    # 回填法人流向（2 請求/日）
  （可同時給；順序：先 flow 再 index，日期由新到舊，讓最近一年先完整）
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "tw")
IDX_CSV = os.path.join(DATA, "sector_index.csv")
FLOW_CSV = os.path.join(DATA, "sector_flow.csv")
HOLIDAYS = os.path.join(DATA, "holidays.txt")
INDMAP = os.path.join(DATA, "industry_map.json")
UA = {"User-Agent": "KIWI-cockpit/1.0 (+https://github.com/gutinganthony/KIWI)"}

# 證交所產業別代碼 → 名稱（t187ap03_L 的「產業別」欄）
IND_NAMES = {
    "01": "水泥", "02": "食品", "03": "塑膠", "04": "紡織纖維", "05": "電機機械", "06": "電器電纜",
    "08": "玻璃陶瓷", "09": "造紙", "10": "鋼鐵", "11": "橡膠", "12": "汽車", "14": "建材營造",
    "15": "航運", "16": "觀光餐旅", "17": "金融保險", "18": "貿易百貨", "20": "其他", "21": "化學",
    "22": "生技醫療", "23": "油電燃氣", "24": "半導體", "25": "電腦及週邊設備", "26": "光電",
    "27": "通信網路", "28": "電子零組件", "29": "電子通路", "30": "資訊服務", "31": "其他電子",
    "32": "文化創意", "33": "農業科技", "34": "電子商務", "35": "綠能環保", "36": "數位雲端",
    "37": "運動休閒", "38": "居家生活", "91": "存託憑證",
}

FLOW_FIELDS = ["date", "ind", "name", "inst_net", "foreign_net", "trust_net", "dealer_net", "turnover", "n"]


class Blocked(Exception):
    pass


class Fetcher:
    def __init__(self, sleep, cooldown, max_block):
        self.sleep, self.cooldown, self.max_block = sleep, cooldown, max_block
        self.blocks = 0
        self.last = 0.0

    def get_json(self, url):
        wait = self.sleep - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        for attempt in range(3):
            self.last = time.time()
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                    raw = r.read()
                    code = r.status
            except urllib.error.HTTPError as e:
                code, raw = e.code, b""
            except Exception as e:  # noqa: BLE001
                print(f"  [net] {e}; 20s 後重試", file=sys.stderr)
                time.sleep(20)
                continue
            if code == 200 and raw[:1] == b"{":
                self.blocks = 0
                return json.loads(raw)
            # 307 / HTML = WAF 擋下
            self.blocks += 1
            print(f"  [blocked {self.blocks}/{self.max_block}] HTTP {code}; 冷卻 {self.cooldown}s", file=sys.stderr)
            if self.blocks >= self.max_block:
                raise Blocked()
            time.sleep(self.cooldown)
        raise Blocked()


def num(x):
    try:
        return float(str(x).replace(",", "").strip())
    except ValueError:
        return None


def ymd(d):
    return d.strftime("%Y%m%d")


def load_holidays():
    try:
        return set(open(HOLIDAYS).read().split())
    except FileNotFoundError:
        return set()


def add_holiday(d):
    with open(HOLIDAYS, "a") as f:
        f.write(d.isoformat() + "\n")


def is_nodata(j):
    return (j.get("stat") or "").startswith("很抱歉") or (j.get("stat") != "OK" and not j.get("tables") and not j.get("data"))


# ---------------------------------------------------------------- sector index
def fetch_index(fx, d):
    j = fx.get_json(f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={ymd(d)}&type=IND&response=json")
    if is_nodata(j):
        return None
    tables = j.get("tables") or [j]
    price = None
    for t in tables:
        if "價格指數" in (t.get("title") or "") and "報酬" not in (t.get("title") or ""):
            price = t
            break
    if price is None:
        price = tables[0]
    out = {}
    for row in price.get("data", []):
        name = row[0].strip()
        v = num(row[1])
        if v is not None:
            out[name] = v
    return out


def idx_dates():
    if not os.path.exists(IDX_CSV):
        return set(), []
    with open(IDX_CSV, encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r)
        rows = list(r)
    return {row[0] for row in rows}, header


def idx_append(d, vals):
    """寬表：欄位會隨新指數出現而增加，所以每次改寫整檔（檔案小，<1MB）。"""
    rows = {}
    header = ["date"]
    if os.path.exists(IDX_CSV):
        with open(IDX_CSV, encoding="utf-8") as f:
            r = csv.reader(f)
            header = next(r)
            for row in r:
                rows[row[0]] = dict(zip(header[1:], row[1:]))
    rows[d.isoformat()] = {k: ("" if v is None else repr(v)) for k, v in vals.items()}
    cols = list(dict.fromkeys(header[1:] + [k for k in vals]))
    tmp = IDX_CSV + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date"] + cols)
        for k in sorted(rows):
            w.writerow([k] + [rows[k].get(c, "") for c in cols])
    os.replace(tmp, IDX_CSV)


# ---------------------------------------------------------------- flows
def industry_map(fx):
    if os.path.exists(INDMAP) and time.time() - os.path.getmtime(INDMAP) < 30 * 86400:
        return json.load(open(INDMAP, encoding="utf-8"))
    with urllib.request.urlopen(urllib.request.Request("https://openapi.twse.com.tw/v1/opendata/t187ap03_L", headers=UA), timeout=60) as r:
        j = json.loads(r.read())
    m = {x["公司代號"]: x["產業別"] for x in j if x.get("公司代號") and x.get("產業別")}
    json.dump(m, open(INDMAP, "w", encoding="utf-8"), ensure_ascii=False)
    return m


def fetch_flow(fx, d, imap):
    t86 = fx.get_json(f"https://www.twse.com.tw/rwd/zh/fund/T86?date={ymd(d)}&selectType=ALLBUT0999&response=json")
    if is_nodata(t86):
        return None
    mi = fx.get_json(f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={ymd(d)}&type=ALLBUT0999&response=json")
    if is_nodata(mi):
        return None
    close, turnover = {}, {}
    for t in mi.get("tables", []):
        f = t.get("fields") or []
        if "證券代號" in f and "收盤價" in f:
            ic, ip, it = f.index("證券代號"), f.index("收盤價"), f.index("成交金額")
            for row in t["data"]:
                code = row[ic].strip()
                close[code] = num(row[ip])
                turnover[code] = num(row[it])
            break
    f = t86.get("fields") or []
    try:
        ic = f.index("證券代號")
        i_for = f.index("外陸資買賣超股數(不含外資自營商)")
        i_fd = f.index("外資自營商買賣超股數")
        i_tr = f.index("投信買賣超股數")
        i_dl = f.index("自營商買賣超股數")
        i_all = f.index("三大法人買賣超股數")
    except ValueError:
        print("  T86 欄位變了：", f, file=sys.stderr)
        return None
    agg = {}
    for row in t86["data"]:
        code = row[ic].strip()
        ind = imap.get(code)
        px = close.get(code)
        if not ind or px is None:
            continue
        a = agg.setdefault(ind, {"inst_net": 0.0, "foreign_net": 0.0, "trust_net": 0.0, "dealer_net": 0.0, "turnover": 0.0, "n": 0})
        a["inst_net"] += (num(row[i_all]) or 0) * px
        a["foreign_net"] += ((num(row[i_for]) or 0) + (num(row[i_fd]) or 0)) * px
        a["trust_net"] += (num(row[i_tr]) or 0) * px
        a["dealer_net"] += (num(row[i_dl]) or 0) * px
        a["turnover"] += turnover.get(code) or 0
        a["n"] += 1
    # 成交金額要用全部上市公司（含當日法人沒動作的），所以再補一次
    for code, tv in turnover.items():
        ind = imap.get(code)
        if ind and ind in agg and code not in {r[ic].strip() for r in t86["data"]}:
            agg[ind]["turnover"] += tv or 0
    return agg


def flow_dates():
    if not os.path.exists(FLOW_CSV):
        return set()
    with open(FLOW_CSV, encoding="utf-8") as f:
        return {row["date"] for row in csv.DictReader(f)}


def flow_append(d, agg):
    new = not os.path.exists(FLOW_CSV)
    with open(FLOW_CSV, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FLOW_FIELDS)
        if new:
            w.writeheader()
        for ind, a in sorted(agg.items()):
            w.writerow({"date": d.isoformat(), "ind": ind, "name": IND_NAMES.get(ind, ind),
                        "inst_net": round(a["inst_net"]), "foreign_net": round(a["foreign_net"]),
                        "trust_net": round(a["trust_net"]), "dealer_net": round(a["dealer_net"]),
                        "turnover": round(a["turnover"]), "n": a["n"]})


# ---------------------------------------------------------------- driver
def trading_days(start, end):
    d = end
    while d >= start:
        if d.weekday() < 5:
            yield d
        d -= timedelta(days=1)


def run(kind, start, fx, imap=None):
    hol = load_holidays()
    have = flow_dates() if kind == "flow" else idx_dates()[0]
    end = date.today()
    todo = [d for d in trading_days(start, end) if d.isoformat() not in have and d.isoformat() not in hol]
    print(f"[{kind}] 待補 {len(todo)} 日（{start} → {end}）", file=sys.stderr)
    done = 0
    for d in todo:
        try:
            res = fetch_flow(fx, d, imap) if kind == "flow" else fetch_index(fx, d)
        except Blocked:
            print(f"[{kind}] 連續被擋，停在 {d}；已補 {done} 日。下次再跑會接著補。", file=sys.stderr)
            return False
        if res is None:
            # 今天／昨天可能只是還沒出表，不要記成休市
            if (end - d).days >= 2:
                add_holiday(d)
            continue
        if kind == "flow":
            flow_append(d, res)
        else:
            idx_append(d, res)
        done += 1
        if done % 20 == 0:
            print(f"[{kind}] {d} 已補 {done}/{len(todo)}", file=sys.stderr)
    print(f"[{kind}] 完成，補了 {done} 日", file=sys.stderr)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="index 與 flow 各從最後一筆補到今天")
    ap.add_argument("--backfill-index", metavar="YYYY-MM-DD")
    ap.add_argument("--backfill-flow", metavar="YYYY-MM-DD")
    ap.add_argument("--sleep", type=float, default=5.0)
    ap.add_argument("--cooldown", type=float, default=180.0)
    ap.add_argument("--max-block", type=int, default=6)
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    fx = Fetcher(a.sleep, a.cooldown, a.max_block)
    ok = True
    if a.update or a.backfill_flow:
        imap = industry_map(fx)
        if a.backfill_flow:
            start = date.fromisoformat(a.backfill_flow)
        else:
            have = flow_dates()
            start = date.fromisoformat(max(have)) + timedelta(days=1) if have else date.today() - timedelta(days=400)
        ok &= run("flow", start, fx, imap)
    if a.update or a.backfill_index:
        if a.backfill_index:
            start = date.fromisoformat(a.backfill_index)
        else:
            have = idx_dates()[0]
            start = date.fromisoformat(max(have)) + timedelta(days=1) if have else date.today() - timedelta(days=400)
        ok &= run("index", start, fx)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
