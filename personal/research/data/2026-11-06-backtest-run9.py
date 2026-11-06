import json,datetime as dt,statistics as st
Y='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/yh/'
def load(f):
    r=json.load(open(Y+f+'.json'))['chart']['result'][0]; m={}
    for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']):
        if c: m[dt.datetime.utcfromtimestamp(t).date().isoformat()]=c
    return m
N=load('NDX'); V=load('VIX'); D=sorted(set(N)&set(V)); nc=[N[d] for d in D]; vx=[V[d] for d in D]; n=len(D)
lv=[1.0]
for i in range(1,n): lv.append(lv[-1]*(1+2*(nc[i]/nc[i-1]-1)-0.01/252))
def first(cond,reset):
    ev=[];arm=True
    for i in range(n):
        if reset(i): arm=True
        if arm and cond(i): ev.append(i); arm=False
    return ev
def tab(name,ev):
    print(f'\n[{name}] 事件 | NDX 6/12/24個月 | 2倍模擬 6/12/24 | 兩年內最深再跌 NDX/2倍')
    agg={k:[] for k in ('n6','n12','n24','l6','l12','l24')}
    for i in ev:
        r=lambda c,h:(c[i+h]/c[i]-1)*100 if i+h<n else None
        vals=[r(nc,126),r(nc,252),r(nc,504),r(lv,126),r(lv,252),r(lv,504)]
        for k,v in zip(agg,vals):
            if v is not None: agg[k].append(v)
        md=(min(nc[i:i+505])/nc[i]-1)*100; ml=(min(lv[i:i+505])/lv[i]-1)*100
        f=lambda v:'NA' if v is None else '%+.0f%%'%v
        print(f" {D[i]} VIX {vx[i]:.0f} | {'/'.join(map(f,vals[:3]))} | {'/'.join(map(f,vals[3:]))} | {md:.0f}%/{ml:.0f}%")
    for k,v in agg.items(): print(f'  {k}: 勝 {sum(x>0 for x in v)}/{len(v)} 中位 {st.median(v):+.0f}% 最差 {min(v):+.0f}%')
tab('VIX 第一次收≥40',first(lambda i:vx[i]>=40,lambda i:vx[i]<20))
tab('VIX 第一次收≥35',first(lambda i:vx[i]>=35,lambda i:vx[i]<20))
ev=[];armed=False
for i in range(n):
    if vx[i]>=35: armed=True
    if armed and vx[i]<25: ev.append(i); armed=False
tab('VIX 衝上35後第一次收回<25',ev)
