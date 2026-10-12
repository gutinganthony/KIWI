#!/usr/bin/env python3
"""本益比軌道模型的網頁：模型長什麼樣子、試算器、怎麼用、S&P 500／Nasdaq-100 回測報告、優勢與限制（README §17）。

    python3 make_orbit_page.py <輸出.html>

資料：results/now_all.csv（今天的股價、最近四季 EPS、殖利率、波動）、data/consensus_snapshots/ 最新的選股器快照（股價、GAAP 最近四季）
與 detail 快照（S&P 500＋科技＋Nasdaq-100 的分析師共識）、results/orbit_model.json（係數與區間）、results/orbit_index_*（回測）；
第二輪優化（README §19）：共識校正模型（pef/eps_correct.py）、外國 ADR（data/adr_now.csv）、利率情境（results/rate_sensitivity.json）、
區間放寬（results/band_widen.json）、實驗結果（results/eps_correction_scores.csv、orbit_factors_*、orbit_small_scores.csv）。
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
from pef import consensus, eps_correct, orbit            # noqa: E402

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
    y_new, _ = orbit.latest_y10()                                   # 軌道的資金成本用最新的 10 年期（now_all 的是落後的月平均）
    out = []
    for r in n.to_dict("records"):
        if y_new is not None:
            r["y10"] = y_new
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
            r2 = dict(r, px=px, eps0=rf["eps0"])
            big = bool(r.get("in_sp500")) or bool(r.get("in_ndx"))        # 中小型股：距離年報 ≥ 9 個月不校正（README §20.3）
            cr = eps_correct.for_ticker(r["ticker"], r2, num(q.get("0y_avg")), fy0, num(q.get("0y_d30")), num(q.get("0y_d90")), q["last_fy"],
                                        today=pd.Timestamp(q["asof_utc"]).tz_localize(None).normalize(), scope="big" if big else "small")
            if cr is not None and cr["small_note"]:
                c["cg"] = cr["small_note"]
                cr = None
            if cr is not None:                                    # 共識校正（README §19.1）：預設的共識係數
                c["cf"] = num(cr["factor"], 4)
                c["cl"] = num(cr["feats"]["lead"], 1)
                c["cx"] = "、".join(f"{n_} {e:+.2f}" for n_, _, e in cr["drivers"])
                if cr["guard"] and abs(cr["factor"] - cr["factor_tree"]) > 1e-6:
                    c["cg"] = cr["guard"]
        out.append(dict(t=r["ticker"], n=short_name(r.get("name")), g=orbit.group_of(r.get("sector")), px=round(px, 4),
                        d=str(pdate.date()), e=num(rf["eps0"], 4), q=str(pd.Timestamp(rf["period_end"]).date()),
                        y=num(r["y10"], 5), dy=num(r.get("dy"), 5) or 0, v=num(r.get("vol36"), 4),
                        sp=bool(r.get("in_sp500")), nd=bool(r.get("in_ndx")), u=int(rf["n_new"]), c=c,
                        pr=num(orbit.pe_rank(px, rf["eps0"]), 3), bw=None if (r.get("in_sp500") or r.get("in_ndx")) else "small"))
    have = {x["t"] for x in out}
    ap = os.path.join(HERE, "data", "adr_now.csv")
    if os.path.exists(ap):                                         # 外國公司 ADR（口徑檢查通過的；每 ADR 美元）
        a = pd.read_csv(ap, parse_dates=["period_end", "price_date", "last_fy"])
        for r in a[a["conv_ok"].astype(bool) & (a["px"] > 0) & a["eps0"].notna()].to_dict("records"):
            if r["ticker"] in have:
                continue
            fy0 = pd.Timestamp(r["last_fy"]) + pd.DateOffset(months=12) + pd.offsets.MonthEnd(0)
            c = None
            if num(r.get("cons_0y")) is not None:
                c = dict(f0=str(fy0.date()), f1=str((fy0 + pd.DateOffset(months=12) + pd.offsets.MonthEnd(0)).date()), c0=num(r["cons_0y"], 4),
                         c1=num(r.get("cons_1y"), 4), k=None, n0=None, n1=None, r0=None, r1=None, d=str(r["price_date"].date()))
            out.append(dict(t=r["ticker"], n=short_name(r.get("name")), g=r["grp"] if r["grp"] in orbit.GNAME else "other", px=round(float(r["px"]), 4),
                            d=str(r["price_date"].date()), e=num(r["eps0"], 4), q=str(r["period_end"].date()), y=num(r["y10"], 5),
                            dy=num(r.get("dy"), 5) or 0, v=num(r.get("vol36"), 4), sp=False, nd=False, u=0, c=c,
                            pr=num(orbit.pe_rank(float(r["px"]), float(r["eps0"])), 3), bw="adr", adr=True))
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
    cp = os.path.join(RES, "orbit_consensus_scores.csv")
    cons = rec(pd.read_csv(cp)) if os.path.exists(cp) else []
    return dict(scores=rec(sc), years=rec(yrs), bands=rec(bands), noise=rec(noise), firms=fs, cons=cons)


def opt():
    """第二輪優化實驗（README §19）的結果表。"""
    rec = lambda d: json.loads(d.to_json(orient="records", force_ascii=False, double_precision=4))
    e = pd.read_csv(os.path.join(RES, "eps_correction_scores.csv"))
    pe = e[e["表"] == "PE"][["期間", "群組", "n", "本益比不變", "原樣", "過去偏差", "樹（今天的線索）", "EPS完全正確"]]
    ep = e[e["表"] == "EPS"][["樣本", "n", "原樣", "過去偏差", "樹（今天的線索）"]]
    cs = pd.read_csv(os.path.join(RES, "orbit_factors_cs.csv"))
    cs = cs[cs["群組"] == "全部"]
    keep = [c for c in cs.columns if c.endswith("｜橫斷面")]
    cs = cs[["期間", "n"] + keep].rename(columns={c: c.replace("｜橫斷面", "") for c in keep})
    mk = pd.read_csv(os.path.join(RES, "orbit_factors_mkt.csv"))
    sm = pd.read_csv(os.path.join(RES, "orbit_small_scores.csv"))
    sm = sm[(sm["期間"] == "全期")][["h", "指數", "n", "家數", "本益比不變", "軌道", "模型", "80%涵蓋", "80%涵蓋_扣大盤"]]
    lg = pd.read_csv(os.path.join(RES, "eps_correction_logic.csv"))
    lg = lg[lg["線索"].isin(["cons_g", "past_bias", "rev3", "ret12", "ltg", "acc"])][["線索", "預期方向", "期間", "n", "Q1", "Q5", "Q5減Q1"]]
    return dict(pe=rec(pe), eps=rec(ep), logic=rec(lg), cs=rec(cs), mkt=rec(mk), small=rec(sm),
                rate=json.load(open(os.path.join(RES, "rate_sensitivity.json")))["regimes"],
                widen={k: v["h"] for k, v in json.load(open(os.path.join(RES, "band_widen.json"))).items()},
                cmeta=json.load(open(os.path.join(RES, "eps_correction_model.json")))["n_train"])


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "artifact", "orbit.html")
    model = orbit.load_model(RES)
    slim = dict(version=model["version"], fit_cutoff=model["fit_cutoff"], erp=model["erp"], alpha=model["alpha"],
                vol_clip=model["vol_clip"], loss_widen=model["loss_widen"], loss_beta=model.get("loss_beta"), turn_widen=model.get("turn_widen"),
                h={h: dict(pair=v["pair"], beta=v["beta"], bands={k: dict(q=b["q"], vol_median=b["vol_median"]) for k, b in v["bands"].items()})
                   for h, v in model["h"].items()})
    tk, snap_date = tickers()
    data = dict(model=slim, tickers=tk, snap=snap_date, bt=backtest(), opt=opt())
    core = open(os.path.join(HERE, "web", "orbit_core.js")).read()
    tpl = open(os.path.join(HERE, "web", "orbit_page.html")).read()
    html = (tpl.replace("/*__CORE__*/", core)
               .replace("/*__DATA__*/", "const DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w").write(html)
    print(f"{len(tk):,} 檔（有共識 {sum(1 for x in tk if x['c']):,}，其中有校正係數 {sum(1 for x in tk if x['c'] and x['c'].get('cf')):,}；"
          f"外國 ADR {sum(1 for x in tk if x.get('adr')):,}；EPS 用 Yahoo 更新 {sum(1 for x in tk if x['u']):,}）→ {out}"
          f"（{len(html) / 1e6:.2f} MB）")


if __name__ == "__main__":
    main()
