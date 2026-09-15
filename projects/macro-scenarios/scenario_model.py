#!/usr/bin/env python3
"""
四情境機率模型 — 把「主觀猜測」換成「可檢查的輸入 + 明確的規則」
=================================================================

背景
----
2026-09-15 的摸魚記文章與 `topics/business/2026-09-13-macro-first-principles-asset-forecast.md`
給了四個情境的機率（A32 / B38 / C12 / D18）。**那是主觀估計，不是算出來的。**
Jake 要求量化成公式，本檔就是那個公式。

設計原則（為什麼這樣做才是誠實的量化）
----------------------------------------
把主觀性**往前推到輸入端**，而不是假裝消掉它。

- ❌ 壞做法：直接對「情境 A」猜一個機率 → 沒有人能檢查你猜得對不對，也沒辦法更新。
- ✅ 本檔做法：只對**三個可觀察、可查證的變數**給機率，情境由**明文規則**推導出來。
  ⇒ 每個輸入都綁一個可以去查的讀數；讀數變了，改一個數字重跑，四個情境自動更新。

**模型不會讓判斷變客觀，它讓判斷變得可以被指認和推翻。** 這才是重點。

三個驅動變數（為什麼是這三個）
-------------------------------
情境的差異，歸根究柢是三件事的組合：

1. **油價 (oil)** — 這次通膨衝擊的外生起點。它決定 Fed 是被迫追、還是可以收手。
2. **核心通膨動能 (core)** — 用「最近三個月年化」，不是年增率（年增率含早就過去的漲幅）。
   這是「最後一哩走不走得完」的直接讀數。
3. **成長／就業 (growth)** — 決定升息的代價，以及 Fed 會不會在就業轉弱時仍硬撐。

⚠️ **三者不獨立**：油價漲會同時推高核心通膨、壓低成長。本模型用**條件機率**處理，
不用「相乘」那種假設獨立的錯誤做法。

用法
----
    python3 scenario_model.py              # 跑基準情境
    python3 scenario_model.py --sensitivity # 加跑敏感度分析

要更新判斷：只改 §1 的 PRIORS 與 CONDITIONALS，不要動規則。
若要改規則（§2），代表你認為情境的定義變了，請在 git commit 訊息說明理由。
"""

import argparse
from itertools import product

# =============================================================================
# §1  輸入：三個變數的機率（← 只有這一段需要隨資料更新）
# =============================================================================
# 每個輸入都附「怎麼查」與「什麼讀數會讓你改這個數字」。

OIL_STATES = ["down", "sticky", "up"]
# down   = Brent 跌破 $90 並維持兩週以上
# sticky = Brent 大致在 $95–110
# up     = Brent 站上 $115
#
# 更新依據：Brent 現貨（2026-09-11 約 $104.6）、荷莫茲談判進展、OPEC 閒置產能。
# 給 down 35% 的理由：戰爭溢價的歷史半衰期短，9/11 已傳出阿曼談判、油價當日 −2.8%。
# 給 up 15% 的理由：荷莫茲從未真正關閉，真關閉是尾部事件。
PRIOR_OIL = {"down": 0.35, "sticky": 0.50, "up": 0.15}

# 核心通膨動能：用「核心 PCE / 核心 CPI 的最近三個月年化」
# cool = 維持 ≤2.5%   hot = 升破 2.5%
#
# 當下讀數：核心 CPI 6–8 月三月年化 2.02%、核心 PCE 5–7 月三月年化 2.43%（皆自行計算）。
#
# 🔴 2026-09-15 大幅上修（原為 down .15 / sticky .35 / up .75）
# 原本給 cool 偏高的理由是「住房落後效應還有下行空間」。**查證後那個理由是錯的、方向還反了**：
#   - 新簽約租金已在回升：ZORI 年增 2026-02 +1.9% → 06 +2.2% → 07 +2.3% → **08 +2.5%**（一年多來最快）
#   - 全國多戶空置率 2021 年底以來**首度下降**；公寓租金四年來首次轉正
#   - 多戶開工 2Q23→2Q24 **−37.1%**，未來供給更少
#   - CPI 住房項落後新租客租金約 3–4 季（Cleveland Fed WP 22-38）
#   ⇒ **住房項在 2026H2–2027 是核心通膨的上行風險，不是下行助力。**
# 這條落後管道正在反向運作，而且它獨立於油價 —— 所以三個油價狀態的 hot 機率一起上調。
P_CORE_HOT_GIVEN_OIL = {"down": 0.35, "sticky": 0.55, "up": 0.85}

