#!/usr/bin/env python3
"""
generate_history.py — 一次性回填過去 5 年 AVI/CRI/TSI 每日歷史分數

用法（在 GitHub Actions 或有網路的環境執行）：
    python scripts/generate_history.py [--days 1825]

輸出：docs/history.json（格式見下方）
"""

import sys, os, json, argparse, logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

DOCS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "docs"
))
HISTORY_PATH = os.path.join(DOCS_DIR, "history.json")

# ─── 載入引擎 ────────────────────────────────────────────────────────────────

from src.cpi import CrashProbabilityIndex
from src.tsi import TechStressIndex

cri_engine = CrashProbabilityIndex()
tsi_engine = TechStressIndex()

# ─── 下載市場數據 ─────────────────────────────────────────────────────────────

def download_data(days):
    try:
        import yfinance as yf
    except ImportError:
        log.error("yfinance 未安裝：pip install yfinance")
        sys.exit(1)

    end   = datetime.today()
    start = end - timedelta(days=days + 400)   # 多抓 400 天供計算視窗用
    start_s = start.strftime("%Y-%m-%d")
    end_s   = end.strftime("%Y-%m-%d")

    tickers = {
        "spy":  "SPY",
        "qqq":  "QQQ",
        "vix":  "^VIX",
        "vvix": "^VVIX",
        "soxx": "SOXX",
        "hyg":  "HYG",
        "mu":   "MU",
        "gspc": "^GSPC",
    }
    log.info(f"下載 {start_s} → {end_s} 市場數據...")
    raw = {}
    for k, sym in tickers.items():
        try:
            df = yf.download(sym, start=start_s, end=end_s,
                             auto_adjust=True, progress=False)
            if isinstance(df.columns, __import__('pandas').MultiIndex):
                df.columns = df.columns.get_level_values(0)
            raw[k] = df
            log.info(f"  {sym}: {len(df)} 筆")
        except Exception as e:
            log.warning(f"  {sym} 下載失敗: {e}")
            raw[k] = None

    # FRED（可選，失敗則略過）
    fred_key = os.environ.get("FRED_API_KEY", "")
    fred = {}
    if fred_key:
        try:
            import fredapi
            f = fredapi.Fred(api_key=fred_key)
            for code, name in [("DGS10","t10y"), ("DGS30","t30y"),
                                ("BAA","baa"), ("CPIAUCSL","cpi")]:
                try:
                    fred[name] = f.get_series(code, observation_start=start_s)
                except Exception as e:
                    log.warning(f"  FRED {code} 失敗: {e}")
        except ImportError:
            log.warning("fredapi 未安裝，略過 FRED 數據")
    return raw, fred

# ─── 計算 CRI（每日）────────────────────────────────────────────────────────

def compute_cri_series(raw, eval_dates):
    spy = raw.get("spy")
    vix_s = raw.get("vix")
    if spy is None or vix_s is None:
        return {}

    # 整理成 sp500 DataFrame（close + volume）
    sp500_df = __import__('pandas').DataFrame({
        "close":  spy["Close"] if "Close" in spy.columns else spy.iloc[:,0],
        "volume": spy["Volume"] if "Volume" in spy.columns else 0,
    }).dropna()
    vix_series = (vix_s["Close"] if "Close" in vix_s.columns else vix_s.iloc[:,0]).dropna()
    empty = __import__('pandas').Series(dtype=float)

    scores = {}
    for i, d in enumerate(eval_dates):
        if i % 200 == 0:
            log.info(f"  CRI 進度 {i}/{len(eval_dates)} ({d.date()})")
        try:
            sp_w  = sp500_df[sp500_df.index <= d].tail(300)
            vix_w = vix_series[vix_series.index <= d].tail(300)
            if len(sp_w) < 100 or len(vix_w) < 50:
                continue
            r = cri_engine.compute(
                sp500_daily=sp_w, vix_daily=vix_w, vix3m_daily=None,
                baa_daily=empty, aaa_daily=empty,
                treasury_10y=empty, treasury_2y=empty,
            )
            scores[d.strftime("%Y-%m-%d")] = round(r.score, 1)
        except Exception:
            pass
    return scores

# ─── 計算 TSI（每日）────────────────────────────────────────────────────────

