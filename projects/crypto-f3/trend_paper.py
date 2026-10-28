#!/usr/bin/env python3
"""BTC＋ETH 趨勢跟隨：紙上交易（不下單），同時跑三個波動目標 40%／45%／50%，跑一段時間再決定用哪個。

規則和回測一模一樣（trend_backtest.py 的 targets()／step()）；差別只在成交價：
  - 每天 UTC 00:00 日線收盤後第一次執行時調整部位，用「執行當下的 OKX 現貨價」成交（記下和收盤價的差距＝延遲成本）。
  - 每次執行（每小時）用最新價格記一筆淨值，給監控台畫圖。
  - 漏跑幾天也只處理最新一根日線：過去的價格已經買不到了。

狀態放在 <home>（GitHub 上是 f3-bot-state 分支的 trend-paper/）：
  state.json    三個版本的持幣數量、現金、已處理到哪一天
  ledger.csv    每次調整的明細
  equity.csv    每次執行的三個淨值
  dash/*.json   監控台資料：trend_summary、trend_equity、trend_signals、trend_trades

用法：python3 projects/crypto-f3/trend_paper.py --home <資料夾> [--capital 83000]
      python3 projects/crypto-f3/trend_paper.py --home <資料夾> --replay 2025-06-01   # 用歷史收盤價重播，驗證和回測一致
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f3_backtest as bt  # noqa: E402
import trend_backtest as tb  # noqa: E402

VARIANTS = (0.40, 0.45, 0.50)
OKX = "https://www.okx.com"


def key(tg):
    return f"{int(round(tg * 100))}"


def now_utc():
    return datetime.now(timezone.utc)


def daily_closes(days=420):
    start = int((pd.Timestamp.now("UTC").tz_localize(None) - pd.Timedelta(days=days)).timestamp() * 1000)
    out = {}
    for c in tb.COINS:
        rows = bt.fetch_okx(c, "1d", start)
        out[c] = pd.Series({pd.Timestamp(k, unit="ms"): v[3] for k, v in rows.items()}).sort_index()
    idx = pd.date_range(min(s.index[0] for s in out.values()), max(s.index[-1] for s in out.values()), freq="D")
    return pd.DataFrame({c: s.reindex(idx).ffill() for c, s in out.items()})


def last_prices():
    return {c: float(bt._get(f"{OKX}/api/v5/market/ticker?instId={c}-USDT")["data"][0]["last"]) for c in tb.COINS}


class Store:
    def __init__(self, home, capital):
        self.home = Path(home)
        self.home.mkdir(parents=True, exist_ok=True)
        self.path = self.home / "state.json"
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
        else:
            self.state = dict(version="trend-1", capital=capital, created_utc=now_utc().isoformat(),
                              variants={key(tg): dict(target=tg, units={c: 0.0 for c in tb.COINS}, cash=capital)
                                        for tg in VARIANTS}, last_day=None)

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2))
        tmp.replace(self.path)

    def log(self, row):
        p = self.home / "ledger.csv"
        new = not p.exists()
        with open(p, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)


def value(v, px):
    return v["cash"] + sum(v["units"][c] * px[c] for c in tb.COINS)


def rebalance(store, P, day, fill, when, say):
    """處理一根新日線：算目標部位，用 fill 價格調整。"""
    for k, v in store.state["variants"].items():
        T, _, _ = tb.targets(P, v["target"])
        tgt = T.loc[day].to_dict()
        before = {c: v["units"][c] * fill[c] / value(v, fill) for c in tb.COINS}
        units, cash, turn = tb.step(v["units"], v["cash"], fill, tgt)
        if turn > 0:
            eq = cash + sum(units[c] * fill[c] for c in tb.COINS)
            for c in tb.COINS:
                d = units[c] - v["units"][c]
                if abs(d) * fill[c] < 1:
                    continue
                store.log(dict(time=when, variant=k, day=f"{day:%Y-%m-%d}", coin=c, side="買" if d > 0 else "賣",
                               qty=f"{abs(d):.6f}", price=f"{fill[c]:.2f}", close=f"{P[c].loc[day]:.2f}",
                               usdt=f"{abs(d) * fill[c]:.2f}", weight_before=f"{before[c]:.4f}",
                               weight_after=f"{units[c] * fill[c] / eq:.4f}", target=f"{tgt[c]:.4f}"))
            say(f"【趨勢紙上】波動目標 {k}%：" + "、".join(
                f"{c} {before[c]:.0%}→{units[c] * fill[c] / eq:.0%}" for c in tb.COINS) + f"（淨值 {eq:,.0f}）")
        v["units"], v["cash"] = units, cash
    store.state["last_day"] = f"{day:%Y-%m-%d}"


def write_dash(store, P, px, when):
    home, st = store.home, store.state
    out = home / "dash"
    out.mkdir(exist_ok=True)
    cap = st["capital"]
    # 淨值歷史
    p = home / "equity.csv"
    new = not p.exists()
    with open(p, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time_utc"] + [f"eq{k}" for k in st["variants"]])
        w.writerow([when] + [f"{value(v, px):.2f}" for v in st["variants"].values()])
    hist = pd.read_csv(p, parse_dates=["time_utc"])
    cut = hist.time_utc.max() - pd.Timedelta(days=30)        # 30 天內逐筆，更早每天一筆
    old = hist[hist.time_utc < cut]
    hist = pd.concat([old.groupby(old.time_utc.dt.floor("D")).tail(1), hist[hist.time_utc >= cut]])
    eq_rows = []
    for k in st["variants"]:
        s = hist[f"eq{k}"]
        dd = (s / s.cummax() - 1) * 100
        for t, e, d in zip(hist.time_utc, s, dd):
            eq_rows.append(dict(time=f"{t:%Y-%m-%dT%H:%M}", variant=f"波動目標 {k}%", equity=round(e, 2),
                                ret_pct=round((e / cap - 1) * 100, 3), dd_pct=round(d, 3)))
    # 總覽
    led = list(csv.DictReader(open(home / "ledger.csv"))) if (home / "ledger.csv").exists() else []
    T_all = {k: tb.targets(P, v["target"]) for k, v in st["variants"].items()}
    summary = []
    for k, v in st["variants"].items():
        e = value(v, px)
        s = pd.read_csv(p)[f"eq{k}"]
        T, S, vol = T_all[k]
        mine = [r for r in led if r["variant"] == k]
        summary.append(dict(variant=f"波動目標 {k}%", target_pct=int(k), equity=round(e, 2), ret_pct=round((e / cap - 1) * 100, 3),
                            max_dd_pct=round(float((s / s.cummax() - 1).min() * 100), 3),
                            btc_pct=round(v["units"]["BTC"] * px["BTC"] / e * 100, 1),
                            eth_pct=round(v["units"]["ETH"] * px["ETH"] / e * 100, 1),
                            cash_pct=round(v["cash"] / e * 100, 1),
                            btc_target_pct=round(T["BTC"].iloc[-1] * 100, 1), eth_target_pct=round(T["ETH"].iloc[-1] * 100, 1),
                            rebalances=len({r["day"] for r in mine}), last_rebalance=mine[-1]["day"] if mine else "",
                            last_day=st["last_day"], started=st["created_utc"][:10], updated=when))
    # 訊號：每個幣 7 個訊號＋波動，三個版本的目標部位
    sig = []
    for c in tb.COINS:
        cl = P[c]
        hi, lo = cl.rolling(20).max().shift(1), cl.rolling(10).min().shift(1)
        don = pd.Series(np.nan, index=cl.index)
        don[cl > hi], don[cl < lo] = 1, 0
        last = cl.iloc[-1]
        row = dict(coin=c, close=round(float(last), 2), score=round(float(T_all["40"][1][c].iloc[-1]), 2),
                   vol60_pct=round(float(T_all["40"][2][c].iloc[-1] * 100), 1),
                   ma100=bool(last > cl.rolling(100).mean().iloc[-1]), ma150=bool(last > cl.rolling(150).mean().iloc[-1]),
                   ma200=bool(last > cl.rolling(200).mean().iloc[-1]), mom60=bool(last > cl.iloc[-61]),
                   mom90=bool(last > cl.iloc[-91]), mom180=bool(last > cl.iloc[-181]), donchian=bool(don.ffill().iloc[-1] == 1))
        for k in st["variants"]:
            row[f"target{k}_pct"] = round(float(T_all[k][0][c].iloc[-1] * 100), 1)
        sig.append(row)
    trades = [dict(id=i, time=r["time"][:16], variant=f"波動目標 {r['variant']}%", coin=r["coin"], side=r["side"],
                   price=float(r["price"]), usdt=float(r["usdt"]),
                   slip_pct=round((float(r["price"]) / float(r["close"]) - 1) * 100 * (1 if r["side"] == "買" else -1), 3),
                   weight_after_pct=round(float(r["weight_after"]) * 100, 1))
              for i, r in list(enumerate(led))[-60:]][::-1]
    if not trades:   # 監控台讀不了空檔案
        trades = [dict(id=-1, time="", variant="（還沒有調整）", coin="", side="", price=0, usdt=0, slip_pct=0, weight_after_pct=0)]
    for name, rows in (("trend_summary", summary), ("trend_equity", eq_rows), ("trend_signals", sig), ("trend_trades", trades)):
        (out / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, allow_nan=False))


def run(home, capital):
    store = Store(home, capital)
    when = now_utc().isoformat(timespec="minutes")
    P = daily_closes()
    day = P.index[-1]                       # 最新一根已收盤日線
    px = last_prices()
    msgs = []
    if store.state["last_day"] != f"{day:%Y-%m-%d}":
        rebalance(store, P, day, px, when, msgs.append)
    store.save()
    write_dash(store, P, px, when)
    print(f"趨勢跟隨紙上交易（日線 {day:%Y-%m-%d}）：" + "；".join(
        f"{k}% {value(v, px):,.0f}" for k, v in store.state["variants"].items()))
    for m in msgs:
        print(m)


def replay(home, capital, start):
    """用 OKX 歷史收盤價重播：結果要和 trend_backtest.simulate() 完全一樣。"""
    store = Store(home, capital)
    P = tb.prices(source="okx")
    for day in P.loc[start:].index:
        rebalance(store, P.loc[:day], day, P.loc[day].to_dict(), f"{day:%Y-%m-%d}T00:05", lambda m: None)
    px = P.iloc[-1].to_dict()
    for k, v in store.state["variants"].items():
        T, _, _ = tb.targets(P, v["target"])
        e, _, _ = tb.simulate(P, T, start)
        print(f"{k}%：重播 {value(v, px) / capital:.6f}　回測 {e.iloc[-1]:.6f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--home", required=True)
    ap.add_argument("--capital", type=float, default=83000.0, help="每個版本的起始紙上資金（第一次建立狀態時用）")
    ap.add_argument("--replay", help="從這一天起用歷史收盤價重播（驗證用，請給一個空資料夾）")
    a = ap.parse_args()
    if a.replay:
        replay(a.home, a.capital, a.replay)
    else:
        run(a.home, a.capital)


if __name__ == "__main__":
    main()
