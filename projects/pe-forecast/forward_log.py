#!/usr/bin/env python3
"""前瞻預測紀錄：把「今天的輸入＋今天的模型」凍結起來，等答案揭曉再驗收（README §15.9）。

    python3 forward_log.py freeze                        # 凍結 results/now_all.csv ＋ results/cond_model.json → results/forward/<股價日>/
    python3 forward_log.py score --tag 2026-09-24 --actuals <實際值.csv>   # 答案揭曉後驗收
    python3 forward_log.py freeze-orbit                  # 凍結本益比軌道模型（§16）：最新共識快照的股價＋results/orbit_model.json
    python3 forward_log.py score-orbit --tag orbit-2026-10-06 --actuals results/now_all.csv
    python3 forward_log.py freeze-orbit2                 # 第二輪（§20.1）：共識校正＋護欄、虧損版、區間放寬、最新 10 年期，連同「只用共識」的事前預測
    python3 forward_log.py freeze-orbit2 --only small    # §21.1：補凍中小型美股（有詳細共識之後）
    python3 forward_log.py score-orbit2 --tag orbit2-2026-10-12 --actuals results/now_all.csv

為什麼要做：給定 EPS 的模型（xs）的設計是看過 2022 以後的逐年結果才定的，所以 2022 以後已經不是完全沒碰過的樣本。
真正的樣本外只能是「規格凍結以後才發生的事」。這裡凍結的是模型係數、區間表和今天的線索；
EPS 是使用者要給的輸入，驗收時用「那時實際公布的最近四季 EPS」代入（和回測「假設 EPS 完全正確」同一個問法）。
另外也凍結了「沒有 EPS：模型自己估」的組合模型預測（ens_h，ln 本益比），一起驗收。

實際值.csv 的欄位：ticker, date（目標日）, px（目標日收盤價）, eps_ttm（目標日那時已公布的最近四季 GAAP 稀釋 EPS）
每一列對上凍結日 + h 個月（h＝6、12、18、24、36；差 20 天以內）。
最省事：到時候重跑 now_run.py，直接 --actuals results/now_all.csv（price_date→date、eps0→eps_ttm 自動對應，財報過舊的列略過）。
"""
import argparse
import json
import os
import shutil
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import cond, consensus, orbit                   # noqa: E402
from pef.yahoo import yahoo_symbol                       # noqa: E402

RES = os.path.join(HERE, "results")
FWD = os.path.join(RES, "forward")
ENS_H = (3, 6, 9, 12, 18, 24, 36)
COLS = ["ticker", "name", "tier", "in_sp500", "sector", "price_date", "px", "eps0", "period_end", "fin_age_days", "ln_pe",
        "pe_rel_sec", "g_rev", "ret12", "dy", "vol36", "vol_n", "y10"] + [f"ens_{h}" for h in ENS_H]


def freeze():
    d = pd.read_csv(os.path.join(RES, "now_all.csv"))
    d = d[~d["too_old"].fillna(False).astype(bool) & (d["px"] > 0)]
    model = json.load(open(os.path.join(RES, "cond_model.json")))
    tag = str(pd.Timestamp(d["price_date"].iloc[0]).date())
    out = os.path.join(FWD, tag)
    if os.path.exists(os.path.join(out, "inputs.csv")):
        sys.exit(f"{out} 已經凍結過了；凍結的紀錄不能改（要重來請換一天）。")
    os.makedirs(out, exist_ok=True)
    d[COLS].to_csv(os.path.join(out, "inputs.csv"), index=False, float_format="%.6g")
    shutil.copy(os.path.join(RES, "cond_model.json"), os.path.join(out, "cond_model.json"))
    meta = dict(frozen_price_date=tag, model_version=model["version"], training_cutoff=model["cutoff"], n=len(d),
                n_sp500=int(d["in_sp500"].astype(bool).sum()),
                note="xs/xs2 係數與區間表＝cond_model.json；ens_h＝組合模型（沒有 EPS）的 ln 本益比預測。驗收：forward_log.py score")
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    print(f"凍結 {len(d):,} 家（S&P 500 {meta['n_sp500']}）→ {out}")