def compute_tsi_series(raw, eval_dates):
    spy = raw.get("spy")
    if spy is None:
        return {}

    def get_close(key):
        df = raw.get(key)
        if df is None or df.empty:
            return __import__('pandas').Series(dtype=float)
        return (df["Close"] if "Close" in df.columns else df.iloc[:,0]).dropna()

    spy_close  = get_close("spy")
    qqq_close  = get_close("qqq")
    vix_close  = get_close("vix")
    vvix_close = get_close("vvix")
    soxx_close = get_close("soxx")
    hyg_close  = get_close("hyg")
    mu_close   = get_close("mu")
    empty = __import__('pandas').Series(dtype=float)

    def win(s, d, n=300):
        return s[s.index <= d].tail(n)

    scores = {}
    for i, d in enumerate(eval_dates):
        if i % 200 == 0:
            log.info(f"  TSI 進度 {i}/{len(eval_dates)} ({d.date()})")
        try:
            sp_w   = __import__('pandas').DataFrame({
                "close":  win(spy_close, d),
                "volume": 0,
            }).dropna()
            qqq_w  = win(qqq_close,  d)
            vix_w  = win(vix_close,  d)
            vvix_w = win(vvix_close, d) if len(vvix_close) else empty
            soxx_w = win(soxx_close, d) if len(soxx_close) else empty
            hyg_w  = win(hyg_close,  d) if len(hyg_close)  else empty
            mu_w   = win(mu_close,   d) if len(mu_close)   else empty
            if len(sp_w) < 60 or len(qqq_w) < 60:
                continue
            r = tsi_engine.compute(
                sp500_daily=sp_w, qqq_daily=qqq_w,
                vix_daily=vix_w, vvix_daily=vvix_w,
                soxx_daily=soxx_w, smh_daily=empty,
                hyg_daily=hyg_w, mu_daily=mu_w,
                treasury_10y=empty, treasury_30y=empty,
                treasury_2y=empty,
            )
            scores[d.strftime("%Y-%m-%d")] = round(r.score, 1)
        except Exception:
            pass
    return scores

# ─── 計算 AVI（月度，用可用數據近似）────────────────────────────────────────

def compute_avi_series(raw, fred, eval_dates):
    import numpy as np
    gspc = raw.get("gspc") or raw.get("spy")
    vix  = raw.get("vix")
    if gspc is None:
        return {}

    price = (gspc["Close"] if "Close" in gspc.columns else gspc.iloc[:,0]).dropna()
    vix_s = (vix["Close"]  if vix is not None and "Close" in vix.columns
             else (vix.iloc[:,0] if vix is not None else None))
    if vix_s is not None:
        vix_s = vix_s.dropna()

    t10y = fred.get("t10y")
    baa  = fred.get("baa")

    # CAPE 近似值：2021年約35，線性爬升到2026年6月約41.5
    def cape_approx(d):
        base = 35.0
        frac = (d - datetime(2021, 1, 1)).days / (365 * 5.5)
        return base + frac * 6.5

    def pctile(s, v, window=504):
        if s is None or len(s) < 10:
            return 50.0
        hist = s[s.index <= d].tail(window)
        if len(hist) < 10:
            return 50.0
        return float(np.mean(hist <= v) * 100)

    scores = {}
    prev_month = None
    cached_avi = None

    for d in eval_dates:
        month_key = (d.year, d.month)
        if month_key == prev_month and cached_avi is not None:
            scores[d.strftime("%Y-%m-%d")] = cached_avi
            continue

        try:
            p = price[price.index <= d]
            if len(p) < 200:
                continue
            cur_price = float(p.iloc[-1])
            ma200     = float(p.tail(200).mean())
            momentum  = min(100, max(0, (cur_price / ma200 - 1) * 200 + 50))

            cape     = cape_approx(d)
            cape_pct = min(100, max(0, (cape - 10) / 35 * 100))

            cur_vix = float(vix_s[vix_s.index <= d].iloc[-1]) if vix_s is not None and len(vix_s[vix_s.index<=d]) else 20.0
            macro   = pctile(vix_s, cur_vix)

            cur_t10y   = float(t10y[t10y.index <= d].iloc[-1]) if t10y is not None and len(t10y[t10y.index<=d]) else 4.0
            rate_pct   = min(100, max(0, (cur_t10y - 0.5) / 4.5 * 100))

            cur_baa   = float(baa[baa.index <= d].iloc[-1]) if baa is not None and len(baa[baa.index<=d]) else 5.5
            credit    = min(100, max(0, (cur_baa - cur_t10y - 0.5) / 5.5 * 100))

            profitability = 34.0

            avi = (cape_pct    * 0.38 +
                   rate_pct    * 0.14 +
                   macro       * 0.14 +
                   momentum    * 0.14 +
                   credit      * 0.12 +
                   profitability * 0.08) / 10.0
            avi = round(min(10.0, max(0.0, avi)), 2)

            cached_avi = avi
            prev_month = month_key
            scores[d.strftime("%Y-%m-%d")] = avi
        except Exception:
            if cached_avi:
                scores[d.strftime("%Y-%m-%d")] = cached_avi

    return scores

