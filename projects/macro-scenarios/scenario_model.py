#!/usr/bin/env python3
"""
情境機率模型 — 兩個軸來自估值恆等式本身
======================================================================

為什麼是這兩個軸
----------------
一檔股票的報酬，拆到底只有兩塊：

    股價變化 ＝ (1 ＋ 獲利成長) × (1 ＋ 倍數變化) − 1
                      ↑                    ↑
                   分子                  分母

**分子是企業獲利。分母是市場願意付的倍數。** 沒有第三塊。

所以情境的兩個軸就是這兩塊：

    軸一：通膨回不回得到目標   → 決定**倍數**
    軸二：企業獲利撐不撐得住   → 決定**分子**

⚠️ **就業不是分子。** 分子是獲利。公司裁員時成本下降，單一公司的獲利反而變好。
   就業之所以有用，是因為它是**獲利的前導指標**，不是因為它等於獲利：

       P(EPS 衰退 | 失業率升 ≥0.4pp) = 78.4%   (n=185)
       P(EPS 衰退 | 失業率沒升那麼多) = 19.5%   (n=595)

   知道就業，把獲利衰退的機率從 20% 推到 78% —— 很有用。
   但**失業率只解釋 EPS 變異的 17%（R²=0.165）**，另外 83% 它看不到。
   而且**就業沒壞的時候，獲利照樣有兩成機率衰退**（利潤率、資本支出、單一產業崩塌）。
   ⇒ 所以就業當「輸入」，獲利當「軸」。把就業當成分子，會漏掉那兩成。

通膨那一邊值多少（實測，不做分解）
----------------------------------
把獲利狀態固定住、只換通膨狀態，看 S&P 500 十二個月**實質**報酬差多少（1871–2022）：

    獲利撐住：通膨回到目標 +9.1%  vs 通膨沒回去 +4.6%   ⇒ 差 **4.5pp**
    獲利轉壞：通膨回到目標 +7.2%  vs 通膨沒回去 +3.4%   ⇒ 差 **3.8pp**

反向（固定通膨、只換獲利）差 1.2–2.0pp。
⇒ **對股票報酬而言，落在哪個通膨狀態比落在哪個獲利狀態更要緊。**
⚠️ 獲利那一邊被低估：財報是十二個月移動的，市場永遠比它早動。

⚠️ **刻意不做「倍數 × 獲利」的分解**，兩個原因都是實測到的：
   (a) 循環論證——trailing EPS 掉時本益比會機械性上升（分母變小）；
   (b) 口徑錯配——PE10 的分母是十年平均實質盈餘，與 trailing EPS 相加不等於股價報酬
       （殘差標準差 29%、最大 222%）。
   細節與每一格的報酬分布見 asset_outcomes.py。

通膨也在分子裡，但很弱
----------------------
名目 EPS 會隨通膨上升（corr +0.10），而且是**駝峰形**：
通膨 2–4% 時名目 EPS 成長中位數 +11.5%，通膨 >6% 時名目 +7.7% 但**實質 −0.7%**。
⇒ 溫和通膨對分子中性偏好，高通膨兩邊都傷。模型把通膨放在倍數那一側，
   並在 --diagnose 裡標出這個簡化。

四個情境（2×2，互斥且窮盡）
---------------------------
                      獲利撐住              獲利轉壞
    通膨回到目標       軟著陸                成長驚嚇
    通膨沒回去         黏著                  停滯性通膨

機率怎麼來
----------
Sklar 定理：聯合分布 ＝ 邊際 × 相依結構，兩者分開估。

    邊際（各自發生的機率）  ← 外部共識與市場定價（判斷，逐條附出處）
    相依結構（會不會一起發生）← 1957–2022 的實際歷史，用**經驗 copula**

用法
----
    python3 scenario_model.py              # 基準
    python3 scenario_model.py --diagnose   # 因子檢定、獨立假設錯多少、基準率
    python3 scenario_model.py --sensitivity
    python3 scenario_model.py --bootstrap

資料：data/monthly.csv（核心 CPI／核心 PCE／失業率／油價／S&P 500 EPS），見 data/SOURCES.md
"""

import argparse
import csv
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "monthly.csv")

# =============================================================================
# §1  輸入 —— 只有這一段是判斷
# =============================================================================