def score(tag, actuals, tol_days=20):
    base = os.path.join(FWD, tag)
    inp = pd.read_csv(os.path.join(base, "inputs.csv"), parse_dates=["price_date"])
    model = json.load(open(os.path.join(base, "cond_model.json")))
    act = pd.read_csv(actuals)
    if "eps_ttm" not in act and {"price_date", "px", "eps0"} <= set(act.columns):   # 直接用重跑後的 results/now_all.csv
        if "too_old" in act:
            act = act[~act["too_old"].fillna(False).astype(bool)]
        act = act.rename(columns={"price_date": "date", "eps0": "eps_ttm"})
    act["date"] = pd.to_datetime(act["date"])
    act["ticker"] = act["ticker"].str.upper().str.replace(".", "-", regex=False)
    rows, skipped = [], {"目標日虧損": 0, "對不到日期": 0}
    by = {t: g for t, g in act.groupby("ticker")}
    for r in inp.to_dict("records"):
        for a in by.get(r["ticker"], pd.DataFrame()).to_dict("records"):
            hit = [h for h in cond.HORIZONS
                   if abs((a["date"] - (r["price_date"] + pd.DateOffset(months=h))).days) <= tol_days]
            if not hit:
                skipped["對不到日期"] += 1
                continue
            h = hit[0]
            if not a["eps_ttm"] > 0:
                skipped["目標日虧損"] += 1
                continue
            o = cond.predict_now(r, float(a["eps_ttm"]), h, model)
            pe_act = a["px"] / a["eps_ttm"]
            ens = r.get(f"ens_{h}", np.nan)
            rows.append(dict(ticker=r["ticker"], in_sp500=bool(r["in_sp500"]), h=h, target=a["date"],
                             xs=o["lpe"] - np.log(pe_act),
                             coe=np.log(r["px"] * np.exp(o["mk"]) / a["eps_ttm"]) - np.log(pe_act),
                             unch=(r["ln_pe"] - np.log(pe_act)) if r["eps0"] > 0 else np.nan,
                             ens=(ens - np.log(pe_act)) if np.isfinite(ens) else np.nan,
                             in80=o["pe_lo80"] <= pe_act <= o["pe_hi80"], in50=o["pe_lo50"] <= pe_act <= o["pe_hi50"]))
    if not rows:
        sys.exit(f"沒有對得上的列：{skipped}")
    s = pd.DataFrame(rows)
    print(f"凍結 {tag}（模型 {model['version']}，訓練截止 {model['cutoff']}）；對上 {len(s):,} 列；略過 {skipped}")
    for nm, g in (("全部", s), ("S&P 500", s[s["in_sp500"]])):
        for h, x in g.groupby("h"):
            med = {m: float(np.nanmedian(np.abs(x[m]))) for m in ("xs", "coe", "unch", "ens")}
            print(f"  {nm}｜{h} 個月 n={len(x):,}：中位 |ln(預測 ÷ 實際)| 給定 EPS 模型 {med['xs']:.3f}、資金成本 {med['coe']:.3f}、"
                  f"本益比不變 {med['unch']:.3f}、組合模型（沒有 EPS）{med['ens']:.3f}；區間涵蓋 80%→{x['in80'].mean():.0%}、"
                  f"50%→{x['in50'].mean():.0%}")
    s.to_csv(os.path.join(base, f"score_{pd.Timestamp.today():%Y-%m-%d}.csv"), index=False, float_format="%.6f")


ORBIT_H = (6, 12, 24)
ORBIT_COLS = ["ticker", "name", "tier", "in_sp500", "sector", "price_date", "px", "eps0", "period_end", "eps_refreshed", "eps_refresh_ratio",
              "dy", "vol36", "y10", "cons_0y", "cons_1y", "earnings_ts", "currency"]


