#!/usr/bin/env python3
"""README §27：把區間變窄——同樣的命中率下最小的寬度（走動式）→ results/band_sharp.txt、band_sharp.json

    python3 research/band_sharp.py --build <pk pickle> --cache <orbit_x2.pkl 目錄> > results/band_sharp.txt   # 先跑 research/unified_lab.py

問題：共識模式（只有共識、沒有自己的看法）的 80% 本益比區間太寬（12 個月中位股票高 ÷ 低 ≈ 2.9 倍），寬到沒有參考價值。
  「範圍越大命中率越高」是對的——所以要比的不是命中率，是「同樣命中率下誰最窄」（區間分數：寬度 ＋ 漏掉時 2/α 倍的距離，
  Gneiting & Raftery 2007；最小化它＝給定涵蓋率下最小寬度的凸形式，分位數迴歸就是這個線性規劃）。
拆開看誤差（results/unified_rows.csv.gz 的 C、eps_err）：
  本益比誤差 ＝ 股價誤差 − 共識 EPS 誤差：ln(實際本益比 ÷ 預測) ＝ ln(實際股價 ÷ 預測股價) − ln(實際 EPS ÷ 共識)
  12 個月 10／90 分位：股價誤差 −0.32／+0.35（寬 0.67）、EPS 誤差 −0.36／+0.52（寬 0.88）、本益比誤差 −0.43／+0.62（寬 1.05）
  → 本益比區間寬主要是「共識 EPS 會錯多少」；股價區間本身窄 1/3。現行把本益比區間 × 共識 EPS 當股價區間，把 EPS 誤差也算進股價了。
方法（每個起點年 Y 只用「目標日在 Y 年第一個起點月以前」的配對校準；目標 y ＝ ln(實際 ÷ 預測)，股價與本益比各自一套）：
  pooled   現行：u ＝ y ÷ (波動^α × exp(δ|ga|))，取 10／90 分位（不置中）
  hdr      同上，但取「最短的 80% 區間」（分位數起點在 0～20% 之間挑最窄的）
  recent3  同 pooled，只用最近 3 個已揭曉的起點年份校準（誤差大小有時期性）
  scale-S  尺度模型：log|y| 對線索做 Huber 迴歸 → ŝ；u ＝ y ÷ ŝ 取分位。S1＝[ln 波動, |ga|]；S2＝S1＋[本益比的歷史波動, |本益比相對自己 5 年中位|]；S3＝全部線索
  qr-S     線性分位數迴歸（線性規劃，scipy linprog／HiGHS）：直接估 y 的 10% 與 90% 條件分位（S1／S2／S3）
  gbm-q    梯度提升分位數迴歸（sklearn HistGradientBoosting，loss="quantile"），S3
  線索（起點當天都算得出來）：ln 波動36、|ln(共識 ÷ 今天 EPS)|、本益比 36 個月 ln 標準差、|本益比相對自己 5 年中位|、|本益比相對同業|、ln 市值、|12 個月報酬|、
       |公司過去的共識偏差|、科技（0/1）、ln 本益比水準
對照（不是模型）：本益比不變 ＋ 歷史 ln(本益比_T ÷ 本益比_0) 分位；公司自己過去 5 年本益比的 10／90 分位。
評分：涵蓋（逐年平均、最低）、寬度（ln 高 − ln 低 的平均；高 ÷ 低 的中位）、區間分數；50／60／70／80／90% 名目水準的邊界（寬度 vs 涵蓋）。
"""
import argparse
import io
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from pef import orbit                                    # noqa: E402
from pef.stats import huber_ols                          # noqa: E402

RES = os.path.join(HERE, "results")
LEVELS = (0.5, 0.6, 0.7, 0.8, 0.9)
FEATS = {"S1": ["lvol", "aga"], "S2": ["lvol", "aga", "pevol", "aown"],
         "S3": ["lvol", "aga", "pevol", "aown", "asec", "lmc", "ar12", "apb", "tech", "lpe"]}
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


