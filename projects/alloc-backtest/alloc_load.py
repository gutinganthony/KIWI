import json,datetime as dt,pandas as pd,numpy as np,os
D=os.path.dirname(__file__)+'/../alloc/'
def load(name,adj=True):
    j=json.load(open(D+name+'.json'))['chart']['result'][0]
    idx=pd.to_datetime(j['timestamp'],unit='s').normalize()
    a=None
    if adj and 'adjclose' in j['indicators']: a=j['indicators']['adjclose'][0]['adjclose']
    if a is None: a=j['indicators']['quote'][0]['close']
    s=pd.Series(a,index=idx,dtype=float).dropna()
    s=s[~s.index.duplicated(keep='last')]
    return s
