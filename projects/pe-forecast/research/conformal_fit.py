#!/usr/bin/env python3
"""README §26.2：共識模式的區間——conformal 校準 → results/conformal.json（pef/unified.py、網頁用）

    python3 research/conformal_fit.py > results/conformal_fit.txt      # 先跑 research/unified_lab.py（產生 results/unified_rows.csv.gz）

正式版區間（orbit_fit.py、§22.4）是用「EPS 猜對」的走動式殘差校準的；實際使用時 EPS 是共識，誤差多了 EPS 那一塊，
80% 區間只涵蓋 57–63%（§25.1）。這裡改用「只有共識」時的實際誤差：
  u ＝ ln(預測本益比 ÷ 實際) ÷ (波動^α × exp(δ_h × min(|ln(共識 EPS_a ÷ 今天 EPS)|, 2)))      α、δ 和軌道區間相同
  分位數（10／25／75／90%）取自已到期的配對；正式版＝目標日 ≤ 資料截止（2025-09）的全部配對；依組別（科技／非科技）各一組，樣本 < 300 用全部。
走動式驗證：每個起點年份只用「目標日在該年第一個起點月以前」的配對校準，看那一年的涵蓋率（＝實際使用時能做到的）。
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
MIN_N = 300


def main():
    o = pd.read_csv(os.path.join(RES, "unified_rows.csv.gz"), parse_dates=["month", "T"])
    model = orbit.load_model()
    alpha = model["alpha"]
    delta = model.get("band_delta") or {}
    out = dict(version="2026-10-15", note="README §26.2：共識模式（只有共識、沒有自己的看法）的區間分位數 [10,25,75,90]%，已除以 波動^α × exp(δ|ga|)；不置中",
               alpha=alpha, delta={h: float(delta.get(h, 0.0)) for h in ("6", "12", "24")}, min_n=MIN_N, cutoff="2025-09-30", h={})
    pd.set_option("display.width", 220)
    for h in (6, 12, 24):
        P = o[(o["h"] == h) & o["C"].notna()].copy()
        vmed = float(P["vol36"].median())
        vol = P["vol36"].where(np.isfinite(P["vol36"]), vmed).clip(*orbit.VOL_CLIP) ** alpha
        P["sc"] = vol * np.exp(float(delta.get(str(h), 0.0)) * P["ga_c"].abs().clip(upper=2))
        P["u"] = P["C"] / P["sc"]
        P["tech"] = P["grp"] != "非科技"
        print(f"\n== {h} 個月：{len(P):,} 組（目標日 {P['T'].min():%Y-%m}～{P['T'].max():%Y-%m}）；共識模式中位 |ln 本益比誤差| {np.median(np.abs(P['C'])):.3f}")
        rows = []
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
            rows.append(r)
        t = pd.DataFrame(rows)
        print(t.round(2).to_string(index=False))
        cov = t.dropna(subset=["全部校準"]) if "全部校準" in t else t
        summ = {c: (float(cov[c].mean()), float(cov[c].min())) for c in cov.columns if c not in ("年", "n")}
        print("  走動式涵蓋（平均／最低）：" + "；".join(f"{k} {v[0]:.2f}／{v[1]:.2f}" for k, v in summ.items()))
        # 正式版：全部已到期
        hh = dict(vol_median=vmed, n=len(P), wf_cover80={k: round(v[0], 3) for k, v in summ.items()},
                  wf_by_year={int(r["年"]): round(float(r["全部校準"]), 3) for _, r in cov.iterrows()})
        for key, m in (("pooled", P["tech"].notna()), ("tech", P["tech"]), ("other", ~P["tech"])):
            u = P.loc[m, "u"]
            hh[key] = dict(n=int(len(u)), q=[float(v) for v in np.quantile(u, Q)], median=float(np.median(u)))
        out["h"][str(h)] = hh
        print("  正式版分位數（u）：" + "；".join(f"{k} n={hh[k]['n']} " + "、".join(f"{v:+.3f}" for v in hh[k]["q"]) for k in ("pooled", "tech", "other")))
        q_old = model["h"][str(h)]["bands"].get("預期b＋修正ab", model["h"][str(h)]["bands"]["軌道"])["q"]
        print(f"  對照正式版（EPS 猜對校準）的分位數：" + "、".join(f"{v:+.3f}" for v in q_old) + f"；80% 寬度 {q_old[3] - q_old[0]:.2f} → conformal {hh['pooled']['q'][3] - hh['pooled']['q'][0]:.2f}（×{(hh['pooled']['q'][3] - hh['pooled']['q'][0]) / (q_old[3] - q_old[0]):.2f}）")
    json.dump(out, open(os.path.join(RES, "conformal.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
