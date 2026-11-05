#!/usr/bin/env python3
"""
market_cockpit_tw.py — 全局觀測台的台股模組（被 market_cockpit.py 呼叫，也可單獨跑）

與美股版同一套框架，差別在資料：
  指數：證交所 20 個類股價格指數 + 發行量加權（TAIEX）。歷史（2019→）一次性從 TradingView 取得存在
        data/tw/tv/IX00xx.json；之後每日由 fetch_tw_sectors.py 用證交所 MI_INDEX 追加到 data/tw/sector_index.csv。
  資金流：**真實資金流**——證交所 T86 三大法人每檔買賣超股數 × 當日收盤價，依 t187ap03_L 產業別彙總
        （data/tw/sector_flow.csv）。流向強度 = 20 日三大法人淨買超 ÷ 20 日成交金額。
  regime：TAIEX 趨勢 + 類股廣度 + 實現波動（台股沒有可免費取得的 VIX／信用利差，權重自動重新正規化）。

輸出：dict（放進 docs/cockpit/data.json 的 "tw" 與 backtest.json 的 "tw"）。
"""

import csv
import json
import math
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import market_cockpit as mc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(ROOT))
DATA = os.path.join(ROOT, "data", "tw")
TV_DIR = os.path.join(DATA, "tv")
IDX_CSV = os.path.join(DATA, "sector_index.csv")
FLOW_CSV = os.path.join(DATA, "sector_flow.csv")
TAIWAN_JSON = os.path.join(REPO, "docs", "taiwan_data.json")

BENCH = "IX0001"
# (TradingView/證交所指數代碼, 中文名, 證交所 MI_INDEX 名稱, 產業別代碼（T86 彙總用）)
SECTORS = [
    ("IX0028", "半導體", "半導體類指數", "24"),
    ("IX0029", "電腦及週邊", "電腦及週邊設備類指數", "25"),
    ("IX0030", "光電", "光電類指數", "26"),
    ("IX0031", "通信網路", "通信網路類指數", "27"),
    ("IX0032", "電子零組件", "電子零組件類指數", "28"),
    ("IX0033", "電子通路", "電子通路類指數", "29"),
    ("IX0034", "資訊服務", "資訊服務類指數", "30"),
    ("IX0035", "其他電子", "其他電子類指數", "31"),
    ("IX0039", "金融保險", "金融保險類指數", "17"),
    ("IX0037", "航運", "航運類指數", "15"),
    ("IX0012", "塑膠", "塑膠類指數", "03"),
    ("IX0024", "鋼鐵", "鋼鐵類指數", "10"),
    ("IX0017", "電機機械", "電機機械類指數", "05"),
    ("IX0021", "生技醫療", "生技醫療類指數", "22"),
    ("IX0036", "建材營造", "建材營造類指數", "14"),
    ("IX0026", "汽車", "汽車類指數", "12"),
    ("IX0011", "食品", "食品類指數", "02"),
    ("IX0038", "觀光餐旅", "觀光餐旅類指數", "16"),
    ("IX0041", "油電燃氣", "油電燃氣類指數", "23"),
    ("IX0020", "化學", "化學類指數", "21"),
]
BENCH_NAME = "發行量加權股價指數"
SECTOR_SYMS = [s for s, _, _, _ in SECTORS]
NAME2CODE = {n: c for c, _, n, _ in SECTORS}
NAME2CODE[BENCH_NAME] = BENCH
IND2CODE = {i: c for c, _, _, i in SECTORS}
PILLAR_W = {"trend": 0.45, "breadth": 0.35, "vol": 0.20}


# ---------------------------------------------------------------- data
def load_index():
    """TradingView 歷史 + 證交所每日追加 → DataFrame[date × code] 收盤。"""
    cols = {}
    for code in [BENCH] + SECTOR_SYMS:
        f = os.path.join(TV_DIR, f"{code}.json")
        if not os.path.exists(f):
            continue
        b = json.load(open(f))["bars"]
        idx = pd.to_datetime(b["t"], unit="s", utc=True).tz_convert("Asia/Taipei").normalize().tz_localize(None)
        cols[code] = pd.Series(b["c"], index=idx, dtype=float)
    df = pd.DataFrame(cols)
    if os.path.exists(IDX_CSV):
        tw = pd.read_csv(IDX_CSV, parse_dates=["date"]).set_index("date")
        tw = tw.rename(columns={n: NAME2CODE[n] for n in tw.columns if n in NAME2CODE})
        tw = tw[[c for c in tw.columns if c in cols]]
        # 證交所資料優先（正式收盤），TradingView 只補證交所沒有的日期
        df = tw.combine_first(df) if not df.empty else tw
    df = df[~df.index.duplicated(keep="last")].sort_index().dropna(subset=[BENCH])
    return df


