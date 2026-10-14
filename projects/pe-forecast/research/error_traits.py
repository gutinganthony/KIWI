#!/usr/bin/env python3
"""README §23.3：哪種公司的本益比預測誤差大、哪種小？

    python3 research/error_traits.py --cache <lab_orbit.py 的暫存目錄> --build <lab_eps_correction.py 的 L.build pickle> > results/error_traits.txt

三份資料、同一套特徵：
  ① 回顧 B：2025-10-02 起點、12 個月（results/case_broad.csv，S&P 500）——分析師 forward EPS 原樣
  ② 回顧 A：2024-09-19 起點、24 個月（同檔）——forward EPS × 隱含成長外推（當時的正式版做法，§22.5 說它偏高）
  ③ 長歷史：I/B/E/S 本財年共識、12 個月（2015–2024 起點、距離年報 10.5–12 個月、約 3,100 個公司年；和 README §18 同一批樣本）
     β＝走動式「原始成長a」（起點那一年 1 月的版本），和 lab_orbit_consensus.py 一樣
特徵（起點當時看得到的）：組別、產業、波動（36 個月）、起點本益比、市值、分析師隱含的 EPS 變化 ln(共識 ÷ 今天 EPS)、
  過去 12 個月報酬、股利殖利率、營收年增、EPS 穩定度（過去 5 年「EPS 年增率」的標準差）、過去 5 年曾虧損；
  事後才知道、只拿來解釋：EPS 實際變化 |ln(目標日 EPS ÷ 今天 EPS)|
本益比誤差 ＝ ln(預測 ÷ 實際) ＝ 股價部分 ln(預測股價 ÷ 實際股價) − EPS 部分 ln(輸入的 EPS ÷ 實際 EPS)
多變量：|誤差| 對所有起點特徵的名次（0＝最低、1＝最高；長歷史在同一年內排）做 OLS，係數＝其他條件相同時「最高 vs 最低」差多少；
  90% 區間用「整家公司一起抽」的 bootstrap（300 次）。
輸出：results/error_traits.txt、error_traits_quintiles.csv、error_traits_multi.csv
"""
import argparse
import io
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "results")
GNAME = {"cyclical": "半導體／設備／記憶體", "growth": "軟體／網路", "tech_other": "其他科技", "other": "非科技"}
SEC = {"gics_indu": "工業", "gics_fin": "金融", "gics_health": "醫療", "gics_discr": "非必需消費", "gics_staples": "必需消費",
       "gics_util": "公用事業", "gics_mat": "原物料", "software": "軟體", "hardware": "硬體", "gics_energy": "能源", "semis": "半導體",
       "gics_comm": "通訊服務", "internet": "網路", "gics_it": "其他資訊科技", "itservices": "資訊服務", "semicap": "半導體設備",
       "gics_re": "不動產", "memory": "記憶體"}
TRAITS = [("波動", "vol"), ("起點本益比", "lpe"), ("市值", "lmc"), ("分析師隱含的 EPS 變化", "ig"), ("過去 12 個月報酬", "ret12"),
          ("股利殖利率", "dy"), ("營收年增", "grev"), ("EPS 不穩定度", "stab")]
POST = [("EPS 實際變化 |ln|（事後）", "aeps")]
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def stability(x):
    """每家公司每個月：過去 60 個月「EPS 年增率 ln(EPS ÷ 12 個月前 EPS)」的標準差（至少 24 個點）、過去 60 個月有沒有虧損過。"""
    out = []
    for t, g in x[["ticker", "month", "eps0"]].drop_duplicates(["ticker", "month"]).groupby("ticker"):
        s = g.set_index("month")["eps0"].sort_index().asfreq("MS")
        pos = s.where(s > 0)
        yoy = np.log(pos / pos.shift(12))
        out.append(pd.DataFrame({"ticker": t, "month": s.index, "stab": yoy.rolling(60, min_periods=24).std().to_numpy(),
                                 "loss5": (s <= 0).astype(float).where(s.notna()).rolling(60, min_periods=12).max().to_numpy()}))
    return pd.concat(out, ignore_index=True)


def lookback(st):
    d = pd.read_csv(os.path.join(RES, "case_broad.csv"))
    sets = {}
    for key, nm, mon in (("B", "B：2025-10-02 起點", "2025-09-01"), ("A", "A：2024-09-19 起點", "2024-08-01")):
        z = d[d["情境"] == nm].copy()
        z["month"] = pd.Timestamp(mon)
        z = z.merge(st.rename(columns={"ticker": "股票"}), on=["股票", "month"], how="left")
        sets[key] = pd.DataFrame({
            "ticker": z["股票"], "year": 0, "grp": z["組別"], "sector": z["產業"].map(SEC).fillna("其他"),
            "vol": z["波動"], "lpe": np.log(z["起點本益比"]), "lmc": np.log(z["市值"]), "ig": z["隱含成長"], "ret12": z["報酬12"],
            "dy": z["股利殖利率"], "grev": z["營收成長"].replace([np.inf, -np.inf], np.nan), "stab": z["stab"], "loss5": z["loss5"],
            "aeps": z["EPS變化"].abs(), "err": z["誤差_分析師"], "px": z["誤差_股價"], "eps": z["誤差_EPS"]})
    return sets


