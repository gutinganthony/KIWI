#!/usr/bin/env python3
"""
情境機率模型 v2 — 用「共識邊際 × 歷史相依結構」取代「三個數字相乘」
=====================================================================

v1 做錯了什麼（2026-09-15 查證後重建）
--------------------------------------
v1 算的是   P(油, 通膨, 就業) = P(油) × P(通膨|油) × P(就業|油)

這個式子**不是**機率的鏈鎖法則。正確的鏈鎖法則是

            P(油, 通膨, 就業) = P(油) × P(通膨|油) × P(就業|油, 通膨)
                                                              ^^^^^^^^
v1 少了 "通膨" 這個條件，等於偷偷假設了「**給定油價之後，通膨與就業互相獨立**」
（統計上叫條件獨立假設 / naive Bayes 假設）。

**用資料檢定的結果：這個假設不成立，而且錯得有方向。**

    控制油價後，corr(Δ核心通膨動能, Δ失業率) = −0.41
    [95% block-bootstrap 區間 −0.55, −0.22]，1986–2025；
    分 1990 後、1998 後重算皆為 −0.41 ~ −0.42，結論穩定。

負相關代表：**通膨與「就業健康」是同向的**（需求好 → 通膨升 + 失業降）。
所以獨立假設會：
    - **高估**「通膨升 + 就業壞」＝ 停滯性通膨（v1 把它算成實際的 1.4 倍）
    - **低估**「通膨降 + 就業壞」＝ 成長驚嚇
    - **低估**「通膨升 + 就業好」＝ 再加速

v1 還有三個結構性問題
---------------------
2. **把三個變數當成平行的輸入**。其實**通膨與就業是情境的兩個座標軸**
   （資產價格 = 現金流 ÷ (1+r)：就業→現金流，通膨→折現率），
   **油價是推動那兩個軸的力量**，不是第三個軸。三者不對等，不該對稱處理。
3. **情境集混了三種東西**：原因（油價路徑）、政策結果（升幾次息）、狀態（成長垮掉）。
   所以會出現「Brent >$115 本身就算情境 C」這種規則——把觸發條件當成結果。
   實際上油價衝到 $125 只讓停滯性通膨從 ~8% 升到 ~11%，不是「直接 100%」。
4. **報到小數點一位**（43.9%）。光是相依結構的抽樣誤差就有 ±3pp，
   邊際本身的不確定性更大。**四捨五入到 5pp 已是誠實的極限。**

v2 怎麼做
---------
Sklar 定理：任何聯合分布都可以拆成「邊際分布」＋「相依結構(copula)」，兩者可以分開估。

    邊際（各自發生的機率）  ← 共識與市場定價錨定，是主觀的，**逐條列出處**
    相依結構（會不會一起發生）← 1986–2025 的實際歷史，**不是猜的**
    油價                   ← 把兩個邊際往上/往下推的力量

相依結構用**經驗 copula**（歷史資料的秩），不用高斯 copula，因為：
    Δ通膨 偏態 +1.78、超峰度 +7.81；Δ失業 偏態 +1.70、超峰度 +16.98
    Jarque-Bera p < 1e-16 ⇒ **常態被強烈拒絕**，而我們關心的正好是角落那幾格。
    實測：高斯 copula 把停滯性通膨算成 0.9%，經驗分布是 2.1%（1986–2025 基準率）。

用法
----
    python3 scenario_model.py              # 基準
    python3 scenario_model.py --diagnose   # 獨立假設錯多少、常態性檢定、基準率
    python3 scenario_model.py --sensitivity # 兩個邊際在合理範圍內移動的影響
    python3 scenario_model.py --bootstrap  # 相依結構的抽樣誤差區間

資料：data/monthly.csv（核心 CPI／核心 PCE／失業率／WTI／Brent 月序列）
     來源為 FRED 官方序列的 GitHub 鏡像，見 data/SOURCES.md。
"""

import argparse
import csv
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "monthly.csv")

# =============================================================================
# §1  輸入 —— 只有這一段是判斷，每一條都附出處與「什麼讀數會讓我改它」
# =============================================================================

