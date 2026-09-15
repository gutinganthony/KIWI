#!/usr/bin/env python3
"""每一格裡，股票實際發生了什麼 —— 直接量，不做分解。

為什麼不用「倍數 × 獲利」去推
-----------------------------
恆等式是  股價報酬 ＝ 獲利成長 ＋ 本益比變化（取對數後相加）。
但這兩項**不是獨立的**：trailing EPS 掉的時候，本益比會**機械性地**上升
（分母變小）。所以「假設倍數壓縮 x%，那獲利要成長多少才打平」是**循環論證**——
你不能一邊固定倍數、一邊變動獲利，因為倍數本來就是獲利的函數。

⚠️ 另一個實測到的陷阱：**席勒的 PE10 不能和 trailing EPS 成長配著用。**
PE10 的分母是十年平均實質盈餘，trailing EPS 的分母是十二個月名目盈餘，
兩者相加**不等於**股價報酬（實測殘差標準差 29%、最大 222%）。
要用就用 trailing P/E（＝股價 ÷ 十二個月盈餘），那個恆等式才成立（殘差 < 1e-13）。

所以本檔直接量三個東西：獲利成長、本益比變化、股價報酬，三個都是測出來的。

結論
----
**四格的中位數報酬其實都是正的。差別幾乎全在左尾。**

    軟著陸      實質中位 +9.1%   25 分位  +3.3%   ⇒ 壞情況只是少賺
    成長驚嚇    實質中位 +7.2%   25 分位  −5.0%
    黏著        實質中位 +4.6%   25 分位  −5.1%
    停滯性通膨  實質中位 +3.4%   25 分位 **−16.8%**  ⇒ 壞情況是實質 −17%

⚠️ **為什麼連「獲利轉壞」的格子中位數也是正的**：因為**市場比 trailing EPS 早動**。
   等到十二個月移動盈餘真的掉了 11%，股價通常早就跌完又漲回來了。
   ⇒ 這不是「獲利衰退沒關係」，而是「用 trailing EPS 當訊號，你會太晚」。

⚠️ 這是 **S&P 500 大盤**，不是高估值成長股。高估值名字兩邊的尾巴都更肥，
   但本檔**沒有**高估值成長股的長序列，所以不替它編數字。

用法：python3 asset_outcomes.py
"""

import csv
import math
import os

import scenario_model as M

HERE = os.path.dirname(os.path.abspath(__file__))
SHILLER = os.path.abspath(os.path.join(
    HERE, "..", "avi-v5", "data", "ext", "shiller_sp500.csv"))
HORIZON = 12


def load():
    out = {}
    with open(SHILLER) as f:
        for r in csv.DictReader(f):
            try:
                p = float(r["SP500"]); e = float(r["Earnings"])
                c = float(r["Consumer Price Index"])
            except (ValueError, KeyError):
                continue
            if p <= 0 or e <= 0 or c <= 0:
                continue
            y, m, _ = r["Date"].split("-")
            out[int(y) * 12 + int(m) - 1] = (p, e, c)
    return out


def q(vals, p):
    v = sorted(vals)
    i = p * (len(v) - 1)
    lo = int(i)
    return v[lo] if lo + 1 >= len(v) else v[lo] + (v[lo + 1] - v[lo]) * (i - lo)


def cells():
    ri, re = M.RANK_INFL, M.RANK_EPS
    pf = M.p_earnings_fall(M.PAIRS, M.P_EMPLOYMENT_BREAKS)
    ps = M.P_INFLATION_STICKY
    return {
        "黏著":       [i for i in range(len(M.PAIRS)) if ri[i] > 1 - ps and re[i] >= pf],
        "軟著陸":     [i for i in range(len(M.PAIRS)) if ri[i] <= 1 - ps and re[i] >= pf],
        "停滯性通膨": [i for i in range(len(M.PAIRS)) if ri[i] > 1 - ps and re[i] < pf],
        "成長驚嚇":   [i for i in range(len(M.PAIRS)) if ri[i] <= 1 - ps and re[i] < pf],
    }


