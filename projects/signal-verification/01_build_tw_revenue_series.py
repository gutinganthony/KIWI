import json,urllib.request,time,statistics as st
B="https://api.finmindtrade.com/api/v4/data"
def get(ds,sid,s,e):
    u=f"{B}?dataset={ds}&data_id={sid}&start_date={s}&end_date={e}"
    for _ in range(3):
        try:
            with urllib.request.urlopen(u,timeout=40) as r: return json.load(r).get("data",[])
        except Exception as ex: time.sleep(3)
    return []
BASKET=["2330","2317","2454","2308","2382","2357","2409","2303","2474","3008","2301","2377"]
rev={}
for s in BASKET:
    d=get("TaiwanStockMonthRevenue",s,"2002-01-01","2026-09-30")
    if not d: print("MISS",s); continue
    ok=0
    for r in d:
        k=(r["revenue_year"],r["revenue_month"])
        rev.setdefault(k,{})[s]=r["revenue"]; ok+=1
    print(f"{s}: {ok} rows, first={min((r['revenue_year'],r['revenue_month']) for r in d)}")
    time.sleep(0.4)
# 只保留全員都有資料的月份，避免成分變動污染 YoY
full=set(BASKET)
months=sorted(k for k,v in rev.items() if set(v)==full)
print("\n完整月份數:",len(months),"範圍:",months[0],"→",months[-1])
agg={k:sum(rev[k].values()) for k in months}
yoy={}
for (y,m) in months:
    p=(y-1,m)
    if p in agg: yoy[(y,m)]=(agg[(y,m)]/agg[p]-1)*100
ks=sorted(yoy)
print("YoY 可用月份:",len(ks),ks[0],"→",ks[-1])
json.dump({"agg":{f"{y}-{m:02d}":v for (y,m),v in agg.items()},
           "yoy":{f"{y}-{m:02d}":v for (y,m),v in yoy.items()}},open("rev.json","w"))
# 印近期與關鍵歷史
def show(lbl,rng):
    print(f"\n--- {lbl} ---")
    for k in ks:
        s=f"{k[0]}-{k[1]:02d}"
        if rng[0]<=s<=rng[1]: print(f"{s}  YoY {yoy[k]:+7.1f}%")
show("2007-2009",("2007-01","2009-06"))
show("2025-2026 近期",("2025-06","2026-12"))
