import csv, math, random
import numpy as np
from events import EVENTS
TICS=["GOOGL","MSFT","META","NVDA","AVGO","TSM","AMD","SMH","QQQ"]
def load(t):
    rows=list(csv.DictReader(open(f"px/{t}.csv")))
    d=[r["date"] for r in rows]; p=np.array([float(r["adjclose"]) for r in rows])
    v=np.array([float(r["volume"] or 0) for r in rows])
    r=np.full(len(p),np.nan); r[1:]=np.log(p[1:]/p[:-1]); return d,{x:i for i,x in enumerate(d)},r,v
PX={t:load(t) for t in TICS}
EARN={}
for t in TICS:
    dates,idx,r,v=PX[t]; byq={}
    for i,d in enumerate(dates):
        byq.setdefault((int(d[:4]),(int(d[5:7])-1)//3),[]).append(i)
    EARN[t]={max(ii,key=lambda i:v[i]) for q,ii in byq.items() if len(ii)>=20}
def car(tic,t0,a,b):
    dates,idx,r,v=PX[tic]; bd,bi,rb,_=PX["QQQ"]
    if t0<260: return None
    est=range(t0-250,t0-30)
    xs=np.array([rb[bi[dates[i]]] for i in est if dates[i] in bi])
    ys=np.array([r[i] for i in est if dates[i] in bi])
    ok=~(np.isnan(xs)|np.isnan(ys)); xs,ys=xs[ok],ys[ok]
    X=np.column_stack([np.ones(len(xs)),xs]); beta,*_=np.linalg.lstsq(X,ys,rcond=None)
    tot=0.0; got=0
    for k in range(a,b+1):
        i=t0+k
        if i>=len(dates) or dates[i] not in bi or np.isnan(r[i]): continue
        tot+=r[i]-(beta[0]+beta[1]*rb[bi[dates[i]]]); got+=1
    return tot if got else None
def t0_of(tic,date):
    dates,_,_,_=PX[tic]
    for i,dd in enumerate(dates):
        if dd>=date: return i
def hits(tic,t0,a,b): return any((t0+k) in EARN[tic] for k in range(a,b+1))

print("="*96)
print("【一】負面事件（樣本太少，只做描述）")
print(f"{'日期':11s}{'標的':6s}{'事件':24s}{'[0]':>8s}{'[0,+1]':>9s}{'[+1,+20]':>10s}")
for d,t,n,s,g in EVENTS:
    if g>0: continue
    i=t0_of(t,d)
    print(f"{d:11s}{t:6s}{n[:22]:24s}{car(t,i,0,0)*100:>8.2f}{car(t,i,0,1)*100:>9.2f}{car(t,i,1,20)*100:>10.2f}")

print("\n【二】不對稱：正面發表 vs 負面事件")
posv=[car(t,t0_of(t,d),0,1) for d,t,n,s,g in EVENTS if g>0 and not hits(t,t0_of(t,d),0,1)]
posv=[x for x in posv if x is not None]
print(f"  正面 [0,+1] 平均 {np.mean(posv)*100:+.2f}%（n={len(posv)}）")
print(f"  負面 [0,+1]：DeepSeek −6.98%、Gemini 3.5 延遲 −3.89% ⇒ 量級是正面的 5–9 倍")

print("\n"+"="*96)
print("【三】大版號 vs 小改版（只看排除財報後的 [0,+1]）")
MAJOR={"ChatGPT 發表","GPT-4","GPT-5","Gemini 1.0","Gemini 3 Pro / DeepThink","Llama 2","Llama 3","Llama 4（4/5 週六，順延）","Gemini 2.0 Flash Exp","Gemini 2.5 Pro Exp"}
for lab,f in [("大版號",lambda n:n in MAJOR),("小改版",lambda n:n not in MAJOR)]:
    v=[car(t,t0_of(t,d),0,1) for d,t,n,s,g in EVENTS if g>0 and f(n) and not hits(t,t0_of(t,d),0,1)]
    v=[x for x in v if x is not None]
    if len(v)>=3:
        a=np.array(v); print(f"  {lab}：平均 {a.mean()*100:+.2f}%  中位 {np.median(a)*100:+.2f}%  勝率 {100*np.mean(a>0):.0f}%  n={len(a)}")

print("\n"+"="*96)
print("【四】外溢：模型發表日，供應鏈有沒有動？（[0,+1] 超額報酬 vs QQQ）")
launch=[(d,t) for d,t,n,s,g in EVENTS if g>0]
print(f"  {'標的':8s}{'平均':>9s}{'中位':>9s}{'勝率':>8s}{'t值':>7s}{'n':>4s}{'隨機百分位':>12s}")
random.seed(11)
for proxy in ["NVDA","AVGO","TSM","AMD","SMH"]:
    v=[]
    for d,t in launch:
        i=t0_of(proxy,d)
        if i and not hits(proxy,i,0,1):
            c=car(proxy,i,0,1)
            if c is not None: v.append(c)
    if len(v)<5: continue
    a=np.array(v); tt=a.mean()/(a.std(ddof=1)/math.sqrt(len(a)))
    sim=[]
    for _ in range(1500):
        vv=[]
        for _ in range(len(a)):
            dates,_,_,_=PX[proxy]; i=random.randint(270,len(dates)-25)
            if hits(proxy,i,0,1): continue
            c=car(proxy,i,0,1)
            if c is not None: vv.append(c)
        if vv: sim.append(np.mean(vv))
    pct=100*np.mean(np.array(sim)<a.mean())
    print(f"  {proxy:8s}{a.mean()*100:>9.2f}{np.median(a)*100:>9.2f}{100*np.mean(a>0):>7.0f}%{tt:>7.2f}{len(a):>4d}{pct:>11.0f}%")
