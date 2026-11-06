import json,datetime as dt,statistics as st
B='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/'
raw=json.load(open(B+'raw_0050.json'))['data']; div={r['date']:r['stock_and_cache_dividend'] for r in json.load(open(B+'div_0050.json'))['data']}
D=[r['date'] for r in raw]; C=[r['close'] for r in raw]
# total-return index with split detection
tr=[1.0]; splits=[]
for i in range(1,len(C)):
    r=C[i]/C[i-1]
    if r<0.4: splits.append((D[i],C[i-1],C[i])); r*= round(C[i-1]/C[i])   # split
    d=div.get(D[i],0)
    if d and r>=0.4: r=(C[i]+d)/C[i-1]
    tr.append(tr[-1]*r)
print('splits',splits)
# simulated 2x daily on TR, cost 1.5%/yr
lv=[1.0]
for i in range(1,len(tr)):
    lv.append(lv[-1]*(1+2*(tr[i]/tr[i-1]-1)-0.015/252))
T=json.load(open(B+'pxv.json'))['TAIEX']; TD=[r[0] for r in T]; TC=[r[4] for r in T]
add=json.load(open(B+'taiex_add.json'))['data']
for x in add:
    if x['date']>TD[-1]: TD.append(x['date']); TC.append(x['close'])
for d_,c_ in (('2026-11-02',44920.14),('2026-11-03',43307.54),('2026-11-04',42948.91),('2026-11-05',41574.72)):
    if d_>TD[-1]: TD.append(d_); TC.append(c_)
E=[('2000-03-15','政黨輪替'),('2000-10-03','網路泡沫'),('2004-05-20','319槍擊案'),('2008-09-19','金融海嘯'),('2011-12-21','歐債危機'),('2015-08-25','人民幣貶值'),('2020-03-19','新冠疫情'),('2022-07-13','升息熊市'),('2025-04-09','對等關稅')]
H=[('6個月',126),('12個月',252),('24個月',504)]
def ret(dates,vals,d0,h):
    i=next(k for k,x in enumerate(dates) if x>=d0)
    return None if i+h>=len(vals) else (vals[i+h]/vals[i]-1)*100
def mdd(dates,vals,d0,h=504):
    i=next(k for k,x in enumerate(dates) if x>=d0); w=vals[i:i+h]; m=min(w); j=w.index(m)
    return (m/vals[i]-1)*100, j
rows={'加權指數':[], '0050（含息）':[], '0050正2（模擬）':[]}
print('\n事件 | 加權 6/12/24 | 0050 含息 6/12/24 | 正2模擬 6/12/24 | 進場後最深再跌(加權/0050/正2) 幾天見底')
for d0,lab in E:
    t=[ret(TD,TC,d0,h) for _,h in H]; rows['加權指數'].append(t)
    if d0>='2003-07-01':
        a=[ret(D,tr,d0,h) for _,h in H]; l=[ret(D,lv,d0,h) for _,h in H]
        rows['0050（含息）'].append(a); rows['0050正2（模擬）'].append(l)
        m=(mdd(TD,TC,d0),mdd(D,tr,d0),mdd(D,lv,d0))
    else: a=l=[None]*3; m=(mdd(TD,TC,d0),(None,None),(None,None))
    f=lambda v:'/'.join('NA' if x is None else '%+.0f%%'%x for x in v)
    print(f"{d0} {lab} | {f(t)} | {f(a)} | {f(l)} | {m[0][0]:.1f}%/{'NA' if m[1][0] is None else '%.1f%%'%m[1][0]}/{'NA' if m[2][0] is None else '%.1f%%'%m[2][0]} 第{m[0][1]}天")
print('\n彙總（有資料的事件）')
for k,v in rows.items():
    for j,(n,_) in enumerate(H):
        x=[r[j] for r in v if r[j] is not None]
        if x: print(f" {k} {n}: 勝 {sum(y>0 for y in x)}/{len(x)} 中位 {st.median(x):+.1f}% 平均 {st.mean(x):+.1f}% 最差 {min(x):+.1f}%")
# check sim vs actual 00631L if available
print('\n現況：加權',TD[-1],TC[-1],'離 10/6 高點 %.1f%%'%((TC[-1]/49822.55-1)*100))
