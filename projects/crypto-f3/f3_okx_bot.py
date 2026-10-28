#!/usr/bin/env python3
"""KIWI F3 / F3 2.0 執行機器人：紙上交易，或下單到 OKX 模擬盤。

每 4 小時在 K 線收盤後跑一次（cron／launchd 排程，見規則手冊 §11）。每次執行會：
  1. 抓 OKX 最新已收盤 K 線，算出各腿訊號（和 f3_backtest.py 同一套程式）
  2. 先處理出場：停利／停損是否已觸發、持有時間是否到期
  3. 再處理進場：最新一根已收盤 K 線有訊號、該腿空手 → 進場並掛停利停損
  4. 把狀態存到 ~/.kiwi-f3/<模式>/state.json，交易明細寫進 ledger.csv

模式：
  python3 f3_okx_bot.py --mode paper --v2                 # 紙上交易：不需要金鑰，按規則模擬成交
  python3 f3_okx_bot.py --mode okx-demo --check           # 只檢查模擬盤金鑰與帳戶設定，不下單
  python3 f3_okx_bot.py --mode okx-demo --v2              # 真的下單到 OKX 模擬盤
  python3 f3_okx_bot.py --mode okx-demo --v2 --smoke      # 小額下單測試：開倉→掛 OCO→撤單平倉（不改狀態）
  python3 f3_okx_bot.py --replay 2025-06-01 --v2          # 用歷史資料把紙上引擎從某天重播到今天（驗證用）
  python3 f3_okx_bot.py --mode paper --v2 --status        # 只印目前持倉與各腿資金

OKX 模擬盤金鑰放在環境變數（不要寫進任何檔案或 repo）：
  OKX_API_KEY、OKX_API_SECRET、OKX_API_PASSPHRASE
本程式只支援模擬盤：所有私有請求都帶 x-simulated-trading: 1，沒有實盤模式。

需求：Python 3.9+、numpy、pandas。
"""
import argparse
import base64
import csv
import hashlib
import hmac
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f3_backtest as bt  # noqa: E402

HOME = Path(os.environ.get("KIWI_F3_HOME", Path.home() / ".kiwi-f3"))
LEDGER_FIELDS = ["run_utc", "leg", "action", "side", "bar_close_utc", "price", "reason", "ret", "sleeve_equity", "note"]


def step_of(leg):
    return pd.Timedelta(hours=4) if leg["tf"] == "4h" else pd.Timedelta(days=1)


def build_legs(v2, capital):
    wkey = "weight_v2" if v2 else "weight"
    legs = [dict(g, w=g[wkey]) for g in bt.LEGS if g[wkey] > 0]
    for g in legs:
        g["capital"] = capital * g["w"]
    return legs


