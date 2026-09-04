import json,statistics as st
R=json.load(open("rev.json")); yoy=R["yoy"]; T=json.load(open("taiex.json")); mc=T["mc"]
mons=sorted(m for m in mc if m in yoy); Y=[yoy[m] for m in mons]; P=[mc[m] for m in mons]; n=len(mons)
def ma(v,k): return [None if i<k-1 else sum(v[i-k+1:i+1])/k for i in range(len(v))]
Y3=ma(Y,3)
def fwd(i,h): return (P[i+h]/P[i]-1)*100 if i+h<n else None
def mdd(i,h):
    j=min(n-1,i+h); seg=P[i:j+1]
    if len(seg)<2: return None
    pk=seg[0]; w=0
    for x in seg: pk=max(pk,x); w=min(w,x/pk-1)
    return w*100
base12=[fwd(i,12) for i in range(n) if fwd(i,12) is not None]
print(f"基準12M 平均{st.mean(base12):+.1f}% 中位{st.median(base12):+.1f}% 負率{sum(1 for x in base12 if x<0)/len(base12)*100:.0f}%")
print("\n=== 條件化：3MA 高於 L% 之後才算減速（D=10pp, M=3）===")
print(f"{'L門檻':>6}{'訊號':>5}{'12M平均':>9}{'12M中位':>9}{'負率':>6}{'均最大回檔':>10}  訊號月份")
for L in (0,15,25,30,35):
    sig=[]
    for i in range(14,n):
        if Y3[i] is None or Y3[i]<L: continue
        hi=max(x for x in Y3[max(0,i-12):i+1] if x is not None)
        if all(Y3[k] is not None and Y3[k]<Y3[k-1] for k in range(i-2,i+1)) and (hi-Y3[i])>=10: sig.append(i)
    dc=[]
    for i in sig:
        if not dc or i-dc[-1]>=12: dc.append(i)
    r=[fwd(i,12) for i in dc if fwd(i,12) is not None]; d=[mdd(i,12) for i in dc if mdd(i,12) is not None]
    if not r: print(f"{L:>6}{len(dc):>5}   —（樣本不足）"); continue
    print(f"{L:>6}{len(dc):>5}{st.mean(r):>+8.1f}%{st.median(r):>+8.1f}%{sum(1 for x in r if x<0)/len(r)*100:>5.0f}%{st.mean(d):>9.1f}%  {[mons[i] for i in dc]}")

print("\n=== 反向檢定：營收『加速』是不是反而危險？（3MA 創 12 個月新高）===")
sig=[i for i in range(14,n) if Y3[i] is not None and Y3[i]==max(x for x in Y3[max(0,i-12):i+1] if x is not None)]
dc=[]
for i in sig:
    if not dc or i-dc[-1]>=12: dc.append(i)
r=[fwd(i,12) for i in dc if fwd(i,12) is not None]; d=[mdd(i,12) for i in dc if mdd(i,12) is not None]
print(f"訊號{len(dc)}次 12M平均{st.mean(r):+.1f}% 中位{st.median(r):+.1f}% 負率{sum(1 for x in r if x<0)/len(r)*100:.0f}% 均最大回檔{st.mean(d):.1f}%")
print("月份:",[mons[i] for i in dc])

print("\n=== 兩次真正見頂前 6 個月的逐月讀數（看有沒有肉眼可辨的形狀）===")
for pk in ("2007-10","2021-12"):
    i=mons.index(pk); print(f"\n[{pk} 峰]")
    for k in range(i-6,i+4):
        if 0<=k<n: print(f"  {mons[k]} YoY{Y[k]:+6.1f}% 3MA{Y3[k]:+6.1f}% TAIEX{P[k]:7.0f}")