# ---------- 資料 ----------
def load(build, cache):
    o = pd.read_csv(os.path.join(RES, "unified_rows.csv.gz"), parse_dates=["month", "T"])
    o = o[o["C"].notna()].copy()
    b = pd.read_pickle(build)
    x = pd.read_pickle(os.path.join(cache, "orbit_x2.pkl")).sort_values(["ticker", "month"])
    # 本益比的歷史波動（36 個月 ln 本益比標準差）與自己過去 5 年的 10／90 分位（都只用起點以前的月份）
    g = x.groupby("ticker")["ln_pe"]
    x["pevol"] = g.transform(lambda s: s.rolling(36, min_periods=24).std())
    x["own_lo"] = g.transform(lambda s: s.shift(1).rolling(60, min_periods=36).quantile(0.1))
    x["own_hi"] = g.transform(lambda s: s.shift(1).rolling(60, min_periods=36).quantile(0.9))
    o = o.merge(x[["ticker", "month", "pevol", "own_lo", "own_hi", "ln_pe"]], on=["ticker", "month"], how="left")
    o = o.merge(b[["ticker", "month", "pe_rel_own", "pe_rel_sec", "ln_mc", "ret12", "past_bias"]], on=["ticker", "month"], how="left")
    model = orbit.load_model()
    delta = model.get("band_delta") or {}
    o["y_pe"] = -o["C"]                                   # ln(實際本益比 ÷ 預測)
    o["y_px"] = -(o["C"] + o["eps_err"])                  # ln(實際股價 ÷ 預測股價)
    o["y_eps"] = -o["eps_err"]                            # ln(實際 EPS ÷ 共識)
    o["y_unch"] = -o["U"]                                 # 本益比不變的誤差
    vmed = o.groupby("h")["vol36"].transform("median")
    vol = o["vol36"].where(np.isfinite(o["vol36"]), vmed).clip(*orbit.VOL_CLIP)
    o["sc0"] = vol ** model["alpha"] * np.exp(o["h"].map(lambda h: float(delta.get(str(h), 0.0))) * o["ga_c"].abs().clip(upper=2))
    o["lvol"] = np.log(vol)
    o["aga"] = o["ga_c"].abs().clip(upper=2)
    o["aown"] = o["pe_rel_own"].abs().clip(upper=3)
    o["asec"] = o["pe_rel_sec"].abs().clip(upper=3)
    o["lmc"] = o["ln_mc"]
    o["ar12"] = o["ret12"].abs().clip(upper=2)
    o["apb"] = o["past_bias"].abs().clip(upper=1.5)
    o["tech"] = (o["grp"] != "非科技").astype(float)
    o["lpe"] = o["ln_pe"].clip(0, 6)
    return o


def design(d, feats, med=None):
    X = d[feats].to_numpy(float)
    if med is None:
        med = np.nanmedian(X, axis=0)
    X = np.where(np.isfinite(X), X, med)
    return np.column_stack([np.ones(len(X)), X]), med


# ---------- 方法 ----------
def qr_fit(X, y, tau):
    """線性分位數迴歸＝線性規劃：min Σ τ·u⁺ + (1−τ)·u⁻  s.t.  Xβ + u⁺ − u⁻ = y，u ≥ 0（HiGHS）。"""
    n, p = X.shape
    c = np.concatenate([np.zeros(p), np.full(n, tau), np.full(n, 1 - tau)])
    A = sparse.hstack([sparse.csr_matrix(X), sparse.identity(n, format="csr"), -sparse.identity(n, format="csr")], format="csr")
    r = linprog(c, A_eq=A, b_eq=y, bounds=[(None, None)] * p + [(0, None)] * (2 * n), method="highs")
    if not r.success:
        raise RuntimeError(r.message)
    return r.x[:p]


def q_pair(level):
    a = (1 - level) / 2
    return a, 1 - a


def band_pooled(cal, cur, y, level, scale="sc0", recent=None, hdr=False):
    if recent:
        yrs = sorted(cal["year"].unique())[-recent:]
        cal = cal[cal["year"].isin(yrs)]
    u = (cal[y] / cal[scale]).to_numpy(float)
    if hdr:                                              # 最短的 level 區間：起點 a 在 0～(1−level) 之間挑最窄
        best = None
        for a in np.linspace(0, 1 - level, 41):
            lo, hi = np.quantile(u, [a, a + level])
            best = (hi - lo, lo, hi) if best is None or hi - lo < best[0] else best
        lo, hi = best[1], best[2]
    else:
        lo, hi = np.quantile(u, q_pair(level))
    s = cur[scale].to_numpy(float)
    return lo * s, hi * s


def band_scale(cal, cur, y, level, feats):
    Xc, med = design(cal, feats)
    ly = np.log(np.abs(cal[y].to_numpy(float)) + 1e-3)
    beta = huber_ols(Xc, ly)
    s_cal = np.exp(Xc @ beta)
    lo, hi = np.quantile(cal[y].to_numpy(float) / s_cal, q_pair(level))
    Xt, _ = design(cur, feats, med)
    s = np.exp(Xt @ beta)
    return lo * s, hi * s, dict(beta=[float(v) for v in beta], q=[float(lo), float(hi)], med=[float(v) for v in med])