def freeze_orbit():
    """本益比軌道模型的前瞻紀錄。股價用最新的共識快照（data/consensus_snapshots/，同一個收盤日），
    其他線索用 results/now_all.csv；快照的財報日晚於 now_all 最新一季的下一季季末時，EPS 改用 Yahoo 的 GAAP 最近四季。
    凍結：今天的輸入、orbit_model.json、各 h 的軌道股價；共識（0y、+1y）原樣保存，之後可以用來驗「共識當你的 EPS」。"""
    import glob
    snaps = sorted(glob.glob(os.path.join(HERE, "data", "consensus_snapshots", "yahoo_2*.csv.gz")))  # 只看選股器快照（不含 yahoo_detail_）
    if not snaps:
        sys.exit("沒有共識快照：先跑 python3 consensus_snapshot.py")
    sn = pd.read_csv(snaps[-1]).set_index("symbol")
    d = pd.read_csv(os.path.join(RES, "now_all.csv"), parse_dates=["period_end"])
    d = d[~d["too_old"].fillna(False).astype(bool)].copy()
    d["sym"] = d["ticker"].map(yahoo_symbol)
    d = d[d["sym"].isin(sn.index)].copy()
    q = sn.loc[d["sym"]]
    d["px"] = q["regularMarketPrice"].to_numpy(float)
    d["price_date"] = pd.to_datetime(q["regularMarketTime"].to_numpy(), unit="s").normalize()
    d["cons_0y"], d["cons_1y"] = q["epsCurrentYear"].to_numpy(float), q["epsForward"].to_numpy(float)
    d["earnings_ts"], d["currency"] = q["earningsTimestamp"].to_numpy(float), q["currency"].to_numpy()
    snap_time = pd.Timestamp(sn["asof_utc"].iloc[0]).tz_localize(None)
    rf = [consensus.refresh_eps(r, sn.loc[r["sym"]].to_dict(), snap_time) for r in d.to_dict("records")]
    d["eps_refreshed"] = [x["n_new"] > 0 for x in rf]
    d["eps_refresh_ratio"] = [x["ratio"] if x["n_new"] else np.nan for x in rf]
    d["eps0"] = [x["eps0"] for x in rf]
    d["period_end"] = [x["period_end"] for x in rf]
    d = d[(d["px"] > 0) & d["price_date"].notna()]
    tag = "orbit-" + str(d["price_date"].mode().iloc[0].date())
    out = os.path.join(FWD, tag)
    if os.path.exists(os.path.join(out, "inputs.csv")):
        sys.exit(f"{out} 已經凍結過了；凍結的紀錄不能改（要重來請換一天）。")
    model = json.load(open(os.path.join(RES, "orbit_model.json")))
    for h in ORBIT_H:
        d[f"orbit_px_{h}"] = d["px"] * np.exp((d["y10"] + model["erp"] - d["dy"].fillna(0)) * h / 12)
    os.makedirs(out, exist_ok=True)
    d[ORBIT_COLS + [f"orbit_px_{h}" for h in ORBIT_H]].to_csv(os.path.join(out, "inputs.csv"), index=False, float_format="%.6g")
    shutil.copy(os.path.join(RES, "orbit_model.json"), os.path.join(out, "orbit_model.json"))
    meta = dict(frozen_price_date=tag[6:], model_version=model["version"], fit_cutoff=model["fit_cutoff"], n=len(d),
                n_sp500=int(d["in_sp500"].astype(bool).sum()), n_eps_refreshed=int(d["eps_refreshed"].sum()),
                consensus_snapshot=os.path.relpath(snaps[-1], HERE),
                note="orbit_px_h＝軌道股價（市場看法不變）；驗收時用目標日實際 EPS 代入 orbit_model.json 的「原始成長a」。"
                     "驗收：forward_log.py score-orbit")
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    print(f"凍結 {len(d):,} 家（S&P 500 {meta['n_sp500']}；EPS 用 Yahoo 更新 {meta['n_eps_refreshed']} 家）→ {os.path.relpath(out, HERE)}")


