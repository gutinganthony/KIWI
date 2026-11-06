"""W45 美股版：VIX 第一次收上 35 那天買那斯達克 100（指數與兩倍模擬），12 個月報酬與兩年內最深再跌（bt/scripts/run9.py）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
E=[("1990/8 伊拉克入侵科威特",35,71,-18,-34),("1997/10 亞洲金融風暴",40,75,-6,-13),("1998/8 俄羅斯違約",83,186,-14,-29),("2001/9 九一一",-28,-58,-36,-67),("2002/7 世界通訊破產",27,39,-21,-41),("2008/9 雷曼倒閉",5,-9,-37,-65),("2010/5 閃電崩盤",29,59,-7,-14),("2011/8 美債降評",32,64,-1,-3),("2015/8 人民幣貶值",19,36,-2,-7),("2018/2 波動率崩盤",8,9,-9,-22),("2018/12 聖誕節崩跌",47,109,0,0),("2020/2 新冠疫情",53,102,-17,-35),("2022/3 升息熊市",-8,-25,-20,-42),("2024/8 日圓套利平倉",31,60,-4,-12),("2025/4 對等關稅",43,94,-2,-4)]
fig=plt.figure(figsize=(15.6,11.2),facecolor=BG)
fig.text(0.05,0.952,"■",color=GOLD,fontsize=17); fig.text(0.077,0.946,"美股版的「國安基金」：恐慌指數第一次收上 35",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.925,0.925],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.91,"VIX 第一次收盤站上 35（之前曾回到 20 以下才算新的一次）那天，以收盤買進那斯達克 100。左：持有 12 個月的報酬。右：買進後兩年內最深再跌多少\n兩倍為以那斯達克 100 每日報酬兩倍、扣年費用 1% 模擬，未計股利，與實際 QLD 會有落差",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
ys=list(range(len(E)))[::-1]; h=0.38
for k,(ttl,i1,i2,xl,fmt) in enumerate((("持有 12 個月報酬（%）",1,2,(-95,215),"{:+.0f}%"),("兩年內最深再跌（%）",3,4,(-80,8),"{:.0f}%"))):
    ax=fig.add_axes([0.22+k*0.40,0.08,0.33,0.75]); ax.set_facecolor(BG)
    fig.text(0.22+k*0.40,0.845,ttl,color=INK,fontsize=16,fontproperties=sb)
    for s in ('top','right','left'): ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(LGRID); ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(axis='x',color=LGRID,lw=0.6,zorder=0); ax.axvline(0,color=INK,lw=0.9)
    ax.set_xlim(*xl); ax.set_ylim(-0.7,len(E)-0.3); ax.set_yticks(ys); ax.set_yticklabels([e[0] for e in E] if k==0 else ['']*len(E),fontsize=12.5,color=INK)
    for y,e in zip(ys,E):
        for idx,col,dy in ((i1,SLATE,h/2),(i2,RED,-h/2)):
            v=e[idx]; ax.barh(y+dy,v,height=h*0.92,color=col,zorder=3); pad=(xl[1]-xl[0])*0.012
            ax.text(v+(pad if v>=0 else -pad),y+dy,fmt.format(v),va='center',ha='left' if v>=0 else 'right',fontsize=10,color=INK)
fig.text(0.22,0.035,"■",color=SLATE,fontsize=14); fig.text(0.235,0.035,"那斯達克 100",color=INK,fontsize=12.5)
fig.text(0.33,0.035,"■",color=RED,fontsize=14); fig.text(0.345,0.035,"那斯達克 100 兩倍（模擬）",color=INK,fontsize=12.5)
fig.text(0.05,0.01,"資料來源：Yahoo Finance（^NDX、^VIX），摸魚記自行回測。1990 年以來 15 次。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W45-chart-us-vix35.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
