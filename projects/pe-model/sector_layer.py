#!/usr/bin/env python3
"""
sector_layer.py — 模組化本益比模型（產業層）

  產業本益比 ＝ 市場合理本益比 × 產業相對倍數

  ln(PE_s) = ln(PE_market) + α_s + β_s·(實質利率 − 基準) + γ_s·(通膨 − 基準) + δ_s·(產業 EPS 成長 − 市場 EPS 成長)

    α_s  產業的長期相對倍數（ln 相對本益比的平均）
    β_s  產業對實質利率「超出市場」的敏感度 —— 久期差。市場層已經含 −8.6，這裡只放差額
    γ_s  對通膨「超出市場」的敏感度 —— 成本轉嫁能力
    δ_s  相對盈餘成長溢價

  ⚠️ 結構已定，係數未校準。repo 裡沒有任何產業級本益比歷史序列，所以我不編數字。
     給它一個 data/sector_pe.csv（欄位：date,sector,pe，月頻或季頻，至少十年），
     `python3 sector_layer.py calibrate` 會把 α/β/γ 估出來、存到 data/sector_params.json，
     之後 `python3 sector_layer.py apply --market-pe 21.3 --real10 0.0124 --infl 0.0336` 就能出各產業合理本益比。

  沒有校準檔時，apply 會拒絕輸出數字，只印理論上的符號方向。
"""
import argparse
import csv
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SECTOR_PE = os.path.join(DATA, "sector_pe.csv")
PARAMS = os.path.join(DATA, "sector_params.json")

sys.path.insert(0, HERE)
from pe_model import load, features, ols_hac  # noqa: E402

# 理論方向（Gordon：P/E ∝ 1/(r − g)，久期越長對 r 越敏感；成本轉嫁決定通膨敏感度）。
# 只有符號，沒有數字 —— 數字要用資料估。
THEORY = {
    "科技／成長":       dict(beta="−（久期長，對實質利率比市場更敏感）", gamma="−／0", note="α 通常 >0"),
    "公用事業":         dict(beta="−（債券替代品）", gamma="−（受管制，轉嫁慢）", note="α 通常 <0"),
    "必需消費":         dict(beta="−（債券替代品，但弱於公用）", gamma="0／＋（轉嫁能力）", note=""),
    "金融":             dict(beta="＋（利差受益）", gamma="−（通膨侵蝕帳面）", note="α 通常 <0"),
    "能源／原物料":     dict(beta="＋／0", gamma="＋（通膨受益）", note="α 隨商品循環大幅波動"),
    "工業／循環消費":   dict(beta="−／0", gamma="−（成本先漲、售價後漲）", note=""),
    "醫療":             dict(beta="−／0", gamma="0", note=""),
}


def _read_sector_pe():
    if not os.path.exists(SECTOR_PE):
        return None
    rows = list(csv.DictReader(open(SECTOR_PE)))
    out = {}
    for r in rows:
        try:
            pe = float(r["pe"])
        except (TypeError, ValueError):
            continue
        if pe <= 0:
            continue
        out.setdefault(r["sector"].strip(), {})[r["date"][:7]] = pe
    return out


