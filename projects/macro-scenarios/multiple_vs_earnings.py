#!/usr/bin/env python3
"""倍數 vs 獲利：成長股在每一格的拉鋸，誰贏。

股價變化 = (1 + 獲利成長) × (1 + 倍數變化) − 1 —— 兩項相乘。
scenario_model.py 給出四個情境的機率；本檔回答每一格裡這兩項誰壓過誰。

做法
----
1. 用 1881–2022 的席勒資料估「倍數在各種利率／通膨組合下實際動多少」
2. 換算成損益兩平的獲利成長：g* = 1/(1+m) − 1
3. 數每一格歷史窗的實際 EPS 中位數，看有多少比例過得了那個門檻

關鍵發現
--------
**倍數壓不壓縮，取決於通膨的方向，不是利率的方向。**

    長率↑ ＋ 通膨↑   倍數中位數 −4.5%   n=243
    長率↑ ＋ 通膨↓   倍數中位數 **+3.0%**  n=84   ← 利率漲，倍數反而擴張
    長率↓ ＋ 通膨↓   倍數中位數 +7.9%   n=191
    長率↓ ＋ 通膨↑   倍數中位數 −4.7%   n=88

而且幅度比直覺小得多。結果（高估值放大 1.5 倍後）：

    黏著        倍數 −6.8%  門檻 +7.3%   實際獲利 +14.1%  ⇒ **81% 過關**
    軟著陸      倍數 +11.8% 門檻 −10.6%  實際獲利 +12.0%  ⇒ 100% 過關
    停滯性通膨  倍數 −6.8%  門檻 +7.3%   實際獲利 −8.8%   ⇒ **0% 過關**
    成長驚嚇    倍數 +11.8% 門檻 −10.6%  實際獲利 −11.0%  ⇒ 50% 過關

⇒ **機率最高的「黏著」那一格，成長股是贏的**——獲利跑贏了倍數。
   真正要命的只有「通膨沒回去、獲利又轉壞」那一格。

⚠️ 三個限制（不要跳過）
---------------------
1. 席勒的 PE10 是**大盤**的平滑本益比，不是高估值成長股。高估值名字存續期間更長，
   倍數會放大（戈登模型一階近似：P/E ≈ 1/(r−g)）。本檔用 1.5 倍放大，
   **那個 1.5 是假設，不是估計值**。
2. 迴歸 R² 只有 0.02–0.10，且 1990 年後係數**翻正** ⇒
   「利率漲 → 倍數跌」在現代樣本不是穩定關係，這正是要按通膨方向拆開的理由。
3. **AI 資本支出週期沒有歷史樣本**（約三年大，從未遇過衰退）⇒
   「成長驚嚇時它會不會跟著砍」這題歷史答不了。可觀察的替代指標見 §4。

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

# 情境 → 對應哪一個歷史分組（軸是「通膨回不回得到目標」，所以只有兩種倍數環境）
SCENARIO_MAP = [
    ("黏著",       0, "通膨沒回去 ⇒ 倍數壓縮"),
    ("軟著陸",     2, "通膨回到目標 ⇒ 倍數擴張"),
    ("停滯性通膨", 0, "通膨沒回去 ⇒ 倍數壓縮（而且獲利也壞）"),
    ("成長驚嚇",   2, "通膨回到目標 ⇒ 倍數擴張（但獲利壞）"),
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
    print("     一家獲利真的在高速成長的公司，四格裡每一格都扛得住倍數壓縮。")
    print("     **真正的問題不是升息，是那個成長還在不在。**")

    print("\n【3】每一格實際的獲利，以及過關率")
    print("  （用 scenario_model 的四象限，數該格歷史窗的 EPS 中位數與超過門檻的比例）")
    try:
        import scenario_model as SM
        ri, re_ = SM.RANK_INFL, SM.RANK_EPS
        pf = SM.p_earnings_fall(SM.PAIRS, SM.P_EMPLOYMENT_BREAKS)
        ps = SM.P_INFLATION_STICKY
        cells = {
            "黏著":       [i for i in range(len(SM.PAIRS)) if ri[i] > 1-ps and re_[i] >= pf],
            "軟著陸":     [i for i in range(len(SM.PAIRS)) if ri[i] <= 1-ps and re_[i] >= pf],
            "停滯性通膨": [i for i in range(len(SM.PAIRS)) if ri[i] > 1-ps and re_[i] < pf],
            "成長驚嚇":   [i for i in range(len(SM.PAIRS)) if ri[i] <= 1-ps and re_[i] < pf],
        }
        print(f"  {'情境':<12}{'n':>5}{'EPS中位數':>11}{'倍數':>9}{'打平門檻':>10}{'過關率':>9}")
        for name, gi, _ in SCENARIO_MAP:
            idx = cells[name]
            eps = sorted(SM.PAIRS[i]["d_eps"] for i in idx)
            m = stats[gi][0] * DURATION_AMPLIFIER
            be = breakeven(m)
            passed = sum(1 for x in eps if x > be) / len(eps)
            print(f"  {name:<12}{len(idx):>5}{eps[len(eps)//2]:>10.1f}%{m:>8.1f}%"
                  f"{be:>9.1f}%{passed:>8.0%}")
        print("\n  ⇒ **機率最高的「黏著」那一格，成長股是贏的** —— 獲利跑贏了倍數。")
        print("     真正要命的只有「停滯性通膨」：0% 過關。")
    except Exception as e:
        print(f"  （需要 scenario_model.py 才能算：{e}）")

    print("\n【4】那個獲利成長還在不在？——這題歷史答不了")
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
