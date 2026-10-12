#!/usr/bin/env python3
"""虧損公司的專用版本：EPS ≤ 0 時，你的看法能不能讓股價預測更準？（README §20.5）

    python3 lab_orbit_loss.py --cache <lab_orbit.py 的暫存目錄>     # 幾秒（只有 Huber 迴歸，不訓練樹模型）

現況（§16.4）：今天或目標日 EPS ≤ 0 時，EPS 成長率 ln(EPS_a ÷ 今天) 沒有定義，股價只用軌道（區間放寬 ×1.35）。
邏輯：虧損公司的股價一樣會對「獲利改善多少」反應，只是要用不需要取對數的量：
  ΔEPS ÷ 股價 ＝（EPS_a − 今天 EPS）÷ 今天股價（盈餘反應文獻的標準寫法：Easton & Harris 1991；正負都能算）
  營收成長 ln(營收_a ÷ 今天營收)（虧損公司常用股價營收比估值）
做法（和 §16 一樣的估法）：同月份去平均、Huber、沒有截距；只用虧損列（今天或目標日 EPS ≤ 0）。
  S&P 500：走動式（每年 1 月只用目標日已到的配對），評分 2015–2025 起點。
  中小型股：直接套用 S&P 500 估的係數（樣本外移植），另做中小型股自己的走動式（2021 起）。
評分：中位 |股價誤差|（＝|實際偏離軌道 − 預測的調整|，EPS 與營收完全正確時的上限），分「虧損→虧損」「虧損→轉盈」「獲利→虧損」。
輸出：results/orbit_loss.txt、orbit_loss_beta.json
"""
import argparse
import io
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lab_orbit import huber_ols                         # noqa: E402

RES = os.path.join(HERE, "results")
buf = io.StringIO()
SPECS = {"EPS 變化÷股價": ["x_e"], "營收成長": ["x_r"], "兩者": ["x_e", "x_r"]}


def say(*a):
    print(*a)
    print(*a, file=buf)


def prep(x, y, eps_f, rev_g):
    d = x.copy()
    d["y"] = y
    d["x_e"] = ((eps_f - d["eps0"]) / d["px"]).clip(-1, 1)
    d["x_r"] = rev_g.clip(-2, 2)
    d["kind"] = np.select([(d["eps0"] <= 0) & (eps_f <= 0), (d["eps0"] <= 0) & (eps_f > 0), (d["eps0"] > 0) & (eps_f <= 0)],
                          ["虧損→虧損", "虧損→轉盈", "獲利→虧損"], "獲利→獲利")
    return d[d["y"].notna() & eps_f.notna() & d["eps0"].notna() & d["px"].gt(0)]


def fit(d, cols):
    d = d.dropna(subset=["y"] + cols)
    if len(d) < 300:
        return np.full(len(cols), np.nan)
    yy = d["y"] - d.groupby("month")["y"].transform("median")
    X = np.column_stack([d[c] - d.groupby("month")[c].transform("median") for c in cols])
    return huber_ols(X, yy.to_numpy(float))


def walk(d, h, start, end, train=None):
    """train：訓練用的資料（預設＝d 自己）。回傳每個寫法的預測與每年的係數。"""
    train = d if train is None else train
    pred = {k: pd.Series(np.nan, index=d.index) for k in SPECS}
    betas = []
    for Y in range(start, end + 1):
        cut = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
        tr = train[train["month"] + pd.DateOffset(months=h) <= cut]
        te = d[(d["month"] > cut) & (d["month"] <= cut + pd.DateOffset(months=12))]
        for k, cols in SPECS.items():
            b = fit(tr, cols)
            if np.all(np.isfinite(b)):
                pred[k].loc[te.index] = te[cols].fillna(0).to_numpy(float) @ b
            betas.append(dict(年=Y, 寫法=k, **{c: v for c, v in zip(cols, b)}))
    return pred, pd.DataFrame(betas)


