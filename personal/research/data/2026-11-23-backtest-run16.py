"""run16（11/23）：(1) 1998 vs 2000 vs 2022 vs 2026 路徑對照（台股加權、那斯達克100），(2) 「這種跌法」買進持有 1/2/3/5 年與至今。
資料：Yahoo（^TWII 1997-07 起、^NDX 1985 起、^GSPC 1950 起、^VIX 1990 起），價格指數不含息；台股 11/19、11/20 以證交所收盤補。"""
import json,datetime as dt,statistics as st
P='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/r16/'
def L(f):
    r=json.load(open(P+f))['chart']['result'][0]
    return [(dt.datetime.utcfromtimestamp(t).date(),c) for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']) if c]
tw=[x for x in L('twii_long.json') if x[0]<dt.date(2026,11,19)]+[(dt.date(2026,11,19),38426.89),(dt.date(2026,11,20),36033.29)]
nd=L('NDX.json'); sp=L('GSPC.json'); vx=L('VIX.json')
def peak(ser,a,b):
    w=[(i,x) for i,x in enumerate(ser) if a<=x[0]<=b]; return max(w,key=lambda t:t[1][1])[0]
def path(ser,i0,n=520):
    p0=ser[i0][1]; return [(k,(ser[i0+k][1]/p0-1)*100) for k in range(0,min(n,len(ser)-i0))]
EP={'台股':(tw,{'1998':('1998-01-01','1998-06-30'),'2000':('2000-01-01','2000-04-30'),'2008':('2007-09-01','2007-12-31'),'2022':('2021-12-01','2022-02-28'),'2026':('2026-09-01','2026-11-20')}),
    '那斯達克100':(nd,{'1998':('1998-06-01','1998-08-31'),'2000':('2000-02-01','2000-04-30'),'2022':('2021-10-01','2022-01-31'),'2026':('2026-09-01','2026-11-20')})}
out={}
for mk,(ser,eps) in EP.items():
    print(f'\n=== {mk}：從高點起算的路徑 ===')
    now_i=peak(ser,*[dt.date.fromisoformat(x) for x in eps['2026']]); now_n=len(ser)-1-now_i; now_dd=(ser[-1][1]/ser[now_i][1]-1)*100
    print(f'2026 高點 {ser[now_i][0]} → {now_n} 個交易日 跌 {now_dd:.1f}%')
    out[mk]={}
    for y,(a,b) in eps.items():
        i0=peak(ser,dt.date.fromisoformat(a),dt.date.fromisoformat(b)); pth=path(ser,i0); out[mk][y]=(str(ser[i0][0]),pth)
        if y=='2026': continue
        at=pth[now_n][1] if now_n<len(pth) else None
        hit=next((k for k,v in pth if v<=now_dd),None)
        mn=min(pth,key=lambda t:t[1]); 
        after=[v for k,v in pth]
        r12=None
        if hit is not None and i0+hit+252<len(ser): r12=(ser[i0+hit+252][1]/ser[i0+hit][1]-1)*100
        mdd_after=None
        if hit is not None: mdd_after=(min(ser[j][1] for j in range(i0+hit,min(len(ser),i0+hit+505)))/ser[i0+hit][1]-1)*100
        print(f'{y} 高點 {ser[i0][0]}：同樣第 {now_n} 天跌 {at:.1f}%；跌到 {now_dd:.0f}% 花了 {hit} 天；兩年內最深 {mn[1]:.0f}%（第 {mn[0]} 天）；從跌到 {now_dd:.0f}% 那天買：之後兩年內再跌 {mdd_after:.0f}%，12 個月 {r12:+.0f}%')
json.dump({k:{y:(d0,[[a,round(b,2)] for a,b in p]) for y,(d0,p) in v.items()} for k,v in out.items()},open(P+'paths.json','w'))
# (2) 買進持有
H=[('1年',252),('2年',504),('3年',756),('5年',1260)]
def hold(name,ser,ev):
    print(f'\n=== {name}：n={len(ev)} ===')
    rows=[]
    for i in ev:
        r=[(ser[i+k][1]/ser[i][1]-1)*100 if i+k<len(ser) else None for _,k in H]
        yrs=(ser[-1][0]-ser[i][0]).days/365.25
        cagr=((ser[-1][1]/ser[i][1])**(1/yrs)-1)*100 if yrs>1 else None
        mdd=(min(x[1] for x in ser[i:i+505])/ser[i][1]-1)*100
        rows.append(r)
        print(ser[i][0],' '.join('—' if x is None else f'{x:+.0f}%' for x in r),'| 至今年化','—' if cagr is None else f'{cagr:+.1f}%','| 兩年內再跌',f'{mdd:.0f}%')
    for j,(n,_) in enumerate(H):
        v=[x[j] for x in rows if x[j] is not None]
        if v: print(f'  {n}: 勝 {sum(a>0 for a in v)}/{len(v)}  中位 {st.median(v):+.0f}%  最差 {min(v):+.0f}%')
def first_dd(ser,th,reset=-0.10,start=252):
    ev=[];arm=True
    for i in range(start,len(ser)):
        hi=max(x[1] for x in ser[i-252:i+1]); dd=ser[i][1]/hi-1
        if dd<=th and arm: ev.append(i); arm=False
        if dd>reset: arm=True
    return ev
hold('台股加權：距一年高點首次跌滿 27%',tw,first_dd(tw,-0.27))
hold('台股加權：距一年高點首次跌滿 25%',tw,first_dd(tw,-0.25))
hold('那斯達克100：距一年高點首次跌滿 20%（1985起）',nd,first_dd(nd,-0.20))
hold('標普500：距一年高點首次跌滿 10%（1950起）',sp,first_dd(sp,-0.10,reset=-0.03))
# VIX 第一次收上 35（VIX 回到 20 以下才重新計）→ 買 NDX、買 S&P
vd={d:c for d,c in vx}; ndi={d:i for i,(d,c) in enumerate(nd)}; spi={d:i for i,(d,c) in enumerate(sp)}
ev=[];arm=True
for d,c in vx:
    if c>=35 and arm: ev.append(d); arm=False
    if c<20: arm=True
print('\nVIX 首次收上 35：',[str(x) for x in ev])
hold('VIX 首次收上 35 → 買那斯達克100',nd,[ndi[d] for d in ev if d in ndi])
hold('VIX 首次收上 35 → 買標普500',sp,[spi[d] for d in ev if d in spi])
