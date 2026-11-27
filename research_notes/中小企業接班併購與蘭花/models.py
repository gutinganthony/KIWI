# R8 models. Every input not tagged with a source is an ASSUMPTION.
# Units: NT$ 萬 (10k) unless noted.

def irr(cfs):
    lo, hi = -0.99, 3.0
    f = lambda r: sum(c / (1 + r) ** t for t, c in enumerate(cfs))
    if f(lo) * f(hi) > 0:
        return float('nan')
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return mid

print("=" * 70)
print("A. 單一收購（營收 2 億、EBITDA 率 12%）")
# 翰林: 營收 4 億、獲利率 7-8%、2.72 億 ≈ 8x 淨利 / 0.6x 營收 (已確認)
# Stanford: 6.2x EBITDA median (US 2024-25)
REV0 = 20000
EBITDA_M0 = 0.12
PRICE_MULT = 6.0
DEBT_SHARE, SELLER_SHARE = 0.40, 0.15   # 台灣無 SBA；銀行 40% 是假設
DEBT_RATE, SELLER_RATE = 0.035, 0.03
FEES = 0.04                               # 仲介 3-5% + 盡調 (崇格 3-5% 已確認*)
YEARS = 6
TAX = 0.20

def deal(growth, uplift_pp, exit_mult, shock=0.0, ai_cost_once=500, label="", rev0=None, m0=None, fixed=0, quiet=False):
    rev0 = rev0 or REV0; m0 = m0 or EBITDA_M0
    ev = rev0 * m0 * PRICE_MULT
    debt = ev * DEBT_SHARE
    seller = ev * SELLER_SHARE
    equity = ev * (1 - DEBT_SHARE - SELLER_SHARE) + ev * FEES + ai_cost_once
    cfs = [-equity]
    d, s = debt, seller
    rev = rev0
    for y in range(1, YEARS + 1):
        rev *= (1 + growth)
        m = m0 + (uplift_pp / 100 if y >= 2 else 0)
        e = rev * m * (1 - shock) - fixed
        interest = d * DEBT_RATE + s * SELLER_RATE
        capex = rev * 0.02
        fcf = (e - interest) * (1 - TAX) - capex
        pay_d = min(d, debt / 7)
        pay_s = min(s, seller / 4)
        d -= pay_d; s -= pay_s
        dist = fcf - pay_d - pay_s
        cfs.append(dist)
    exit_ev = e * exit_mult
    cfs[-1] += exit_ev - d - s - exit_ev * 0.02
    moic = sum(c for c in cfs[1:]) / equity
    if not quiet:
        print(f"  {label:<26} 股權投入 {equity:>6.0f}萬  末年EBITDA {e:>5.0f}萬  "
              f"MOIC {moic:4.2f}x  IRR {irr(cfs)*100:5.1f}%")
    return moic

eq = deal(0.03, 0.0, 6.0, label="基準：無 AI、倍數不變")
deal(0.03, 0.9, 6.0, label="AI +0.9pp、倍數不變")
deal(0.03, 3.9, 6.0, label="AI +3.9pp（樂觀）")
deal(0.03, 0.9, 8.0, label="AI +0.9pp、出場 8x")
deal(0.00, 0.0, 5.0, shock=0.30, label="客戶隨老闆走 -30%、5x")
deal(-0.03, 0.0, 4.0, shock=0.50, label="嚴重失敗 -50%、4x")
print("  → 單家：AI 升級對 IRR 的貢獻遠小於「出場倍數」與「客戶是否留下」。")

# probability-weighted (search-fund-like distribution, Taiwan haircut)
print("\n  機率加權 MOIC（假設：順利 50%、持平無成長 25%、-30% 衝擊 15%、嚴重失敗 10%；失敗時 MOIC 下限 0）")
for up, xm, lab in ((0.0, 6.0, "無 AI"), (0.9, 6.0, "AI +0.9pp"), (0.9, 8.0, "AI +0.9pp、出場 8x")):
    outs = [(0.50, deal(0.03, up, xm, quiet=True)), (0.25, deal(0.0, up, xm-0.5, quiet=True)),
            (0.15, deal(0.0, 0, 5.0, shock=0.3, quiet=True)), (0.10, max(0, deal(-0.03, 0, 4.0, shock=0.5, quiet=True)))]
    print(f"  {lab:<18} 期望 MOIC {sum(p*m for p,m in outs):4.2f}x（6 年）")

print("=" * 70)
print("B. 平台：4 家合計營收 6 億、EBITDA 11%，扣控股公司與共用技術團隊 1,000 萬/年")
deal(0.03, 0.0, 6.0, rev0=60000, m0=0.11, fixed=1000, ai_cost_once=1500, label="無升級、6x")
deal(0.03, 0.9, 6.0, rev0=60000, m0=0.11, fixed=1000, ai_cost_once=1500, label="AI +0.9pp、6x")
deal(0.03, 1.6, 6.0, rev0=60000, m0=0.11, fixed=1000, ai_cost_once=1500, label="AI +1.6pp（共用團隊）、6x")
deal(0.03, 1.6, 9.0, rev0=60000, m0=0.11, fixed=1000, ai_cost_once=1500, label="AI +1.6pp、9x（賣給 PE）")
deal(0.06, 3.0, 10.0, rev0=60000, m0=0.11, fixed=1000, ai_cost_once=1500, label="樂觀 +3pp、成長 6%、10x")
print("  → 平台要靠『合併後更大、可賣給 PE 或上市』的倍數擴張；台灣這條出場路沒有先例。")

