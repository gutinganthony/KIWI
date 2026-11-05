import json,datetime as dt,statistics as st,bisect,sys
Y='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/yh/'
def load(f):
    d=json.load(open(Y+f+'.json'))['chart']['result'][0]
    out=[(dt.datetime.utcfromtimestamp(t).date(),c) for t,c in zip(d['timestamp'],d['indicators']['quote'][0]['close']) if c]
    # dedupe dates
    m={};[m.__setitem__(a,b) for a,b in out]; ks=sorted(m); return ks,[m[k] for k in ks]
def eday(y):
    d=dt.date(y,11,1)
    while d.weekday()!=0: d+=dt.timedelta(1)
    return d+dt.timedelta(1)
H={'1個月':21,'3個月':63,'6個月':126,'12個月':252}
BOTH={1954,1986,1994,2006,2014}
print('=== 期中選舉日收盤買進（選舉日或之前最後一個交易日）===')
for name in ('GSPC','IXIC','SOX','TWII'):
    D,C=load(name); N=len(C)
    rows=[]
    for y in range(1950,2023,4):
        e=eday(y)
        i=bisect.bisect_right(D,e)-1
        if i<1 or D[0]>e-dt.timedelta(30): continue
        r={k:(C[i+h]/C[i]-1)*100 for k,h in H.items() if i+h<N}
        rows.append((y,r))
    base={k:[(C[j+h]/C[j]-1)*100 for j in range(N-h)] for k,h in H.items()}
    print(f'\n## {name} 樣本 {len(rows)} 次（{rows[0][0]}–{rows[-1][0]}）')
    for k in H:
        v=[r[k] for y,r in rows if k in r]
        b=base[k]
        print(f' {k}: 勝率 {sum(x>0 for x in v)}/{len(v)}  中位 {st.median(v):+.1f}%  平均 {st.mean(v):+.1f}%  最差 {min(v):+.1f}% ｜ 隨便哪天 勝率 {sum(x>0 for x in b)/len(b)*100:.0f}% 中位 {st.median(b):+.1f}%')
    sub=[(y,r) for y,r in rows if y in BOTH]
    if sub:
        print('  反對黨選後掌握兩院：',' '.join(f"{y}:{'/'.join(('%+.0f'%r[k]) if k in r else 'NA' for k in H)}" for y,r in sub))
    print('  逐年(1m/3m/6m/12m)：',' '.join(f"{y}:{'/'.join(('%+.0f'%r[k]) if k in r else 'NA' for k in H)}" for y,r in rows[-8:]))
# 2026 current
print('\n=== 抄底：台股（Yahoo ^TWII 1997 起）大漲年第一次收盤跌到各門檻 ===')
D,C=load('TWII'); N=len(C)
# drop today's partial bar if date==2026-11-05
if D[-1]==dt.date(2026,11,5): D,C=D[:-1],C[:-1]; N-=1
hi=[max(C[max(0,i-251):i+1]) for i in range(N)]; dd=[(c/h-1)*100 for c,h in zip(C,hi)]
r12=[(C[i]/C[i-250]-1)*100 if i>=250 else None for i in range(N)]
print('最新',D[-1],C[-1],'距一年高 %.1f%%'%dd[-1],'一年漲 %+.0f%%'%r12[-1])
for th in (10,13,15,20):
    ev=[];arm=True
    for i in range(260,N):
        if dd[i]>=-1: arm=True
        if arm and dd[i]<=-th: ev.append(i); arm=False
    for lab,cond in (('一年漲>40%',lambda x:x and x>40),('一年漲>30%',lambda x:x and x>30),('全部',lambda x:True)):
        e=[i for i in ev if cond(r12[i])]
        if not e: print(f' 跌{th}% {lab}: 0'); continue
        s=[]
        for k,h in (('3個月',63),('6個月',126),('12個月',252)):
            v=[(C[i+h]/C[i]-1)*100 for i in e if i+h<N]
            if v: s.append(f"{k} {sum(x>0 for x in v)}/{len(v)} 中{st.median(v):+.1f}%")
        mdd=[(min(C[i:min(N,i+127)])/C[i]-1)*100 for i in e]
        print(f' 跌{th}% {lab} n={len(e)}：'+' | '.join(s)+f" ｜6個月內再跌 中位{st.median(mdd):.1f}% 最差{min(mdd):.1f}%")
        if lab!='全部': print('    ',', '.join(f"{D[i]}({r12[i]:+.0f}%,再跌{(min(C[i:min(N,i+127)])/C[i]-1)*100:.1f}%,3m{('%+.1f%%'%((C[i+63]/C[i]-1)*100)) if i+63<N else 'NA'})" for i in e))
