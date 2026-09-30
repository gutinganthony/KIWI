import json,gzip,os,sys,datetime,math,random
import numpy as np
random.seed(11); np.random.seed(11)
IS=('2009-07-01','2017-12-31'); OOS=('2018-01-01','2026-09-30')
def ema(x,n):
    k=2/(n+1); o=np.empty_like(x); o[0]=x[0]
    for i in range(1,len(x)): o[i]=o[i-1]+k*(x[i]-o[i-1])
    return o
def wt(h,l,c):
    hlc3=(h+l+c)/3; esa=ema(hlc3,10); d=ema(np.abs(hlc3-esa),10)
    ci=np.where(d>0,(hlc3-esa)/(0.015*np.where(d>0,d,1)),0.0); w1=ema(ci,21)
    w2=np.convolve(w1,np.ones(4)/4,'full')[:len(w1)]; w2[:3]=w1[:3]
    return w1,w2
def load(path,tw=False):
    r=json.load(gzip.open(path,'rt'))
    if not r.get('ok') or not r.get('d') or len(r['d'])<500: return None
    d=np.array(r['d']); h=np.array(r['h'],float); l=np.array(r['l'],float); c=np.array(r['c'],float); a=np.array(r['a'],float); v=np.array(r['v'],float)
    m=(a>0)&(c>0)&(h>0)&(l>0); d,h,l,c,a,v=d[m],h[m],l[m],c[m],a[m],v[m]
    f=a/c; H,L,C=h*f,l*f,a.copy(); nspl=0
    if tw:
        # 台股有漲跌幅限制（2015-06-01 前 7%，之後 10%）：超過限制的單日變動只可能是減資／資料錯誤，把它之前的價格等比例接合
        thr=np.where(d[1:]<'2015-06-01',0.075,0.105); ret=C[1:]/C[:-1]-1
        jumps=np.flatnonzero(np.abs(ret)>thr)+1
        for j in jumps[::-1]:
            k=C[j]/C[j-1]; H[:j]*=k; L[:j]*=k; C[:j]*=k; nspl+=1
    return dict(d=d,h=H,l=L,c=C,v=v,cr=c,nspl=nspl)
def weekly(D):
    d=D['d']; wk=np.array([datetime.date.fromisoformat(x).isocalendar()[:2] for x in d]); key=wk[:,0]*100+wk[:,1]
    idx=np.flatnonzero(np.r_[key[1:]!=key[:-1],True]); st=np.r_[0,idx[:-1]+1]
    return dict(d=d[idx],h=np.array([D['h'][s:e+1].max() for s,e in zip(st,idx)]),l=np.array([D['l'][s:e+1].min() for s,e in zip(st,idx)]),c=D['c'][idx])
def declus(ix,gap):
    out=[];last=-10**9
    for i in ix:
        if i-last>=gap: out.append(i); last=i
    return np.array(out,int)
def sigs(w1,w2,warm):
    gx=np.flatnonzero((w1[:-1]<=w2[:-1])&(w1[1:]>w2[1:]))+1; dx=np.flatnonzero((w1[:-1]>=w2[:-1])&(w1[1:]<w2[1:]))+1
    b=gx[(w1[gx]<=-53)&(gx>=warm)]; s=dx[(w1[dx]>=53)&(dx>=warm)]
    return b,s
def edge(c,d,b,s,H,per,warm):
    N=len(c); lo=np.searchsorted(d,per[0]); hi=np.searchsorted(d,per[1],side='right')
    lo=max(lo,warm); last=min(hi,N-H)
    if last-lo<200: return None
    base=c[lo+H:last+H]/c[lo:last]-1; mu=base.mean(); sd=base.std()
    bb=b[(b>=lo)&(b<last)]; ss=s[(s>=lo)&(s<last)]
    if len(bb)<3 or len(ss)<3: return None
    rb=c[bb+H]/c[bb]-1; rs=c[ss+H]/c[ss]-1
    zb=(rb.mean()-mu)/(sd/math.sqrt(len(bb))); zs=(mu-rs.mean())/(sd/math.sqrt(len(ss)))
    return dict(zb=zb,zs=zs,z=(zb+zs)/math.sqrt(2),nb=len(bb),ns=len(ss),exb=rb.mean()-mu,exs=mu-rs.mean(),winb=(rb>0).mean(),wins=(rs<0).mean(),mu=mu,lo=lo,last=last)