def load_flow():
    if not os.path.exists(FLOW_CSV):
        return None
    f = pd.read_csv(FLOW_CSV, dtype={"ind": str}, parse_dates=["date"])
    f["code"] = f["ind"].map(IND2CODE)
    f = f.dropna(subset=["code"])
    out = {}
    for col in ("inst_net", "foreign_net", "trust_net", "dealer_net", "turnover"):
        out[col] = f.pivot_table(index="date", columns="code", values=col, aggfunc="sum").sort_index()
    return out


# ---------------------------------------------------------------- regime（TAIEX）
def build_regime(px_df):
    px = px_df[BENCH]
    ma50, ma200 = px.rolling(50).mean(), px.rolling(200).mean()
    out = pd.DataFrame(index=px.index)
    out["spy"], out["spy_close"] = px, px  # 欄位名沿用美股版，讓 bt_regime 可直接重用
    out["ma50"], out["ma200"] = ma50, ma200
    out["dist200"] = px / ma200 - 1
    t1 = mc.clip100((px / ma200 - 1) / 0.10 * 100)
    t2 = mc.clip100((ma50 / ma200 - 1) / 0.05 * 100)
    t3 = mc.clip100(ma200.pct_change(20) / 0.02 * 100)
    out["trend"] = 0.5 * t1 + 0.25 * t2 + 0.25 * t3
    out["t_dist200"], out["t_golden"], out["t_slope"] = t1, t2, t3
    secs = px_df[[c for c in SECTOR_SYMS if c in px_df]]
    a200 = (secs > secs.rolling(200).mean()).where(secs.notna()).mean(axis=1)
    a50 = (secs > secs.rolling(50).mean()).where(secs.notna()).mean(axis=1)
    ew = (secs / secs.iloc[0]).mean(axis=1)  # 類股等權指數（參與度）
    part = mc.clip100((ew / px).pct_change(63) / 0.05 * 100)
    b1, b2 = (a200 - 0.5) * 200, (a50 - 0.5) * 200
    out["breadth"] = 0.4 * b1 + 0.3 * b2 + 0.3 * part.fillna((b1 + b2) / 2)
    out["b_above200"], out["b_above50"], out["b_particip"] = b1, b2, part
    out["pct_above200"], out["pct_above50"] = a200, a50
    rv = px.pct_change().rolling(20).std() * math.sqrt(252)
    v3 = (0.5 - mc.pct_rank_rolling(rv, 252)) * 200
    v2 = mc.clip100(-(rv / rv.rolling(50).mean() - 1) / 0.5 * 100)
    out["vol"] = 0.6 * v3 + 0.4 * v2
    out["rv20"] = rv
    out["v_rv_pct"], out["v_rv_trend"] = v3, v2
    W = pd.DataFrame({k: out[k].notna() * w for k, w in PILLAR_W.items()})
    out["score"] = sum(out[k].fillna(0) * PILLAR_W[k] for k in PILLAR_W) / W.sum(axis=1).replace(0, np.nan)
    states, st, pend, pend_n = [], "range", None, 0
    sc, d2 = out["score"].values, out["dist200"].values
    for i in range(len(out)):
        s, d = sc[i], d2[i]
        if np.isnan(s) or np.isnan(d):
            states.append(None)
            continue
        if st == "bull":
            want = "range" if s < mc.BULL_OUT else "bull"
        elif st == "bear":
            want = "range" if s > mc.BEAR_OUT else "bear"
        else:
            want = "bull" if (s >= mc.BULL_IN and d > 0) else "bear" if (s <= mc.BEAR_IN and d < 0) else "range"
        if want != st:
            pend_n = pend_n + 1 if want == pend else 1
            pend = want
            if pend_n >= mc.CONFIRM_DAYS:
                st, pend, pend_n = want, None, 0
        else:
            pend, pend_n = None, 0
        states.append(st)
    out["state"] = states
    return out


