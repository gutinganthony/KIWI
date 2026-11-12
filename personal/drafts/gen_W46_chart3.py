"""W46 超大型 IPO 掛牌之後，那斯達克 100 怎麼走（bt/scripts/run13.py）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
E=[("1999/5 高盛",70,-32),("1999/11 UPS",11,-36),("2000/4 AT&T Wireless",-48,-67),("2001/6 卡夫食品",-41,-41),("2007/6 黑石",-1,-25),("2008/3 Visa",-32,-50),("2010/11 通用汽車",8,-16),("2012/5 Facebook",20,-12),("2014/9 阿里巴巴",6,-14),("2019/5 Uber",23,-28),("2020/9 Snowflake",36,-11),("2020/12 Airbnb",32,-11),("2021/3 Coupang",7,-20),("2021/11 Rivian",-28,-35),("2023/9 Arm",27,-14)]
fig=plt.figure(figsize=(15.6,9.4),facecolor=BG)
fig.text(0.05,0.945,"■",color=GOLD,fontsize=17); fig.text(0.077,0.938,"超大型 IPO 掛牌之後，科技股怎麼走",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.91,0.91],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.895,"美國史上募資規模最大的一批 IPO，從掛牌日起算。左：那斯達克 100 之後 12 個月的報酬（虛線是 1999 年以來任一天買進的中位數 +16%）\n右：之後 12 個月內，那斯達克 100 從高點最深跌了多少",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
ys=list(range(len(E)))[::-1]
for k,(ttl,idx,xl) in enumerate((("那斯達克 100 之後 12 個月（%）",1,(-60,85)),("之後 12 個月內最大回檔（%）",2,(-75,5)))):
    ax=fig.add_axes([0.20+k*0.42,0.08,0.34,0.70]); ax.set_facecolor(BG)
    fig.text(0.20+k*0.42,0.80,ttl,color=INK,fontsize=16,fontproperties=sb)
    for s in ('top','right','left'): ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(LGRID); ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(axis='x',color=LGRID,lw=0.6,zorder=0); ax.axvline(0,color=INK,lw=0.9)
    if k==0: ax.axvline(16.2,color=GREY,lw=1.2,ls='--',zorder=2)
    ax.set_xlim(*xl); ax.set_ylim(-0.7,len(E)-0.3); ax.set_yticks(ys); ax.set_yticklabels([e[0] for e in E] if k==0 else ['']*len(E),fontsize=12.5,color=INK)
    for y,e in zip(ys,E):
        v=e[idx]; col=(SLATE if v>=0 else RED) if k==0 else (RED if v<=-20 else GOLD)
        ax.barh(y,v,height=0.6,color=col,zorder=3); pad=(xl[1]-xl[0])*0.012
        ax.text(v+(pad if v>=0 else -pad),y,f"{v:+d}%",va='center',ha='left' if v>=0 else 'right',fontsize=10.5,color=INK)
fig.text(0.05,0.025,"資料來源：Yahoo Finance（^NDX），掛牌日依公開資料，摸魚記自行回測。右圖紅色為回檔兩成以上。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W46-chart-mega-ipo.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
