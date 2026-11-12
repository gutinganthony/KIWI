import json,datetime as dt,statistics as st
P='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/sc/'
N={'2317.TW':'鴻海','2382.TW':'廣達','3231.TW':'緯創','6669.TW':'緯穎','2449.TW':'京元電','2330.TW':'台積電','3711.TW':'日月光投控','2454.TW':'聯發科','2408.TW':'南亞科','2344.TW':'華邦電','2308.TW':'台達電','3017.TW':'奇鋐','2383.TW':'台光電','3037.TW':'欣興','2376.TW':'技嘉','3443.TW':'創意','3661.TW':'世芯-KY','2357.TW':'華碩','4938.TW':'和碩','2356.TW':'英業達',
   'AMD':'AMD','AVGO':'博通','MU':'美光','TSM':'台積電ADR','DELL':'戴爾','SMCI':'美超微','CRWV':'CoreWeave','ORCL':'甲骨文','MRVL':'Marvell','GOOGL':'Alphabet','MSFT':'微軟','AMZN':'亞馬遜','META':'Meta','ANET':'Arista','VRT':'Vertiv'}
def L(s):
    r=json.load(open(P+s+'.json'))['chart']['result'][0]; m={}
    for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']):
        if c: m[dt.datetime.utcfromtimestamp(t).date().isoformat()]=c
    return m
nv=L('NVDA'); tw=L('TWII'); qq=L('QQQ')
def wk(m):  # weekly closes (ISO week, last close)
    w={}
    for d in sorted(m): w[dt.date.fromisoformat(d).isocalendar()[:2]]=m[d]
    return w
def corr(a,b):
    ks=sorted(set(a)&set(b)); ks=[k for k in ks if k>=(2025,45) and k<(2026,45)]
    ra=[a[ks[i]]/a[ks[i-1]]-1 for i in range(1,len(ks))]; rb=[b[ks[i]]/b[ks[i-1]]-1 for i in range(1,len(ks))]
    ma,mb=st.mean(ra),st.mean(rb); c=sum((x-ma)*(y-mb) for x,y in zip(ra,rb)); va=sum((x-ma)**2 for x in ra); vb=sum((y-mb)**2 for y in rb)
    return c/(va*vb)**0.5, c/vb   # corr, beta to NVDA
def ret(m,a,b):
    ks=sorted(m); x=max(k for k in ks if k<=a); y=max(k for k in ks if k<=b); return (m[y]/m[x]-1)*100,y
W=wk(nv); out=[]
nvr,nvd=ret(nv,'2026-11-06','2026-11-12'); twr,_=ret(tw,'2026-11-06','2026-11-12'); qqr,_=ret(qq,'2026-11-06','2026-11-12')
print('NVDA 11/6→%s %+.1f%%  加權 %+.1f%%  QQQ %+.1f%%'%(nvd,nvr,twr,qqr))
for s,n in N.items():
    m=L(s); c,b=corr(wk(m),W); r,d=ret(m,'2026-11-06','2026-11-12'); bench=twr if s.endswith('.TW') else qqr
    out.append((n,s,c,b,r,r-bench,d))
out.sort(key=lambda x:-x[2])
print('公司|代號|與輝達週報酬相關係數(近一年)|11/6→最新 報酬|相對大盤')
for n,s,c,b,r,rel,d in out: print(f'{n}|{s}|{c:.2f}|{r:+.1f}%|{rel:+.1f}% ({d})')
tw_=[x for x in out if x[1].endswith('.TW')]; us_=[x for x in out if not x[1].endswith('.TW')]
for nm,g in (('台股',tw_),('美股',us_)):
    xs=[x[2] for x in g]; ys=[x[5] for x in g]; mx,my=st.mean(xs),st.mean(ys)
    r=sum((a-mx)*(b-my) for a,b in zip(xs,ys))/(sum((a-mx)**2 for a in xs)*sum((b-my)**2 for b in ys))**0.5
    print(nm,'相關係數 vs 相對報酬 的相關',round(r,2))