print("=" * 70)
print("C. 接班顧問／併購仲介（成交收 3–5%，崇格模式）")
for deals, size, rate, lab in ((2, 15000, 0.05, "起步：年 2 件"),
                                (4, 15000, 0.05, "成長：年 4 件"),
                                (8, 20000, 0.04, "成熟：年 8 件"),
                                (15, 20000, 0.04, "規模：年 15 件")):
    success = deals * max(size * rate, 300)   # 最低收費 300 萬 (假設；日本多有最低報酬)
    retainers = deals * 2 * 40                # 每成交 1 件另有 2 件只收估值/前期費 40 萬 (假設)
    rev = success + retainers
    advisors = max(2, deals / 1.5)            # 每位顧問年成交 1.5 件 (假設)
    cost = advisors * 250 + 2 * 120 + 300 + rev * (0.25 + 0.08)  # 介紹費 25%、行銷 8% (假設)
    op = rev - cost
    print(f"  {lab:<14} 營收 {rev:>5.0f}萬  成本 {cost:>5.0f}萬  營業利益 {op:>6.0f}萬 ({op/rev*100:5.1f}%)")
print("  對照：日本 M&A Center 營益率 37.9%、Strike 31.2%、M&A 総研 28.8%（已確認*）")

print("=" * 70)
print("D1. 蘭花授權撮合＋權利金代收（池子 $90 萬–$760 萬/年，已確認*推算）")
FX = 32
for pool_usd, capture, take, lab in ((90, 0.3, 0.15, "低池、拿 30%"),
                                     (300, 0.3, 0.15, "中池、拿 30%"),
                                     (760, 0.5, 0.20, "高池、拿 50%")):
    rev = pool_usd * capture * take * FX / 1   # 萬 USD→萬 NT
    rev = pool_usd * 1e4 * capture * take * FX / 1e4
    cost = 2 * 150 + 200   # 2 人 + 海外稽核差旅 (假設)
    print(f"  {lab:<14} 營收 {rev:>5.0f}萬  成本 {cost}萬  營業利益 {rev-cost:>6.0f}萬")

print("D2. 侵權取證包（中國；鉅寶紫水晶判賠 RMB 12 萬 ≈ NT$54 萬）")
for cases, fee in ((5, 20), (15, 25), (30, 30)):
    rev = cases * fee
    cost = 150 + cases * 8
    print(f"  年 {cases:>2} 件 × {fee} 萬：營收 {rev}萬  成本 {cost}萬  利益 {rev-cost}萬")

print("=" * 70)
print("D3. 中型蘭場（大苗一株 50 元、賺 10 元＝營益率約 20%，業者口述 已確認*；20% 關稅各吸收一半時『幾乎無毛利』）")
P, PROFIT, PLANTS = 50, 10, 200   # 年 200 萬株 → 營收 1 億
for t, us, extra, lab in ((0.0, 0.75, 0, "無關稅"), (0.15, 0.75, 0, "對美 15%、吸收一半"),
                          (0.20, 1.00, 0, "對美 20%、全銷美（校準點）"),
                          (0.15, 0.75, 2.0, "15% + AI 分級/病毒篩檢省 2 元/株"),
                          (0.15, 0.75, 4.0, "15% + 降損耗 + 新市場溢價共 4 元/株")):
    per = PROFIT - (t / 0.20) * PROFIT * us + extra   # 校準：20% 吸收一半＝吃光 10 元
    print(f"  {lab:<36} 每株 {per:5.2f} 元  營業利益 {per*PLANTS:>5.0f}萬 ({per/P*100:4.1f}%)")
print("  註：『一株 50 元』與『大苗 3.5 美元（約 112 元）』兩個口徑不一致，可能是不同苗齡或出廠價 vs 到岸價。")
print("D4. 美國近市場催花場（每株，美元；全部假設，零售 Costco $11.97 已確認*）")
for whsl, finish, shrink, lab in ((6.0, 2.0, 0.08, "批發 $6、催花 $2"),
                                  (7.0, 1.8, 0.05, "批發 $7、催花 $1.8"),
                                  (5.5, 2.3, 0.12, "批發 $5.5、催花 $2.3")):
    cost = 3.5 * 1.15 + 0.35 + finish     # 大苗 3.5 + 15% 關稅 + 海運/通關 0.35
    margin = whsl * (1 - shrink) - cost
    print(f"  {lab:<22} 每株毛利 ${margin:5.2f}  ({margin/whsl*100:5.1f}%)  "
          f"500 萬株 → ${margin*500:,.0f} 萬")