def report(d, pred, lab):
    rows = []
    for kind in ("虧損→虧損", "虧損→轉盈", "獲利→虧損", "虧損合計"):
        g = d[d["kind"] != "獲利→獲利"] if kind == "虧損合計" else d[d["kind"] == kind]
        g = g[pred["兩者"].loc[g.index].notna() | pred["EPS 變化÷股價"].loc[g.index].notna()]
        if len(g) < 50:
            continue
        r = dict(樣本=lab, 類別=kind, n=len(g), 家數=g["ticker"].nunique(), 只用軌道=float(np.median(np.abs(g["y"]))))
        for k in SPECS:
            p = pred[k].loc[g.index]
            ok = p.notna()
            r[k] = float(np.median(np.abs(g["y"][ok] - p[ok]))) if ok.any() else np.nan
        rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    x = pd.read_pickle(os.path.join(a.cache, "orbit_x2.pkl"))
    x = x[x["month"] >= "2012-01-01"]
    sp = prep(x, x["y12"], x["eps_f12"], x["y_rev_4"])
    loss_sp = sp[sp["kind"] != "獲利→獲利"]
    say(f"S&P 500（2012 起，12 個月）：{len(sp):,} 列，其中虧損相關 {len(loss_sp):,} 列（"
        + "、".join(f"{k} {int((sp['kind'] == k).sum()):,}" for k in ("虧損→虧損", "虧損→轉盈", "獲利→虧損")) + "）")
    say("\n== 1. 邏輯檢查：虧損列的「EPS 變化÷股價」五分位 → 偏離軌道（扣當月中位）的中位數；應該由低到高")
    z = loss_sp.assign(yd=loss_sp["y"] - sp.groupby("month")["y"].transform("median").loc[loss_sp.index])
    for c, nm in (("x_e", "EPS 變化÷股價"), ("x_r", "營收成長")):
        zz = z.dropna(subset=[c])
        qn = pd.qcut(zz[c].rank(method="first"), 5, labels=False)
        med = zz.groupby(qn)["yd"].median()
        say(f"  {nm}：" + "  ".join(f"{v:+.3f}" for v in med) + f"   Spearman {zz[c].corr(zz['yd'], method='spearman'):+.3f}（n={len(zz):,}）")
    pred, betas = walk(loss_sp, 12, 2015, 2025)
    rows = report(loss_sp, pred, "S&P 500 走動式 2015–2025")
    # 中小型股
    sc_path = os.path.join(a.cache, "small_cond.pkl")
    if os.path.exists(sc_path):
        c = pd.read_pickle(sc_path)
        model = json.load(open(os.path.join(RES, "orbit_model.json")))
        orbit_lr = (c["y10"] + model["erp"] - c["dy"].fillna(0))
        sm = prep(c, c["rp_12"] - orbit_lr, c["eps_f12"], c["y_rev_4"])
        loss_sm = sm[sm["kind"] != "獲利→獲利"]
        say(f"\n中小型股（季資料 2019-12～，12 個月）：{len(loss_sm):,} 列虧損相關（"
            + "、".join(f"{k} {int((sm['kind'] == k).sum()):,}" for k in ("虧損→虧損", "虧損→轉盈", "獲利→虧損")) + "）")
        p_tr, _ = walk(loss_sm, 12, 2021, 2025, train=loss_sp)          # 套用 S&P 500 的係數
        rows += report(loss_sm, p_tr, "中小型股，套用 S&P 500 係數")
        p_own, _ = walk(loss_sm, 12, 2021, 2025)
        rows += report(loss_sm, p_own, "中小型股，自己的走動式")
    t = pd.DataFrame(rows)
    say("\n== 2. 中位 |股價誤差|（EPS 與營收完全正確的上限；越小越好）")
    say(t.round(4).to_string(index=False))
    say("\n== 3. S&P 500 走動式係數（最後三年）")
    say(betas.tail(9).round(3).to_string(index=False))
    final = {k: fit(loss_sp[loss_sp["month"] + pd.DateOffset(months=12) <= pd.Timestamp("2025-09-30")], cols).tolist() for k, cols in SPECS.items()}
    say("\n== 4. 正式版係數（S&P 500 全部虧損列、目標日 ≤ 2025-09-30）：" + json.dumps(final, ensure_ascii=False))
    say("   讀法：EPS 變化 ÷ 股價 每多 0.10（例：股價 50 的公司 EPS 從 −2 改善到 +3），股價相對軌道約多 β × 0.10")

    # 5. 6、24 個月（只做採用的寫法：EPS 變化÷股價）＋區間涵蓋（正式版區間：軌道的分位數 × 波動^α；EPS_a ≤ 0 時再放寬 loss_widen）
    model = json.load(open(os.path.join(RES, "orbit_model.json")))
    out = {}
    say("\n== 5. 各預測距離（S&P 500 走動式 2015–2025，虧損列；EPS 變化÷股價）與 80% 區間涵蓋")
    for h, ycol, ef, rg in ((6, "y6", "eps_f6", "y_rev_2"), (12, "y12", "eps_f12", "y_rev_4"), (24, "y24", "eps_f24", "y_rev_8")):
        dd = prep(x, x[ycol], x[ef], x[rg])
        dd = dd[dd["kind"] != "獲利→獲利"]
        pr, _ = walk(dd, h, 2015, 2025)
        p = pr["EPS 變化÷股價"]
        ok = p.notna()
        b = fit(dd[dd["month"] + pd.DateOffset(months=h) <= pd.Timestamp("2025-09-30")], ["x_e"])[0]
        out[str(h)] = float(b)
        band = model["h"][str(h)]["bands"]["軌道"]
        sc = np.clip(dd["vol36"].fillna(band["vol_median"]), *model["vol_clip"]) ** model["alpha"]
        widen = np.where(dd[ef] <= 0, model["loss_widen"][str(h)], 1.0)
        for nm, pp in (("只用軌道", 0.0), ("EPS 變化÷股價", p.fillna(0))):
            u = (dd["y"] - pp) / (sc * widen)
            cov = ((u >= band["q"][0]) & (u <= band["q"][3]))[ok]
            by = {k: float(cov[dd.loc[ok, "kind"] == k].mean()) for k in ("虧損→虧損", "虧損→轉盈", "獲利→虧損")}
            say(f"  {h:>2} 個月 {nm}：中位 |誤差| {np.median(np.abs((dd['y'] - pp)[ok])):.3f}；80% 區間涵蓋 {cov.mean():.0%}（"
                + "、".join(f"{k} {v:.0%}" for k, v in by.items()) + f"）；n={int(ok.sum()):,}" + (f"；正式版 β {b:+.3f}" if nm != "只用軌道" else ""))
    # 6. 今天虧損、目標日轉盈：用一般（未放寬）的區間涵蓋不到 80% → 需要的放寬倍數
    turn = {}
    say("\n== 6. 今天虧損 → 目標日轉盈（EPS_a > 0）：80% 區間要放寬幾倍才涵蓋 80%（套用 EPS 變化÷股價 之後）")
    for h, ycol, ef, rg in ((6, "y6", "eps_f6", "y_rev_2"), (12, "y12", "eps_f12", "y_rev_4"), (24, "y24", "eps_f24", "y_rev_8")):
        dd = prep(x, x[ycol], x[ef], x[rg])
        dd = dd[dd["kind"] != "獲利→獲利"]
        pr, _ = walk(dd, h, 2015, 2025)
        g = dd[(dd["kind"] == "虧損→轉盈") & pr["EPS 變化÷股價"].notna()]
        band = model["h"][str(h)]["bands"]["軌道"]
        u = ((g["y"] - pr["EPS 變化÷股價"].loc[g.index]) / np.clip(g["vol36"].fillna(band["vol_median"]), *model["vol_clip"]) ** model["alpha"]).to_numpy()
        lo, hi = 0.5, 3.0
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if ((u >= band["q"][0] * mid) & (u <= band["q"][3] * mid)).mean() < 0.8 else (lo, mid)
        turn[str(h)] = round(max(1.0, hi), 3)
        say(f"  {h:>2} 個月（n={len(u):,}）：不放寬涵蓋 {((u >= band['q'][0]) & (u <= band['q'][3])).mean():.0%} → 需要 ×{hi:.2f}")
    json.dump(dict(note="虧損公司（今天或目標日 EPS ≤ 0）的看法係數：調整＝β × (EPS_a − 今天 EPS) ÷ 今天股價；turn_widen＝今天虧損、"
                        "EPS_a > 0 時的區間放寬（lab_orbit_loss.py，README §20.5）", beta=out, turn_widen=turn, h12_specs=final),
              open(os.path.join(RES, "orbit_loss_beta.json"), "w"), ensure_ascii=False, indent=1)
    t.to_csv(os.path.join(RES, "orbit_loss_scores.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "orbit_loss.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
