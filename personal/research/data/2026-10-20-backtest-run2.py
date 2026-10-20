import json,statistics as st,bisect,datetime as dt
S='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt'
P=json.load(open(S+'/pxv.json')); V=dict(json.load(open(S+'/vix.json')))
def ema(x,n):
    k=2/(n+1);o=[];e=None
    for v in x: e=v if e is None else e+k*(v-e); o.append(e)
    return o
def sma(x,n): 
    o=[];s=0
    for i,v in enumerate(x):
        s+=v
        if i>=n: s-=x[i-n]
        o.append(s/n if i>=n-1 else None)
    return o
def rsi(cl,n=14):
    g=[0]+[max(cl[i]-cl[i-1],0) for i in range(1,len(cl))]; l=[0]+[max(cl[i-1]-cl[i],0) for i in range(1,len(cl))]
    ag=ema(g,2*n-1); al=ema(l,2*n-1)  # Wilder approx
    return [100-100/(1+a/b) if b else 100 for a,b in zip(ag,al)]
def wt(hi,lo,cl):
    h=[(a+b+c)/3 for a,b,c in zip(hi,lo,cl)]; esa=ema(h,10); d=ema([abs(a-b) for a,b in zip(h,esa)],10)
    ci=[(a-b)/(0.015*c) if c else 0 for a,b,c in zip(h,esa,d)]; w1=ema(ci,21); w2=[st.mean(w1[max(0,i-3):i+1]) for i in range(len(w1))]; return w1,w2
HS=[20,60,120,250]
RES={}
def stats(cl,ev,hs=HS):
    out={}
    for h in hs:
        v=[(cl[i+h]/cl[i]-1)*100 for i in ev if i+h<len(cl)]
        if v: out[h]=(len(v),sum(x>0 for x in v)/len(v)*100,st.mean(v),st.median(v),min(v))
    return out
