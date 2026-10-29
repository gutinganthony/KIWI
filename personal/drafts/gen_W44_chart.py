"""W44 同樣在燒錢，市場照自由現金流打分數（數字取自 research/2026-10-30-earnings-fomc-factcheck.md、2026-10-28-ai-financing-factcheck.md）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
# (公司, Q3 自由現金流 億美元＝營運現金流−購置資產, 財報後第一個交易日漲跌%, 是否為盤後報價)
D=[("微軟",186,-0.16,False),("Meta",-21,-6.98,False),("Alphabet",-91,-12.64,False),("Amazon",-348,-5.30,True)]
fig=plt.figure(figsize=(15.6,8.6),facecolor=BG)
fig.text(0.05,0.94,"■",color=GOLD,fontsize=17); fig.text(0.077,0.932,"同樣在燒錢，市場照自由現金流打分數",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.905,0.905],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.888,"左：2026 年第三季自由現金流（營運現金流減去購置設備與資料中心的支出）。右：財報公布後第一個交易日的股價漲跌\n微軟、Alphabet 為 10/29，Meta 為 10/22，Amazon 為 10/29 盤後報價（各家報導從 −5% 到 −10% 都有）",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
ys=list(range(len(D)))[::-1]
for k,(ttl,idx,xl,unit) in enumerate((("第三季自由現金流（億美元）",1,(-500,260),"億"),("財報後第一個交易日股價（%）",2,(-15.5,3.5),"%"))):
    ax=fig.add_axes([0.13+k*0.45,0.13,0.36,0.62]); ax.set_facecolor(BG)
    fig.text(0.13+k*0.45,0.79,ttl,color=INK,fontsize=16,fontproperties=sb)
    for s in ('top','right','left'): ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(LGRID); ax.tick_params(colors=GREY,labelsize=11,length=0)
    ax.grid(axis='x',color=LGRID,lw=0.6,zorder=0); ax.axvline(0,color=INK,lw=0.9,zorder=2)
    ax.set_xlim(*xl); ax.set_ylim(-0.7,len(D)-0.3)
    ax.set_yticks(ys); ax.set_yticklabels([d[0] for d in D] if k==0 else ['']*len(D),fontsize=15,color=INK)
    for y,d in zip(ys,D):
        v=d[idx]; col=SLATE if v>=0 else RED
        hatch='//' if (k==1 and d[3]) else None
        ax.barh(y,v,height=0.55,color=col if not hatch else BG,edgecolor=col,hatch=hatch,lw=1.2,zorder=3)
        txt=(f"{v:+,.0f} 億" if unit=="億" else f"{v:+.2f}%")+("（盤後）" if (k==1 and d[3]) else "")
        pad=(xl[1]-xl[0])*0.015
        ax.text(v+(pad if v>=0 else -pad),y,txt,va='center',ha='left' if v>=0 else 'right',fontsize=13,color=INK,zorder=4)
fig.lines.append(plt.Line2D([0.05,0.96],[0.07,0.07],transform=fig.transFigure,color=LGRID,lw=0.9))
fig.text(0.05,0.035,"資料來源：各公司 SEC 財報（自由現金流為摸魚記以營運現金流減購置資產自行計算）、Yahoo Finance 收盤價。同期那斯達克：10/22 −2.60%、10/29 −1.38%。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W44-chart-fcf-scorecard.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
