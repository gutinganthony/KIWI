import json,sys,math,statistics as st
import numpy as np
mk=sys.argv[1]; R=json.load(open(f'scan/res_{mk}.json')); U=json.load(open(f'scan/{mk}_universe.json'))
def Phi(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
def rankdata(a):
    a=np.asarray(a,float); o=a.argsort(); r=np.empty(len(a)); r[o]=np.arange(len(a)); return r
def spear(x,y):
    m=[(a,b) for a,b in zip(x,y) if a is not None and b is not None and not math.isnan(a) and not math.isnan(b)]
    if len(m)<10: return float('nan'),len(m)
    x,y=zip(*m); return float(np.corrcoef(rankdata(x),rankdata(y))[0,1]),len(m)
rows=[]
for k,o in R.items():
    S=None; tfb=None; zz={}
    for tf in ('d','w'):
        ei,eo=o.get(f'{tf}_is'),o.get(f'{tf}_oos')
        if ei and eo and ei!='None' and eo!='None':
            m=min(ei['z'],eo['z']); zz[tf]=(ei['z'],eo['z'],m)
            if S is None or m>S: S=m; tfb=tf
    if S is None: continue
    nulls=[np.array(o[f'{tf}_nullmin']) for tf in zz if f'{tf}_nullmin' in o]
    sn=np.max(np.vstack(nulls),axis=0) if nulls else None
    rows.append(dict(k=k,S=S,tf=tfb,zz=zz,sn=sn,o=o))
print(f'{mk}: 可評分 {len(rows)} 檔（兩個時期都至少各有 3 次買訊與 3 次賣訊）')
# null sd check
allnull=np.concatenate([np.array(r['o'][f'{tf}_nullmin']) for r in rows for tf in r['zz'] if f'{tf}_nullmin' in r['o']])
# analytic p: P(max_tf min(zi,zo) >= s), zi,zo ~ N(0,1) indep
for r in rows:
    q=(1-Phi(r['S']))**2; nt=len(r['zz']); r['p']=1-(1-q)**nt
rows.sort(key=lambda r:-r['S'])
# universe-level null: k-th largest across stocks per draw
D=min(len(r['sn']) for r in rows if r['sn'] is not None)
M=np.vstack([r['sn'][:D] for r in rows if r['sn'] is not None])
srt=-np.sort(-M,axis=0)
print('虛無假設下（訊號日期隨機）第1/5/10名的分數：平均',[round(float(srt[i].mean()),2) for i in (0,4,9)],'95分位',[round(float(np.percentile(srt[i],95)),2) for i in (0,4,9)])
print('實際第1/5/10名：',[round(rows[i]['S'],2) for i in (0,4,9)])
Sv=np.array([r['S'] for r in rows]); print('分數分布：≥+1 %d 檔｜≤−1 %d 檔｜中位 %+.2f'%((Sv>=1).sum(),(Sv<=-1).sum(),np.median(Sv)))
for tf in ('d','w'):
    zi=[r['zz'][tf][0] for r in rows if tf in r['zz']]; zo=[r['zz'][tf][1] for r in rows if tf in r['zz']]
    if zi: print(f'{tf} 全體平均 z：前半段 {np.mean(zi):+.2f}（>0 佔 {100*np.mean(np.array(zi)>0):.0f}%）｜後半段 {np.mean(zo):+.2f}（>0 佔 {100*np.mean(np.array(zo)>0):.0f}%）')
    for part,lab in (('zb','買訊'),('zs','賣訊')):
        a=[r['o'][f'{tf}_is'][part] for r in rows if tf in r['zz']]; b=[r['o'][f'{tf}_oos'][part] for r in rows if tf in r['zz']]
        if a: print(f'   {lab}平均 z：前 {np.mean(a):+.2f}／後 {np.mean(b):+.2f}')
for r in rows:
    mi=[]
    for tf in r['zz']:
        a,b=r['o'].get(f'{tf}_is_mkt'),r['o'].get(f'{tf}_oos_mkt')
        if a and b and a!='None' and b!='None': mi.append(min(a['z'],b['z']))
    r['Smkt']=max(mi) if mi else float('nan')
cnt=[int((M>=t).sum(axis=0).mean()) for t in (1.0,1.5,2.0)]
act=[sum(r['S']>=t for r in rows) for t in (1.0,1.5,2.0)]
print('分數≥1.0/1.5/2.0 的檔數：實際',act,'｜隨機平均',cnt)
# BH
ps=sorted((r['p'],i) for i,r in enumerate(rows)); m=len(ps); passed=0
for j,(p,i) in enumerate(ps,1):
    if p<=0.10*j/m: passed=j
print('BH FDR 10% 通過檔數:',passed)
# persistence
for tf in ('d','w'):
    x=[r['zz'][tf][0] for r in rows if tf in r['zz']]; y=[r['zz'][tf][1] for r in rows if tf in r['zz']]
    print(f'持續性 {tf}：前半段 z 與後半段 z 的等級相關 = {spear(x,y)[0]:+.3f}（n={len(x)}）')
    for part in ('zb','zs'):
        x=[r['o'][f'{tf}_is'][part] for r in rows if tf in r['zz']]; y=[r['o'][f'{tf}_oos'][part] for r in rows if tf in r['zz']]
        print(f'   {part}（{"買訊" if part=="zb" else "賣訊"}）前後半段相關 = {spear(x,y)[0]:+.3f}')
# features
fk=['vol','beta','idio','vr','er','cagr','mdd','logtv']
print('特徵與分數的等級相關（特徵用前半段 2009-2017 計算）:')
for f in fk:
    xs=[r['o']['f_is'].get(f) for r in rows]
    c1,_=spear(xs,[r['S'] for r in rows])
    cd,_=spear(xs,[r['zz']['d'][1] if 'd' in r['zz'] else None for r in rows]); cw,_=spear(xs,[r['zz']['w'][1] if 'w' in r['zz'] else None for r in rows])
    top=[r['o']['f_is'].get(f) for r in rows[:10] if r['o']['f_is'].get(f) is not None]; allv=[r['o']['f_is'].get(f) for r in rows if r['o']['f_is'].get(f) is not None]
    print(f'  {f:6s} 對穩健分數 {c1:+.2f}｜預測後半段日線z {cd:+.2f}｜週線z {cw:+.2f}｜前10中位 {st.median(top):.3f} vs 全體中位 {st.median(allv):.3f}')
print('\n前 20 名：')
for i,r in enumerate(rows[:20],1):
    k=r['k']; info=U.get(k); o=r['o']; tf=r['tf']; ei=o[f'{tf}_is']; eo=o[f'{tf}_oos']; s=o[f'{tf}_strat_oos']; nw=o[f'{tf}_now']
    name=(info[3] if mk=='us' else info[2]) if info else ''; ind=(info[1] if mk=='us' else info[1]) if info else ''
    print(f"{i:2d} {k} {str(name)[:28]}｜{str(ind)[:26]}｜{'日' if tf=='d' else '週'}線 穩健分數 {r['S']:.2f}（前 {ei['z']:.2f}／後 {eo['z']:.2f}）p≈{r['p']:.4f}｜扣大盤後 {r['Smkt']:.2f}｜隨機平移勝過比例 {100*float((r['sn']>=r['S']).mean()) if r['sn'] is not None else float('nan'):.1f}%")
    print(f"    後半段：買訊 n={eo['nb']} 超額 {100*eo['exb']:+.1f}% 勝率 {100*eo['winb']:.0f}%｜賣訊 n={eo['ns']} 少漲 {100*eo['exs']:+.1f}% 賣對率 {100*eo['wins']:.0f}%｜前半段：買 {100*ei['exb']:+.1f}% 賣 {100*ei['exs']:+.1f}%")
    print(f"    後半段策略(超賣金叉買/超買死叉賣)：年化 {100*s['cagr']:+.1f}% vs 持有 {100*s['bh']:+.1f}%｜回撤 {100*s['mdd']:.0f}% vs {100*s['bmdd']:.0f}%｜{s['n']} 筆 勝率 {100*s['win'] if s['win']==s['win'] else float('nan'):.0f}%｜在場 {100*s['expo']:.0f}%｜現在 WT1 {nw['w1']:+.0f} WT2 {nw['w2']:+.0f}")
    f=o['f_is']; print(f"    特徵(前半段)：波動 {100*f['vol']:.0f}% β {f.get('beta',float('nan')):.2f} 個股特有 {100*f.get('idio',float('nan')):.0f}% VR {f['vr']:.2f} ER {f['er']:.2f} 年化 {100*f['cagr']:+.0f}% 回撤 {100*f['mdd']:.0f}% 成交值log {f['logtv']:.1f}")
json.dump([dict(k=r['k'],S=r['S'],tf=r['tf'],p=r['p']) for r in rows],open(f'scan/rank_{mk}.json','w'))
print('\n特徵分五組（用前半段特徵分組）→ 後半段日線 z 平均（越高＝WT 越有效）｜扣大盤後 z：')
for f,lab in [('vol','波動度'),('vr','變異數比VR(<1均值回歸)'),('mdd','最大回撤(越接近0越淺)'),('beta','β'),('idio','個股特有波動比'),('cagr','前半段年化報酬'),('er','效率比ER(越低越盤整)'),('logtv','成交值')]:
    xs=[(r['o']['f_is'].get(f),r['zz']['d'][1],(r['o'].get('d_oos_mkt') or {}).get('z') if isinstance(r['o'].get('d_oos_mkt'),dict) else None) for r in rows if 'd' in r['zz'] and r['o']['f_is'].get(f) is not None and r['o']['f_is'].get(f)==r['o']['f_is'].get(f)]
    xs.sort(key=lambda t:t[0]); q=len(xs)//5
    out=[]
    for g in range(5):
        seg=xs[g*q:(g+1)*q] if g<4 else xs[4*q:]
        zm=[t[2] for t in seg if t[2] is not None]
        out.append(f"Q{g+1}[{seg[0][0]:.2f}~{seg[-1][0]:.2f}] z {np.mean([t[1] for t in seg]):+.2f}/{np.mean(zm) if zm else float('nan'):+.2f}")
    print(f'  {lab}: '+'｜'.join(out))