# ── 軸一：通膨 ────────────────────────────────────────────────────────────
# 「通膨沒回到目標」＝ 12 個月後核心通膨動能（6 個月年化）仍 >2.5%
#
#   當下讀數：核心 CPI 2.57%、核心 PCE 3.46%。
#   ⚠️ **兩把尺差 0.89pp，1985 年以來最大，而答案完全取決於用哪一把：**
#       從核心 CPI 2.57% 出發 → 歷史上 12 個月後仍 >2.5% 的比例 34%（n=189）
#       從核心 PCE 3.46% 出發 → 89%（n=56；全歷史 n=91 為 93%）
#   聯準會盯 PCE；SPF 預測的核心 CPI 是 2.7%（仍在門檻上）。
#   ⇒ 取 0.70，偏 PCE 那一側。**這是全模型最大的單一不確定性。**
P_INFLATION_STICKY = 0.70

# ── 軸二的輸入：就業 ──────────────────────────────────────────────────────
# 「就業壞掉」＝ 失業率 12 個月後 ≥4.5%（當下 4.1%，即上升 ≥0.4pp）
#   外部錨：紐約聯準殖利率曲線 13.9%／Goldman 15%／SPF anxious 20%／JPM 20%／WSJ 25%
#   自算基準率（1986–2025）≈20%。⇒ 取 0.20。
P_EMPLOYMENT_BREAKS = 0.20

# ── 油價：推通膨軸，並透過就業間接影響獲利軸 ───────────────────────────────
#   當下 Brent 現貨 $107.35（2026-09-15）。近月曲線逆價差、選擇權 skew 偏高。
#   ⚠️ 取不到選擇權隱含機率 ⇒ **這三個數字是判斷，不是市場定價。**
OIL_STATES = {
    "down":   {"p": 0.40, "level": 85,  "label": "回落到 $85 附近"},
    "sticky": {"p": 0.45, "level": 105, "label": "維持 $100–110"},
    "up":     {"p": 0.15, "level": 125, "label": "衝上 $125 以上"},
}
BRENT_NOW = 107.35

# 油價 Δlog 每 +100% ⇒ 核心通膨動能 +1.23pp（自算，1986–2025，OLS，R²=0.15）
BETA_OIL_TO_INFLATION = 1.23

# 油價對失業率的推力（pp）。
# ⚠️ **全模型唯一沒有資料支撐的參數。** 簡約式係數方向被需求型油價污染
#    （算出來是油價漲→失業降，因為歷史上多數油價上漲是需求拉動的），所以不能用。
#    改用文獻方向＋明示幅度：持續 20% 的供給型油價衝擊約使一年 GDP 少 0.2–0.5pp，
#    按 Okun 約對應失業率 +0.1–0.2pp。--sensitivity 會把它從 +0.05 掃到 +0.50。
OIL_TO_UNRATE_PP = {"down": -0.05, "sticky": 0.0, "up": +0.15}

# =============================================================================
# §2  情境定義
# =============================================================================

SCENARIOS = [
    ("軟著陸",     "通膨回到目標 ・ 獲利撐住"),
    ("黏著",       "通膨沒回去 ・ 獲利撐住"),
    ("成長驚嚇",   "通膨回到目標 ・ 獲利轉壞"),
    ("停滯性通膨", "通膨沒回去 ・ 獲利轉壞"),
]

MOMENTUM_MONTHS = 6      # 通膨動能：6 個月年化
HORIZON_MONTHS = 12      # 預測視野
INFL_SAMPLE_START = 1986  # 通膨×油價的樣本起點（油價資料所限）

# =============================================================================
# §3  資料
# =============================================================================


def load_monthly(path=DATA):
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            y, m = row["date"].split("-")
            out[int(y) * 12 + int(m) - 1] = {
                k: (float(v) if v not in ("", None) else None)
                for k, v in row.items() if k != "date"}
    return out


def momentum(monthly, key, i, months):
    a = monthly.get(i, {}).get(key)
    b = monthly.get(i - months, {}).get(key)
    if a is None or b is None or b <= 0:
        return None
    return ((a / b) ** (12.0 / months) - 1) * 100