def fmt(o): return ' | '.join(f"{h}日 n{n} 勝{w:.0f}% 均{m:+.1f}% 中{md:+.1f}% 最差{mn:+.1f}%" for h,(n,w,m,md,mn) in o.items())
for name in ("TAIEX","SPY","QQQ","SOXX"):
    R=P[name]; D=[r[0] for r in R]; op=[r[1] for r in R]; hi=[r[2] for r in R]; lo=[r[3] for r in R]; cl=[r[4] for r in R]; vol=[r[5] for r in R]
    N=len(cl); ma20=sma(cl,20); ma50=sma(cl,50); ma250=sma(cl,250); r14=rsi(cl)
    hi252=[max(cl[max(0,i-251):i+1]) for i in range(N)]; dd=[(c/h-1)*100 for c,h in zip(cl,hi252)]
    ret12=[(cl[i]/cl[i-250]-1)*100 if i>=250 else None for i in range(N)]
    vx=[V.get(d) for d in D]
    base=list(range(260,N))
    print(f"\n################ {name}  最新 {D[-1]} 收 {cl[-1]}  距一年高 {dd[-1]:.1f}%  RSI {r14[-1]:.0f}  年線乖離 {(cl[-1]/ma250[-1]-1)*100:+.1f}%  過去一年漲幅 {ret12[-1]:+.0f}%")
    print(" 基準:",fmt(stats(cl,base)))
    def first_cross(cond,reset):
        ev=[];arm=True
        for i in range(260,N):
            if reset(i): arm=True
            if arm and cond(i): ev.append(i); arm=False
        return ev
    sig={}
    for th in (5,10,15,20): sig[f'跌破一年高 −{th}%']=first_cross(lambda i,th=th:dd[i]<=-th, lambda i:dd[i]>=-1)
    sig['跌10%且過去一年漲>40%']=[i for i in sig['跌破一年高 −10%'] if ret12[i] and ret12[i]>40]
    sig['跌10%且過去一年漲≤40%']=[i for i in sig['跌破一年高 −10%'] if ret12[i] is not None and ret12[i]<=40]
    big=3 if name in('TAIEX','SOXX') else 2.5
    sig[f'單日跌≥{big}%']=[i for i in range(260,N) if (cl[i]/cl[i-1]-1)*100<=-big]
    sig['RSI14首次<30']=first_cross(lambda i:r14[i]<30, lambda i:r14[i]>50)
    sig['收盤低於50日線8%']=first_cross(lambda i:cl[i]<ma50[i]*0.92, lambda i:cl[i]>ma50[i])
    sig['連跌5天以上']=first_cross(lambda i:all(cl[j]<cl[j-1] for j in range(i-4,i+1)), lambda i:cl[i]>cl[i-1])
    sig['VIX首次≥30']=first_cross(lambda i:vx[i] is not None and vx[i]>=30, lambda i:vx[i] is not None and vx[i]<20)
    sig['VIX首次≥25']=first_cross(lambda i:vx[i] is not None and vx[i]>=25, lambda i:vx[i] is not None and vx[i]<18)
    # confirmation signals per episode (episode: dd<=-8; trough tracking)
    w1,w2=wt(hi,lo,cl)
    # weekly WT mapped to last day of week
    wk=[dt.date.fromisoformat(d).isocalendar()[:2] for d in D]
    W=[];cur=None
    for i in range(N):
        if cur and cur['k']==wk[i]: cur.update(h=max(cur['h'],hi[i]),l=min(cur['l'],lo[i]),c=cl[i],i=i)
        else:
            if cur: W.append(cur)
            cur=dict(k=wk[i],h=hi[i],l=lo[i],c=cl[i],i=i)
    W.append(cur); v1,v2=wt([w['h'] for w in W],[w['l'] for w in W],[w['c'] for w in W])
    wcross=set(W[k]['i'] for k in range(1,len(W)) if v1[k-1]<=v2[k-1] and v1[k]>v2[k] and v1[k]<0)
    conf={k:[] for k in ('收復20日線','收復50日線','跟進日(第4天後漲≥1.5%且量增)','週線WT黃金交叉','離低點反彈5%','離低點反彈10%','VIX回落<20')}
    prem={k:[] for k in conf}; fail={k:[] for k in conf}
    i=260
    while i<N:
        if dd[i]<=-8:
            s=i; tr=i; got={}
            j=i
            while j<N and dd[j]<-1:
                if cl[j]<cl[tr]: tr=j
                def put(k):
                    if k not in got: got[k]=j
                if cl[j]>ma20[j] and j>tr: put('收復20日線')
                if cl[j]>ma50[j] and j>tr: put('收復50日線')
                if j-tr>=3 and (cl[j]/cl[j-1]-1)*100>=1.5 and vol[j]>vol[j-1]: put('跟進日(第4天後漲≥1.5%且量增)')
                if j in wcross and j>=s: put('週線WT黃金交叉')
                if cl[j]>=cl[tr]*1.05 and j>tr: put('離低點反彈5%')
                if cl[j]>=cl[tr]*1.10 and j>tr: put('離低點反彈10%')
                if vx[j] is not None and vx[j]<20 and max([x for x in vx[s:j+1] if x] or [0])>=25 and j>tr: put('VIX回落<20')
                j+=1
            # trough of whole episode (until recovery)
            ep_end=j; ep_tr=min(range(s,min(ep_end,N)),key=lambda x:cl[x])
            for k,e in got.items():
                conf[k].append(e); prem[k].append((cl[e]/cl[ep_tr]-1)*100)
                fail[k].append(min(cl[e:min(e+61,N)])<cl[min(range(s,e+1),key=lambda x:cl[x])])
            i=ep_end+1
        else: i+=1
    rows=[]
    for k,ev in sig.items(): rows.append(('恐慌當下',k,ev))
    for k,ev in conf.items(): rows.append(('確認訊號',k,ev))
    for typ,k,ev in rows:
        o=stats(cl,ev); extra=''
        if typ=='確認訊號' and prem[k]:
            extra=f" ｜買點比整段最低點貴 中位{st.median(prem[k]):.1f}% ｜60日內再破底 {sum(fail[k])}/{len(fail[k])}"
        print(f" [{typ}] {k} (n={len(ev)}) 最近:{[D[x] for x in ev[-2:]]}\n     {fmt(o)}{extra}")
    print(f" 現況：日WT {w1[-1]:.0f}/{w2[-1]:.0f} 週WT {v1[-1]:.0f}/{v2[-1]:.0f} 20日線{ma20[-1]:.0f} 50日線{ma50[-1]:.0f} VIX {vx[-1]}")
