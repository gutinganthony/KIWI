# Unit economics sketch (all assumptions labelled in report)
for rev in (1e8,2e8,3e8):
    labor=0.55*rev; addr=0.25*labor
    for name,p,revup in (("保守",0.03,0.0),("基準",0.14,0.01),("樂觀",0.31,0.03)):
        # 保守: 3% of ALL labor (Humlum); 基準: 14% of addressable labor; 樂觀: 31% of addressable
        save = p*labor if name=="保守" else p*addr
        rev_gain = revup*rev*0.30   # incremental revenue at 30% contribution margin
        recurring = 1.8e6 + 0.004*rev   # tech lead/外包 1.8M + SaaS/API 0.4% of revenue
        onetime = 3e6 + 0.01*rev        # data cleanup/ERP/integration
        net = save+rev_gain-recurring
        pb = onetime/net if net>0 else float('inf')
        print(f"rev {rev/1e8:.0f}億 {name}: 節省{save/1e4:.0f}萬 營收貢獻{rev_gain/1e4:.0f}萬 經常成本{recurring/1e4:.0f}萬 淨{net/1e4:.0f}萬 = {net/rev*100:+.1f}pp 一次性{onetime/1e4:.0f}萬 回本{pb:.1f}年")
