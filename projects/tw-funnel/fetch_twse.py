"""fetch_twse.py — 抓 TWSE 公開端點，更新 data/state/ 精簡狀態檔（唯讀、防禦性）。

端點全掛也不 crash：每端點結果記入 data/state/fetch_meta.json 的 endpoint_health，
後續 funnel.py / track_performance.py 憑既有狀態照常產出（誠實降級）。

原始回應落 data/tmp/{date}/（.gitignore，不入版控）；入版控的只有 data/state/ 精簡狀態：
  trust_history.json      投信買賣超逐日 {days: {date: {ticker: net_shares}}, names: {ticker: 名稱}}
  turnover_history.json   成交金額逐日（只留投信活躍股，控體積）{days: {date: {ticker: value_twd}}}
  revenue_history.json    月營收 {months: {YYYY-MM: {ticker: {rev, yoy}}}}
  latest_close.json       {date, close: {ticker: 收盤}, value: {ticker: 成交金額}}
  shares_outstanding.json {ticker: 已發行普通股數}
  veto_lists.json         {date, punish: [...], attention: [...], pledge_ratio: {ticker: 比率}}
  fetch_meta.json         {fetched_at, endpoint_health: {...}}
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config

BASE = Path(__file__).resolve().parent
STATE_DIR = BASE / "data" / "state"
TMP_DIR = BASE / "data" / "tmp"

TAIPEI_TZ = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

def taipei_today() -> str:
    return datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")


def load_json(path: Path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def parse_number(raw):
    """TWSE 數字常為含逗號字串（'1,234,567'）或空字串；解析失敗回 None。"""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).replace(",", "").replace("+", "").strip()
    if s in ("", "-", "--", "N/A", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def find_key(row: dict, *substrings):
    """在 row 的鍵裡找同時包含所有 substrings 的鍵（防欄位名微調）。"""
    for k in row.keys():
        if all(s in k for s in substrings):
            return k
    return None


def parse_roc_or_ad_date(raw) -> str | None:
    """把 '1140710' / '114/07/10' / '20260710' / '2026-07-10' 統一成 YYYY-MM-DD。"""
    if raw is None:
        return None
    s = str(raw).strip().replace("/", "").replace("-", "")
    if not s.isdigit():
        return None
    if len(s) == 7:      # 民國 YYYMMDD
        y, m, d = int(s[:3]) + 1911, int(s[3:5]), int(s[5:7])
    elif len(s) == 8:    # 西元 YYYYMMDD
        y, m, d = int(s[:4]), int(s[4:6]), int(s[6:8])
    else:
        return None
    try:
        return datetime(y, m, d).strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_roc_or_ad_month(raw) -> str | None:
    """把 '11406' / '202506' 統一成 YYYY-MM。"""
    if raw is None:
        return None
    s = str(raw).strip().replace("/", "").replace("-", "")
    if not s.isdigit():
        return None
    if len(s) == 5:      # 民國 YYYMM
        y, m = int(s[:3]) + 1911, int(s[3:5])
    elif len(s) == 6:    # 西元 YYYYMM
        y, m = int(s[:4]), int(s[4:6])
    else:
        return None
    if not 1 <= m <= 12:
        return None
    return f"{y:04d}-{m:02d}"


def prune_days(days: dict, keep: int) -> dict:
    """days 是 {date: {...}}；只留最近 keep 個鍵（日期字串排序即時間序）。"""
    keys = sorted(days.keys())
    return {k: days[k] for k in keys[-keep:]}


# ---------------------------------------------------------------------------
# HTTP（requests 延遲載入：離線測試 import 本模組不需要 requests）
# ---------------------------------------------------------------------------

def fetch_json(url: str, params: dict | None, health: dict, name: str):
    """GET url，retry/backoff；成功回 parsed JSON，失敗回 None 並記 health[name]。"""
    try:
        import requests  # noqa: PLC0415 — 延遲載入，離線測試不需安裝
    except ImportError as exc:
        health[name] = {"ok": False, "status": None, "error": f"requests unavailable: {exc}"}
        return None
    headers = {"User-Agent": config.USER_AGENT, "Accept": "application/json"}
    last_err, last_status = None, None
    for attempt in range(1 + config.HTTP_RETRIES):
        if attempt:
            time.sleep(config.HTTP_BACKOFFS[min(attempt - 1, len(config.HTTP_BACKOFFS) - 1)])
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=config.HTTP_TIMEOUT)
            last_status = resp.status_code
            if resp.status_code == 200:
                data = resp.json()
                health[name] = {"ok": True, "status": 200, "url": url}
                return data
            last_err = resp.text[: config.ERROR_BODY_SNIPPET_LEN]
        except Exception as exc:  # noqa: BLE001 — 防禦性：任何網路/解析錯誤都降級
            last_err = str(exc)[: config.ERROR_BODY_SNIPPET_LEN]
    health[name] = {"ok": False, "status": last_status, "error": last_err, "url": url}
    return None


# ---------------------------------------------------------------------------
# 各數據源解析（純函數，測試可離線餵 fixture）
# ---------------------------------------------------------------------------

def parse_t86_openapi(rows: list) -> tuple[str | None, dict, dict]:
    """OpenAPI /fund/T86 → (資料日期或 None, {ticker: 投信買賣超股數}, {ticker: 名稱})。"""
    net, names, data_date = {}, {}, None
    if not isinstance(rows, list):
        return None, {}, {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        code_k = find_key(row, "證券代號") or find_key(row, "Code")
        name_k = find_key(row, "證券名稱") or find_key(row, "Name")
        net_k = find_key(row, "投信買賣超")
        if not code_k or not net_k:
            continue
        code = str(row[code_k]).strip()
        if not code or not code[0].isdigit():
            continue
        n = parse_number(row[net_k])
        if n is None:
            continue
        if data_date is None:
            date_k = find_key(row, "日期") or find_key(row, "Date")
            if date_k:
                data_date = parse_roc_or_ad_date(row[date_k])
        if n != 0:
            net[code] = int(n)
            if name_k:
                names[code] = str(row[name_k]).strip()
    return data_date, net, names


def parse_t86_rwd(payload: dict) -> tuple[str | None, dict, dict]:
    """rwd T86（{date, fields, data}）→ 同 parse_t86_openapi 的輸出。"""
    if not isinstance(payload, dict):
        return None, {}, {}
    fields = payload.get("fields") or []
    rows = payload.get("data") or []
    data_date = parse_roc_or_ad_date(payload.get("date"))
    try:
        code_i = next(i for i, f in enumerate(fields) if "證券代號" in f)
        name_i = next(i for i, f in enumerate(fields) if "證券名稱" in f)
        net_i = next(i for i, f in enumerate(fields) if "投信買賣超" in f)
    except StopIteration:
        return data_date, {}, {}
    net, names = {}, {}
    for row in rows:
        if len(row) <= max(code_i, name_i, net_i):
            continue
        code = str(row[code_i]).strip()
        n = parse_number(row[net_i])
        if code and n is not None and n != 0:
            net[code] = int(n)
            names[code] = str(row[name_i]).strip()
    return data_date, net, names


def parse_stock_day_all(rows: list) -> tuple[dict, dict]:
    """STOCK_DAY_ALL → ({ticker: 收盤價}, {ticker: 成交金額 TWD})。"""
    close, value = {}, {}
    if not isinstance(rows, list):
        return {}, {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        code_k = find_key(row, "Code") or find_key(row, "證券代號")
        close_k = find_key(row, "ClosingPrice") or find_key(row, "收盤價")
        value_k = find_key(row, "TradeValue") or find_key(row, "成交金額")
        if not code_k:
            continue
        code = str(row[code_k]).strip()
        c = parse_number(row.get(close_k)) if close_k else None
        v = parse_number(row.get(value_k)) if value_k else None
        if code and c is not None and c > 0:
            close[code] = c
        if code and v is not None:
            value[code] = int(v)
    return close, value


def parse_revenue(rows: list) -> dict:
    """t187ap05_L → {YYYY-MM: {ticker: {"rev": 當月營收, "yoy": 去年同月增減%}}}。"""
    months: dict = {}
    if not isinstance(rows, list):
        return {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        code_k = find_key(row, "公司代號") or find_key(row, "Code")
        ym_k = find_key(row, "資料年月")
        rev_k = find_key(row, "當月營收")
        # 排除累計欄（鍵名含「累計」）
        if rev_k and "累計" in rev_k:
            rev_k = next(
                (k for k in row if "當月營收" in k and "累計" not in k), None)
        yoy_k = find_key(row, "去年同月增減")
        if not code_k or not ym_k:
            continue
        ym = parse_roc_or_ad_month(row[ym_k])
        code = str(row[code_k]).strip()
        if not ym or not code:
            continue
        rev = parse_number(row.get(rev_k)) if rev_k else None
        yoy = parse_number(row.get(yoy_k)) if yoy_k else None
        if yoy is None:
            continue
        months.setdefault(ym, {})[code] = {"rev": rev, "yoy": yoy}
    return months


def parse_shares_outstanding(rows: list) -> dict:
    """t187ap03_L → {ticker: 已發行普通股數}；缺欄位時退回 實收資本額/10（面額 10 元）。"""
    out = {}
    if not isinstance(rows, list):
        return {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        code_k = find_key(row, "公司代號") or find_key(row, "Code")
        if not code_k:
            continue
        code = str(row[code_k]).strip()
        shares_k = find_key(row, "已發行普通股")
        shares = parse_number(row.get(shares_k)) if shares_k else None
        if shares is None:
            cap_k = find_key(row, "實收資本額")
            cap = parse_number(row.get(cap_k)) if cap_k else None
            shares = cap / 10 if cap else None  # 台股普通股面額 10 元的粗估
        if code and shares and shares > 0:
            out[code] = int(shares)
    return out


def parse_code_list(rows: list) -> list:
    """處置/注意公告 → 證券代號清單（欄位名防禦性搜尋）。"""
    codes = []
    if not isinstance(rows, list):
        return []
    for row in rows:
        if not isinstance(row, dict):
            continue
        code_k = find_key(row, "證券代號") or find_key(row, "Code") or find_key(row, "股票代號")
        if code_k:
            code = str(row[code_k]).strip()
            if code and code[0].isdigit():
                codes.append(code)
    return sorted(set(codes))


def parse_pledge(rows: list) -> dict:
    """董監持股/設質 dataset（未實測 best-effort）→ {ticker: 質押比 0–1}。

    欄位防禦性搜尋：需同時找得到「設質」股數欄與「持股」股數欄才計算；
    找不到 → 回空 dict，上游記 degradation（誠實降級，不假裝有接）。
    """
    out = {}
    if not isinstance(rows, list):
        return {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        code_k = find_key(row, "公司代號") or find_key(row, "證券代號") or find_key(row, "Code")
        pledge_k = find_key(row, "設質", "股數") or find_key(row, "質押", "股數")
        hold_k = find_key(row, "持股", "股數") or find_key(row, "選任時持股")
        if not code_k or not pledge_k or not hold_k or pledge_k == hold_k:
            continue
        code = str(row[code_k]).strip()
        pledged = parse_number(row.get(pledge_k))
        held = parse_number(row.get(hold_k))
        if code and pledged is not None and held and held > 0:
            ratio = max(pledged / held, out.get(code, 0.0))  # 多列（逐董監）取最大
            out[code] = round(ratio, 4)
    return out


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_fetch(t86_date: str | None = None) -> dict:
    health: dict = {}
    today = taipei_today()
    tmp_day = TMP_DIR / today
    tmp_day.mkdir(parents=True, exist_ok=True)

    # --- 1. T86 投信買賣超 ---
    raw = fetch_json(config.T86_OPENAPI_URL, None, health, "t86_openapi")
    data_date, net, names = (None, {}, {})
    if raw is not None:
        save_json(tmp_day / "t86_openapi.json", raw)
        data_date, net, names = parse_t86_openapi(raw)
    if not net:  # 主端點失敗或解析為空 → rwd 備援（帶日期）
        d = t86_date or today.replace("-", "")
        raw2 = fetch_json(config.T86_RWD_URL,
                          {"date": d, "selectType": "ALL", "response": "json"},
                          health, "t86_rwd")
        if raw2 is not None:
            save_json(tmp_day / "t86_rwd.json", raw2)
            data_date, net, names = parse_t86_rwd(raw2)
    if net:
        data_date = data_date or today
        trust = load_json(STATE_DIR / "trust_history.json", {"days": {}, "names": {}})
        trust["days"][data_date] = net
        trust["days"] = prune_days(trust["days"], config.TRUST_HISTORY_KEEP_DAYS)
        trust["names"].update(names)
        # names 只留 days 內仍出現過的票，控體積
        active = {t for day in trust["days"].values() for t in day}
        trust["names"] = {t: n for t, n in trust["names"].items() if t in active}
        save_json(STATE_DIR / "trust_history.json", trust)
        print(f"T86: {data_date} 投信有動作 {len(net)} 檔")
    else:
        trust = load_json(STATE_DIR / "trust_history.json", {"days": {}, "names": {}})
        print("T86: 取數失敗（見 endpoint_health），沿用既有狀態")

    # --- 2. 全市場收盤/成交額 ---
    raw = fetch_json(config.STOCK_DAY_ALL_URL, None, health, "stock_day_all")
    if raw is not None:
        save_json(tmp_day / "stock_day_all.json", raw)
        close, value = parse_stock_day_all(raw)
        if close:
            save_json(STATE_DIR / "latest_close.json",
                      {"date": today, "close": close, "value": value})
            # 成交額歷史：只留投信活躍股（trust_history 出現過的），控體積
            active = {t for day in trust["days"].values() for t in day}
            tv = load_json(STATE_DIR / "turnover_history.json", {"days": {}})
            tv["days"][today] = {t: value[t] for t in active if t in value}
            tv["days"] = prune_days(tv["days"], config.TURNOVER_HISTORY_KEEP_DAYS)
            save_json(STATE_DIR / "turnover_history.json", tv)
            print(f"STOCK_DAY_ALL: {len(close)} 檔收盤價")
    else:
        print("STOCK_DAY_ALL: 取數失敗")

    # --- 3. 月營收 ---
    raw = fetch_json(config.REVENUE_URL, None, health, "revenue_t187ap05_L")
    if raw is not None:
        save_json(tmp_day / "revenue.json", raw)
        months = parse_revenue(raw)
        if months:
            rh = load_json(STATE_DIR / "revenue_history.json", {"months": {}})
            for ym, data in months.items():
                rh["months"][ym] = data
            keys = sorted(rh["months"].keys())
            rh["months"] = {k: rh["months"][k] for k in keys[-config.REVENUE_HISTORY_KEEP_MONTHS:]}
            save_json(STATE_DIR / "revenue_history.json", rh)
            print(f"月營收: {', '.join(sorted(months))} 共 {sum(len(v) for v in months.values())} 筆")
    else:
        print("月營收: 取數失敗")

    # --- 4. 已發行股數（市值用；低頻資料，失敗沿用舊檔） ---
    raw = fetch_json(config.COMPANY_BASIC_URL, None, health, "company_basic")
    if raw is not None:
        shares = parse_shares_outstanding(raw)
        if shares:
            save_json(STATE_DIR / "shares_outstanding.json", shares)
            print(f"已發行股數: {len(shares)} 檔")

    # --- 5. 否決清單（處置/注意/質押；全部 best-effort、誠實降級） ---
    veto = load_json(STATE_DIR / "veto_lists.json",
                     {"date": None, "punish": [], "attention": [], "pledge_ratio": {}})
    raw = fetch_json(config.PUNISH_URL, None, health, "punish_list")
    if raw is not None:
        veto["punish"] = parse_code_list(raw)
        veto["date"] = today
    raw = fetch_json(config.ATTENTION_URL, None, health, "attention_list")
    if raw is not None:
        veto["attention"] = parse_code_list(raw)
        veto["date"] = today
    raw = fetch_json(config.PLEDGE_URL, None, health, "pledge_t187ap11_L")
    if raw is not None:
        pledge = parse_pledge(raw)
        if pledge:
            veto["pledge_ratio"] = pledge
        else:
            health["pledge_t187ap11_L"]["ok"] = False
            health["pledge_t187ap11_L"]["error"] = "回應可取但無設質/持股欄位——欄位假設不成立，質押否決不生效"
    save_json(STATE_DIR / "veto_lists.json", veto)

    # --- 6. fetch meta ---
    meta = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "taipei_date": today,
        "endpoint_health": health,
    }
    save_json(STATE_DIR / "fetch_meta.json", meta)
    ok = sum(1 for h in health.values() if h.get("ok"))
    print(f"fetch 完成：{ok}/{len(health)} 端點成功（明細見 data/state/fetch_meta.json）")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description="TWSE 唯讀取數（防禦性，端點全掛也 exit 0）")
    ap.add_argument("--date", help="T86 rwd 備援端點的日期（YYYYMMDD），預設台北今日")
    args = ap.parse_args()
    try:
        run_fetch(t86_date=args.date)
    except Exception as exc:  # noqa: BLE001 — 最外層保底：任何意外都落 meta 不 crash
        save_json(STATE_DIR / "fetch_meta.json", {
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endpoint_health": {},
            "fatal_error": str(exc)[:500],
        })
        print(f"fetch 意外失敗（已記 meta）：{exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
