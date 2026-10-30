import json,statistics as st,datetime as dt
S='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt'
src=open(S+'/run3.py').read(); exec(src[src.index('def ema'):src.index('HS=[60')])
P=json.load(open(S+'/pxv.json'))
R=P['TAIEX']; last=R[-1][0]
add=[x for x in json.load(open(S+'/taiex_add.json'))['data'] if x['date']>last]
for x in add: R.append([x['date'],x['open'],x['max'],x['min'],x['close'],x['Trading_Volume']])
D=[r[0] for r in R]; hi=[r[2] for r in R]; lo=[r[3] for r in R]; cl=[r[4] for r in R]; N=len(cl)
ma250=sma(cl,250); ma20=sma(cl,20); ma60=sma(cl,60)
hi252=[max(cl[max(0,i-251):i+1]) for i in range(N)]; dd=[(c/h-1)*100 for c,h in zip(cl,hi252)]
ret12=[(cl[i]/cl[i-250]-1)*100 if i>=250 else None for i in range(N)]
print('最新',D[-1],cl[-1],'距一年高%.2f'%dd[-1],'一年高',hi252[-1],'年線%.0f'%ma250[-1],'年線乖離%+.1f%%'%((cl[-1]/ma250[-1]-1)*100),'一年漲幅%+.0f%%'%ret12[-1],'20日線%.0f'%ma20[-1],'季線%.0f'%ma60[-1])
print('-10%位置',round(hi252[-1]*0.9,2),'-15%',round(hi252[-1]*0.85,2))
# weekly WT
wk=[dt.date.fromisoformat(d).isocalendar()[:2] for d in D]; W=[];cur=None
for i in range(N):
    if cur and cur['k']==wk[i]: cur['h']=max(cur['h'],hi[i]); cur['l']=min(cur['l'],lo[i]); cur['c']=cl[i]; cur['d']=D[i]
    else:
        if cur: W.append(cur)
        cur={'k':wk[i],'h':hi[i],'l':lo[i],'c':cl[i],'d':D[i]}
W.append(cur); v1,v2=wt([w['h'] for w in W],[w['l'] for w in W],[w['c'] for w in W])
for j in range(-6,0): print('週',W[j]['d'],'WT1 %.1f WT2 %.1f'%(v1[j],v2[j]))
# events: first -10% with ret12>30
ev=[];arm=True
for i in range(260,N):
    if dd[i]>=-1: arm=True
    if arm and dd[i]<=-10: ev.append(i); arm=False
print('\n大漲後第一次跌一成（過去一年漲>30%）')
for i in ev:
    if ret12[i] and ret12[i]>30:
        r=lambda h:'%+.1f%%'%((cl[i+h]/cl[i]-1)*100) if i+h<N else 'NA'
        mn=min(cl[i:i+121]); 
        # did month close break annual line within 6m?
        print(D[i],'一年漲%+.0f%%'%ret12[i],'年線乖離%+.0f%%'%((cl[i]/ma250[i]-1)*100),'3m',r(60),'6m',r(120),'12m',r(250),'6個月內再跌%.1f%%'%((mn/cl[i]-1)*100))
# first time -9% with ret12>40 (where we are)
ev9=[];arm=True
for i in range(260,N):
    if dd[i]>=-1: arm=True
    if arm and dd[i]<=-9: ev9.append(i); arm=False
print('\n第一次跌離高點9%且一年漲>40%')
for i in ev9:
    if ret12[i] and ret12[i]>40:
        r=lambda h:'%+.1f%%'%((cl[i+h]/cl[i]-1)*100) if i+h<N else 'NA'
        mn=min(cl[i:i+121]); reached10=any(dd[j]<=-10 for j in range(i,min(N,i+120)))
        print(D[i],'一年漲%+.0f%%'%ret12[i],'3m',r(60),'6m',r(120),'12m',r(250),'6個月內再跌%.1f%%'%((mn/cl[i]-1)*100),'之後跌到一成' if reached10 else '沒跌到一成')
