#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
白鯨記・紫點（白鯨之眼 v3）選股與進出場 ── 可獨立執行的回測／掃描程式
=====================================================================

只用 Python 標準函式庫（3.8 以上），不需要 pip install 任何東西。

  python whale_purple_dot.py scan                       # 今天亮紫點的股票
  python whale_purple_dot.py scan --mode site_purple    # 網站「🟣 全市場今日紫燈」名單
  python whale_purple_dot.py backtest                   # 用下方 CONFIG 的設定回測全市場（約 2,000 檔，第一次要下載十幾分鐘）
  python whale_purple_dot.py backtest --codes 2330,2317,3617 --start 2024-01-01
  python whale_purple_dot.py backtest --stop 0.15 --hold 60
  python whale_purple_dot.py backtest --rule 2026-08    # 改用現行規則（E/G/H 不算紫點）

輸出：whale_out/ 底下的 CSV（每筆交易、每日名單）＋ 終端機摘要。
抓下來的 K 線會存在 whale_cache/，第二次跑不會重抓。

---------------------------------------------------------------------
這支程式在做什麼（三層）
---------------------------------------------------------------------
一、指標：白鯨之眼快線／慢線（-100 ~ +100）
    快線 = 短期動能：MA5/MA13 斜率 + MA5 與 MA13 的距離 + 收盤位置×量比 + 近 10 日區間位置，EMA(3) 平滑
    慢線 = 中期動能：MA34/MA55 斜率 + MA34 與 MA55 的距離 + 20 日均量趨勢 + 近 34 日區間位置，EMA(7) 平滑

二、紫點（launch_confirm）：九個場景任一成立，且距上一個紫點 > 10 根 K 棒
    前提（不逆勢）：慢線兩日斜率 ≥ +1（I、H 兩個高位場景允許 ≥ 0）
      I 極端洗盤   慢線連 3 根 > +50、快線 ≤ -50、兩線都止跌
      H 高位深拉回 慢線 > +50、快線 < 0、快線兩日斜率 ≥ +1
      ── 以下慢線須 ≤ +50 且兩日斜率 ≥ +1 ──
      G 動能爆發   快線剛突破 +50
      B 走出深底   快線近 4 根曾 ≤ -50，現在 > -50 且斜率 ≥ +1
      D 雙線出水   慢線剛上穿 0，快線 > 0
      C 快線出水   快線剛上穿 0，慢線 < 0
      A 雙底翻轉   兩線都 < 0，快線斜率 ≥ +1
      F 強勢續攻   兩線都 > 0，快線淺回後再起
      E 回檔再起   慢線 0~+50，快線 < 0 且斜率 ≥ +1
    （優先序由上而下，一根 K 棒只會落一個場景）

三、選股（SELECT_MODE，兩種）
    母體 = 上市＋上櫃 4 碼代號（含 4 碼 ETF，與網站相同）

    "any_purple"（預設）── 有紫點就進場
       每出現一顆新紫點，隔天開盤買進；不管它之後有沒有其他訊號、不設成交量門檻。
       這是「紫點實測」實際的做法（2026-06/07 那 5 筆，有 3 筆在紫點出現 32～51 天後才買，
       其間還出現過紅色交叉、潮退等訊號，網站的紫燈模式不會列出它們）。

    "site_purple" ── 網站「🟣 全市場今日紫燈」的篩法（逐行照網站程式）
       1. 每檔算出 60 天內的所有訊號（紫點以外還有綠／紅交叉、Pivot、潮起潮退、深度樞紐）
       2. 取「最新的那一個訊號」── 它必須是紫點，且距今 ≤ SCAN_DAYS 個日曆日
          （紫點之後若又出現其他訊號，例如紅色交叉，就不會入選）
       3. 近 20 日均量 ≥ MIN_VOL_LOTS 張（網站下拉選單 1,000 / 3,000 / 5,000 / 10,000，預設 3,000）

    出場：網站本身沒有出場規則（當時的設計是「進場靠系統、出場靠心態」）。
    這裡提供可調的出場：持有 N 個交易日、固定停損、移動停損、停損後是否允許下一次紫點再進場。

---------------------------------------------------------------------
兩個版本（RULE_VERSION）
---------------------------------------------------------------------
  "2026-07"：九個場景全部算紫點（2026 年 6～7 月「紫點實測」當時線上用的版本）
  "2026-08"：E 回檔再起 / G 動能爆發 / H 高位深拉回 不再算紫點（2026-08-28 起線上版本）
             這三個場景被拿掉時「不佔用」10 根冷卻期

---------------------------------------------------------------------
與網站的差異（請讀）
---------------------------------------------------------------------
* 價格：與網站相同，用 Yahoo 的還原權值價（四捨五入到小數 2 位），量用原始股數。
  指標全是比例，不受還原造成的等比例縮放影響。
* 網站每天只抓「最近 540 個日曆日」來算；這裡為了速度，每檔只算一次整段歷史，
  再逐日只看「截至當天」的訊號（全部指標都只用過去資料，沒有前視）。
  已用網站原始程式碼對照：80 檔 × 67,681 個股票-日，兩種算法的名單完全相同。
* 母體是「今天還在掛牌」的股票 ── 期間下市的股票不在裡面（倖存者偏誤，回測會偏樂觀）。
* 同一天名單裡常有幾十檔、而且持有期互相重疊，交易筆數 ≠ 獨立樣本數。
  請把結果當成「這套規則在這段期間的表現」，不要當成統計顯著性。
