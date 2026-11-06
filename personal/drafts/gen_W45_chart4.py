"""W45 那斯達克 100 單日跌 6% 以上（20 天內只算第一次）之後的三種結局：之後一年內最深再跌 vs 12 個月報酬（bt/out7.txt）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
G={"急殺之後 V 轉":(SLATE,[("1987/10",-17,13),("1988/1",-4,12),("1997/10",-4,38),("1998/8",-1,110),("2011/8",-1,32),("2020/3",-12,61),("2025/4",-2,43)]),
   "熊市裡的大跌":(GOLD,[("2002/7",-10,43),("2008/9",-31,15),("2008/12",-4,64)]),
   "泡沫破裂的開始":(RED,[("2000/1",-40,-29),("2000/4",-66,-66),("2000/5",-55,-35),("2000/10",-64,-56),("2000/12",-49,-27),("2001/2",-49,-36),("2001/9",-32,-28),("2001/10",-39,-28)])}
OFF={"2000/4":(8,-4),"2000/10":(-52,-4),"2000/5":(8,4),"2001/2":(8,-12),"2000/12":(-56,6),"2001/10":(8,-12),"2001/9":(8,4),"2000/1":(-52,4),"1988/1":(8,-12),"1997/10":(-60,0),"2011/8":(8,-12),"2025/4":(8,4),"1998/8":(-58,0)}
fig=plt.figure(figsize=(15.6,9.0),facecolor=BG)
fig.text(0.05,0.94,"■",color=GOLD,fontsize=17); fig.text(0.077,0.932,"單日大跌之後的三種結局",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.905,0.905],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.888,"那斯達克 100 指數單日跌 6% 以上（同一段大跌只算第一天），1987 年以來 18 次已滿一年。以當天收盤買進\n橫軸：之後一年內最深再跌多少。縱軸：持有 12 個月的報酬",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
ax=fig.add_axes([0.08,0.10,0.86,0.70]); ax.set_facecolor(BG)
for s in ('top','right'): ax.spines[s].set_visible(False)
for s in ('left','bottom'): ax.spines[s].set_color(LGRID)
ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(color=LGRID,lw=0.6,zorder=0); ax.axhline(0,color=INK,lw=0.9)
for name,(col,pts) in G.items():
    ax.scatter([p[1] for p in pts],[p[2] for p in pts],s=170,color=col,zorder=3,label=name)
    for lab,x,y in pts: ax.annotate(lab,(x,y),xytext=OFF.get(lab,(8,4)),textcoords='offset points',fontsize=12,color=INK)
ax.set_xlim(-72,3); ax.set_ylim(-75,120)
ax.set_xlabel("之後一年內最深再跌（%）",color=GREY,fontsize=12); ax.set_ylabel("持有 12 個月報酬（%）",color=GREY,fontsize=12)
ax.legend(loc='upper left',frameon=False,fontsize=13)
fig.text(0.05,0.035,"資料來源：Yahoo Finance（^NDX），摸魚記自行回測。2026/11/5 那一次還沒有結果，未列入。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W45-chart-crash-outcomes.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
