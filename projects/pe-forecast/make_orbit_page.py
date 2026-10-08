#!/usr/bin/env python3
"""本益比軌道模型的網頁：模型長什麼樣子、試算器、怎麼用、S&P 500／Nasdaq-100 回測報告、優勢與限制（README §17）。

    python3 make_orbit_page.py <輸出.html>

資料：results/now_all.csv（今天的股價、最近四季 EPS、殖利率、波動）、data/consensus_snapshots/ 最新的選股器快照（股價、GAAP 最近四季）
與 detail 快照（S&P 500＋科技＋Nasdaq-100 的分析師共識）、results/orbit_model.json（係數與區間）、results/orbit_index_*（回測）。
計算核心 web/orbit_core.js 和 pef/orbit.py 相同（web/test_orbit_core.py 對照）。
"""
import glob
import json
import math
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import consensus, orbit                         # noqa: E402

RES = os.path.join(HERE, "results")
SNAP = os.path.join(HERE, "data", "consensus_snapshots")


def num(v, nd=6):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if not math.isfinite(f) else round(f, nd)


def short_name(n):
    n = re.sub(r"\s+(Common Stock|Class [A-C] (Common|Ordinary|Capital) (Stock|Shares)|Ordinary Shares|American Depositary Shares.*|"
               r"Common Shares|Capital Stock)$", "", str(n or ""))
    return n.strip()[:60]


def tickers():
    n = pd.read_csv(os.path.join(RES, "now_all.csv"), parse_dates=["period_end", "price_date"])
    n = n[~n["too_old"].fillna(False).astype(bool) & (n["px"] > 0) & n["eps0"].notna() & n["y10"].notna()]
    sf = sorted(glob.glob(os.path.join(SNAP, "yahoo_2*.csv.gz")))
    df = sorted(glob.glob(os.path.join(SNAP, "yahoo_detail_*.csv.gz")))
    sn = pd.read_csv(sf[-1]).drop_duplicates("symbol").set_index("symbol") if sf else pd.DataFrame()
    dt = pd.read_csv(df[-1], parse_dates=["last_fy", "mrq"]).drop_duplicates("symbol").set_index("symbol") if df else pd.DataFrame()
    snap_time = pd.Timestamp(sn["asof_utc"].iloc[0]).tz_localize(None) if len(sn) else None
    out = []
    for r in n.to_dict("records"):
        sym = consensus.yahoo_symbol(r["ticker"])
        s = sn.loc[sym].to_dict() if sym in sn.index else None
        q = dt.loc[sym].to_dict() if sym in dt.index else None
        px, pdate = float(r["px"]), pd.Timestamp(r["price_date"])
        if s is not None and s.get("currency") == "USD" and num(s.get("regularMarketPrice")):
            px, pdate = float(s["regularMarketPrice"]), pd.Timestamp(int(s["regularMarketTime"]), unit="s").normalize()
        mrq = q["mrq"] if q is not None and pd.notna(q.get("mrq")) else None
        rf = consensus.refresh_eps(r, s, snap_time, mrq=mrq)
        c = None
        if q is not None and pd.notna(q.get("last_fy")) and num(q.get("0y_avg")) is not None:
            fy0 = pd.Timestamp(q["last_fy"]) + pd.DateOffset(months=12)
            gaap = num(s.get("epsTrailingTwelveMonths")) if s is not None else None
            st = num(q.get("street_ttm"))
            k = gaap / st if (gaap is not None and st and st > 0) else None
            rev = lambda a, b: (a / b - 1) if (a is not None and b not in (None, 0)) else None
            c = dict(f0=str(fy0.date()), f1=str((fy0 + pd.DateOffset(months=12)).date()), c0=num(q.get("0y_avg"), 4),
                     c1=num(q.get("+1y_avg"), 4), k=num(k, 4), n0=num(q.get("0y_n"), 0), n1=num(q.get("+1y_n"), 0),
                     r0=num(rev(num(q.get("0y_avg")), num(q.get("0y_d90"))), 4), r1=num(rev(num(q.get("+1y_avg")), num(q.get("+1y_d90"))), 4),
                     d=str(q["asof_utc"])[:10])
        out.append(dict(t=r["ticker"], n=short_name(r.get("name")), g=orbit.group_of(r.get("sector")), px=round(px, 4),
                        d=str(pdate.date()), e=num(rf["eps0"], 4), q=str(pd.Timestamp(rf["period_end"]).date()),
                        y=num(r["y10"], 5), dy=num(r.get("dy"), 5) or 0, v=num(r.get("vol36"), 4),
                        sp=bool(r.get("in_sp500")), nd=bool(r.get("in_ndx")), u=int(rf["n_new"]), c=c))
    out.sort(key=lambda x: (not x["sp"] and not x["nd"], x["t"]))
    return out, (str(snap_time.date()) if snap_time is not None else None)


