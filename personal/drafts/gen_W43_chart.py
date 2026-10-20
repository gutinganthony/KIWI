"""W43 確認訊號的代價：等越久，買越貴，但被洗出場的機率越低（數字取自 bt/run2.py 回測輸出）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
# (訊號, 比最低點貴%, 60日內再破底%)
TW=[("站回20日線",9.5,12/22*100),("跟進日",8.2,13/22*100),("離低點反彈5%",7.3,11/22*100),("離低點反彈10%",11.4,6/18*100),("週線WT黃金交叉",10.9,4/15*100)]
US=[("站回20日線",6.4,12/29*100),("跟進日",6.6,10/28*100),("離低點反彈5%",6.1,10/29*100),("離低點反彈10%",10.6,1/22*100),("週線WT黃金交叉",11.5,3/13*100)]
fig=plt.figure(figsize=(15.6,9.0),facecolor=BG)
fig.text(0.05,0.94,"■",color=GOLD,fontsize=17); fig.text(0.077,0.932,"等確認訊號，要錯過多少漲幅？",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.905,0.905],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.888,"跌離一年高點 8% 以上之後，第一次出現各個訊號就買進。「真正的谷底」＝這段跌勢回到前高之前的最低收盤，常常出現在訊號之後，\n所以「反彈 5%」的上車點，事後量起來會離真正谷底 6% 以上。縱軸：買進後三個月內，指數跌破買進前那個低點的機率",color=GREY,fontsize=12.5,linespacing=1.5,va='top')
for k,(data,ttl,col) in enumerate(((TW,"台股加權指數（1999 起）",RED),(US,"那斯達克 100 ETF（QQQ，2000 起）",SLATE))):
    ax=fig.add_axes([0.07+k*0.47,0.14,0.40,0.62]); ax.set_facecolor(BG)
    fig.text(0.07+k*0.47,0.80,ttl,color=INK,fontsize=16,fontproperties=sb)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color(LGRID)
    ax.tick_params(colors=GREY,labelsize=11,length=0); ax.grid(color=LGRID,lw=0.6,zorder=0)
    ax.set_xlim(4,14); ax.set_ylim(0,70); ax.set_xlabel("上車點離這段跌勢真正的谷底有多遠（中位數，%）",color=GREY,fontsize=12); ax.set_ylabel("三個月內跌破前底機率（%）",color=GREY,fontsize=12)
    for n,x,y in data:
        ax.scatter([x],[y],s=170,color=col,zorder=3)
        off={('跟進日',1):(10,-22),('離低點反彈5%',1):(-30,-30)}.get((n,k),(8,8))
        ax.annotate(n,(x,y),xytext=off,textcoords='offset points',fontsize=12.5,color=INK,bbox=dict(facecolor=BG,edgecolor='none',pad=1))
fig.lines.append(plt.Line2D([0.05,0.96],[0.07,0.07],transform=fig.transFigure,color=LGRID,lw=0.9))
fig.text(0.05,0.035,"資料來源：FinMind 收盤價，摸魚記自行回測。樣本數 13–29 次，僅供參考，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W43-chart-confirmation-cost.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
