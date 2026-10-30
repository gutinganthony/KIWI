"""W44 外資與投信累計買賣超（10/6–10/30，FinMind；10/30 用證交所 BFI82U）"""
import json, datetime as dt
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
d=json.load(open('/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/inst_all.json'))['data']
f={r['date']:(r['buy']-r['sell'])/1e8 for r in d if r['name']=='Foreign_Investor'}
t={r['date']:(r['buy']-r['sell'])/1e8 for r in d if r['name']=='Investment_Trust'}
f['2026-10-30']=-1124.67; t['2026-10-30']=239.93
ks=sorted(k for k in f if '2026-10-06'<=k<='2026-10-30')
cf=[];ct=[];a=b=0
for k in ks: a+=f[k]; b+=t.get(k,0); cf.append(a); ct.append(b)
x=list(range(len(ks))); lab=[f"{int(k[5:7])}/{int(k[8:])}" for k in ks]
fig=plt.figure(figsize=(15.6,8.6),facecolor=BG)
fig.text(0.05,0.94,"■",color=GOLD,fontsize=17); fig.text(0.077,0.932,"外資一路賣，投信一路接",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.905,0.905],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.888,"從十月六日台股創高那天起算，外資與投信在台股集中市場的累計買賣超（億元）。長條是外資每天的買賣超",color=GREY,fontsize=12.5,va='top')
ax=fig.add_axes([0.09,0.13,0.76,0.66]); ax.set_facecolor(BG)
for s in ('top','right'): ax.spines[s].set_visible(False)
for s in ('left','bottom'): ax.spines[s].set_color(LGRID)
ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(axis='y',color=LGRID,lw=0.6,zorder=0); ax.axhline(0,color=INK,lw=0.9)
ax.bar(x,[f[k] for k in ks],width=0.55,color=[RED if f[k]<0 else SLATE for k in ks],alpha=0.35,zorder=2)
ax.plot(x,cf,color=RED,lw=2.6,marker='o',ms=5,zorder=3); ax.plot(x,ct,color=SLATE,lw=2.6,marker='o',ms=5,zorder=3)
ax.text(x[-1]+0.4,cf[-1],f"外資累計\n{cf[-1]:,.0f} 億",va='center',fontsize=13,color=RED)
ax.text(x[-1]+0.4,ct[-1],f"投信累計\n+{ct[-1]:,.0f} 億",va='center',fontsize=13,color=SLATE)
i=ks.index('2026-10-15'); ax.annotate(f"10/15 單日 {f[ks[i]]:,.0f} 億\n史上最大",(x[i],f[ks[i]]),xytext=(40,-15),textcoords='offset points',fontsize=12,color=INK,bbox=dict(facecolor=BG,edgecolor='none',pad=1),arrowprops=dict(arrowstyle='-',color=GREY,lw=0.8))
i=len(ks)-1; ax.annotate(f"10/30 單日 {f[ks[i]]:,.0f} 億\n史上第七大",(x[i],f[ks[i]]),xytext=(-150,-40),textcoords='offset points',fontsize=12,color=INK,arrowprops=dict(arrowstyle='-',color=GREY,lw=0.8))
ax.set_xticks(x); ax.set_xticklabels(lab); ax.set_xlim(-0.6,len(x)+1.6)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v,p:f"{v:,.0f}"))
fig.lines.append(plt.Line2D([0.05,0.96],[0.07,0.07],transform=fig.transFigure,color=LGRID,lw=0.9))
fig.text(0.05,0.035,"資料來源：FinMind、臺灣證券交易所三大法人買賣金額統計。「史上」指 2004 年有資料以來。10/23、10/26 休市。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W44-chart-foreign-flows.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out, round(cf[-1]), round(ct[-1]))