def backtest():
    sc = pd.read_csv(os.path.join(RES, "orbit_index_scores.csv"))
    sc["模型"] = sc["＋你的EPS(a)"].fillna(sc.get("模型"))
    keep = ["h", "期間", "指數", "類型", "樣本", "家數", "n", "本益比不變", "軌道", "模型", "＋你的EPS(a,b)", "＋共識代理＋你的EPS",
            "本益比不變_±20%", "軌道_±20%", "＋你的EPS(a)_±20%", "命中20_模型", "股價偏離軌道中位"]
    sc = sc[[c for c in keep if c in sc]]
    yrs = pd.read_csv(os.path.join(RES, "orbit_index_years.csv"))
    bands = pd.read_csv(os.path.join(RES, "orbit_index_bands.csv"))
    noise = pd.read_csv(os.path.join(RES, "orbit_index_epsnoise.csv"))
    firms = pd.read_csv(os.path.join(RES, "orbit_index_firms.csv"))
    fs = []
    for gname, g in firms.groupby("指數"):
        g = g.sort_values("model")
        fs.append(dict(指數=gname, 家數=len(g), 勝不變=float((g["model"] < g["unch"]).mean()), 勝軌道=float((g["model"] < g["orbit"]).mean()),
                       最準=[[t, round(v, 3)] for t, v in zip(g["ticker"].head(6), g["model"].head(6))],
                       最不準=[[t, round(v, 3)] for t, v in zip(g["ticker"].tail(6)[::-1], g["model"].tail(6)[::-1])],
                       類型={k: dict(模型=round(float(d["model"].median()), 3), 不變=round(float(d["unch"].median()), 3), 家數=len(d))
                           for k, d in g.groupby("grp")}))
    rec = lambda d: json.loads(d.to_json(orient="records", force_ascii=False, double_precision=5))
    return dict(scores=rec(sc), years=rec(yrs), bands=rec(bands), noise=rec(noise), firms=fs)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "artifact", "orbit.html")
    model = json.load(open(os.path.join(RES, "orbit_model.json")))
    slim = dict(version=model["version"], fit_cutoff=model["fit_cutoff"], erp=model["erp"], alpha=model["alpha"],
                vol_clip=model["vol_clip"], loss_widen=model["loss_widen"],
                h={h: dict(pair=v["pair"], beta=v["beta"], bands={k: dict(q=b["q"], vol_median=b["vol_median"]) for k, b in v["bands"].items()})
                   for h, v in model["h"].items()})
    tk, snap_date = tickers()
    data = dict(model=slim, tickers=tk, snap=snap_date, bt=backtest())
    core = open(os.path.join(HERE, "web", "orbit_core.js")).read()
    tpl = open(os.path.join(HERE, "web", "orbit_page.html")).read()
    html = (tpl.replace("/*__CORE__*/", core)
               .replace("/*__DATA__*/", "const DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w").write(html)
    print(f"{len(tk):,} 檔（有共識 {sum(1 for x in tk if x['c']):,}；EPS 用 Yahoo 更新 {sum(1 for x in tk if x['u']):,}）→ {out}"
          f"（{len(html) / 1e6:.2f} MB）")


if __name__ == "__main__":
    main()
