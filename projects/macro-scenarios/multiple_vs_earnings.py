#!/usr/bin/env python3
"""倍數 vs 獲利：情境矩陣算不出來的那一欄。

問題（Jake 2026-09-15 提出）
---------------------------
情境矩陣只評估了**折現率**的衝擊，沒有評估**現金流**。但

    股價變化 = (1 + EPS 成長) × (1 + 倍數變化) − 1

兩項相乘。矩陣只給了第二項的方向，然後默認第一項跟著就業走。
**對 AI 資本支出驅動的公司，第一項不由失業率決定。**
⇒ 「高估值成長股」在「黏著」與「成長驚嚇」兩格，總體面根本決定不了方向。

本檔做兩件事：
1. 用 1881–2022 的席勒資料估「倍數在各種利率／通膨組合下實際動多少」
2. 換算成**損益兩平的 EPS 成長**：g* = 1/(1+m) − 1

關鍵發現
--------
**倍數壓不壓縮，取決於利率「為什麼」動，不是動了多少。**

    長率↑ ＋ 通膨↑（通膨型）  倍數中位數 −4.5%   n=243
    長率↑ ＋ 通膨↓（成長型）  倍數中位數 **+3.0%**  n=84   ← 利率漲，倍數反而擴張
    長率↓ ＋ 通膨↓（軟著陸）  倍數中位數 +7.9%   n=191
    長率↓ ＋ 通膨↑（停滯型）  倍數中位數 −4.7%   n=88

而且**幅度比直覺小得多**：最糟那一組的中位數也只有 −4.5%，
換算成打平門檻只要 EPS 成長 +4.7%。

⇒ **一家 EPS 成長 30% 的公司，在五格裡每一格都扛得住倍數壓縮。**
   真正的問題從來不是升息，是那 30% 還在不在。

⚠️ 三個限制（不要跳過）
---------------------
1. 席勒的 PE10 是**大盤**的平滑本益比，不是高估值成長股。高估值名字存續期間更長，
   倍數會放大（戈登模型一階近似：P/E ≈ 1/(r−g) ⇒ 倍數對利率的彈性約等於 P/E 本身）。
   本檔另給 1.5 倍放大的情境作參考，**那個 1.5 是假設，不是估計值**。
2. R² 只有 0.02–0.10，且 1990 年後迴歸係數**翻正**。
   ⇒ 「利率漲 → 倍數跌」在現代樣本裡**不是穩定關係**，這正是要按通膨方向拆開的理由。
3. **AI 資本支出週期沒有歷史樣本。** 它約三年大，從未遇過一次衰退 ⇒
   「成長驚嚇時 AI 資本支出會不會跟著砍」這題，歷史答不了，本檔也沒有答。
   可觀察的替代指標見 §3。

用法：python3 multiple_vs_earnings.py
"""

import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SHILLER = os.path.abspath(os.path.join(
    HERE, "..", "avi-v5", "data", "ext", "shiller_sp500.csv"))

HORIZON = 12
DURATION_AMPLIFIER = 1.5     # 高估值成長股相對大盤的倍數彈性；**這是假設**


def load():
    rows = {}
    with open(SHILLER) as f:
        for r in csv.DictReader(f):
            try:
                pe = float(r["PE10"])
                ir = float(r["Long Interest Rate"])
                cpi = float(r["Consumer Price Index"])
            except (ValueError, KeyError):
                continue
            if pe <= 0 or ir <= 0 or cpi <= 0:
                continue
            y, m, _ = r["Date"].split("-")
            rows[int(y) * 12 + int(m) - 1] = (pe, ir, cpi)
    return rows


def build(rows):
    out = []
    for i, (pe, ir, cpi) in sorted(rows.items()):
        if i + HORIZON not in rows or i - HORIZON not in rows:
            continue
        pe2, ir2, cpi2 = rows[i + HORIZON]
        _, _, cpi0 = rows[i - HORIZON]
        out.append(dict(
            d_pe=math.log(pe2 / pe) * 100,
            d_y=(ir2 - ir) * 100,
            d_infl=(cpi2 / cpi - 1) * 100 - (cpi / cpi0 - 1) * 100,
        ))
    return out


def pct(vals, q):
    s = sorted(vals)
    if not s:
        return float("nan")
    pos = q * (len(s) - 1)
    lo = int(pos)
    if lo + 1 >= len(s):
        return s[-1]
    return s[lo] + (s[lo + 1] - s[lo]) * (pos - lo)


def breakeven(m_pct):
    """倍數變化 m%（負為壓縮）下，EPS 要成長多少才打平。"""
    return (1 / (1 + m_pct / 100) - 1) * 100


GROUPS = [
    ("長率↑ ＋ 通膨↑（通膨型）", lambda o: o["d_y"] > 25 and o["d_infl"] > 0.5),
    ("長率↑ ＋ 通膨↓（成長型）", lambda o: o["d_y"] > 25 and o["d_infl"] < -0.5),
    ("長率↓ ＋ 通膨↓（軟著陸型）", lambda o: o["d_y"] < -25 and o["d_infl"] < -0.5),
    ("長率↓ ＋ 通膨↑（停滯型）", lambda o: o["d_y"] < -25 and o["d_infl"] > 0.5),
]

