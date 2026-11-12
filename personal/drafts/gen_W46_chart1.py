"""W46 傳奇執行長離開後，股價相對標普 500（含息）的表現：12 個月、24 個月、到 2026/11/12（bt/scripts/run11.py）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
# 只留科技股（Jake 11/12）。(標籤, 12m, 24m, 至今, 之後一年 NDX 最大回檔<=-20%)
# NDX 一年內最大回檔：微軟 -54.8、蘋果 -11.7、甲骨文 -14.2、Alphabet -28.0、亞馬遜 -15.5、惠普 -15.2、英特爾2018 -23.0、英特爾2024 -22.9
E=[("2000/1 微軟 蓋茲",-47,-25,92,True),("2011/8 蘋果 賈伯斯",45,-7,278,False),("2014/9 甲骨文 艾利森",-10,-13,-20,False),("2019/12 Alphabet 佩吉、布林",17,45,71,True),("2021/2 亞馬遜 貝佐斯",-27,-45,-26,False),
   ("2010/8 惠普 赫德＊",-34,-68,-75,False),("2018/6 英特爾 柯再奇＊",-16,0,-56,True),("2024/12 英特爾 季辛格＊",46,None,101,True)]
fig=plt.figure(figsize=(15.6,8.6),facecolor=BG)
fig.text(0.05,0.940,"■",color=GOLD,fontsize=17); fig.text(0.077,0.934,"科技業傳奇執行長離開之後，股價贏過大盤了嗎",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.905,0.905],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.888,"以宣布前一天收盤為起點，個股含息報酬相對標普 500（SPY 含息）的超額報酬。＊為醜聞或被董事會撤換，其餘為創辦人或傳奇執行長交棒\n◆ 標記：宣布後一年內，那斯達克 100 曾從高點回落兩成以上（遇到科技股大跌）",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
ys=list(range(len(E)))[::-1]; h=0.26
ax=fig.add_axes([0.25,0.10,0.68,0.70]); ax.set_facecolor(BG)
for s in ('top','right','left'): ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(LGRID); ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(axis='x',color=LGRID,lw=0.6,zorder=0); ax.axvline(0,color=INK,lw=0.9)
ax.set_xlim(-100,300); ax.set_ylim(-0.7,len(E)-0.3); ax.set_yticks(ys); ax.set_yticklabels([("◆ " if e[4] else "")+e[0] for e in E],fontsize=12.5,color=INK)
for y,e in zip(ys,E):
    for k,(col,dy) in enumerate(((GOLD,h),(SLATE,0),(RED,-h))):
        v=e[1+k]
        if v is None: ax.text(2,y+dy,"未滿 24 個月",va='center',fontsize=9.5,color=GREY); continue
        ax.barh(y+dy,v,height=h*0.9,color=col,zorder=3)
        ax.text(v+(3 if v>=0 else -3),y+dy,f"{v:+d}%",va='center',ha='left' if v>=0 else 'right',fontsize=9.5,color=INK)
for x,lab,col in ((0.25,"12 個月",GOLD),(0.34,"24 個月",SLATE),(0.43,"到 2026/11/12",RED)):
    fig.text(x,0.045,"■",color=col,fontsize=14); fig.text(x+0.015,0.045,lab,color=INK,fontsize=12.5)
fig.text(0.05,0.008,"資料來源：Yahoo Finance 還原股價，摸魚記自行回測。宣布日以消息見報後第一個交易日計。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W46-chart-ceo-exit.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