def score_orbit(tag, actuals, tol_days=20):
    base = os.path.join(FWD, tag)
    inp = pd.read_csv(os.path.join(base, "inputs.csv"), parse_dates=["price_date", "period_end"])
    model = json.load(open(os.path.join(base, "orbit_model.json")))
    act = pd.read_csv(actuals)
    if "eps_ttm" not in act and {"price_date", "px", "eps0"} <= set(act.columns):
        if "too_old" in act:
            act = act[~act["too_old"].fillna(False).astype(bool)]
        act = act.rename(columns={"price_date": "date", "eps0": "eps_ttm"})
    act["date"] = pd.to_datetime(act["date"])
    act["ticker"] = act["ticker"].str.upper().str.replace(".", "-", regex=False)
    by = {t: g for t, g in act.groupby("ticker")}
    rows, skipped = [], {"對不到日期": 0}
    for r in inp.to_dict("records"):
        for a in by.get(r["ticker"], pd.DataFrame()).to_dict("records"):
            hit = [h for h in ORBIT_H if abs((a["date"] - (r["price_date"] + pd.DateOffset(months=h))).days) <= tol_days]
            if not hit:
                skipped["對不到日期"] += 1
                continue
            h, ea = hit[0], float(a["eps_ttm"])
            o = orbit.predict(r, h, model, ea)
            la = np.log(a["px"])
            rows.append(dict(ticker=r["ticker"], grp=orbit.group_of(r["sector"]), in_sp500=bool(r["in_sp500"]), h=h,
                             target=a["date"], loss=not ea > 0, orbit=np.log(r[f"orbit_px_{h}"]) - la,
                             model=np.log(o["px"]) - la,
                             unch=(np.log(r["px"] / r["eps0"] * ea) - la) if (r["eps0"] > 0 and ea > 0) else np.nan,
                             in80=o["px_lo80"] <= a["px"] <= o["px_hi80"], in50=o["px_lo50"] <= a["px"] <= o["px_hi50"]))
    if not rows:
        sys.exit(f"沒有對得上的列：{skipped}")
    s = pd.DataFrame(rows)
    print(f"凍結 {tag}（{model['version']}，β 截止 {model['fit_cutoff']}）；對上 {len(s):,} 列；略過 {skipped}")
    for nm, g in (("全部", s), ("S&P 500", s[s["in_sp500"]]), ("科技", s[s["grp"] != "other"])):
        for h, x in g.groupby("h"):
            med = {m: float(np.nanmedian(np.abs(x[m]))) for m in ("orbit", "model", "unch")}
            print(f"  {nm}｜{h} 個月 n={len(x):,}：中位 |ln(預測 ÷ 實際股價)| 軌道 {med['orbit']:.3f}、軌道＋實際 EPS {med['model']:.3f}、"
                  f"本益比不變 {med['unch']:.3f}；區間涵蓋 80%→{x['in80'].mean():.0%}、50%→{x['in50'].mean():.0%}；"
                  f"市場偏離軌道中位 {np.median(-x['orbit']):+.3f}")
    s.to_csv(os.path.join(base, f"score_{pd.Timestamp.today():%Y-%m-%d}.csv"), index=False, float_format="%.6f")


BUNDLE = ["orbit_model.json", "orbit_loss_beta.json", "band_widen.json", "rate_sensitivity.json", "eps_correction_model.json",
          "eps_correction_firm.csv"]


def _bw(base, kind, h):
    p = os.path.join(base, "band_widen.json")
    bw = json.load(open(p)) if os.path.exists(p) else {}
    return float(bw.get(kind, {}).get("h", {}).get(str(h), 1.0)) if isinstance(kind, str) and kind else 1.0