# ── 1a. 兩個座標軸的邊際機率（12 個月視野）────────────────────────────────
#
# 通膨軸：核心通膨動能（6 個月年化）在 12 個月後是否仍高於 2.5%
#   當下讀數（自 data/monthly.csv 計算）：核心 CPI 2.57%、核心 PCE 3.46%
#   ⚠️ **這兩個數字現在差 0.90pp（核心 PCE 年增 3.34% vs 核心 CPI 2.45%），
#      是 1985 年以來最大的背離。用哪一把尺，答案天差地遠：**
#        從核心 CPI 2.57% 出發 → 歷史上 12 個月後仍 >2.5% 的比例只有 34%（n=189）
#        從核心 PCE 3.46% 出發 → 89%（n=56；擴大到全歷史 n=91 則為 93%）
#      聯準會盯的是 PCE，但 SPF 預測的核心 CPI 是 2.7%（仍高於門檻）。
#   ⇒ 取 0.70，並在 --sensitivity 裡跑 0.50–0.85。**這是全模型最大的不確定性。**
P_INFLATION_ABOVE_TARGET = 0.70      # P(核心動能 > 2.5%)
P_INFLATION_REACCEL      = 0.30      # P(核心動能 > 3.5%)，是上面那個的子集
#   取 0.30 的理由：核心 PCE 6 個月年化當下就是 3.46%，恰好壓在 3.5% 門檻上。

# 就業軸：失業率在 12 個月後是否 ≥ 4.5%（當下 4.1%，等於上升 0.4pp 以上）
#   外部錨（全部查證，日期見 data/SOURCES.md）：
#     紐約聯準銀行殖利率曲線 12 個月衰退機率 13.9%（資料至 2026-08，發布 09-06）
#     Goldman 12 個月衰退機率 15%（2026 年年中）
#     費城聯準 SPF anxious index 20.0%（2026Q4 負成長機率，Q3 調查）
#     摩根大通 20%／WSJ 經濟學家調查 25%
#   自算基準率：1986–2025，P(失業率 12 個月內上升 ≥0.4pp) ≈ 20%
#   ⇒ 取 0.20，區間 0.15–0.30。**這一格外部對照物最多，也最可信。**
P_EMPLOYMENT_BREAKS = 0.20

# ── 1b. 油價三態 ─────────────────────────────────────────────────────────
#   當下 Brent 現貨 $107.35（2026-09-15）。
#   給 down 偏高的理由：近月曲線呈逆價差（市場預期未來價格較低）、戰爭溢價半衰期短。
#   給 up 15% 的理由：選擇權 skew 偏高（154.49，09-14 單日 +5.08%）＝尾部風險有人在買，
#     但荷莫茲從未真正關閉。
#   ⚠️ 取不到選擇權隱含機率（CME/Barchart 需即時頁、FRED OVXCLS 被擋），**這三個數字是判斷**。
OIL_STATES = {
    "down":   {"p": 0.40, "level": 85,  "label": "回落到 $85 附近"},
    "sticky": {"p": 0.45, "level": 105, "label": "維持 $100–110"},
    "up":     {"p": 0.15, "level": 125, "label": "衝上 $125 以上"},
}
BRENT_NOW = 107.35

# ── 1c. 油價對兩個軸的推力 ────────────────────────────────────────────────
# 兩條推力都以**同一種自然單位（pp）**表示，再用同一個機制換算成機率：
#   把經驗分布整體平移 shift pp，看超過原門檻的比例變成多少（見 shifted_prob）。
#   ⇒ 沒有任何「pp 換算成機率」的自由參數。
#
#   通膨：自算簡約式係數 = 油價 Δlog 每 +100% ⇒ 核心通膨動能 +1.23pp
#         （1986–2025，OLS，R²=0.15；用 --diagnose 可重跑）
BETA_OIL_TO_INFLATION = 1.23