# ---------- 狀態與明細 ----------
class Store:
    def __init__(self, folder, legs, capital, version):
        self.dir = Path(folder)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "state.json"
        self.ledger = self.dir / "ledger.csv"
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            if self.state.get("version") != version:
                raise SystemExit(f"{self.path} 是 {self.state.get('version')} 的狀態，和這次的 {version} 不同。"
                                 f"請換一個 --home 資料夾，或確認後自行刪除舊狀態。")
        else:
            self.state = {"version": version, "capital": capital, "created_utc": datetime.now(timezone.utc).isoformat(),
                          "legs": {}}
        for g in legs:
            self.state["legs"].setdefault(g["name"], {"equity": g["capital"], "pos": None, "last_bar": None})

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2, default=str))
        tmp.replace(self.path)

    def log(self, row):
        new = not self.ledger.exists()
        with open(self.ledger, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
            if new:
                w.writeheader()
            w.writerow({k: row.get(k, "") for k in LEDGER_FIELDS})


def leg_return(leg, entry_px, exit_px, bars_held):
    if leg["side"] == "short":
        return (entry_px * (1 - bt.COST) - exit_px * (1 + bt.COST)) / entry_px \
            - bt.FUND_DAY * bars_held * (step_of(leg) / pd.Timedelta(days=1))
    return exit_px / entry_px * (1 - bt.COST) / (1 + bt.COST) - 1


def levels(leg, px):
    if leg["side"] == "short":
        return px * (1 - leg["tp"]), px * (1 + leg["sl"])
    return px * (1 + leg["tp"]), px * (1 - leg["sl"])


# ---------- 紙上交易 ----------
class PaperBroker:
    """完全照回測規則成交：進場＝訊號 K 線收盤價；之後每根 K 線先檢查停損、再檢查停利；第 N 根收盤時間出場。"""
    name = "paper"

    def enter(self, leg, st, bar_time, close):
        tp, sl = levels(leg, close)
        return {"side": leg["side"], "entry_bar": bar_time.isoformat(), "entry_px": close, "tp": tp, "sl": sl,
                "checked_until": bar_time.isoformat()}, ""

    def check_exit(self, leg, st, pos, bars):
        """bars＝已收盤 K 線（index＝開盤時間 UTC）。回傳 (出場 K 線開盤時間, 價格, 原因) 或 None。"""
        entry_bar = pd.Timestamp(pos["entry_bar"])
        after = bars[bars.index > pd.Timestamp(pos["checked_until"])]
        short = pos["side"] == "short"
        for t, row in after.iterrows():
            n = int(round((t - entry_bar) / step_of(leg)))
            if n > leg["max_bars"]:
                break
            if (row.high >= pos["sl"]) if short else (row.low <= pos["sl"]):
                return t, (max(pos["sl"], row.open) if short else min(pos["sl"], row.open)), "停損"
            if (row.low <= pos["tp"]) if short else (row.high >= pos["tp"]):
                return t, (min(pos["tp"], row.open) if short else max(pos["tp"], row.open)), "停利"
            if n == leg["max_bars"]:
                return t, row.close, "時間到"
            pos["checked_until"] = t.isoformat()
        return None

    def close_now(self, leg, pos, bars, why):
        """風控清倉：用最新一根已收盤 K 線的收盤價出場。"""
        return bars.index[-1], float(bars.close.iloc[-1]), why


# ---------- OKX 模擬盤 ----------
class OKXDemo:
    name = "okx-demo"
    base = "https://www.okx.com"

    def __init__(self):
        try:
            self.key = os.environ["OKX_API_KEY"]
            self.secret = os.environ["OKX_API_SECRET"].encode()
            self.passphrase = os.environ["OKX_API_PASSPHRASE"]
        except KeyError as e:
            raise SystemExit(f"缺少環境變數 {e}。請先設定 OKX 模擬盤的 OKX_API_KEY／OKX_API_SECRET／OKX_API_PASSPHRASE。")
        self._inst = {}
        self._cfg = None

    def req(self, method, path, params=None, body=None):
        qs = ("?" + urllib.parse.urlencode(params)) if params else ""
        body_s = json.dumps(body) if body is not None else ""
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
        sign = base64.b64encode(hmac.new(self.secret, (ts + method + path + qs + body_s).encode(), hashlib.sha256).digest()).decode()
        headers = {"OK-ACCESS-KEY": self.key, "OK-ACCESS-SIGN": sign, "OK-ACCESS-TIMESTAMP": ts,
                   "OK-ACCESS-PASSPHRASE": self.passphrase, "Content-Type": "application/json",
                   "x-simulated-trading": "1", "User-Agent": "kiwi-f3-bot"}
        r = urllib.request.Request(self.base + path + qs, data=body_s.encode() if body_s else None, headers=headers, method=method)
        try:
            with urllib.request.urlopen(r, timeout=20) as resp:
                out = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            out = json.loads(e.read() or b"{}")
        if out.get("code") != "0":
            detail = out.get("data") or ""
            raise RuntimeError(f"OKX {method} {path} 失敗：code={out.get('code')} msg={out.get('msg')} {detail}")
        return out["data"]

    # -- 帳戶與商品資訊 --
    def config(self):
        if self._cfg is None:
            self._cfg = self.req("GET", "/api/v5/account/config")[0]
        return self._cfg

    def long_short_mode(self):
        return self.config().get("posMode") == "long_short_mode"

    def spot_td(self):
        # 現貨模式／合約模式（acctLv 1、2）用 cash；跨幣種保證金／組合保證金（3、4）不接受 cash，要用 cross。
        # cross 下只買得起 USDT 餘額內的量、賣出量不超過持有量，所以不會借幣（2026-10-28 下單測試踩到）
        return "cross" if self.config().get("acctLv") in ("3", "4") else "cash"

    def spot_sell(self, inst_id, qty, lot):
        body = {"instId": inst_id, "tdMode": self.spot_td(), "side": "sell", "ordType": "market", "sz": self._fmt(qty, lot)}
        if body["tdMode"] == "cash":
            body["tgtCcy"] = "base_ccy"
        return self.req("POST", "/api/v5/trade/order", body=body)[0]

    def inst(self, leg):
        iid = f"{leg['symbol']}-USDT" + ("-SWAP" if leg["side"] == "short" else "")
        if iid not in self._inst:
            itype = "SWAP" if leg["side"] == "short" else "SPOT"
            self._inst[iid] = bt._get(f"{self.base}/api/v5/public/instruments?instType={itype}&instId={iid}")["data"][0]
        return self._inst[iid]

    @staticmethod
    def _fmt(x, step):
        step = float(step)
        dec = max(0, -int(math.floor(math.log10(step)))) if step < 1 else 0
        return f"{x:.{dec}f}"

    @staticmethod
    def _floor(x, step):
        step = float(step)
        return math.floor(x / step + 1e-9) * step

    def check(self, legs):
        cfg = self.config()
        print(f"帳戶模式 acctLv={cfg.get('acctLv')}（1＝現貨模式，2 以上才能交易永續合約）　持倉模式 posMode={cfg.get('posMode')}"
              f"　現貨下單模式 {self.spot_td()}　自動借幣 autoLoan={cfg.get('autoLoan')}")
        bal = self.req("GET", "/api/v5/account/balance", {"ccy": "USDT"})[0]
        usdt = next((d for d in bal.get("details", []) if d["ccy"] == "USDT"), {})
        print(f"模擬盤 USDT 可用餘額：{usdt.get('availBal', '0')}")
        for g in legs:
            i = self.inst(g)
            print(f"  {g['name']:<10} {i['instId']:<16} 最小下單 {i['minSz']}　數量級距 {i['lotSz']}　價格級距 {i['tickSz']}"
                  + (f"　每張 {i['ctVal']} {i['ctValCcy']}" if g["side"] == "short" else ""))
        if any(g["side"] == "short" for g in legs) and cfg.get("acctLv") == "1":
            print("⚠️ 目前是現貨模式，F3 2.0 的做空腿無法下單。請在 OKX 模擬盤的帳戶設定把帳戶模式改成「合約模式／單幣種保證金」。")

    def _order(self, inst_id, ord_id):
        o = {}
        for _ in range(15):
            o = self.req("GET", "/api/v5/trade/order", {"instId": inst_id, "ordId": ord_id})[0]
            filled = float(o.get("accFillSz") or 0)
            if o["state"] == "filled" or (o["state"] in ("canceled", "mmp_canceled") and filled > 0):
                return o   # 市價單剩餘部分被取消時，以實際成交的數量為準
            if o["state"] in ("canceled", "mmp_canceled"):
                raise RuntimeError(f"訂單 {ord_id} 被取消且沒有成交")
            time.sleep(1)
        raise RuntimeError(f"訂單 {ord_id} 沒有在時限內成交：state={o.get('state')}，請到 OKX 模擬盤手動檢查")

    def _fills_vwap(self, inst_id, since_ms, side):
        rows = self.req("GET", "/api/v5/trade/fills", {"instId": inst_id, "begin": str(since_ms)})
        rows = [r for r in rows if r["side"] == side]
        sz = sum(float(r["fillSz"]) for r in rows)
        return sum(float(r["fillPx"]) * float(r["fillSz"]) for r in rows) / sz if sz else None

    def enter(self, leg, st, bar_time, close):
        i = self.inst(leg)
        notional = st["equity"]
        if leg["side"] == "long":
            body = {"instId": i["instId"], "tdMode": self.spot_td(), "side": "buy", "ordType": "market",
                    "sz": self._fmt(notional, "0.01")}   # 市價買單的 sz 是 USDT 金額（cash 用 tgtCcy 指定；cross 預設就是）
            if body["tdMode"] == "cash":
                body["tgtCcy"] = "quote_ccy"
            o = self.req("POST", "/api/v5/trade/order", body=body)[0]
            f = self._order(i["instId"], o["ordId"])
            px = float(f["avgPx"])
            qty = float(f["accFillSz"]) + (float(f["fee"]) if f.get("feeCcy") == leg["symbol"] else 0.0)
            qty = self._floor(qty, i["lotSz"])
            tp, sl = levels(leg, px)
            a = self.req("POST", "/api/v5/trade/order-algo", body={
                "instId": i["instId"], "tdMode": self.spot_td(), "side": "sell", "ordType": "oco", "sz": self._fmt(qty, i["lotSz"]),
                "tpTriggerPx": self._fmt(tp, i["tickSz"]), "tpOrdPx": "-1",
                "slTriggerPx": self._fmt(sl, i["tickSz"]), "slOrdPx": "-1"})[0]
        else:
            ls = self.long_short_mode()
            lev = {"instId": i["instId"], "lever": "1", "mgnMode": "isolated"}
            if ls:
                lev["posSide"] = "short"
            self.req("POST", "/api/v5/account/set-leverage", body=lev)
            ct = float(i["ctVal"])
            qty = self._floor(notional / (close * ct), i["lotSz"])
            if qty < float(i["minSz"]):
                raise RuntimeError(f"{leg['name']} 資金 {notional:.2f} USDT 不到 1 個最小下單單位，略過")
            body = {"instId": i["instId"], "tdMode": "isolated", "side": "sell", "ordType": "market", "sz": self._fmt(qty, i["lotSz"])}
            if ls:
                body["posSide"] = "short"
            o = self.req("POST", "/api/v5/trade/order", body=body)[0]
            px = float(self._order(i["instId"], o["ordId"])["avgPx"])
            tp, sl = levels(leg, px)
            ab = {"instId": i["instId"], "tdMode": "isolated", "side": "buy", "ordType": "oco", "sz": self._fmt(qty, i["lotSz"]),
                  "tpTriggerPx": self._fmt(tp, i["tickSz"]), "tpOrdPx": "-1",
                  "slTriggerPx": self._fmt(sl, i["tickSz"]), "slOrdPx": "-1"}
            if ls:
                ab["posSide"] = "short"
            else:
                ab["reduceOnly"] = True
            a = self.req("POST", "/api/v5/trade/order-algo", body=ab)[0]
        pos = {"side": leg["side"], "entry_bar": bar_time.isoformat(), "entry_px": px, "tp": tp, "sl": sl,
               "inst": i["instId"], "qty": qty, "algoId": a["algoId"], "entry_ms": int(time.time() * 1000)}
        return pos, f"ordId={o['ordId']} algoId={a['algoId']} 訊號收盤 {close:.6g} 實際成交 {px:.6g}"

    def check_exit(self, leg, st, pos, bars):
        h = self.req("GET", "/api/v5/trade/orders-algo-history", {"ordType": "oco", "algoId": pos["algoId"]})
        state = h[0]["state"] if h else "live"
        if state == "effective":   # 停利或停損已觸發
            side = "buy" if pos["side"] == "short" else "sell"
            px = self._fills_vwap(pos["inst"], pos["entry_ms"], side) or float(h[0].get("actualPx") or 0) or None
            why = "停利" if h[0].get("actualSide") == "tp" else "停損" if h[0].get("actualSide") == "sl" else "停利/停損"
            if px is None:
                px = pos["tp"] if why == "停利" else pos["sl"]
            return bars.index[-1], px, why
        if state in ("canceled", "order_failed"):
            raise RuntimeError(f"{leg['name']} 的停利停損單狀態是 {state}，請到 OKX 模擬盤手動檢查這筆部位")
        held = int(round((bars.index[-1] - pd.Timestamp(pos["entry_bar"])) / step_of(leg)))
        if held >= leg["max_bars"]:
            return self.close_now(leg, pos, bars, "時間到")
        return None

    def close_now(self, leg, pos, bars, why):
        """撤掉停利停損單、市價平倉（時間到或風控清倉）。"""
        self.req("POST", "/api/v5/trade/cancel-algos", body=[{"algoId": pos["algoId"], "instId": pos["inst"]}])
        since = int(time.time() * 1000) - 5000
        if pos["side"] == "long":
            i = self.inst(leg)
            bal = self.req("GET", "/api/v5/account/balance", {"ccy": leg["symbol"]})[0]
            avail = float(next((d["availBal"] for d in bal.get("details", []) if d["ccy"] == leg["symbol"]), 0))
            qty = self._floor(min(pos["qty"], avail), i["lotSz"])
            o = self.spot_sell(pos["inst"], qty, i["lotSz"])
            px = float(self._order(pos["inst"], o["ordId"])["avgPx"])
        else:
            body = {"instId": pos["inst"], "mgnMode": "isolated"}
            if self.long_short_mode():
                body["posSide"] = "short"
            self.req("POST", "/api/v5/trade/close-position", body=body)
            time.sleep(2)
            px = self._fills_vwap(pos["inst"], since, "buy") or float(bars.close.iloc[-1])
        return bars.index[-1], px, why


    def smoke(self, legs, store, notional=50.0):
        """端到端下單測試：用 50 USDT 開一筆現貨多單和一筆永續空單、掛 OCO、確認後全部撤銷平倉。
        不碰狀態檔；交易會留在 OKX 模擬盤的訂單歷史和成交明細裡。"""
        held = {n for n, st in store.state["legs"].items() if st["pos"]}
        long_leg = next(g for g in legs if g["side"] == "long" and g["name"] not in held)
        short_leg = next((g for g in legs if g["side"] == "short" and g["name"] not in held), None)
        print(f"下單測試（每筆約 {notional:.0f} USDT，不影響策略資金與狀態）")
        for g in [long_leg] + ([short_leg] if short_leg else []):
            i = self.inst(g)
            px = float(bt._get(f"{self.base}/api/v5/market/ticker?instId={i['instId']}")["data"][0]["last"])
            if g["side"] == "short" and self._floor(notional / (px * float(i["ctVal"])), i["lotSz"]) < float(i["minSz"]):
                print(f"  {g['name']}：{notional:.0f} USDT 不到最小下單單位，改用最小單位")
            pos, note = self.enter(g, {"equity": notional if g["side"] == "long" else max(notional, px * float(i["ctVal"]) * float(i["minSz"]) * 1.01)},
                                   pd.Timestamp.now("UTC").tz_localize(None), px)
            print(f"  ✅ {g['name']} 進場成功：{note}　數量 {pos['qty']}　停利 {pos['tp']:.6g}　停損 {pos['sl']:.6g}")
            live = self.req("GET", "/api/v5/trade/orders-algo-pending", {"ordType": "oco", "instId": pos["inst"]})
            assert any(a["algoId"] == pos["algoId"] for a in live), "OCO 停利停損單沒有出現在掛單列表"
            print("  ✅ OCO 停利停損單已在掛單列表")
            self.req("POST", "/api/v5/trade/cancel-algos", body=[{"algoId": pos["algoId"], "instId": pos["inst"]}])
            if g["side"] == "long":
                o = self.spot_sell(pos["inst"], pos["qty"], i["lotSz"])
            else:   # 只平掉測試的數量，不動機器人可能持有的其他部位
                body = {"instId": pos["inst"], "tdMode": "isolated", "side": "buy", "ordType": "market",
                        "sz": self._fmt(pos["qty"], i["lotSz"])}
                if self.long_short_mode():
                    body["posSide"] = "short"
                else:
                    body["reduceOnly"] = True
                o = self.req("POST", "/api/v5/trade/order", body=body)[0]
            out = float(self._order(pos["inst"], o["ordId"])["avgPx"])
            print(f"  ✅ 已撤銷 OCO 並平倉，成交 {out:.6g}")
        print("下單測試完成：現貨、永續、OCO、平倉都正常。可以到 OKX 模擬盤的「訂單歷史／成交明細」看到這幾筆。")


# ---------- 每次執行 ----------
def fetch_all(legs, now=None):
    now = now or pd.Timestamp.now("UTC").tz_localize(None)
    d_from = int((now - pd.Timedelta(days=420)).timestamp() * 1000)
    b_from = int((now - pd.Timedelta(days=70)).timestamp() * 1000)
    data = {}
    for g in legs:
        daily = bt.load("okx", g["symbol"], "1d", d_from)
        bars = daily[daily.index >= pd.Timestamp(b_from, unit="ms")] if g["tf"] == "1d" else bt.load("okx", g["symbol"], "4h", b_from)
        entry, _ = bt.signals(g, bars, daily)
        data[g["name"]] = (bars, entry)
    return data


# ---------- 自動風控（規則手冊 §15.1、策略介紹「風險規劃」） ----------
# 單一個幣：連虧上限＝回測最長連虧＋2、回撤上限＝回測最大回撤×1.5（做空籃子 8 個幣合併判斷）
STREAK_LIMIT = {"BNB 日線 多": 6, "TRX 4小時 多": 6, "BCH 4小時 多": 4, "做空籃子": 15}
DD_LIMIT = {"BNB 日線 多": -26.0, "TRX 4小時 多": -38.0, "BCH 4小時 多": -21.0, "做空籃子": -31.0}
YELLOW_DD, YELLOW_OFF_DD, RED_DD = -7.5, -5.0, -15.0   # 組合回撤（%）：黃燈半倉、黃燈解除、紅燈清倉
LOW_VOL_M, LOW_VOL_DAYS = 2.0, 7                       # OKX 現貨 24h 成交額 < 200 萬 USDT 連續 7 天 → 停用


def group_of(leg):
    return "做空籃子" if leg["side"] == "short" else leg["name"]


def leg_flags(legs, store, min_n=10):
    """依已平倉交易判斷每組要不要停用（勝率明顯低於回測）或暫停（連虧、回撤超過上限）。回傳 {組: (動作, 說明)}。"""
    rows = [r for r in csv.DictReader(open(store.ledger)) if r["action"] == "EXIT" and r["ret"]] if store.ledger.exists() else []
    since = store.state.get("risk", {}).get("since_n", {})   # 解除風控後只看之後的交易
    out = {}
    for key in {group_of(g) for g in legs}:
        names = {g["name"] for g in legs if group_of(g) == key}
        bt_wr = next(g["bt_wr"] for g in legs if group_of(g) == key)
        rets = [float(r["ret"]) for r in rows if r["leg"] in names][since.get(key, 0):]
        n, wins = len(rets), sum(x > 0 for x in rets)
        streak = 0
        for x in rets:
            streak = streak + 1 if x <= 0 else 0
        eq = np.cumprod([1 + x for x in rets]) if rets else np.array([1.0])
        dd = float((eq / np.maximum.accumulate(eq) - 1).min() * 100)
        if n >= min_n and wilson_upper(wins, n) < bt_wr:
            out[key] = ("disabled", f"勝率 {wins / n * 100:.0f}%（{n} 筆）明顯低於回測 {bt_wr:.0f}%")
        elif streak > STREAK_LIMIT[key]:
            out[key] = ("paused", f"連虧 {streak} 筆，超過上限 {STREAK_LIMIT[key]}")
        elif dd < DD_LIMIT[key]:
            out[key] = ("paused", f"回撤 {dd:.1f}%，超過上限 {DD_LIMIT[key]:.0f}%")
    return out


def liquidity_check(legs, store, now):
    """每天一次：OKX 現貨 24h 成交額連續 7 天低於 200 萬 USDT 的幣停用。"""
    risk = store.state.setdefault("risk", {})
    today = f"{now:%Y-%m-%d}"
    if risk.get("vol_day") == today:
        return []
    risk["vol_day"] = today
    tk = {r["instId"]: r for r in bt._get("https://www.okx.com/api/v5/market/tickers?instType=SPOT")["data"]}
    msgs = []
    for g in legs:
        st = store.state["legs"][g["name"]]
        vol = float(tk.get(f"{g['symbol']}-USDT", {}).get("volCcy24h") or 0) / 1e6
        st["low_vol_days"] = st.get("low_vol_days", 0) + 1 if vol < LOW_VOL_M else 0
        if st["low_vol_days"] >= LOW_VOL_DAYS and not st.get("disabled"):
            st["disabled"] = f"OKX 現貨成交額連續 {st['low_vol_days']} 天低於 {LOW_VOL_M:.0f} 百萬 USDT（今天 {vol:.1f}）"
            msgs.append(f"【風控】{g['name']} 停用：{st['disabled']}")
    return msgs


def leg_mark(st, close):
    """該腿目前價值（含未實現）。"""
    pos = st["pos"]
    if not pos or close is None:
        return st["equity"]
    move = close / pos["entry_px"] - 1
    return st["equity"] * (1 + pos.get("frac", 1.0) * (-move if pos["side"] == "short" else move))


def run_cycle(legs, data, store, broker, run_utc, quiet=False, risk=True):
    say = (lambda m: None) if quiet else print
    fresh = {}
    # 1) 出場（每根 K 線只處理一次）
    for g in legs:
        st = store.state["legs"][g["name"]]
        bars, entry = data[g["name"]]
        if bars.empty:
            continue
        last_t = bars.index[-1]
        if st["last_bar"] and pd.Timestamp(st["last_bar"]) >= last_t:
            continue   # 這根 K 線處理過了
        fresh[g["name"]] = last_t
        if st["last_bar"]:
            missed = int(round((last_t - pd.Timestamp(st["last_bar"])) / step_of(g))) - 1
            if missed > 0:
                say(f"⚠️ {g['name']}：上次執行後漏了 {missed} 根 K 線（電腦睡眠或沒排程？），那些 K 線上的進場訊號已錯過")
        pos = st["pos"]
        if pos:
            ex = broker.check_exit(g, st, pos, bars)
            if ex:
                close_out(g, st, pos, ex, store, run_utc, say)

    # 2) 風控
    rk = store.state.setdefault("risk", {"mode": "normal"})
    rk.setdefault("mode", "normal")
    if risk:
        closes = {g["name"]: (float(data[g["name"]][0].close.iloc[-1]) if not data[g["name"]][0].empty else None) for g in legs}
        total = sum(leg_mark(store.state["legs"][g["name"]], closes[g["name"]]) for g in legs)
        rk["peak"] = max(rk.get("peak", store.state["capital"]), total)
        dd = (total / rk["peak"] - 1) * 100
        rk["dd"] = round(dd, 3)
        if rk["mode"] != "red" and dd <= RED_DD:
            rk["mode"], rk["since"] = "red", run_utc
            say(f"【風控】🛑 紅燈：組合從高點回撤 {dd:.1f}%（門檻 {RED_DD:.0f}%），全部平倉並停止新進場。要恢復請按 Run workflow 的「解除風控」")
            for g in legs:
                st = store.state["legs"][g["name"]]
                if st["pos"] and not data[g["name"]][0].empty:
                    try:
                        ex = broker.close_now(g, st["pos"], data[g["name"]][0], "風控清倉")
                        close_out(g, st, st["pos"], ex, store, run_utc, say)
                    except Exception as e:
                        store.log(dict(run_utc=run_utc, leg=g["name"], action="ERROR", side=g["side"], note=f"風控清倉失敗：{e}"[:300]))
                        say(f"❌ {g['name']} 風控清倉失敗：{e}")
        elif rk["mode"] == "normal" and dd <= YELLOW_DD:
            rk["mode"], rk["since"] = "yellow", run_utc
            say(f"【風控】⚠️ 黃燈：組合從高點回撤 {dd:.1f}%（門檻 {YELLOW_DD}%），之後新進場只用一半資金，回到 {YELLOW_OFF_DD:.0f}% 以內才恢復")
        elif rk["mode"] == "yellow" and dd > YELLOW_OFF_DD:
            rk["mode"], rk["since"] = "normal", run_utc
            say(f"【風控】✅ 黃燈解除：組合回撤回到 {dd:.1f}%，新進場恢復全額")
        for key, (act, why) in leg_flags(legs, store).items():
            for g in legs:
                st = store.state["legs"][g["name"]]
                if group_of(g) == key and not st.get(act):
                    st[act] = why
                    if g["name"] == next(x["name"] for x in legs if group_of(x) == key):
                        say(f"【風控】{key} {'停用' if act == 'disabled' else '暫停新進場'}：{why}。要恢復請按 Run workflow 的「解除風控」")
        try:
            for m in liquidity_check(legs, store, pd.Timestamp.now("UTC")):
                say(m)
        except Exception as e:   # 行情抓不到不影響交易
            say(f"（流動性檢查這一輪失敗：{e}）")

    # 3) 進場（只看最新一根已收盤 K 線）
    for g in legs:
        if g["name"] not in fresh:
            continue
        st = store.state["legs"][g["name"]]
        bars, entry = data[g["name"]]
        last_t = fresh[g["name"]]
        blocked = risk and (rk["mode"] == "red" or st.get("disabled") or st.get("paused"))
        if st["pos"] is None and bool(entry.iloc[-1]) and not blocked:
            close = float(bars.close.iloc[-1])
            frac = 0.5 if risk and rk["mode"] == "yellow" else 1.0
            try:
                pos, note = broker.enter(g, dict(st, equity=st["equity"] * frac), last_t, close)
            except Exception as e:  # 下單失敗：記錄後繼續處理其他腿
                store.log(dict(run_utc=run_utc, leg=g["name"], action="ERROR", side=g["side"], bar_close_utc=last_t + step_of(g),
                               note=str(e)[:300]))
                say(f"❌ {g['name']} 進場失敗：{e}")
                pos = None
            if pos:
                pos["frac"] = frac
                st["pos"] = pos
                half = "（黃燈：半倉）" if frac < 1 else ""
                store.log(dict(run_utc=run_utc, leg=g["name"], action="ENTER", side=g["side"], bar_close_utc=last_t + step_of(g),
                               price=f"{pos['entry_px']:.6g}", reason="訊號" + half, sleeve_equity=f"{st['equity']:.2f}",
                               note=f"停利 {pos['tp']:.6g} 停損 {pos['sl']:.6g} {note}"))
                say(f"【進場】{g['name']} {'做空' if g['side'] == 'short' else '做多'}{half} 價格 {pos['entry_px']:.6g}"
                    f"　停利 {pos['tp']:.6g}　停損 {pos['sl']:.6g}　最晚第 {g['max_bars']} 根收盤出場　{note}")
        elif st["pos"] is None and bool(entry.iloc[-1]) and blocked:
            why = "紅燈停止新進場" if rk["mode"] == "red" else st.get("disabled") or st.get("paused")
            say(f"【風控】{g['name']} 有進場訊號但沒有下單：{why}")
        st["last_bar"] = last_t.isoformat()
    store.save()


def close_out(g, st, pos, ex, store, run_utc, say):
    t_exit, px, why = ex
    held = int(round((t_exit - pd.Timestamp(pos["entry_bar"])) / step_of(g)))
    ret = leg_return(g, pos["entry_px"], px, held)
    st["equity"] *= (1 + ret * pos.get("frac", 1.0))
    st["pos"] = None
    store.log(dict(run_utc=run_utc, leg=g["name"], action="EXIT", side=g["side"], bar_close_utc=t_exit + step_of(g),
                   price=f"{px:.6g}", reason=why, ret=f"{ret:.5f}", sleeve_equity=f"{st['equity']:.2f}"))
    say(f"【出場】{g['name']} {why} 價格 {px:.6g} 報酬 {ret*100:+.2f}% → 該腿資金 {st['equity']:.2f}")


def wilson_upper(wins, n, z=1.2816):
    """勝率的單尾 90% 信賴上限（Wilson）。上限仍低於回測勝率＝統計上明顯變差。"""
    p = wins / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (center + half) * 100


def leg_health(legs, store, min_n=10):
    """用 ledger 裡已平倉的交易檢查每條腿是否失效。做多腿各自判斷，做空腿合併成一個籃子判斷。"""
    if not store.ledger.exists():
        return []
    rows = [r for r in csv.DictReader(open(store.ledger)) if r["action"] == "EXIT" and r["ret"]]
    groups = {}
    for g in legs:
        key = "做空籃子" if g["side"] == "short" else g["name"]
        groups.setdefault(key, {"bt_wr": g.get("bt_wr"), "names": set()})["names"].add(g["name"])
    out = []
    for key, info in groups.items():
        rets = [float(r["ret"]) for r in rows if r["leg"] in info["names"]]
        n, wins = len(rets), sum(x > 0 for x in rets)
        if n == 0:
            out.append(f"  {key}：還沒有平倉的交易")
            continue
        wr = wins / n * 100
        avg = float(np.mean(rets)) * 100
        line = f"  {key}：{n} 筆，勝率 {wr:.0f}%（回測 {info['bt_wr']:.0f}%），平均每筆 {avg:+.2f}%"
        if n < min_n:
            line += f"　樣本不足（滿 {min_n} 筆才判斷）"
        elif info["bt_wr"] and wilson_upper(wins, n) < info["bt_wr"]:
            line += "　🩺 勝率明顯低於回測，建議停用這條腿"
        else:
            line += "　正常"
        out.append(line)
    return out


def print_status(legs, store, data=None):
    total = 0.0
    print(f"\n狀態檔：{store.path}")
    for g in legs:
        st = store.state["legs"][g["name"]]
        eq, pos = st["equity"], st["pos"]
        close = float(data[g["name"]][0].close.iloc[-1]) if data and not data[g["name"]][0].empty else None
        mark = leg_mark(st, close)
        line = f"  {g['name']:<10} 資金 {eq:>10.2f}"
        if pos:
            half = "（半倉）" if pos.get("frac", 1.0) < 1 else ""
            line += f"　持倉中{half}（{pos['entry_bar'][:16]} 進場 {pos['entry_px']:.6g}，停利 {pos['tp']:.6g}／停損 {pos['sl']:.6g}）"
        else:
            line += "　空手"
        if st.get("disabled"):
            line += f"　⛔ 停用：{st['disabled']}"
        elif st.get("paused"):
            line += f"　⏸ 暫停：{st['paused']}"
        total += mark
        print(line)
    cap = store.state["capital"]
    rk = store.state.get("risk", {})
    mode = {"normal": "正常", "yellow": "⚠️ 黃燈（新進場半倉）", "red": "🛑 紅燈（已清倉、停止新進場）"}.get(rk.get("mode", "normal"))
    print(f"  合計（含未實現）{total:.2f}　起始 {cap:.2f}　{(total / cap - 1) * 100:+.2f}%")
    if "peak" in rk:
        print(f"  風控：{mode}　高點 {rk['peak']:.2f}　目前回撤 {rk.get('dd', 0):.2f}%（黃燈 {YELLOW_DD}%／紅燈 {RED_DD:.0f}%）")
    health = leg_health(legs, store)
    if health:
        print("失效檢查（模擬盤實際勝率 vs 回測；單尾 90% 信賴上限仍低於回測才判定失效）：")
        print("\n".join(health))
    print()


def resume(legs, store, target):
    """解除風控：target＝某個幣的名稱（例如「BCH 4小時 多」）、「做空籃子」，或 all（全部解除並把紅燈／黃燈歸零）。"""
    done = []
    rows = [r for r in csv.DictReader(open(store.ledger)) if r["action"] == "EXIT" and r["ret"]] if store.ledger.exists() else []
    since = store.state.setdefault("risk", {}).setdefault("since_n", {})
    for g in legs:
        st = store.state["legs"][g["name"]]
        if target in ("all", g["name"], group_of(g), g["symbol"]):
            key = group_of(g)
            since[key] = sum(1 for r in rows if r["leg"] in {x["name"] for x in legs if group_of(x) == key})
            for k in ("disabled", "paused"):
                if st.get(k):
                    done.append(f"{g['name']}：解除「{st[k]}」")
                    st[k] = None
            st["low_vol_days"] = 0
    if target == "all":
        rk = store.state.setdefault("risk", {})
        if rk.get("mode", "normal") != "normal":
            done.append(f"組合風控：{rk['mode']} → 正常，高點重設為目前資金")
        rk["mode"] = "normal"
        rk["peak"] = sum(store.state["legs"][g["name"]]["equity"] for g in legs)
        rk["dd"] = 0.0
    store.save()
    print("【風控】解除完成：" + ("；".join(done) if done else f"沒有符合「{target}」且需要解除的項目"))
    print("注意：之後如果條件再次觸發，機器人會再自動停用／暫停。")


def replay(legs, start, home, capital):
    """把紙上引擎從 start 開始，每 4 小時一步重播到今天。驗證引擎和回測是否一致。"""
    for f in ("state.json", "ledger.csv"):
        (Path(home) / f).unlink(missing_ok=True)
    store = Store(home, legs, capital, "replay")
    d_from = int((pd.Timestamp(start) - pd.Timedelta(days=420)).timestamp() * 1000)
    b_from = int((pd.Timestamp(start) - pd.Timedelta(days=70)).timestamp() * 1000)
    full = {}
    for g in legs:
        daily = bt.load("okx", g["symbol"], "1d", d_from)
        bars = daily[daily.index >= pd.Timestamp(b_from, unit="ms")] if g["tf"] == "1d" else bt.load("okx", g["symbol"], "4h", b_from)
        entry, _ = bt.signals(g, bars, daily)
        entry &= bars.index >= pd.Timestamp(start)
        full[g["name"]] = (bars, entry)
    broker = PaperBroker()
    end = max(b.index[-1] for b, _ in full.values()) + pd.Timedelta(days=1)
    for now in pd.date_range(pd.Timestamp(start), end, freq="4h"):
        sl = {}
        for g in legs:
            bars, entry = full[g["name"]]
            m = bars.index + step_of(g) <= now
            sl[g["name"]] = (bars[m], entry[m])
        run_cycle(legs, sl, store, broker, now.isoformat(), quiet=True, risk=False)   # 驗證引擎和回測一致，不套風控
    return store


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["paper", "okx-demo"], default="paper")
    ap.add_argument("--v2", action="store_true", help="F3 2.0（含熊市做空籃子）")
    ap.add_argument("--capital", type=float, default=10000.0, help="第一次執行時的總資金（USDT），之後以狀態檔為準")
    ap.add_argument("--home", help="狀態與明細的資料夾（預設 ~/.kiwi-f3/<模式>-<版本>）")
    ap.add_argument("--check", action="store_true", help="只檢查 OKX 模擬盤金鑰與帳戶設定")
    ap.add_argument("--status", action="store_true", help="只印目前持倉與資金")
    ap.add_argument("--smoke", action="store_true", help="OKX 模擬盤端到端下單測試（小額開倉→掛 OCO→撤單平倉，不改狀態）")
    ap.add_argument("--replay", metavar="YYYY-MM-DD", help="用歷史資料重播紙上引擎（驗證用）")
    ap.add_argument("--resume", metavar="目標", help="解除風控：某個幣的名稱、做空籃子，或 all（連組合紅燈／黃燈一起解除）")
    a = ap.parse_args()

    version = "F3-2.0" if a.v2 else "F3"
    legs = build_legs(a.v2, a.capital)

    if a.replay:
        home = Path(a.home or HOME / f"replay-{version}")
        store = replay(legs, a.replay, home, a.capital)
        print(f"重播完成（{a.replay} → 今天），明細：{store.ledger}")
        print_status(legs, store)
        return

    home = Path(a.home or HOME / f"{a.mode}-{version}")
    if a.mode == "okx-demo":
        broker = OKXDemo()
        if a.check:
            broker.check(legs)
            return
    else:
        broker = PaperBroker()
    store = Store(home, legs, a.capital, version)
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if a.smoke:
        if a.mode != "okx-demo":
            raise SystemExit("--smoke 只能搭配 --mode okx-demo")
        broker.smoke(legs, store)
        return
    if a.resume:
        resume(legs, store, a.resume.strip())
        return
    if a.status:
        print_status(legs, store, fetch_all(legs))
        return
    print(f"{version}｜模式 {a.mode}｜執行時間 {pd.Timestamp.now(tz='Asia/Taipei'):%Y-%m-%d %H:%M}（台北）")
    data = fetch_all(legs)
    run_cycle(legs, data, store, broker, run_utc)
    print_status(legs, store, data)


if __name__ == "__main__":
    main()