def freeze_orbit2(only=None):
    """第二輪（README §20.1）：凍結整套模型——共識校正（含同時點護欄）、虧損版、轉盈／中小型股／ADR 區間放寬、最新 10 年期。
    A. 給定 EPS（和回測同一個問法）：今天的輸入＋全部係數；驗收時代入目標日實際公布的最近四季 EPS。
    B. 只用共識（真正的事前預測，不需要任何人給 EPS）：S&P 500／Nasdaq-100 用詳細共識（本財年、下一財年）×當時的校正係數，
       算好 6／12／24 個月的股價中位、80% 區間、本益比；原樣共識也存，驗收時比校正前後誰準。外國 ADR 用每 ADR 美元的共識（不校正）。
    only="small"（README §21.1）：只凍結中小型美股（不在 S&P 500／Nasdaq-100、有詳細共識的），資料夾 orbit2s-<股價日>；
       用來補上 2026-10-09 那份沒有的中小型股「只用共識」預測（當時詳細快照只有約 460 檔大型股）。"""
    import glob
    import hashlib
    import consensus_monthly as CM
    scr = sorted(glob.glob(os.path.join(HERE, "data", "consensus_snapshots", "yahoo_2*.csv.gz")))
    det = sorted(glob.glob(os.path.join(HERE, "data", "consensus_snapshots", "yahoo_detail_*.csv.gz")))
    if not scr or not det:
        sys.exit("要先有選股器快照與詳細快照：python3 consensus_monthly.py")
    sn = pd.read_csv(scr[-1]).drop_duplicates("symbol").set_index("symbol")
    dq = pd.read_csv(det[-1], parse_dates=["last_fy", "mrq"]).drop_duplicates("symbol").set_index("symbol")
    det_date = os.path.basename(det[-1])[len("yahoo_detail_"):-len(".csv.gz")]
    d = pd.read_csv(os.path.join(RES, "now_all.csv"), parse_dates=["period_end"])
    d = d[~d["too_old"].fillna(False).astype(bool)].copy()
    d["sym"] = d["ticker"].map(yahoo_symbol)
    d = d[d["sym"].isin(sn.index)].copy()
    q = sn.loc[d["sym"]]
    d["px"] = q["regularMarketPrice"].to_numpy(float)
    d["price_date"] = pd.to_datetime(q["regularMarketTime"].to_numpy(), unit="s").normalize()
    snap_time = pd.Timestamp(sn["asof_utc"].iloc[0]).tz_localize(None)
    rf = [consensus.refresh_eps(r, sn.loc[r["sym"]].to_dict(), snap_time,
                                mrq=dq.loc[r["sym"], "mrq"] if r["sym"] in dq.index and pd.notna(dq.loc[r["sym"], "mrq"]) else None)
          for r in d.to_dict("records")]
    d["eps0"], d["period_end"] = [x["eps0"] for x in rf], [x["period_end"] for x in rf]
    y_new, y_m = orbit.latest_y10()
    d["y10"] = y_new if y_new is not None else d["y10"]
    big = d["in_sp500"].astype(bool) | d["in_ndx"].fillna(False).astype(bool)
    d["band_kind"] = np.where(big, "", "small")
    d["grp"] = d["sector"].map(lambda v: orbit.group_of(v))
    d["adr"] = False
    if only == "small":
        d = d[~big & d["sym"].isin(dq.index)].copy()
    a = pd.read_csv(os.path.join(HERE, "data", "adr_now.csv"), parse_dates=["period_end", "price_date", "last_fy"])
    a = a[a["conv_ok"].astype(bool) & (a["px"] > 0) & ~a["ticker"].isin(d["ticker"]) & (only is None)].copy()
    a = a.assign(sym=a["ticker"], name=a["name"], tier="adr", in_sp500=False, in_ndx=False, sector=None, band_kind="adr", adr=True,
                 y10=y_new if y_new is not None else a["y10"])
    keep = ["ticker", "sym", "name", "tier", "in_sp500", "in_ndx", "sector", "grp", "adr", "band_kind", "price_date", "px", "eps0",
            "period_end", "y10", "dy", "vol36"]
    d = pd.concat([d[keep], a[keep]], ignore_index=True)
    d = d[(d["px"] > 0) & d["price_date"].notna() & d["eps0"].notna()]
    tag = ("orbit2s-" if only == "small" else "orbit2-") + str(pd.Timestamp(d["price_date"].mode().iloc[0]).date())
    out = os.path.join(FWD, tag)
    if os.path.exists(os.path.join(out, "inputs.csv")):
        sys.exit(f"{out} 已經凍結過了；凍結的紀錄不能改（要重來請換一天）。")
    # B. 只用共識的事前預測
    cf = CM.corrections(det_date)
    cf = cf.set_index("symbol")["cf"] if cf is not None and len(cf) else pd.Series(dtype=float)
    model = orbit.load_model(RES)
    cons_rows = []
    for r in d.to_dict("records"):
        if r["adr"]:
            x = a[a["ticker"] == r["ticker"]].iloc[0]
            fy0, c0, c1, k = pd.Timestamp(x["last_fy"]) + pd.DateOffset(months=12), x.get("cons_0y"), x.get("cons_1y"), np.nan
        elif r["sym"] in dq.index and pd.notna(dq.loc[r["sym"], "last_fy"]):
            x = dq.loc[r["sym"]]
            fy0, c0, c1, k = pd.Timestamp(x["last_fy"]) + pd.DateOffset(months=12), x.get("0y_avg"), x.get("+1y_avg"), cf.get(r["sym"], np.nan)
        else:
            continue
        if not (pd.notna(c0) and c0 > 0):
            continue
        fy1 = fy0 + pd.DateOffset(months=12)
        rec = dict(ticker=r["ticker"], fy0_end=fy0.date(), cons0=c0, cons1=c1, cf=k)
        row = dict(px=r["px"], eps0=r["eps0"], y10=r["y10"], dy=r["dy"], vol36=r["vol36"], sector=r["sector"], grp=r["grp"])
        for h in ORBIT_H:
            ta, tb = r["price_date"] + pd.DateOffset(months=h), r["price_date"] + pd.DateOffset(months=h + 12)
            for tagc, mult in (("raw", 1.0), ("corr", k if np.isfinite(k) else 1.0)):
                fy = {fy0: c0 * mult}
                if pd.notna(c1) and c1 > 0:
                    fy[fy1] = c1 * mult
                ca, _ = orbit.calendarize(fy, ta, r["period_end"], r["eps0"], extrapolate=True)
                cb, _ = orbit.calendarize(fy, tb, r["period_end"], r["eps0"], extrapolate=True)
                rec[f"ca_{tagc}_{h}"], rec[f"cb_{tagc}_{h}"] = ca, cb
                if tagc == "corr" and ca is not None:
                    o = orbit.predict(row, h, model, ca, cb, ca, cb, band_mult=orbit.band_widen(r["band_kind"] or None, h))
                    rec.update({f"px_{h}": o["px"], f"px_lo80_{h}": o["px_lo80"], f"px_hi80_{h}": o["px_hi80"], f"pe_{h}": o["pe"], f"spec_{h}": o["spec"]})
        cons_rows.append(rec)
    os.makedirs(out, exist_ok=True)
    d.to_csv(os.path.join(out, "inputs.csv"), index=False, float_format="%.6g")
    cp = pd.DataFrame(cons_rows)
    cp.to_csv(os.path.join(out, "consensus_preds.csv"), index=False, float_format="%.6g")
    for f in BUNDLE:
        if os.path.exists(os.path.join(RES, f)):
            shutil.copy(os.path.join(RES, f), os.path.join(out, f))
    meta = dict(frozen_price_date=tag.split("-", 1)[1], scope="中小型美股" if only == "small" else "全部",
                model_version=model["version"] + "＋第二輪（§19–20）", fit_cutoff=model["fit_cutoff"], n=len(d),
                n_sp500=int(d["in_sp500"].astype(bool).sum()), n_small=int((d["band_kind"] == "small").sum()), n_adr=int(d["adr"].sum()),
                n_consensus_preds=len(cp), n_corrected=int(cp["cf"].notna().sum()) if len(cp) else 0, y10=y_new, y10_month=str(y_m)[:7],
                snapshot=os.path.relpath(scr[-1], HERE), detail_snapshot=os.path.relpath(det[-1], HERE),
                eps_correction_model_md5=hashlib.md5(open(os.path.join(RES, "eps_correction_model.pkl"), "rb").read()).hexdigest(),
                note="A＝inputs.csv＋係數（驗收時代入實際 EPS）；B＝consensus_preds.csv（只用共識的事前預測，raw＝原樣、corr＝乘校正係數）。"
                     "驗收：forward_log.py score-orbit2")
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    print(f"凍結 {len(d):,} 家（S&P 500 {meta['n_sp500']}、中小型股 {meta['n_small']}、外國 ADR {meta['n_adr']}）；"
          f"只用共識的事前預測 {len(cp):,} 家（其中乘校正係數 {meta['n_corrected']}）→ {os.path.relpath(out, HERE)}")


