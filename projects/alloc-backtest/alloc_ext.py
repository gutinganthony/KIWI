from alloc_bt import *
ff=fred('FEDFUNDS'); ff.index=ff.index+pd.offsets.MonthEnd(0)
cpi=fred('CPIAUCSL'); cpi.index=cpi.index+pd.offsets.MonthEnd(0); cpiy=(cpi/cpi.shift(12)-1)*100
y10=me(fred('DGS10'))
M=pd.DataFrame({'ff':ff,'ffchg':ff-ff.shift(12),'cpiy':cpiy,'y10':y10}).loc['2003-10':]
print('now:',M.tail(3).round(2))
print('recent corr TW-QQQ 2022+',R.loc['2022':,['TW','QQQ','SPY','AGG','FX']].corr().round(2).loc['TW'].to_dict())
# grid
rows=[]
for kind in ['QQQ','SPY','HALF']:
  for us in range(0,55,5):
    u=us/100; w={'AGG':.5,'TW':.5-u}
    if kind=='HALF': w['QQQ']=u/2; w['SPY']=u/2
    else: w[kind]=u
    w={k:v for k,v in w.items() if v>0}
    a=stats(port(w,'2003-10-31')); b=stats(port(w,'2021-12-31'))
    rows.append((kind,us,round(a['CAGR'],2),round(a['MDD'],1),round(a['RetVol'],2),round(b['CAGR'],2),round(b['MDD'],1)))
G=pd.DataFrame(rows,columns=['美股類型','美股%','全期CAGR','全期MDD','報酬/波動','2022+CAGR','2022+MDD'])
print(G.to_string())
# regime: forward 12m return starting at month-ends with condition
def fwd12(w):
    v=port(w,'2003-10-31'); return (v.shift(-12)/v-1)*100
F=pd.DataFrame({k:fwd12(w) for k,w in MIX.items()})
F=F.join(M,how='left')
for lab,cond in [('全部月份',F.index==F.index),('Fed 過去12月升息',F.ffchg>0.25),('10年債≥4.5%',F.y10>=4.5),('CPI年增≥3%',F.cpiy>=3),('升息且10Y≥4%',(F.ffchg>0.25)&(F.y10>=4))]:
    sub=F[cond].dropna(subset=[list(MIX)[0]])
    print('\n--',lab,'n=',len(sub),'起點月份樣本', sub.index.year.value_counts().sort_index().to_dict())
    print(sub[list(MIX)].agg(['mean','median','min']).T.round(1).assign(win=(sub[list(MIX)]>0).mean().round(2)).to_string())