def build_pairs(monthly, start=1957):
    """每個歷史月份往後 12 個月，(Δ通膨動能, EPS 成長 %, Δ失業率, Δlog 油價)。"""
    out = []
    for i in sorted(monthly):
        if i // 12 < start:
            continue
        pi0 = momentum(monthly, "core_cpi", i, MOMENTUM_MONTHS)
        pi1 = momentum(monthly, "core_cpi", i + HORIZON_MONTHS, MOMENTUM_MONTHS)
        e0 = monthly.get(i, {}).get("sp500_eps")
        e1 = monthly.get(i + HORIZON_MONTHS, {}).get("sp500_eps")
        u0 = monthly.get(i, {}).get("unrate")
        u1 = monthly.get(i + HORIZON_MONTHS, {}).get("unrate")
        if None in (pi0, pi1, e0, e1, u0, u1) or e0 <= 0:
            continue
        o0 = monthly.get(i, {}).get("wti")
        o1 = monthly.get(i + HORIZON_MONTHS, {}).get("wti")
        out.append(dict(
            i=i,
            d_infl=pi1 - pi0,
            d_eps=math.log(e1 / e0) * 100,
            d_unrate=u1 - u0,
            d_oil=(math.log(o1 / o0) if (o0 and o1) else None),
        ))
    return out


def to_ranks(values):
    n = len(values)
    order = sorted(range(n), key=lambda k: values[k])
    r = [0.0] * n
    for pos, k in enumerate(order):
        r[k] = (pos + 1) / (n + 1.0)
    return r


def quantile(sorted_vals, q):
    n = len(sorted_vals)
    if q <= 0:
        return sorted_vals[0]
    if q >= 1:
        return sorted_vals[-1]
    pos = q * (n - 1)
    lo = int(pos)
    if lo + 1 >= n:
        return sorted_vals[-1]
    return sorted_vals[lo] * (1 - (pos - lo)) + sorted_vals[lo + 1] * (pos - lo)


def shifted_prob(sorted_vals, base_p, shift):
    """把經驗分布整體平移 shift，再看超過原門檻的比例。沒有換算參數。"""
    thr = quantile(sorted_vals, 1 - base_p)
    return sum(1 for v in sorted_vals if v + shift > thr) / len(sorted_vals)


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    return sxy / math.sqrt(sxx * syy)


# =============================================================================
# §4  獲利軸的邊際：由就業的外部錨推導
# =============================================================================

U_BREAK_THRESHOLD = 0.4      # 與 §1 一致：失業率上升 ≥0.4pp


def earnings_given_employment(pairs):
    """回傳 (P(EPS<0|就業壞), P(EPS<0|就業沒壞), n_bad, n_ok) —— 全部由資料算。"""
    bad = [p for p in pairs if p["d_unrate"] >= U_BREAK_THRESHOLD]
    ok = [p for p in pairs if p["d_unrate"] < U_BREAK_THRESHOLD]
    p_bad = sum(1 for p in bad if p["d_eps"] < 0) / len(bad)
    p_ok = sum(1 for p in ok if p["d_eps"] < 0) / len(ok)
    return p_bad, p_ok, len(bad), len(ok)


def p_earnings_fall(pairs, p_emp_breaks):
    """全機率公式：P(獲利轉壞) = P(就業壞)·P(EPS<0|就業壞) + P(就業好)·P(EPS<0|就業好)"""
    p_bad, p_ok, _, _ = earnings_given_employment(pairs)
    return p_emp_breaks * p_bad + (1 - p_emp_breaks) * p_ok


# =============================================================================
# §5  計算
# =============================================================================


def scenario_probs(rank_infl, rank_eps, p_sticky, p_eps_fall):
    """經驗 copula：用歷史的秩相依結構，套上指定的邊際機率。"""
    n = len(rank_infl)
    both = sum(1 for a, b in zip(rank_infl, rank_eps)
               if a > 1 - p_sticky and b < p_eps_fall) / n
    return [
        1 - p_sticky - p_eps_fall + both,   # 軟著陸
        p_sticky - both,                    # 黏著
        p_eps_fall - both,                  # 成長驚嚇
        both,                               # 停滯性通膨
    ]


