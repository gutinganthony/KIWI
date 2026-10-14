#!/usr/bin/env python3
"""README §25.3：指數層級的長回測——S&P 500 指數 1960–2022 年每個月當起點，預估 12、24 個月後的本益比

    python3 research/long_index.py > results/long_index.txt      # 讀 data/shiller_sp500_monthly.csv

資料：Shiller（datahub 鏡像 datasets/s-and-p-500）：月平均股價 P、過去 12 個月股利 D、過去 12 個月「申報」盈餘 E（季資料內插）、10 年期殖利率。
  盈餘到 2023-06，所以 12 個月起點到 2022-06、24 個月到 2021-06（猜對 B 要再多 12 個月）。
指數沒有歷史分析師共識 → 「事前」的 EPS 用統計預測：每年 1 月只用已揭曉的歷史（1881 年起）估
  ln(E_{t+k} ÷ E_t) ＝ a ＋ b1 × ln(E_t ÷ E_{t−12})（獲利動能）＋ b2 × ln(E_t ÷ 過去 10 年平均 E)（獲利循環的位置），k＝12、24、36。
方法：
  U       本益比不變
  O       軌道（正式版「預期b＋修正ab」非科技 β；EPS_a、EPS_b＝統計預測）
  G       成長定價（正式版非科技係數；EPS_a、目標日的成長預期、今天的成長預期都用統計預測）
  G指數   同上，但係數用指數自己的歷史估（走動式：只用目標日在起點那年以前的月份）
  猜對：O_or（EPS_a＝實際）｜G_or（EPS_a、EPS_b＝實際；今天的成長預期＝統計預測——你知道答案、市場當時不知道）
軌道：ln 股價_T ＝ ln 股價_0 ＋ (10 年期殖利率 ＋ 5% − 股利殖利率) × h/12 ＋ β × ln(EPS ÷ 今天 EPS)。
限制：指數不是個股（同樣的係數套在「一家代表性公司」上）；Shiller 的價格是月平均、盈餘是申報盈餘；起點每個月一個，前後重疊、不是獨立樣本。
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from pef import orbit, growth_price as GP               # noqa: E402
from pef.stats import huber_ols                          # noqa: E402

RES = os.path.join(HERE, "results")
DATA = os.path.join(HERE, "data")


def load():
    d = pd.read_csv(os.path.join(DATA, "shiller_sp500_monthly.csv"), parse_dates=["Date"]).set_index("Date")
    d = d[(d["Earnings"] > 0) & (d["SP500"] > 0)]
    s = pd.DataFrame(index=d.index)
    s["P"], s["E"], s["D"] = d["SP500"], d["Earnings"], d["Dividend"]
    s["y10"] = d["Long Interest Rate"] / 100
    s["dy"] = s["D"] / s["P"]
    s["lpe"] = np.log(s["P"] / s["E"])
    r = np.log(s["P"]).diff()
    s["ret12"] = np.log(s["P"] / s["P"].shift(12))
    s["vol36"] = r.rolling(36).std() * np.sqrt(12)
    s["mom"] = np.log(s["E"] / s["E"].shift(12))
    s["cyc"] = np.log(s["E"] / s["E"].rolling(120).mean())
    for k in (12, 24, 36, 48):
        s[f"E{k}"] = s["E"].shift(-k)
        s[f"P{k}"] = s["P"].shift(-k)
    return s


def eps_forecast(s):
    """每年 1 月重估（只用 t＋k 在那年以前的月份），回傳 ln(E_{t+k} ÷ E_t) 的預測，k＝12、24、36。"""
    out = {k: pd.Series(np.nan, index=s.index) for k in (12, 24, 36)}
    for k in (12, 24, 36):
        tgt = np.log(s[f"E{k}"] / s["E"])
        for Y in range(1925, 2024):
            cut = pd.Timestamp(f"{Y}-01-01")
            tr = s[(s.index + pd.DateOffset(months=k) < cut) & (s.index >= "1881-01-01")]
            tr = tr.assign(t=tgt).dropna(subset=["mom", "cyc", "t"])
            te = s[(s.index >= cut) & (s.index < cut + pd.DateOffset(years=1))].dropna(subset=["mom", "cyc"])
            if len(tr) < 240 or te.empty:
                continue
            X = np.column_stack([np.ones(len(tr)), tr["mom"].clip(-1, 1), tr["cyc"].clip(-1.5, 1.5)])
            co = huber_ols(X, tr["t"].to_numpy(float))
            Xt = np.column_stack([np.ones(len(te)), te["mom"].clip(-1, 1), te["cyc"].clip(-1.5, 1.5)])
            out[k].loc[te.index] = Xt @ co
    return out


def run(s, fc, h, model, gm):
    erp = model["erp"]
    b_exp = float(model["h"][str(h)]["beta"]["預期b＋修正ab"]["other"][0])
    b_raw = float(model["h"][str(h)]["beta"]["原始成長a"]["other"][0])
    d = s.copy()
    d["T_lpe"] = np.log(d[f"P{h}"] / d[f"E{h}"])
    d["orb"] = (d["y10"] + erp - d["dy"]) * h / 12
    d["gh"] = fc[h]                                          # 預測 ln(E_T ÷ E_0)
    d["g12"] = fc[12]
    d["gT"] = fc[36 if h == 24 else 24] - fc[h]              # 目標日的成長預期：ln(E_{T+12} ÷ E_T) 的預測
    d["ga_or"] = np.log(d[f"E{h}"] / d["E"])
    d["gT_or"] = np.log(d[f"E{h + 12}"] / d[f"E{h}"])
    d = d.dropna(subset=["T_lpe", "gh", "g12", "gT", "y10", "dy"])
    c = gm["h"][str(h)]["coef"]["other"]
    rc = d["ret12"].fillna(0).clip(-1, 1)

    def gp(ga, GT, G0, co):
        return co[0] + co[1] * ga.clip(-2, 2) + co[2] * GT.clip(-1.5, 1.5) + co[3] * G0.clip(-1.5, 1.5) + co[4] * rc
    p = pd.DataFrame(index=d.index)
    p["U"] = d["lpe"]
    p["O"] = d["lpe"] + d["orb"] + b_exp * (d["gh"] + d["gT"]).clip(-2, 2) - d["gh"]
    p["G"] = d["lpe"] + d["orb"] + gp(d["gh"], d["gT"], d["g12"], c)
    p["O_or"] = d["lpe"] + d["orb"] + b_raw * d["ga_or"].clip(-2, 2) - d["ga_or"]
    p["G_or"] = d["lpe"] + d["orb"] + gp(d["ga_or"], d["gT_or"], d["g12"], c)
    # 指數自己的係數（走動式）：y ＝ 本益比變化扣掉軌道，線索用「實際 EPS_a、實際目標日成長、統計的今天成長預期、過去 12 個月報酬」
    y = d["T_lpe"] - d["lpe"] - d["orb"]
    Xf = lambda ga, GT: np.column_stack([np.ones(len(d)), ga.clip(-2, 2), GT.clip(-1.5, 1.5), d["g12"].clip(-1.5, 1.5), rc])  # noqa: E731
    Xor, Xex = Xf(d["ga_or"], d["gT_or"]), Xf(d["gh"], d["gT"])
    p["G指數"], p["G指數_or"] = np.nan, np.nan
    co_last = None
    for Y in range(1960, 2024):
        cut = pd.Timestamp(f"{Y}-01-01")
        tr = (d.index + pd.DateOffset(months=h + 12) < cut) & d["gT_or"].notna().to_numpy()
        te = (d.index >= cut) & (d.index < cut + pd.DateOffset(years=1))
        if tr.sum() < 240 or not te.any():
            continue
        co = huber_ols(Xor[tr], y.to_numpy(float)[tr])
        co_last = co
        p.loc[te, "G指數"] = d["lpe"][te] + d["orb"][te] + Xex[te] @ co
        p.loc[te, "G指數_or"] = d["lpe"][te] + d["orb"][te] + Xor[te] @ co
    err = p.sub(d["T_lpe"], axis=0)
    err["ga_or"] = d["ga_or"]
    err["mkt_dpe"] = d["T_lpe"] - d["lpe"]
    return err, co_last


PERIODS = [("1960–1989", "1960-01-01", "1989-12-01"), ("1990–1999", "1990-01-01", "1999-12-01"), ("2000–2002 網路泡沫破裂", "2000-01-01", "2002-12-01"),
           ("2003–2006", "2003-01-01", "2006-12-01"), ("2007–2009 金融海嘯", "2007-01-01", "2009-12-01"), ("2010–2019", "2010-01-01", "2019-12-01"),
           ("2020–2022", "2020-01-01", "2022-12-01"), ("1990 以後全部", "1990-01-01", "2022-12-01")]
NAMES = [("U", "本益比不變"), ("O", "軌道"), ("G", "成長定價"), ("G指數", "成長定價（指數係數）"),
         ("O_or", "猜對：軌道"), ("G_or", "猜對：成長定價"), ("G指數_or", "猜對：成長定價（指數係數）")]


def main():
    s = load()
    model = orbit.load_model()
    gm = GP.load()
    fc = eps_forecast(s)
    pd.set_option("display.width", 240)
    v = s.assign(f=fc[12], t=np.log(s["E12"] / s["E"])).dropna(subset=["f", "t"])
    v = v[v.index >= "1990-01-01"]
    print(f"S&P 500 指數（Shiller），{s.index.min():%Y-%m}～{s.index.max():%Y-%m}；統計 EPS 預測 12 個月（1990 起）中位 |誤差| {np.median(np.abs(v['f'] - v['t'])):.3f}"
          f"（假設 EPS 不變 {np.median(np.abs(v['t'])):.3f}）")
    rows, yrs = [], []
    for h in (12, 24):
        e, co = run(s, fc, h, model, gm)
        print(f"\n== {h} 個月：指數自己的係數（最後一年）[a, c_a, c_T, c_0, c_r] ＝ {', '.join(f'{v:+.3f}' for v in co)}；"
              f"正式版非科技 {', '.join(f'{v:+.3f}' for v in gm['h'][str(h)]['coef']['other'])}")
        for lab, a_, b_ in PERIODS:
            g = e.loc[a_:b_]
            r = dict(h=h, 期間=lab, 起點數=len(g))
            for c, nm in NAMES:
                r[nm] = float(np.median(np.abs(g[c].dropna()))) if g[c].notna().any() else np.nan
            r["實際本益比變化中位"] = float(np.median(g["mkt_dpe"]))
            rows.append(r)
        t = e.loc["1990-01-01":].groupby(e.loc["1990-01-01":].index.year)
        for Y, g in t:
            r = dict(h=h, 年=Y, 實際本益比變化=float(g["mkt_dpe"].mean()), EPS變化=float(g["ga_or"].mean()))
            for c, nm in NAMES:
                r[nm] = float(g[c].mean())                # 平均 ln(預測 ÷ 實際)：+＝預測太高
            yrs.append(r)
        z = e.loc["1990-01-01":]
        print("  ±20% 內（1990 以後）：" + "、".join(f"{nm} {np.mean(np.abs(np.exp(z[c].dropna()) - 1) <= 0.2):.0%}" for c, nm in NAMES))
        print("  軌道勝本益比不變的年份（1990 以後、逐年中位 |誤差|）：" + str(int((z.groupby(z.index.year).apply(lambda g: np.median(np.abs(g['O'])) < np.median(np.abs(g['U'])))).sum()))
              + f"／{z.index.year.nunique()}；成長定價勝軌道 {int((z.groupby(z.index.year).apply(lambda g: np.median(np.abs(g['G'])) < np.median(np.abs(g['O'])))).sum())}；"
              f"猜對時成長定價勝軌道 {int((z.dropna(subset=['G_or']).groupby(z.dropna(subset=['G_or']).index.year).apply(lambda g: np.median(np.abs(g['G_or'])) < np.median(np.abs(g['O_or'])))).sum())}／{z.dropna(subset=['G_or']).index.year.nunique()}")
    t = pd.DataFrame(rows)
    print("\n== 1. 依期間：中位 |ln 本益比誤差|（起點每個月一個）")
    print(t.round(3).to_string(index=False))
    y = pd.DataFrame(yrs)
    print("\n== 2. 逐年（起點年份）：平均 ln(預測 ÷ 實際)，+＝預測的本益比太高；實際本益比變化、EPS 變化都是 ln")
    print(y.round(2).to_string(index=False))
    t.to_csv(os.path.join(RES, "long_index_scores.csv"), index=False, float_format="%.6f")
    y.to_csv(os.path.join(RES, "long_index_years.csv"), index=False, float_format="%.6f")


if __name__ == "__main__":
    main()
