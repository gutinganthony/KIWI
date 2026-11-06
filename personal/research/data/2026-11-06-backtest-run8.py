import json,datetime as dt,statistics as st
Y='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/yh/'
def load(f):
    r=json.load(open(Y+f+'.json'))['chart']['result'][0]; m={}
    for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']):
        if c: m[dt.datetime.utcfromtimestamp(t).date().isoformat()]=c
    return m
N=load('NDX'); S=load('GSPC'); V=load('VIX'); V3=load('VIX3M')
D=sorted(set(N)&set(V)); nc=[N[d] for d in D]; sc=[S.get(d) for d in D]; vx=[V[d] for d in D]; r3=[V[d]/V3[d] if d in V3 else None for d in D]
n=len(D); hi=[max(nc[max(0,i-251):i+1]) for i in range(n)]; dd=[(nc[i]/hi[i]-1)*100 for i in range(n)]
def first(cond,reset,start=0):
    ev=[];arm=True
    for i in range(start,n):
        if reset(i): arm=True
        if arm and cond(i): ev.append(i); arm=False
    return ev
def rep(name,ev):
    out=[f'\n[{name}] n={len(ev)}']
    for lab,h in (('3個月',63),('6個月',126),('12個月',252)):
        for nm,c in (('NDX',nc),('S&P',sc)):
            v=[(c[i+h]/c[i]-1)*100 for i in ev if i+h<n and c[i] and c[i+h]]
            if v: out.append(f'  {nm} {lab}: 勝 {sum(x>0 for x in v)}/{len(v)} 中位 {st.median(v):+.1f}% 最差 {min(v):+.1f}%')
    md=[(min(nc[i:i+127])/nc[i]-1)*100 for i in ev]
    out.append(f'  NDX 6個月內再跌 中位 {st.median(md):.1f}% 最差 {min(md):.1f}%')
    out.append('  '+' '.join(D[i] for i in ev)); print('\n'.join(out))
i3=next(i for i,x in enumerate(r3) if x)
rep('S1 VIX 第一次收≥40（曾<20）',first(lambda i:vx[i]>=40,lambda i:vx[i]<20))
rep('S2 VIX 第一次收≥35（曾<20）',first(lambda i:vx[i]>=35,lambda i:vx[i]<20))
rep('S3 VIX/VIX3M 第一次>1（倒掛，曾<0.9）2006+',first(lambda i:r3[i] and r3[i]>1,lambda i:r3[i] and r3[i]<0.9,i3))
# S4: after inversion >1.05, first day back <0.95
ev=[];armed=False
for i in range(i3,n):
    if r3[i] and r3[i]>1.05: armed=True
    if armed and r3[i] and r3[i]<0.95: ev.append(i); armed=False
rep('S4 倒掛（>1.05）後第一次回到<0.95（恐慌退燒）2006+',ev)
# S5 VIX >=35 then first close <25
ev=[];armed=False
for i in range(n):
    if vx[i]>=35: armed=True
    if armed and vx[i]<25: ev.append(i); armed=False
rep('S5 VIX 衝上35後第一次收回<25',ev)
rep('S6 NDX 第一次離高點跌20%',first(lambda i:dd[i]<=-20,lambda i:dd[i]>=-2,252))
# S7 rebound 10% from trough after >=15% drawdown
ev=[];arm=False;lo=None
for i in range(252,n):
    if dd[i]<=-15 and not arm: arm=True; lo=nc[i]
    if arm:
        lo=min(lo,nc[i])
        if nc[i]>=lo*1.10: ev.append(i); arm=False
    if dd[i]>=-2: arm=False
rep('S7 NDX 跌15%以上後，第一次離低點反彈10%',ev)
rep('S8 NDX 離高跌≥15% 且 VIX≥35 同時成立（第一次）',first(lambda i:dd[i]<=-15 and vx[i]>=35,lambda i:dd[i]>=-2,252))
print('\n現況',D[-1],'NDX離高 %.1f%%'%dd[-1],'VIX',vx[-1],'VIX/VIX3M',r3[-1])