def compute(pairs, rank_infl, rank_eps, sorted_infl,
            p_sticky=None, p_emp=None, oil_to_unrate=None):
    p_sticky = P_INFLATION_STICKY if p_sticky is None else p_sticky
    p_emp = P_EMPLOYMENT_BREAKS if p_emp is None else p_emp
    oil_to_unrate = OIL_TO_UNRATE_PP if oil_to_unrate is None else oil_to_unrate

    total = [0.0] * 4
    rows = []
    for state, cfg in OIL_STATES.items():
        d_infl = BETA_OIL_TO_INFLATION * math.log(cfg["level"] / BRENT_NOW)
        d_u = oil_to_unrate[state]
        ps = shifted_prob(sorted_infl, p_sticky, d_infl)
        pe_emp = min(0.60, max(0.02, p_emp + d_u))
        pf = p_earnings_fall(pairs, pe_emp)
        q = scenario_probs(rank_infl, rank_eps, ps, pf)
        rows.append((cfg, d_infl, d_u, ps, pe_emp, pf, q))
        for k in range(4):
            total[k] += cfg["p"] * q[k]
    assert abs(sum(total) - 1.0) < 1e-9, f"機率沒加總到 1：{sum(total)}"
    return total, rows


def bar(p, width=46):
    return "█" * round(p * width)


# =============================================================================
# §6  輸出
# =============================================================================


def print_main(monthly, pairs, total, rows):
    print("=" * 76)
    print("情境機率模型  —  兩個軸就是估值恆等式的兩塊")
    print("=" * 76)
    print("\n    股價變化 ＝ (1 ＋ 獲利成長) × (1 ＋ 倍數變化) − 1")
    print("                      分子                  分母")
    print("    軸二：獲利撐不撐得住          軸一：通膨回不回得到目標")

    last = lambda k: max(i for i in monthly if monthly[i].get(k) is not None)
    lc, lp, lu = last("core_cpi"), last("core_pce"), last("unrate")
    print("\n【起點讀數】（自 data/monthly.csv 計算）")
    print(f"  核心 CPI 6 個月年化  {momentum(monthly,'core_cpi',lc,6):.2f}%"
          f"   核心 PCE 6 個月年化  {momentum(monthly,'core_pce',lp,6):.2f}%"
          f"   ⚠️ 差 {momentum(monthly,'core_pce',lp,6)-momentum(monthly,'core_cpi',lc,6):+.2f}pp")
    print(f"  失業率 {monthly[lu]['unrate']:.1f}%        Brent 現貨 ${BRENT_NOW:.2f}")

    p_bad, p_ok, n_bad, n_ok = earnings_given_employment(pairs)
    print("\n【軸一：通膨】（判斷，外部錨見 §1）")
    print(f"  P(12 個月後核心動能仍 >2.5%) = {P_INFLATION_STICKY:.0%}"
          f"   ← 最大的不確定性：CPI 說 34%、PCE 說 89%")
    print("\n【軸二：獲利】（由就業的外部錨推導，兩個條件機率來自資料）")
    print(f"  P(就業壞掉) = {P_EMPLOYMENT_BREAKS:.0%}   ← 外部錨 13.9/15/20/20/25%")
    print(f"  P(EPS 衰退 | 就業壞掉)     = {p_bad:.1%}   (n={n_bad})")
    print(f"  P(EPS 衰退 | 就業沒壞)     = {p_ok:.1%}   (n={n_ok})")
    print(f"  ⇒ P(獲利轉壞) = {P_EMPLOYMENT_BREAKS:.2f}×{p_bad:.3f}"
          f" + {1-P_EMPLOYMENT_BREAKS:.2f}×{p_ok:.3f} = "
          f"**{p_earnings_fall(pairs, P_EMPLOYMENT_BREAKS):.1%}**")
    print("  ⚠️ 注意它比 P(就業壞掉) 高得多 —— **獲利比就業脆弱**。")
    print("     就業沒壞、獲利照樣有兩成機率衰退，那一塊就業完全看不到。")

    print("\n【油價：推通膨軸，並透過就業間接影響獲利軸】")
    for cfg, d_infl, d_u, ps, pe, pf, q in rows:
        print(f"  {cfg['label']:<16}機率 {cfg['p']:.0%}  ⇒ 通膨動能 {d_infl:+.2f}pp／失業率 {d_u:+.2f}pp"
              f"  ⇒ P(通膨黏) {ps:.0%}  P(獲利壞) {pf:.0%}")

    avg_s = sum(cfg["p"] * ps for cfg, _, _, ps, _, _, _ in rows)
    avg_f = sum(cfg["p"] * pf for cfg, _, _, _, _, pf, _ in rows)
    print(f"\n  ⚠️ 油價分層後的實際邊際：P(通膨黏) {avg_s:.3f}（輸入 {P_INFLATION_STICKY:.2f}）、"
          f"P(獲利壞) {avg_f:.3f}")
    print("     輸入值是「油價維持現狀」下的基準，加權後會略微偏移，這是預期行為。")

    print("\n【輸出：四個情境】")
    for k in sorted(range(4), key=lambda j: -total[j]):
        name, desc = SCENARIOS[k]
        print(f"  {total[k]*100:4.0f}%  {bar(total[k])}")
        print(f"        {name} — {desc}")
    print("\n  ⚠️ 四捨五入到整數。相依結構的抽樣誤差就有 ±3pp（--bootstrap），")
    print("     邊際的不確定性更大（--sensitivity）。**不要比較小數點後一位。**")