# 成長／就業：strong / normal / breaks
# strong = 非農三月均 >150K 或 GDPNow 續 >3%
# normal = 非農三月均 50–150K
# breaks = 非農三月均 <50K 或 失業率 ≥4.3%
#
# 更新依據：非農三月均約 71K（偏 normal 下緣）、失業率 4.1%、ISM 製造 54.6／服務 55.4、
# GDPNow Q3 4.6%。⇒ 硬資料與軟資料分歧，所以 normal 給最高。
P_GROWTH_GIVEN_OIL = {
    "down":   {"strong": 0.30, "normal": 0.55, "breaks": 0.15},
    "sticky": {"strong": 0.18, "normal": 0.57, "breaks": 0.25},
    "up":     {"strong": 0.05, "normal": 0.50, "breaks": 0.45},
}

# =============================================================================
# §2  規則：(油價, 核心動能, 成長) → 情境
# =============================================================================
# 這一段是「情境的定義」，不是判斷。改它等於改了情境的意思。

SCENARIOS = {
    "A": "升一次就停，油價回落",
    "B": "連續升息，油價黏著",
    "C": "油價再升或需求被打壞（停滯性通膨）",
    "D": "經濟夠強，撐得住高利率",
    "E": "成長驚嚇：通膨降了，但經濟也垮了",  # ← 建模時才發現原本四格漏掉這一格
}


def classify(oil: str, core: str, growth: str, strict_c: bool = False,
             merge_e_into_a: bool = False) -> str:
    """
    把一組狀態對應到一個情境。規則是明文的，可以逐條吵。

    strict_c
        False（預設，忠實實作原報告的定義）：油價 >$115 **本身**就算 C。
        True ：油價 >$115 還要**加上**（核心轉熱 或 成長斷掉）才算 C。
        兩者差很多，見輸出的對照——這是原報告 C 定義是否過鬆的檢定。

    merge_e_into_a
        原報告只有四格。「成長垮了但通膨也降了」在四格裡無處可放，
        原本被歸進 A（因為 Fed 一樣會收手）。但**就資產結果而言那是錯的**：
        A 說高估值成長股最有利，成長驚嚇卻會先打它。設 True 可重現原本的四格結果。
    """

    # 油價衝上 $115：headline 逼著 Fed 追，同時打壞需求
    if oil == "up":
        if not strict_c or core == "hot" or growth == "breaks":
            return "C"
        # strict 模式下，油價高但核心溫和且成長撐住 ⇒ 仍是「續升」不是停滯性通膨
        return "B"

    # 成長斷掉，而通膨還沒解決 → 最難的組合（Fed 想停也不敢停）
    if growth == "breaks" and core == "hot":
        return "C"

    # 成長斷掉但通膨已經降溫 → Fed 會收手，但這**不是** A
    if growth == "breaks" and core == "cool":
        return "A" if merge_e_into_a else "E"

    # 核心動能升破 2.5% → 最後一哩沒走完，Fed 得繼續
    if core == "hot":
        return "B"

    # 以下都是 core == "cool" 且 growth in (strong, normal)
    if growth == "strong":
        # 通膨溫和 + 成長強 = r* 上移型，利率與獲利可以同漲
        return "D"

    # growth == "normal"，此時由油價決定 Fed 收不收手
    return "A" if oil == "down" else "B"


# =============================================================================
# §3  計算
# =============================================================================

def compute(prior_oil=None, p_core_hot=None, p_growth=None,
            strict_c=False, merge_e_into_a=False):
    prior_oil = prior_oil or PRIOR_OIL
    p_core_hot = p_core_hot or P_CORE_HOT_GIVEN_OIL
    p_growth = p_growth or P_GROWTH_GIVEN_OIL

    probs = {k: 0.0 for k in SCENARIOS}
    rows = []

    for oil, core, growth in product(OIL_STATES, ["cool", "hot"], ["strong", "normal", "breaks"]):
        p_oil = prior_oil[oil]
        p_c = p_core_hot[oil] if core == "hot" else 1 - p_core_hot[oil]
        p_g = p_growth[oil][growth]
        joint = p_oil * p_c * p_g
        if joint == 0:
            continue
        sc = classify(oil, core, growth, strict_c, merge_e_into_a)
        probs[sc] += joint
        rows.append((oil, core, growth, joint, sc))

    total = sum(probs.values())
    assert abs(total - 1.0) < 1e-9, f"機率沒加總到 1，實際 {total}"
    return probs, rows


def fmt(probs, keys="ABCDE"):
    return " / ".join(f"{k} {probs[k]*100:.0f}%" for k in keys if probs.get(k, 0) > 0.0005)


# =============================================================================
# §4  敏感度：哪一個輸入最重要？
# =============================================================================

