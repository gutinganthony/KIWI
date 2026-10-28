#!/usr/bin/env python3
"""KIWI F3 2.0 監控資料：給模擬盤監控台（dashboard）用的 JSON 檔。

每次機器人跑完後執行，讀機器人的 state.json／ledger.csv，再抓 OKX 公開行情，寫出：
  <home>/dash/summary.json      總覽（淨值、報酬、持倉數、目前的警示）
  <home>/dash/legs.json         每條腿的資金、持倉、停利停損距離
  <home>/dash/equity.json       淨值歷史（每次執行記一筆，也存在 <home>/equity.csv）
  <home>/dash/trades.json       最近的進出場明細（含實際成交和訊號價的差距）
  <home>/dash/health.json       失效檢查（規則手冊 §15.1：勝率、連虧、單腿回撤）
  <home>/dash/market.json       市場變量與門檻（規則手冊 §16）
  <home>/dash/market_hist.json  市場變量最近 180 天
  <home>/dash/shorts.json       做空籃子 8 個幣的狀態（波動比、資金費率）
  <home>/dash/candidates.json   候選幣五關檢查（規則手冊 §15.2；每 7 天重算一次）

  python3 f3_monitor.py --home ~/.kiwi-f3/okx-demo-F3-2.0
  python3 f3_monitor.py --home ... --candidates      # 強制重算候選幣

只讀 OKX 公開 API，不需要金鑰、不下單。
"""
import argparse
import csv
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f3_backtest as bt  # noqa: E402
from f3_okx_bot import build_legs, wilson_upper  # noqa: E402

OKX = "https://www.okx.com"
# 監控和候選的範圍：研究時用的 25 個幣（規則手冊 §13）
UNIVERSE = ["BTC", "ETH", "SOL", "XRP", "DOGE", "LINK", "AVAX", "ADA", "LTC", "DOT", "TRX", "BCH", "NEAR", "ATOM",
            "UNI", "AAVE", "BNB", "XLM", "ETC", "HBAR", "FIL", "ICP", "OP", "INJ", "APT"]
ACTIVE = {"BNB", "TRX", "BCH"}
# §15.1 門檻：回測最長連虧 + 2、回測最大回撤 × 1.5（做空籃子以 8 幣合計）
STREAK_LIMIT = {"BNB 日線 多": 6, "TRX 4小時 多": 6, "BCH 4小時 多": 4, "做空籃子": 15}
DD_LIMIT = {"BNB 日線 多": -26.0, "TRX 4小時 多": -38.0, "BCH 4小時 多": -21.0, "做空籃子": -31.0}
# §16 市場變量門檻（2022-10 → 2026-10 交易依進場時的變量分三等份；兩半樣本方向一致才列為警示）
BREADTH_HOT, BREADTH_COLD = 48.0, 16.7
BTC_RET30_HOT = 7.7
VOL_RATIO_COLD = 0.68
FUNDING_COST = -0.0001   # 每 8 小時 −0.01%：做空每天付約 0.03%，等於回測假設的上限
# §15 流動性：OKX 現貨 24 小時成交額（百萬 USDT）。最大一條腿約 2.3 萬 USDT，5 百萬時單筆約佔一天的 0.5%
MIN_VOL_M = 5.0
SLIP_LIMIT = 0.15        # 每邊實際成交和訊號價差 > 0.15%（回測假設 0.02% 滑價＋0.05% 手續費）


def now_utc():
    return datetime.now(timezone.utc)


def write(folder, name, rows):
    (folder / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, default=float, allow_nan=False))


def clean(x, nd=4):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return None
    return round(float(x), nd)


def tickers():
    out = {}
    for itype in ("SPOT", "SWAP"):
        for r in bt._get(f"{OKX}/api/v5/market/tickers?instType={itype}")["data"]:
            out[r["instId"]] = r
    return out


def daily(symbol, days):
    start = int((pd.Timestamp.now("UTC").tz_localize(None) - pd.Timedelta(days=days)).timestamp() * 1000)
    rows = bt.fetch_okx(symbol, "1d", start)
    df = pd.DataFrame.from_dict(rows, orient="index", columns=["open", "high", "low", "close"]).sort_index()
    df.index = pd.to_datetime(df.index, unit="ms")
    return df


# ---------- 策略本身 ----------
def ledger_rows(home):
    p = home / "ledger.csv"
    return list(csv.DictReader(open(p))) if p.exists() else []