def history(build):
    b = pd.read_pickle(build)
    beta = pd.read_csv(os.path.join(RES, "orbit_beta.csv"))
    bt = beta[(beta["方法"] == "原始成長a") & (beta["h"] == 12)].set_index(["年", "組別"])["b0"]
    z = b[(b["lead"] > 10.5) & (b["lead"] <= 12.0) & (b["month"] >= "2015-01-01") & ~b["near_split"] & (b["eps0"] > 0)
          & (b["feps"] > 0) & (b["eps_f12"] > 0) & b["y12"].notna()].copy()
    z["b"] = [bt.get((m.year, GNAME[g]), np.nan) for m, g in zip(z["month"], z["grp"])]
    z = z[z["b"].notna()]
    px_err = z["b"] * np.log(z["feps"] / z["eps0"]).clip(-2, 2) - z["y12"]          # 預測 ln 股價 − 實際 ln 股價（軌道兩邊相消）
    eps_err = np.log(z["feps"] / z["eps_f12"])
    return pd.DataFrame({
        "ticker": z["ticker"], "year": z["month"].dt.year, "month": z["month"], "grp": z["grp"].map(GNAME),
        "sector": z["sector"].map(SEC).fillna("其他"), "vol": z["vol36"], "lpe": z["ln_pe"], "lmc": z["ln_mc"],
        "ig": np.log(z["feps"] / z["eps0"]), "ret12": z["ret12"], "dy": z["dy"], "grev": z["g_rev"].replace([np.inf, -np.inf], np.nan),
        "aeps": np.log(z["eps_f12"] / z["eps0"]).abs(), "err": px_err - eps_err, "px": px_err, "eps": eps_err})


def med_abs(v):
    return float(np.median(np.abs(v))) if len(v) else np.nan


def w20(v):
    return float(np.mean(np.abs(np.exp(v) - 1) <= 0.2)) if len(v) else np.nan


def quintiles(sets):
    rows = []
    for lab, col in TRAITS + POST:
        for key, z in sets.items():
            zz = z[z[col].notna()]
            if len(zz) < 100:
                continue
            q = pd.qcut(zz[col].rank(method="first"), 5, labels=[f"Q{i}" for i in range(1, 6)])
            r = dict(特徵=lab, 資料=key, n=len(zz), ρ=float(zz[col].corr(zz["err"].abs(), method="spearman")))
            for qi, g in zz.groupby(q, observed=True):
                r[qi] = med_abs(g["err"])
                r[qi + "_值"] = float(g[col].median())
            g1, g5 = zz[q == "Q1"], zz[q == "Q5"]
            r.update(Q1_EPS部分=med_abs(g1["eps"]), Q5_EPS部分=med_abs(g5["eps"]), Q1_股價部分=med_abs(g1["px"]), Q5_股價部分=med_abs(g5["px"]),
                     Q1_偏差=float(np.median(g1["err"])), Q5_偏差=float(np.median(g5["err"])), Q1_20內=w20(g1["err"]), Q5_20內=w20(g5["err"]))
            rows.append(r)
    return pd.DataFrame(rows)


def multi(z, nboot=300, seed=0):
    cols = [c for _, c in TRAITS]
    zz = z.dropna(subset=cols + ["err"]).copy()
    X = zz.groupby("year")[cols].rank(pct=True).to_numpy(float)
    G = pd.get_dummies(zz["grp"]).drop(columns="非科技", errors="ignore").astype(float)
    X = np.column_stack([np.ones(len(zz)), X, G.to_numpy()])
    y = np.abs(zz["err"].to_numpy(float))
    names = ["截距"] + [lab for lab, _ in TRAITS] + [f"組別：{c}" for c in G.columns]
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    rng = np.random.default_rng(seed)
    tick = zz["ticker"].to_numpy()
    idx_by = pd.Series(np.arange(len(zz))).groupby(tick).apply(list).to_dict()
    keys = list(idx_by)
    bs = []
    for _ in range(nboot):
        pick = np.concatenate([idx_by[keys[i]] for i in rng.integers(0, len(keys), len(keys))])
        bs.append(np.linalg.lstsq(X[pick], y[pick], rcond=None)[0])
    bs = np.array(bs)
    return pd.DataFrame({"變數": names, "係數": coef, "lo90": np.quantile(bs, 0.05, axis=0), "hi90": np.quantile(bs, 0.95, axis=0)}), len(zz)