# ---------------------------------------------------------------- sectors + real flows
def build_sectors(px_df, flow):
    bench = px_df[BENCH]
    panel = {}
    for code in SECTOR_SYMS:
        if code not in px_df:
            continue
        p = px_df[code]
        d = pd.DataFrame(index=px_df.index)
        d["adj"], d["close"] = p, p
        for h, name in ((5, "1w"), (21, "1m"), (63, "3m"), (126, "6m"), (252, "1y")):
            d[f"ret_{name}"] = p.pct_change(h)
            d[f"exc_{name}"] = p.pct_change(h) - bench.pct_change(h)
        d["above50"] = p > p.rolling(50).mean()
        d["above200"] = p > p.rolling(200).mean()
        d["rs_ratio"], d["rs_mom"] = mc.rrg_series(p, bench)
        if flow is not None and code in flow["inst_net"]:
            inst = flow["inst_net"][code].reindex(px_df.index)
            tov = flow["turnover"][code].reindex(px_df.index)
            d["inst20"] = inst.rolling(20, min_periods=5).sum()
            d["foreign20"] = flow["foreign_net"][code].reindex(px_df.index).rolling(20, min_periods=5).sum()
            d["trust20"] = flow["trust_net"][code].reindex(px_df.index).rolling(20, min_periods=5).sum()
            d["dealer20"] = flow["dealer_net"][code].reindex(px_df.index).rolling(20, min_periods=5).sum()
            d["dv20"] = tov.rolling(20, min_periods=5).sum()
            d["flow"] = d["inst20"] / d["dv20"]
            d["flow_avg_1y"] = d["flow"].rolling(252, min_periods=120).mean()
            d["flow_avg_5y"] = d["flow"].rolling(1260, min_periods=120).mean()
            d["flow_pct"] = mc.pct_rank_rolling(d["flow"], 1260, min_periods=60) * 100
            d["flow_z1y"] = (d["flow"] - d["flow_avg_1y"]) / d["flow"].rolling(252, min_periods=120).std()
            d["inst_5d"] = inst.rolling(5, min_periods=3).sum()
        else:
            for c in ("inst20", "foreign20", "trust20", "dealer20", "dv20", "flow", "flow_avg_1y", "flow_avg_5y", "flow_pct", "flow_z1y", "inst_5d"):
                d[c] = np.nan
        panel[code] = d
    strength = {}
    for h, w in (("3m", 0.30), ("6m", 0.40), ("1y", 0.30)):
        exc = pd.concat({s: panel[s][f"exc_{h}"] for s in panel}, axis=1)
        strength[h] = exc.rank(axis=1, pct=True) * w
    tot = sum(strength.values())
    cnt = pd.concat({s: panel[s]["exc_1y"] for s in panel}, axis=1).notna().sum(axis=1)
    score = (tot * 100).where(cnt >= 10)
    dv_all = pd.concat({s: panel[s]["dv20"] for s in panel}, axis=1)
    share = dv_all.div(dv_all.sum(axis=1), axis=0)
    for s in panel:
        panel[s]["strength"] = score[s]
        panel[s]["share"] = share[s]
        panel[s]["share_avg_1y"] = share[s].rolling(252, min_periods=120).mean()
    return panel


def taiwan_aux():
    try:
        j = json.load(open(TAIWAN_JSON, encoding="utf-8"))
        return {"futures_net": j.get("futures_latest"), "futures_signal": j.get("futures_signal"),
                "margin_ratio": j.get("margin_ratio_latest"), "margin_pct": j.get("margin_pct"), "margin_level": j.get("margin_level"),
                "updated": j.get("updated")}
    except Exception:  # noqa: BLE001
        return {}


