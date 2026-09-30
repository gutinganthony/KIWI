#!/usr/bin/env python3
"""外部審查建議的兩個檢查，用在「沒有 EPS：模型自己估」的組合模型上（S&P 500 走動式回測，results/broad_predictions.csv.gz）。

    python3 review_checks.py

1. 依預測距離往「本益比不變」收縮：預測 ＝ 今天 ＋ λ ×（組合預測 − 今天），λ 只在選模期（預測起點 2015–2021）挑，保留期（2022 以後）驗收。
2. 方向命中率的基準：「永遠猜本益比會跌」「永遠猜會漲」各猜對幾成（平手算錯）。
輸出：results/review_old.txt、review_old_shrink.csv、review_old_direction.csv（README §15.7、REVIEW_RESPONSE.md）
"""
import io
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
SEL, HOLD = ("2015-01-01", "2021-12-31"), ("2022-01-01", "2026-12-31")
GRID = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25]
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def main():
    p = pd.read_csv(os.path.join(RES, "broad_predictions.csv.gz"), parse_dates=["month"])
    p = p[p["ln_pe"].notna() & p["actual"].notna() & p["E_all"].notna()]
    shr, dr = [], []
    for h, g in p.groupby("h"):
        per = {nm: g[(g["month"] >= a) & (g["month"] <= b)] for nm, (a, b) in (("選模期", SEL), ("保留期", HOLD))}
        err = lambda x, lam: float(np.median(np.abs(x["ln_pe"] + lam * (x["E_all"] - x["ln_pe"]) - x["actual"])))
        es = [err(per["選模期"], lam) for lam in GRID]
        best = GRID[int(np.argmin(es))]
        shr.append(dict(h=h, 選到的λ=best, **{f"選模期_λ={lam}": e for lam, e in zip(GRID, es)},
                        保留期_選到的λ=err(per["保留期"], best), 保留期_λ1_原模型=err(per["保留期"], 1.0),
                        保留期_λ0_本益比不變=err(per["保留期"], 0.0), n_保留期=len(per["保留期"])))
        for nm, x in per.items():
            up = np.sign(x["actual"] - x["ln_pe"])
            pr = np.sign(x["E_all"] - x["ln_pe"])
            dr.append(dict(h=h, 期間=nm, n=len(x), 模型=float(((pr == up) & (pr != 0)).mean()),
                           永遠猜跌=float((up < 0).mean()), 永遠猜漲=float((up > 0).mean()), 模型猜跌的比例=float((pr < 0).mean())))
    shr, dr = pd.DataFrame(shr), pd.DataFrame(dr)
    say("== 組合模型往「本益比不變」收縮（中位 |ln 誤差|；λ＝0 是本益比不變、λ＝1 是原模型；λ 在選模期挑）")
    say(shr.round(4).to_string(index=False))
    say("\n== 方向命中率（本益比 h 個月後比今天高還是低；平手算錯）vs 永遠猜跌／永遠猜漲")
    say(dr.round(3).to_string(index=False))
    shr.to_csv(os.path.join(RES, "review_old_shrink.csv"), index=False, float_format="%.6f")
    dr.to_csv(os.path.join(RES, "review_old_direction.csv"), index=False, float_format="%.6f")
    open(os.path.join(RES, "review_old.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()
