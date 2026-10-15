#!/usr/bin/env python3
"""README §26.2、§27：共識模式的區間——conformal 校準 → results/conformal.json（pef/unified.py、網頁用）

    python3 research/conformal_fit.py > results/conformal_fit.txt      # 先跑 research/unified_lab.py（產生 results/unified_rows.csv.gz）

正式版區間（orbit_fit.py、§22.4）是用「EPS 猜對」的走動式殘差校準的；實際使用時 EPS 是共識，誤差多了 EPS 那一塊，
80% 區間只涵蓋 57–63%（§25.1）。這裡改用「只有共識」時的實際誤差：
  u ＝ ln(實際 ÷ 預測) ÷ (波動^α × exp(δ_h × min(|ln(共識 EPS_a ÷ 今天 EPS)|, 2)))      α、δ 和軌道區間相同
  （符號和軌道區間一致：區間 ＝ 預測 × exp(尺度 × 分位數)。2026-10-15 前誤用 ln(預測 ÷ 實際)，網頁區間上下顛倒；涵蓋率的檢查是對稱的，所以當時沒抓到）
§27：股價和本益比分開校準。本益比誤差 ＝ 股價誤差 − 共識 EPS 誤差（ln(實際本益比 ÷ 預測) ＝ ln(實際股價 ÷ 預測股價) − ln(實際 EPS ÷ 共識)），
  本益比區間寬主要是 EPS 會錯多少；股價誤差窄 1/3。所以：
    pe   ＝ 本益比誤差的分位數（同上）        px ＝ 股價誤差的分位數（同尺度）        eps ＝ 共識 EPS 誤差 ln(實際 ÷ 共識) 的分位數（不除以波動）
  每個都給 50／60／70／80／90% 的等尾區間（levels：{水準: [低分位, 高分位]}），讓使用者自己挑「命中率 vs 寬度」。q（[10,25,75,90]，本益比）保留給舊讀法。
  分位數取自已到期的配對；正式版＝目標日 ≤ 資料截止（2025-09）的全部配對；依組別（科技／非科技）各一組，樣本 < 300 用全部。
走動式驗證：每個起點年份只用「目標日在該年第一個起點月以前」的配對校準，看那一年的涵蓋率（＝實際使用時能做到的）；每個水準、股價與本益比都報。
不置中（conformal 保留偏差）：共識模式的誤差有整體偏差（軌道低估本益比），置中會把它藏起來。
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from pef import orbit                                    # noqa: E402

RES = os.path.join(HERE, "results")
Q = (0.1, 0.25, 0.75, 0.9)
LEVELS = (50, 60, 70, 80, 90)
MIN_N = 300
TARGETS = (("pe", "本益比"), ("px", "股價"), ("eps", "共識 EPS"))


def qpair(level):
    a = (1 - level / 100) / 2
    return [a, 1 - a]


def levels_of(u):
    return {str(L): [float(v) for v in np.quantile(u, qpair(L))] for L in LEVELS}


def main():
    o = pd.read_csv(os.path.join(RES, "unified_rows.csv.gz"), parse_dates=["month", "T"])
    model = orbit.load_model()
    alpha = model["alpha"]
    delta = model.get("band_delta") or {}
    out = dict(version="2026-10-15b",
               note="README §26.2／§27：共識模式（只有共識、沒有自己的看法）的區間。q＝本益比 u 的 [10,25,75,90]% 分位（舊讀法）；"
                    "pe／px＝本益比／股價誤差 u＝ln(實際÷預測)÷(波動^α×exp(δ|ga|)) 的等尾分位，eps＝ln(實際 EPS÷共識)（不除以波動）；levels 鍵＝涵蓋水準 50–90；不置中；區間＝預測×exp(尺度×分位數)",
               alpha=alpha, delta={h: float(delta.get(h, 0.0)) for h in ("6", "12", "24")}, min_n=MIN_N, levels=list(LEVELS), cutoff="2025-09-30", h={})
    pd.set_option("display.width", 220)
    for h in (6, 12, 24):
        P = o[(o["h"] == h) & o["C"].notna()].copy()
        vmed = float(P["vol36"].median())
        vol = P["vol36"].where(np.isfinite(P["vol36"]), vmed).clip(*orbit.VOL_CLIP) ** alpha
        P["sc"] = vol * np.exp(float(delta.get(str(h), 0.0)) * P["ga_c"].abs().clip(upper=2))
        P["u"] = -P["C"] / P["sc"]                      # 本益比：C ＝ ln(預測 ÷ 實際)；區間要的是 ln(實際 ÷ 預測)
        P["u_px"] = -(P["C"] + P["eps_err"]) / P["sc"]  # 股價：ln(實際股價 ÷ 預測股價) ＝ 本益比誤差 ＋ EPS 誤差（eps_err ＝ ln(共識 ÷ 實際)）
        P["u_eps"] = -P["eps_err"]                      # 共識 EPS：ln(實際 ÷ 共識)
        P["tech"] = P["grp"] != "非科技"
        ucol = {"pe": "u", "px": "u_px", "eps": "u_eps"}
        print(f"\n== {h} 個月：{len(P):,} 組（目標日 {P['T'].min():%Y-%m}～{P['T'].max():%Y-%m}）；共識模式中位 |ln 本益比誤差| {np.median(np.abs(P['C'])):.3f}、"
              f"|ln 股價誤差| {np.median(np.abs(P['C'] + P['eps_err'])):.3f}、|ln EPS 誤差| {np.median(np.abs(P['eps_err'])):.3f}")
        rows, lv_rows = [], []
        for Y in sorted(P["year"].unique()):
            cur = P[P["year"] == Y]
            mat = P[P["T"] < cur["month"].min()]
            r = dict(年=int(Y), n=len(cur))
            if len(mat) >= 200:
                lo, hi = np.quantile(mat["u"], [0.1, 0.9])
                r["全部校準"] = float(((cur["u"] >= lo) & (cur["u"] <= hi)).mean())
                for key, m in (("科技", cur["tech"]), ("非科技", ~cur["tech"])):
                    mm = mat[mat["tech"] == (key == "科技")]
                    src = mm if len(mm) >= MIN_N else mat
                    lo2, hi2 = np.quantile(src["u"], [0.1, 0.9])
                    r[f"{key}（分組校準）"] = float(((cur.loc[m, "u"] >= lo2) & (cur.loc[m, "u"] <= hi2)).mean()) if m.any() else np.nan
                    r[f"{key}（全部校準）"] = float(((cur.loc[m, "u"] >= lo) & (cur.loc[m, "u"] <= hi)).mean()) if m.any() else np.nan
                lr = dict(年=int(Y), n=len(cur))
                for tk, _ in TARGETS:
                    for L in LEVELS:
                        lo3, hi3 = np.quantile(mat[ucol[tk]], qpair(L))
                        v = cur[ucol[tk]]
                        lr[f"{tk}{L}"] = float(((v >= lo3) & (v <= hi3)).mean())
                        lr[f"{tk}{L}w"] = float(np.mean((hi3 - lo3) * (cur["sc"] if tk != "eps" else 1.0)))
                lv_rows.append(lr)
            rows.append(r)
        t = pd.DataFrame(rows)
        print(t.round(2).to_string(index=False))
        cov = t.dropna(subset=["全部校準"]) if "全部校準" in t else t
        summ = {c: (float(cov[c].mean()), float(cov[c].min())) for c in cov.columns if c not in ("年", "n")}
        print("  走動式涵蓋（本益比 80%；平均／最低）：" + "；".join(f"{k} {v[0]:.2f}／{v[1]:.2f}" for k, v in summ.items()))
        lt = pd.DataFrame(lv_rows)
        wf_cover = {}
        print("  各水準走動式涵蓋（全部校準；平均／最低；倍數＝高 ÷ 低 的平均寬度換算）：")
        for tk, nm in TARGETS:
            wf_cover[tk] = {}
            cells = []
            for L in LEVELS:
                c_ = lt[f"{tk}{L}"]
                w_ = float(np.average(lt[f"{tk}{L}w"], weights=lt["n"]))
                wf_cover[tk][str(L)] = dict(avg=round(float(c_.mean()), 3), min=round(float(c_.min()), 3), by_year={int(y): round(float(v), 3) for y, v in zip(lt["年"], c_)},
                                            width=round(w_, 4))
                cells.append(f"{L}%: {c_.mean():.2f}／{c_.min():.2f}（×{np.exp(w_):.2f}）")
            print(f"    {nm:6s} " + "  ".join(cells))
        # 正式版：全部已到期
        hh = dict(vol_median=vmed, n=len(P), wf_cover80={k: round(v[0], 3) for k, v in summ.items()},
                  wf_by_year={int(r["年"]): round(float(r["全部校準"]), 3) for _, r in cov.iterrows()}, wf_cover=wf_cover)
        for key, m in (("pooled", P["tech"].notna()), ("tech", P["tech"]), ("other", ~P["tech"])):
            u = P.loc[m, "u"]
            hh[key] = dict(n=int(len(u)), q=[float(v) for v in np.quantile(u, Q)], median=float(np.median(u)),
                           **{tk: levels_of(P.loc[m, ucol[tk]]) for tk, _ in TARGETS})
        out["h"][str(h)] = hh
        print("  正式版分位數（本益比 u）：" + "；".join(f"{k} n={hh[k]['n']} " + "、".join(f"{v:+.3f}" for v in hh[k]["q"]) for k in ("pooled", "tech", "other")))
        for tk, nm in TARGETS:
            print(f"  正式版 {nm} 各水準（全部）：" + "；".join(f"{L}% [{v[0]:+.3f}, {v[1]:+.3f}]" for L, v in hh["pooled"][tk].items()))
        q_old = model["h"][str(h)]["bands"].get("預期b＋修正ab", model["h"][str(h)]["bands"]["軌道"])["q"]
        print(f"  對照正式版（EPS 猜對校準）的分位數：" + "、".join(f"{v:+.3f}" for v in q_old) + f"；80% 寬度 {q_old[3] - q_old[0]:.2f} → conformal 本益比 {hh['pooled']['q'][3] - hh['pooled']['q'][0]:.2f}"
              f"（×{(hh['pooled']['q'][3] - hh['pooled']['q'][0]) / (q_old[3] - q_old[0]):.2f}）、股價 {hh['pooled']['px']['80'][1] - hh['pooled']['px']['80'][0]:.2f}")
    json.dump(out, open(os.path.join(RES, "conformal.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
