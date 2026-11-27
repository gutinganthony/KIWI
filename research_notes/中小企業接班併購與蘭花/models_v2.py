# R8 models v2 (after adversarial review). Units: NT$ 萬. Untagged inputs are ASSUMPTIONS.
# Fixes vs v1: no AI cost in no-AI cases; exit tax 20% on gain; bank debt 0-20% base;
# interest not tax-deductible (share deal, see r8-search-fund §4); entry-multiple sensitivity;
# working capital 15% of incremental revenue; broker comp = base + bonus; orchid calibration both price bases.

def irr(cfs):
    f = lambda r: sum(c / (1 + r) ** t for t, c in enumerate(cfs))
    lo, hi = -0.99, 3.0
    if f(lo) * f(hi) > 0:
        return float('nan')
    for _ in range(200):
        mid = (lo + hi) / 2
        (hi := mid) if f(lo) * f(mid) <= 0 else (lo := mid)
    return mid

def deal(rev0=20000, m0=0.12, entry=6.0, exit_m=6.0, growth=0.03, uplift=0.0, shock=0.0,
         debt=0.20, seller=0.15, rate=0.05, years=6, fixed=0, ai_once=None, exit_tax=0.20):
    ai_once = (500 if uplift > 0 else 0) if ai_once is None else ai_once
    ev = rev0 * m0 * entry
    d0, s0 = ev * debt, ev * seller
    equity = ev - d0 - s0 + ev * 0.04 + ai_once
    d, s, rev, cfs = d0, s0, rev0, [-equity]
    for y in range(1, years + 1):
        prev = rev
        rev *= 1 + growth
        e = rev * (m0 + (uplift / 100 if y >= 2 else 0)) * (1 - shock) - fixed
        tax = max(0, e - rev * 0.02) * 0.20          # interest NOT deductible
        fcf = e - tax - d * rate - s * 0.03 - rev * 0.02 - max(0, rev - prev) * 0.15
        pd, ps = min(d, d0 / 7), min(s, s0 / 4)
        d -= pd; s -= ps
        cfs.append(fcf - pd - ps)
    exit_ev = e * exit_m
    proceeds = exit_ev * 0.98 - d - s
    gain = proceeds - equity
    cfs[-1] += proceeds - max(0, gain) * exit_tax
    inflow = sum(c for c in cfs[1:] if c > 0)
    outflow = equity - sum(c for c in cfs[1:] if c < 0)
    return inflow / outflow, irr(cfs), equity

def show(label, **kw):
    m, r, eq = deal(**kw)
    print(f"  {label:<34} 股權 {eq:>6.0f}萬  MOIC {m:4.2f}x  IRR {r*100:6.1f}%")
    return m

print("A. 單一收購（營收 2 億、EBITDA 12%、持有 6 年、出場課 20%）")
show("基準：6x 買、6x 賣、銀行 20%、無 AI")
show("零銀行債", debt=0.0)
show("銀行 40%（樂觀，美國 SBA 式）", debt=0.40, rate=0.035)
show("AI +0.9pp", uplift=0.9)
show("AI +2.3pp", uplift=2.3)
show("AI +3.9pp（樂觀）", uplift=3.9)
show("出場 8x（倍數擴張）", exit_m=8.0)
show("進場 4x（日本年買法級距）", entry=4.0, exit_m=6.0)
show("進場 4x、出場 4x", entry=4.0, exit_m=4.0)
show("進場 8x（翰林級，約淨利 8 倍）", entry=8.0, exit_m=6.0)
show("客戶隨老闆走 -30%、5x", shock=0.30, growth=0.0, exit_m=5.0)
show("嚴重失敗 -50%、4x", shock=0.50, growth=-0.03, exit_m=4.0)