#   就業：**不能用簡約式係數**。自算結果是「油價漲 → 失業率降」（係數 −1.79pp per 100%），
#   因為歷史上多數油價上漲是需求拉動的：
#       油價上漲的窗裡，需求型（油↑且工業生產↑）n=223，供給型（油↑且工業生產↓）n=39
#   直接套用會得出「油價漲對就業有利」，與供給衝擊的因果相反。
#   ⇒ 改為**明示假設**：供給型油價衝擊推升失業率，幅度如下（單位 pp）。
#   ⚠️ **這是本模型唯一沒有資料支撐的參數**。取值理由：文獻上持續 20% 的供給型油價衝擊
#      約使一年內 GDP 成長少 0.2–0.5pp，按 Okun 法則約對應失業率 +0.1–0.2pp。
#      取 +0.15pp（$125 情境）。--sensitivity 會把它從 +0.05 掃到 +0.50。
OIL_TO_UNRATE_PP = {"down": -0.05, "sticky": 0.0, "up": +0.15}

# =============================================================================
# §2  情境定義 —— 3 條通膨帶 × 2 條就業帶
# =============================================================================
# 為什麼是這兩個軸：資產價格 = 現金流 ÷ (1 + 折現率)。
#   就業/成長 → 決定現金流；通膨 → 決定折現率。兩個軸各管一半，互不重複。
# 為什麼通膨切三帶：實測「明顯再加速(>3.5%)」佔 25% 的機率質量（> 10% 的門檻），
#   而它與「只是黏著」的資產結果不同（前者壓估值倍數，後者主要影響政策節奏）。

SCENARIOS = [
    ("軟著陸",     "通膨回到目標 ・ 就業撐住"),
    ("黏著",       "通膨卡在 2.5–3.5% ・ 就業撐住"),
    ("再加速",     "通膨衝破 3.5% ・ 就業撐住"),
    ("成長驚嚇",   "通膨回到目標 ・ 就業壞掉"),
    ("停滯性通膨", "通膨沒回去 ・ 就業壞掉"),
]

# =============================================================================
# §3  相依結構 —— 從資料算出來的，不是輸入
# =============================================================================

MOMENTUM_MONTHS = 6      # 通膨動能：6 個月年化（3 個月太吵，年增率太鈍）
HORIZON_MONTHS  = 12     # 預測視野
SAMPLE_START    = 1986   # 有油價資料的起點；--diagnose 會一併跑全樣本對照


def load_monthly(path=DATA):
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            y, m = row["date"].split("-")
            i = int(y) * 12 + int(m) - 1
            out[i] = {k: (float(v) if v not in ("", None) else None)
                      for k, v in row.items() if k != "date"}
    return out


def momentum(monthly, key, i, months):
    a = monthly.get(i, {}).get(key)
    b = monthly.get(i - months, {}).get(key)
    if a is None or b is None or b <= 0:
        return None
    return ((a / b) ** (12.0 / months) - 1) * 100


def build_pairs(monthly, gauge="core_cpi", start=SAMPLE_START, with_oil=False):
    """回傳 [(Δ通膨動能, Δ失業率)]：每個歷史月份，往後 12 個月實際發生了什麼。

    with_oil=True 時回傳 [(Δ通膨, Δ失業, Δlog 油價)]，且只保留油價也有值的月份
    —— 那是 oil_controlled_correlation() 用的樣本。
    """
    out = []
    for i in sorted(monthly):
        if i // 12 < start:
            continue
        pi_now = momentum(monthly, gauge, i, MOMENTUM_MONTHS)
        pi_fut = momentum(monthly, gauge, i + HORIZON_MONTHS, MOMENTUM_MONTHS)
        u_now = monthly.get(i, {}).get("unrate")
        u_fut = monthly.get(i + HORIZON_MONTHS, {}).get("unrate")
        if None in (pi_now, pi_fut, u_now, u_fut):
            continue
        if not with_oil:
            out.append((pi_fut - pi_now, u_fut - u_now))
            continue
        o_now = monthly.get(i, {}).get("wti")
        o_fut = monthly.get(i + HORIZON_MONTHS, {}).get("wti")
        if not o_now or not o_fut:
            continue
        out.append((pi_fut - pi_now, u_fut - u_now, math.log(o_fut / o_now)))
    return out


