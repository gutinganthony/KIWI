"""fetch_data.py — 市場數據抓取：FinMind 主源、TWSE OpenAPI 次源（唯讀、防禦性）。

主/次源架構（2026-07-10 CI 實跑證實 TWSE OpenAPI 對 GitHub Actions 海外 IP
全數阻擋，故改以 FinMind 為主源；證據見 data/meta_latest.json endpoint_health）：
  投信買賣超   FinMind TaiwanStockInstitutionalInvestorsBuySell（全市場單日 1 req）
               → TWSE T86 OpenAPI → TWSE T86 rwd
  收盤/成交額  FinMind TaiwanStockPrice（全市場單日 1 req）→ TWSE STOCK_DAY_ALL
  月營收       FinMind TaiwanStockMonthRevenue（先篩後逐檔：買超資格池 ~50 檔
               × 近 15 個月，自算 YoY）→ TWSE t187ap05_L 全市場（官方 YoY）
  公司名/上市過濾  FinMind TaiwanStockInfo（type=twse 才留，1 req）
  已發行股數、處置/注意/質押清單  TWSE only（FinMind 無對應 dataset，best-effort）

端點全掛也不 crash：兩源結果都記入 data/state/fetch_meta.json 的 endpoint_health
（失敗含 body 前 150 字，診斷用），後續 funnel.py / track_performance.py 憑既有
狀態照常產出（誠實降級）。

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
import os
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


def month_start_n_ago(day: str, n: int) -> str:
    """'YYYY-MM-DD' 往前 n 個月的當月 1 日（YYYY-MM-DD）。逐檔營收窗口起點用。"""
    total = int(day[:4]) * 12 + (int(day[5:7]) - 1) - n
    return f"{total // 12:04d}-{total % 12 + 1:02d}-01"


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
# FinMind 主源 HTTP（api.finmindtrade.com/api/v4/data；回應包 {msg,status,data}）
# ---------------------------------------------------------------------------

def finmind_unwrap(payload):
    """FinMind 回應包裝 {"msg":"success","status":200,"data":[...]} → data list。

    msg 非 success（額度用盡/參數錯/被擋）或格式不符 → None（呼叫端視為硬失敗）。
    注意：data=[]（成功但當日無資料，例：假日）合法回傳空 list，與 None 有別。
    """
    if not isinstance(payload, dict) or payload.get("msg") != "success":
        return None
    data = payload.get("data")
    return data if isinstance(data, list) else None


def _finmind_request(params: dict) -> tuple[list | None, int | None, str | None]:
    """單次 FinMind GET（含 retry/backoff、可選 token 注入）。

    回 (data, http_status, error_snippet)：data=[] 是成功但無資料；None 是硬失敗。
    token 讀環境變數 FINMIND_TOKEN（可選）；未設定＝匿名低額度模式照樣能跑。
    """
    try:
        import requests  # noqa: PLC0415 — 延遲載入，離線測試不需安裝
    except ImportError as exc:
        return None, None, f"requests unavailable: {exc}"
    q = dict(params)
    token = os.environ.get(config.FINMIND_TOKEN_ENV, "").strip()
    if token:
        q["token"] = token
    headers = {"User-Agent": config.USER_AGENT, "Accept": "application/json"}
    last_err, last_status = None, None
    for attempt in range(1 + config.HTTP_RETRIES):
        if attempt:
            time.sleep(config.HTTP_BACKOFFS[min(attempt - 1, len(config.HTTP_BACKOFFS) - 1)])
        try:
            resp = requests.get(config.FINMIND_API_URL, params=q, headers=headers,
                                timeout=config.HTTP_TIMEOUT)
            last_status = resp.status_code
            if resp.status_code == 200:
                data = finmind_unwrap(resp.json())
                if data is not None:
                    return data, 200, None
            last_err = resp.text[: config.ERROR_BODY_SNIPPET_LEN]
        except Exception as exc:  # noqa: BLE001 — 防禦性：任何網路/解析錯誤都降級
            last_err = str(exc)[: config.ERROR_BODY_SNIPPET_LEN]
    return None, last_status, last_err


def fetch_finmind_day(dataset: str, day: str, health: dict, name: str):
    """全市場單日拉法：start_date=end_date=day（不帶 data_id）→ rows 或 None。

    當日 data=[]（假日/資料未發布）→ 往前一天再試，最多共試 FINMIND_DAY_LOOKBACK 天；
    硬失敗（額度/被擋/斷線）→ 立即放棄不再回溯（保護額度）。health[name] 記結果。
    """
    day_dt = datetime.strptime(day, "%Y-%m-%d")
    last_status = None
    for i in range(config.FINMIND_DAY_LOOKBACK):
        d = (day_dt - timedelta(days=i)).strftime("%Y-%m-%d")
        data, status, err = _finmind_request(
            {"dataset": dataset, "start_date": d, "end_date": d})
        if data:
            health[name] = {"ok": True, "status": status, "source": "finmind",
                            "dataset": dataset, "data_date": d, "rows": len(data)}
            return data
        if data is None:  # 硬失敗 → 不回溯
            health[name] = {"ok": False, "status": status, "source": "finmind",
                            "dataset": dataset, "error": err}
            return None
        last_status = status
        time.sleep(config.FINMIND_SLEEP_BETWEEN)
    health[name] = {"ok": False, "status": last_status, "source": "finmind",
                    "dataset": dataset,
                    "error": f"empty data for last {config.FINMIND_DAY_LOOKBACK} days"}
    return None


def fetch_finmind_table(dataset: str, health: dict, name: str):
    """不帶日期的全表拉法（TaiwanStockInfo 用；1 req）→ rows 或 None。"""
    data, status, err = _finmind_request({"dataset": dataset})
    if data:
        health[name] = {"ok": True, "status": status, "source": "finmind",
                        "dataset": dataset, "rows": len(data)}
        return data
    health[name] = {"ok": False, "status": status, "source": "finmind",
                    "dataset": dataset,
                    "error": err if data is None else "empty data"}
    return None


def fetch_finmind_revenue_pool(pool: list, today: str, health: dict) -> dict:
    """對候選池逐檔查近 REVENUE_LOOKBACK_MONTHS 個月營收並自算 YoY。

    先篩後逐檔（額度守則）：pool 由 chip_pass_pool() 以買超資格先縮到 ~50 檔，
    每檔 1 req → 常態 ~50 req、上限 REVENUE_POOL_MAX；連續硬失敗
    FINMIND_ABORT_AFTER_ERRORS 次即中止（源掛了/額度盡，保護剩餘額度）。
    回 {YYYY-MM: {ticker: {rev, yoy}}}（只含成功取得且算得出 YoY 的股票）。
    """
    start = month_start_n_ago(today, config.REVENUE_LOOKBACK_MONTHS)
    months: dict = {}
    fetched, errors, consec, last_err = 0, 0, 0, None
    take = pool[: config.REVENUE_POOL_MAX]
    for ticker in take:
        data, _status, err = _finmind_request(
            {"dataset": config.FINMIND_DS_MONTH_REVENUE, "data_id": ticker,
             "start_date": start, "end_date": today})
        if data:
            fetched += 1
            consec = 0
            for ym, rec in yoy_from_revenue(parse_finmind_month_revenue(data)).items():
                months.setdefault(ym, {})[ticker] = rec
        elif data is None:
            errors += 1
            consec += 1
            last_err = err
            if consec >= config.FINMIND_ABORT_AFTER_ERRORS:
                break
        else:
            consec = 0  # 成功但該檔無月營收（ETF 等）→ 略過
        time.sleep(config.FINMIND_SLEEP_BETWEEN)
    h = {"ok": errors == 0 or fetched > 0, "source": "finmind",
         "dataset": config.FINMIND_DS_MONTH_REVENUE,
         "pool": len(pool), "fetched": fetched, "errors": errors}
    if len(pool) > config.REVENUE_POOL_MAX:
        h["pool_truncated_to"] = config.REVENUE_POOL_MAX
    if consec >= config.FINMIND_ABORT_AFTER_ERRORS:
        h["ok"] = False
        h["aborted"] = True
    if last_err:
        h["error"] = last_err
    health["finmind_month_revenue"] = h
    return months


# ---------------------------------------------------------------------------
# FinMind 解析（純函數，測試可離線餵 fixture）
# ---------------------------------------------------------------------------

def parse_finmind_stock_info(rows: list) -> tuple[dict, set]:
    """TaiwanStockInfo → ({ticker: 中文名}, 上市（type=twse）ticker set)。

    type=tpex（上櫃）排除——v0 只做上市；非數字開頭代號（指數等）排除。
    """
    names, listed = {}, set()
    if not isinstance(rows, list):
        return {}, set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = str(row.get("stock_id", "")).strip()
        if not code or not code[0].isdigit():
            continue
        if str(row.get("type", "")).strip().lower() != "twse":
            continue
        listed.add(code)
        name = str(row.get("stock_name", "")).strip()
        if name:
            names[code] = name
    return names, listed


def parse_finmind_institutional(rows: list, listed: set | None = None) -> tuple[str | None, dict]:
    """TaiwanStockInstitutionalInvestorsBuySell（全市場單日）→
    (資料日期或 None, {ticker: 投信買賣超股數})。

    name 含 "Investment_Trust" 即投信（Foreign_Investor/Dealer_* 略過）；
    net = buy − sell；listed 給定時只留上市代號。
    """
    net, data_date = {}, None
    if not isinstance(rows, list):
        return None, {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if config.FINMIND_TRUST_NAME_KEY not in str(row.get("name", "")):
            continue
        code = str(row.get("stock_id", "")).strip()
        if not code or not code[0].isdigit():
            continue
        if listed is not None and code not in listed:
            continue
        buy, sell = parse_number(row.get("buy")), parse_number(row.get("sell"))
        if buy is None or sell is None:
            continue
        if data_date is None:
            data_date = parse_roc_or_ad_date(row.get("date"))
        n = int(buy - sell)
        if n != 0:
            net[code] = net.get(code, 0) + n
    return data_date, net


def parse_finmind_price(rows: list, listed: set | None = None) -> tuple[dict, dict]:
    """TaiwanStockPrice（全市場單日）→ ({ticker: 收盤}, {ticker: 成交金額 TWD})。"""
    close, value = {}, {}
    if not isinstance(rows, list):
        return {}, {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = str(row.get("stock_id", "")).strip()
        if not code or not code[0].isdigit():
            continue
        if listed is not None and code not in listed:
            continue
        c = parse_number(row.get("close"))
        v = parse_number(row.get("Trading_money"))
        if c is not None and c > 0:
            close[code] = c
        if v is not None:
            value[code] = int(v)
    return close, value


def parse_finmind_month_revenue(rows: list) -> dict:
    """TaiwanStockMonthRevenue（單檔多月）→ {YYYY-MM: 當月營收}（用 revenue_year/month）。"""
    out = {}
    if not isinstance(rows, list):
        return {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        y = parse_number(row.get("revenue_year"))
        m = parse_number(row.get("revenue_month"))
        rev = parse_number(row.get("revenue"))
        if y is None or m is None or rev is None or not 1 <= int(m) <= 12:
            continue
        out[f"{int(y):04d}-{int(m):02d}"] = rev
    return out


def yoy_from_revenue(rev_by_month: dict) -> dict:
    """{YYYY-MM: rev} → {YYYY-MM: {"rev": rev, "yoy": 去年同月增減%}}。

    去年同月缺或 ≤0 → 該月不產 YoY（誠實略過，不假造）；語意同 TWSE
    t187ap05_L 的「去年同月增減(%)」欄，餵 funnel 判 YoY>0 與加速。
    """
    out = {}
    for ym, rev in rev_by_month.items():
        prev = rev_by_month.get(f"{int(ym[:4]) - 1:04d}-{ym[5:7]}")
        if rev is None or prev is None or prev <= 0:
            continue
        out[ym] = {"rev": rev, "yoy": round((rev / prev - 1.0) * 100.0, 2)}
    return out


def chip_pass_pool(trust_days: dict, close: dict, cfg: dict | None = None) -> list:
    """「先篩後逐檔」的候選池：與 funnel 第一層籌碼關同判準（保證覆蓋可能入池股）。

    最新一日投信買超 >0 且 近 QUAL_WINDOW_DAYS 日累計 ≥ 股數或金額門檻（OR）。
    回傳按 3 日買超市值（無收盤價用股數）由大到小排序——池超過上限截斷時保大者。
    """
    if not trust_days:
        return []

    def g(key):
        return cfg[key] if cfg and key in cfg else getattr(config, key)

    window = sorted(trust_days)[-int(g("QUAL_WINDOW_DAYS")):]
    as_of = window[-1]
    pool = []
    for ticker, net in trust_days[as_of].items():
        if net <= 0:
            continue
        cum = sum(trust_days[d].get(ticker, 0) for d in window)
        px = close.get(ticker)
        if cum >= g("MIN_3D_NET_BUY_SHARES") or (
                px is not None and cum * px >= g("MIN_3D_NET_BUY_VALUE_TWD")):
            pool.append((cum * px if px is not None else cum, ticker))
    return [t for _, t in sorted(pool, key=lambda x: (-x[0], x[1]))]


def merge_revenue_months(existing: dict, new_months: dict, keep: int) -> dict:
    """月營收狀態合併：同月「逐檔 update」而非整月覆蓋——FinMind 逐檔制下，
    不同日抓到的候選股會落在同一個月，整月覆蓋會洗掉先前股票。最後修剪到 keep 個月。
    """
    merged = {ym: dict(data) for ym, data in existing.items()}
    for ym, data in new_months.items():
        merged.setdefault(ym, {}).update(data)
    keys = sorted(merged)
    return {k: merged[k] for k in keys[-keep:]}


# ---------------------------------------------------------------------------
# TWSE 次源解析（純函數，測試可離線餵 fixture）
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

    # --- 0. 公司名／上市過濾（FinMind TaiwanStockInfo，1 req）---
    # 失敗 → listed=None（不過濾，誠實記 health）、名稱沿用既有狀態/TWSE fallback
    fm_names, listed = {}, None
    rows = fetch_finmind_table(config.FINMIND_DS_STOCK_INFO, health, "finmind_stock_info")
    if rows:
        fm_names, listed_set = parse_finmind_stock_info(rows)
        listed = listed_set or None
        print(f"TaiwanStockInfo: 上市 {len(listed_set)} 檔（tpex 已排除）")

    # --- 1. 投信買賣超（主：FinMind 全市場單日；次：TWSE T86 OpenAPI → rwd）---
    data_date, net, names = None, {}, {}
    rows = fetch_finmind_day(config.FINMIND_DS_INSTITUTIONAL, today, health,
                             "finmind_institutional")
    if rows:
        save_json(tmp_day / "finmind_institutional.json", rows)
        data_date, net = parse_finmind_institutional(rows, listed)
        names = {t: fm_names[t] for t in net if t in fm_names}
    if not net:  # FinMind 失敗/空 → TWSE fallback
        raw = fetch_json(config.T86_OPENAPI_URL, None, health, "t86_openapi")
        if raw is not None:
            save_json(tmp_day / "t86_openapi.json", raw)
            data_date, net, names = parse_t86_openapi(raw)
        if not net:  # 再退 rwd 備援（帶日期）
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
        print(f"投信買賣超: {data_date} 有動作 {len(net)} 檔")
    else:
        trust = load_json(STATE_DIR / "trust_history.json", {"days": {}, "names": {}})
        print("投信買賣超: 兩源皆失敗（見 endpoint_health），沿用既有狀態")

    # --- 2. 全市場收盤/成交額（主：FinMind TaiwanStockPrice 單日；次：TWSE）---
    close, value, price_date = {}, {}, None
    rows = fetch_finmind_day(config.FINMIND_DS_PRICE, today, health, "finmind_price")
    if rows:
        save_json(tmp_day / "finmind_price.json", rows)
        close, value = parse_finmind_price(rows, listed)
        price_date = health["finmind_price"].get("data_date")
    if not close:  # FinMind 失敗/空 → TWSE fallback
        raw = fetch_json(config.STOCK_DAY_ALL_URL, None, health, "stock_day_all")
        if raw is not None:
            save_json(tmp_day / "stock_day_all.json", raw)
            close, value = parse_stock_day_all(raw)
            price_date = today
    if close:
        price_date = price_date or today
        save_json(STATE_DIR / "latest_close.json",
                  {"date": price_date, "close": close, "value": value})
        # 成交額歷史：只留投信活躍股（trust_history 出現過的），控體積
        active = {t for day in trust["days"].values() for t in day}
        tv = load_json(STATE_DIR / "turnover_history.json", {"days": {}})
        tv["days"][price_date] = {t: value[t] for t in active if t in value}
        tv["days"] = prune_days(tv["days"], config.TURNOVER_HISTORY_KEEP_DAYS)
        save_json(STATE_DIR / "turnover_history.json", tv)
        print(f"收盤/成交額: {price_date} 共 {len(close)} 檔")
    else:
        print("收盤/成交額: 兩源皆失敗，沿用既有狀態")

    # --- 3. 月營收（主：FinMind 先篩後逐檔；次：TWSE t187ap05_L 全市場）---
    # 「先篩後逐檔」：全市場逐檔查太貴 → 先用買超資格（同 funnel 籌碼關）縮池
    # ~50 檔，逐檔查近 15 個月自算 YoY（本月＋上月 YoY 都要去年同期）。
    latest_close_map = close or load_json(
        STATE_DIR / "latest_close.json", {"close": {}}).get("close", {})
    pool = chip_pass_pool(trust["days"], latest_close_map)
    fm_months = {}
    if pool:
        fm_months = fetch_finmind_revenue_pool(pool, today, health)
    else:
        health["finmind_month_revenue"] = {
            "ok": True, "source": "finmind", "pool": 0,
            "note": "候選池為空（無買超達標股），本日無需逐檔查營收"}
    new_months = [fm_months] if fm_months else []
    # FinMind 失敗/中止/池空 → TWSE 全市場 fallback（也可補齊被中止漏掉的股票）
    if not fm_months or health["finmind_month_revenue"].get("aborted"):
        raw = fetch_json(config.REVENUE_URL, None, health, "revenue_t187ap05_L")
        if raw is not None:
            save_json(tmp_day / "revenue.json", raw)
            tw_months = parse_revenue(raw)
            if tw_months:
                new_months.append(tw_months)
    if new_months:
        rh = load_json(STATE_DIR / "revenue_history.json", {"months": {}})
        for months in new_months:
            rh["months"] = merge_revenue_months(
                rh["months"], months, config.REVENUE_HISTORY_KEEP_MONTHS)
        save_json(STATE_DIR / "revenue_history.json", rh)
        got = sorted({ym for m in new_months for ym in m})
        print(f"月營收: 更新 {len(got)} 個月（最新 {got[-1]}）；候選池 {len(pool)} 檔")
    else:
        print("月營收: 無新資料（池空/兩源皆失敗），沿用既有狀態")

    # --- 4. 已發行股數（市值用；FinMind 需求 dataset 無此欄 → TWSE only，失敗沿用舊檔） ---
    raw = fetch_json(config.COMPANY_BASIC_URL, None, health, "company_basic")
    if raw is not None:
        shares = parse_shares_outstanding(raw)
        if shares:
            save_json(STATE_DIR / "shares_outstanding.json", shares)
            print(f"已發行股數: {len(shares)} 檔")

    # --- 5. 否決清單（處置/注意/質押；FinMind 無對應 dataset → TWSE only best-effort、誠實降級） ---
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
    ap = argparse.ArgumentParser(
        description="市場數據唯讀取數：FinMind 主源、TWSE 次源（防禦性，端點全掛也 exit 0）")
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