def null_z(c,d,b,s,H,per,warm,draws=300):
    N=len(c); lo=max(np.searchsorted(d,per[0]),warm); last=min(np.searchsorted(d,per[1],side='right'),N-H)
    base=c[lo+H:last+H]/c[lo:last]-1; mu=base.mean(); sd=base.std(); L=last-lo
    bb=b[(b>=lo)&(b<last)]-lo; ss=s[(s>=lo)&(s<last)]-lo; out=[]
    for _ in range(draws):
        kb=np.random.randint(H,L-H); ks=np.random.randint(H,L-H)
        rb=base[(bb+kb)%L]; rs=base[(ss+ks)%L]
        out.append(((rb.mean()-mu)/(sd/math.sqrt(len(bb)))+(mu-rs.mean())/(sd/math.sqrt(len(ss))))/math.sqrt(2))
    return np.array(out)
def strat(c,d,w1,w2,per,warm):
    lo=max(np.searchsorted(d,per[0]),warm+1); hi=np.searchsorted(d,per[1],side='right')
    gx=(w1[:-1]<=w2[:-1])&(w1[1:]>w2[1:]); dx=(w1[:-1]>=w2[:-1])&(w1[1:]<w2[1:])
    inpos=False; eq=1.0; pk=1.0; mdd=0; tr=[]; ent=None; t_in=0
    for i in range(lo,hi):
        if inpos: eq*=c[i]/c[i-1]; t_in+=1
        pk=max(pk,eq); mdd=min(mdd,eq/pk-1); j=i-1
        if not inpos and gx[j-1] and w1[j]<=-53: inpos=True; ent=i
        elif inpos and dx[j-1] and w1[j]>=53: inpos=False; tr.append(c[i]/c[ent]-1)
    bh=c[hi-1]/c[lo]; yrs=(hi-lo)/ (252 if len(c)>2000 else 52)
    b=c[lo:hi]/c[lo]; bmdd=(b/np.maximum.accumulate(b)-1).min()
    return dict(cagr=eq**(1/yrs)-1,bh=bh**(1/yrs)-1,mdd=mdd,bmdd=bmdd,expo=t_in/(hi-lo),n=len(tr),win=(np.mean([x>0 for x in tr]) if tr else float('nan')),avg=(np.mean(tr) if tr else float('nan')))
def feats(D,idx_c=None,idx_d=None,per=IS):
    d,c=D['d'],D['c']; lo=np.searchsorted(d,per[0]); hi=np.searchsorted(d,per[1],side='right'); cc=c[lo:hi]
    r=np.diff(np.log(cc)); vol=r.std()*math.sqrt(252)
    r20=np.log(cc[20:]/cc[:-20]); vr=r20.var()/(20*r.var())
    yrs=len(cc)/252; cagr=(cc[-1]/cc[0])**(1/yrs)-1
    mdd=(cc/np.maximum.accumulate(cc)-1).min()
    # efficiency ratio over 60-day windows
    er=float(np.mean([abs(cc[i+60]-cc[i])/den for i in range(0,len(cc)-61,20) for den in [np.abs(np.diff(cc[i:i+61])).sum()] if den>0]))
    tv=np.median((D['cr']*D['v'])[lo:hi])
    out=dict(vol=vol,vr=vr,cagr=cagr,mdd=mdd,er=er,logtv=math.log10(tv+1))
    if idx_c is not None:
        m=dict(zip(idx_d,idx_c)); common=[i for i in range(lo,hi) if d[i] in m]
        if len(common)>500:
            x=np.array([c[i] for i in common]); y=np.array([m[d[i]] for i in common])
            rx=np.diff(np.log(x)); ry=np.diff(np.log(y)); beta=np.cov(rx,ry)[0,1]/ry.var(); r2=np.corrcoef(rx,ry)[0,1]**2
            out.update(beta=beta,idio=1-r2)
    return out
