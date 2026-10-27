#!/usr/bin/env python3
"""KIWI F3 — 三腿加密貨幣均值回歸組合：回測 + 今日訊號檢查。

規則全文見 topics/business/2026-10-27-crypto-f3-mean-reversion-rulebook.md。

用法：
  python3 f3_backtest.py                       # 用 OKX 資料回測 4 年（預設）
  python3 f3_backtest.py --exchange binance    # 改用 Binance 資料（雲端被擋，Mac 可用）
  python3 f3_backtest.py --start 2023-10-27    # 改回測起點
  python3 f3_backtest.py --signals             # 只看最新一根已收盤 K 線有沒有進場訊號
  python3 f3_backtest.py --trades trades.csv   # 另存每筆交易明細

需求：Python 3.9+、numpy、pandas。只用交易所公開 K 線 API，不需要金鑰。
"""
import argparse
import json
import time
import urllib.request

import numpy as np
import pandas as pd

COST = 0.0007  # 每邊：手續費 0.05% + 滑價 0.02%

# 三條腿：資金比例、時間框架、進場訊號、停利、停損、最長持有根數
LEGS = [
    dict(name="BNB 日線", symbol="BNB", tf="1d", weight=0.30,
         signal="ema20_crossunder", tp=0.15, sl=0.10, max_bars=7),
    dict(name="TRX 4小時", symbol="TRX", tf="4h", weight=0.30,
         signal="rsi2_cross_above_10", tp=0.03, sl=0.07, max_bars=90),
    dict(name="BCH 4小時", symbol="BCH", tf="4h", weight=0.40,
         signal="rsi14_cross_above_35", tp=0.07, sl=0.07, max_bars=18),
]


# ---------- 資料 ----------
def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 kiwi-f3"})
    for i in range(5):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except Exception:
            if i == 4:
                raise
            time.sleep(2 ** i)


def fetch_okx(symbol, tf, start_ms):
    bar = {"1d": "1Dutc", "4h": "4H"}[tf]
    rows, after = {}, ""
    while True:
        url = (f"https://www.okx.com/api/v5/market/history-candles?instId={symbol}-USDT"
               f"&bar={bar}&limit=100" + (f"&after={after}" if after else ""))
        data = _get(url)["data"]
        if not data:
            break
        for r in data:
            if r[8] == "1":  # 只收已收盤的 K 線
                rows[int(r[0])] = [float(x) for x in r[1:5]]
        after = data[-1][0]
        if int(after) <= start_ms:
            break
        time.sleep(0.12)
    return rows


def fetch_binance(symbol, tf, start_ms):
    rows, cur = {}, start_ms
    now_ms = int(time.time() * 1000)
    while True:
        url = (f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={tf}"
               f"&startTime={cur}&limit=1000")
        data = _get(url)
        if not data:
            break
        for r in data:
            if r[6] < now_ms:  # close time 已過＝已收盤
                rows[int(r[0])] = [float(x) for x in r[1:5]]
        if len(data) < 1000:
            break
        cur = data[-1][0] + 1
        time.sleep(0.12)
    return rows


def load(exchange, symbol, tf, start_ms):
    fn = fetch_okx if exchange == "okx" else fetch_binance
    rows = fn(symbol, tf, start_ms)
    df = pd.DataFrame.from_dict(rows, orient="index", columns=["open", "high", "low", "close"]).sort_index()
    df.index = pd.to_datetime(df.index, unit="ms")
    return df[df.index >= pd.Timestamp(start_ms, unit="ms")]


# ---------- 指標 ----------
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(s, n):
    d = s.diff().fillna(0)
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d).clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, 1e-12))