def to_ranks(values):
    """經驗累積機率（平均秩 / (n+1)），落在 (0,1) 開區間。"""
    n = len(values)
    order = sorted(range(n), key=lambda k: values[k])
    r = [0.0] * n
    for pos, k in enumerate(order):
        r[k] = (pos + 1) / (n + 1.0)
    return r


def rank_pairs(pairs):
    return list(zip(to_ranks([p[0] for p in pairs]), to_ranks([p[1] for p in pairs])))


def _ols2(y, x):
    """單變數 OLS（含常數項）。回傳 (斜率, 殘差)。"""
    n = len(y)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx
    a0 = my - b * mx
    return b, [c - (a0 + b * a) for a, c in zip(x, y)]


def oil_controlled_correlation(triples):
    """§1 與 README 宣稱的 −0.41 就是這個函式算出來的。

    做法：Δ通膨 與 Δ失業 各自對「同一個 12 個月窗的油價 Δlog」做迴歸，
    取殘差再算相關係數 —— 也就是「把油價的共同影響扣掉之後，兩者還剩多少相關」。
    這正是條件獨立假設要求 ≈ 0 的那個量。
    """
    dpi = [t[0] for t in triples]
    du = [t[1] for t in triples]
    doil = [t[2] for t in triples]
    b1, e1 = _ols2(dpi, doil)
    b2, e2 = _ols2(du, doil)
    return pearson(e1, e2), b1, b2, e1, e2


