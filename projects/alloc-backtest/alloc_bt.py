import pandas as pd,numpy as np,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from alloc_load import load
from tw0050 import tw0050
D2=os.path.dirname(__file__)+'/../alloc2/'
def fred(id):
    s=pd.read_csv(D2+id+'.csv',index_col=0,parse_dates=True).iloc[:,0]
    return pd.to_numeric(s,errors='coerce').dropna()
fx=fred('DEXTAUS')
END=pd.Timestamp('2026-11-16')
def me(s):  # month-end series incl. final partial month at END
    s=s[s.index<=END]; return s.resample('ME').last().dropna()
p,r=tw0050(); tw=(1+r).cumprod()
lv={'TW':me(tw)}
fxm=me(fx)
for n in ['QQQ','SPY','AGG','IEF','TLT','SHY','LQD','BND']:
    lv[n]=me(load(n))*fxm   # TWD value of USD asset
    lv[n+'_usd']=me(load(n))
lv['FX']=fxm
L=pd.DataFrame(lv)
R=L.pct_change()
def port(w,start,end=None,reb='A'):
    rr=R.loc[start:end,list(w)].dropna()
    W=np.array([w[k] for k in w]); h=W.copy(); vals=[1.0]; idx=[rr.index[0]-pd.offsets.MonthEnd(1)]
    for t,row in rr.iterrows():
        h=h*(1+row.values); vals.append(h.sum()); idx.append(t)
        if reb=='M' or (reb=='A' and t.month==12) or (reb=='Q' and t.month in (3,6,9,12)): h=h.sum()*W
    return pd.Series(vals,index=idx)
def stats(v):
    m=v.pct_change().dropna(); yrs=len(m)/12
    cagr=v.iloc[-1]**(1/yrs)-1; vol=m.std()*np.sqrt(12)
    dd=(v/v.cummax()-1).min()
    y5=(v.shift(-60)/v)**(1/5)-1; y5=y5.dropna()
    y10=(v.shift(-120)/v)**(1/10)-1; y10=y10.dropna()
    return dict(CAGR=cagr*100,Vol=vol*100,MDD=dd*100,RetVol=cagr/vol,
        p5ge11=(y5>=0.11).mean()*100 if len(y5) else np.nan, worst5=y5.min()*100 if len(y5) else np.nan,
        med5=y5.median()*100 if len(y5) else np.nan,
        p10ge11=(y10>=0.11).mean()*100 if len(y10) else np.nan, worst10=y10.min()*100 if len(y10) else np.nan)
MIX={
 'A 基準 QQQ25/TW25':{'AGG':.5,'QQQ':.25,'TW':.25},
 'B QQQ10/TW40':{'AGG':.5,'QQQ':.10,'TW':.40},
 'C 全台股 TW50':{'AGG':.5,'TW':.50},
 'D SPY25/TW25':{'AGG':.5,'SPY':.25,'TW':.25},
 'E SPY10/TW40':{'AGG':.5,'SPY':.10,'TW':.40},
 'F QQQ12.5/SPY12.5/TW25':{'AGG':.5,'QQQ':.125,'SPY':.125,'TW':.25},
 'G SPY15/TW35':{'AGG':.5,'SPY':.15,'TW':.35},
 'H 全美科技 QQQ50':{'AGG':.5,'QQQ':.5},
 'I 全大盤 SPY50':{'AGG':.5,'SPY':.5},
}
if __name__=='__main__':
    pd.set_option('display.width',250); pd.set_option('display.max_columns',20)
    print('data start',L.dropna().index[0], 'end',L.index[-1])
    for st,en,lab in [('2003-10-31',None,'全期 2003/10–2026/11'),('2003-10-31','2009-12-31','2003–2009 (含金融海嘯)'),('2010-01-31','2019-12-31','2010–2019'),('2020-01-31',None,'2020–2026/11'),('2021-12-31',None,'2022–2026/11 (升息後)')]:
        print('\n==',lab)
        T=pd.DataFrame({k:stats(port(w,st,en)) for k,w in MIX.items()}).T.round(2)
        print(T if st=='2003-10-31' and en is None else T[['CAGR','Vol','MDD','RetVol']])
    print('\n== 單一資產（台幣計價，全期）')
    for a in ['TW','QQQ','SPY','AGG','IEF','TLT','SHY','LQD','FX','QQQ_usd','SPY_usd','AGG_usd']:
        print(a,{k:round(v,2) for k,v in stats(port({a:1},'2003-10-31')).items() if k in('CAGR','Vol','MDD')})
    print('\ncorr (月報酬, TWD)'); print(R[['TW','QQQ','SPY','AGG','FX']].loc['2003-11':].corr().round(2))