def calibrate(args):
    sec = _read_sector_pe()
    if not sec:
        raise SystemExit(f"找不到 {SECTOR_PE}。格式：date,sector,pe（date 為 YYYY-MM 或 YYYY-MM-DD）。")
    d = load()
    y, F = features(d)
    months = d["months"]
    mi = {m: i for i, m in enumerate(months)}
    params = {}
    print(f"{'產業':16s} {'n':>4s} {'α(相對倍數)':>12s} {'β(實質利率)':>12s} {'t':>5s} {'γ(通膨)':>9s} {'t':>5s} {'R²':>5s}")
    for s, series in sorted(sec.items()):
        rows = []
        for ym, pe in series.items():
            i = mi.get(ym)
            if i is None or np.isnan(y[i]) or np.isnan(F["real10"][i]) or np.isnan(F["infl"][i]):
                continue
            # 相對於「實際」市場本益比（不是模型值），這樣 α/β/γ 只描述產業相對市場的部分
            rows.append((math.log(pe) - y[i], F["real10"][i], F["infl"][i]))
        if len(rows) < 60:
            print(f"{s:16s} {len(rows):>4d}   資料不足（<60 個月），略過")
            continue
        A = np.array(rows)
        X = np.column_stack([np.ones(len(A)), A[:, 1] - A[:, 1].mean(), A[:, 2] - A[:, 2].mean()])
        beta, se, r2, _, _ = ols_hac(A[:, 0], X, L=12)
        params[s] = dict(alpha=beta[0], beta=beta[1], gamma=beta[2], delta=0.0,
                         real10_ref=float(A[:, 1].mean()), infl_ref=float(A[:, 2].mean()),
                         n=len(A), r2=r2, t_beta=beta[1] / se[1], t_gamma=beta[2] / se[2])
        print(f"{s:16s} {len(A):>4d} {beta[0]:>12.3f} {beta[1]:>12.2f} {beta[1]/se[1]:>5.1f} {beta[2]:>9.2f} {beta[2]/se[2]:>5.1f} {r2:>5.2f}")
    if not params:
        raise SystemExit("沒有任何產業有足夠資料。")
    json.dump(params, open(PARAMS, "w"), ensure_ascii=False, indent=2)
    print(f"\n已寫入 {PARAMS}。δ（相對成長溢價）預設 0，需要產業 EPS 成長序列才能估。")


def apply(args):
    if not os.path.exists(PARAMS):
        print("⚠️ 產業層尚未校準（沒有 data/sector_params.json），不輸出數字。\n")
        print("理論上的方向（符號），供你判斷資料進來後結果合不合理：")
        print(f"  {'產業':14s} {'β 實質利率':30s} {'γ 通膨':26s} 備註")
        for s, t in THEORY.items():
            print(f"  {s:14s} {t['beta']:30s} {t['gamma']:26s} {t['note']}")
        print("\n要校準：放 data/sector_pe.csv（date,sector,pe），跑 `python3 sector_layer.py calibrate`。")
        print("可用來源（都要在 Mac 上抓）：TWSE 月報「上市公司本益比（依產業）」2005 起；")
        print("Damodaran `pedata.xls`（美股產業，年頻，1999 起）；FactSet／S&P 各板塊 P/E。")
        return
    params = json.load(open(PARAMS))
    if args.market_pe is None or args.real10 is None or args.infl is None:
        raise SystemExit("apply 需要 --market-pe --real10 --infl（都用小數，例：--real10 0.0124）")
    print(f"市場合理本益比 {args.market_pe:.1f}  實質利率 {args.real10*100:.2f}%  通膨 {args.infl*100:.2f}%\n")
    print(f"  {'產業':16s} {'相對倍數':>8s} {'合理本益比':>10s}   n    R²")
    for s, p in sorted(params.items()):
        rel = p["alpha"] + p["beta"] * (args.real10 - p["real10_ref"]) + p["gamma"] * (args.infl - p["infl_ref"])
        if args.growth_gap is not None:
            rel += p["delta"] * args.growth_gap
        print(f"  {s:16s} {math.exp(rel):>8.2f}× {args.market_pe*math.exp(rel):>10.1f}   {p['n']:>3d}  {p['r2']:.2f}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("calibrate")
    a = sub.add_parser("apply")
    a.add_argument("--market-pe", type=float)
    a.add_argument("--real10", type=float)
    a.add_argument("--infl", type=float)
    a.add_argument("--growth-gap", type=float, help="產業 EPS 成長 − 市場 EPS 成長（小數）")
    args = ap.parse_args()
    calibrate(args) if args.cmd == "calibrate" else apply(args)


if __name__ == "__main__":
    main()