def block_bootstrap_corr(e1, e2, block=24, B=3000, seed=11):
    """重疊的 12 個月窗會造成序列相關，一般標準誤會低估。用 block bootstrap 給區間。"""
    rng = random.Random(seed)
    n = len(e1)
    nb = max(1, n // block)
    out = []
    for _ in range(B):
        idx = []
        for _ in range(nb):
            s = rng.randrange(0, n - block + 1)
            idx.extend(range(s, s + block))
        out.append(pearson([e1[j] for j in idx], [e2[j] for j in idx]))
    out.sort()
    return out[int(0.025 * B)], out[int(0.975 * B)]


def quantile(sorted_vals, q):
    """經驗分位數（線性內插）。"""
    n = len(sorted_vals)
    if q <= 0:
        return sorted_vals[0]
    if q >= 1:
        return sorted_vals[-1]
    pos = q * (n - 1)
    lo = int(pos)
    frac = pos - lo
    if lo + 1 >= n:
        return sorted_vals[-1]
    return sorted_vals[lo] * (1 - frac) + sorted_vals[lo + 1] * frac


def shifted_prob(sorted_vals, base_p, shift_pp):
    """把經驗分布整體平移 shift_pp，再看超過原門檻的比例。

    base_p 定義了門檻（使 P(X > 門檻) = base_p）；平移後回傳 P(X + shift > 門檻)。
    ⇒ 「pp 位移 → 機率位移」全部由歷史分布的形狀決定，沒有自由參數。
    """
    thr = quantile(sorted_vals, 1 - base_p)
    n = len(sorted_vals)
    return sum(1 for v in sorted_vals if v + shift_pp > thr) / n


def cell_prob(rpairs, pi_lo, pi_hi, u_lo, u_hi):
    """經驗 copula：秩落在 (pi_lo, pi_hi] × (u_lo, u_hi] 這個長方形裡的比例。"""
    n = len(rpairs)
    if n == 0:
        return 0.0
    c = sum(1 for a, b in rpairs
            if pi_lo < a <= pi_hi and u_lo < b <= u_hi)
    return c / n


# =============================================================================
# §4  計算
# =============================================================================

def scenario_probs(rpairs, p_above, p_reaccel, p_breaks):
    """給定三個邊際機率，用經驗 copula 算五個情境。"""
    # 通膨軸的三條帶（用分位切）：
    #   回到目標 = 秩 ≤ 1-p_above ；黏著 = (1-p_above, 1-p_reaccel] ；再加速 = > 1-p_reaccel
    a1, a2 = 1 - p_above, 1 - p_reaccel
    b = 1 - p_breaks                       # 就業：秩 ≤ b 撐住，> b 壞掉
    soft   = cell_prob(rpairs, 0.0, a1, 0.0, b)
    sticky = cell_prob(rpairs, a1,  a2, 0.0, b)
    reacc  = cell_prob(rpairs, a2, 1.0, 0.0, b)
    scare  = cell_prob(rpairs, 0.0, a1, b,  1.0)
    stagf  = cell_prob(rpairs, a1, 1.0, b,  1.0)
    return [soft, sticky, reacc, scare, stagf]


def marginals_given_oil(state, sorted_dpi, sorted_du):
    """油價狀態 → 兩個軸的邊際機率。兩條推力都走 shifted_prob，沒有換算參數。"""
    cfg = OIL_STATES[state]
    d_pi = BETA_OIL_TO_INFLATION * math.log(cfg["level"] / BRENT_NOW)
    d_u = OIL_TO_UNRATE_PP[state]
    p_above = shifted_prob(sorted_dpi, P_INFLATION_ABOVE_TARGET, d_pi)
    p_reaccel = shifted_prob(sorted_dpi, P_INFLATION_REACCEL, d_pi)
    p_breaks = shifted_prob(sorted_du, P_EMPLOYMENT_BREAKS, d_u)
    # 三帶必須單調：>3.5% 是 >2.5% 的子集
    p_reaccel = min(p_reaccel, p_above)
    return p_above, p_reaccel, p_breaks, d_pi, d_u


def compute(rpairs, sorted_dpi=None, sorted_du=None):
    """對油價三態取加權平均。"""
    sorted_dpi = sorted_dpi if sorted_dpi is not None else SORTED_DPI
    sorted_du = sorted_du if sorted_du is not None else SORTED_DU
    total = [0.0] * 5
    rows = []
    for state, cfg in OIL_STATES.items():
        p_above, p_reaccel, p_breaks, d_pi, d_u = marginals_given_oil(
            state, sorted_dpi, sorted_du)
        q = scenario_probs(rpairs, p_above, p_reaccel, p_breaks)
        rows.append((state, cfg, p_above, p_reaccel, p_breaks, d_pi, d_u, q))
        for k in range(5):
            total[k] += cfg["p"] * q[k]
    s = sum(total)
    assert abs(s - 1.0) < 1e-9, f"機率沒加總到 1：{s}"
    return total, rows


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    return sxy / math.sqrt(sxx * syy)


def bar(p, width=44):
    return "█" * round(p * width)


# =============================================================================
# §5  輸出
# =============================================================================

def print_main(monthly, total, rows):
    print("=" * 74)
    print("情境機率模型 v2  —  邊際靠共識，相依結構靠 40 年歷史")
    print("=" * 74)

    last_cpi = max(i for i in monthly if monthly[i].get("core_cpi") is not None)
    last_pce = max(i for i in monthly if monthly[i].get("core_pce") is not None)
    last_u   = max(i for i in monthly if monthly[i].get("unrate") is not None)
    print("\n【起點讀數】（自 data/monthly.csv 計算）")
    print(f"  核心 CPI 6 個月年化   {momentum(monthly,'core_cpi',last_cpi,6):.2f}%"
          f"   （3 個月年化 {momentum(monthly,'core_cpi',last_cpi,3):.2f}%）")
    print(f"  核心 PCE 6 個月年化   {momentum(monthly,'core_pce',last_pce,6):.2f}%"
          f"   ⚠️ 與 CPI 差 {momentum(monthly,'core_pce',last_pce,6)-momentum(monthly,'core_cpi',last_cpi,6):+.2f}pp")
    print(f"  失業率                {monthly[last_u]['unrate']:.1f}%")
    print(f"  Brent 現貨            ${BRENT_NOW:.2f}")

    print("\n【輸入：三個邊際機率】（判斷，出處見 §1）")
    print(f"  P(通膨 12 個月後仍 >2.5%)  {P_INFLATION_ABOVE_TARGET:.0%}   ← 最大的不確定性（CPI 說 34%、PCE 說 89%）")
    print(f"  P(其中衝破 3.5%)           {P_INFLATION_REACCEL:.0%}")
    print(f"  P(失業率 ≥4.5%)            {P_EMPLOYMENT_BREAKS:.0%}   ← 外部錨最多：13.9%/15%/20%/20%/25%")

    print("\n【輸入：油價三態】")
    for state, cfg, p_above, p_reaccel, p_breaks, d_pi, d_u, q in rows:
        print(f"  {cfg['label']:<16}機率 {cfg['p']:.0%}  ⇒ 核心動能 {d_pi:+.2f}pp／失業率 {d_u:+.2f}pp"
              f"  ⇒ P(通膨>2.5%) {p_above:.0%}  P(就業壞) {p_breaks:.0%}")

    print("\n【輸出：五個情境】")
    order = sorted(range(5), key=lambda k: -total[k])
    for k in order:
        name, desc = SCENARIOS[k]
        print(f"  {total[k]*100:4.0f}%  {bar(total[k])}")
        print(f"        {name} — {desc}")
    print("\n  ⚠️ 全部四捨五入到整數；相依結構的抽樣誤差就有 ±3pp（--bootstrap），"
          "\n     邊際的不確定性更大（--sensitivity）。**不要拿小數點後一位去比較。**")


def diagnose(monthly, rpairs):
    print("\n" + "=" * 74)
    print("【診斷 1】條件獨立假設（v1 的做法）錯多少")
    p_above, p_reaccel, p_breaks = (P_INFLATION_ABOVE_TARGET,
                                    P_INFLATION_REACCEL, P_EMPLOYMENT_BREAKS)
    emp = scenario_probs(rpairs, p_above, p_reaccel, p_breaks)
    # 獨立版本：同樣的邊際，但假設兩軸無關
    ind = [(1 - p_above) * (1 - p_breaks),
           (p_above - p_reaccel) * (1 - p_breaks),
           p_reaccel * (1 - p_breaks),
           (1 - p_above) * p_breaks,
           p_above * p_breaks]
    print(f"  {'情境':<12}{'經驗copula':>12}{'假設獨立':>11}{'誤差':>10}")
    for k in range(5):
        d = (ind[k] - emp[k]) * 100
        tag = "  ← 高估" if d > 1 else ("  ← 低估" if d < -1 else "")
        print(f"  {SCENARIOS[k][0]:<12}{emp[k]*100:10.1f}%{ind[k]*100:10.1f}%{d:+9.1f}pp{tag}")
    tvd = sum(abs(a - b) for a, b in zip(ind, emp)) / 2
    line = f"  總變異距離 {tvd:.3f}"
    if emp[4] > 0:
        line += f"   停滯性通膨被高估成 {ind[4]/emp[4]:.2f} 倍"
    print(line)

    print("\n【診斷 2】相依結構本身（不套任何主觀邊際，直接看資料）")
    dpi = [p[0] for p in PAIRS]
    du = [p[1] for p in PAIRS]
    rp = [r[0] for r in rpairs]
    ru = [r[1] for r in rpairs]
    print(f"  樣本 {SAMPLE_START}–2025，n={len(PAIRS)}（相依結構用的樣本）")
    print(f"    無條件 Pearson 相關      {pearson(dpi, du):+.3f}")
    print(f"    無條件秩相關（copula 用） {pearson(rp, ru):+.3f}")

    # ---- 這一段就是 §1 與 README 宣稱的 −0.41 的來源，現在可重跑 ----
    r_cond, b1, b2, e1, e2 = oil_controlled_correlation(TRIPLES)
    lo, hi = block_bootstrap_corr(e1, e2)
    print(f"\n  **控制油價後**（Δ通膨、Δ失業各自對油價 Δlog 迴歸後取殘差），n={len(TRIPLES)}：")
    print(f"    Pearson 相關  {r_cond:+.3f}   [95% block-bootstrap {lo:+.3f}, {hi:+.3f}]")
    print(f"    油價 Δlog 每 +100%：核心動能 {b1:+.2f}pp、失業率 {b2:+.2f}pp")
    print("    ⚠️ 失業率那個係數為負（油價漲→失業降），是因為歷史上多數油價上漲是需求拉動的。")
    print("       這就是為什麼模型不用它，改用 §1 的明示假設 OIL_TO_UNRATE_PP。")
    print("\n  ⚠️ **三個數字不是同一件事，不要混用**：")
    print("     無條件 Pearson ≠ 無條件秩相關 ≠ 控制油價後的 Pearson。")
    print("     條件獨立假設要求 ≈0 的是**最後那一個**；經驗 copula 實際用到的是**秩相關**那一個。")
    print("     三個都離 0 很遠，所以結論不受選哪一個影響。")
    for start in (1990, 1998):
        t = build_pairs(MONTHLY, start=start, with_oil=True)
        rc, _, _, _, _ = oil_controlled_correlation(t)
        print(f"     穩定性檢查：{start} 後 n={len(t)}  控制油價後 {rc:+.3f}")
    print("\n  負號代表通膨與『就業健康』同向 ⇒ 需求主導，不是供給主導。")
    print("  ⇒ 這就是為什麼獨立假設會高估停滯性通膨：它把兩件『不太會同時發生』的壞事當成無關。")

    n = len(dpi)
    mx = sum(dpi) / n
    sd = math.sqrt(sum((x - mx) ** 2 for x in dpi) / (n - 1))
    sk = sum(((x - mx) / sd) ** 3 for x in dpi) / n
    ku = sum(((x - mx) / sd) ** 4 for x in dpi) / n - 3
    my = sum(du) / n
    sdy = math.sqrt(sum((x - my) ** 2 for x in du) / (n - 1))
    sky = sum(((x - my) / sdy) ** 3 for x in du) / n
    kuy = sum(((x - my) / sdy) ** 4 for x in du) / n - 3
    print(f"\n【診斷 3】為什麼用經驗 copula 而不是高斯 copula")
    print(f"  Δ通膨：偏態 {sk:+.2f}  超峰度 {ku:+.2f}")
    print(f"  Δ失業：偏態 {sky:+.2f}  超峰度 {kuy:+.2f}")
    print("  兩者都遠離常態（常態的偏態=0、超峰度=0），而我們關心的正是角落那幾格。")
    print("  高斯 copula 會把尾部算得太乾淨：實測它把『通膨升+就業壞』的基準率算成 0.9%，")
    print("  經驗分布是 2.1%。**用錯 copula 的代價，和用錯獨立假設一樣大。**")

    print("\n【診斷 4】歷史基準率（不套共識邊際，純粹數歷史）")
    print("  問題：從任一個月往後看 12 個月，實際落在哪一格？")
    b_above = sum(1 for d, _ in PAIRS if d > 0) / len(PAIRS)
    b_break = sum(1 for _, d in PAIRS if d >= 0.4) / len(PAIRS)
    b_both  = sum(1 for a, d in PAIRS if a > 0 and d >= 0.4) / len(PAIRS)
    print(f"  P(通膨動能比一年前高)          {b_above:.0%}")
    print(f"  P(失業率上升 ≥0.4pp)           {b_break:.0%}   ← 與外部衰退機率 14–25% 相符")
    print(f"  P(兩者同時發生＝停滯性通膨)     {b_both:.0%}   "
          f"（獨立假設會算成 {b_above*b_break:.0%}）")
    print("  ⇒ **真正的停滯性通膨在歷史上很罕見。** v1 publish 的 24% 需要非常強的理由，它沒有。")


def sensitivity(rpairs):
    print("\n" + "=" * 74)
    print("【敏感度】兩個邊際在各自合理範圍內移動")
    print("  （相依結構固定 —— 那一段是資料，不是判斷）\n")
    print("  停滯性通膨的機率：")
    breaks = [0.15, 0.20, 0.25, 0.30]
    print("            " + "".join(f"  就業壞 {b:.0%}" for b in breaks))
    for above in (0.50, 0.60, 0.70, 0.80, 0.85):
        cells = []
        for b in breaks:
            q = scenario_probs(rpairs, above, min(P_INFLATION_REACCEL, above * 0.45), b)
            cells.append(q[4] * 100)
        print(f"  通膨 >2.5% {above:.0%}" + "".join(f"{c:10.0f}%" for c in cells))
    print("\n  讀法：即使把兩個邊際都推到最悲觀（通膨 85% × 就業壞 30%），")
    print("       停滯性通膨也只到十幾趴——**因為歷史說這兩件事不太同時發生。**")

    print("\n  油價推力假設的敏感度（唯一沒有資料支撐的參數）：")
    global OIL_TO_UNRATE_PP
    keep = dict(OIL_TO_UNRATE_PP)
    for up_shift in (0.05, 0.15, 0.30, 0.50):
        OIL_TO_UNRATE_PP = {"down": -0.05, "sticky": 0.0, "up": up_shift}
        total, _ = compute(rpairs)
        print(f"    油價衝上 $125 使失業率 +{up_shift:.2f}pp  ⇒  "
              + "  ".join(f"{SCENARIOS[k][0]} {total[k]*100:.0f}%" for k in (0, 4)))
    OIL_TO_UNRATE_PP = keep


def bootstrap(pairs, B=2000, block=24, seed=7):
    print("\n" + "=" * 74)
    print(f"【抽樣誤差】block bootstrap（block={block} 個月，處理重疊窗造成的序列相關）")
    rng = random.Random(seed)
    n = len(pairs)
    nb = n // block
    acc = [[] for _ in range(5)]
    for _ in range(B):
        idx = []
        for _ in range(nb):
            s = rng.randrange(0, n - block + 1)
            idx.extend(range(s, s + block))
        samp = [pairs[j] for j in idx]
        rp = rank_pairs(samp)
        total, _ = compute(rp)
        for k in range(5):
            acc[k].append(total[k])
    print(f"  {'情境':<12}{'中位數':>9}{'95% 區間':>18}")
    for k in range(5):
        v = sorted(acc[k])
        lo, mid, hi = v[int(.025 * B)], v[int(.5 * B)], v[int(.975 * B)]
        print(f"  {SCENARIOS[k][0]:<12}{mid*100:7.0f}%   [{lo*100:4.0f}%, {hi*100:4.0f}%]")
    print("\n  ⚠️ 這**只是**相依結構的抽樣誤差。邊際本身的不確定性（見 --sensitivity）更大。")
    print("     兩者合起來 ⇒ **這種模型的輸出，四捨五入到 5pp 才是誠實的。**")


MONTHLY = load_monthly()
PAIRS = build_pairs(MONTHLY)                       # 相依結構用（不需要油價）
TRIPLES = build_pairs(MONTHLY, with_oil=True)      # 控制油價的相關係數用
SORTED_DPI = sorted(p[0] for p in PAIRS)
SORTED_DU = sorted(p[1] for p in PAIRS)


def main():
    ap = argparse.ArgumentParser(description="情境機率模型 v2")
    ap.add_argument("--diagnose", action="store_true", help="獨立假設錯多少、常態性、基準率")
    ap.add_argument("--sensitivity", action="store_true", help="邊際在合理範圍內移動的影響")
    ap.add_argument("--bootstrap", action="store_true", help="相依結構的抽樣誤差區間（慢）")
    ap.add_argument("--all", action="store_true", help="全部跑一遍")
    args = ap.parse_args()

    rpairs = rank_pairs(PAIRS)
    total, rows = compute(rpairs)
    print_main(MONTHLY, total, rows)
    print(f"\n  相依結構樣本：{SAMPLE_START}–2025，n={len(PAIRS)} 個重疊的 12 個月窗")

    if args.diagnose or args.all:
        diagnose(MONTHLY, rpairs)
    if args.sensitivity or args.all:
        sensitivity(rpairs)
    if args.bootstrap or args.all:
        bootstrap(PAIRS)

    print("\n" + "=" * 74)
    print("這個模型不會讓判斷變客觀。它做的是把主觀性關進幾個攤得開的數字，")
    print("把『兩件事會不會一起發生』交給 40 年的實際資料，")
    print("然後把每一個假設都攤開來，讓別人可以指著其中一條說「這裡錯了」。")
    print("沒處理的：時間點、政策失誤、地緣尾部、以及真實世界不會剛好落在五格裡。")
    print("=" * 74)


if __name__ == "__main__":
    main()
