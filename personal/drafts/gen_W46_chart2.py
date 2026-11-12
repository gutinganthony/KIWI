"""W46 跟輝達連動越高，這週跌越重嗎？近一年週報酬相關係數 vs 11/6 以來相對大盤（bt/scripts/run12.py；台股至 11/11、美股至 11/12）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a";GREEN="#5b7f5b"
TW={"輝達平台組裝":(RED,[("鴻海",.37,-3.7),("廣達",.22,-8.9),("緯創",.26,-2.4),("緯穎",.44,-3.4),("技嘉",.44,-9.1),("英業達",.28,-14.1),("華碩",.23,-6.5),("和碩",-.02,-7.9)]),
    "客製晶片設計服務":(GREEN,[("世芯",.46,17.5),("創意",.27,15.6)]),
    "散熱、電力、板材":(GOLD,[("奇鋐",.22,20.1),("台達電",.29,11.3),("台光電",.23,6.3),("欣興",.13,7.4)]),
    "晶圓、封測、記憶體、IC 設計":(SLATE,[("台積電",.27,.7),("日月光",.26,5.6),("京元電",.12,.7),("南亞科",.45,3.2),("華邦電",.31,1.8),("聯發科",.38,6.2)])}
US={"輝達":(RED,[("輝達",1.0,-17.2)]),"競爭對手與網通":(GREEN,[("AMD",.46,25.3),("博通",.53,19.5),("Marvell",.40,13.5),("Arista",.40,14.8)]),
    "雲端與新雲":(GOLD,[("CoreWeave",.51,19.3),("甲骨文",.47,5.0),("Meta",.56,-2.9),("微軟",.23,-6.0),("Alphabet",.24,-.6),("亞馬遜",.28,-1.3)]),
    "伺服器、記憶體、電力":(SLATE,[("戴爾",.27,5.6),("美超微",.35,-8.1),("美光",.44,9.2),("Vertiv",.53,11.0)])}
OFF={"台光電":(-46,6),"日月光":(6,-14),"台積電":(-48,-4),"華邦電":(6,4),"CoreWeave":(-78,4),"博通":(6,-14),"Alphabet":(-62,6),"亞馬遜":(6,-12),"Marvell":(6,-12)}
fig=plt.figure(figsize=(15.6,9.2),facecolor=BG)
fig.text(0.05,0.945,"■",color=GOLD,fontsize=17); fig.text(0.077,0.938,"跟輝達連動越高，這週跌得越重嗎？",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.91,0.91],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.895,"橫軸：過去一年與輝達的週報酬相關係數。縱軸：11/6（調查曝光前）到最新收盤，相對大盤的超額報酬（台股比加權指數至 11/11，美股比 QQQ 至 11/12）\n顏色是生意上和輝達綁得多緊，不是統計上的相關",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
for k,(G,ttl,xl) in enumerate(((TW,"台股",(-.08,.55)),(US,"美股",(.1,1.05)))):
    ax=fig.add_axes([0.07+k*0.48,0.10,0.42,0.68]); ax.set_facecolor(BG)
    fig.text(0.07+k*0.48,0.80,ttl,color=INK,fontsize=16,fontproperties=sb)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color(LGRID)
    ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(color=LGRID,lw=0.6,zorder=0); ax.axhline(0,color=INK,lw=0.9)
    for name,(col,pts) in G.items():
        ax.scatter([p[1] for p in pts],[p[2] for p in pts],s=120,color=col,zorder=3,label=name)
        for lab,x,y in pts: ax.annotate(lab,(x,y),xytext=OFF.get(lab,(6,4)),textcoords='offset points',fontsize=11,color=INK)
    ax.set_xlim(*xl); ax.set_ylim(-20,30); ax.set_xlabel("與輝達的週報酬相關係數",color=GREY,fontsize=11.5); ax.set_ylabel("相對大盤（%）",color=GREY,fontsize=11.5)
    ax.legend(loc='upper left',frameon=False,fontsize=11)
fig.text(0.05,0.03,"資料來源：Yahoo Finance，摸魚記自行計算。輝達本身同期 −11.5%（相對 QQQ −17.2%）。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W46-chart-supply-chain.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
