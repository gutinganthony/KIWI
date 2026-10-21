#!/usr/bin/env python3
"""
risk_board_backtest.py — 崩盤風險對照台的 30 年驗證：①有沒有提前預警大跌 ②照它進出場的年化報酬

方法（避免偷看未來）：
- 指標全用「當天收盤以前就拿得到」的資料；月資料（CPI、CAPE）延後 1.5 個月才生效。
- 訊號以收盤判定、次一交易日起換倉；現金部位用 3 個月國庫券利率（^IRX）計息；每次進出扣 0.10%。
- 門檻沿用 docs/risk/index.html 的燈號門檻，不另外調參。對照台上以「絕對水位」設定的燈（10 年期 5%、
  油價 90 美元…）放到 30 年會失真，改成「變化量」版本（10 年期 12 個月變化、油價 12 個月漲幅）。

資料（全部免金鑰）：Yahoo ^GSPC／SPY／^VIX／^VIX3M／^SKEW／^SOX／^MOVE／^TNX／^IRX／VWEHX／CL=F／JPY=X，
CPI（datasets/cpi-us），CAPE（datasets/s-and-p-500，2023-09 之後以 10 年平均盈餘的幾何內插延伸），
CRI（data/backtest/cri_history_30yr.csv ＋ cri_history_ext.csv）。
FRED 在部分 session 會被擋，所以這支腳本刻意不依賴 FRED（NFCI、CCC 利差因此不納入）。

用法：python scripts/risk_board_backtest.py [--cache DIR]
輸出：data/backtest/risk_board_backtest.json
"""
import argparse, json, os, sys, urllib.request
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(ROOT))
BT = os.path.join(ROOT, "data", "backtest")
OUT = os.path.join(BT, "risk_board_backtest.json")
COST = 0.001
START = "1997-01-02"

# 燈號門檻：(注意, 警戒, 方向)  方向 +1＝越大越危險，−1＝越小越危險
TH = {
    "y10_chg":   (0.75, 1.25, +1),   # 10 年期殖利率 12 個月變化（pp）
    "gap":       (2.0, 3.5, +1),     # 10 年期 − CAPE 盈餘殖利率（pp）
    "real_rate": (1.2, 2.0, +1),     # 3 個月國庫券 − CPI 年增率（%）
    "bill_chg":  (0.75, 1.5, +1),    # 3 個月國庫券 12 個月變化（升息力道）
    "oil_chg":   (30, 60, +1),       # 原油 12 個月漲幅（%）
    "jpy_3m":    (-4, -7, -1),       # USD/JPY 3 個月變化（%，負＝日圓升值）
    "credit_dd": (-3, -6, -1),       # 高收益債基金 VWEHX 距一年高點（%）
    "vix_term":  (0.95, 1.05, +1),   # VIX ÷ VIX3M
    "skew":      (140, 150, +1),     # SKEW
    "sox_dd":    (-10, -20, -1),     # 費城半導體距一年高點（%）
    "move":      (110, 140, +1),     # MOVE 債市波動率
    "cri":       (35, 50, +1),       # KIWI CRI
}
MACRO = ["y10_chg", "gap", "real_rate", "bill_chg", "oil_chg", "jpy_3m"]
MARKET = ["credit_dd", "vix_term", "skew", "sox_dd", "move", "cri", "ma"]


def yahoo(tk, cache, adj=True):
    p = os.path.join(cache, f"y_{urllib.request.quote(tk)}.json") if cache else None
    if p and os.path.exists(p):
        raw = open(p, "rb").read()
    else:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(tk)}?period1=-1325635200&period2=4102444800&interval=1d"
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
        if p:
            open(p, "wb").write(raw)
    r = json.loads(raw)["chart"]["result"][0]
    q = r["indicators"]
    v = (q.get("adjclose", [{}])[0].get("adjclose") if adj else None) or q["quote"][0]["close"]
    s = pd.Series(v, index=pd.to_datetime(r["timestamp"], unit="s").normalize(), dtype=float)
    return s.dropna().groupby(level=0).last()


def gh_csv(url, cache, name):
    p = os.path.join(cache, name) if cache else None
    if p and os.path.exists(p):
        return pd.read_csv(p)
    raw = urllib.request.urlopen(url, timeout=60).read()
    if p:
        open(p, "wb").write(raw)
    return pd.read_csv(pd.io.common.BytesIO(raw))


