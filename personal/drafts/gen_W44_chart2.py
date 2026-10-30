"""W44 台股現在站在哪裡：一年高點、回檔一成／一成五、年線，與 KIWI 雙紅燈日期（FinMind 收盤＋docs/history.json）"""
import json, datetime as dt
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm, matplotlib.dates as mdates
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
B='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt'
R=json.load(open(B+'/pxv.json'))['TAIEX']
for x in json.load(open(B+'/taiex_add.json'))['data']:
    if x['date']>R[-1][0]: R.append([x['date'],0,0,0,x['close'],0])
D=[dt.date.fromisoformat(r[0]) for r in R]; C=[r[4] for r in R]
ma=[sum(C[i-249:i+1])/250 if i>=249 else None for i in range(len(C))]
s=next(i for i,d in enumerate(D) if d>=dt.date(2026,5,1))
HI=49822.55; L10=HI*0.9; L15=HI*0.85
fig=plt.figure(figsize=(15.6,8.6),facecolor=BG)
fig.text(0.05,0.94,"■",color=GOLD,fontsize=17); fig.text(0.077,0.932,"台股現在站在哪裡",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.905,0.905],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.888,"加權指數收盤。虛線是離一年高點（10/6 收盤 49,822.55）跌一成與跌一成五的位置；灰線是年線（250 日均線）。\n紅點是 KIWI 風險儀表板亮雙紅燈的日子（CRI＞35 且 TSI＞55）",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
ax=fig.add_axes([0.08,0.13,0.80,0.66]); ax.set_facecolor(BG)
for k in ('top','right'): ax.spines[k].set_visible(False)
for k in ('left','bottom'): ax.spines[k].set_color(LGRID)
ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(axis='y',color=LGRID,lw=0.6,zorder=0)
ax.plot(D[s:],C[s:],color=SLATE,lw=2.2,zorder=3)
ax.plot(D[s:],ma[s:],color=GREY,lw=1.4,zorder=2)
for y,lab in ((HI,"一年高點 49,823"),(L10,"跌一成 44,840"),(L15,"跌一成五 42,349")):
    ax.hlines(y,D[s],D[-1],color=INK if y==HI else RED,lw=1.0,ls='-' if y==HI else '--',zorder=1)
    ax.text(D[-1]+dt.timedelta(days=3),y,lab,va='center',fontsize=12,color=INK)
ax.text(D[-1]+dt.timedelta(days=3),ma[-1],"年線 %s"%format(round(ma[-1]),","),va="center",fontsize=12,color=GREY)
for d in ["2026-07-17","2026-07-24","2026-07-27","2026-07-29","2026-10-16","2026-10-22"]:
    i=D.index(dt.date.fromisoformat(d)); ax.scatter([D[i]],[C[i]],s=90,color=RED,zorder=4)
i=len(D)-1; ax.scatter([D[i]],[C[i]],s=110,color=INK,zorder=5)
ax.annotate("10/30 收 45,212\n離高點 −9.3%",(D[i],C[i]),xytext=(-230,-52),textcoords='offset points',fontsize=12.5,color=INK,bbox=dict(facecolor=BG,edgecolor='none',pad=1),arrowprops=dict(arrowstyle='-',color=GREY,lw=0.8))
ax.set_xlim(D[s],D[-1]+dt.timedelta(days=40)); ax.set_ylim(34000,51500)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%-m月'))
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v,p:f"{v:,.0f}"))
fig.lines.append(plt.Line2D([0.05,0.96],[0.07,0.07],transform=fig.transFigure,color=LGRID,lw=0.9))
fig.text(0.05,0.035,"資料來源：FinMind 收盤價、KIWI 風險儀表板（gutinganthony.github.io/KIWI）。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W44-chart-where-we-are.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
