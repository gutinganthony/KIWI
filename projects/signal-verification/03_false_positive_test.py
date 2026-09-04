import json,statistics as st
R=json.load(open("rev.json")); yoy=R["yoy"]; T=json.load(open("taiex.json")); mc=T["mc"]
mons=sorted(m for m in mc if m in yoy)   # 共同月份
Y=[yoy[m] for m in mons]; P=[mc[m] for m in mons]
n=len(mons); print("共同樣本月數",n,mons[0],"→",mons[-1])
def ma(v,k):
    return [None if i<k-1 else sum(v[i-k+1:i+1])/k for i in range(len(v))]
Y3=ma(Y,3)
def fwd(i,h):
    j=i+h
    return (P[j]/P[i]-1)*100 if j<n else None
def maxdd(i,h):
    j=min(n-1,i+h); seg=P[i:j+1]
    if len(seg)<2: return None
    pk=seg[0]; w=0
    for x in seg:
        pk=max(pk,x); w=min(w,x/pk-1)
    return w*100
# 基準
for h in (6,12):
    r=[fwd(i,h) for i in range(n) if fwd(i,h) is not None]
    d=[maxdd(i,h) for i in range(n) if maxdd(i,h) is not None]
    print(f"基準 {h}M: 平均 {st.mean(r):+.1f}% 中位 {st.median(r):+.1f}%  負報酬率 {sum(1 for x in r if x<0)/len(r)*100:.0f}%  平均最大回檔 {st.mean(d):.1f}%")

print("\n=== 規則測試：YoY 3MA 自 12 個月高點下滑 >= D pp，且連續 M 個月下滑 ===")
print(f"{'D':>4}{'M':>3} {'訊號數':>6} {'去叢集':>6} {'12M平均':>9}{'12M中位':>9}{'12M負率':>8}{'12M均回檔':>10}")
def signals(D,M):
    sig=[]
    for i in range(14,n):
        if Y3[i] is None: continue
        hi=max(x for x in Y3[max(0,i-12):i+1] if x is not None)
        dec=all(Y3[k] is not None and Y3[k]<Y3[k-1] for k in range(i-M+1,i+1))
        if dec and (hi-Y3[i])>=D: sig.append(i)
    return sig
best=None
for D in (5,8,10,15):
    for M in (2,3):
        s=signals(D,M)
        # 去叢集：12 個月內只留第一個
        dc=[]; 
        for i in s:
            if not dc or i-dc[-1]>=12: dc.append(i)
        r=[fwd(i,12) for i in dc if fwd(i,12) is not None]
        d=[maxdd(i,12) for i in dc if maxdd(i,12) is not None]
        if not r: continue
        print(f"{D:>4}{M:>3} {len(s):>6} {len(dc):>6} {st.mean(r):>+8.1f}%{st.median(r):>+8.1f}%{sum(1 for x in r if x<0)/len(r)*100:>7.0f}%{st.mean(d):>9.1f}%")
        if best is None or st.mean(r)<best[0]: best=(st.mean(r),D,M,dc)
print("\n=== 最佳規則的每一次訊號（逐筆，看有沒有真的抓到頂）===")
_,D,M,dc=best; print(f"參數 D={D}pp M={M}")
for i in dc:
    f6,f12=fwd(i,6),fwd(i,12); dd=maxdd(i,12)
    print(f"{mons[i]}  YoY3MA {Y3[i]:+6.1f}%  6M {f6 if f6 is None else round(f6,1)}  12M {f12 if f12 is None else round(f12,1)}  12M最大回檔 {dd if dd is None else round(dd,1)}")
print("\n=== 現況 ===")
for i in range(n-8,n):
    print(f"{mons[i]}  YoY {Y[i]:+6.1f}%  3MA {Y3[i]:+6.1f}%  TAIEX {P[i]:.0f}")
hi=max(x for x in Y3[n-13:n] if x is not None)
print(f"\n近 12 個月 3MA 高點 {hi:+.1f}%，最新 {Y3[n-1]:+.1f}%，自高點下滑 {hi-Y3[n-1]:.1f}pp")
