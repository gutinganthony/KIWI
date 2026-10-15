#!/usr/bin/env python3
"""本益比軌道模型的網頁：模型長什麼樣子、試算器、怎麼用、S&P 500／Nasdaq-100 回測報告、優勢與限制（README §17）。

    python3 make_orbit_page.py <輸出.html>

資料：results/now_all.csv（今天的股價、最近四季 EPS、殖利率、波動）、data/consensus_snapshots/ 最新的選股器快照（股價、GAAP 最近四季）
與 detail 快照（S&P 500＋科技＋Nasdaq-100 的分析師共識）、results/orbit_model.json（係數與區間）、results/orbit_index_*（回測）；
第二輪優化（README §19）：共識校正模型（pef/eps_correct.py）、外國 ADR（data/adr_now.csv）、利率情境（results/rate_sensitivity.json）、
區間放寬（results/band_widen.json）、實驗結果（results/eps_correction_scores.csv、orbit_factors_*、orbit_small_scores.csv）。
第十輪（README §26）：統一模型（pef/unified.py）、共識模式的 conformal 區間（results/conformal.json）、相對大盤（results/relative_dist.json，這裡算）。
計算核心 web/orbit_core.js 和 pef/orbit.py、pef/unified.py 相同（web/test_orbit_core.py 對照）。
"""
import glob
import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import consensus, eps_correct, orbit            # noqa: E402
from pef import growth_price, unified                    # noqa: E402

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
                        sp=bool(r.get("in_sp500")), nd=bool(r.get("in_ndx")), u=int(rf["n_new"]), c=c, r=num(r.get("ret12"), 4),
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
                            r=num(growth_price.adr_ret12(r["ticker"], float(r["px"]), r["price_date"]), 4),   # 成長定價用
                            pr=num(orbit.pe_rank(float(r["px"]), float(r["eps0"])), 3), bw="adr", adr=True))
    out.sort(key=lambda x: (not x["sp"] and not x["nd"], x["t"]))
    return out, (str(snap_time.date()) if snap_time is not None else None)


def cons_for(t, h, k_user=None):
    """網頁 consFor 的 Python 版（web/test_orbit_core.py 對照）：預設共識係數 k0（校正模型 cf ＞ 中小型股不校正 cg ＞ 口徑係數 k）；
    係數先乘在會計年度共識上，再換算成目標日的最近四季（可外推）。回傳 dict(a=(eps, how)|None, b=…, k, k0, cf, k_bad) 或 None。"""
    c = t.get("c")
    if not c or c.get("c0") is None:
        return None
    asof, last_q = pd.Timestamp(t["d"]), pd.Timestamp(t["q"])
    kraw = c.get("k")
    k_ok = kraw is not None and 0.4 <= kraw <= 1.15
    cf = c.get("cf") if (c.get("cf") is not None and math.isfinite(c.get("cf"))) else None
    k_bad = cf is None and kraw is not None and not k_ok
    k0 = cf if cf is not None else 1 if c.get("cg") else (kraw if (k_ok and abs(kraw - 1) > 0.03) else 1)
    same = k_user is not None and abs(k_user - round(k0 * 100) / 100) < 1e-9
    k = k_user if (k_user is not None and math.isfinite(k_user) and k_user > 0 and not same) else k0
    fy = {pd.Timestamp(c["f0"]): c["c0"] * k}
    if c.get("c1") is not None:
        fy[pd.Timestamp(c["f1"])] = c["c1"] * k
    a = orbit.calendarize(fy, asof + pd.DateOffset(months=h), last_q, t["e"], extrapolate=True)
    b = orbit.calendarize(fy, asof + pd.DateOffset(months=h + 12), last_q, t["e"], extrapolate=True)
    return dict(a=a if a[0] is not None else None, b=b if b[0] is not None else None, k=k, k0=k0, cf=cf, k_bad=k_bad)


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


def slim_cq(cq):
    if not cq:
        return None
    return dict(min_n=cq["min_n"], cutoff=cq["cutoff"],
                h={h: dict(vol_median=v["vol_median"], n=v["n"], wf_cover80=v["wf_cover80"].get("全部校準"), wf_min=min(v["wf_by_year"].values()),
                           **{k: dict(n=v[k]["n"], q=v[k]["q"]) for k in ("pooled", "tech", "other")}) for h, v in cq["h"].items()})


def lab_numbers():
    """results/unified_lab.txt（research/unified_lab.py）的幾個數字，給網頁與命令列的註解用：每個 h 的 C／A／B／A1 表「全部」列、相對誤差、Spearman。"""
    p = os.path.join(RES, "unified_lab.txt")
    if not os.path.exists(p):
        return None
    parts = re.split(r"=+ (\d+) 個月：", open(p).read())
    out = {}
    for h, blk in zip(parts[1::2], parts[2::2]):
        d = {}
        for key in ("C", "A", "B", "A1"):
            m = re.search(r"-- " + key + r" [^\n]*\n[^\n]*\n\s*全部\s+n=\s*\d+((?:\s+[\d.]+)+)", blk)
            d[key] = [float(v) for v in m.group(1).split()] if m else None
        m = re.search(r"相對誤差（扣同月中位）：統一 ([\d.]+)（絕對 ([\d.]+)）；本益比不變 ([\d.]+)（絕對 ([\d.]+)）", blk)
        d["rel"] = [float(v) for v in m.groups()] if m else None
        m = re.search(r"Spearman 中位：統一 ([\d.]+)、本益比不變 ([\d.]+)", blk)
        d["sp"] = [float(v) for v in m.groups()] if m else None
        out[h] = d
    return out