def score_orbit2(tag, actuals, tol_days=20):
    base = os.path.join(FWD, tag)
    inp = pd.read_csv(os.path.join(base, "inputs.csv"), parse_dates=["price_date", "period_end"])
    cp = pd.read_csv(os.path.join(base, "consensus_preds.csv")).set_index("ticker")
    model = orbit.load_model(base)
    act = pd.read_csv(actuals)
    if "eps_ttm" not in act and {"price_date", "px", "eps0"} <= set(act.columns):
        if "too_old" in act:
            act = act[~act["too_old"].fillna(False).astype(bool)]
        act = act.rename(columns={"price_date": "date", "eps0": "eps_ttm"})
    act["date"] = pd.to_datetime(act["date"])
    act["ticker"] = act["ticker"].str.upper().str.replace(".", "-", regex=False)
    by = {t: g for t, g in act.groupby("ticker")}
    rows = []
    for r in inp.to_dict("records"):
        for x in by.get(r["ticker"], pd.DataFrame()).to_dict("records"):
            hit = [h for h in ORBIT_H if abs((x["date"] - (r["price_date"] + pd.DateOffset(months=h))).days) <= tol_days]
            if not hit:
                continue
            h, ea, la = hit[0], float(x["eps_ttm"]), np.log(x["px"])
            bm = _bw(base, r["band_kind"] if isinstance(r["band_kind"], str) else "", h)
            o = orbit.predict(r, h, model, ea, band_mult=bm)
            orb = np.log(r["px"]) + (r["y10"] + model["erp"] - (r["dy"] if np.isfinite(r["dy"]) else 0)) * h / 12
            z = dict(ticker=r["ticker"], h=h, grp=r["grp"], kind="ADR" if r["adr"] else ("中小型股" if r["band_kind"] == "small" else "S&P 500／Nasdaq-100"),
                     loss=not ea > 0, orbit=orb - la, model=np.log(o["px"]) - la, in80=o["px_lo80"] <= x["px"] <= o["px_hi80"])
            if r["ticker"] in cp.index and pd.notna(cp.loc[r["ticker"]].get(f"px_{h}")):
                c = cp.loc[r["ticker"]]
                z.update(cons_px=np.log(c[f"px_{h}"]) - la, cons_in80=bool(c[f"px_lo80_{h}"] <= x["px"] <= c[f"px_hi80_{h}"]),
                         eps_raw=np.log(ea / c[f"ca_raw_{h}"]) if ea > 0 and c[f"ca_raw_{h}"] > 0 else np.nan,
                         eps_corr=np.log(ea / c[f"ca_corr_{h}"]) if ea > 0 and c[f"ca_corr_{h}"] > 0 else np.nan,
                         cons_pe=(np.log(c[f"px_{h}"] / c[f"ca_corr_{h}"]) - np.log(x["px"] / ea)) if ea > 0 and c[f"ca_corr_{h}"] > 0 else np.nan)
            rows.append(z)
    if not rows:
        sys.exit("沒有對得上的列（還沒到目標日？）")
    s = pd.DataFrame(rows)
    print(f"凍結 {tag}；對上 {len(s):,} 列")
    for (kind, h), g in s.groupby(["kind", "h"]):
        msg = (f"  {kind}｜{h} 個月 n={len(g):,}：中位 |ln 股價誤差| 軌道 {np.nanmedian(np.abs(g['orbit'])):.3f}、軌道＋實際 EPS {np.nanmedian(np.abs(g['model'])):.3f}；"
               f"80% 區間涵蓋 {g['in80'].mean():.0%}")
        if "cons_px" in g and g["cons_px"].notna().any():
            gc = g[g["cons_px"].notna()]
            msg += (f"｜只用共識（n={len(gc):,}）：股價 {np.nanmedian(np.abs(gc['cons_px'])):.3f}、本益比 {np.nanmedian(np.abs(gc['cons_pe'])):.3f}、"
                    f"EPS 誤差 原樣 {np.nanmedian(np.abs(gc['eps_raw'])):.3f} → 校正 {np.nanmedian(np.abs(gc['eps_corr'])):.3f}、區間涵蓋 {gc['cons_in80'].astype(float).mean():.0%}")
        print(msg)
    s.to_csv(os.path.join(base, f"score_{pd.Timestamp.today():%Y-%m-%d}.csv"), index=False, float_format="%.6f")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("freeze")
    sub.add_parser("freeze-orbit")
    fo = sub.add_parser("freeze-orbit2")
    fo.add_argument("--only", choices=["small"], default=None, help="small＝只凍結中小型美股（README §21.1）")
    for nm in ("score", "score-orbit", "score-orbit2"):
        s = sub.add_parser(nm)
        s.add_argument("--tag", required=True, help="results/forward/ 底下的資料夾名（凍結那天的股價日）")
        s.add_argument("--actuals", required=True)
    a = ap.parse_args()
    if a.cmd == "freeze":
        freeze()
    elif a.cmd == "freeze-orbit":
        freeze_orbit()
    elif a.cmd == "freeze-orbit2":
        freeze_orbit2(a.only)
    elif a.cmd == "score":
        score(a.tag, a.actuals)
    elif a.cmd == "score-orbit2":
        score_orbit2(a.tag, a.actuals)
    else:
        score_orbit(a.tag, a.actuals)


if __name__ == "__main__":
    main()