"""

import argparse
import csv
import json
import math
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

# ════════════════════════════════════════════════════════════════════
# CONFIG ── 主要可調參數都在這裡（命令列參數會覆蓋）
# ════════════════════════════════════════════════════════════════════
CONFIG = {
    "RULE_VERSION": "2026-07",   # "2026-07"（紫點實測當時）或 "2026-08"（現行，E/G/H 不算）

    # ── 選股 ──
    "SELECT_MODE": "any_purple", # "any_purple"＝有紫點就進（紫點實測的做法）；"site_purple"＝網站 🟣 紫燈模式
    "SCAN_DAYS": 1,              # scan 指令列出幾個日曆日內的紫點；site_purple 回測也用它（網站預設「今天」=1，可選 7/14/30/60）
    "MIN_VOL_LOTS": None,        # 近 20 日均量門檻（張）；None = any_purple 不設、site_purple 用網站預設 3000
    "FRESH_DAYS": 60,            # site_purple 的「最新訊號」搜尋窗口（網站固定 60，勿改）

    # ── 回測期間 ──
    "START": "2024-01-01",
    "END": None,                 # None = 到最新資料

    # ── 進場 ──
    "ENTRY": "next_open",        # "next_open"＝入選隔天開盤買；"close"＝入選當天收盤買

    # ── 出場（網站沒有出場規則，以下是可調的實驗設定）──
    "HOLD_DAYS": 60,             # 最長持有 N 個交易日，到期以收盤價出場；None = 不設上限（持有到資料結束）
    "STOP_LOSS": None,           # 固定停損，例 0.15 = 收盤跌破成本 -15% 當天收盤出場；None = 不停損
    "TRAIL_STOP": None,          # 移動停損，例 0.20 = 收盤自持有期最高收盤回落 20% 出場；None = 不用
    "REENTRY_AFTER_STOP": True,  # 停損出場後，該股再次入選名單時可以再進場
                                 #   False = 停損後到原本持有期結束前都不再碰這檔

    # ── 成本 ──
    "COST_ROUNDTRIP_PCT": 0.585, # 來回成本 %：手續費 0.1425%×2 + 證交稅 0.3%（有折讓請自行調低）

    # ── 資料品質 ──
    "JUMP_PCT": 11.0,            # 持有期間（含進場那根）任一日收盤漲跌超過 ±此 %（台股漲跌停 10%）→ 標記 jump_flag
                                 #   多半是 Yahoo 沒還原的分割／減資（例：0052 2025 年分割被算成 -83%），摘要會另列排除後的結果

    # ── 比較基準 ──
    "BENCHMARK": "^TWII",        # 每筆交易同期的加權指數報酬，用來算超額

    # ── 抓資料 ──
    "CACHE_DIR": "whale_cache",
    "OUT_DIR": "whale_out",
    "WORKERS": 6,                # 同時抓幾檔（Yahoo 會限流，別開太大）
    "SLEEP": 0.3,                # 每次請求後休息秒數
    "FINMIND_TOKEN": os.environ.get("FINMIND_TOKEN", ""),   # 有的話抓清單比較穩，沒有也行
}

YF_HEADERS = {   # 與網站相同；沒有 User-Agent 會被 Yahoo 回 429
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# 場景代號 → 中文
KIND_LABEL = {
    "washout": "I 極端洗盤", "high_pullback": "H 高位深拉回", "thrust_breakout": "G 動能爆發",
    "climb_out": "B 走出深底", "twin_breakout": "D 雙線出水", "fast_breakout": "C 快線出水",
    "twin_reversal": "A 雙底翻轉", "continuation": "F 強勢續攻", "pullback_reentry": "E 回檔再起",
}
DEMOTED_2026_08 = {"pullback_reentry", "thrust_breakout", "high_pullback"}


# ════════════════════════════════════════════════════════════════════
# 一、白鯨之眼 v3：快慢線 + 全部訊號（逐行移植自網站 calcWhaleEyeV3）
# ════════════════════════════════════════════════════════════════════
def _js_round2(x):
    """等同 JavaScript 的 Number(x.toFixed(2))（對正數：剛好一半時取大）。"""
    return float(Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _sma(arr, n):
    out = [None] * len(arr)
    s, cnt = 0.0, 0
    need = math.ceil(n * 0.8)
    for i in range(len(arr)):
        if arr[i] is not None:
            s += arr[i]; cnt += 1
        if i >= n and arr[i - n] is not None:
            s -= arr[i - n]; cnt -= 1
        if cnt >= need:
            out[i] = s / cnt
    return out


def _ema(arr, n):
    out = [None] * len(arr)
    k = 2 / (n + 1)
    prev = None
    for i in range(len(arr)):
        if arr[i] is None:
            out[i] = prev
            continue
        prev = arr[i] if prev is None else arr[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def _pct_slope(arr, i, lb):
    if i < lb or arr[i] is None or arr[i - lb] is None:
        return 0
    base = abs(arr[i - lb])
    return (arr[i] - arr[i - lb]) / base * 100 if base > 0 else 0


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def whale_eye_v3(rows, rule_version="2026-07"):
    """rows: [{'time':'YYYY-MM-DD','open','high','low','close','volume'}...]（舊→新）
    回傳 dict：fast/slow 序列與八類訊號清單；資料不足回傳 None。"""
    if len(rows) < 80:
        return None
    valid = [r for r in rows if r.get("close") is not None and r.get("time")]
    if len(valid) < 80:
        return None
    closes = [b["close"] for b in valid]
    highs = [b["high"] if b.get("high") is not None else b["close"] for b in valid]
    lows = [b["low"] if b.get("low") is not None else b["close"] for b in valid]
    vols = [b["volume"] if (b.get("volume") is not None and b["volume"] > 0) else 0 for b in valid]
    opens = [b["open"] if b.get("open") is not None else b["close"] for b in valid]
    times = [b["time"] for b in valid]

    ma5, ma13, ma34, ma55 = _sma(closes, 5), _sma(closes, 13), _sma(closes, 34), _sma(closes, 55)
    vol_ma20 = _sma(vols, 20)
    N = len(valid)
    fast_raw = [None] * N
    slow_raw = [None] * N

    for i in range(60, N):
        if ma55[i] is None or ma34[i] is None or ma13[i] is None or ma5[i] is None:
            continue
        c, h, l, v = closes[i], highs[i], lows[i], vols[i]
        # 快線
        F1 = _clamp((_pct_slope(ma5, i, 5) * 0.6 + _pct_slope(ma13, i, 5) * 0.4) * 8, -35, 35)
        d513 = (ma5[i] - ma13[i]) / ma13[i] * 100 if ma13[i] != 0 else 0
        F2 = _clamp(d513 * 6, -25, 25)
        vol_ratio = v / vol_ma20[i] if (vol_ma20[i] and vol_ma20[i] > 0) else 1
        close_strength = (c - l) / (h - l) - 0.5 if h > l else 0
        F3 = _clamp(close_strength * vol_ratio * 40, -20, 20)
        lb10 = closes[max(0, i - 9): i + 1]
        F4 = 0
        if len(lb10) > 1:
            hi10, lo10 = max(lb10), min(lb10)
            pos = (c - lo10) / (hi10 - lo10) - 0.5 if hi10 > lo10 else 0
            F4 = _clamp(pos * 40, -20, 20)
        fast_raw[i] = F1 + F2 + F3 + F4
        # 慢線
        S1 = _clamp((_pct_slope(ma34, i, 10) * 0.6 + _pct_slope(ma55, i, 10) * 0.4) * 10, -40, 40)
        d3455 = (ma34[i] - ma55[i]) / ma55[i] * 100 if ma55[i] != 0 else 0
        S2 = _clamp(d3455 * 4, -25, 25)
        S3 = 0
        if i >= 20 and vol_ma20[i] and vol_ma20[i - 10]:
            vol_trend = (vol_ma20[i] - vol_ma20[i - 10]) / vol_ma20[i - 10] * 100
            above55 = 1 if (ma55[i] and c > ma55[i]) else -1
            S3 = _clamp(vol_trend * above55 * 0.5, -15, 15)
        S4 = 0
        lb34 = closes[max(0, i - 33): i + 1]
        if len(lb34) > 1:
            hi34, lo34 = max(lb34), min(lb34)
            pos34 = (c - lo34) / (hi34 - lo34) - 0.5 if hi34 > lo34 else 0
            S4 = _clamp(pos34 * 40, -20, 20)
        slow_raw[i] = S1 + S2 + S3 + S4

    fast = _ema(fast_raw, 3)
    slow = _ema(slow_raw, 7)
    fast = [None if x is None else _clamp(x, -100, 100) for x in fast]
    slow = [None if x is None else _clamp(x, -100, 100) for x in slow]

    ma30 = _sma(closes, 30)
    bull, bear, pbull, pbear, tide_r, tide_f, launch, deep = [], [], [], [], [], [], [], []
    last_bull = last_bear = last_pbull = last_pbear = -10
    last_tr = last_tf = last_launch = last_deep = -10

    def mk(i, **kw):
        d = {"time": times[i], "idx": i, "price": closes[i], "fast": fast[i], "slow": slow[i]}
        d.update(kw)
        return d

    for i in range(61, N):
        f, s, fp, sp = fast[i], slow[i], fast[i - 1], slow[i - 1]
        if f is None or s is None or fp is None or sp is None:
            continue
        cross_up = fp <= sp and f > s
        cross_down = fp >= sp and f < s

        if cross_up and i - last_bull > 3:
            accel = f >= 50 and s >= 50
            slow_stable = slow[i - 3] is not None and s >= slow[i - 3] - 2
            strong = f <= -50 and slow_stable and not accel
            bull.append(mk(i, sig="green_accel" if accel else ("green_strong" if strong else "green")))
            last_bull = i
        if cross_down and i - last_bear > 3:
            slow_falling = slow[i - 5] is not None and (slow[i - 5] - s) > 3
            bear.append(mk(i, sig="red_strong" if (f >= 50 and slow_falling) else "red"))
            last_bear = i

        # Pivot（轉折但未交叉）
        if i >= 65 and fast[i - 2] is not None and slow[i - 2] is not None:
            if f < s and i - last_pbull > 5 and i - last_bull > 5:
                hit = any(fast[k] is not None and fast[k] <= -50 for k in range(max(60, i - 6), i + 1))
                if hit and f > fast[i - 2] and abs(f - s) < abs(fast[i - 2] - slow[i - 2]):
                    pbull.append(mk(i, sig="pivot_bull"))
                    last_pbull = i
            if f > s and i - last_pbear > 5 and i - last_bear > 5:
                hit = any(fast[k] is not None and fast[k] >= 50 for k in range(max(60, i - 6), i + 1))
                if hit and f < fast[i - 2] and abs(f - s) < abs(fast[i - 2] - slow[i - 2]):
                    pbear.append(mk(i, sig="pivot_bear"))
                    last_pbear = i

        # 🟣 紫點（九場景）
        if (i >= 65 and None not in (fast[i - 1], fast[i - 2], fast[i - 3], slow[i - 1], slow[i - 2], slow[i - 3])):
            ss2 = s - slow[i - 2]
            fs2 = f - fast[i - 2]
            if i - last_launch > 10:
                trig = None
                if s > 50 and slow[i - 3] > 50 and f <= -50 and ss2 >= 0 and fs2 >= 0:
                    trig = "washout"
                elif s > 50 and f < 0 and ss2 >= 0 and fs2 >= 1:
                    trig = "high_pullback"
                elif s <= 50 and ss2 >= 1:
                    if f > 50 and fast[i - 1] <= 50:
                        trig = "thrust_breakout"
                    elif f <= 50:
                        was_deep = (fast[i - 1] <= -50 or fast[i - 2] <= -50 or fast[i - 3] <= -50
                                    or (i >= 4 and fast[i - 4] is not None and fast[i - 4] <= -50))
                        if was_deep and f > -50 and fs2 >= 1:
                            trig = "climb_out"
                        elif s > 0 and slow[i - 1] <= 0 and f > 0:
                            trig = "twin_breakout"
                        elif f > 0 and fast[i - 1] <= 0 and s < 0:
                            trig = "fast_breakout"
                        elif f < 0 and s < 0 and fs2 >= 1:
                            trig = "twin_reversal"
                        elif s > 0 and f > 0 and fs2 >= 1:
                            if i >= 4 and fast[i - 4] is not None and min(fast[i - 2], fast[i - 3], fast[i - 4]) < f - 2:
                                trig = "continuation"
                        elif s > 0 and f < 0 and fs2 >= 1:
                            trig = "pullback_reentry"
                demoted = rule_version == "2026-08" and trig in DEMOTED_2026_08
                if trig and not demoted:
                    launch.append(mk(i, sig="launch_confirm", kind=trig, fast_slope=fs2, slow_slope=ss2))
                    last_launch = i

        # 深度樞紐
        if i >= 65 and None not in (fast[i - 1], fast[i - 2], fast[i - 3], slow[i - 3]):
            m30 = ma30[i]
            dist30 = (closes[i] - m30) / m30 * 100 if (m30 is not None and m30 > 0) else None
            if (f < 0 and s < 0
                    and (fast[i - 1] <= -50 or fast[i - 2] <= -50 or fast[i - 3] <= -50)
                    and (f - fast[i - 2]) >= 10
                    and (s - slow[i - 3]) <= 5
                    and dist30 is not None and dist30 <= -5
                    and closes[i] > opens[i]
                    and closes[i - 1] >= closes[i - 2] * 0.97
                    and i - last_deep > 4):
                deep.append(mk(i, sig="deep_pivot"))
                last_deep = i

        # 潮起／潮退
        if fast[i - 1] is not None and slow[i - 1] is not None:
            if f < 0 and s < 0 and f > fp and s > sp and i - last_tr > 5:
                tide_r.append(mk(i, sig="tide_rise")); last_tr = i
            if f > 0 and s > 0 and f < fp and s < sp and i - last_tf > 5:
                tide_f.append(mk(i, sig="tide_fall")); last_tf = i

    # 每根 K 棒「截至當天的最新訊號」。
    # ⚠️ 同一天有多個訊號時，網站取這個串接順序裡較後面的那一類（綠紅交叉 → Pivot → 潮起潮退 → 紫點 → 深度樞紐），
    #    例如紫點與深度樞紐同日，最新訊號算深度樞紐 → 不會進 🟣 名單。
    groups = [bull, bear, pbull, pbear, tide_r, tide_f, launch, deep]
    events = sorted(((m["idx"], g, m) for g, grp in enumerate(groups) for m in grp), key=lambda x: (x[0], x[1]))
    latest = [None] * N
    k, cur = 0, None
    for i in range(N):
        while k < len(events) and events[k][0] <= i:
            cur = events[k][2]; k += 1
        latest[i] = cur

    return {"times": times, "closes": closes, "fast": fast, "slow": slow,
            "groups": groups, "launch": launch, "launch_at": {m["idx"]: m for m in launch}, "latest": latest}


# ════════════════════════════════════════════════════════════════════
# 二、選股：網站「🟣 全市場今日紫燈」
# ════════════════════════════════════════════════════════════════════
def _days_between(d1, d2):
    return (date.fromisoformat(d2) - date.fromisoformat(d1)).days


def latest_signal_asof(eye, asof_idx, fresh_days=60, asof_date=None):
    """截至第 asof_idx 根 K 棒，網站會認定的「最新訊號」（只看 fresh_days 日曆日內）。
    最新的那個若已超過 fresh_days，更早的也一定超過 → 沒有訊號。"""
    m = eye["latest"][asof_idx]
    if m is None or _days_between(m["time"], asof_date or eye["times"][asof_idx]) > fresh_days:
        return None
    return m


def avg_vol20_lots(rows, asof_idx):
    last20 = [r["volume"] for r in rows[max(0, asof_idx - 19): asof_idx + 1] if r.get("volume") is not None]
    if len(last20) < 10:
        return None
    return math.floor(sum(last20) / len(last20) / 1000 + 0.5)


def min_vol(cfg):
    if cfg["MIN_VOL_LOTS"] is not None:
        return cfg["MIN_VOL_LOTS"]
    return 3000 if cfg["SELECT_MODE"] == "site_purple" else 0


def purple_pick(rows, eye, asof_idx, cfg):
    """回測用：這一天收盤後要不要把這檔列為進場標的；要的話回傳紫點資訊。"""
    if cfg["SELECT_MODE"] == "any_purple":
        m = eye["launch_at"].get(asof_idx)          # 今天剛亮的紫點
        if not m:
            return None
        vol = avg_vol20_lots(rows, asof_idx)
        if min_vol(cfg) > 0 and (vol or 0) < min_vol(cfg):
            return None
        return {"dot_date": m["time"], "kind": m["kind"], "age": 0, "vol20": vol,
                "fast": round(m["fast"], 1), "slow": round(m["slow"], 1)}
    return site_pick(rows, eye, asof_idx, cfg)


def site_pick(rows, eye, asof_idx, cfg, asof_date=None):
    """網站 🟣 全市場今日紫燈：這一天這檔會不會出現在名單。"""
    asof_date = asof_date or eye["times"][asof_idx]
    m = latest_signal_asof(eye, asof_idx, cfg["FRESH_DAYS"], asof_date)
    if not m or m["sig"] != "launch_confirm":
        return None
    age = _days_between(m["time"], asof_date)
    if age > cfg["SCAN_DAYS"]:
        return None
    vol = avg_vol20_lots(rows, asof_idx)
    if min_vol(cfg) > 0 and (vol or 0) < min_vol(cfg):
        return None
    return {"dot_date": m["time"], "kind": m["kind"], "age": age, "vol20": vol,
            "fast": round(m["fast"], 1), "slow": round(m["slow"], 1)}


# ════════════════════════════════════════════════════════════════════
# 三、資料
# ════════════════════════════════════════════════════════════════════
def _get(url, headers, timeout=30, tries=5):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and k < tries - 1:
                time.sleep(2 ** (k + 1)); continue
            raise
        except Exception:
            if k < tries - 1:
                time.sleep(2 ** (k + 1)); continue
            raise


def fetch_universe(cfg):
    """上市＋上櫃 4 碼代號。回傳 [(code, yahoo_ticker, name)]
    當天抓到的清單存成 whale_cache/universe_<日期>.json；全部來源都失敗時沿用最近一份。"""
    os.makedirs(cfg["CACHE_DIR"], exist_ok=True)
    fn = os.path.join(cfg["CACHE_DIR"], f"universe_{date.today().isoformat()}.json")
    if os.path.exists(fn):
        with open(fn, encoding="utf-8") as fh:
            return [tuple(x) for x in json.load(fh)]
    out = {}
    for k in range(3):   # FinMind 免 token 有每小時配額，超過回 402，等一下常常就好
        try:
            url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo"
            if cfg["FINMIND_TOKEN"]:
                url += "&token=" + cfg["FINMIND_TOKEN"]
            # FinMind 依 User-Agent 分配額（共用出口時 "Mozilla/5.0" 常被別人用光而回 402），用自己的 UA
            data = json.loads(_get(url, {"User-Agent": "whale-purple-dot/1.0"}, timeout=60, tries=2)).get("data", [])
            for x in data:
                c = str(x.get("stock_id", "")).strip()
                if x.get("type") in ("twse", "tpex") and re.fullmatch(r"\d{4}", c) and c not in out:
                    out[c] = (c, f"{c}.{'TW' if x['type'] == 'twse' else 'TWO'}", x.get("stock_name", ""))
            break
        except Exception as e:
            print(f"  FinMind 清單抓不到（{e}）", file=sys.stderr)
            if k < 2:
                time.sleep(20)
    has_otc = any(tk.endswith(".TWO") for _, tk, _ in out.values())
    if not out:
        print("  改用證交所 openapi", file=sys.stderr)
        try:
            tw = json.loads(_get("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", {"User-Agent": "Mozilla/5.0"}, 60, tries=2))
            for x in tw:
                c = str(x.get("Code", "")).strip()
                if re.fullmatch(r"\d{4}", c):
                    out[c] = (c, f"{c}.TW", x.get("Name", ""))
        except Exception as e:
            print(f"  證交所 openapi 抓不到（{e}）", file=sys.stderr)
    if not has_otc:
        print("  改用櫃買 openapi 補上櫃", file=sys.stderr)
        try:
            tp = json.loads(_get("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes", {"User-Agent": "Mozilla/5.0"}, 60, tries=2))
            for x in tp:
                c = str(x.get("SecuritiesCompanyCode", "")).strip()
                if re.fullmatch(r"\d{4}", c) and c not in out:
                    out[c] = (c, f"{c}.TWO", x.get("CompanyName", ""))
        except Exception as e:
            print(f"  櫃買 openapi 抓不到（{e}）── 母體會缺上櫃股", file=sys.stderr)
    if not out:
        old = sorted(f for f in os.listdir(cfg["CACHE_DIR"]) if re.fullmatch(r"universe_\d{4}-\d{2}-\d{2}\.json", f))
        if not old:
            raise RuntimeError("上市櫃清單全部來源都抓不到，也沒有舊的清單快取")
        print(f"  全部來源失敗，沿用 {old[-1]}", file=sys.stderr)
        with open(os.path.join(cfg["CACHE_DIR"], old[-1]), encoding="utf-8") as fh:
            return [tuple(x) for x in json.load(fh)]
    res = sorted(out.values())
    if any(tk.endswith(".TWO") for _, tk, _ in res):   # 缺上櫃的不完整清單不存，下次再試
        with open(fn, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False)
    return res


def codes_universe(codes, cfg):
    """--codes 指定的代號：查清單補名稱與上市／上櫃；查不到就先試 .TW 再試 .TWO。"""
    try:
        known = {c: (tk, name) for c, tk, name in fetch_universe(cfg)}
    except Exception:
        known = {}
    return [(c, [known[c][0]], known[c][1]) if c in known else (c, [f"{c}.TW", f"{c}.TWO"], "") for c in codes]


def fetch_daily(ticker, start, end, cfg):
    """與網站 fetchOHLCV 相同：還原權值 OHLC（四捨五入 2 位）＋原始成交量（股）。"""
    os.makedirs(cfg["CACHE_DIR"], exist_ok=True)
    p1 = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp())
    p2 = int(datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp()) + 86400
    fn = os.path.join(cfg["CACHE_DIR"], f"{ticker}_{start}_{end}.json")
    if os.path.exists(fn):
        try:
            with open(fn, encoding="utf-8") as fh:
                return json.load(fh)
        except ValueError:   # 舊版中斷時可能留下寫一半的檔 → 丟掉重抓
            os.remove(fn)
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(ticker)}"
           f"?period1={p1}&period2={p2}&interval=1d&events=history&includePrePost=false")
    try:
        j = json.loads(_get(url, YF_HEADERS))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    finally:
        time.sleep(cfg["SLEEP"])
    rows = rows_from_chart(j)
    if rows is None:
        return None
    tmp = f"{fn}.{os.getpid()}.tmp"   # 先寫暫存檔再改名：中途被中斷也不會留下壞掉的快取
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rows, fh)
    os.replace(tmp, fn)
    return rows


def rows_from_chart(j):
    """Yahoo v8 chart JSON → K 線（與網站 fetchOHLCV 逐行相同）。"""
    res = (j.get("chart") or {}).get("result") or []
    if not res:
        return None
    res = res[0]
    ts = res.get("timestamp") or []
    q = (res.get("indicators", {}).get("quote") or [{}])[0]
    ac = ((res.get("indicators", {}).get("adjclose") or [{}])[0]).get("adjclose") or []
    meta = res.get("meta") or {}
    rows = []
    for i, t in enumerate(ts):
        c = (q.get("close") or [None] * len(ts))[i]
        a = ac[i] if i < len(ac) else None
        ratio = a / c if (a and c) else 1
        def adj(key):
            v = (q.get(key) or [None] * len(ts))[i]
            return _js_round2(v * ratio) if v is not None else None
        rows.append({"time": datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d"),
                     "open": adj("open"), "high": adj("high"), "low": adj("low"), "close": adj("close"),
                     "volume": (q.get("volume") or [None] * len(ts))[i]})
    if rows and rows[-1]["close"] is None and isinstance(meta.get("regularMarketPrice"), (int, float)):
        p = _js_round2(meta["regularMarketPrice"])
        for k in ("close", "open", "high", "low"):
            if rows[-1][k] is None:
                rows[-1][k] = p
    return [r for r in rows if r["open"] and r["high"] and r["low"] and r["close"]]


def load_many(tickers, start, end, cfg):
    data = {}
    def one(item):
        code, cands, name = item
        for tk in cands:
            try:
                rows = fetch_daily(tk, start, end, cfg)
            except Exception as e:
                print(f"  {tk} 抓取失敗：{e}", file=sys.stderr)
                rows = None
            if rows:
                return code, tk, name, rows
        return code, None, name, None
    with ThreadPoolExecutor(max_workers=cfg["WORKERS"]) as ex:
        for n, (code, tk, name, rows) in enumerate(ex.map(one, tickers), 1):
            if rows:
                data[code] = {"ticker": tk, "name": name, "rows": rows}
            if n % 100 == 0 or n == len(tickers):
                print(f"  下載 {n}/{len(tickers)}，可用 {len(data)} 檔", file=sys.stderr)
    return data


# ════════════════════════════════════════════════════════════════════
# 四、回測
# ════════════════════════════════════════════════════════════════════
def simulate_stock(code, d, cfg, start, end):
    rows, eye = d["rows"], d["eye"]
    times = eye["times"]
    trades, picks = [], []
    hold_n = cfg["HOLD_DAYS"]
    holding = None            # 進行中的部位
    blocked_until = -1        # 停損後不再進場（REENTRY_AFTER_STOP=False 時）

    for i in range(len(times)):
        t = times[i]
        # 1) 先處理持有中的部位（用當天收盤判斷；開盤進場的話，進場當天收盤就要檢查）
        if holding and i >= holding["check_from"]:
            c = rows[i]["close"]
            holding["peak"] = max(holding["peak"], c)
            holding["trough"] = min(holding["trough"], rows[i]["low"])
            why = None
            if cfg["STOP_LOSS"] is not None and c <= holding["entry_px"] * (1 - cfg["STOP_LOSS"]):
                why = "停損"
            elif cfg["TRAIL_STOP"] is not None and c <= holding["peak"] * (1 - cfg["TRAIL_STOP"]):
                why = "移動停損"
            elif hold_n is not None and i - holding["entry_idx"] >= hold_n:
                why = "到期"
            if why:
                trades.append(_close_trade(code, d, holding, i, c, why, cfg))
                if why in ("停損", "移動停損") and not cfg["REENTRY_AFTER_STOP"]:
                    blocked_until = holding["entry_idx"] + (hold_n or 10 ** 9)
                holding = None
        if t < start or (end and t > end):
            continue
        # 2) 今天收盤後的名單
        p = purple_pick(rows, eye, i, cfg)
        if not p:
            continue
        picks.append({"date": t, "code": code, "name": d["name"], **p, "close": rows[i]["close"]})
        if holding or i <= blocked_until:
            continue
        if cfg["ENTRY"] == "close":
            ei, px, check_from = i, rows[i]["close"], i + 1
        else:
            if i + 1 >= len(rows):
                continue
            ei, px, check_from = i + 1, rows[i + 1]["open"], i + 1
        holding = {"entry_idx": ei, "entry_px": px, "check_from": check_from, "signal_idx": i,
                   "signal_date": t, "kind": p["kind"], "dot_date": p["dot_date"], "peak": px, "trough": px}
    if holding:
        last = len(rows) - 1
        if last >= holding["check_from"]:
            trades.append(_close_trade(code, d, holding, last, rows[last]["close"], "未平倉(以最後收盤計)", cfg))
    return trades, picks


def _close_trade(code, d, h, xi, px, why, cfg):
    rows = d["rows"]
    gross = (px / h["entry_px"] - 1) * 100
    net = gross - cfg["COST_ROUNDTRIP_PCT"]
    bench = None
    B = cfg.get("_bench")
    if B:   # 基準從「入選當天收盤」起算（隔天開盤進場時，這是最接近的可比起點）
        b0, b1 = B.get(rows[h["signal_idx"]]["time"]), B.get(rows[xi]["time"])
        if b0 and b1:
            bench = (b1 / b0 - 1) * 100
    jump = any(abs(rows[k]["close"] / rows[k - 1]["close"] - 1) * 100 > cfg["JUMP_PCT"]
               for k in range(max(1, h["entry_idx"]), xi + 1))
    return {
        "code": code, "name": d["name"], "kind": KIND_LABEL.get(h["kind"], h["kind"]),
        "dot_date": h["dot_date"], "signal_date": h["signal_date"],
        "entry_date": rows[h["entry_idx"]]["time"], "entry_px": h["entry_px"],
        "exit_date": rows[xi]["time"], "exit_px": px, "exit_reason": why,
        "days_held": xi - h["entry_idx"],
        "ret_pct": round(net, 2),
        "mae_pct": round((h["trough"] / h["entry_px"] - 1) * 100, 2),   # 持有期間最深浮虧（用盤中低）
        "bench_pct": None if bench is None else round(bench, 2),
        "excess_pct": None if bench is None else round(net - bench, 2),
        "jump_flag": int(jump),
    }


def summarize(trades, title):
    if not trades:
        print(f"\n{title}：沒有交易"); return
    r = [t["ret_pct"] for t in trades]
    wins = [x for x in r if x > 0]; loss = [x for x in r if x <= 0]
    ex = [t["excess_pct"] for t in trades if t["excess_pct"] is not None]
    pf = (sum(wins) / -sum(loss)) if loss and sum(loss) < 0 else float("inf")
    print(f"\n{title}")
    print(f"  筆數 {len(r)}　勝率 {len(wins) / len(r) * 100:.1f}%　平均 {statistics.mean(r):+.2f}%　中位 {statistics.median(r):+.2f}%")
    print(f"  平均獲利 {statistics.mean(wins) if wins else 0:+.2f}%　平均虧損 {statistics.mean(loss) if loss else 0:+.2f}%　獲利因子 {pf:.2f}")
    if ex:
        print(f"  相對加權指數同期：平均超額 {statistics.mean(ex):+.2f}pp　中位超額 {statistics.median(ex):+.2f}pp　贏指數比例 {sum(1 for x in ex if x > 0) / len(ex) * 100:.1f}%")
    mae = [t["mae_pct"] for t in trades]
    print(f"  持有期間最深浮虧：中位 {statistics.median(mae):+.1f}%　最差 {min(mae):+.1f}%　（≤ -20% 的有 {sum(1 for x in mae if x <= -20)} 筆）")


def run_backtest(cfg, codes=None):
    start = cfg["START"]
    end = cfg["END"] or date.today().isoformat()
    fetch_start = (date.fromisoformat(start) - timedelta(days=800)).isoformat()   # 指標暖機
    fetch_end = (date.fromisoformat(end) + timedelta(days=int((cfg["HOLD_DAYS"] or 0) * 1.6) + 5)).isoformat()
    fetch_end = min(fetch_end, date.today().isoformat())

    if codes:
        uni = codes_universe(codes, cfg)
    else:
        print("抓母體清單…", file=sys.stderr)
        uni = [(c, [tk], name) for c, tk, name in fetch_universe(cfg)]
    print(f"母體 {len(uni)} 檔，下載日線 {fetch_start} ~ {fetch_end}…", file=sys.stderr)
    data = load_many(uni, fetch_start, fetch_end, cfg)

    if cfg["BENCHMARK"]:
        b = fetch_daily(cfg["BENCHMARK"], fetch_start, fetch_end, cfg) or []
        cfg["_bench"] = {r["time"]: r["close"] for r in b}

    print("計算指標與回測…", file=sys.stderr)
    all_trades, all_picks = [], []
    for code, d in data.items():
        d["eye"] = whale_eye_v3(d["rows"], cfg["RULE_VERSION"])
        if not d["eye"]:
            continue
        tr, pk = simulate_stock(code, d, cfg, start, end)
        all_trades += tr; all_picks += pk

    os.makedirs(cfg["OUT_DIR"], exist_ok=True)
    tag = (f"{cfg['RULE_VERSION']}_{cfg['SELECT_MODE']}"
           + (f"_d{cfg['SCAN_DAYS']}" if cfg["SELECT_MODE"] == "site_purple" else "")
           + f"_v{min_vol(cfg)}_h{cfg['HOLD_DAYS']}_sl{cfg['STOP_LOSS']}_ts{cfg['TRAIL_STOP']}"
           + ("" if cfg["REENTRY_AFTER_STOP"] else "_noreentry")
           + ("" if cfg["ENTRY"] == "next_open" else "_eclose"))
    _write_csv(os.path.join(cfg["OUT_DIR"], f"trades_{tag}.csv"), sorted(all_trades, key=lambda x: (x["entry_date"], x["code"])))
    _write_csv(os.path.join(cfg["OUT_DIR"], f"picks_{tag}.csv"), sorted(all_picks, key=lambda x: (x["date"], x["code"])))

    print("\n" + "═" * 64)
    print(f"白鯨記紫點回測　規則 {cfg['RULE_VERSION']}　{start} ~ {end}")
    if cfg["SELECT_MODE"] == "site_purple":
        print(f"選股：網站紫燈模式 ── 紫點為最新訊號且 ≤{cfg['SCAN_DAYS']} 天　20日均量 ≥{min_vol(cfg)} 張")
    else:
        print(f"選股：每出現一顆新紫點就進場　20日均量 ≥{min_vol(cfg)} 張")
    print(f"進場：{'入選隔天開盤' if cfg['ENTRY'] == 'next_open' else '入選當天收盤'}　"
          f"出場：持有 {cfg['HOLD_DAYS'] or '不限'} 日　停損 {cfg['STOP_LOSS'] or '無'}　移動停損 {cfg['TRAIL_STOP'] or '無'}　"
          f"停損後再進場 {'可' if cfg['REENTRY_AFTER_STOP'] else '不可'}　來回成本 {cfg['COST_ROUNDTRIP_PCT']}%")
    print(f"可用股票 {len(data)} 檔　入選次數 {len(all_picks)}　交易 {len(all_trades)} 筆")
    closed = [t for t in all_trades if not t["exit_reason"].startswith("未平倉")]
    summarize(closed, "【已平倉交易】")
    clean = [t for t in closed if not t["jump_flag"]]
    summarize(clean, f"【已平倉、排除疑似分割／減資跳價 {len(closed) - len(clean)} 筆】")
    if not cfg["HOLD_DAYS"]:   # 不設持有上限時多數部位到資料結束都還沒出場，另外以最後收盤計
        summarize(all_trades, "【含未平倉（以最後收盤計）】")
    by_kind = {}
    for t in closed:
        by_kind.setdefault(t["kind"], []).append(t)
    print("\n【依場景】")
    for k in sorted(by_kind):
        r = [t["ret_pct"] for t in by_kind[k]]
        ex = [t["excess_pct"] for t in by_kind[k] if t["excess_pct"] is not None]
        print(f"  {k:<10} {len(r):>5} 筆　勝率 {sum(1 for x in r if x > 0) / len(r) * 100:5.1f}%　"
              f"中位 {statistics.median(r):+6.2f}%　中位超額 {statistics.median(ex) if ex else float('nan'):+6.2f}pp")
    by_year = {}
    for t in closed:
        by_year.setdefault(t["entry_date"][:4], []).append(t["ret_pct"])
    print("\n【依進場年份】")
    for y in sorted(by_year):
        r = by_year[y]
        print(f"  {y}　{len(r):>5} 筆　勝率 {sum(1 for x in r if x > 0) / len(r) * 100:5.1f}%　中位 {statistics.median(r):+6.2f}%")
    print(f"\n明細：{cfg['OUT_DIR']}/trades_{tag}.csv、picks_{tag}.csv")
    print("提醒：持有期互相重疊、母體不含已下市股票 ── 筆數不是獨立樣本數，結果偏樂觀。")


def run_scan(cfg, codes=None):
    today = date.today().isoformat()
    fetch_start = (date.today() - timedelta(days=540)).isoformat()     # 與網站相同：540 個日曆日
    if codes:
        uni = codes_universe(codes, cfg)
    else:
        uni = [(c, [tk], name) for c, tk, name in fetch_universe(cfg)]
    data = load_many(uni, fetch_start, today, cfg)
    out = []
    for code, d in data.items():
        eye = whale_eye_v3(d["rows"], cfg["RULE_VERSION"])
        if not eye:
            continue
        i = len(eye["times"]) - 1
        vol = avg_vol20_lots(d["rows"], i)
        if min_vol(cfg) > 0 and (vol or 0) < min_vol(cfg):
            continue
        # 距今天數一律以「掃描當天」計（與網站相同；資料最後一根若不是今天，照樣用今天算）
        if cfg["SELECT_MODE"] == "site_purple":
            m = latest_signal_asof(eye, i, cfg["FRESH_DAYS"], asof_date=today)
            dots = [m] if (m and m["sig"] == "launch_confirm" and _days_between(m["time"], today) <= cfg["SCAN_DAYS"]) else []
        else:
            dots = [m for m in eye["launch"] if _days_between(m["time"], today) <= cfg["SCAN_DAYS"]][-1:]
        for m in dots:
            out.append({"code": code, "name": d["name"], "kind": KIND_LABEL[m["kind"]], "dot_date": m["time"],
                        "age": _days_between(m["time"], today), "vol20": vol, "close": d["rows"][-1]["close"],
                        "fast": round(m["fast"], 1), "slow": round(m["slow"], 1)})
    out.sort(key=lambda x: (x["age"], x["kind"], -(x["vol20"] or 0)))
    os.makedirs(cfg["OUT_DIR"], exist_ok=True)
    fn = os.path.join(cfg["OUT_DIR"], f"scan_{today}_{cfg['SELECT_MODE']}.csv")
    _write_csv(fn, out)
    title = "🟣 網站紫燈模式（紫點是最新訊號）" if cfg["SELECT_MODE"] == "site_purple" else "🟣 有紫點的股票"
    print(f"\n{title}　{today}　規則 {cfg['RULE_VERSION']}　紫點 ≤{cfg['SCAN_DAYS']} 天　均量 ≥{min_vol(cfg)} 張　共 {len(out)} 檔")
    for p in out:
        print(f"  {p['code']} {p['name']:<8} {p['kind']:<10} 紫點 {p['dot_date']}（{p['age']} 天前）　收 {p['close']}　快 {p['fast']:+.1f}／慢 {p['slow']:+.1f}　均量 {p['vol20']} 張")
    print(f"\n已存 {fn}")


def _write_csv(fn, rows):
    with open(fn, "w", newline="", encoding="utf-8-sig") as fh:
        if not rows:
            fh.write(""); return
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description="白鯨記紫點 選股／回測")
    ap.add_argument("cmd", choices=["scan", "backtest"])
    ap.add_argument("--codes", help="只跑這些代號，逗號分隔，例 2330,3617,1815")
    ap.add_argument("--start"); ap.add_argument("--end")
    ap.add_argument("--rule", choices=["2026-07", "2026-08"], help="紫點規則版本")
    ap.add_argument("--mode", dest="select_mode", choices=["any_purple", "site_purple"], help="選股模式")
    ap.add_argument("--days", type=int, help="SCAN_DAYS：紫點距今 ≤ N 日曆日")
    ap.add_argument("--minvol", type=int, help="MIN_VOL_LOTS：20 日均量門檻（張）")
    ap.add_argument("--hold", type=int, help="HOLD_DAYS：最長持有交易日；0 = 不設上限")
    ap.add_argument("--stop", type=float, help="STOP_LOSS，例 0.15")
    ap.add_argument("--trail", type=float, help="TRAIL_STOP，例 0.2")
    ap.add_argument("--no-reentry", action="store_true", help="停損後不再進場")
    ap.add_argument("--entry", choices=["next_open", "close"])
    a = ap.parse_args()
    cfg = dict(CONFIG)
    for k, v in [("START", a.start), ("END", a.end), ("RULE_VERSION", a.rule), ("SELECT_MODE", a.select_mode), ("SCAN_DAYS", a.days),
                 ("MIN_VOL_LOTS", a.minvol), ("STOP_LOSS", a.stop), ("TRAIL_STOP", a.trail), ("ENTRY", a.entry)]:
        if v is not None:
            cfg[k] = v
    if a.hold is not None:
        cfg["HOLD_DAYS"] = None if a.hold == 0 else a.hold
    if a.no_reentry:
        cfg["REENTRY_AFTER_STOP"] = False
    codes = [c.strip() for c in a.codes.split(",")] if a.codes else None
    if a.cmd == "scan":
        run_scan(cfg, codes)
    else:
        run_backtest(cfg, codes)


if __name__ == "__main__":
    main()