def main():
    px = load()
    print("=" * 80)
    print("每一格裡，股票實際發生了什麼（S&P 500，12 個月，log 報酬，不含股息）")
    print("=" * 80)

    # 先驗恆等式，證明沒有循環論證
    chk = []
    for i, (p, e, c) in sorted(px.items()):
        if i + HORIZON not in px:
            continue
        p2, e2, _ = px[i + HORIZON]
        chk.append(math.log(p2 / p) * 100
                   - (math.log(e2 / e) * 100 + math.log((p2 / e2) / (p / e)) * 100))
    print(f"\n恆等式檢查：股價報酬 −（獲利成長 ＋ 本益比變化）最大絕對殘差 = "
          f"{max(abs(x) for x in chk):.2e} ⇒ 成立")

    rows = []
    for name, idx in cells().items():
        de, dpe, nom, real, infl = [], [], [], [], []
        for i in idx:
            t = M.PAIRS[i]["i"]
            if t not in px or t + HORIZON not in px:
                continue
            p0, e0, c0 = px[t]
            p1, e1, c1 = px[t + HORIZON]
            de.append(math.log(e1 / e0) * 100)
            dpe.append(math.log((p1 / e1) / (p0 / e0)) * 100)
            n = math.log(p1 / p0) * 100
            pi = math.log(c1 / c0) * 100
            nom.append(n); real.append(n - pi); infl.append(pi)
        rows.append((name, len(nom), de, dpe, nom, real, infl))

    print("\n【拆解】三個數字都是測出來的，相加為恆等式")
    print(f"  {'情境':<12}{'n':>5}{'獲利成長':>10}{'本益比變化':>12}{'股價報酬':>10}")
    for name, n, de, dpe, nom, real, infl in rows:
        print(f"  {name:<12}{n:>5}{q(de,.5):>9.1f}%{q(dpe,.5):>11.1f}%{q(nom,.5):>9.1f}%")
    print("\n  ⚠️ 「獲利轉壞」那兩格的本益比大漲，**大半是機械性的**——")
    print("     分母（trailing EPS）變小，本益比自然變大。不要讀成「市場願意付更多」。")

    print("\n【真正該看的：實質報酬的分布】")
    print(f"  {'情境':<12}{'實質中位':>10}{'25 分位':>10}{'75 分位':>10}{'實質正報酬':>12}")
    for name, n, de, dpe, nom, real, infl in sorted(rows, key=lambda r: -q(r[5], .25)):
        print(f"  {name:<12}{q(real,.5):>9.1f}%{q(real,.25):>9.1f}%{q(real,.75):>9.1f}%"
              f"{sum(1 for x in real if x>0)/len(real):>11.0%}")

    print("\n  ⇒ **四格的中位數都是正的。差別幾乎全在左尾。**")
    print("     軟著陸的壞情況只是少賺（25 分位仍 +3.3%）；")
    print("     停滯性通膨的壞情況是實質 −16.8%。**那才是這張圖真正的內容。**")
    print("\n  ⚠️ 為什麼連獲利轉壞的格子中位數也是正的：**市場比 trailing EPS 早動。**")
    print("     等移動盈餘真的掉了，股價通常已經跌完又漲回來。")
    print("     ⇒ 不是「獲利衰退沒關係」，是「用 trailing EPS 當訊號會太晚」。")

    print("\n" + "=" * 80)
    print("⚠️ 這是大盤，不是高估值成長股。高估值名字兩邊尾巴都更肥，")
    print("   但本檔沒有高估值成長股的長序列，所以不替它編數字。")
    print("⚠️ 不含股息；1957 年前的 EPS 為席勒的內插值。")
    print("=" * 80)


if __name__ == "__main__":
    main()
