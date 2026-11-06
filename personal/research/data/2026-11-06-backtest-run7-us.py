import json,datetime as dt,statistics as st
Y='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/yh/'
def load(f):
    r=json.load(open(Y+f+'.json'))['chart']['result'][0]; m={}
    for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']):
        if c: m[dt.datetime.utcfromtimestamp(t).date().isoformat()]=c
    k=sorted(m); return k,[m[x] for x in k]
H=[('3個月',63),('6個月',126),('12個月',252)]
def summ(name,D,C,ev,extra=''):
    print(f'\n[{name}] n={len(ev)} {extra}')
    for lab,h in H:
        v=[(C[i+h]/C[i]-1)*100 for i in ev if i+h<len(C)]
        if v: print(f'  {lab}: 勝 {sum(x>0 for x in v)}/{len(v)} 中位 {st.median(v):+.1f}% 最差 {min(v):+.1f}%')
    md=[(min(C[i:i+127])/C[i]-1)*100 for i in ev]
    print(f'  6個月內再跌 中位 {st.median(md):.1f}% 最差 {min(md):.1f}%')
    print('  ',' '.join(D[i] for i in ev))
ND,NC=load('NDX'); SD,SC=load('GSPC'); VD,VC=load('VIX'); vix=dict(zip(VD,VC))
# 1. NDX single-day drop >=6%, first in 20 days
ev=[];last=-99
for i in range(1,len(NC)):
    if (NC[i]/NC[i-1]-1)<=-0.06 and i-last>20: ev.append(i)
    if (NC[i]/NC[i-1]-1)<=-0.06: last=i
summ('那斯達克100 單日跌≥6%（20天內第一次）',ND,NC,ev)
# show path for each: drawdown from 1y high at event and later bottom
for i in ev:
    hi=max(NC[max(0,i-251):i+1]); w=NC[i:i+253]; lo=min(w)
    print('   ',ND[i],'當時離高 %.0f%%'%((NC[i]/hi-1)*100),'之後一年內最低再跌 %.0f%%'%((lo/NC[i]-1)*100),'12m %s'%('%+.0f%%'%((NC[i+252]/NC[i]-1)*100) if i+252<len(NC) else 'NA'))
# 2. S&P single day <= -4% first in 20 days
ev=[];last=-99
for i in range(1,len(SC)):
    if SD[i]<'1950': continue
    if (SC[i]/SC[i-1]-1)<=-0.04 and i-last>20: ev.append(i)
    if (SC[i]/SC[i-1]-1)<=-0.04: last=i
summ('標普500 單日跌≥4%（20天內第一次，1950起）',SD,SC,ev)
# 3. VIX first close >=30 after <20 ; buy S&P
idx={d:i for i,d in enumerate(SD)}
for th,reset in ((30,20),(40,20)):
    ev=[];arm=True
    for d in VD:
        v=vix[d]
        if v<reset: arm=True
        if arm and v>=th and d in idx: ev.append(idx[d]); arm=False
    summ(f'VIX 第一次收≥{th}（之前曾<{reset}）買標普',SD,SC,ev)
# 4. NDX first close -20% from 1y high
for th in (10,20,30):
    ev=[];arm=True
    for i in range(252,len(NC)):
        hi=max(NC[i-251:i+1]); dd=(NC[i]/hi-1)*100
        if dd>=-2: arm=True
        if arm and dd<=-th: ev.append(i); arm=False
    summ(f'那斯達克100 第一次收盤離高點跌{th}%',ND,NC,ev)
hi=max(NC[-252:]); print('\n現況 NDX',ND[-1],NC[-1],'離一年高 %.1f%%'%((NC[-1]/hi-1)*100)); hi=max(SC[-252:]); print('S&P',SD[-1],SC[-1],'離一年高 %.1f%%'%((SC[-1]/hi-1)*100)); print('VIX',VD[-1],VC[-1])