def leg_rows(legs, state, tk):
    rows, total = [], 0.0
    for g in legs:
        st = state["legs"][g["name"]]
        eq, pos = st["equity"], st["pos"]
        last = float(tk.get(f"{g['symbol']}-USDT", {}).get("last") or "nan")
        row = dict(leg=g["name"], symbol=g["symbol"], side="空" if g["side"] == "short" else "多", tf=g["tf"],
                   weight=clean(g["w"] * 100, 2), equity=clean(eq, 2), status="空手", last=clean(last, 6),
                   entry=None, tp=None, sl=None, unreal_pct=None, to_tp_pct=None, to_sl_pct=None,
                   bars_held=None, max_bars=g["max_bars"])
        mark = eq
        if pos and not math.isnan(last):
            short = pos["side"] == "short"
            move = last / pos["entry_px"] - 1
            unreal = -move if short else move
            mark = eq * (1 + unreal)
            step = pd.Timedelta(hours=4) if g["tf"] == "4h" else pd.Timedelta(days=1)
            held = int((pd.Timestamp.now("UTC").tz_localize(None) - pd.Timestamp(pos["entry_bar"])) / step)
            row.update(status="持倉中", entry=clean(pos["entry_px"], 6), tp=clean(pos["tp"], 6), sl=clean(pos["sl"], 6),
                       unreal_pct=clean(unreal * 100, 2), bars_held=held,
                       to_tp_pct=clean(abs(pos["tp"] / last - 1) * 100, 2), to_sl_pct=clean(abs(pos["sl"] / last - 1) * 100, 2))
        row["mark"] = clean(mark, 2)
        total += mark
        rows.append(row)
    return rows, total


