"""run17（11/23）：VIX 首次收上 35（回到 20 以下才重新計）之後：幾天見底、再跌多深、幾天後 VIX 回到 25 以下、等退燒才買差多少。台股：訊號隔一個交易日買加權。"""
import json,datetime as dt,statistics as st
P='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/r16/'
def L(f):
    r=json.load(open(P+f))['chart']['result'][0]
    return [(dt.datetime.utcfromtimestamp(t).date(),c) for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']) if c]
nd=L('NDX.json'); sp=L('GSPC.json'); vx=L('VIX.json'); tw=L('twii_long.json')
ndi={d:i for i,(d,c) in enumerate(nd)}; spi={d:i for i,(d,c) in enumerate(sp)}; vxi={d:i for i,(d,c) in enumerate(vx)}
ev=[];arm=True
for d,c in vx:
    if c>=35 and arm: ev.append(d); arm=False
    if c<20: arm=True
ev=[d for d in ev if d<dt.date(2026,11,1)]
print('事件|VIX當天|標普:幾天見底/再跌|那指:幾天見底/再跌|VIX幾天後回<25|等退燒那天的標普 vs 訊號日|訊號日買標普12m|退燒日買標普12m|VIX之後最高')
R=[]
for d in ev:
    i=spi[d]; j=ndi[d]; k=vxi[d]
    w=sp[i:i+127]; lo=min(range(len(w)),key=lambda n:w[n][1]); sdd=(w[lo][1]/sp[i][1]-1)*100
    w2=nd[j:j+127]; lo2=min(range(len(w2)),key=lambda n:w2[n][1]); ndd=(w2[lo2][1]/nd[j][1]-1)*100
    cool=next((n for n in range(1,400) if k+n<len(vx) and vx[k+n][1]<25),None)
    cd=vx[k+cool][0]; ci=spi.get(cd); gap=(sp[ci][1]/sp[i][1]-1)*100
    r1=(sp[i+252][1]/sp[i][1]-1)*100 if i+252<len(sp) else None; r2=(sp[ci+252][1]/sp[ci][1]-1)*100 if ci+252<len(sp) else None
    vmax=max(x[1] for x in vx[k:k+127])
    R.append((lo,sdd,lo2,ndd,cool,gap,r1,r2,vmax))
    print(f"{d}|{vx[k][1]:.1f}|{lo}天/{sdd:.0f}%|{lo2}天/{ndd:.0f}%|{cool}天({cd})|{gap:+.0f}%|{'—' if r1 is None else f'{r1:+.0f}%'}|{'—' if r2 is None else f'{r2:+.0f}%'}|{vmax:.0f}")
m=lambda n:st.median([x[n] for x in R])
print(f"\n中位：標普 {m(0):.0f} 天見底、再跌 {m(1):.1f}%；那指 {m(2):.0f} 天、再跌 {m(3):.1f}%；VIX {m(4):.0f} 天回到 25 以下；退燒日標普比訊號日 {m(5):+.1f}%")
print('訊號日就是 6 個月內最低收盤（0 天）的次數：',sum(x[0]==0 for x in R),'/',len(R),'；10 天內見底：',sum(x[0]<=10 for x in R),'；再跌超過 10%：',sum(x[1]<=-10 for x in R))
print('退燒日比訊號日貴的次數：',sum(x[5]>0 for x in R),'/',len(R))
# 台股：訊號後下一個台股交易日買
print('\n台股（訊號後下一個交易日買加權）')
T=[]
for d in ev:
    i=next((n for n,(x,c) in enumerate(tw) if x>d),None)
    if i is None or tw[i][0]<dt.date(1997,8,1) or (tw[i][0]-d).days>7: continue
    w=tw[i:i+127]; lo=min(range(len(w)),key=lambda n:w[n][1]); dd=(w[lo][1]/tw[i][1]-1)*100
    f=lambda k:(tw[i+k][1]/tw[i][1]-1)*100 if i+k<len(tw) else None
    T.append((lo,dd,f(63),f(126),f(252),f(504)))
    print(tw[i][0],f"{lo}天/{dd:.0f}%",' '.join('—' if x is None else f'{x:+.0f}%' for x in (f(63),f(126),f(252),f(504))))
for n,lab in ((2,'3m'),(3,'6m'),(4,'12m'),(5,'24m')):
    v=[x[n] for x in T if x[n] is not None]; print(lab,'勝',sum(a>0 for a in v),'/',len(v),'中位',round(st.median(v),1))
print('幾天見底中位',st.median([x[0] for x in T]),'再跌中位',round(st.median([x[1] for x in T]),1))