print("\n  機率加權（順利 40%、持平 30%、-30% 衝擊 20%、嚴重失敗 10%——比 v1 保守）")
for lab, kw in (("6x 買、無 AI", {}), ("6x 買、AI +0.9pp", {"uplift": 0.9}),
                ("4x 買、無 AI", {"entry": 4.0}), ("零銀行債、6x 買", {"debt": 0.0})):
    outs = [(0.40, deal(**kw)[0]), (0.30, deal(**{**kw, "growth": 0.0, "exit_m": 5.5})[0]),
            (0.20, deal(**{**kw, "uplift": 0, "shock": 0.3, "growth": 0.0, "exit_m": 5.0})[0]),
            (0.10, deal(**{**kw, "uplift": 0, "shock": 0.5, "growth": -0.03, "exit_m": 4.0})[0])]
    print(f"  {lab:<20} 期望 MOIC {sum(p * m for p, m in outs):4.2f}x")

print("\nB. 平台：4 家合計營收 6 億、EBITDA 11%")
show("無升級、無控股成本、6x", rev0=60000, m0=0.11)
show("無升級、控股成本 500 萬/年、6x", rev0=60000, m0=0.11, fixed=500)
show("AI +1.6pp、控股+技術 1,000 萬、6x", rev0=60000, m0=0.11, uplift=1.6, fixed=1000, ai_once=1500)
show("AI +1.6pp、同上、9x（賣給 PE）", rev0=60000, m0=0.11, uplift=1.6, fixed=1000, ai_once=1500, exit_m=9.0)

print("\nC. 獨立接班顧問精品（成交 3–5%、底薪 150 萬＋營收 20% 獎金、每位顧問年成交 1 件、"
      "介紹費 25%、行銷 8%、保險法務 200 萬、辦公 300 萬）")
for deals, size, lab in ((0, 5000, "第 0 年：無成交"), (2, 5000, "年 2 件、平均 0.5 億"),
                         (4, 5000, "年 4 件、平均 0.5 億"), (4, 10000, "年 4 件、平均 1 億"),
                         (8, 10000, "年 8 件、平均 1 億"), (8, 15000, "年 8 件、平均 1.5 億")):
    fee_each = max(size * 0.05 if size <= 5000 else size * 0.04, 150)
    retain = deals * 2 * 30 + 3 * 30       # 前期費/估值費 (假設)
    rev = deals * fee_each + retain
    advisors = max(2, deals)
    cost = advisors * 150 + rev * (0.20 + 0.25 + 0.08) + 200 + 300
    op = rev - cost
    pct = f"{op / rev * 100:5.1f}%" if rev else "  —"
    print(f"  {lab:<20} 營收 {rev:>5.0f}萬  成本 {cost:>5.0f}萬  營業利益 {op:>6.0f}萬 ({pct})")

print("\nC2. 兩人精品、自有案源（無介紹費、行銷 3%、辦公 150 萬、保險法務 100 萬）")
for deals, size in ((2, 5000), (3, 10000), (4, 10000), (6, 10000)):
    fee_each = max(size * 0.05 if size <= 5000 else size * 0.04, 150)
    rev = deals * fee_each + deals * 2 * 30
    cost = 2 * 150 + rev * (0.20 + 0.03) + 250
    op = rev - cost
    print(f"  年 {deals} 件、平均 {size/10000:.1f} 億   營收 {rev:>5.0f}萬  營業利益 {op:>5.0f}萬 ({op/rev*100:5.1f}%)")

print("\nD3. 中型蘭場：業者口述『一株 50 元、賺約 10 元（毛利約 20%）』，扣管銷 8% 後營益率約 12%（假設）")
print("    關稅成本 = 售價 × 稅率 × 台方吸收比例 × 銷美占比")
for price in (50,):
    for us, lab_us in ((0.40, "銷美 40%（全國口徑）"), (0.75, "銷美 75%（一心口徑）")):
        for t, share in ((0.0, 0.5), (0.15, 0.5), (0.15, 0.3)):
            gp = price * 0.20 - price * t * share * us
            op = gp - price * 0.08
            print(f"  售價 {price:>3} 元 {lab_us:<16} 關稅 {int(t*100):>2}%、台方吸收 {int(share*100)}%："
                  f" 毛利 {gp:5.1f} 元 ({gp/price*100:4.1f}%)  營益 {op/price*100:5.1f}%")