def band_qr(cal, cur, y, level, feats):
    Xc, med = design(cal, feats)
    yy = cal[y].to_numpy(float)
    a, b_ = q_pair(level)
    bl, bh = qr_fit(Xc, yy, a), qr_fit(Xc, yy, b_)
    Xt, _ = design(cur, feats, med)
    # 線索截在校準期的 1／99 分位（避免外推）
    lo_c, hi_c = np.nanpercentile(Xc[:, 1:], [1, 99], axis=0)
    Xt[:, 1:] = np.clip(Xt[:, 1:], lo_c, hi_c)
    lo, hi = Xt @ bl, Xt @ bh
    return np.minimum(lo, hi), np.maximum(lo, hi), dict(beta_lo=[float(v) for v in bl], beta_hi=[float(v) for v in bh], med=[float(v) for v in med],
                                                        clip=[[float(a_), float(b2)] for a_, b2 in zip(lo_c, hi_c)])


def band_gbm(cal, cur, y, level, feats):
    from sklearn.ensemble import HistGradientBoostingRegressor
    Xc, med = design(cal, feats)
    Xt, _ = design(cur, feats, med)
    out = []
    for tau in q_pair(level):
        m = HistGradientBoostingRegressor(loss="quantile", quantile=tau, learning_rate=0.05, max_iter=200, max_leaf_nodes=8,
                                          min_samples_leaf=60, l2_regularization=1.0, random_state=0)
        m.fit(Xc[:, 1:], cal[y].to_numpy(float))
        out.append(m.predict(Xt[:, 1:]))
    return np.minimum(*out), np.maximum(*out)


def iscore(yv, lo, hi, level):
    a = 1 - level
    return (hi - lo) + (2 / a) * np.maximum(lo - yv, 0) + (2 / a) * np.maximum(yv - hi, 0)


# ---------- 走動式評分 ----------
def walk(P, y, method, level, min_cal=200):
    rows, per_row = [], []
    for Y in sorted(P["year"].unique()):
        cur = P[P["year"] == Y]
        cal = P[P["T"] < cur["month"].min()]
        if len(cal) < min_cal:
            continue
        kind, _, spec = method.partition("-")
        if kind == "pooled":
            lo, hi = band_pooled(cal, cur, y, level)
        elif kind == "hdr":
            lo, hi = band_pooled(cal, cur, y, level, hdr=True)
        elif kind == "recent3":
            lo, hi = band_pooled(cal, cur, y, level, recent=3)
        elif kind == "unch":                             # 對照：本益比不變 ＋ 歷史分位（同尺度）
            lo, hi = band_pooled(cal, cur, "y_unch", level)
        elif kind == "scale":
            lo, hi, _ = band_scale(cal, cur, y, level, FEATS[spec])
        elif kind == "qr":
            lo, hi, _ = band_qr(cal, cur, y, level, FEATS[spec])
        elif kind == "gbm":
            lo, hi = band_gbm(cal, cur, y, level, FEATS["S3"])
        else:
            raise ValueError(method)
        yv = cur["y_unch" if kind == "unch" else y].to_numpy(float)
        inside = (yv >= lo) & (yv <= hi)
        rows.append(dict(年=int(Y), n=len(cur), 涵蓋=float(inside.mean()), 寬度=float(np.mean(hi - lo)), 分數=float(np.mean(iscore(yv, lo, hi, level)))))
        per_row.append(pd.DataFrame(dict(inside=inside, w=hi - lo, lo=lo, hi=hi), index=cur.index))
    t = pd.DataFrame(rows)
    pr = pd.concat(per_row) if per_row else None
    return t, pr


def summarize(t, pr):
    return dict(年數=len(t), 涵蓋平均=float(t["涵蓋"].mean()), 涵蓋最低=float(t["涵蓋"].min()), 涵蓋合計=float(pr["inside"].mean()),
                寬度=float(pr["w"].mean()), 倍數中位=float(np.exp(np.median(pr["w"]))), 分數=float(np.average(t["分數"], weights=t["n"])))


