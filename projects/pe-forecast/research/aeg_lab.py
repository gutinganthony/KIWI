#!/usr/bin/env python3
"""AEG（Ohlson-Juettner-Nauroth 2005）＋本益比軌道：用今天的股價反推長期成長，預測 12 個月後的股價／本益比。

    python3 research/aeg_lab.py          # 約 2 分鐘；輸出 results/aeg_lab.txt、aeg_lab_scores.csv、aeg_lab_rows.csv.gz

模型（每股，年為單位；r＝10 年期殖利率＋5%）：
  今天：  P0 ＝ eps1/r ＋ z1 / [r(r − γ)]，   z1 ＝ eps2 ＋ r·dps1 − (1＋r)·eps1      （異常盈餘成長 AEG）
          → 反推市場隱含的長期 AEG 成長率 γ ＝ r − z1 / (r·P0 − eps1)                 （閉式解）
  12 個月後：P1 ＝ eps2/r ＋ z2 / [r(r − γ)]，z2 ＝ eps3 ＋ r·dps2 − (1＋r)·eps2
          ＝ (1＋r)·P0 − dps1                       ← 本益比軌道：市場看法不變時，股價照資金成本漲（扣股利）
           ＋ [z2 − (1＋γ)·z1] / [r(r − γ)]        ← 修正項：第 3 年 EPS 和「市場隱含路徑」的差距
回測用事後實際公布的 EPS 當「你給的 EPS 路徑」（eps1、eps2、eps3＝12、24、36 個月後那時已公布的最近四季 EPS），
所以這是「EPS 路徑完全正確」的上限測試，和 README §15 的回測同一個問法。樣本：S&P 500，預測起點 2012-01～2022-09。
"""
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from pef import cond, lab                                # noqa: E402
from pef.load import panel_sp500                         # noqa: E402

RES = os.path.join(HERE, "results")
TECH = {"software", "hardware", "semis", "internet", "itservices", "semicap", "memory", "gics_it"}
CYCL = {"semis", "semicap", "memory"}
GROWTH = {"software", "internet"}
EARLY, LATE = ("2012-01-01", "2017-12-31"), ("2018-01-01", "2022-09-30")
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def group(sector):
    if sector in GROWTH:
        return "科技：軟體／網路"
    if sector in CYCL:
        return "科技：半導體／設備／記憶體"
    if sector in TECH:
        return "科技：硬體／IT 服務／其他"
    return "非科技"


def build():
    df, qf = panel_sp500()
    c = cond.build(lab.build(df, qf), df)
    x = c[(c["month"] >= EARLY[0]) & (c["month"] <= LATE[1])].copy()
    x["r"] = x["y10"] + cond.ERP
    x["eps1"], x["eps2"], x["eps3"] = x["eps_f12"], x["eps_f24"], x["eps_f36"]
    x["dps1"] = x["dy"].fillna(0) * x["px"]
    pay = (x["dps1"] / x["eps1"]).where(x["eps1"] > 0, 0).clip(0, 1)
    x["dps2"] = pay * x["eps2"].clip(lower=0)
    need = ["px", "px_f12", "eps0", "eps1", "eps2", "eps3", "r"]
    x = x[x[need].notna().all(axis=1) & (x["px"] > 0) & (x["eps0"] > 0) & (x["eps1"] > 0)].copy()
    x["grp"] = x["sector"].map(group)
    x["tech"] = x["sector"].isin(TECH)
    return x


def aeg(x):
    r, P = x["r"], x["px"]
    x["z1"] = x["eps2"] + r * x["dps1"] - (1 + r) * x["eps1"]
    den = r * P - x["eps1"]                                  # r·P0 − eps1：P/E 高於 1/r 時為正
    x["gam"] = r - x["z1"] / den
    x["valid"] = np.isfinite(x["gam"]) & (x["gam"] < r - 0.005) & (x["gam"] > -0.5) & (den.abs() > 1e-9)
    x["mult"] = 1 / (r * (r - x["gam"]))                     # 修正項的放大倍數
    x["z2"] = x["eps3"] + r * x["dps2"] - (1 + r) * x["eps2"]
    x["orbit"] = (1 + r) * P - x["dps1"]                     # 本益比軌道（看法不變）
    x["rev"] = (x["z2"] - (1 + x["gam"]) * x["z1"]) * x["mult"]
    x["aeg"] = x["orbit"] + x["rev"]
    x["unch"] = P * x["eps1"] / x["eps0"]                    # 本益比不變
    return x


def err(pred, actual):
    p = np.asarray(pred, float)
    return np.where(p > 0, np.log(np.maximum(p, 1e-12) / actual), np.nan)


def score(g, cols):
    out = {}
    for m in cols:
        e = err(g[m], g["px_f12"])
        ok = np.isfinite(e)
        out[m] = dict(err=float(np.median(np.abs(e[ok]))) if ok.any() else np.nan, bad=float(1 - ok.mean()),
                      hit20=float(np.mean(np.abs(np.exp(e[ok]) - 1) <= 0.2)) if ok.any() else np.nan)
    return out