def groups(z, col, min_n):
    rows = []
    for k, g in z.groupby(col):
        if len(g) >= min_n:
            rows.append(dict(類別=k, n=len(g), 中位誤差=med_abs(g["err"]), EPS部分=med_abs(g["eps"]), 股價部分=med_abs(g["px"]),
                             偏差中位=float(np.median(g["err"])), 在20內=w20(g["err"])))
    return pd.DataFrame(rows).sort_values("中位誤差")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--build", required=True)
    a = ap.parse_args()
    x = pd.read_pickle(os.path.join(a.cache, "orbit_x2.pkl"))
    st = stability(x)
    sets = lookback(st)
    h = history(a.build).merge(st, on=["ticker", "month"], how="left")
    sets["長歷史"] = h
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    say("資料：B＝2025-10 起點 12 個月（S&P 500 回顧）、A＝2024-09 起點 24 個月（同）、長歷史＝I/B/E/S 2015–2024 起點 12 個月")
    for k, z in sets.items():
        say(f"  {k}：{len(z):,} 列、{z['ticker'].nunique()} 家；中位 |本益比誤差| {med_abs(z['err']):.3f}；"
            f"EPS 部分 {med_abs(z['eps']):.3f}、股價部分 {med_abs(z['px']):.3f}；±20% 內 {w20(z['err']):.0%}")

    say("\n== 1. 依特徵分五等分（Q1＝最低 20%、Q5＝最高 20%）：中位 |ln 本益比誤差|；ρ＝特徵和 |誤差| 的 Spearman 相關")
    q = quintiles(sets)
    show = q[["特徵", "資料", "n", "ρ", "Q1", "Q2", "Q3", "Q4", "Q5", "Q1_值", "Q5_值", "Q1_EPS部分", "Q5_EPS部分", "Q1_股價部分", "Q5_股價部分", "Q1_偏差", "Q5_偏差", "Q1_20內", "Q5_20內"]]
    say(show.round(3).to_string(index=False))
    q.to_csv(os.path.join(RES, "error_traits_quintiles.csv"), index=False, float_format="%.6f")

    say("\n== 2. 組別")
    for k, z in sets.items():
        say(f"-- {k}")
        say(groups(z, "grp", 10).round(3).to_string(index=False))
    say("\n== 3. 產業（長歷史 n ≥ 60；B 的 n ≥ 10）")
    for k in ("長歷史", "B"):
        say(f"-- {k}")
        say(groups(sets[k], "sector", 60 if k == "長歷史" else 10).round(3).to_string(index=False))
    say("\n== 4. 過去 5 年曾虧損 vs 沒有")
    for k, z in sets.items():
        say(f"-- {k}")
        say(groups(z.assign(虧損=z["loss5"].map({1.0: "過去 5 年虧損過", 0.0: "沒虧損過"})), "虧損", 10).round(3).to_string(index=False))

    say("\n== 5. 多變量：|誤差| ~ 起點特徵名次（0＝最低、1＝最高）＋組別；係數＝其他條件相同時最高 vs 最低差多少（ln）")
    mm = []
    for k, z in sets.items():
        t, n = multi(z)
        t.insert(0, "資料", k)
        say(f"-- {k}（n＝{n:,}）")
        say(t.round(3).to_string(index=False))
        mm.append(t)
    pd.concat(mm).to_csv(os.path.join(RES, "error_traits_multi.csv"), index=False, float_format="%.6f")

    say("\n== 6. 大誤差（|本益比誤差| > 0.5，約差 65% 以上）是 EPS 估錯還是股價走勢？")
    for k, z in sets.items():
        big = z[z["err"].abs() > 0.5]
        if len(big):
            say(f"  {k}：{len(big)} 列（{len(big) / len(z):.0%}）；EPS 部分比股價部分大的 {np.mean(big['eps'].abs() > big['px'].abs()):.0%}；"
                f"EPS 實際變化 > ±50% 的 {np.mean(big['aeps'] > np.log(1.5)):.0%}（全體 {np.mean(z['aeps'] > np.log(1.5)):.0%}）")
    say("\n== 7. 長歷史分前後期，看規律穩不穩（Spearman ρ：特徵 vs |誤差|）")
    rr = []
    for lab, col in TRAITS + POST:
        r = dict(特徵=lab)
        for per, m in (("2015–2019", h["year"] <= 2019), ("2020–2024", h["year"] >= 2020)):
            g = h[m & h[col].notna()]
            r[per] = float(g[col].corr(g["err"].abs(), method="spearman"))
        rr.append(r)
    say(pd.DataFrame(rr).round(3).to_string(index=False))
    open(os.path.join(RES, "error_traits.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
