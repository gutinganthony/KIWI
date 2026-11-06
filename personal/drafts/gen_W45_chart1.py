"""W45 國安基金進場日買進：0050（含息）與 0050 正2（模擬）12 個月報酬 vs 進場後最深再跌（bt/scripts/run6.py）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
# (事件, 0050 12m, 正2 12m, 0050 最深再跌, 正2 最深再跌)
E=[("2004/5 319槍擊案",6,8,-7.4,-15.6),("2008/9 金融海嘯",16,15,-34.2,-59.1),("2011/12 歐債危機",11,19,-3.2,-8.1),("2015/8 人民幣貶值",20,39,-4.1,-9.8),("2020/3 新冠疫情",102,333,0,0),("2022/7 升息熊市",20,52,-13.4,-21.1),("2025/4 對等關稅",154,371,0,0)]
fig=plt.figure(figsize=(15.6,9.0),facecolor=BG)
fig.text(0.05,0.94,"■",color=GOLD,fontsize=17); fig.text(0.077,0.932,"國安基金進場那天一起買，之後發生了什麼",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.905,0.905],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.888,"以國安基金進場日收盤買進。左：持有 12 個月的報酬。右：買進後兩年內，曾經再往下跌多少（最深的那一刻）\n0050 含現金股利再投入；0050 正2：2020 年起用 00631L 實際價格；2015 年以前用 0050 每日報酬兩倍、扣年費用 1.5% 模擬",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
ys=list(range(len(E)))[::-1]; h=0.36
for k,(ttl,i1,i2,xl,fmt) in enumerate((("持有 12 個月報酬（%）",1,2,(-20,420),"{:+.0f}%"),("買進後最深再跌（%）",3,4,(-70,8),"{:.0f}%"))):
    ax=fig.add_axes([0.19+k*0.42,0.11,0.34,0.66]); ax.set_facecolor(BG)
    fig.text(0.19+k*0.42,0.79,ttl,color=INK,fontsize=16,fontproperties=sb)
    for s in ('top','right','left'): ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(LGRID); ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(axis='x',color=LGRID,lw=0.6,zorder=0); ax.axvline(0,color=INK,lw=0.9)
    ax.set_xlim(*xl); ax.set_ylim(-0.7,len(E)-0.3); ax.set_yticks(ys); ax.set_yticklabels([e[0] for e in E] if k==0 else ['']*len(E),fontsize=13.5,color=INK)
    for y,e in zip(ys,E):
        for j,(idx,col,dy) in enumerate(((i1,SLATE,h/2),(i2,RED,-h/2))):
            v=e[idx]; ax.barh(y+dy,v,height=h*0.92,color=col,zorder=3)
            pad=(xl[1]-xl[0])*0.012
            ax.text(v+(pad if v>=0 else -pad),y+dy,fmt.format(v),va='center',ha='left' if v>=0 else 'right',fontsize=11,color=INK)
fig.text(0.19,0.045,"■",color=SLATE,fontsize=14); fig.text(0.205,0.045,"0050（含息）",color=INK,fontsize=12.5)
fig.text(0.30,0.045,"■",color=RED,fontsize=14); fig.text(0.315,0.045,"0050 正2（00631L）",color=INK,fontsize=12.5)
fig.text(0.05,0.015,"資料來源：FinMind、臺灣證券交易所；國安基金進場日依財政部與媒體整理。2000 年兩次進場時 0050 尚未上市，未列入。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W45-chart-nsf-entry.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