def equity_history(home, state, rows, total):
    p = home / "equity.csv"
    longs = sum(r["mark"] for r in rows if r["side"] == "多")
    shorts = sum(r["mark"] for r in rows if r["side"] == "空")
    new = not p.exists()
    with open(p, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time_utc", "equity", "long", "short"])
        w.writerow([now_utc().isoformat(timespec="minutes"), f"{total:.2f}", f"{longs:.2f}", f"{shorts:.2f}"])
    hist = pd.read_csv(p, parse_dates=["time_utc"])
    cap = state["capital"]
    hist["ret_pct"] = (hist.equity / cap - 1) * 100
    hist["dd_pct"] = (hist.equity / hist.equity.cummax() - 1) * 100
    # 最近 30 天逐筆（每小時），更早的每天留最後一筆，檔案才不會越長越大
    cut = hist.time_utc.max() - pd.Timedelta(days=30)
    old = hist[hist.time_utc < cut]
    old = old.groupby(old.time_utc.dt.floor("D")).tail(1)
    hist = pd.concat([old, hist[hist.time_utc >= cut]])
    return [dict(time=f"{r.time_utc:%Y-%m-%dT%H:%M}", equity=clean(r.equity, 2), long=clean(r.long, 2), short=clean(r.short, 2),
                 ret_pct=clean(r.ret_pct, 3), dd_pct=clean(r.dd_pct, 3)) for r in hist.itertuples()]


def slip_of(r):
    """ENTER 的 note 有「訊號收盤 X 實際成交 Y」：回傳不利方向的滑價 %（紙上交易沒有這段）。"""
    note = r.get("note") or ""
    if "訊號收盤" not in note or "實際成交" not in note:
        return None
    try:
        sig = float(note.split("訊號收盤")[1].split()[0])
        fill = float(note.split("實際成交")[1].split()[0])
    except (IndexError, ValueError):
        return None
    d = (fill / sig - 1) * 100
    return clean(-d if r["side"] == "short" else d, 3)


def trade_rows(led):
    out = []
    for i, r in enumerate(led[-150:]):
        out.append(dict(id=i, time=r["run_utc"][:16], leg=r["leg"], action={"ENTER": "進場", "EXIT": "出場", "ERROR": "錯誤"}.get(r["action"], r["action"]),
                        price=clean(float(r["price"]), 6) if r.get("price") else None, reason=r.get("reason") or "",
                        ret_pct=clean(float(r["ret"]) * 100, 2) if r.get("ret") else None,
                        slip_pct=slip_of(r) if r["action"] == "ENTER" else None, note=(r.get("note") or "")[:120]))
    return out[::-1]


def health_rows(legs, led):
    groups = {}
    for g in legs:
        key = "做空籃子" if g["side"] == "short" else g["name"]
        groups.setdefault(key, {"bt_wr": g["bt_wr"], "names": set()})["names"].add(g["name"])
    exits = [r for r in led if r["action"] == "EXIT" and r.get("ret")]
    enters = [r for r in led if r["action"] == "ENTER"]
    out = []
    for key, info in groups.items():
        rets = [float(r["ret"]) for r in exits if r["leg"] in info["names"]]
        n, wins = len(rets), sum(x > 0 for x in rets)
        streak = 0
        for x in rets:
            streak = streak + 1 if x <= 0 else 0
        eq = np.cumprod([1 + x for x in rets]) if rets else np.array([1.0])
        dd = float((eq / np.maximum.accumulate(eq) - 1).min() * 100) if rets else 0.0
        slips = [s for s in (slip_of(r) for r in enters if r["leg"] in info["names"]) if s is not None]
        upper = wilson_upper(wins, n) if n else None
        if n and upper < info["bt_wr"] and n >= 10:
            status = "建議停用"
        elif streak > STREAK_LIMIT[key] or dd < DD_LIMIT[key]:
            status = "暫停複查"
        elif n < 10:
            status = "樣本不足"
        else:
            status = "正常"
        out.append(dict(group=key, n=n, wr=clean(wins / n * 100, 1) if n else None, bt_wr=info["bt_wr"],
                        wilson_upper=clean(upper, 1), avg_pct=clean(np.mean(rets) * 100, 2) if n else None,
                        streak=streak, streak_limit=STREAK_LIMIT[key], dd_pct=clean(dd, 2), dd_limit=DD_LIMIT[key],
                        slip_pct=clean(np.mean(slips), 3) if slips else None, slip_limit=SLIP_LIMIT, status=status))
    return out


# ---------- 市場變量（§16） ----------
def market(dfs, tk):
    C = pd.DataFrame({c: d.close for c, d in dfs.items()}).sort_index()
    R = np.log(C).diff()
    above = (C > C.ewm(span=200, adjust=False).mean()).where(C.notna())
    valid = C.notna().cumsum() >= 200   # EMA200 至少暖機 200 天才算進廣度
    breadth = above.where(valid).mean(axis=1) * 100
    btc = C["BTC"]
    btc_trend = (btc / btc.ewm(span=200, adjust=False).mean() - 1) * 100
    btc_ret30 = (btc / btc.shift(30) - 1) * 100
    btc_vol30 = R["BTC"].rolling(30).std() * math.sqrt(365) * 100
    corr30 = pd.Series({R.index[i]: (lambda c: (c.sum() - len(c)) / (len(c) ** 2 - len(c)))(R.iloc[i - 30:i].dropna(axis=1).corr().to_numpy())
                        for i in range(len(R) - 200, len(R))})
    shorts = [g["symbol"] for g in bt.LEGS if g["side"] == "short"]
    vr = pd.DataFrame({c: R[c].rolling(30).std() / R[c].rolling(365).std() for c in shorts})
    basket_vr = vr.mean(axis=1)

    s_rows = []
    for c in shorts:
        fr = bt._get(f"{OKX}/api/v5/public/funding-rate?instId={c}-USDT-SWAP")["data"]
        f = float(fr[0]["fundingRate"]) if fr else None
        e200 = C[c].ewm(span=200, adjust=False).mean()
        s_rows.append(dict(coin=c, close=clean(C[c].iloc[-1], 6), dist200_pct=clean((C[c].iloc[-1] / e200.iloc[-1] - 1) * 100, 1),
                           gate="可開空" if C[c].iloc[-1] < e200.iloc[-1] else "不開空（在 EMA200 之上）",
                           vol_ratio=clean(vr[c].iloc[-1], 2), funding_8h_pct=clean(f * 100, 4) if f is not None else None,
                           vol24h_musd=clean(float(tk.get(f"{c}-USDT-SWAP", {}).get("volCcy24h") or 0) *
                                             float(tk.get(f"{c}-USDT-SWAP", {}).get("last") or 0) / 1e6, 1)))
    fund = [r["funding_8h_pct"] for r in s_rows if r["funding_8h_pct"] is not None]
    avg_fund = float(np.mean(fund)) / 100 if fund else None

    b, r30, bvr = breadth.iloc[-1], btc_ret30.iloc[-1], basket_vr.iloc[-1]
    m = [
        dict(key="breadth", name="市場廣度", value=clean(b, 1), unit="%",
             rule=f"> {BREADTH_HOT:.0f}% 警示；< {BREADTH_COLD:.0f}% 做多腿多半空手",
             status="警示" if b > BREADTH_HOT else "提示" if b < BREADTH_COLD else "正常",
             meaning="25 個幣裡收盤在自己 EMA200 之上的比例。",
             effect="> 48%（山寨普漲）時 TRX 新單平均每筆 −0.1%、勝率 67%，其他時候 +1.4%、勝率 81%，兩半樣本一致；< 17% 時做多腿幾乎不開倉。"),
        dict(key="btc_ret30", name="BTC 30 日漲跌", value=clean(r30, 1), unit="%",
             rule=f"> +{BTC_RET30_HOT}% 警示（做空籃子）",
             status="警示" if r30 > BTC_RET30_HOT else "正常",
             meaning="BTC 最近 30 天的漲跌幅。",
             effect="> +7.7%（V 型反彈）時做空籃子新單平均每筆 −1.4%、勝率 52%；其他時候 +1.7%、勝率 71%，兩半樣本一致。"),
        dict(key="basket_vol_ratio", name="做空籃子波動比", value=clean(bvr, 2), unit="倍",
             rule=f"< {VOL_RATIO_COLD} 警示（做空籃子）",
             status="警示" if bvr < VOL_RATIO_COLD else "正常",
             meaning="8 個做空幣 30 日波動 ÷ 365 日波動的平均。小於 1 代表最近比平常安靜。",
             effect="波動收斂（< 0.68）時做空新單平均每筆 −1.2%、勝率 53%；其他時候 +1.5%、勝率 69%，兩半樣本一致。"),
        dict(key="funding", name="做空資金費率", value=clean(avg_fund * 100, 4) if avg_fund is not None else None, unit="%/8h",
             rule="< −0.01%/8h 警示（做空成本高於回測假設）",
             status="警示" if avg_fund is not None and avg_fund < FUNDING_COST else "正常",
             meaning="8 個做空幣永續合約目前的資金費率平均。正數＝做空收錢，負數＝做空付錢。",
             effect="回測假設做空每天付 0.03%（每 8 小時 0.01%），實際更負就會比回測差。"),
        dict(key="btc_trend", name="BTC 距 EMA200", value=clean(btc_trend.iloc[-1], 1), unit="%", rule="只看方向，不設警示",
             status="參考", meaning="BTC 收盤高於（正）或低於（負）200 日均線多少。",
             effect="決定大盤多空；對各腿的影響在兩半樣本不一致，所以只當背景。"),
        dict(key="btc_vol30", name="BTC 30 日波動", value=clean(btc_vol30.iloc[-1], 1), unit="%/年", rule="只看方向，不設警示",
             status="參考", meaning="BTC 最近 30 天的年化波動。", effect="對做多腿影響不明顯；做空籃子在高波動時較好，但已由波動比涵蓋。"),
        dict(key="corr30", name="幣之間平均相關", value=clean(corr30.iloc[-1], 2), unit="", rule="只看方向，不設警示",
             status="參考", meaning="25 個幣最近 30 天日報酬的平均兩兩相關。", effect="越高代表越同漲同跌，分散效果越差；對勝率的影響不穩定。"),
    ]
    hist = pd.DataFrame({"breadth": breadth, "btc_ret30": btc_ret30, "basket_vol_ratio": basket_vr,
                         "btc_trend": btc_trend, "btc_vol30": btc_vol30}).dropna().iloc[-180:]
    h = [dict(day=f"{d:%Y-%m-%d}", **{k: clean(v, 3) for k, v in r.items()}) for d, r in hist.iterrows()]
    return m, h, s_rows


# ---------- 候選幣（§15.2） ----------
RULES = [g for g in bt.LEGS if g["side"] == "long"]   # 只能用現有三條規則，參數不改


def realized(rets):
    return float(np.prod([1 + r for r in rets]) - 1) if rets else 0.0


def candidates_due(folder, force):
    meta_p = folder.parent / "candidates_state.json"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {"updated": None, "since": {}}
    due = force or not (folder / "candidates.json").exists() or not meta["updated"] \
        or pd.Timestamp.now("UTC") - pd.Timestamp(meta["updated"]) >= pd.Timedelta(days=7)
    return due, meta, meta_p


def candidates(dfs, tk, meta, meta_p):
    now = pd.Timestamp.now("UTC").tz_localize(None)
    start4 = now - pd.Timedelta(days=4 * 365)
    half = now - pd.Timedelta(days=2 * 365)
    ref = {c: np.log(dfs[c].close).diff() for c in ACTIVE if c in dfs}
    rows = []
    for c in UNIVERSE:
        if c == "BTC" or c not in dfs:
            continue
        d = dfs[c]
        spot, swap = tk.get(f"{c}-USDT"), tk.get(f"{c}-USDT-SWAP")
        vol24 = float(spot.get("volCcy24h") or 0) / 1e6 if spot else 0.0   # 現貨的 volCcy24h 是 USDT 計價
        g1 = bool(spot and swap and vol24 >= MIN_VOL_M and len(d) >= 1000)
        last2 = d[d.index >= now - pd.Timedelta(days=730)]
        r = np.log(last2.close).diff().dropna()
        vol = float(r.std() * math.sqrt(365) * 100)
        e200 = d.close.ewm(span=200, adjust=False).mean()
        above = float((d.close > e200)[d.index >= now - pd.Timedelta(days=730)].mean() * 100)
        k = 5
        vr5 = float(np.var(r.rolling(k).sum().dropna()[::k]) / (k * np.var(r)))
        g2 = vol <= 70 and above >= 50 and vr5 < 1
        row = dict(coin=c, active="現役" if c in ACTIVE else "", vol24h_musd=clean(vol24, 1), days=len(d),
                   gate1=g1, vol2y=clean(vol, 1), above2y=clean(above, 1), vr5=clean(vr5, 2), gate2=g2,
                   rule=None, n=None, wr=None, rule_bt_wr=None, h1=None, h2=None, gate3=False,
                   since=None, shadow_n=None, shadow_wr=None, shadow_avg=None, corr=None, gate4=False, stage=0)
        row["stage"] = 1 if not g1 else 2 if not g2 else 3
        if (g1 and g2) or c in ACTIVE:
            best = None
            for g in RULES:
                if c in ACTIVE and g["symbol"] != c:
                    continue   # 現役幣只看自己的規則
                daily_from = int((start4 - pd.Timedelta(days=400)).timestamp() * 1000)
                bars = d if g["tf"] == "1d" else bt.load("okx", c, "4h", int((start4 - pd.Timedelta(days=30)).timestamp() * 1000))
                entry, _ = bt.signals(g, bars, d)
                tr = bt.simulate(g, bars, entry, start4)
                rets = [x["ret"] for x in tr if x["reason"] != "期末未平"]
                if len(rets) < 1:
                    continue
                wr = float(np.mean([x > 0 for x in rets]) * 100)
                h1 = realized([x["ret"] for x in tr if x["entry_time_utc"] < half])
                h2 = realized([x["ret"] for x in tr if x["entry_time_utc"] >= half])
                no_best = realized(sorted(rets)[:-1])
                ok = len(rets) >= 30 and wr >= g["bt_wr"] - 5 and h1 > 0 and h2 > 0 and no_best > 0
                cand = dict(rule=g["name"].replace(g["symbol"], "").strip() + f"（{g['symbol']} 規則）", n=len(rets), wr=clean(wr, 1),
                            rule_bt_wr=g["bt_wr"], h1=clean(h1 * 100, 1), h2=clean(h2 * 100, 1), gate3=ok, _g=g)
                if best is None or (cand["gate3"], cand["wr"] - cand["rule_bt_wr"]) > (best["gate3"], best["wr"] - best["rule_bt_wr"]):
                    best = cand
                time.sleep(0.2)
            if best:
                g = best.pop("_g")
                row.update(best)
                if best["gate3"] and c not in ACTIVE:
                    row["stage"] = 4
                    since = meta["since"].setdefault(c, {"rule": g["name"], "since": f"{now:%Y-%m-%d}"})
                    row["since"] = since["since"]
                    sg = next(x for x in RULES if x["name"] == since["rule"])
                    bars = d if sg["tf"] == "1d" else bt.load("okx", c, "4h", int((pd.Timestamp(since["since"]) - pd.Timedelta(days=30)).timestamp() * 1000))
                    entry, _ = bt.signals(sg, bars, d)
                    sh = [x["ret"] for x in bt.simulate(sg, bars, entry, pd.Timestamp(since["since"])) if x["reason"] != "期末未平"]
                    rc = np.log(d.close).diff()
                    corr = max(rc.iloc[-90:].corr(v.iloc[-90:]) for v in ref.values()) if ref else None
                    row.update(shadow_n=len(sh), shadow_wr=clean(np.mean([x > 0 for x in sh]) * 100, 1) if sh else None,
                               shadow_avg=clean(np.mean(sh) * 100, 2) if sh else None, corr=clean(corr, 2))
                    row["gate4"] = bool(sh and len(sh) >= 20 and row["shadow_wr"] >= row["wr"] and row["shadow_avg"] >= 0.3
                                        and (corr is None or corr < 0.6))
                    row["stage"] = 5 if row["gate4"] else 4
                elif not best["gate3"] and c in meta["since"]:
                    meta["since"].pop(c)   # 掉出第 3 關：影子腿重來
        miss = [n for n, ok in (("波動", vol <= 70), ("多頭時間", above >= 50), ("均值回歸", vr5 < 1)) if not ok]
        if not g1:
            v = "第 1 關未過：流動性或上市時間"
        elif not g2:
            v = "第 2 關未過：" + "、".join(miss)
        elif not row["gate3"]:
            v = "第 3 關未過：固定規則回測"
        elif not row["gate4"] and c not in ACTIVE:
            v = f"影子腿觀察中（{row['shadow_n'] or 0}／20 筆）"
        else:
            v = "五關都過" if c not in ACTIVE else "第 1～3 關都過"
        row["verdict"] = ("現役，" if c in ACTIVE else "") + v
        rows.append(row)
    meta["updated"] = pd.Timestamp.now("UTC").isoformat()
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    rows.sort(key=lambda r: (-r["stage"], r["coin"]))
    for r in rows:
        r["updated"] = meta["updated"][:16]
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--home", required=True, help="機器人的狀態資料夾（含 state.json）")
    ap.add_argument("--mode", default="okx-demo")
    ap.add_argument("--candidates", action="store_true", help="強制重算候選幣")
    a = ap.parse_args()
    home = Path(a.home)
    state = json.loads((home / "state.json").read_text())
    legs = build_legs(True, state["capital"])
    out = home / "dash"
    out.mkdir(exist_ok=True)
    tk = tickers()
    led = ledger_rows(home)

    legs_r, total = leg_rows(legs, state, tk)
    eq = equity_history(home, state, legs_r, total)
    health = health_rows(legs, led)
    due, meta, meta_p = candidates_due(out, a.candidates)
    dfs = {c: daily(c, 1600 if due else 620) for c in UNIVERSE}   # 候選幣要 4 年；市場變量 620 天夠算 365 日波動和 EMA200
    mkt, mhist, shorts = market(dfs, tk)
    cands = candidates(dfs, tk, meta, meta_p) if due else None

    alerts = [f"{m['name']} {m['value']}{m['unit']}：{m['rule']}" for m in mkt if m["status"] == "警示"]
    alerts += [f"{h['group']}：{h['status']}" for h in health if h["status"] in ("建議停用", "暫停複查")]
    alerts += [f"{h['group']} 平均滑價 {h['slip_pct']}% 超過 {SLIP_LIMIT}%" for h in health if h["slip_pct"] and h["slip_pct"] > SLIP_LIMIT]
    cap = state["capital"]
    summary = [dict(updated=now_utc().isoformat(timespec="minutes"), mode=a.mode, capital=cap, equity=clean(total, 2),
                    ret_pct=clean((total / cap - 1) * 100, 3), dd_pct=eq[-1]["dd_pct"] if eq else 0,
                    max_dd_pct=clean(min(r["dd_pct"] for r in eq), 3) if eq else 0, dd_stop=-15.0,
                    open_positions=sum(r["status"] == "持倉中" for r in legs_r),
                    closed_trades=sum(1 for r in led if r["action"] == "EXIT"),
                    errors=sum(1 for r in led if r["action"] == "ERROR"),
                    alerts=len(alerts), alert_text="；".join(alerts) if alerts else "沒有警示",
                    started=state.get("created_utc", "")[:10])]
    for name, rows in [("summary", summary), ("legs", legs_r), ("equity", eq), ("trades", trade_rows(led)),
                       ("health", health), ("market", mkt), ("market_hist", mhist), ("shorts", shorts)]:
        write(out, name, rows)
    if cands is not None:
        write(out, "candidates", cands)
    print(f"監控資料已更新：{out}（警示 {len(alerts)} 項）" + ("，候選幣已重算" if cands is not None else ""))
    for x in alerts:
        print(f"  ⚠️ {x}")


if __name__ == "__main__":
    main()