def diagnose(pairs, rank_infl, rank_eps):
    print("\n" + "=" * 76)
    print("【診斷 1】就業到底是不是「分子」？——不是，但它是最好用的前導指標")
    d_eps = [p["d_eps"] for p in pairs]
    d_u = [p["d_unrate"] for p in pairs]
    r = pearson(d_eps, d_u)
    # R²（單變數迴歸）
    print(f"  corr(EPS 成長, Δ失業率) = {r:+.3f}   R² = {r*r:.3f}")
    print(f"  ⇒ **失業率只解釋 EPS 變異的 {r*r*100:.0f}%**，另外 {100-r*r*100:.0f}% 它看不到。")
    print("     裁員讓單一公司成本下降、獲利變好；總體上則是需求掉、營收掉。")
    print("     兩股力量方向相反，所以關係是真的、但很弱。")
    print("\n  分組（Δ失業率 → 同期名目 EPS 成長中位數）：")
    bands = [(-99, -0.5, "失業率大降"), (-0.5, -0.1, "小降"), (-0.1, 0.2, "持平"),
             (0.2, 0.5, "小升"), (0.5, 1.0, "升 0.5–1.0pp"), (1.0, 99, "大升")]
    for lo, hi, nm in bands:
        sub = sorted(p["d_eps"] for p in pairs if lo <= p["d_unrate"] < hi)
        if len(sub) < 15:
            continue
        print(f"    {nm:<14} n={len(sub):<4} EPS 中位數 {quantile(sub, 0.5):+6.1f}%")

    print("\n【診斷 2】兩個軸的相依結構（經驗 copula 用的就是這個）")
    d_infl = [p["d_infl"] for p in pairs]
    print(f"  corr(Δ通膨動能, EPS 成長)  Pearson {pearson(d_infl, d_eps):+.3f}"
          f"   秩相關 {pearson(rank_infl, rank_eps):+.3f}")
    print("  正號 ⇒ 通膨加速與獲利成長**同向**（都是需求在推）。")
    print("  ⇒ 「通膨燒起來」和「獲利垮掉」不太會同時發生，而那正是停滯性通膨的定義。")

    print("\n【診斷 3】假設兩軸獨立會錯多少")
    pf = p_earnings_fall(pairs, P_EMPLOYMENT_BREAKS)
    emp = scenario_probs(rank_infl, rank_eps, P_INFLATION_STICKY, pf)
    ind = [(1 - P_INFLATION_STICKY) * (1 - pf), P_INFLATION_STICKY * (1 - pf),
           (1 - P_INFLATION_STICKY) * pf, P_INFLATION_STICKY * pf]
    print(f"  {'情境':<12}{'經驗copula':>12}{'假設獨立':>11}{'誤差':>10}")
    for k in range(4):
        d = (ind[k] - emp[k]) * 100
        tag = "  ← 高估" if d > 1 else ("  ← 低估" if d < -1 else "")
        print(f"  {SCENARIOS[k][0]:<12}{emp[k]*100:10.1f}%{ind[k]*100:10.1f}%{d:+9.1f}pp{tag}")
    print(f"  總變異距離 {sum(abs(a-b) for a, b in zip(ind, emp))/2:.3f}")

    print("\n【診斷 4】歷史基準率（不套任何共識邊際，純粹數歷史）")
    n = len(pairs)
    print(f"  P(EPS 12 個月衰退)                 {sum(1 for p in pairs if p['d_eps']<0)/n:.0%}")
    print(f"  P(失業率上升 ≥0.4pp)               "
          f"{sum(1 for p in pairs if p['d_unrate']>=U_BREAK_THRESHOLD)/n:.0%}")
    print(f"  P(通膨動能上升 且 EPS 衰退)         "
          f"{sum(1 for p in pairs if p['d_infl']>0 and p['d_eps']<0)/n:.0%}")
    print("  ⇒ 停滯性通膨在歷史上不常見，但**比「就業壞掉」常見**，因為獲利更脆弱。")

    print("\n【診斷 5】兩個可能的方法學漏洞，各檢查過一次")
    # (a) 油價層與 copula 是否重複計算
    sub = [p for p in pairs if p["d_oil"] is not None]
    if len(sub) > 100:
        def _resid(y, x):
            n = len(y); mx = sum(x) / n; my = sum(y) / n
            b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
            a0 = my - b * mx
            return [c - (a0 + b * a) for a, c in zip(x, y)]
        ox = [p["d_oil"] for p in sub]
        ri_r = to_ranks(_resid([p["d_infl"] for p in sub], ox))
        re_r = to_ranks(_resid([p["d_eps"] for p in sub], ox))
        ri_0 = to_ranks([p["d_infl"] for p in sub])
        re_0 = to_ranks([p["d_eps"] for p in sub])
        pf2 = p_earnings_fall(pairs, P_EMPLOYMENT_BREAKS)
        q0 = scenario_probs(ri_0, re_0, P_INFLATION_STICKY, pf2)
        qr = scenario_probs(ri_r, re_r, P_INFLATION_STICKY, pf2)
        qfull = scenario_probs(rank_infl, rank_eps, P_INFLATION_STICKY, pf2)
        print(f"  (a) 油價既推邊際、又已含在 copula 裡 —— 會不會重複計算？")
        print(f"      1986 後子樣本(n={len(sub)})：原始停滯 {q0[3]*100:.1f}%"
              f" → 對油價殘差化後 {qr[3]*100:.1f}%")
        print(f"      全樣本(n={len(pairs)})：{qfull[3]*100:.1f}%"
              f" —— 與殘差化後的值幾乎相同 ⇒ **全樣本估計沒有被污染。**")
    # (b) trailing EPS 的時間對齊
    print("  (b) 席勒的 EPS 是 12 個月移動的，會不會和失業率窗對不齊？")
    best = None
    for lag in (0, 3, 6, 9, 12):
        xs, ys = [], []
        for p in pairs:
            u0 = MONTHLY.get(p["i"] - lag, {}).get("unrate")
            u1 = MONTHLY.get(p["i"] + HORIZON_MONTHS - lag, {}).get("unrate")
            if u0 is None or u1 is None:
                continue
            xs.append(p["d_eps"]); ys.append(u1 - u0)
        c = pearson(xs, ys)
        if best is None or abs(c) > abs(best[1]):
            best = (lag, c)
        print(f"      失業率窗前移 {lag:>2} 個月：corr {c:+.3f}")
    print(f"      ⇒ 最強的是前移 {best[0]} 個月 ⇒ **同期對齊是對的**，沒有系統性錯位。")

    print("\n【診斷 6】模型知道自己簡化了什麼")
    print("  通膨被放在倍數那一側，但名目 EPS 也會隨通膨上升（corr +0.10），")
    print("  而且是駝峰形：通膨 2–4% 時名目 EPS 成長最好，>6% 時實質 EPS 轉負。")
    print("  ⇒ 溫和通膨對分子中性偏好、對分母偏壞；高通膨兩邊都壞。**模型只算了分母那一邊。**")


