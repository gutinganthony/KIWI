"""W47 這次像 1998 還是 2000？從高點起算的路徑（research/data/2026-11-23-backtest-run16.py → bt/r16/paths.json）"""
import json, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a";GREEN="#5b7f5b";LG="#b5b5b5"
P=json.load(open('/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/r16/paths.json'))
STY={'1998':(GREEN,'1998 亞洲金融風暴／LTCM'),'2000':(SLATE,'2000 網路泡沫破裂'),'2008':(LG,'2008 金融海嘯'),'2022':(GOLD,'2022 升息熊市'),'2026':(RED,'2026 這一次')}
fig=plt.figure(figsize=(15.6,8.8),facecolor=BG)
fig.text(0.05,0.94,"■",color=GOLD,fontsize=17); fig.text(0.077,0.933,"這次比較像 1998 年，還是 2000 年？",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.905,0.905],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.89,"各次從前高收盤起算的累計跌幅，橫軸是距離高點的交易日數。紅線為 2026 年 10 月 6 日高點以來（台股至 11/20、那斯達克 100 至 11/20 收盤）",color=GREY,fontsize=12.5,va='top')
for k,mk in enumerate(['台股','那斯達克100']):
    ax=fig.add_axes([0.07+k*0.48,0.11,0.42,0.66]); ax.set_facecolor(BG)
    fig.text(0.07+k*0.48,0.795,'台股加權指數' if k==0 else '那斯達克 100',color=INK,fontsize=16,fontproperties=sb)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color(LGRID)
    ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(color=LGRID,lw=0.6,zorder=0); ax.axhline(0,color=INK,lw=0.9)
    for y,(d0,pth) in P[mk].items():
        col,lab=STY[y]; xs=[a for a,b in pth if a<=400]; ys=[b for a,b in pth if a<=400]
        ax.plot(xs,ys,color=col,lw=3.2 if y=='2026' else 1.8,zorder=5 if y=='2026' else 3,label=f"{lab}（高點 {d0[:7].replace('-','/')}）")
        if y=='2026': ax.scatter([xs[-1]],[ys[-1]],color=RED,s=60,zorder=6); ax.annotate(f"{ys[-1]:.0f}%",(xs[-1],ys[-1]),xytext=(10,-18),textcoords='offset points',color=RED,fontsize=13,fontproperties=sb,bbox=dict(boxstyle='round,pad=0.2',fc='white',ec='none'),zorder=7)
    ax.set_xlim(0,400); ax.set_ylim(-80,25); ax.set_xlabel("距離高點的交易日數",color=GREY,fontsize=11.5); ax.set_ylabel("距高點（%）",color=GREY,fontsize=11.5)
    if k==1: ax.text(118,21,'1998 這條之後一路漲，一年後 +110%',color=GREEN,fontsize=11,va='top')
    ax.legend(loc='lower left',frameon=False,fontsize=10.5)
fig.text(0.05,0.015,"資料來源：Yahoo Finance、證交所，摸魚記自行計算；價格指數，不含股息。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W47-chart-1998-vs-2000.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