def own_range(P, level=0.8):
    """對照：公司自己過去 5 年本益比的 10／90 分位（只有 80%）。"""
    m = P["own_lo"].notna() & P["own_hi"].notna()
    d = P[m]
    yv = d["act"].to_numpy(float)
    inside = (yv >= d["own_lo"]) & (yv <= d["own_hi"])
    return dict(n=int(len(d)), 涵蓋=float(inside.mean()), 寬度=float(np.mean(d["own_hi"] - d["own_lo"])), 倍數中位=float(np.exp(np.median(d["own_hi"] - d["own_lo"]))),
                分數=float(np.mean(iscore(yv, d["own_lo"].to_numpy(float), d["own_hi"].to_numpy(float), level))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--fit", action="store_true", help="同時把正式版（全部已到期配對）的係數寫進 results/band_sharp.json 的 production")
    a = ap.parse_args()
    o = load(a.build, a.cache)
    pd.set_option("display.width", 220)
    out = dict(version="2026-10-15", levels=list(LEVELS), feats=FEATS, h={})
    methods = ["pooled", "hdr", "recent3", "scale-S1", "scale-S2", "scale-S3", "qr-S1", "qr-S2", "qr-S3", "gbm-S3"]
    for h in (6, 12, 24):
        P = o[o["h"] == h].copy()
        say(f"\n==================== {h} 個月：{len(P):,} 組（起點 {P['month'].min():%Y-%m}～{P['month'].max():%Y-%m}）")
        for y, nm in (("y_px", "股價"), ("y_pe", "本益比"), ("y_eps", "共識 EPS")):
            q = np.quantile(P[y], [0.1, 0.25, 0.5, 0.75, 0.9])
            say(f"  {nm}誤差 ln(實際 ÷ 預測) 的 10／25／50／75／90 分位：" + "、".join(f"{v:+.3f}" for v in q) + f"；80% 寬 {q[4] - q[0]:.3f}（高 ÷ 低 {np.exp(q[4] - q[0]):.2f} 倍）")
        say(f"  股價誤差與 EPS 誤差的相關：{np.corrcoef(P['y_px'], P['y_eps'])[0, 1]:+.2f}（本益比誤差 ＝ 股價誤差 − EPS 誤差）")
        hh = dict(n=int(len(P)), targets={})
        for y, nm in (("y_pe", "本益比"), ("y_px", "股價")):
            say(f"\n-- {nm}區間，80%（走動式；涵蓋 平均／最低／合計；寬度＝ln 高 − ln 低 的平均；倍數＝高 ÷ 低 的中位；分數越低越好）")
            res = {}
            for mth in methods + (["unch"] if y == "y_pe" else []):
                t, pr = walk(P, y, mth, 0.8)
                if t.empty:
                    continue
                s = summarize(t, pr)
                s["逐年"] = {int(r.年): round(float(r.涵蓋), 3) for r in t.itertuples()}
                res[mth] = s
                lab = "本益比不變＋歷史分位（對照）" if mth == "unch" else mth
                say(f"  {lab:28s} 涵蓋 {s['涵蓋平均']:.2f}／{s['涵蓋最低']:.2f}／{s['涵蓋合計']:.2f}  寬度 {s['寬度']:.3f}  倍數 {s['倍數中位']:.2f}  分數 {s['分數']:.3f}  "
                    + "逐年 " + " ".join(f"{yy}:{v:.2f}" for yy, v in s["逐年"].items()))
            if y == "y_pe":
                orng = own_range(P)
                res["own5y"] = orng
                say(f"  {'自己過去 5 年本益比 10–90%（對照）':28s} 涵蓋 {orng['涵蓋']:.2f}（n={orng['n']:,}）  寬度 {orng['寬度']:.3f}  倍數 {orng['倍數中位']:.2f}  分數 {orng['分數']:.3f}")
            # 邊界：名目水準 50～90%，每個方法的 涵蓋 vs 寬度
            say(f"  名目水準邊界（涵蓋合計／倍數中位）：")
            front = {}
            for mth in ("pooled", "qr-S2", "qr-S3", "scale-S2", "gbm-S3"):
                cells = []
                front[mth] = {}
                for lv in LEVELS:
                    t, pr = walk(P, y, mth, lv)
                    s = summarize(t, pr)
                    front[mth][str(lv)] = dict(涵蓋=round(s["涵蓋合計"], 3), 涵蓋最低=round(s["涵蓋最低"], 3), 倍數中位=round(s["倍數中位"], 3), 寬度=round(s["寬度"], 4), 分數=round(s["分數"], 4))
                    cells.append(f"{lv:.0%}: {s['涵蓋合計']:.2f}／{s['倍數中位']:.2f}")
                say(f"    {mth:10s} " + "  ".join(cells))
            hh["targets"][y] = dict(methods=res, frontier=front)
        out["h"][str(h)] = hh
    if a.fit:
        prod = {}
        cutoff = pd.Timestamp("2025-09-30")
        for h in (6, 12, 24):
            P = o[(o["h"] == h) & (o["T"] <= cutoff)]
            prod[str(h)] = dict(n=int(len(P)), months=[str(P["month"].min().date()), str(P["month"].max().date())], targets={})
            for y in ("y_pe", "y_px"):
                prod[str(h)]["targets"][y] = {}
                for lv in LEVELS:
                    _, _, info = band_qr(P, P.iloc[:5], y, lv, FEATS["S2"])
                    prod[str(h)]["targets"][y][str(lv)] = dict(beta_lo=info["beta_lo"], beta_hi=info["beta_hi"], med=info["med"], clip=info["clip"])
        out["production"] = dict(method="qr-S2", feats=FEATS["S2"], cutoff=str(cutoff.date()), h=prod)
    json.dump(out, open(os.path.join(RES, "band_sharp.json"), "w"), ensure_ascii=False, indent=1)
    open(os.path.join(RES, "band_sharp.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