# ─── 主流程 ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=1825, help="回填天數（預設5年=1825）")
    parser.add_argument("--weekly", action="store_true", help="只算每週五（速度快5倍）")
    args = parser.parse_args()

    import pandas as pd

    raw, fred = download_data(args.days)

    # 確定評估日期範圍
    spy = raw.get("spy")
    if spy is None or spy.empty:
        log.error("SPY 數據下載失敗，無法繼續")
        sys.exit(1)

    cutoff = datetime.today() - timedelta(days=args.days)
    all_dates = spy.index[spy.index >= pd.Timestamp(cutoff)]
    if args.weekly:
        # 每週五
        eval_dates = [d for d in all_dates if d.weekday() == 4]
    else:
        eval_dates = list(all_dates)
    log.info(f"評估日期：{len(eval_dates)} 個（{'每週' if args.weekly else '每日'}）")

    log.info("計算 CRI 歷史分數...")
    cri_scores = compute_cri_series(raw, eval_dates)
    log.info(f"  CRI: {len(cri_scores)} 筆")

    log.info("計算 TSI 歷史分數...")
    tsi_scores = compute_tsi_series(raw, eval_dates)
    log.info(f"  TSI: {len(tsi_scores)} 筆")

    log.info("計算 AVI 歷史分數...")
    avi_scores = compute_avi_series(raw, fred, eval_dates)
    log.info(f"  AVI: {len(avi_scores)} 筆")

    # 合併：只保留三者都有的日期
    dates = sorted(set(cri_scores) & set(tsi_scores) & set(avi_scores))
    log.info(f"共 {len(dates)} 個有效交易日")

    history = {
        "d": dates,
        "a": [avi_scores[d] for d in dates],
        "c": [cri_scores[d] for d in dates],
        "t": [tsi_scores[d] for d in dates],
    }

    # 讀取現有 history.json，若已存在則合併（新數據優先）
    if os.path.exists(HISTORY_PATH):
        try:
            existing = json.loads(open(HISTORY_PATH).read())
            # 現有 KIWI-HISTORY-START marker 格式
            if "d" in existing:
                old = {existing["d"][i]: (existing["a"][i], existing["c"][i], existing["t"][i])
                       for i in range(len(existing["d"]))}
                new = {dates[i]: (history["a"][i], history["c"][i], history["t"][i])
                       for i in range(len(dates))}
                merged = {**old, **new}
                dates_m = sorted(merged)
                history = {
                    "d": dates_m,
                    "a": [merged[d][0] for d in dates_m],
                    "c": [merged[d][1] for d in dates_m],
                    "t": [merged[d][2] for d in dates_m],
                }
                log.info(f"合併後共 {len(dates_m)} 筆")
        except Exception as e:
            log.warning(f"讀取現有 history.json 失敗，覆寫：{e}")

    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, separators=(",", ":"))
    log.info(f"已寫入 {HISTORY_PATH}（{os.path.getsize(HISTORY_PATH)//1024} KB）")

    # 同步注入 index.html
    inject_html(history)

def inject_html(history):
    html_path = os.path.join(DOCS_DIR, "index.html")
    if not os.path.exists(html_path):
        log.warning(f"找不到 {html_path}，略過注入")
        return
    import re
    content = open(html_path, encoding="utf-8").read()
    json_str = json.dumps(history, separators=(",", ":"))
    new_block = f"// [KIWI-HISTORY-START]\nvar KIWI_HISTORY = {json_str};\n// [KIWI-HISTORY-END]"
    pattern = re.compile(
        r"// \[KIWI-HISTORY-START\].*?// \[KIWI-HISTORY-END\]", re.DOTALL
    )
    if pattern.search(content):
        content = pattern.sub(new_block, content)
    else:
        content = content.replace("// [KIWI-DATA-END]",
                                  "// [KIWI-DATA-END]\n</script>\n<script>\n" + new_block)
    open(html_path, "w", encoding="utf-8").write(content)
    log.info(f"已更新 {html_path} 的 KIWI-HISTORY 區塊")

if __name__ == "__main__":
    main()
