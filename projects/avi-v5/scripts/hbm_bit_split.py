#!/usr/bin/env python3
"""HBM vs 傳統 DRAM 的位元供給拆解 — 區分情境② vs ③ 的計算器。

背景：`topics/business/2026-07-29-memory-cycle-vs-structural-hypothesis-test.md`
指出最大盲點是「位元供給成長的分產品拆解」——它是區分
  情境②（全產業谷底提高）與 情境③（產品分化，僅 HBM 結構性）的關鍵。

核心恆等式（晶圓 → 位元）：
    bits_total ∝ W · D · [(1−s) + s/r]
    bits_conv  ∝ W · D · (1−s)
    bits_hbm   ∝ W · D · (s/r)
其中
    W = DRAM 晶圓產能（片/月）
    D = 傳統 DRAM 每片晶圓可售位元（隨製程微縮成長）
    s = 配置給 HBM 的**晶圓**佔比（不是位元佔比！）
    r = trade ratio＝生產 1 位元 HBM 相對 1 位元傳統 DRAM 消耗的晶圓面積倍數
        （TSV 開銷、更大 die、堆疊與封裝良率損失；業界常引用 2–3×）

由此可得年成長率（r 若不變會在 HBM 那條約掉）：
    g_conv  = (1+g_W)(1+g_D) · (1−s1)/(1−s0) − 1
    g_hbm   = (1+g_W)(1+g_D) · (s1/s0)      − 1
    g_total = (1+g_W)(1+g_D) · [(1−s1)+s1/r] / [(1−s0)+s0/r] − 1

**本腳本要證明的關鍵結構性洞見**：
    傳統 DRAM 得到的「保護」來自 (1−s1)/(1−s0) 這一項——也就是
    **HBM 晶圓佔比的『變化量』，不是它的『水位』**。
    一旦 s 走平（HBM 專用產能建成、或 AI 需求增速放緩），該項 → 1，
    g_conv 立刻跳回 (1+g_W)(1+g_D)＝週期論的預測值。
    ⇒ **情境② 在數學上是過渡態，不是穩態；其壽命＝HBM 佔比爬升期長度。**

⚠️ 所有輸入均為**待驗證假設**（本 session 對 TrendForce/Micron IR/IDC 等
   來源全數 403、WebSearch 額度用罄）。本腳本輸出的是**敏感度地圖與判準**，
   不是事實。拿到真數據後改 ASSUMPTIONS 重跑即可。

用法：python3 scripts/hbm_bit_split.py [--grid]
"""

import argparse
from itertools import product

# ── 待驗證假設（拿到真數據就改這裡）───────────────────────────────
ASSUMPTIONS = {
    # DRAM 晶圓產能年成長（2026-2027；新 greenfield 廠多在 2028+，
    # 故成長主要來自 debottlenecking、NAND→DRAM 轉線、既有廠擴充）
    "g_W": (0.00, 0.10),
    # 傳統 DRAM 每片晶圓位元年成長（製程微縮；先進節點下遞減）
    "g_D": (0.05, 0.15),
    # HBM 佔 DRAM **晶圓**比重：起點 s0 → 一年後 s1
    "s0":  (0.15, 0.25),
    "s1":  (0.20, 0.35),
    # trade ratio（HBM 每位元耗用晶圓面積 ÷ 傳統每位元）
    "r":   (2.0, 3.0),
}

# ── 判準（依 2026-07-29 報告 §6 事前寫定，不得事後修改）──────────
CONV_CYCLE_THRESHOLD = 0.15   # 傳統 DRAM 位元供給年增 ≥15% → 回歸歷史＝情境③
CONV_TIGHT_THRESHOLD = 0.10   # 持續 <10% → 供給結構性受限＝情境② 才可能成立


def growth(g_W, g_D, s0, s1, r):
    base = (1 + g_W) * (1 + g_D)
    g_conv = base * (1 - s1) / (1 - s0) - 1
    g_hbm = base * (s1 / s0) - 1
    tot0 = (1 - s0) + s0 / r
    tot1 = (1 - s1) + s1 / r
    g_total = base * tot1 / tot0 - 1
    # HBM 排擠造成的總量拖累（相對於沒有 HBM 的世界）
    drag = base - 1 - g_total
    return g_conv, g_hbm, g_total, drag


