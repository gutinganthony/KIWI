from alloc_bt import *
import json,datetime as d
j=json.load(open(os.path.dirname(__file__)+'/../alloc/AGG.json'))['chart']['result'][0]
dv=pd.Series({pd.Timestamp(int(k),unit='s'):v['amount'] for k,v in j['events']['dividends'].items()}).sort_index()
px=load('AGG',False); ttm=dv[dv.index>END-pd.Timedelta(days=365)].sum(); print('AGG TTM dist yield %.2f%% (n=%d, px %.2f)'%(100*ttm/px.iloc[-1],len(dv[dv.index>END-pd.Timedelta(days=365)]),px.iloc[-1]))
H=R.loc['2003-11':'2026-10',['TW','QQQ','SPY','FX','AGG_usd']].dropna()
print('hist sample',H.index[0],H.index[-1],len(H))
rng=np.random.default_rng(7)
def sim(w,ybond,eq_haircut=0.0,yrs=5,N=20000,blk=12):
    n=yrs*12; nb=n//blk; T=len(H)
    ag=H.AGG_usd.values-H.AGG_usd.mean()+ybond/12
    fxr=H.FX.values
    usd={'QQQ':H.QQQ.values,'SPY':H.SPY.values}
    out=np.empty(N)
    starts=rng.integers(0,T-blk,size=(N,nb))
    W=w
    for i in range(N):
        idx=(starts[i][:,None]+np.arange(blk)).ravel()
        g=1.0; h={k:W[k] for k in W}
        for m,t in enumerate(idx):
            for k in h:
                if k=='AGG': r=(1+ag[t])*(1+fxr[t])-1
                elif k=='TW': r=H.TW.values[t]-eq_haircut/12
                else: r=usd[k][t]-eq_haircut/12   # usd series already in TWD? no -> below
                h[k]*=1+r
            if m%12==11:
                s=sum(h.values()); h={k:s*W[k] for k in W}
        out[i]=sum(h.values())**(1/yrs)-1
    return out
# H.QQQ/H.SPY in R are TWD returns already (L built as usd*fx). ok.
if __name__=='__main__':
    rows=[]
    for ybond in [0.0285,0.050]:
      for hc in [0.0,0.03]:
        for k,w in MIX.items():
            o=sim(w,ybond,hc,N=4000)
            rows.append((f'債{ybond*100:.1f}%',f'股折減{hc*100:.0f}pp',k,round(np.median(o)*100,1),round((o>=0.11).mean()*100,0),round((o<0).mean()*100,0),round(np.percentile(o,10)*100,1)))
    print(pd.DataFrame(rows,columns=['債券假設','股票假設','組合','5年CAGR中位','P(≥11%)','P(<0)','P10']).to_string())
