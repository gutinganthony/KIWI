"""W47 台股這次是誰在賣：上市融資餘額（證交所 MI_MARGN）與外資買賣超（BFI82U）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
D=["11/13","11/16","11/17","11/18","11/19","11/20"]
MG=[5366.0,5245.0,5087.2,5080.3,4843.7,4352.3]   # 上市融資餘額（億元）
FD=["11/16","11/17","11/18","11/19","11/20","11/23"]; FI=[-701.9,-380.9,-765.6,-243.1,-95.1,-289.5]  # 外資及陸資買賣超（億元）
IX=[41040.08,40092.11,40194.91,38426.89,36033.29,36811.89]
fig=plt.figure(figsize=(15.6,8.4),facecolor=BG)
fig.text(0.05,0.94,"■",color=GOLD,fontsize=17); fig.text(0.077,0.932,"台股連跌一成的那兩天，外資反而賣得最少",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.902,0.902],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.887,"左：上市融資餘額，一週少了一千億元以上，其中 11/19、11/20 兩天就減少 728 億元。右：外資每日買賣超與加權指數收盤",color=GREY,fontsize=12.5,va='top')
ax=fig.add_axes([0.07,0.12,0.40,0.66]); ax.set_facecolor(BG); fig.text(0.07,0.80,"上市融資餘額（億元）",color=INK,fontsize=15,fontproperties=sb)
for s in ('top','right','left'): ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(LGRID); ax.tick_params(colors=GREY,labelsize=11.5,length=0); ax.grid(axis='y',color=LGRID,lw=0.6,zorder=0)
ax.bar(D,MG,color=[SLATE]*4+[RED,RED],width=0.62,zorder=3); ax.set_ylim(4000,5600)
for x,v in zip(D,MG): ax.text(x,v+18,f"{v:,.0f}",ha='center',fontsize=11,color=INK)
ax2=fig.add_axes([0.56,0.12,0.38,0.66]); ax2.set_facecolor(BG); fig.text(0.56,0.80,"外資買賣超（億元，柱）與加權指數（線）",color=INK,fontsize=15,fontproperties=sb)
for s in ('top','right','left'): ax2.spines[s].set_visible(False)
ax2.spines['bottom'].set_color(LGRID); ax2.tick_params(colors=GREY,labelsize=11.5,length=0); ax2.grid(axis='y',color=LGRID,lw=0.6,zorder=0); ax2.axhline(0,color=INK,lw=0.9)
ax2.bar(FD,FI,color=GOLD,width=0.62,zorder=3); ax2.set_ylim(-900,650); ax2.set_yticks([-800,-600,-400,-200,0])
for x,v in zip(FD,FI): ax2.text(x,v-38,f"{v:,.0f}",ha='center',fontsize=11,color=INK)
ax3=ax2.twinx(); ax3.plot(FD,IX,color=RED,lw=2.4,marker='o',ms=6,zorder=5); ax3.set_ylim(22600,42600); ax3.set_yticks([])
for s in ('top','right','left','bottom'): ax3.spines[s].set_visible(False)
ax3.tick_params(colors=RED,labelsize=11,length=0)
for x,v in zip(FD,IX): ax3.text(x,v+520,f"{v:,.0f}",ha='center',fontsize=10.5,color=RED)
fig.text(0.05,0.015,"資料來源：臺灣證券交易所（信用交易統計、三大法人買賣金額統計表）。外資為外資及陸資（不含外資自營商）。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W47-chart-who-sold.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
