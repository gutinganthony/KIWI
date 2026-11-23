"""W47 VIX 首次收上 35 之後：標普 6 個月內最多再跌多少、那斯達克 100 持有兩年報酬（research/data/2026-11-23-backtest-run16/17.py，FRED 複核 run18）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
# (標籤, 標普6個月內再跌%, 幾個交易日見底, 那指兩年報酬%)
E=[("1990/8 伊拉克入侵科威特",-12,47,55),("1997/10 亞洲金融風暴",0,0,161),("1998/8 俄羅斯違約",-8,2,200),("2001/9 九一一",-7,4,10),("2002/7 企業會計醜聞",-15,61,39),
   ("2008/9 雷曼倒閉",-41,118,20),("2010/5 歐債、閃崩",-8,39,43),("2011/8 美債降評",-2,39,51),("2015/8 人民幣貶值",-3,118,45),("2018/2 波動率風暴",-3,3,45),
   ("2018/12 升息恐慌",0,0,114),("2020/2 新冠疫情",-25,17,68),("2022/3 俄烏戰爭、升息",-13,71,35),("2024/8 日圓套利平倉",0,0,66),("2025/4 對等關稅",-2,2,None)]
fig=plt.figure(figsize=(15.6,10.4),facecolor=BG)
fig.text(0.05,0.95,"■",color=GOLD,fontsize=17); fig.text(0.077,0.943,"恐慌指數第一次收上 35 之後，買進會怎樣",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.918,0.918],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.903,"1990 年以來，美股恐慌指數 VIX 第一次收在 35 以上的 15 次（VIX 回到 20 以下才重新計算），在當天收盤買進\n左：標普 500 之後六個月內最多再跌多少，括號是第幾個交易日見底。右：那斯達克 100 持有兩年的報酬",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
ys=list(range(len(E)))[::-1]
axL=fig.add_axes([0.27,0.07,0.27,0.74]); axR=fig.add_axes([0.60,0.07,0.33,0.74])
fig.text(0.27,0.822,"之後六個月內，標普 500 最多再跌",color=INK,fontsize=14.5,fontproperties=sb); fig.text(0.60,0.822,"那斯達克 100 持有兩年",color=INK,fontsize=14.5,fontproperties=sb)
for ax in (axL,axR):
    ax.set_facecolor(BG)
    for s in ('top','right','left'): ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(LGRID); ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(axis='x',color=LGRID,lw=0.6,zorder=0); ax.set_ylim(-0.7,len(E)-0.3); ax.set_yticks(ys)
axL.set_yticklabels([e[0] for e in E],fontsize=12.5,color=INK); axR.set_yticklabels(['']*len(E))
axL.set_xlim(-62,0); axR.set_xlim(0,230); axL.axvline(0,color=INK,lw=0.9); axR.axvline(0,color=INK,lw=0.9)
for y,(lab,dd,days,r2) in zip(ys,E):
    if dd<0:
        axL.barh(y,dd,height=0.58,color=RED,zorder=3); axL.text(dd-0.8,y,f"{dd}%（第 {days} 天）",va='center',ha='right',fontsize=10.5,color=INK)
    else: axL.text(-0.8,y,"當天就是最低點",va='center',ha='right',fontsize=10.5,color=GREY)
    if r2 is None: axR.text(3,y,"未滿兩年（一年 +43%）",va='center',fontsize=10.5,color=GREY)
    else: axR.barh(y,r2,height=0.58,color=GOLD,zorder=3); axR.text(r2+3,y,f"+{r2}%",va='center',fontsize=10.5,color=INK)
fig.text(0.05,0.012,"資料來源：Yahoo Finance、FRED，摸魚記自行回測；價格指數不含股息，六個月以 126 個交易日計。過去績效不代表未來。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W47-chart-vix35.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
