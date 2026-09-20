import csv, math, random
import numpy as np
from events import EVENTS
TICS=["GOOGL","MSFT","META","QQQ"]
def load(t):
    rows=list(csv.DictReader(open(f"px/{t}.csv")))
    d=[r["date"] for r in rows]; p=np.array([float(r["adjclose"]) for r in rows])
    op=np.array([float(r["open"]) for r in rows]); v=np.array([float(r["volume"] or 0) for r in rows])
    r=np.full(len(p),np.nan); r[1:]=np.log(p[1:]/p[:-1]); return d,{x:i for i,x in enumerate(d)},r,v,p,op
PX={t:load(t) for t in TICS}
EARN={}
for t in TICS:
    dates,idx,r,v,p,op=PX[t]; byq={}
    for i,d in enumerate(dates): byq.setdefault((int(d[:4]),(int(d[5:7])-1)//3),[]).append(i)
    EARN[t]={max(ii,key=lambda i:v[i]) for q,ii in byq.items() if len(ii)>=20}
def beta_of(tic,t0):
    dates,idx,r,v,p,op=PX[tic]; bd,bi,rb,_,_,_=PX["QQQ"]
    est=range(t0-250,t0-30)
    xs=np.array([rb[bi[dates[i]]] for i in est if dates[i] in bi])
    ys=np.array([r[i] for i in est if dates[i] in bi])
    ok=~(np.isnan(xs)|np.isnan(ys)); xs,ys=xs[ok],ys[ok]
    X=np.column_stack([np.ones(len(xs)),xs]); b,*_=np.linalg.lstsq(X,ys,rcond=None); return b
def ar_day(tic,t0,k):
    dates,idx,r,v,p,op=PX[tic]; bd,bi,rb,_,_,_=PX["QQQ"]; b=beta_of(tic,t0); i=t0+k
    if i>=len(dates) or dates[i] not in bi or np.isnan(r[i]): return None
    return r[i]-(b[0]+b[1]*rb[bi[dates[i]]])
def t0_of(tic,date):
    dates,_,_,_,_,_=PX[tic]
    for i,dd in enumerate(dates):
        if dd>=date: return i
def hits(tic,t0,a,b): return any((t0+k) in EARN[tic] for k in range(a,b+1))

print("="*92)
print("【逐日拆解】正面發表事件，每一天的平均超額報酬（已排除撞財報者）")
print(f"  {'相對日':>7s}{'平均':>9s}{'中位':>9s}{'勝率':>8s}{'t值':>7s}{'n':>4s}")
for k in range(-3,6):
    v=[]
    for d,t,n,s,g in EVENTS:
        if g<0: continue
        i=t0_of(t,d)
        if i is None or i<260 or hits(t,i,k,k): continue
        a=ar_day(t,i,k)
        if a is not None: v.append(a)
    a=np.array(v); tt=a.mean()/(a.std(ddof=1)/math.sqrt(len(a)))
    star="  ←" if abs(tt)>1.6 else ""
    print(f"  {k:>+7d}{a.mean()*100:>9.2f}{np.median(a)*100:>9.2f}{100*np.mean(a>0):>7.0f}%{tt:>7.2f}{len(a):>4d}{star}")

print("\n"+"="*92)
print("【可交易性】假設你只能在『發表當天收盤』才買得到（因為多數是當天才公告）")
buy0=[]
for d,t,n,s,g in EVENTS:
    if g<0: continue
    i=t0_of(t,d)
    if i is None or i<260 or hits(t,i,1,1): continue
    a=ar_day(t,i,1)
    if a is not None: buy0.append(a)
a=np.array(buy0)
print(f"  第 0 天收盤買、第 +1 天收盤賣：平均 {a.mean()*100:+.2f}%  中位 {np.median(a)*100:+.2f}%  勝率 {100*np.mean(a>0):.0f}%  t={a.mean()/(a.std(ddof=1)/math.sqrt(len(a))):.2f}  n={len(a)}")
print(f"  標準差 {a.std(ddof=1)*100:.2f}%  ⇒ 單次下注的報酬／風險比 = {a.mean()/a.std(ddof=1):.2f}")

print("\n【事件叢聚檢查】兩個事件相隔幾個交易日？重疊視窗會讓顯著性虛高")
prev={}
close=[]
for d,t,n,s,g in EVENTS:
    if g<0: continue
    i=t0_of(t,d)
    if t in prev and i-prev[t]<=20: close.append(f"{n[:18]}(距前 {i-prev[t]} 日)")
    prev[t]=i
print(f"  20 個交易日內有前一事件的：{len(close)} 筆 → {', '.join(close) if close else '無'}")
