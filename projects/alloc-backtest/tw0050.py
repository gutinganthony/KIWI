import json,pandas as pd,numpy as np,os
D=os.path.dirname(__file__)+'/../alloc2/'
def tw0050():
    d=json.load(open(D+'fm0050.json'))['data']
    p=pd.Series({pd.Timestamp(r['date']):float(r['close']) for r in d if r['close']>0}).sort_index()
    divs=json.load(open(D+'fmdiv.json'))['data']
    dv=pd.Series({pd.Timestamp(r['CashExDividendTradingDate']):float(r['CashEarningsDistribution'])+float(r['CashStatutorySurplus'] or 0) for r in divs})
    split=pd.Timestamp('2025-06-18')
    r=p/p.shift(1)
    for t,a in dv.items():
        if t in r.index: r[t]=(p[t]+a)/p.shift(1)[t]
        else: print('missing exdate',t)
    if split in r.index: r[split]=p[split]*4/p.shift(1)[split]
    r=r.iloc[1:]-1
    return p,r
if __name__=='__main__':
    p,r=tw0050()
    lim=np.where(r.index<pd.Timestamp('2015-06-01'),0.071,0.101)
    print('limit breaches:',r[r.abs()>lim])
    print('split window',p['2025-06-09':'2025-06-19'].to_dict())
    tr=(1+r).cumprod(); print('TR CAGR %.2f%%'%(100*(tr.iloc[-1]**(365.25/(tr.index[-1]-tr.index[0]).days)-1)), tr.index[0],tr.index[-1])
