import json,datetime as dt,bisect,statistics as st
Y='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/yh/'
def L(f):
    r=json.load(open(Y+f+'.json'))['chart']['result'][0]; m={}
    for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']):
        if c: m[dt.datetime.utcfromtimestamp(t).date().isoformat()]=c
    k=sorted(m); return k,[m[x] for x in k]
ND,NC=L('NDX'); SD,SC=L('GSPC')
E=[('1999-05-04','高盛'),('1999-11-10','UPS'),('2000-04-27','AT&T Wireless'),('2001-06-13','卡夫食品'),('2007-06-22','黑石'),('2008-03-19','Visa'),('2010-11-18','通用汽車'),('2012-05-18','Facebook'),('2014-09-19','阿里巴巴'),('2019-05-10','Uber'),('2020-09-16','Snowflake'),('2020-12-10','Airbnb'),('2021-03-11','Coupang'),('2021-11-10','Rivian'),('2023-09-14','Arm')]
def fw(D,C,d,h):
    i=bisect.bisect_left(D,d); return None if i+h>=len(C) else (C[i+h]/C[i-1]-1)*100
def mdd(D,C,d,h=252):
    i=bisect.bisect_left(D,d); pk=C[i-1]; m=0
    for x in C[i-1:i+h]: pk=max(pk,x); m=min(m,x/pk-1)
    return m*100
def toppos(D,C,d):  # days from IPO to NDX peak within ±1y window: was IPO within 3 months of a 1y high before a 20% drop?
    i=bisect.bisect_left(D,d); w=C[i:i+253]; j=w.index(max(w)); dd=min(C[i+j:i+j+253])/max(w)-1
    return j, dd*100
f=lambda x:'NA' if x is None else '%+.0f%%'%x
rows=[]
print('日期|公司|那指100 6/12/24月|標普 12月|之後12月那指最大回撤|IPO後那指一年內高點出現在第幾天、高點後跌幅')
for d,n in E:
    a=[fw(ND,NC,d,h) for h in (126,252,504)]; s=fw(SD,SC,d,252); j,dd=toppos(ND,NC,d)
    rows.append(a); print(f"{d}|{n}|{'/'.join(map(f,a))}|{f(s)}|{mdd(ND,NC,d):.0f}%|第{j}天，之後跌{dd:.0f}%")
for k,lab in enumerate(('6月','12月','24月')):
    v=[r[k] for r in rows if r[k] is not None]; print(lab,'勝',sum(x>0 for x in v),'/',len(v),'中位 %+.1f%%'%st.median(v))
# baseline: NDX any day 12m win rate since 1999
i0=bisect.bisect_left(ND,'1999-01-01'); b=[(NC[i+252]/NC[i]-1) for i in range(i0,len(NC)-252)]; print('那指100 任一天 12月 勝率 %.0f%% 中位 %+.1f%%'%(sum(x>0 for x in b)/len(b)*100,st.median(b)*100))