def _dist_given(oil=None, core=None, growth=None):
    """條件分布：若已知某個變數的狀態，情境機率會變成什麼。回傳 (分布, 該狀態的機率)。"""
    probs = {k: 0.0 for k in SCENARIOS}
    tot = 0.0
    for o, c, g in product(OIL_STATES, ["cool", "hot"], ["strong", "normal", "breaks"]):
        if oil and o != oil:
            continue
        if core and c != core:
            continue
        if growth and g != growth:
            continue
        p = PRIOR_OIL[o]
        p *= P_CORE_HOT_GIVEN_OIL[o] if c == "hot" else 1 - P_CORE_HOT_GIVEN_OIL[o]
        p *= P_GROWTH_GIVEN_OIL[o][g]
        probs[classify(o, c, g)] += p
        tot += p
    return {k: v / tot for k, v in probs.items()}, tot


def _tvd(p, q):
    """總變異距離：兩個機率分布差多少（0=一樣，1=完全不同）。"""
    return sum(abs(p[k] - q[k]) for k in SCENARIOS) / 2


VARIABLES = [
    ("油價", OIL_STATES, "oil"),
    ("核心通膨", ["cool", "hot"], "core"),
    ("就業", ["strong", "normal", "breaks"], "growth"),
]


def information_value():
    """
    🔴 這一段是 2026-09-15 補的，用來修正一個方法論錯誤。

    原本的 sensitivity() 把**油價推到機率 1.0**，卻只把**核心通膨移動 0.25**，
    然後得出「油價主導一切」。**那是不公平的比較** —— 標準不同，結論當然偏向油價。

    正確問法不是「把輸入推到極端會怎樣」，而是：
        **「如果我能查清楚其中一個變數，平均而言我的判斷會移動多少？」**
    這就是資訊價值（EVPI 的簡化版）：
        資訊價值(V) = Σ_s  P(V=s) × TVD( P(情境 | V=s), P(情境) )
    用每個狀態自己的機率加權 —— 一個很少發生但很極端的狀態，不該拿滿分。
    """
    base, _ = compute()

    print("\n【公平測試 1】三個變數都推到「完全確定」，看擺幅一樣大嗎")
    for label, states, kw in VARIABLES:
        print(f"\n  {label}")
        for s in states:
            d, w = _dist_given(**{kw: s})
            line = " ".join(f"{k}{d[k]*100:4.0f}%" for k in SCENARIOS)
            print(f"    確定是 {s:<7}（機率 {w*100:4.1f}%）→ {line}   偏離基準 {_tvd(d, base)*100:4.1f}")

    print("\n【公平測試 2】資訊價值 —— 該先去查哪一個？")
    print("  （用各狀態自己的機率加權，避免「罕見但極端」被高估）\n")
    ranked = []
    for label, states, kw in VARIABLES:
        v = sum(_dist_given(**{kw: s})[1] * _tvd(_dist_given(**{kw: s})[0], base)
                for s in states)
        ranked.append((v, label))
    for v, l in sorted(ranked, reverse=True):
        print(f"    {l:<6} {v*100:5.1f}  " + "█" * int(v * 120))

    top = sorted(ranked, reverse=True)[0][1]
    print(f"\n  ⇒ 最值得先查的是：**{top}**")
    print("  ⚠️ 但三者差距不大（最大與最小相差不到 8），而這個排序**部分來自模型結構**：")
    print("     核心通膨與就業都是「條件於油價」的，油價因此有額外的間接影響力；")
    print("     而分類規則寫法也會改變誰比較重要。**不要把它當成經濟學結論。**")


def sensitivity():
    base, _ = compute()
    print("\n【敏感度分析】把單一輸入推到極端，看情境怎麼動")
    print("  ⚠️ 這一段的比較**標準不一致**（油價推到 1.0，核心只移 0.25），")
    print("     曾因此得出「油價主導一切」的錯誤結論。公平版見 --info。\n")
    print(f"  基準： {fmt(base)}\n")

    cases = [
        ("油價確定回落（down=1.0）",
         {"down": 1.0, "sticky": 0.0, "up": 0.0}, None, None),
        ("油價確定黏著（sticky=1.0）",
         {"down": 0.0, "sticky": 1.0, "up": 0.0}, None, None),
        ("油價衝上 $115（up=1.0）",
         {"down": 0.0, "sticky": 0.0, "up": 1.0}, None, None),
        ("核心動能全面轉熱（各狀態 +0.25）", None,
         {k: min(1.0, v + 0.25) for k, v in P_CORE_HOT_GIVEN_OIL.items()}, None),
        ("核心動能全面轉冷（各狀態 −0.15）", None,
         {k: max(0.0, v - 0.15) for k, v in P_CORE_HOT_GIVEN_OIL.items()}, None),
        ("就業明顯轉弱（breaks +0.20，由 normal 挪）", None, None,
         {o: {"strong": d["strong"],
              "normal": max(0.0, d["normal"] - 0.20),
              "breaks": d["breaks"] + 0.20}
          for o, d in P_GROWTH_GIVEN_OIL.items()}),
    ]

    for name, oil, core, growth in cases:
        p, _ = compute(oil, core, growth)
        delta = " ".join(f"{k}{(p[k]-base[k])*100:+.0f}" for k in "ABCD")
        print(f"  {name}")
        print(f"      → {fmt(p)}     （變動 {delta}）")

    print("\n  讀法：變動最大的那個輸入，就是最該花力氣去查證的那個讀數。")