def status(x, warn, hot, d):
    if d > 0:
        return np.where(np.isnan(x), np.nan, np.where(x >= hot, 2, np.where(x >= warn, 1, 0)))
    return np.where(np.isnan(x), np.nan, np.where(x <= hot, 2, np.where(x <= warn, 1, 0)))


def auc(score, y):
    m = ~(np.isnan(score) | np.isnan(y))
    s, y = score[m], y[m].astype(bool)
    r = pd.Series(s).rank().values
    n1, n0 = y.sum(), (~y).sum()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else None


def perf(ret, cash, w, idx):
    w = pd.Series(w, index=idx).shift(1).fillna(1.0)          # 收盤訊號 → 次日部位
    turn = w.diff().abs().fillna(0)
    r = w * ret + (1 - w) * cash - turn * COST
    eq = (1 + r).cumprod()
    yrs = (idx[-1] - idx[0]).days / 365.25
    ex = r - cash
    return {"cagr": round((eq.iloc[-1] ** (1 / yrs) - 1) * 100, 2),
            "mdd": round((eq / eq.cummax() - 1).min() * 100, 1),
            "vol": round(r.std() * np.sqrt(252) * 100, 1),
            "sharpe": round(ex.mean() / ex.std() * np.sqrt(252), 2) if ex.std() else None,
            "out_pct": round((w < 0.999).mean() * 100, 0),
            "switches": int((turn > 0.25).sum())}, eq


def hysteresis(enter_out, enter_in, n=len):
    st, w = 1.0, []
    for o, i in zip(enter_out, enter_in):
        if st == 1.0 and o:
            st = 0.0
        elif st == 0.0 and i:
            st = 1.0
        w.append(st)
    return np.array(w)


