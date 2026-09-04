import json,urllib.request,time
B="https://api.finmindtrade.com/api/v4/data"
def get(ds,sid,s,e):
    u=f"{B}?dataset={ds}&data_id={sid}&start_date={s}&end_date={e}"
    for _ in range(3):
        try:
            with urllib.request.urlopen(u,timeout=60) as r: return json.load(r).get("data",[])
        except Exception: time.sleep(4)
    return []
# TAIEX 日線 -> 月收盤
px=[]
for a,b in [("2002-01-01","2010-12-31"),("2011-01-01","2018-12-31"),("2019-01-01","2026-09-03")]:
    px+=get("TaiwanStockPrice","TAIEX",a,b); time.sleep(0.5)
mc={}
for r in sorted(px,key=lambda x:x["date"]):
    mc[r["date"][:7]]=r["close"]
mons=sorted(mc)
print("TAIEX 月數",len(mons),mons[0],"→",mons[-1],"最新收盤",mc[mons[-1]])
R=json.load(open("rev.json")); yoy=R["yoy"]

# 找出所有「峰值後 >=20% 回檔」的峰
peaks=[]; i=0
while i<len(mons):
    p=mons[i]; hi=mc[p]
    # 往後找最低
    lo=hi; loj=i
    for j in range(i+1,len(mons)):
        if mc[mons[j]]<lo: lo,loj=mc[mons[j]],j
        if mc[mons[j]]>hi: break
    dd=lo/hi-1
    if dd<=-0.20 and (not peaks or p>peaks[-1][0]):
        # 確認 p 是區域高點（前後 6 個月內最高）
        w=[mc[m] for m in mons[max(0,i-6):i+7]]
        if hi==max(w): peaks.append((p,hi,mons[loj],lo,dd))
    i+=1
# 去重：同一波只留第一個
ded=[]
for pk in peaks:
    if not ded or pk[0]>ded[-1][2]: ded.append(pk)
print("\n=== TAIEX >=20% 回檔（月收盤口徑）===")
for p,hi,lm,lo,dd in ded: print(f"峰 {p} {hi:8.0f} → 谷 {lm} {lo:8.0f}  {dd*100:6.1f}%")

def y(m): return yoy.get(m)
print("\n=== 每次見頂前後：營收 YoY 的行為 ===")
print(f"{'指數峰':8} {'峰前YoY最高月':>13} {'領先(月)':>8} {'峰當月YoY':>10} {'YoY首次轉負':>12} {'落後(月)':>8}")
def midx(m): return mons.index(m) if m in mons else None
for p,hi,lm,lo,dd in ded:
    i=midx(p)
    win=[mons[k] for k in range(max(0,i-18),i+1) if mons[k] in yoy]
    if not win: continue
    ymax=max(win,key=lambda m:yoy[m])
    lead=(i-midx(ymax))
    # 首次轉負（峰之後）
    neg=None
    for k in range(i,min(len(mons),i+24)):
        m=mons[k]
        if m in yoy and yoy[m]<0: neg=m;break
    lag=(midx(neg)-i) if neg else None
    print(f"{p:8} {ymax:>13} {lead:>8} {yoy.get(p,float('nan')):>9.1f}% {str(neg):>12} {str(lag):>8}")
json.dump({"mc":mc,"peaks":[[a,b,c,d,e] for a,b,c,d,e in ded]},open("taiex.json","w"))
