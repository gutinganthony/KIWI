"""W46 網傳圖〈When a CEO's affair comes out〉同一組案例，扣掉標普 500 之後（research/data/2026-11-17-backtest-run15-affair-table.py）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a";LG="#c9c9c9"
# (標籤, 1年原始, 1年相對SPY, 至今原始, 至今相對財富)；相對財富＝(1+個股)/(1+標普)−1
E=[("2013 Google†",37.0,12.0,1317,145),("2012 洛克希德",60.8,29.5,904,44),("2012 百思買",11.5,-6.2,672,10),("2005 波音",26.4,20.1,318,-54),
   ("2025 柯爾百貨",126.9,95.4,269,166),("2019 亞馬遜†",14.2,-14.5,223,-2),("2023 Cboe",44.9,16.6,154,44),("2010 惠普",-28.9,-37.9,123,-75),
   ("2019 麥當勞",12.4,2.4,66,-39),("2023 BP",-12.8,-39.9,41,-20),("2018 英特爾",-9.0,-17.6,35,-57),("2025 雀巢",7.3,-13.9,19,0)]
fig=plt.figure(figsize=(15.6,10.2),facecolor=BG)
fig.text(0.05,0.948,"■",color=GOLD,fontsize=17); fig.text(0.077,0.941,"同一張「CEO 婚外情」表，扣掉大盤之後",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.915,0.915],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.9,"網傳圖的 12 個案例，起點同樣是消息曝光前一個收盤（還原股價）。灰色是網傳圖的算法（只看股價漲幅），彩色是同期扣掉標普 500（含息）之後\n† Google 曝光的是共同創辦人布林的婚變、亞馬遜的貝佐斯續任執行長，兩案都沒有執行長因此離職",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
ys=list(range(len(E)))[::-1]; h=0.36
for k,(ttl,xl,iraw,irel) in enumerate((("一年後",(-60,140),1,2),("到 2026/11/12",(-110,215),3,4))):
    ax=fig.add_axes([0.20+k*0.41,0.08,0.33 if k==0 else 0.27,0.72]); ax.set_facecolor(BG)
    fig.text(0.20+k*0.41,0.815,ttl,color=INK,fontsize=16,fontproperties=sb)
    for s in ('top','right','left'): ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(LGRID); ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(axis='x',color=LGRID,lw=0.6,zorder=0); ax.axvline(0,color=INK,lw=0.9)
    ax.set_xlim(*xl); ax.set_ylim(-0.7,len(E)-0.3); ax.set_yticks(ys)
    ax.set_yticklabels([e[0] for e in E] if k==0 else ['']*len(E),fontsize=12.5,color=INK)
    for y,e in zip(ys,E):
        raw,rel=e[iraw],e[irel]; col=GOLD if rel>=0 else RED
        if k==0:
            ax.barh(y+h/2,raw,height=h*0.9,color=LG,zorder=3); ax.text(raw+(2 if raw>=0 else -2),y+h/2,f"{raw:+.0f}%",va='center',ha='left' if raw>=0 else 'right',fontsize=9.5,color=GREY)
            ax.barh(y-h/2,rel,height=h*0.9,color=col,zorder=3); ax.text(rel+(2 if rel>=0 else -2),y-h/2,f"{rel:+.0f}%",va='center',ha='left' if rel>=0 else 'right',fontsize=9.5,color=INK)
        else:
            ax.barh(y,rel,height=h*1.4,color=col,zorder=3)
            ax.text(rel+(3 if rel>=0 else -3),y,f"{rel:+.0f}%",va='center',ha='left' if rel>=0 else 'right',fontsize=10.5,color=INK)
            ax.text(1.02,y,f"圖上 {raw:+,}%",transform=ax.get_yaxis_transform(),va='center',ha='left',fontsize=9.5,color=GREY)
fig.text(0.20,0.035,"■",color=LG,fontsize=14); fig.text(0.215,0.035,"網傳圖：股價漲幅",color=INK,fontsize=12)
fig.text(0.36,0.035,"■",color=GOLD,fontsize=14); fig.text(0.375,0.035,"扣掉標普後贏大盤",color=INK,fontsize=12)
fig.text(0.52,0.035,"■",color=RED,fontsize=14); fig.text(0.535,0.035,"扣掉標普後輸大盤",color=INK,fontsize=12)
fig.text(0.05,0.008,"資料來源：Yahoo Finance 還原股價，摸魚記自行回測；一年＝252 個交易日。右欄為「相對財富」：(1＋個股報酬)÷(1＋標普報酬)−1。僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W46-chart-affair-table.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
