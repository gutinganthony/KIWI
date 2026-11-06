import json,datetime as dt,statistics as st,bisect
B='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/'
def yload(f):
    r=json.load(open(B+'yh/'+f+'.json'))['chart']['result'][0]; m={}
    for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']):
        if c: m[dt.datetime.utcfromtimestamp(t).date().isoformat()]=c
    k=sorted(m); return k,[m[x] for x in k]
SD,SC=yload('SOX'); TD,TC=yload('TWII')
# 0050 TR
raw=json.load(open(B+'raw_0050.json'))['data']; div={r['date']:r['stock_and_cache_dividend'] for r in json.load(open(B+'div_0050.json'))['data']}
ED=[r['date'] for r in raw]; EC=[r['close'] for r in raw]; tr=[1.0]
for i in range(1,len(EC)):
    r=EC[i]/EC[i-1]
    if r<0.4: r*=round(EC[i-1]/EC[i])
    elif div.get(ED[i]): r=(EC[i]+div[ED[i]])/EC[i-1]
    tr.append(tr[-1]*r)
n=len(SC); hi=[max(SC[max(0,i-251):i+1]) for i in range(n)]; dd=[(SC[i]/hi[i]-1)*100 for i in range(n)]
def nxt(D,d): return bisect.bisect_right(D,d)  # first Taiwan session after US date
def rep(name,ev):
    print(f'\n[{name}] n={len(ev)}')
    for lab,(D,C) in (('加權',(TD,TC)),('0050含息',(ED,tr)),('費半',(SD,SC))):
        rows={6:[],12:[],24:[]}; md=[]
        for d in ev:
            i=nxt(D,d) if lab!='費半' else D.index(d)
            if d<D[0] or i>=len(C): continue
            for m,h in ((6,126),(12,252),(24,504)):
                if i+h<len(C): rows[m].append((C[i+h]/C[i]-1)*100)
            md.append((min(C[i:i+253])/C[i]-1)*100)
        s=' | '.join(f"{m}個月 {sum(x>0 for x in v)}/{len(v)} 中{st.median(v):+.0f}%" for m,v in rows.items() if v)
        if md: print(f'  {lab}: {s} ｜一年內再跌 中位{st.median(md):.0f}% 最差{min(md):.0f}%')
    print('  ',' '.join(ev))
def first(cond,reset,start=252):
    ev=[];arm=True
    for i in range(start,n):
        if reset(i): arm=True
        if arm and cond(i): ev.append(SD[i]); arm=False
    return ev
for th in (20,30,40):
    rep(f'費半第一次收盤離一年高點跌{th}%',first(lambda i,th=th:dd[i]<=-th,lambda i:dd[i]>=-5))
ev=[];last=-99
for i in range(1,n):
    r=SC[i]/SC[i-1]-1
    if r<=-0.08 and i-last>20: ev.append(SD[i])
    if r<=-0.08: last=i
rep('費半單日跌≥8%（20天內第一次）',ev)
# SOX -30% then rebound 15% from low (confirmation)
ev=[];arm=False;lo=None
for i in range(252,n):
    if dd[i]<=-30 and not arm: arm=True; lo=SC[i]
    if arm:
        lo=min(lo,SC[i])
        if SC[i]>=lo*1.15: ev.append(SD[i]); arm=False; 
    if dd[i]>=-5: arm=False
rep('費半跌三成以上後，第一次離低點反彈15%',ev)
print('\n現況 費半',SD[-1],SC[-1],'離一年高 %.1f%%'%dd[-1],'一年高',max(SC[-252:]))
