"""W44 錢流示意圖：缺錢的、缺貨的、被擠的（概念圖，無新數字）"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; SB='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS,SB): fm.fontManager.addfont(p)
sb=fm.FontProperties(fname=SB); matplotlib.rcParams['font.family']=fm.FontProperties(fname=SANS).get_name()
BG="#ffffff";INK="#1a1a1a";GREY="#6b6b6b";LGRID="#dcdcdc";GOLD="#b8954a";RED="#b23b32";SLATE="#4a5d7a";PALE="#f4f1ea"
fig=plt.figure(figsize=(15.6,8.6),facecolor=BG)
fig.text(0.05,0.94,"■",color=GOLD,fontsize=17); fig.text(0.077,0.932,"同一條鏈上的三種位置",color=INK,fontsize=27,fontproperties=sb)
fig.lines.append(plt.Line2D([0.05,0.96],[0.905,0.905],transform=fig.transFigure,color=INK,lw=1.0))
fig.text(0.077,0.888,"箭頭是錢的流向。雲端業者借錢買記憶體，記憶體廠賺到錢再回饋股東，代價有一部分落在電腦和手機這一端",color=GREY,fontsize=12.5,va='top')
ax=fig.add_axes([0.03,0.06,0.94,0.78]); ax.set_xlim(0,100); ax.set_ylim(0,60); ax.axis('off')
def box(x,y,w,h,title,tag,lines,col):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.4,rounding_size=1.2",fc=PALE,ec=col,lw=2))
    ax.text(x+1.5,y+h-3.2,title,fontsize=19,color=INK,fontproperties=sb,va='center')
    ax.text(x+w-1.5,y+h-3.2,tag,fontsize=15,color=BG,va='center',ha='right',bbox=dict(boxstyle="round,pad=0.35",fc=col,ec='none'))
    for k,t in enumerate(lines): ax.text(x+1.5,y+h-8.5-k*4.4,t,fontsize=13.5,color=INK,va='center')
def arrow(a,b,txt,col=GREY,off=(0,1.8),rad=0.0):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=22,color=col,lw=2,connectionstyle=f"arc3,rad={rad}"))
    ax.text((a[0]+b[0])/2+off[0],(a[1]+b[1])/2+off[1],txt,fontsize=12.5,color=col,ha='center',va='bottom')
# 外部資金
box(2,37,24,20,"外部資金","借來的錢",["債市：發公司債","股市：發新股、特別股","私募：買晶片再出租"],GREY)
# 雲端
box(2,6,24,26,"雲端業者","缺錢",["需求是真的，雲端營收大增","但擴張跑贏賺錢的速度","自由現金流轉負","差額靠借，借錢的價格變貴"],SLATE)
# 記憶體
box(38,6,26,26,"記憶體廠","缺貨",["缺在自己手上：可以漲價","客戶先簽長約排隊","利潤率創紀錄","但也是最擁擠的交易"],RED)
# PC
box(76,6,22,26,"電腦與手機","被擠",["記憶體變貴、變難買","整機售價被推高","品牌降庫存、出貨衰退","英特爾財報後重挫"],INK)
# 設備
box(38,37,26,20,"設備商","缺在別人手上",["無塵室、零組件不夠","訂單接得到，貨出不去","瓶頸，不是定價權"],GOLD)
# 股東
box(76,37,22,20,"記憶體廠股東","回饋",["股利","買回庫藏股"],GREY)
arrow((13,36.5),(13,32.8),"",GREY)
ax.text(14,34.6,"補缺口",fontsize=12.5,color=GREY,va='center')
arrow((26.6,19),(37.4,19),"付錢買記憶體",SLATE)
arrow((64.6,19),(75.4,19),"漲價的成本往下傳",RED)
arrow((64.6,28),(75.4,42),"",RED,rad=-0.15)
ax.text(72.0,34.6,"賺到的錢",fontsize=12.5,color=RED,ha="left",va="center",bbox=dict(facecolor=BG,edgecolor="none",pad=1))
arrow((51,32.8),(51,36.5),"",GOLD)
ax.text(52.2,34.6,"擴產要買設備",fontsize=12.5,color=GOLD,va='center')
fig.lines.append(plt.Line2D([0.05,0.96],[0.05,0.05],transform=fig.transFigure,color=LGRID,lw=0.9))
fig.text(0.05,0.022,"資料來源：各公司財報與法說、彭博，摸魚記整理。概念示意，不構成投資建議。",color=GREY,fontsize=10)
out='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/nl/personal/drafts/W44-chart-three-positions.png'; plt.savefig(out,dpi=150,facecolor=BG); print(out)