def signals(leg, bars, daily):
    """回傳 (entry 布林序列, 指標 DataFrame)。所有判斷都只用該根 K 線收盤時已知的資訊。"""
    c = bars.close
    if leg["signal"] == "ema20_crossunder":
        e20 = ema(c, 20)
        raw = (c < e20) & (c.shift(1) >= e20.shift(1))
        ind = pd.DataFrame({"close": c, "EMA20": e20})
    else:
        n, th = (2, 10) if leg["signal"] == "rsi2_cross_above_10" else (14, 35)
        r = rsi(c, n)
        raw = (r > th) & (r.shift(1) <= th)
        ind = pd.DataFrame({"close": c, f"RSI({n})": r})
    d_ok = daily.close > ema(daily.close, 200)
    if leg["tf"] == "1d":
        gate = d_ok.reindex(bars.index).fillna(False)            # 當天收盤 > 當天 EMA200
    else:
        avail = pd.Series(d_ok.values, index=daily.index + pd.Timedelta(days=1))  # 日線收盤後才可用
        gate = avail.reindex(bars.index, method="ffill").fillna(False)            # ＝前一天的日線狀態
    ind["日線>EMA200" if leg["tf"] == "1d" else "前一日日線>EMA200"] = gate
    return (raw & gate).astype(bool), ind


# ---------- 模擬 ----------
def simulate(leg, bars, entry, start):
    o, h, l, c = (bars[k].to_numpy() for k in ("open", "high", "low", "close"))
    t = bars.index
    n, trades, busy_until = len(c), [], -1
    for e in np.nonzero(entry.to_numpy() & (t >= start))[0]:
        if e < busy_until or e >= n - 1:   # 持倉中不進場；出場那根收盤可立刻再進場
            continue
        ep = c[e]
        tp, sl = ep * (1 + leg["tp"]), ep * (1 - leg["sl"])
        exit_i, px, why = None, None, None
        for j in range(e + 1, min(n, e + 1 + leg["max_bars"])):
            if l[j] <= sl:                              # 同根同時碰到時保守當作停損
                exit_i, px, why = j, min(sl, o[j]), "停損"
                break
            if h[j] >= tp:
                exit_i, px, why = j, max(tp, o[j]), "停利"
                break
        if exit_i is None:
            exit_i = min(n - 1, e + leg["max_bars"])
            px, why = c[exit_i], "時間到" if e + leg["max_bars"] < n else "期末未平"
        ret = px / ep * (1 - COST) / (1 + COST) - 1
        step = pd.Timedelta(hours=4) if leg["tf"] == "4h" else pd.Timedelta(days=1)
        # 進場時間＝訊號 K 線收盤（UTC）；出場時間＝出場那根 K 線的收盤（停利／停損實際是在那根 K 線之內成交）
        trades.append(dict(leg=leg["name"], entry_time_utc=t[e] + step, entry=ep, exit_bar_close_utc=t[exit_i] + step,
                           exit=px, reason=why, ret=ret, e=e, x=exit_i))
        busy_until = exit_i
    return trades


def daily_equity(trades, bars, tf, days):
    c, n = bars.close.to_numpy(), len(bars)
    eq, cur, k, act = np.empty(n), 1.0, 0, None
    for b in range(n):
        if act is not None and b == act["x"]:
            cur, act = base * (1 + act["ret"]), None
        if act is None and k < len(trades) and trades[k]["e"] == b:
            act, base, k = trades[k], cur, k + 1
        eq[b] = base * c[b] / act["entry"] if act is not None and b > act["e"] else cur
    step = pd.Timedelta(hours=4) if tf == "4h" else pd.Timedelta(days=1)
    lab = (bars.index + step - pd.Timedelta(milliseconds=1)).normalize()
    s = pd.Series(eq, index=lab).groupby(level=0).last().reindex(days).ffill().bfill()
    return s / s.iloc[0]


def stats(e):
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    return (e.iloc[-1] ** (1 / yrs) - 1) * 100, ((e / e.cummax()) - 1).min() * 100, (e.iloc[-1] - 1) * 100


