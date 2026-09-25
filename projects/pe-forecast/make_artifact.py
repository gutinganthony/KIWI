#!/usr/bin/env python3
"""把模型、回測、現在的預測打包成一頁互動網頁（artifact/page.html 樣板 ＋ 資料）。

    python3 make_artifact.py <輸出.html>

只讀 results/ 與 data/（lab_run.py、lab_broad.py、now_run.py 的產出），約 1 分鐘。資料都是公開公司的財報與股價衍生數字。
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import ensemble as en   # noqa: E402
from pef import lab              # noqa: E402
from pef.load import panel, panel_sp500   # noqa: E402

RES = os.path.join(HERE, "results")
ASOF = pd.Timestamp("2026-09-30")
CASES = [   # (ticker, 預測月份, 標題, 類型)
    ("NVDA", "2021-07-01", "盈餘快速成長，本益比自然下降", "盈餘成長"),
    ("AMD", "2023-11-01", "帳面盈餘被攤銷壓低，本益比虛高", "一次性項目"),
    ("HPQ", "2022-11-01", "本益比 5 倍不是便宜，是盈餘在高點", "週期高點"),
    ("MU", "2025-09-01", "站在一年前，預測今天的美光", "推到現在"),
    ("NVDA", "2022-07-01", "模型沒看到 AI 行情", "失敗案例"),
]


def r(x, k=4):
    return None if x is None or not np.isfinite(x) else round(float(x), k)


def horizon_block():
    hz = pd.read_csv(os.path.join(RES, "lab_horizons_all.csv"))
    hz = hz[hz["口徑"] == "GAAP"]
    hits = pd.read_csv(os.path.join(RES, "lab_hits.csv")).set_index("h")
    nn = pd.read_csv(os.path.join(RES, "lab_near_now.csv"))
    nn = nn[nn["窗口"] == "最後12個月"].set_index("h")
    cov = pd.read_csv(os.path.join(RES, "lab_horizon.csv")).set_index("h")
    allh = pd.read_csv(os.path.join(RES, "lab_horizons_all.csv"))
    core = allh[(allh["口徑"] == "核心") & (allh["期間"] == "全期")].set_index("h")
    out = []
    for h in lab.HORIZONS:
        a = hz[(hz["h"] == h) & (hz["期間"] == "全期")].iloc[0]
        s = hz[(hz["h"] == h) & (hz["期間"] == "選模期")].iloc[0]
        o = hz[(hz["h"] == h) & (hz["期間"] == "保留期")].iloc[0]
        hi = hits.loc[h]
        out.append(dict(
            h=h, n=int(a["n"]), rw=r(a["隨機漫步_誤差"]), ens=r(a["組合_誤差"]), oracle=r(a["盈餘全知_誤差"]),
            imp=r(a["改善"]), r2_sel=r(s["OOS_R2"]), r2_hold=r(o["OOS_R2"]), n_hold=int(o["n"]),
            dir=r(hi["方向命中"]), big_dir=r(hi["大變動時方向命中"]), big_share=r(hi["大變動占比"]),
            in20=r(hi["組合_±20%內"]), in20_rw=r(hi["不變_±20%內"]), in30=r(hi["組合_±30%內"]),
            in30_rw=r(hi["不變_±30%內"]), beat=r(hi["組合比不變準的比例"]),
            cover=r(cov.loc[h, "實測涵蓋率"]), sc_cover=r(hi["情境區間_實測涵蓋率"]),
            now_imp=r(nn.loc[h, "改善"]) if h in nn.index else None,
            now_win=r(nn.loc[h, "組合贏的公司比例"]) if h in nn.index else None,
            now_n=int(nn.loc[h, "公司數"]) if h in nn.index else None,
            core_rw=r(core.loc[h, "隨機漫步_誤差"]), core_ens=r(core.loc[h, "組合_誤差"])))
    return out


def methods_block():
    s = pd.read_csv(os.path.join(RES, "lab_scores.csv"))
    s = s[s["h"] == 12]
    out = {}
    for per in ("選模期", "保留期"):
        g = s[(s["期間"] == per) & (s["比較"] == "各方法")].set_index("方法")
        o = s[(s["期間"] == per) & (s["比較"] == "舊模型")].set_index("方法")
        hh = s[(s["期間"] == per) & (s["比較"] == "歷史本益比特徵")].set_index("方法")
        out[per] = {m: dict(r2=r(g.loc[m, "OOS_R2"]), err=r(g.loc[m, "中位絕對誤差"])) for m in g.index}
        out[per]["old_vs"] = {m: r(o.loc[m, "OOS_R2"]) for m in o.index}
        out[per]["hist_vs"] = {m: r(hh.loc[m, "OOS_R2"]) for m in hh.index}
    return out


def sector_block(p):
    g = p[(p["h"] == 12) & p["actual"].notna() & p["ln_pe"].notna() & p["ens"].notna() & (p["month"] >= "2015-01-01")]
    g = g.assign(em=(g["ens"] - g["actual"]).abs(), er=(g["ln_pe"] - g["actual"]).abs())
    s = g.groupby("sector").agg(n=("em", "size"), rw=("er", "median"), ens=("em", "median"))
    return [dict(sector=k, n=int(v.n), rw=r(v.rw), ens=r(v.ens)) for k, v in s.iterrows()]


def cases_block(p, d):
    out = []
    for t, m, title, kind in CASES:
        m = pd.Timestamp(m)
        x = p[(p["h"] == 12) & (p["ticker"] == t) & (p["month"] == m)].iloc[0]
        row = d[(d["ticker"] == t) & (d["month"] == m)].iloc[0]
        coe = (row["y10"] + lab.ERP)
        impl = np.exp(np.log(row["mc"]) + coe - x["ens"])
        mem = {k: r(np.exp(x[k]), 1) if np.isfinite(x[k]) else None for k in ("old", "huber", "gbm", "gbm_z")}
        out.append(dict(
            ticker=t, month=m.strftime("%Y-%m"), target=(m + pd.DateOffset(months=12)).strftime("%Y-%m"),
            title=title, kind=kind, sector=x["sector"],
            pe0=r(np.exp(x["ln_pe"]), 1), pred=r(np.exp(x["ens"]), 1), act=r(np.exp(x["actual"]), 1),
            mc0=r(row["mc"] / 1e9, 1), mc1=r(row["mc_f12"] / 1e9, 1), ni0=r(row["ni_ttm"] / 1e9, 2),
            ni1=r(row["ni_ttm_f12"] / 1e9, 2), ni_impl=r(impl / 1e9, 2), coe=r(coe, 4), members=mem))
    return out


GICS_ZH = {"Information Technology": "資訊科技", "Communication Services": "通訊服務", "Consumer Discretionary": "非必需消費",
           "Consumer Staples": "必需消費", "Health Care": "醫療保健", "Financials": "金融", "Industrials": "工業",
           "Energy": "能源", "Utilities": "公用事業", "Real Estate": "不動產", "Materials": "原物料"}
SEC_ZH = {"software": "軟體", "internet": "網路", "semis": "半導體", "semicap": "半導體設備", "memory": "記憶體", "hardware": "硬體",
          "itservices": "IT 服務", "gics_it": "資訊科技", "gics_comm": "通訊服務", "gics_discr": "非必需消費", "gics_staples": "必需消費",
          "gics_health": "醫療保健", "gics_fin": "金融", "gics_indu": "工業", "gics_energy": "能源", "gics_util": "公用事業",
          "gics_re": "不動產", "gics_mat": "原物料", "other": "其他"}
NAME_TRIM = [" Common Stock", " Class A", " Class B", " Class C", " Ordinary Shares", " American Depositary Shares", ", Inc.", " Inc.",
             " Corporation", " Corp.", " Holdings", " Incorporated", " Ltd.", " plc", " N.V.", " Company"]


def short(name):
    for w in NAME_TRIM:
        name = name.replace(w, "")
    return name.strip(" ,")[:40]


def broad_block():
    hz = pd.read_csv(os.path.join(RES, "broad_horizon.csv"))
    nn = pd.read_csv(os.path.join(RES, "broad_near_now.csv")).set_index("h")
    bd = pd.read_csv(os.path.join(RES, "broad_bands.csv")).set_index("h")
    sec = pd.read_csv(os.path.join(RES, "broad_sector.csv"))
    sc = pd.read_csv(os.path.join(RES, "broad_scores.csv"))
    rows = []
    for h in lab.HORIZONS:
        a = hz[(hz["h"] == h) & (hz["期間"] == "全期")].iloc[0]
        s_ = hz[(hz["h"] == h) & (hz["期間"] == "選模期")].iloc[0]
        o = hz[(hz["h"] == h) & (hz["期間"] == "保留期")].iloc[0]
        rows.append(dict(h=h, n=int(a["n"]), rw=r(a["本益比不變"]), ens=r(a["模型"]), imp=r(a["改善"]), r2=r(a["OOS_R2"]),
                         r2_sel=r(s_["OOS_R2"]), r2_hold=r(o["OOS_R2"]), n_hold=int(o["n"]), dir=r(a["方向命中"]),
                         big_dir=r(a["大變動時方向命中"]), in20=r(a["±20%內"]), in20_rw=r(a["±20%內_不變"]),
                         in30=r(a["±30%內"]), in30_rw=r(a["±30%內_不變"]), beat=r(a["組合比不變準"]),
                         now_win=r(nn.loc[h, "模型較準的公司"]), now_imp=r(nn.loc[h, "模型"] / nn.loc[h, "本益比不變"] - 1),
                         now_firms=int(nn.loc[h, "公司數"]), cover=r(bd.loc[h, "涵蓋率"])))
    cmp = {}
    def pick(tag, sample, per, h, method):
        x = sc[(sc["比較"] == tag) & (sc["樣本"] == sample) & (sc["期間"] == per) & (sc["h"] == h) & (sc["方法"] == method)]
        return r(x["OOS_R2"].iloc[0]) if len(x) else None
    for per in ("選模期", "保留期"):
        for h in (12, 36):
            for sample in ("全部", "科技股名單", "非科技股"):
                cmp[f"train|{per}|{h}|{sample}"] = [pick("訓練名單", sample, per, h, "E_tech"), pick("訓練名單", sample, per, h, "E_all")]
            cmp[f"feat|{per}|{h}"] = [pick("額外特徵", "全部", per, h, "E_all"), pick("額外特徵", "全部", per, h, "E_all_b")]
            cmp[f"ret|{per}|{h}"] = {m[2:]: pick("報酬假設", "全部", per, h, m) for m in
                                     ("R_資金成本", "R_CAPM beta", "R_同產業過去10年", "R_全體過去10年", "R_零")}
        for tag in sc["比較"].unique():
            if tag.startswith(("大樹", "小學習率")):
                for h in (12, 24):
                    cmp[f"hp|{tag}|{per}|{h}"] = [pick(tag, "全部", per, h, "現行"), pick(tag, "全部", per, h, "新參數")]
    sectors = [dict(name=x.產業, n=int(x.n), firms=int(x.公司數), rw=r(x.本益比不變), tech=r(x.E_tech), all=r(x.E_all),
                    r2=r(x.E_all_R2), dir=r(x.方向命中_all)) for x in sec.itertuples()]
    return dict(horizons=rows, compare=cmp, sectors=sectors,
                bands={int(h): [r(v.q10, 4), r(v.q90, 4)] for h, v in bd.iterrows()})


def history_broad():
    p = pd.read_csv(os.path.join(RES, "broad_predictions.csv.gz"), parse_dates=["month"])
    out = {}
    for h in (12, 36):
        g = p[p["h"] == h].copy()
        g["tgt"] = (g["month"] + pd.DateOffset(months=h)).dt.strftime("%Y-%m")
        per = {}
        for t, x in g.groupby("ticker"):
            x = x.sort_values("tgt").drop_duplicates("tgt")
            months = pd.period_range(x["tgt"].iloc[0], x["tgt"].iloc[-1], freq="M").strftime("%Y-%m")
            x = x.set_index("tgt").reindex(months)
            f = lambda c: [None if not np.isfinite(v) else round(float(np.exp(v)), 1) for v in x[c].to_numpy(float)]
            per[t] = dict(s=months[0], pred=f("E_all"), act=f("actual"), rw=f("ln_pe"))
        out[str(h)] = per
    return out


def now_block():
    """現在的預測：每家一列（欄位見 cols）。群組＝快照名單的分組（沒在名單裡就空白）。"""
    from snapshot_run import LIST
    grp = {t: g for t, g, _ in LIST}
    d = pd.read_csv(os.path.join(RES, "now_all.csv"), parse_dates=["period_end"])
    coe = d["y10"] + lab.ERP
    cols = ["t", "n", "a", "sec", "sp", "px", "mc", "ni", "pe", "fe", "st", "e3", "e6", "e9", "e12", "e18", "e24", "e36",
            "o12", "h12", "g12", "z12", "core", "oneoff", "grp", "old"]
    rows = []
    for x in d.itertuples():
        core_ni = x.oi_ttm * 0.85 if np.isfinite(x.oi_ttm) else np.nan
        oneoff = bool(np.isfinite(core_ni) and abs(x.ni_ttm - core_ni) > 0.3 * abs(core_ni) and abs(x.ni_ttm - core_ni) > 0.03 * x.rev_ttm)
        e = [r(np.exp(getattr(x, f"ens_{h}")), 1) if hasattr(x, f"ens_{h}") and np.isfinite(getattr(x, f"ens_{h}")) else None
             for h in lab.HORIZONS]
        mem = [r(np.exp(getattr(x, f"{m}_12")), 1) if np.isfinite(getattr(x, f"{m}_12")) else None for m in ("old", "huber", "gbm", "gbm_z")]
        rows.append([x.ticker, short(str(x.name)), x.aliases if isinstance(x.aliases, str) else "", SEC_ZH.get(x.sector, "其他"),
                     bool(x.in_sp500), r(x.px, 2), r(x.mc / 1e9, 2), r(x.ni_ttm / 1e9, 3), r(x.pe, 1) if x.ni_ttm > 0 else None,
                     x.period_end.strftime("%Y-%m-%d"), bool(x.stale)] + e + mem +
                    [r(x.mc / core_ni, 1) if np.isfinite(core_ni) and core_ni > 0 else None, oneoff, grp.get(x.ticker, ""),
                     bool(getattr(x, "too_old", False) is True)])
    mc_only = pd.read_csv(os.path.join(RES, "now_mc_only.csv"))
    extra = [[t, short(str(n)), r(m / 1e9, 2), r(p_, 2), str(ind)] for t, n, m, p_, ind in
             zip(mc_only["ticker"], mc_only["name"], mc_only["mc"], mc_only["px"], mc_only["industry"])]
    order = ["四大CSP", "記憶體", "光通訊", "半導體設備", "能源", "電力", "軍工", "那斯達克其他"]
    return dict(cols=cols, rows=rows, mc_only=extra, groups=order, price_date=str(d["price_date"].iloc[0])[:10],
                y10=r(float(d["y10"].iloc[0]), 4))


def main():
    out_path = sys.argv[1]
    df, qf = panel()
    d = lab.build(df, qf)
    p = pd.read_csv(os.path.join(RES, "lab_predictions.csv.gz"), parse_dates=["month"])
    dfb, qfb = panel_sp500()
    db = lab.build(dfb, qfb)
    ret_b = en.return_bands(db, ASOF)
    u = pd.read_csv(os.path.join(HERE, "data", "universe_sp500.csv"), keep_default_na=False)
    nw = now_block()
    data = dict(
        asof=ASOF.strftime("%Y-%m-%d"), y10=nw["y10"], erp=lab.ERP, n_firms=int(d["ticker"].nunique()),
        n_sp=int(db["ticker"].nunique()), ret_bands={h: [r(a, 4), r(b, 4)] for h, (a, b) in ret_b.items()},
        horizons=horizon_block(), methods=methods_block(), sectors=sector_block(p), cases=cases_block(p, d),
        broad=broad_block(), now=nw, history=history_broad(),
        gics_of={t: GICS_ZH.get(g, g) for t, g in zip(u["ticker"], u["gics"])})
    tpl = open(os.path.join(HERE, "artifact", "page.html"), encoding="utf-8").read()
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = tpl.replace("/*__DATA__*/null", blob)
    open(out_path, "w", encoding="utf-8").write(html)
    print(f"寫入 {out_path}（{len(html) / 1e3:,.0f} KB）")


if __name__ == "__main__":
    main()