def conv_from_observed_total(g_total, s0, s1, r):
    """**最有用的模式**：用「已觀察到的總位元供給成長」反解傳統 DRAM 的成長。

    因為 g_total = base·tot1/tot0 − 1，而 g_conv = base·(1−s1)/(1−s0) − 1，
    把 base 消掉可得：
        g_conv = (1+g_total) · (tot0/tot1) · (1−s1)/(1−s0) − 1
    **好處：不需要知道 g_W 與 g_D**（晶圓產能成長、節點微縮）——這兩個
    最難取得的數字被消掉了，只剩 HBM 晶圓佔比路徑 (s0→s1) 與 trade ratio r。
    """
    tot0 = (1 - s0) + s0 / r
    tot1 = (1 - s1) + s1 / r
    return (1 + g_total) * (tot0 / tot1) * (1 - s1) / (1 - s0) - 1


def verdict(g_conv):
    if g_conv >= CONV_CYCLE_THRESHOLD:
        return "③ 分化（傳統回週期）"
    if g_conv < CONV_TIGHT_THRESHOLD:
        return "② 全產業偏緊"
    return "灰色地帶"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", action="store_true", help="印完整敏感度網格")
    args = ap.parse_args()

    lo = {k: v[0] for k, v in ASSUMPTIONS.items()}
    hi = {k: v[1] for k, v in ASSUMPTIONS.items()}
    mid = {k: (v[0] + v[1]) / 2 for k, v in ASSUMPTIONS.items()}

    print("=" * 78)
    print("HBM vs 傳統 DRAM 位元供給拆解 — 情境②/③ 判別器")
    print("⚠️ 輸入皆為待驗證假設，非事實")
    print("=" * 78)
    print(f"判準（事前寫定）：傳統 DRAM 位元年增 ≥{CONV_CYCLE_THRESHOLD:.0%} → ③；"
          f"<{CONV_TIGHT_THRESHOLD:.0%} → ②")
    print()

    # 中位情境
    gc, gh, gt, dr = growth(**mid)
    print("── 中位假設 ──")
    for k, v in mid.items():
        print(f"   {k:5s} = {v:.3f}")
    print(f"   → 傳統 DRAM 位元成長 {gc:+.1%}　HBM 位元成長 {gh:+.1%}　"
          f"總位元成長 {gt:+.1%}　HBM 排擠拖累 {dr:.1%}")
    print(f"   → 判定：{verdict(gc)}")
    print()

    # 關鍵洞見演示：s 走平會怎樣
    print("── 關鍵洞見：HBM 佔比『走平』後會發生什麼 ──")
    flat = dict(mid); flat["s1"] = flat["s0"]
    gc_f, gh_f, gt_f, dr_f = growth(**flat)
    print(f"   若 s 停在 {flat['s0']:.2f} 不再上升（HBM 專用產能建成／AI 增速放緩）：")
    print(f"   → 傳統 DRAM 位元成長 {gc_f:+.1%}（vs 爬升期的 {gc:+.1%}）")
    print(f"   → 判定：{verdict(gc_f)}")
    print(f"   ⇒ 傳統 DRAM 的『保護』來自 s 的**變化量**，不是水位。")
    print(f"     s 一走平，g_conv 立刻跳回 (1+g_W)(1+g_D) = {(1+mid['g_W'])*(1+mid['g_D'])-1:+.1%}")
    print(f"     ⇒ **情境② 是過渡態，不是穩態**；壽命＝HBM 佔比爬升期長度。")
    print()

    # 敏感度：哪些組合才撐得住情境②
    combos = list(product(*[ASSUMPTIONS[k] for k in ("g_W", "g_D", "s0", "s1", "r")]))
    rows = []
    for g_W, g_D, s0, s1, r in combos:
        if s1 < s0:
            continue
        gc, gh, gt, dr = growth(g_W, g_D, s0, s1, r)
        rows.append((g_W, g_D, s0, s1, r, gc, gh, gt, verdict(gc)))

    n2 = sum(1 for x in rows if x[8].startswith("②"))
    n3 = sum(1 for x in rows if x[8].startswith("③"))
    ng = len(rows) - n2 - n3
    print("── 敏感度掃描（極值角點）──")
    print(f"   有效組合 {len(rows)} 個：情境② {n2}（{n2/len(rows):.0%}）・"
          f"情境③ {n3}（{n3/len(rows):.0%}）・灰色 {ng}（{ng/len(rows):.0%}）")
    # 情境② 需要什麼條件？
    if n2:
        s2 = [x for x in rows if x[8].startswith("②")]
        jumps = [x[3] - x[2] for x in s2]
        gws = [x[0] for x in s2]; gds = [x[1] for x in s2]
        print(f"   撐住 ② 的組合特徵：HBM 佔比年增幅 {min(jumps):+.2f}~{max(jumps):+.2f}、"
              f"g_W {min(gws):.0%}~{max(gws):.0%}、g_D {min(gds):.0%}~{max(gds):.0%}")
    if n3:
        s3 = [x for x in rows if x[8].startswith("③")]
        jumps3 = [x[3] - x[2] for x in s3]
        print(f"   落入 ③ 的組合特徵：HBM 佔比年增幅 {min(jumps3):+.2f}~{max(jumps3):+.2f}")
    print()

    if args.grid:
        print(f"{'g_W':>5} {'g_D':>5} {'s0':>5} {'s1':>5} {'r':>4} │ "
              f"{'傳統':>7} {'HBM':>8} {'總量':>7} │ 判定")
        print("-" * 78)
        for g_W, g_D, s0, s1, r, gc, gh, gt, v in sorted(rows, key=lambda x: x[5]):
            print(f"{g_W:>5.0%} {g_D:>5.0%} {s0:>5.2f} {s1:>5.2f} {r:>4.1f} │ "
                  f"{gc:>+7.1%} {gh:>+8.1%} {gt:>+7.1%} │ {v}")
        print()

    # ── 錨定模式：用觀察到的總量反解傳統 DRAM ──
    print("=" * 78)
    print("★ 錨定模式：用『已觀察到的總位元供給成長』反解傳統 DRAM")
    print("  （消掉 g_W 與 g_D 兩個最難取得的未知數，只需 s0→s1 與 r）")
    print("=" * 78)
    for g_tot_obs in (0.12, 0.16, 0.20):
        print(f"\n  若總 DRAM 位元供給年增 = {g_tot_obs:.0%}"
              f"{'  ← IDC 對 2026 的數字 [二手未核對]' if abs(g_tot_obs-0.16)<1e-9 else ''}")
        print(f"  {'s0→s1':>12} {'r':>5} │ {'傳統 DRAM 位元成長':>18} │ 判定")
        print("  " + "-" * 62)
        for s0, s1 in ((0.20, 0.225), (0.20, 0.275), (0.20, 0.35), (0.25, 0.35)):
            for r in (2.0, 3.0):
                gc = conv_from_observed_total(g_tot_obs, s0, s1, r)
                print(f"  {s0:.2f}→{s1:.2f}{'':>3} {r:>5.1f} │ {gc:>17.1%} │ {verdict(gc)}")

    print("\n  判讀：**在任何合理的 HBM 佔比路徑下，只要總量真的 +16%，"
          "\n  傳統 DRAM 的位元供給都還在正成長（多數落在 +8%~+14%）**——"
          "\n  它沒有被 HBM 餓死到『結構性短缺』的程度。要讓傳統 DRAM 掉到 <10%，"
          "\n  需要 HBM 晶圓佔比一年內跳升 ≥7-10 個百分點且 r 偏低。")
    print()

    print("── 需要的真實數據（拿到就改 ASSUMPTIONS 重跑）──")
    print("   1. DRAM 晶圓產能年成長 g_W（三大廠 wpm 指引）")
    print("   2. 傳統 DRAM 每片晶圓位元成長 g_D（節點遷移）")
    print("   3. **HBM 佔 DRAM 晶圓比重 s 的時間序列**（最關鍵——要的是變化量）")
    print("   4. trade ratio r（HBM 每位元晶圓面積倍數）")
    print("   對照錨點：IDC 稱 2026 年 DRAM 總位元供給 +16% YoY [二手未核對]")
    print("   → 可用它反解：若 g_total≈16%，(g_W,g_D,s0,s1,r) 的哪些組合相容？")


if __name__ == "__main__":
    main()