def main():
    x = aeg(build())
    say(f"樣本：{len(x):,} 個公司月（S&P 500，預測起點 2012-01～2022-09，今天與 12 個月後 EPS 為正、36 個月 EPS 已知）")
    say(f"  科技 {int(x['tech'].sum()):,}、非科技 {int((~x['tech']).sum()):,}")

    # 1) 反推能不能成功
    say("\n== 1. 從今天股價反推長期 AEG 成長 γ：能解出合理值（γ < r）的比例、γ 與放大倍數的中位數")
    for g, y in x.groupby("grp"):
        v = y[y["valid"]]
        say(f"  {g:18s} n={len(y):6,}  解得出 {y['valid'].mean():.0%}  γ 中位 {v['gam'].median():+.1%}"
            f"（四分位 {v['gam'].quantile(.25):+.1%}～{v['gam'].quantile(.75):+.1%}）  r−γ 中位 {(v['r'] - v['gam']).median():.1%}"
            f"  放大倍數中位 {v['mult'].median():.0f}")

    # 2) 修正項的實際傳導：ln(P1/軌道) 對 修正項/軌道 的斜率（理論＝1）
    x["y"] = np.log(x["px_f12"] / x["orbit"].where(x["orbit"] > 0))
    x["s"] = (x["rev"] / x["orbit"]).clip(-1, 1)
    say("\n== 2. 修正項有沒有用：ln(實際 ÷ 軌道) 對（修正項 ÷ 軌道，截在 ±1）的迴歸；理論上斜率＝1")
    sl = {}
    x["per"] = np.where(x["month"] <= EARLY[1], "2012–2017", "2018–2022")
    for (g, per), y in x[x["valid"] & x["y"].notna()].groupby(["grp", "per"]):
        b = np.polyfit(y["s"], y["y"], 1)[0]
        rr = np.corrcoef(y["s"], y["y"])[0, 1] ** 2
        sl[(g, per)] = b
        say(f"  {g:18s} {per}：斜率 {b:+.3f}  R² {rr:.3f}  n={len(y):,}")

    # 3) 預測準確度：本益比不變、軌道、AEG（完全照理論）、AEG（修正項打折 λ，λ 在 2012–2017 挑）
    v = x[x["valid"]].copy()
    early = v[v["month"] <= EARLY[1]]
    grid = [0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]
    e_l = [np.median(np.abs(err(early["orbit"] + lam * early["rev"], early["px_f12"])[np.isfinite(
        err(early["orbit"] + lam * early["rev"], early["px_f12"]))])) for lam in grid]
    lam = grid[int(np.argmin(e_l))]
    say("\n== 3. λ（修正項打幾折）在 2012–2017 挑：" + "、".join(f"λ={g_} {e_:.4f}" for g_, e_ in zip(grid, e_l)) + f" → 選 λ＝{lam}")
    v["aeg_lam"] = v["orbit"] + lam * v["rev"]
    # 舊模型（README §15）的 xs、xs2：同一列比較
    p = pd.read_csv(os.path.join(RES, "cond_predictions.csv.gz"), usecols=["ticker", "h", "origin", "xs", "xs2", "eps_target"],
                    parse_dates=["origin"])
    p = p[p["h"] == 12]
    v = v.merge(p, left_on=["ticker", "month"], right_on=["ticker", "origin"], how="left")
    v["xs_px"] = np.exp(v["xs"]) * v["eps1"]
    v["xs2_px"] = np.exp(v["xs2"]) * v["eps1"]
    cols = ["unch", "orbit", "aeg", "aeg_lam", "xs_px", "xs2_px"]
    names = {"unch": "本益比不變", "orbit": "軌道（股價照資金成本）", "aeg": "AEG 完全照理論", "aeg_lam": f"AEG 修正項×{lam}",
             "xs_px": "舊模型 xs", "xs2_px": "舊模型 xs2"}
    rows = []
    say("\n== 4. 12 個月後股價（＝給定 EPS 下的本益比）的中位 |ln 誤差|；同一批列比較（xs2 只在有資料的列）")
    for per, rng in (("2012–2017", EARLY), ("2018–2022", LATE)):
        for g, y in v[(v["month"] >= rng[0]) & (v["month"] <= rng[1])].groupby("grp"):
            y = y[y["xs_px"].notna()]
            s = score(y, cols)
            for m in cols:
                rows.append(dict(期間=per, 組別=g, 方法=names[m], n=len(y), 中位絕對誤差=s[m]["err"], 命中20=s[m]["hit20"],
                                 預測無效比例=s[m]["bad"]))
            say(f"  {per} {g:18s} n={len(y):6,}  " + "  ".join(f"{names[m]} {s[m]['err']:.3f}" for m in cols)
                + f"  （AEG 無效 {s['aeg']['bad']:.0%}）")
    sc = pd.DataFrame(rows)

    # 5) 範例：AEG 在哪種情況錯最多
    v["e_aeg"] = err(v["aeg"], v["px_f12"])
    v["e_orb"] = err(v["orbit"], v["px_f12"])
    say("\n== 5. AEG 完全照理論 vs 軌道：依放大倍數分組的中位 |ln 誤差|（科技股）")
    t = v[v["tech"]].copy()
    t["mbin"] = pd.cut(t["mult"], [0, 30, 60, 120, 1e9], labels=["<30", "30–60", "60–120", ">120"])
    for b, y in t.groupby("mbin", observed=True):
        say(f"  放大倍數 {b:>7s}  n={len(y):5,}  AEG {np.nanmedian(np.abs(y['e_aeg'])):.3f}  軌道 {np.nanmedian(np.abs(y['e_orb'])):.3f}")

    sc.to_csv(os.path.join(RES, "aeg_lab_scores.csv"), index=False, float_format="%.6f")
    keep = ["ticker", "sector", "grp", "month", "px", "px_f12", "eps0", "eps1", "eps2", "eps3", "dps1", "r", "z1", "z2", "gam",
            "valid", "mult", "orbit", "rev", "aeg", "unch"]
    x[keep].to_csv(os.path.join(RES, "aeg_lab_rows.csv.gz"), index=False, float_format="%.6g",
                   compression={"method": "gzip", "mtime": 0})
    open(os.path.join(RES, "aeg_lab.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