# ---------- 主程式 ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exchange", choices=["okx", "binance"], default="okx")
    ap.add_argument("--start", default="2022-10-27", help="回測起點（UTC 日期）")
    ap.add_argument("--signals", action="store_true", help="只檢查最新已收盤 K 線的進場訊號")
    ap.add_argument("--trades", help="把交易明細存成 CSV")
    a = ap.parse_args()

    start = pd.Timestamp(a.start)
    if a.signals:
        start = pd.Timestamp.now("UTC").tz_localize(None).normalize() - pd.Timedelta(days=10)
    daily_from = int((start - pd.Timedelta(days=400)).timestamp() * 1000)   # EMA200 暖機
    bars_from = int((start - pd.Timedelta(days=60)).timestamp() * 1000)

    data = {}
    for leg in LEGS:
        daily = load(a.exchange, leg["symbol"], "1d", daily_from)
        bars = daily[daily.index >= pd.Timestamp(bars_from, unit="ms")] if leg["tf"] == "1d" \
            else load(a.exchange, leg["symbol"], "4h", bars_from)
        data[leg["name"]] = (bars, daily)

    if a.signals:
        tz = "Asia/Taipei"
        print(f"資料來源：{a.exchange.upper()}　檢查時間：{pd.Timestamp.now(tz=tz):%Y-%m-%d %H:%M}（台北）\n")
        for leg in LEGS:
            bars, daily = data[leg["name"]]
            entry, ind = signals(leg, bars, daily)
            last = ind.iloc[-1]
            step = pd.Timedelta(hours=4) if leg["tf"] == "4h" else pd.Timedelta(days=1)
            closed = (ind.index[-1] + step).tz_localize("UTC").tz_convert(tz)
            vals = "　".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in last.items())
            print(f"【{leg['name']}】最新已收盤 K 線收盤於 {closed:%Y-%m-%d %H:%M}（台北）")
            print(f"   {vals}")
            if entry.iloc[-1]:
                px = last["close"]
                print(f"   ✅ 進場訊號成立 → 買入用該腿資金的 100%；停利 {px*(1+leg['tp']):.6g}　停損 {px*(1-leg['sl']):.6g}"
                      f"　最晚第 {leg['max_bars']} 根收盤出場\n")
            else:
                print("   — 沒有訊號（若已持倉，照原本的停利／停損／時間出場）\n")
        return

    days = pd.date_range(start, max(b.index[-1] for b, _ in data.values()).normalize(), freq="D")
    port, rows = 0, []
    print(f"資料來源：{a.exchange.upper()}　區間：{days[0]:%Y-%m-%d} → {days[-1]:%Y-%m-%d}　成本每邊 {COST*100:.2f}%\n")
    for leg in LEGS:
        bars, daily = data[leg["name"]]
        entry, _ = signals(leg, bars, daily)
        tr = simulate(leg, bars, entry, start)
        eq = daily_equity(tr, bars, leg["tf"], days)
        port = port + leg["weight"] * eq
        r = np.array([x["ret"] for x in tr])
        cg, dd, tot = stats(eq)
        print(f"{leg['name']:<8} 資金 {leg['weight']*100:.0f}%｜{len(r)} 筆　勝率 {(r > 0).mean()*100:.1f}%"
              f"　年化 {cg:.1f}%　最大回撤 {dd:.1f}%　總報酬 {tot:.1f}%")
        rows += tr
    cg, dd, tot = stats(port)
    print(f"\nF3 組合（固定比例、不再平衡）：年化 {cg:.1f}%　最大回撤 {dd:.1f}%　總報酬 {tot:.1f}%")
    for y in sorted(set(port.index.year)):
        s = port[port.index.year == y]
        prev = port[port.index < s.index[0]]
        base = prev.iloc[-1] if len(prev) else s.iloc[0]
        print(f"   {y}：{(s.iloc[-1]/base-1)*100:+.1f}%　年內最大回撤 {((s/s.cummax())-1).min()*100:.1f}%")
    if a.trades:
        pd.DataFrame(rows).drop(columns=["e", "x"]).to_csv(a.trades, index=False)
        print(f"\n交易明細已存到 {a.trades}")


if __name__ == "__main__":
    main()
