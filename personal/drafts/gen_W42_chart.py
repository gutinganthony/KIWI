"""摸魚記 W42 AI 被問了三個問題：跌勢集中度＋利率兩塊（資料：FinMind 收盤）"""
import json,urllib.request,urllib.parse,time
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sans=fm.FontProperties(fname=SANS); sb=fm.FontProperties(fname=SB)
matplotlib.rcParams['font.family']=sans.get_name(); matplotlib.rcParams['axes.unicode_minus']=False
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a"
B="https://api.finmindtrade.com/api/v4/data"
def g(ds,i,s,e):
    for a in range(5):
        try:
            with urllib.request.urlopen(B+"?"+urllib.parse.urlencode({"dataset":ds,"data_id":i,"start_date":s,"end_date":e}),timeout=90) as r: return json.load(r)["data"]
        except Exception: time.sleep(20)
    raise SystemExit('fetch fail '+i)
def chg(ds,i,key):
    d={r['date']:r[key] for r in g(ds,i,"2026-10-07","2026-10-15")}
    return (d['2026-10-15']/d['2026-10-07']-1)*100
items=[("美股大盤（SPY）","USStockPrice","SPY","Close"),("美國半導體（SOXX）","USStockPrice","SOXX","Close"),
       ("美光","USStockPrice","MU","Close"),("台股加權指數","TaiwanStockPrice","TAIEX","close"),
       ("台積電","TaiwanStockPrice","2330","close"),("聯發科","TaiwanStockPrice","2454","close"),
       ("華邦電","TaiwanStockPrice","2344","close"),("南亞科","TaiwanStockPrice","2408","close")]
vals=[(n,chg(ds,i,k)) for n,ds,i,k in items]
for n,v in vals: print(f"{n} {v:+.1f}%")
yl=[]
for n,i in (("二年期","United States 2-Year"),("十年期","United States 10-Year"),("三十年期","United States 30-Year")):
    d={r['date']:r['value'] for r in g("GovernmentBondsYield",i,"2026-10-07","2026-10-14")}
    yl.append((n,(d['2026-10-14']-d['2026-10-07'])*100,d['2026-10-07'],d['2026-10-14'])); print(yl[-1])
fig=plt.figure(figsize=(15.6,9.6),facecolor=BG)
fig.text(0.05,0.945,"■",color=GOLD,fontsize=17)
fig.text(0.077,0.937,"這一週，跌的不是大盤",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.91,0.91],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.885,"利率只有短端在升，長端反而往下；跌勢集中在 AI 與記憶體",color=GREY,fontsize=14.5)
# 左：漲跌幅
fig.text(0.05,0.835,"10/7 收盤到 10/15 收盤，漲跌幅",color=INK,fontsize=16,fontproperties=sb)
ax=fig.add_axes([0.20,0.13,0.36,0.67]); ax.set_facecolor(BG)
names=[n for n,_ in vals][::-1]; v=[x for _,x in vals][::-1]
cols=[SLATE if ("大盤" in n or "加權" in n) else RED for n in names]
ax.barh(range(len(v)),v,color=cols,height=0.62,zorder=3)
ax.set_yticks(range(len(v))); ax.set_yticklabels(names,fontsize=13,color=INK)
for s in ('top','right','left'): ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(LGRID); ax.tick_params(axis='x',colors=GREY,labelsize=11,length=0); ax.tick_params(axis='y',length=0)
ax.axvline(0,color=INK,lw=0.9); ax.set_xlim(-19,3); ax.grid(axis='x',color=LGRID,lw=0.6,zorder=0)
for k,x in enumerate(v): ax.text(x-0.4,k,f"{x:+.1f}%",ha='right',va='center',fontsize=12.5,color=cols[k],fontproperties=sb)
# 右：殖利率變化
fig.text(0.62,0.835,"美債殖利率，10/7 到 10/14 的變化",color=INK,fontsize=16,fontproperties=sb)
ax2=fig.add_axes([0.66,0.13,0.30,0.63]); ax2.set_facecolor(BG)
bp=[x[1] for x in yl]; c2=[RED if b>0 else SLATE for b in bp]
ax2.bar(range(3),bp,color=c2,width=0.55,zorder=3); ax2.axhline(0,color=INK,lw=0.9)
ax2.set_xticks(range(3)); ax2.set_xticklabels([x[0] for x in yl],fontsize=13.5,color=INK)
for s in ('top','right','left'): ax2.spines[s].set_visible(False)
ax2.spines['bottom'].set_visible(False); ax2.set_yticks([]); ax2.set_ylim(-19,9); ax2.tick_params(length=0)
for k,(n,b,a0,a1) in enumerate(yl):
    ax2.text(k,b+(1.0 if b>0 else -1.0),f"{b:+.0f} 個基點",ha='center',va='bottom' if b>0 else 'top',fontsize=13,color=c2[k],fontproperties=sb)
    ax2.text(k,7.6,f"{a0:.2f}% → {a1:.2f}%",ha='center',fontsize=11.5,color=GREY)
fig.text(0.62,0.80,"紅＝上升：市場在押聯準會升息（第一塊）\n藍＝下降：長天期的額外補償（第二塊）",color=GREY,fontsize=11.5,linespacing=1.6,va="top")
fig.lines.append(plt.Line2D([0.05,0.96],[0.075,0.075],transform=fig.transFigure,color=LGRID,lw=0.9))
fig.text(0.05,0.045,"資料來源：FinMind 收盤價與美國公債殖利率（10/12 美國債市休市，10/15 殖利率資料尚未更新）。本圖為摸魚記自行整理，不構成投資建議。",color=GREY,fontsize=10)
out='/home/user/KIWI/personal/drafts/W42-chart-three-questions.png'; plt.savefig(out,dpi=150,facecolor=BG); print('Done',out)