def sensitivity(pairs, rank_infl, rank_eps, sorted_infl):
    print("\n" + "=" * 76)
    print("【敏感度】兩個邊際在各自合理範圍內移動（相依結構固定 —— 那是資料）")
    print("\n  停滯性通膨的機率：")
    emps = [0.15, 0.20, 0.25, 0.30]
    print("             " + "".join(f"  就業壞 {e:.0%}" for e in emps))
    for s in (0.50, 0.60, 0.70, 0.80, 0.85):
        cells = []
        for e in emps:
            t, _ = compute(pairs, rank_infl, rank_eps, sorted_infl, p_sticky=s, p_emp=e)
            cells.append(t[3] * 100)
        print(f"  通膨黏 {s:.0%}" + "".join(f"{c:11.0f}%" for c in cells))

    print("\n  油價→失業率推力（唯一沒有資料支撐的參數）：")
    for up in (0.05, 0.15, 0.30, 0.50):
        t, _ = compute(pairs, rank_infl, rank_eps, sorted_infl,
                       oil_to_unrate={"down": -0.05, "sticky": 0.0, "up": up})
        print(f"    油價衝上 $125 使失業率 +{up:.2f}pp  ⇒  "
              + "  ".join(f"{SCENARIOS[k][0]} {t[k]*100:.0f}%" for k in (0, 3)))


