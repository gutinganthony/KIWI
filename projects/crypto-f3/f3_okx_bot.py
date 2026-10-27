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
        print(f"帳戶模式 acctLv={cfg.get('acctLv')}（1＝現貨模式，2 以上才能交易永續合約）　持倉模式 posMode={cfg.get('posMode')}")
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
            o = self.req("POST", "/api/v5/trade/order", body={
                "instId": i["instId"], "tdMode": "cash", "side": "buy", "ordType": "market",
                "sz": self._fmt(notional, "0.01"), "tgtCcy": "quote_ccy"})[0]
            f = self._order(i["instId"], o["ordId"])
            px = float(f["avgPx"])
            qty = float(f["accFillSz"]) + (float(f["fee"]) if f.get("feeCcy") == leg["symbol"] else 0.0)
            qty = self._floor(qty, i["lotSz"])
            tp, sl = levels(leg, px)
            a = self.req("POST", "/api/v5/trade/order-algo", body={
                "instId": i["instId"], "tdMode": "cash", "side": "sell", "ordType": "oco", "sz": self._fmt(qty, i["lotSz"]),
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
            self.req("POST", "/api/v5/trade/cancel-algos", body=[{"algoId": pos["algoId"], "instId": pos["inst"]}])
            since = int(time.time() * 1000) - 5000
            if pos["side"] == "long":
                i = self.inst(leg)
                bal = self.req("GET", "/api/v5/account/balance", {"ccy": leg["symbol"]})[0]
                avail = float(next((d["availBal"] for d in bal.get("details", []) if d["ccy"] == leg["symbol"]), 0))
                qty = self._floor(min(pos["qty"], avail), i["lotSz"])
                o = self.req("POST", "/api/v5/trade/order", body={
                    "instId": pos["inst"], "tdMode": "cash", "side": "sell", "ordType": "market",
                    "sz": self._fmt(qty, i["lotSz"]), "tgtCcy": "base_ccy"})[0]
                px = float(self._order(pos["inst"], o["ordId"])["avgPx"])
            else:
                body = {"instId": pos["inst"], "mgnMode": "isolated"}
                if self.long_short_mode():
                    body["posSide"] = "short"
                self.req("POST", "/api/v5/trade/close-position", body=body)
                time.sleep(2)
                px = self._fills_vwap(pos["inst"], since, "buy") or float(bars.close.iloc[-1])
            return bars.index[-1], px, "時間到"
        return None


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


def run_cycle(legs, data, store, broker, run_utc, quiet=False):
    for g in legs:
        st = store.state["legs"][g["name"]]
        bars, entry = data[g["name"]]
        if bars.empty:
            continue
        last_t = bars.index[-1]
        if st["last_bar"] and pd.Timestamp(st["last_bar"]) >= last_t:
            continue   # 這根 K 線處理過了
        if st["last_bar"]:
            missed = int(round((last_t - pd.Timestamp(st["last_bar"])) / step_of(g))) - 1
            if missed > 0 and not quiet:
                print(f"⚠️ {g['name']}：上次執行後漏了 {missed} 根 K 線（電腦睡眠或沒排程？），那些 K 線上的進場訊號已錯過")
        # 1) 出場
        pos = st["pos"]
        if pos:
            ex = broker.check_exit(g, st, pos, bars)
            if ex:
                t_exit, px, why = ex
                held = int(round((t_exit - pd.Timestamp(pos["entry_bar"])) / step_of(g)))
                ret = leg_return(g, pos["entry_px"], px, held)
                st["equity"] *= (1 + ret)
                st["pos"] = None
                store.log(dict(run_utc=run_utc, leg=g["name"], action="EXIT", side=g["side"], bar_close_utc=t_exit + step_of(g),
                               price=f"{px:.6g}", reason=why, ret=f"{ret:.5f}", sleeve_equity=f"{st['equity']:.2f}"))
                if not quiet:
                    print(f"【出場】{g['name']} {why} 價格 {px:.6g} 報酬 {ret*100:+.2f}% → 該腿資金 {st['equity']:.2f}")
        # 2) 進場（只看最新一根已收盤 K 線）
        if st["pos"] is None and bool(entry.iloc[-1]):
            close = float(bars.close.iloc[-1])
            try:
                pos, note = broker.enter(g, st, last_t, close)
            except Exception as e:  # 下單失敗：記錄後繼續處理其他腿
                store.log(dict(run_utc=run_utc, leg=g["name"], action="ERROR", side=g["side"], bar_close_utc=last_t + step_of(g),
                               note=str(e)[:300]))
                print(f"❌ {g['name']} 進場失敗：{e}")
                pos = None
            if pos:
                st["pos"] = pos
                store.log(dict(run_utc=run_utc, leg=g["name"], action="ENTER", side=g["side"], bar_close_utc=last_t + step_of(g),
                               price=f"{pos['entry_px']:.6g}", reason="訊號", sleeve_equity=f"{st['equity']:.2f}",
                               note=f"停利 {pos['tp']:.6g} 停損 {pos['sl']:.6g} {note}"))
                if not quiet:
                    print(f"【進場】{g['name']} {'做空' if g['side'] == 'short' else '做多'} 價格 {pos['entry_px']:.6g}"
                          f"　停利 {pos['tp']:.6g}　停損 {pos['sl']:.6g}　最晚第 {g['max_bars']} 根收盤出場　{note}")
        st["last_bar"] = last_t.isoformat()
    store.save()


def print_status(legs, store, data=None):
    total = 0.0
    print(f"\n狀態檔：{store.path}")
    for g in legs:
        st = store.state["legs"][g["name"]]
        eq, pos = st["equity"], st["pos"]
        mark = eq
        line = f"  {g['name']:<10} 資金 {eq:>10.2f}"
        if pos:
            if data:
                c = float(data[g["name"]][0].close.iloc[-1])
                mark = eq * ((2 - c / pos["entry_px"]) if pos["side"] == "short" else c / pos["entry_px"])
            line += f"　持倉中（{pos['entry_bar'][:16]} 進場 {pos['entry_px']:.6g}，停利 {pos['tp']:.6g}／停損 {pos['sl']:.6g}）"
        else:
            line += "　空手"
        total += mark
        print(line)
    cap = store.state["capital"]
    print(f"  合計（含未實現）{total:.2f}　起始 {cap:.2f}　{(total / cap - 1) * 100:+.2f}%\n")


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
        run_cycle(legs, sl, store, broker, now.isoformat(), quiet=True)
    return store


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["paper", "okx-demo"], default="paper")
    ap.add_argument("--v2", action="store_true", help="F3 2.0（含熊市做空籃子）")
    ap.add_argument("--capital", type=float, default=10000.0, help="第一次執行時的總資金（USDT），之後以狀態檔為準")
    ap.add_argument("--home", help="狀態與明細的資料夾（預設 ~/.kiwi-f3/<模式>-<版本>）")
    ap.add_argument("--check", action="store_true", help="只檢查 OKX 模擬盤金鑰與帳戶設定")
    ap.add_argument("--status", action="store_true", help="只印目前持倉與資金")
    ap.add_argument("--replay", metavar="YYYY-MM-DD", help="用歷史資料重播紙上引擎（驗證用）")
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
    if a.status:
        print_status(legs, store, fetch_all(legs))
        return
    print(f"{version}｜模式 {a.mode}｜執行時間 {pd.Timestamp.now(tz='Asia/Taipei'):%Y-%m-%d %H:%M}（台北）")
    data = fetch_all(legs)
    run_cycle(legs, data, store, broker, run_utc)
    print_status(legs, store, data)


if __name__ == "__main__":
    main()
