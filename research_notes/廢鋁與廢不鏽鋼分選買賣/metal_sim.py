# 廢鋁、廢不鏽鋼分選買賣模型。事實來源 r5-aluminium/stainless/equipment/margins.md；(A)=假設
W = 1e4
def light(name, tons, price, gm_pcts, fixed_yr, transport_kg, inv_days=30, ar_days=30, drop=0.264):
    rev = tons*1000*price
    print(f"\n== {name}：年 {tons:,} 噸 × {price} 元/公斤 = 營收 {rev/1e8:.2f} 億元 ==")
    print("  毛利率(A) | 每公斤毛利 | 毛利(萬) | 固定費用+折舊 | 運費 | 營業利益(萬) | 營益率")
    for g in gm_pcts:
        gp = rev*g; tr = tons*1000*transport_kg; op = gp - fixed_yr - tr
        print(f"   {g:5.1%}   |  {price*g:5.1f}    | {gp/W:7,.0f} |   {fixed_yr/W:6,.0f}     | {tr/W:4,.0f} | {op/W:8,.0f}    | {op/rev:5.1%}")
    wc = rev*(inv_days+ar_days)/365
    print(f"  營運資金(存貨{inv_days}天+應收{ar_days}天)：約 {wc/W:,.0f} 萬元；存貨遇三個月跌 {drop:.0%} 的跌價損失：約 {rev*inv_days/365*drop/W:,.0f} 萬元")

fixed = (23.1+10.0)*12*1e4      # 月固定 23.1 萬 + 折舊 10 萬（r5-equipment 輕資產表，多為假設）
light("廢鋁 輕資產（手持雷射光譜儀＋400 坪場地）", 2400, 65, (0.04, 0.08, 0.12, 0.18), fixed, 1.0)
light("廢不鏽鋼 輕資產（手持 X 光分析儀）", 2400, 36, (0.03, 0.05, 0.08), fixed, 1.0)
light("廢鋁＋廢不鏽鋼 共用一個場", 4800, 50.5, (0.04, 0.07, 0.10), fixed*1.3, 1.0)

print("\n== 廢鋁 重資產：自動分選線，年 25,000 噸(A) ==")
t = 25000; price = 60; rev = t*1000*price
capex_lo, capex_hi = 2.5e8, 4.0e8            # 挪威案例 2.25 億(3 噸/時)外加前處理(A)
print(f"  營收約 {rev/1e8:.1f} 億元；投資 {capex_lo/1e8:.1f}-{capex_hi/1e8:.1f} 億元(A)；營運資金(60天) 約 {rev*60/365/1e8:.1f} 億元")
print("  每公斤升值(A) | 處理成本 | 貢獻(億) | 扣管銷 3,000 萬(A) 後 EBITDA(億) | 每噸 EBITDA(美元)")
for up, proc in ((3.5, 3.2), (6.0, 3.2), (8.0, 2.6), (12.0, 2.6)):
    contrib = t*1000*(up-proc); ebitda = contrib - 3e7
    print(f"     {up:4.1f}      |  {proc:3.1f}    | {contrib/1e8:5.2f}   |        {ebitda/1e8:5.2f}                 |   {ebitda/t/32:5.0f}")
print("  同業基準：有分選加工的每噸 EBITDA 35–130 美元；景氣差 5–40 美元")
for usd in (5, 40, 80, 130):
    e = usd*32*t
    print(f"    每噸 {usd:>3} 美元 → EBITDA {e/1e8:4.2f} 億元 → 回本 {capex_lo/e:5.1f}–{capex_hi/e:5.1f} 年")

print("\n== 市場規模（推算，來自兩份底盤）==")
print("  廢鋁：年流通 48.5–52 萬噸、貨值 267–416 億元；分選可創造毛價值 5.6–40 億元（混合料占比 15–40% 為假設）")
print("  廢不鏽鋼：年流通 40–47 萬噸、貨值 120–188 億元；分選可創造價值 0.55–7.5 億元")
for share in (0.005, 0.01, 0.05):
    print(f"  廢鋁市占 {share:.1%} = {50e4*share:,.0f} 噸，營收約 {50e4*share*1000*65/1e8:.1f} 億元")
