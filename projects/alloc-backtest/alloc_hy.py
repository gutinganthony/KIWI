from alloc_bt import *
import alloc_mc as mc
hy=fred('BAMLHYH0A0HYM2TRIV'); ig=fred('BAMLCC0A0CMTRIV')
print('HY yld',fred('BAMLH0A0HYM2EY').iloc[-1],'IG yld',fred('BAMLC0A0CMEY').iloc[-1])
# daily-aligned TWD values, month-ends from 2023-11
def twd(s): f=fx.reindex(s.index).ffill(); return s*f
X=pd.DataFrame({'HY':me(twd(hy)),'IG':me(twd(ig)),'HYu':me(hy),'IGu':me(ig)})
st=pd.Timestamp('2023-11-30')
Lx=L.join(X,how='left'); Rx=Lx.pct_change().loc[st+pd.offsets.MonthEnd(1):]
print('months',len(Rx),Rx.index[0].date(),Rx.index[-1].date())
yrs=len(Rx)/12
for c in ['HYu','IGu','HY','IG','AGG','TW','QQQ','SPY']:
    v=(1+Rx[c]).prod(); m=Rx[c]
    print(c,'CAGR %.1f%% vol %.1f%% worstM %.1f%%'%(100*(v**(1/yrs)-1),100*m.std()*12**.5,100*m.min()))
print(Rx[['HY','IG','AGG','TW','QQQ','SPY','FX']].corr().round(2))
def port3(w,fee=0.0):
    h={k:w[k] for k in w}; vals=[1]
    for t,row in Rx.iterrows():
        for k in h: h[k]*=1+row[k]-(fee/12 if k=='HY' else (0.005/12 if k=='IG' else 0))
        vals.append(sum(h.values()))
        if t.month==12: s=sum(h.values()); h={k:s*w[k] for k in w}
    v=pd.Series(vals); return 100*(v.iloc[-1]**(1/yrs)-1),100*(v/v.cummax()-1).min()
mixes={'A QQQ25/TW25':{'QQQ':.25,'TW':.25},'C TW50':{'TW':.5},'D SPY25/TW25':{'SPY':.25,'TW':.25},'F Q12.5/S12.5/TW25':{'QQQ':.125,'SPY':.125,'TW':.25},'H QQQ50':{'QQQ':.5},'I SPY50':{'SPY':.5}}
print('\n3y real: bond=AGG50 | HY25+IG25 gross | HY25+IG25 net(HY fee1.5%,IG0.5%)')
for k,e in mixes.items():
    a=port3({**e,'AGG':.5}); b=port3({**e,'HY':.25,'IG':.25}); c=port3({**e,'HY':.25,'IG':.25},0.015)
    print(k,'%.1f/%.1f | %.1f/%.1f | %.1f/%.1f'%(*a,*b,*c))
# forward: bond sleeve mean = assumption (USD), AGG-shaped noise
print('\nforward 5y bootstrap (bond sleeve mean in USD, unhedged):')
rows=[]
for yb in [0.05,0.06,0.07,0.08]:
  for hc in [0.0,0.03]:
    for k,e in mixes.items():
        o=mc.sim({**e,'AGG':.5},yb,hc,N=3000)
        rows.append((f'債{yb*100:.0f}%',f'股-{hc*100:.0f}pp',k,round(np.median(o)*100,1),round((o>=0.11).mean()*100),round(np.percentile(o,10)*100,1)))
print(pd.DataFrame(rows,columns=['債','股','組合','中位','P≥11','P10']).to_string())
