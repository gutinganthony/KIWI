import csv, math, random
import numpy as np
from events import EVENTS

TICS=["GOOGL","MSFT","META","NVDA","QQQ"]
def load(t):
    rows=list(csv.DictReader(open(f"px/{t}.csv")))
    d=[r["date"] for r in rows]; p=np.array([float(r["adjclose"]) for r in rows])
    v=np.array([float(r["volume"] or 0) for r in rows])
    r=np.full(len(p),np.nan); r[1:]=np.log(p[1:]/p[:-1])
    return d,{x:i for i,x in enumerate(d)},r,v
PX={t:load(t) for t in TICS}

# 財報日代理：每個日曆季，成交量最高的那一天。只用成交量，不用報酬 ⇒ 不會循環論證
EARN={}
for t in TICS:
    dates,idx,r,v=PX[t]
    byq={}
    for i,d in enumerate(dates):
        y,m=int(d[:4]),int(d[5:7]); q=(y,(m-1)//3)
        byq.setdefault(q,[]).append(i)
    EARN[t]=set()
    for q,ii in byq.items():
        if len(ii)<20: continue
        EARN[t].add(max(ii,key=lambda i:v[i]))

WINDOWS={"[-20,-1]":(-20,-1),"[-5,-1]":(-5,-1),"[0]":(0,0),"[0,+1]":(0,1),
         "[+1,+5]":(1,5),"[+1,+10]":(1,10),"[+1,+20]":(1,20)}

def car(tic,t0,windows,allow_short=False):
    dates,idx,r,v=PX[tic]; bd,bi,rb,_=PX["QQQ"]
    if t0<260: return None
    est=range(t0-250,t0-30)
    xs=np.array([rb[bi[dates[i]]] for i in est if dates[i] in bi])
    ys=np.array([r[i] for i in est if dates[i] in bi])
    ok=~(np.isnan(xs)|np.isnan(ys)); xs,ys=xs[ok],ys[ok]
    X=np.column_stack([np.ones(len(xs)),xs]); beta,*_=np.linalg.lstsq(X,ys,rcond=None)
    def ar(i):
        if i>=len(dates) or dates[i] not in bi or np.isnan(r[i]): return None
        return r[i]-(beta[0]+beta[1]*rb[bi[dates[i]]])
    out={}
    for lab,(a,b) in windows.items():
        vals=[ar(t0+k) for k in range(a,b+1)]
        got=[x for x in vals if x is not None]
        if not allow_short and any(x is None for x in vals): out[lab]=None
        elif len(got)==0: out[lab]=None
        else: out[lab]=sum(got)
    return out

def hits_earnings(tic,t0,a,b):
    return any((t0+k) in EARN[tic] for k in range(a,b+1))

def t0_of(tic,date):
    dates,_,_,_=PX[tic]
    for i,dd in enumerate(dates):
        if dd>=date: return i
    return None

res=[]
for date,tic,name,src,sign in EVENTS:
    i=t0_of(tic,date)
    if i is None: continue
    c=car(tic,i,WINDOWS,allow_short=True)
    if c: res.append(dict(date=date,tic=tic,name=name,src=src,sign=sign,t0=i,car=c))
pos=[x for x in res if x["sign"]>0]

print("="*104)
print("【清理後】用成交量尖峰推定的財報日，標出每個視窗是否被財報污染")
print(f"{'日期':11s}{'標的':6s}{'事件':26s}" + "".join(f"{w:>11s}" for w in ["[0,+1]","[+1,+10]","[+1,+20]"]))
for x in pos:
    marks=[]
    for w,(a,b) in [("[0,+1]",(0,1)),("[+1,+10]",(1,10)),("[+1,+20]",(1,20))]:
        c=x["car"][w]
        s="  n/a" if c is None else f"{c*100:6.2f}"
        s+="⚠️" if hits_earnings(x["tic"],x["t0"],a,b) else "  "
        marks.append(s)
    print(f"{x['date']:11s}{x['tic']:6s}{x['name'][:24]:26s}" + "".join(f"{m:>11s}" for m in marks))

def stats(sel,lab,clean=False):
    n_by={}
    print(f"\n── {lab} ──")
    print(f"  {'視窗':>10s}{'平均CAR':>9s}{'中位數':>8s}{'勝率':>7s}{'t值':>7s}{'n':>4s}")
    for w,(a,b) in WINDOWS.items():
        v=[]
        for x in sel:
            if x["car"][w] is None: continue
            if clean and hits_earnings(x["tic"],x["t0"],a,b): continue
            v.append(x["car"][w])
        if len(v)<3: print(f"  {w:>10s}{'不足':>9s}{'':>8s}{'':>7s}{'':>7s}{len(v):>4d}"); continue
        v=np.array(v); t=v.mean()/(v.std(ddof=1)/math.sqrt(len(v)))
        print(f"  {w:>10s}{v.mean()*100:>9.2f}{np.median(v)*100:>8.2f}{100*np.mean(v>0):>6.0f}%{t:>7.2f}{len(v):>4d}")
        n_by[w]=len(v)
    return n_by

stats(pos,"全部正面事件（未清理）")
nb=stats(pos,"⭐ 排除該視窗撞到財報的事件",clean=True)

print("\n"+"="*104)
print("【對照組】同股票、同事件數、同樣排除撞財報的隨機日期 × 2000 次")
random.seed(7)
tickers=[x["tic"] for x in pos]
sim={w:[] for w in WINDOWS}
for _ in range(2000):
    vals={w:[] for w in WINDOWS}
    for tic in tickers:
        dates,_,_,_=PX[tic]
        i=random.randint(270,len(dates)-25)
        c=car(tic,i,WINDOWS)
        if not c: continue
        for w,(a,b) in WINDOWS.items():
            if c[w] is not None and not hits_earnings(tic,i,a,b): vals[w].append(c[w])
    for w in WINDOWS:
        if len(vals[w])>=3: sim[w].append(np.mean(vals[w]))
print(f"  {'視窗':>10s}{'實際':>9s}{'隨機均':>9s}{'隨機5%':>9s}{'隨機95%':>9s}{'百分位':>8s}{'判定':>10s}")
for w,(a,b) in WINDOWS.items():
    v=[x["car"][w] for x in pos if x["car"][w] is not None and not hits_earnings(x["tic"],x["t0"],a,b)]
    if len(v)<3: continue
    act=np.mean(v); s=np.array(sim[w]); pct=100*np.mean(s<act)
    verdict="✅有效果" if (pct<5 or pct>95) else "—無差別"
    print(f"  {w:>10s}{act*100:>9.2f}{s.mean()*100:>9.2f}{np.percentile(s,5)*100:>9.2f}{np.percentile(s,95)*100:>9.2f}{pct:>7.0f}%{verdict:>10s}")