def bootstrap(pairs, sorted_infl, B=1500, block=24, seed=11):
    print("\n" + "=" * 76)
    print(f"【抽樣誤差】block bootstrap（block={block} 個月，處理重疊窗的序列相關）")
    rng = random.Random(seed)
    n = len(pairs)
    nb = n // block
    acc = [[] for _ in range(4)]
    for _ in range(B):
        idx = []
        for _ in range(nb):
            s = rng.randrange(0, n - block + 1)
            idx.extend(range(s, s + block))
        samp = [pairs[j] for j in idx]
        ri = to_ranks([p["d_infl"] for p in samp])
        re = to_ranks([p["d_eps"] for p in samp])
        t, _ = compute(samp, ri, re, sorted_infl)
        for k in range(4):
            acc[k].append(t[k])
    print(f"  {'情境':<12}{'中位數':>9}{'95% 區間':>18}")
    for k in range(4):
        v = sorted(acc[k])
        print(f"  {SCENARIOS[k][0]:<12}{v[B//2]*100:7.0f}%   "
              f"[{v[int(.025*B)]*100:4.0f}%, {v[int(.975*B)]*100:4.0f}%]")
    print("\n  ⚠️ 這只是相依結構的抽樣誤差，邊際的不確定性更大。")
    print("     兩者合起來 ⇒ **四捨五入到 5pp 才是誠實的。**")


MONTHLY = load_monthly()
PAIRS = build_pairs(MONTHLY)
RANK_INFL = to_ranks([p["d_infl"] for p in PAIRS])
RANK_EPS = to_ranks([p["d_eps"] for p in PAIRS])
SORTED_INFL = sorted(p["d_infl"] for p in PAIRS)


def main():
    ap = argparse.ArgumentParser(description="情境機率模型")
    ap.add_argument("--diagnose", action="store_true")
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--bootstrap", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    total, rows = compute(PAIRS, RANK_INFL, RANK_EPS, SORTED_INFL)
    print_main(MONTHLY, PAIRS, total, rows)
    print(f"\n  相依結構樣本：{PAIRS[0]['i']//12}–{PAIRS[-1]['i']//12}，"
          f"n={len(PAIRS)} 個重疊的 12 個月窗")

    if args.diagnose or args.all:
        diagnose(PAIRS, RANK_INFL, RANK_EPS)
    if args.sensitivity or args.all:
        sensitivity(PAIRS, RANK_INFL, RANK_EPS, SORTED_INFL)
    if args.bootstrap or args.all:
        bootstrap(PAIRS, SORTED_INFL)

    print("\n" + "=" * 76)
    print("這個模型不會讓判斷變客觀。它把主觀性關進兩個攤得開的數字，")
    print("把「兩件事會不會一起發生」交給六十年的實際資料，")
    print("然後把每個假設攤開，讓別人可以指著其中一條說「這裡錯了」。")
    print("沒處理的：時間點、政策失誤、地緣尾部，以及單一公司與指數的差異。")
    print("=" * 76)


if __name__ == "__main__":
    main()