def build_board(C=None, live_cri=True, start="1994-01-01"):
    """組出每日的對照台分數。回傳 (D 指標＋分數, st 各燈 0/1/2, spy, ser)。
    回測與每日管線（risk_dashboards_data.py）共用這一份定義，避免兩邊門檻不一致。
    live_cri=True 時，docs/history.json 的即時 CRI（含信用/利率指標）會覆蓋同日期的回測版 CRI。"""
    if C:
        os.makedirs(C, exist_ok=True)

    spx = yahoo("^GSPC", C, adj=False)
    spy = yahoo("SPY", C)
    ser = {k: yahoo(t, C, adj=(k == "vwehx")) for k, t in
           {"vix": "^VIX", "vix3m": "^VIX3M", "skew": "^SKEW", "sox": "^SOX", "move": "^MOVE", "tnx": "^TNX",
            "irx": "^IRX", "vwehx": "VWEHX", "cl": "CL=F", "jpy": "JPY=X"}.items()}
    cpi = gh_csv("https://raw.githubusercontent.com/datasets/cpi-us/main/data/cpiai.csv", C, "cpi.csv")
    cpi = pd.Series(cpi["Index"].values, index=pd.to_datetime(cpi["Date"]))
    cpi_yoy = (cpi / cpi.shift(12) - 1) * 100
    cpi_yoy.index = cpi_yoy.index + pd.DateOffset(months=1, days=14)       # 公布延遲
    sh = gh_csv("https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv", C, "shiller.csv")
    sh = sh[sh["PE10"] > 0]
    cape = pd.Series(sh["PE10"].values, index=pd.to_datetime(sh["Date"]))
    # 2023-09 之後：10 年平均盈餘 E10 在「最後一筆 Shiller」與「KIWI 儀表板現值」之間幾何內插，CAPE＝價格÷E10
    now_cape = json.load(open(os.path.join(REPO, "docs", "risk", "data.json"), encoding="utf-8"))["now"]["cape"]
    last_d, last_c = cape.index[-1], cape.iloc[-1]
    e0 = spx[:last_d + pd.offsets.MonthEnd(0)].iloc[-1] / last_c
    e1 = spx.iloc[-1] / now_cape
    mon = pd.date_range(last_d + pd.DateOffset(months=1), spx.index[-1], freq="MS")
    tot = (spx.index[-1] - last_d).days
    ext = {d: spx[:d + pd.offsets.MonthEnd(0)].iloc[-1] / (e0 * (e1 / e0) ** ((d - last_d).days / tot)) for d in mon}
    cape = pd.concat([cape, pd.Series(ext)])
    cape.index = cape.index + pd.DateOffset(months=1)                          # 月資料延後 1 個月
    cri = pd.concat([pd.read_csv(os.path.join(BT, f), parse_dates=["date"]).set_index("date")["score"]
                     for f in ("cri_history_30yr.csv", "cri_history_ext.csv")])
    if live_cri:
        try:
            h = json.load(open(os.path.join(REPO, "docs", "history.json"), encoding="utf-8"))
            live = pd.Series(h["c"], index=pd.to_datetime(h["d"]), dtype=float).dropna()
            cri = pd.concat([cri, live])
        except Exception as e:
            print(f"  ⚠️ 即時 CRI 讀不到，只用回測版：{e}", file=sys.stderr)
    cri = cri[~cri.index.duplicated(keep="last")].sort_index()

    idx = spx.index[spx.index >= start]
    f = lambda s: s.reindex(idx.union(s.index)).ffill().reindex(idx)
    D = pd.DataFrame(index=idx)
    D["spx"] = spx.reindex(idx)
    ma = spx.rolling(200).mean().reindex(idx)
    D["ma"] = (D.spx / ma - 1) * 100
    tnx, irx = f(ser["tnx"]), f(ser["irx"])
    D["y10_chg"] = tnx - tnx.shift(252)
    D["gap"] = tnx - 100 / f(cape)
    D["real_rate"] = irx - f(cpi_yoy)
    D["bill_chg"] = irx - irx.shift(252)
    cl = ser["cl"]; D["oil_chg"] = f((cl / cl.shift(252) - 1) * 100)
    jp = ser["jpy"]; D["jpy_3m"] = f((jp / jp.shift(63) - 1) * 100)
    vw = ser["vwehx"]; D["credit_dd"] = f((vw / vw.rolling(252).max() - 1) * 100)
    D["vix_term"] = f(ser["vix"] / ser["vix3m"])
    D["skew"] = f(ser["skew"])
    sx = ser["sox"]; D["sox_dd"] = f((sx / sx.rolling(252).max() - 1) * 100)
    D["move"] = f(ser["move"])
    D["cri"] = f(cri)

    st = pd.DataFrame(index=idx)
    for k, (w_, h_, d_) in TH.items():
        st[k] = status(D[k].values, w_, h_, d_)
    st["ma"] = np.where(D["ma"].isna(), np.nan, np.where(D["ma"] < 0, 2, 0))
    def board(cols):
        s = st[cols]
        return (s.sum(axis=1, min_count=1) / (2 * s.notna().sum(axis=1)) * 100)
    D["board"] = board(list(TH) + ["ma"])
    D["board_macro"] = board(MACRO)
    D["board_market"] = board(MARKET)
    return D, st, spy, ser


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cache"); a = ap.parse_args()
    C = a.cache
    if C:
        os.makedirs(C, exist_ok=True)
    D, st, spy, ser = build_board(C, live_cri=False)
    idx = D.index
    f = lambda s: s.reindex(idx.union(s.index)).ffill().reindex(idx)
    D = D[D.index >= START]
    st = st[st.index >= START]

    # ─── ① 預警能力 ──────────────────────────────────────────────────────────
    px = D.spx.values
    n = len(px)
    fwd = np.full(n, np.nan)
    for i in range(n - 63):
        fwd[i] = px[i + 1:i + 64].min() / px[i] - 1
    D["fwd_dd"] = fwd * 100
    y = (D.fwd_dd <= -10).astype(float).where(D.fwd_dd.notna())
    base = float(y.mean())
    horizons = {"3 個月內跌 10%": (63, -0.10), "6 個月內跌 15%": (126, -0.15), "12 個月內跌 20%": (252, -0.20)}
    labels = {}
    for hn, (h, thr) in horizons.items():
        fd = np.full(n, np.nan)
        for i in range(n - h):
            fd[i] = px[i + 1:i + h + 1].min() / px[i] - 1
        labels[hn] = pd.Series(np.where(np.isnan(fd), np.nan, (fd <= thr).astype(float)), index=D.index)
    pred = {"_base_rates": {hn: round(float(lb.mean()) * 100, 1) for hn, lb in labels.items()}}
    for name, s in {"對照台總分": D.board, "總體分項（慢）": D.board_macro, "市場分項（快）": D.board_market,
                    "CRI 單獨": D.cri, "跌破 200 日線（負距離）": -D.ma}.items():
        pred[name] = {hn: round(auc(s.values, lb.values), 3) for hn, lb in labels.items()}
    for T in (30, 35, 40, 45, 50):
        m = D.board >= T
        pred[f"總分≥{T}"] = {"days_pct": round(m.mean() * 100, 1),
                             "precision": round(float(y[m].mean()) * 100, 1) if m.any() else None,
                             "recall": round(float(m[y == 1].mean()) * 100, 1),
                             "lift": round(float(y[m].mean()) / base, 2) if m.any() else None}
    # 事件：15% 波段（zigzag）——高點後跌 15% 確認為一次下跌，低點後漲 15% 才算結束；能抓到大空頭裡的分段下跌
    events, mode, hi_i, lo_i = [], "up", 0, 0
    for i in range(1, n):
        if mode == "up":
            if px[i] > px[hi_i]:
                hi_i = i
            elif px[i] / px[hi_i] - 1 <= -0.15:
                mode, lo_i = "down", i
        else:
            if px[i] < px[lo_i]:
                lo_i = i
            elif px[i] / px[lo_i] - 1 >= 0.15:
                seg = px[hi_i:lo_i + 1]
                c10 = hi_i + int(np.argmax(seg / px[hi_i] - 1 <= -0.10))
                events.append((hi_i, c10, lo_i, None))
                mode, hi_i = "up", i
    if mode == "down":
        seg = px[hi_i:lo_i + 1]
        events.append((hi_i, hi_i + int(np.argmax(seg / px[hi_i] - 1 <= -0.10)), lo_i, None))
    pct = D.board.rank(pct=True) * 100
    ev_rows = []
    for pk, c10, tr, rec in events:
        win = D.board.iloc[max(0, pk - 126):c10 + 1]
        def first(T):
            hit = win[win >= T]
            return None if hit.empty else int(D.index.get_loc(hit.index[0]) - pk)
        cri_w = D.cri.iloc[max(0, pk - 126):c10 + 1]
        cri_hit = cri_w[cri_w >= 50]
        ev_rows.append({
            "peak": D.index[pk].date().isoformat(), "cross10": D.index[c10].date().isoformat(),
            "trough": D.index[tr].date().isoformat(), "max_dd": round((px[tr] / px[pk] - 1) * 100, 1),
            "days_peak_to_cross10": int(c10 - pk),
            "board_at_peak": round(float(D.board.iloc[pk]), 0),
            "board_max_60d_before_peak": round(float(D.board.iloc[max(0, pk - 60):pk + 1].max()), 0),
            "board_at_cross10": round(float(D.board.iloc[c10]), 0),
            "board_pctile_avg_60d_before_peak": round(float(pct.iloc[max(0, pk - 60):pk + 1].mean()), 0),
            "board_pctile_at_cross10": round(float(pct.iloc[c10]), 0),
            "first_board35_vs_peak": first(35), "first_board45_vs_peak": first(45),
            "first_cri50_vs_peak": None if cri_hit.empty else int(D.index.get_loc(cri_hit.index[0]) - pk),
        })

    # ─── ② 進出場回測 ────────────────────────────────────────────────────────
    ret = spy.pct_change().reindex(D.index).fillna(0)
    cash = (f(ser["irx"]).reindex(D.index) / 100 / 252).fillna(0)
    bd, mad, cr = D.board.values, D.ma.values, D.cri.values
    calm = lambda arr, T: pd.Series(arr < T).rolling(10).sum().values == 10
    strategies = {
        "買進持有": np.ones(len(D)),
        "只看 200 日線": hysteresis(mad < 0, mad > 0),
        "規則 3（CRI≥50 且跌破 200 日線）": hysteresis((cr >= 50) & (mad < 0), calm(cr, 35) & (mad > 0)),
    }
    for H in (35, 40, 45, 50):
        strategies[f"對照台總分≥{H} 出場"] = hysteresis(bd >= H, calm(bd, H - 10))
    for H in (30, 35, 40):
        strategies[f"總分≥{H} 且跌破 200 日線"] = hysteresis((bd >= H) & (mad < 0), calm(bd, H - 5) & (mad > 0))
    strategies["分數漸進減碼（20→0%、60→全出）"] = np.clip(1 - (np.nan_to_num(bd) - 20) / 40, 0, 1)

    # 2 倍槓桿（借款利率＝國庫券利率）：出場時整個部位轉現金
    lev = {}
    for name in ["買進持有", "規則 3（CRI≥50 且跌破 200 日線）", "對照台總分≥35 出場", "總分≥35 且跌破 200 日線"]:
        w = pd.Series(strategies[name], index=D.index).shift(1).fillna(1)
        r2 = w * (2 * ret - cash) + (1 - w) * cash - w.diff().abs().fillna(0) * COST * 2
        eq = (1 + r2).cumprod(); yrs = (D.index[-1] - D.index[0]).days / 365.25
        lev[name] = {"cagr": round((eq.iloc[-1] ** (1 / yrs) - 1) * 100, 2), "mdd": round((eq / eq.cummax() - 1).min() * 100, 1)}

    periods = {"全期 1997–2026": (START, None), "前半 1997–2011": (START, "2011-12-31"),
               "後半 2012–2026": ("2012-01-01", None), "CRI 樣本外 2020/4–2026": ("2020-04-02", None)}
    bt = {}
    for name, w in strategies.items():
        bt[name] = {}
        for pn, (a0, a1) in periods.items():
            m = (D.index >= a0) & ((D.index <= a1) if a1 else True)
            res, _ = perf(ret[m], cash[m], w[m], D.index[m])
            bt[name][pn] = res
    # 大空頭年份
    yearly = {}
    for name in ["買進持有", "只看 200 日線", "規則 3（CRI≥50 且跌破 200 日線）", "對照台總分≥40 出場",
                 "總分≥35 且跌破 200 日線"]:
        w = pd.Series(strategies[name], index=D.index).shift(1).fillna(1)
        r = w * ret + (1 - w) * cash - w.diff().abs().fillna(0) * COST
        yr = (1 + r).groupby(D.index.year).prod() - 1
        yearly[name] = {int(k): round(v * 100, 1) for k, v in yr.items() if k in (2000, 2001, 2002, 2008, 2011, 2015, 2018, 2020, 2022, 2025, 2026)}

    latest = {"date": D.index[-1].date().isoformat(), "board": round(float(D.board.iloc[-1]), 1),
              "board_macro": round(float(D.board_macro.iloc[-1]), 1),
              "board_market": round(float(D.board_market.iloc[-1]), 1),
              "lights": {k: (None if np.isnan(v) else int(v)) for k, v in st.iloc[-1].items()},
              "values": {k: (None if pd.isna(D[k].iloc[-1]) else round(float(D[k].iloc[-1]), 2)) for k in list(TH) + ["ma"]},
              "board_pct_rank": round(float((D.board <= D.board.iloc[-1]).mean() * 100), 1)}
    hist_board = D.board.resample("W").last().dropna()
    out = {"generated": pd.Timestamp.today().date().isoformat(), "period": [START, D.index[-1].date().isoformat()],
           "base_rate_fwd63_dd10": round(base * 100, 1), "prediction": pred, "events": ev_rows,
           "backtest": bt, "yearly": yearly, "lev2x": lev, "latest": latest, "thresholds": TH,
           "board_weekly": [[d.date().isoformat(), round(float(v), 1)] for d, v in hist_board.items()],
           "spx_weekly": [[d.date().isoformat(), round(float(v), 1)] for d, v in D.spx.resample("W").last().dropna().items()]}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 公開頁用（docs/risk/backtest.json）：只有市場數據與回測結果，沒有持倉
    json.dump(out, open(os.path.join(REPO, "docs", "risk", "backtest.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(json.dumps({k: out[k] for k in ("period", "base_rate_fwd63_dd10", "prediction", "latest")}, ensure_ascii=False, indent=1))
    print("\n事件：")
    for e in ev_rows:
        print(e)
    print("\n回測：")
    for name, v in bt.items():
        print(f"{name:34s}", " | ".join(f"{p[:6]} {r['cagr']:5.2f}%/{r['mdd']:6.1f}%/S{r['sharpe']}/out{r['out_pct']:.0f}%/{r['switches']}x" for p, r in v.items()))
    print("\n大空頭年份：")
    for k, v in yearly.items():
        print(f"{k:34s}", v)


if __name__ == "__main__":
    main()