def main():
    ap = argparse.ArgumentParser(description="四情境機率模型")
    ap.add_argument("--sensitivity", action="store_true", help="加跑敏感度分析（⚠️ 標準不一致，見 --info）")
    ap.add_argument("--info", action="store_true", help="加跑資訊價值分析（公平比較，推薦用這個）")
    ap.add_argument("--detail", action="store_true", help="列出全部組合")
    args = ap.parse_args()

    probs, rows = compute()

    print("=" * 66)
    print("情境機率模型  —  由三個可觀察變數推導")
    print("=" * 66)
    print("\n【輸入】")
    print(f"  油價        ：{PRIOR_OIL}")
    print(f"  核心轉熱機率：{P_CORE_HOT_GIVEN_OIL}   （條件於油價）")
    print(f"  成長分布    ：條件於油價，見原始碼 §1")

    print("\n【輸出：五情境（建模時發現原本四格漏了一格）】")
    for k in "ABCDE":
        bar = "█" * round(probs[k] * 50)
        print(f"  {k}  {probs[k]*100:5.1f}%  {bar}  {SCENARIOS[k]}")

    # 建模抓到的兩個問題
    four, _ = compute(merge_e_into_a=True)
    strict, _ = compute(strict_c=True)
    subjective = {"A": .32, "B": .38, "C": .12, "D": .18, "E": 0.0}

    print("\n" + "-" * 66)
    print("【建模抓到的問題 1：原本四格漏了「成長驚嚇」】")
    print(f"  「通膨降了但經濟也垮了」佔 {probs['E']*100:.1f}% 的機率質量。")
    print("  原本把它歸進 A（因為 Fed 一樣會停手），但**就資產結果而言那是錯的**：")
    print("  A 說高估值成長股最有利，成長驚嚇卻會先打它、而長債會贏。")
    print(f"  若硬併回四格：{fmt(four, 'ABCD')}")

    print("\n【建模抓到的問題 2：C 的定義可能過鬆】")
    print("  原報告寫「Brent >$115 **任一項**即觸發 C」，模型忠實照做。")
    print("  但油價高、核心卻溫和、成長也撐住時，那其實是「續升」不是停滯性通膨。")
    print(f"  寬鬆定義（現行）：{fmt(probs)}")
    print(f"  嚴格定義（需再加一個條件）：{fmt(strict)}")
    print(f"  ⇒ C 從 {probs['C']*100:.0f}% 降到 {strict['C']*100:.0f}%。這是定義問題，不是資料問題。")

    print("\n【與 2026-09-14 那組主觀估計比較】")
    print("  情境   模型(5格)  主觀    差")
    for k in "ABCDE":
        print(f"   {k}     {probs[k]*100:5.1f}%   {subjective[k]*100:5.1f}%  "
              f"{(probs[k]-subjective[k])*100:+5.1f}pp")
    gap = max(abs(probs[k] - subjective[k]) for k in "ABCD") * 100
    print(f"\n  A–D 最大差距 {gap:.1f}pp。", end=" ")
    if gap <= 5:
        print("接近 ⇒ 原估計內部一致，但它仍然只是判斷。")
    else:
        print("差距明顯 ⇒ 主要來自 C 的定義與遺漏的 E。")

    if args.detail:
        print("\n【全部組合】")
        for oil, core, growth, joint, sc in sorted(rows, key=lambda r: -r[3]):
            print(f"  油{oil:<7} 核心{core:<5} 成長{growth:<7} "
                  f"→ {sc}  {joint*100:5.2f}%")

    if args.sensitivity:
        sensitivity()

    if args.info:
        information_value()

    print("\n" + "=" * 66)
    print("⚠️  這個模型不會讓判斷變客觀。它做的是把主觀性推到三個")
    print("    可以去查的讀數上，讓別人能指出你哪一個輸入錯了。")
    print("    模型沒有處理的：時間（六到十二個月內何時發生）、")
    print("    政策失誤、地緣尾部、以及真實世界不會剛好落在四格裡。")
    print("=" * 66)


if __name__ == "__main__":
    main()