# ---------------------------------------------------------------- snapshot
def snapshot(px_df, reg, panel, flow):
    d = reg.dropna(subset=["score"]).index[-1]
    row = reg.loc[d]
    px = px_df[BENCH]
    h = reg.loc[:d].tail(504)
    ytd = px.loc[d] / px[px.index.year == d.year].iloc[0] - 1
    eps = mc.regime_episodes(reg)
    cur = eps[-1] if eps else None
    r = mc.r
    pillars = {
        "trend": {"label": "趨勢", "score": r(row["trend"], 1), "weight": PILLAR_W["trend"],
                  "parts": {"加權指數 vs 200日線": r(row["t_dist200"], 0), "50日線 vs 200日線": r(row["t_golden"], 0), "200日線斜率": r(row["t_slope"], 0)}},
        "breadth": {"label": "廣度", "score": r(row["breadth"], 1), "weight": PILLAR_W["breadth"],
                    "parts": {"類股站上200日線": r(row["b_above200"], 0), "類股站上50日線": r(row["b_above50"], 0), "類股等權 vs 加權": r(row["b_particip"], 0)}},
        "vol": {"label": "波動", "score": r(row["vol"], 1), "weight": PILLAR_W["vol"],
                "parts": {"實現波動一年百分位": r(row["v_rv_pct"], 0), "實現波動 vs 50日均": r(row["v_rv_trend"], 0)}},
    }
    flow_days = int(flow["inst_net"].shape[0]) if flow is not None else 0
    flow_asof = flow["inst_net"].index[-1].strftime("%Y-%m-%d") if flow is not None else None
    sectors = []
    for code, zh, _, ind in SECTORS:
        if code not in panel:
            continue
        p = panel[code].loc[d]
        trail = panel[code].loc[:d, ["rs_ratio", "rs_mom"]].iloc[::-5].head(6).iloc[::-1]
        fl = {"intensity": r(p["flow"], 3), "pct": r(p["flow_pct"], 0), "label": mc.flow_label(p["flow_pct"]),
              "avg_1y": r(p["flow_avg_1y"], 3), "avg_5y": r(p["flow_avg_5y"], 3), "z_1y": r(p["flow_z1y"], 2),
              "net20_usd": None,
              "inst20_twd": r(p["inst20"] / 1e8, 1), "foreign20_twd": r(p["foreign20"] / 1e8, 1), "trust20_twd": r(p["trust20"] / 1e8, 1),
              "dealer20_twd": r(p["dealer20"] / 1e8, 1), "inst5_twd": r(p["inst_5d"] / 1e8, 1),
              "dv20_twd": r(p["dv20"] / 1e8, 0), "share": r(p["share"] * 100, 1), "share_avg_1y": r(p["share_avg_1y"] * 100, 1)}
        sectors.append({
            "symbol": code, "name": zh, "name_en": zh, "ind": ind, "close": r(p["close"], 2),
            "ret": {k: r(p[f"ret_{k}"] * 100, 1) for k in ("1w", "1m", "3m", "6m", "1y")},
            "exc": {k: r(p[f"exc_{k}"] * 100, 1) for k in ("1w", "1m", "3m", "6m", "1y")},
            "above50": bool(p["above50"]), "above200": bool(p["above200"]),
            "strength": r(p["strength"], 0), "rs_ratio": r(p["rs_ratio"], 1), "rs_mom": r(p["rs_mom"], 1),
            "quadrant": mc.quadrant(p["rs_ratio"], p["rs_mom"]),
            "trail": [[r(a, 1), r(b, 1)] for a, b in zip(trail["rs_ratio"], trail["rs_mom"])],
            "flow": fl,
            "spark": [r(x, 2) for x in panel[code]["adj"].loc[:d].tail(60).tolist()],
        })
    sectors.sort(key=lambda x: -(x["strength"] if x["strength"] is not None else -1))
    for i, s in enumerate(sectors, 1):
        s["rank"] = i
    # 流向排序：有百分位用百分位，沒有（樣本未滿 60 日）就用強度本身
    def fkey(s):
        f = s["flow"]
        return f["pct"] if f["pct"] is not None else (f["intensity"] or -9) * 100
    fs = sorted([s for s in sectors if s["flow"]["intensity"] is not None], key=lambda s: -fkey(s))
    total_inst20 = sum((s["flow"]["inst20_twd"] or 0) for s in sectors)
    return {
        "market": "tw", "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "asof": d.strftime("%Y-%m-%d"), "bench": {"symbol": "TAIEX", "name": "發行量加權股價指數"},
        "regime": {
            "state": row["state"], "label": mc.REGIME_LABEL.get(row["state"]), "score": r(row["score"], 1),
            "since": cur["start"] if cur else None, "days": cur["days"] if cur else None,
            "thresholds": {"bull_in": mc.BULL_IN, "bull_out": mc.BULL_OUT, "bear_in": mc.BEAR_IN, "bear_out": mc.BEAR_OUT},
            "pillars": pillars,
            "spy": {"close": r(row["spy_close"], 2), "ma50": r(row["ma50"], 2), "ma200": r(row["ma200"], 2), "dist200": r(row["dist200"] * 100, 1),
                    "ret_1m": r(px.pct_change(21).loc[d] * 100, 1), "ret_3m": r(px.pct_change(63).loc[d] * 100, 1), "ytd": r(ytd * 100, 1)},
            "vix": None, "rv20": r(row["rv20"] * 100, 1),
            "breadth": {"pct_above200": r(row["pct_above200"] * 100, 0), "pct_above50": r(row["pct_above50"] * 100, 0)},
            "hyg_ief": None,
            "history": {"dates": [x.strftime("%Y-%m-%d") for x in h.index], "score": [r(x, 1) for x in h["score"]],
                        "state": h["state"].tolist(), "spy": [r(x, 2) for x in h["spy_close"]],
                        "ma200": [r(x, 2) if not np.isnan(x) else None for x in h["ma200"]]},
            "episodes": eps[-8:],
        },
        "sectors": sectors,
        "flows": {"ranking": [s["symbol"] for s in fs], "total_net20_usd": None, "total_inst20_twd": r(total_inst20, 1),
                  "inflow": [s["symbol"] for s in fs if (s["flow"]["pct"] is not None and s["flow"]["pct"] >= 60) or (s["flow"]["pct"] is None and (s["flow"]["intensity"] or 0) > 0.02)],
                  "outflow": [s["symbol"] for s in fs if (s["flow"]["pct"] is not None and s["flow"]["pct"] <= 40) or (s["flow"]["pct"] is None and (s["flow"]["intensity"] or 0) < -0.02)],
                  "history_days": flow_days, "asof": flow_asof},
        "aux": taiwan_aux(),
        "watch": [],
        "method": {
            "regime": "台股 Regime Score = 趨勢 45% + 廣度 35% + 波動 20%（沒有免費 VIX／信用利差，兩支柱省略）。門檻與美股相同（±25 進、±10 出、3 日確認）。",
            "strength": "類股強度 = 3M/6M/12M 相對加權指數超額報酬的橫斷面百分位（30/40/30）→ 0–100；RRG 同美股版。",
            "flow": "資金流向 = 三大法人 20 日淨買超金額 ÷ 20 日成交金額（證交所 T86 × 收盤價，依產業別彙總；真實法人資金，不是價量代理）。百分位 = 該類股自身歷史分位（樣本自 2025-11 起累積）。",
        },
    }