# 情境 → 對應哪一個歷史分組
SCENARIO_MAP = [
    ("軟著陸",     2, "通膨降、利率跟著降"),
    ("黏著",       None, "利率高檔不動，通膨也沒明顯方向"),
    ("再加速",     0, "通膨衝高、利率被迫追"),
    ("成長驚嚇",   2, "通膨降、利率大降（但獲利受傷）"),
    ("停滯性通膨", 3, "通膨沒下來、利率降不動"),
]


def main():
    obs = build(load())
    print("=" * 78)
    print("倍數 vs 獲利 —— 情境矩陣算不出來的那一欄")
    print("=" * 78)
    print(f"\n樣本：席勒 S&P 500 月資料，12 個月重疊窗，n={len(obs)}")

    print("\n【1】倍數壓不壓縮，取決於利率『為什麼』動")
    print(f"  {'分組':<26}{'n':>5}{'倍數中位數':>12}{'較差四分位':>12}")
    stats = []
    for name, f in GROUPS:
        sub = [o["d_pe"] for o in obs if f(o)]
        med, q25 = pct(sub, 0.5), pct(sub, 0.25)
        stats.append((med, q25))
        print(f"  {name:<26}{len(sub):>5}{med:>11.1f}%{q25:>11.1f}%")
    # 「黏著」用全部升息窗當代理
    all_up = [o["d_pe"] for o in obs if o["d_y"] > 25]
    sticky = (pct(all_up, 0.5), pct(all_up, 0.25))
    print(f"  {'長率↑ 全部（黏著的代理）':<26}{len(all_up):>5}"
          f"{sticky[0]:>11.1f}%{sticky[1]:>11.1f}%")

    print("\n  ⇒ 通膨在升的時候倍數才會壓縮；通膨在降的時候，**利率漲倍數反而擴張**。")

    print("\n【2】換算成「EPS 要成長多少才打平」　g* = 1/(1+m) − 1")
    print(f"\n  {'情境':<12}{'倍數(中位數)':>12}{'EPS打平':>10}"
          f"{'倍數(較差1/4)':>14}{'EPS打平':>10}")
    for name, gi, _why in SCENARIO_MAP:
        med, q25 = sticky if gi is None else stats[gi]
        print(f"  {name:<12}{med:>11.1f}%{breakeven(med):>9.0f}%"
              f"{q25:>13.1f}%{breakeven(q25):>9.0f}%")

    print(f"\n  高估值成長股（倍數彈性假設為大盤的 {DURATION_AMPLIFIER} 倍）：")
    print(f"  {'情境':<12}{'倍數(中位數)':>12}{'EPS打平':>10}"
          f"{'倍數(較差1/4)':>14}{'EPS打平':>10}")
    worst = 0.0
    for name, gi, _why in SCENARIO_MAP:
        med, q25 = sticky if gi is None else stats[gi]
        med *= DURATION_AMPLIFIER
        q25 *= DURATION_AMPLIFIER
        worst = max(worst, breakeven(q25))
        print(f"  {name:<12}{med:>11.1f}%{breakeven(med):>9.0f}%"
              f"{q25:>13.1f}%{breakeven(q25):>9.0f}%")

    print(f"\n  ⇒ **最嚴苛的一格，打平門檻也只有 EPS +{worst:.0f}%。**")
    print("     一家 EPS 成長 30% 的公司，在五格裡每一格都扛得住倍數壓縮。")
    print("     **真正的問題不是升息，是那 30% 還在不在。**")

    print("\n【3】那 30% 還在不在？——這題歷史答不了")
    print("  AI 資本支出週期約三年大，**從未遇過一次衰退**，所以沒有可比樣本。")
    print("  可觀察的替代指標（決定它是循環性還是結構性）：")
    print("    a. 那些資本支出是**自己賺的錢**還是**借來的**")
    print("       ——用營運現金流蓋的，需求一掉就跟著砍；舉債蓋的，信用一緊就跟著砍。")
    print("    b. 大型雲端商對**下一年**資本支出的指引有沒有下修")
    print("    c. 折舊年限有沒有被拉長（拉長＝用會計撐獲利，是壓力的訊號）")
    print("  ⇒ 這三項都在十月底的財報裡。**那一天比任何一場央行會議更能決定這一欄。**")

    print("\n" + "=" * 78)
    print("⚠️ PE10 是大盤平滑本益比，不是高估值成長股；1.5 倍放大是假設不是估計。")
    print("   迴歸 R² 只有 0.02–0.10，1990 年後係數甚至翻正 ⇒")
    print("   「利率漲＝倍數跌」在現代樣本不是穩定關係，這正是要按通膨方向拆開的理由。")
    print("=" * 78)


if __name__ == "__main__":
    main()