def relative_dist(tk, date, lab):
    """相對輸出（README §26.3）：同一天 S&P 500 成分股「只用共識」的統一模型預測 ln(預測本益比 ÷ 今天本益比)，每個 h 一組排序後的數列；
    網頁和命令列（orbit_price.py）用它算「相對大盤」與百分位 → results/relative_dist.json。只用 S&P 500（β、conformal 都是用它校準的）。"""
    model, gm, cq = orbit.load_model(RES), growth_price.load(RES), unified.load_conformal(RES)
    out = dict(date=date, note="S&P 500 成分股、只用共識（校正後）的統一模型預測：ln(預測本益比 ÷ 今天本益比)，依 h 排序；lab＝results/unified_lab.txt 的相對誤差與 Spearman",
               lab={h: dict(rel=v["rel"], sp=v["sp"]) for h, v in (lab or {}).items()}, h={})
    for h in (6, 12, 24):
        vals, grp = [], []
        for t in tk:
            if not t["sp"] or t["e"] is None or t["e"] <= 0:
                continue
            cs = cons_for(t, h)
            if not cs or cs["k_bad"] or not cs["a"]:
                continue
            cs12 = cons_for(t, 12)
            row = dict(px=t["px"], eps0=t["e"], y10=t["y"], dy=t["dy"], vol36=t["v"] if t["v"] is not None else np.nan, grp=t["g"])
            o = unified.predict(row, h, model=model, gm=gm, cq=cq, cons_a=cs["a"][0], cons_b=cs["b"][0] if cs["b"] else None,
                                fwd0=cs12["a"][0] if (cs12 and cs12["a"]) else None)
            if o.get("pe"):
                vals.append(float(np.log(o["pe"] / (t["px"] / t["e"]))))
                grp.append(t["g"])
        v, g = np.array(vals), np.array(grp)
        out["h"][str(h)] = dict(n=int(len(v)), med=float(np.median(v)), med_tech=float(np.median(v[g != "other"])) if (g != "other").any() else None,
                                med_other=float(np.median(v[g == "other"])) if (g == "other").any() else None, v=[round(float(x), 4) for x in np.sort(v)])
    json.dump(out, open(os.path.join(RES, "relative_dist.json"), "w"), ensure_ascii=False)
    return out


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "artifact", "orbit.html")
    model = orbit.load_model(RES)
    slim = dict(version=model["version"], fit_cutoff=model["fit_cutoff"], erp=model["erp"], alpha=model["alpha"],
                vol_clip=model["vol_clip"], loss_widen=model["loss_widen"], loss_beta=model.get("loss_beta"), turn_widen=model.get("turn_widen"),
                band_delta=model.get("band_delta"),
                h={h: dict(pair=v["pair"], beta=v["beta"], bands={k: dict(q=b["q"], vol_median=b["vol_median"]) for k, b in v["bands"].items()})
                   for h, v in model["h"].items()})
    gp = growth_price.load(RES)                                        # 成長定價（README §24）
    slim["gp"] = dict(h={h: dict(coef=v["coef"], q=v["q"], delta=v["delta"], vol_median=v["vol_median"], wf_cover80=v.get("wf_cover80"), gt_hat=v["gt_hat"])
                         for h, v in gp["h"].items()}) if gp else None
    slim["cq"] = slim_cq(unified.load_conformal(RES))                 # 共識模式的 conformal 區間（README §26.2）
    tk, snap_date = tickers()
    slim["lab"] = lab_numbers()                                        # 統一模型回測的幾個數字（註解用）
    slim["rel"] = relative_dist(tk, snap_date or max(x["d"] for x in tk), slim["lab"])   # 相對大盤（README §26.3）
    data = dict(model=slim, tickers=tk, snap=snap_date, bt=backtest(), opt=opt())
    core = open(os.path.join(HERE, "web", "orbit_core.js")).read()
    tpl = open(os.path.join(HERE, "web", "orbit_page.html")).read()
    html = (tpl.replace("/*__CORE__*/", core)
               .replace("/*__DATA__*/", "const DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w").write(html)
    print(f"{len(tk):,} 檔（有共識 {sum(1 for x in tk if x['c']):,}，其中有校正係數 {sum(1 for x in tk if x['c'] and x['c'].get('cf')):,}；"
          f"外國 ADR {sum(1 for x in tk if x.get('adr')):,}；EPS 用 Yahoo 更新 {sum(1 for x in tk if x['u']):,}）→ {out}"
          f"（{len(html) / 1e6:.2f} MB）；相對大盤分布：" + "、".join(f"{h} 個月 {v['n']} 家、中位 {np.exp(v['med']) - 1:+.1%}" for h, v in slim["rel"]["h"].items()))


if __name__ == "__main__":
    main()