def backtest(reg, panel, px_df):
    bench = px_df[BENCH]
    out = {"regime": mc.bt_regime(reg), "sectors": mc.bt_sectors(panel, bench, reg, k=5)}
    try:
        if any(panel[s]["flow"].notna().sum() > 120 for s in panel):
            out["flows"] = mc.bt_flows(panel, bench)
            out["flows"]["note"] = "流向＝三大法人 20 日淨買超 ÷ 20 日成交金額（真實法人資金）。樣本自 2025-11 起，月數少，統計力有限。"
        else:
            out["flows"] = None
    except Exception as e:  # noqa: BLE001
        out["flows"] = None
        print(f"[tw] flows backtest skipped: {e}", file=sys.stderr)
    out["caveats"] = [
        "類股指數為價格指數（不含股息），樣本 2019-01 → 今；regime 回測只有 7 年、一次完整空頭（2022）。",
        "法人流向自 2025-11 起由證交所每日回填，歷史平均／百分位會隨樣本累積而變；滿一年前請把百分位當參考。",
        "回測無交易成本，Top5／Bottom5 以類股指數計算，實際用 ETF 或個股會有追蹤差。",
    ]
    return out


def run():
    px_df = load_index()
    if px_df.empty or BENCH not in px_df:
        raise RuntimeError("台股指數資料不存在（data/tw/tv/*.json）")
    flow = load_flow()
    reg = build_regime(px_df)
    panel = build_sectors(px_df, flow)
    return snapshot(px_df, reg, panel, flow), backtest(reg, panel, px_df)


if __name__ == "__main__":
    snap, bt = run()
    print(json.dumps({"asof": snap["asof"], "regime": snap["regime"]["label"], "score": snap["regime"]["score"],
                      "top": [s["symbol"] + s["name"] for s in snap["sectors"][:3]], "bottom": [s["symbol"] + s["name"] for s in snap["sectors"][-3:]],
                      "flow_days": snap["flows"]["history_days"]}, ensure_ascii=False))
