"""run18（11/23）：用 FRED（VIXCLS、NASDAQ100、SP500）獨立重算 run16／run17 的 VIX 35 事件與報酬，和 Yahoo 版逐筆比對。"""
import csv,json,datetime as dt,statistics as st
P='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/r16/'
def F(f):
    o=[]
    for r in list(csv.reader(open(P+f)))[1:]:
        try: o.append((dt.date.fromisoformat(r[0]),float(r[1])))
        except: pass
    return o
def Y(f):
    r=json.load(open(P+f))['chart']['result'][0]
    return [(dt.datetime.utcfromtimestamp(t).date(),c) for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']) if c]
fv,fn,fs=F('fred_vix.csv'),F('fred_ndx.csv'),F('fred_sp.csv'); yv,yn,ys=Y('VIX.json'),Y('NDX.json'),Y('GSPC.json')
print('FRED 最後一筆 VIX',fv[-1],'NDX',fn[-1],'SP',fs[-1])
def events(vx):
    ev=[];arm=True
    for d,c in vx:
        if c>=35 and arm: ev.append(d); arm=False
        if c<20: arm=True
    return ev
ef=[d for d in events(fv) if d<dt.date(2026,11,1)]; ey=[d for d in events(yv) if d<dt.date(2026,11,1)]
print('FRED 事件',len(ef),'Yahoo 事件',len(ey),'一致' if ef==ey else ('差異',set(ef)^set(ey)))
# VIX 值差異
dy=dict(yv); mx=max((abs(c-dy[d]),d) for d,c in fv if d in dy); print('VIX 兩源最大差',mx)
# 2000 年 VIX 最高
print('2000 年 VIX 最高 FRED',max((c,d) for d,c in fv if d.year==2000),'Yahoo',max((c,d) for d,c in yv if d.year==2000))
def stats(ser,ev,name):
    idx={d:i for i,(d,c) in enumerate(ser)}; out={}
    for lab,k in (('1年',252),('2年',504),('3年',756),('5年',1260)):
        v=[(ser[idx[d]+k][1]/ser[idx[d]][1]-1)*100 for d in ev if d in idx and idx[d]+k<len(ser)]
        out[lab]=(sum(x>0 for x in v),len(v),round(st.median(v)),round(min(v)))
    print(name,out)
    return idx
stats(fn,ef,'FRED 那指'); stats(yn,ey,'Yahoo 那指'); stats(ys,ey,'Yahoo 標普')
# run17: 見底天數、再跌、退燒
def after(sp,vx,ev,name):
    si={d:i for i,(d,c) in enumerate(sp)}; vi={d:i for i,(d,c) in enumerate(vx)}; R=[]
    for d in ev:
        if d not in si: continue
        i=si[d]; w=sp[i:i+127]; lo=min(range(len(w)),key=lambda n:w[n][1]); dd=(w[lo][1]/sp[i][1]-1)*100
        k=vi[d]; cool=next(n for n in range(1,500) if vx[k+n][1]<25); cd=vx[k+cool][0]
        gap=(sp[si[cd]][1]/sp[i][1]-1)*100 if cd in si else None
        R.append((d,lo,dd,cool,gap))
    m=lambda n:st.median([x[n] for x in R if x[n] is not None])
    print(name,'n',len(R),'見底天數中位',m(1),'再跌中位',round(m(2),1),'退燒天數中位',m(3),'退燒日貴中位',round(m(4),1),'當天即最低',sum(x[1]==0 for x in R),'再跌>10%',sum(x[2]<=-10 for x in R),'退燒日較貴',sum(x[4]>0 for x in R if x[4] is not None),'最慘',min(R,key=lambda x:x[2])[:3])
    return R
after(ys,yv,ey,'Yahoo 標普＋Yahoo VIX'); after(ys,fv,ef,'Yahoo 標普＋FRED VIX')
# 近十年用 FRED SP500 驗 Yahoo 標普
ya=dict(ys); df=max((abs(c/ya[d]-1),d) for d,c in fs if d in ya); print('標普兩源最大相對差',df)
na=dict(yn); df=max((abs(c/na[d]-1),d) for d,c in fn if d in na); print('那指兩源最大相對差',df)
# 現況
hi=max(c for d,c in yn if d>=dt.date(2026,9,1)); print('那指高點',hi,'11/20 距高',round((yn[-1][1]/hi-1)*100,2),'差幾點到 -20%',round(yn[-1][1]-hi*0.8,1))
hs=max(c for d,c in ys if d>=dt.date(2026,9,1)); print('標普高點',hs,round((ys[-1][1]/hs-1)*100,2))
print('台股 36033.29/49822.55',round((36033.29/49822.55-1)*100,2),'36811.89',round((36811.89/49822.55-1)*100,2),'今日漲幅',round(778.60/36033.29*100,2),'兩日',round((36033.29/40194.91-1)*100,2),'11/20單日',round(-2393.60/38426.89*100,2))
print('國安基金進場 41661.70 → 36811.89',round((36811.89/41661.70-1)*100,1),'歷史區間',round(49822.55*0.75),round(49822.55*0.71))