SKIP=[]
def analyze(folder,liq_top=300,idx=None,min_start='2009-06-30'):
    res={}
    for fn in sorted(os.listdir(folder)):
        D=load(os.path.join(folder,fn),tw=folder.endswith('tw'))
        if D is None or D['d'][0]>min_start or D['d'][-1]<'2026-09-20': continue
        r=np.diff(np.log(D['c']))
        if np.abs(r).max()>np.log(1.8) or D['nspl']>10: SKIP.append((fn,D['nspl'])); continue   # data-error guard
        res[fn.split('.')[0]]=D
    # liquidity rank (last 250 days median trading value)
    tv={k:np.median((D['cr']*D['v'])[-250:]) for k,D in res.items()}
    keep=sorted(tv,key=lambda k:-tv[k])[:liq_top]
    out={}
    for k in keep:
        D=res[k]; W=weekly(D); o={'tv':tv[k],'nspl':D['nspl']}
        for tf,X,H,warm,gap in [('d',D,60,60,20),('w',W,13,30,4)]:
            w1,w2=wt(X['h'],X['l'],X['c']); b,s=sigs(w1,w2,warm); b=declus(b,gap); s=declus(s,gap)
            for pn,per in [('is',IS),('oos',OOS),('all',(IS[0],OOS[1]))]:
                o[f'{tf}_{pn}']=edge(X['c'],X['d'],b,s,H,per,warm)
            if idx:
                j=np.searchsorted(idx[1],X['d'],side='right')-1; ok=j>=0
                ic=np.where(ok,idx[0][np.clip(j,0,None)],np.nan)
                rel=X['c']/np.where(np.isnan(ic),1,ic)
                if not np.isnan(ic[np.searchsorted(X['d'],IS[0])]):
                    for pn,per in [('is',IS),('oos',OOS)]:
                        o[f'{tf}_{pn}_mkt']=edge(rel,X['d'],b,s,H,per,warm)
            ei,eo=o[f'{tf}_is'],o[f'{tf}_oos']
            if ei and eo:
                ni=null_z(X['c'],X['d'],b,s,H,IS,warm); no=null_z(X['c'],X['d'],b,s,H,OOS,warm)
                o[f'{tf}_nullmin']=np.minimum(ni,no).tolist()
            o[f'{tf}_strat_oos']=strat(X['c'],X['d'],w1,w2,OOS,warm)
            xs=np.flatnonzero((w1[:-1]-w2[:-1])*(w1[1:]-w2[1:])<0)+1; lx=int(xs[-1]) if len(xs) else None
            o[f'{tf}_now']=dict(w1=float(w1[-1]),w2=float(w2[-1]),date=str(X['d'][-1]),lastx=(str(X['d'][lx]),'黃金' if w1[lx]>w2[lx] else '死亡',float(w1[lx])) if lx else None,
                lastb=(str(X['d'][b[-1]]),float(w1[b[-1]])) if len(b) else None,lasts=(str(X['d'][s[-1]]),float(w1[s[-1]])) if len(s) else None)
        o['f_is']=feats(D,*(idx if idx else (None,None)),per=IS); o['f_all']=feats(D,*(idx if idx else (None,None)),per=(IS[0],OOS[1]))
        out[k]=o
    return out
if __name__=='__main__':
    mk=sys.argv[1]
    if mk=='us':
        I=load('scan/idx_spy.json.gz')
    else:
        I=load('scan/idx_0050.json.gz',tw=True)
    idx=(I['c'],I['d']) if I else None
    out=analyze(f'scan/{mk}',idx=idx)
    json.dump(out,open(f'scan/res_{mk}.json','w'),default=lambda x: float(x) if isinstance(x,(np.floating,np.integer)) else str(x))
    print(mk,'analyzed',len(out),'skipped(data)',len(SKIP))
