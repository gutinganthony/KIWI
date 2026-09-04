import json,urllib.request,time
B="https://api.finmindtrade.com/api/v4/data"
def get(ds,sid=None,s=None,e=None):
    u=f"{B}?dataset={ds}"+(f"&data_id={sid}" if sid else "")+(f"&start_date={s}" if s else "")+(f"&end_date={e}" if e else "")
    for _ in range(3):
        try:
            with urllib.request.urlopen(u,timeout=60) as r: return json.load(r).get("data",[])
        except Exception: time.sleep(3)
    return []
NAMES={"3533":"嘉澤(UQD/連接器)","3013":"晟銘電(sidecar機殼)","3324":"雙鴻(冷板+CDU+快接)","3017":"奇鋐(冷板)","2308":"台達電(電源/sidecar)","6412":"群電(電源)"}
print(f"{'代碼':6}{'名稱':22}{'股價':>9}{'PER':>8}{'PBR':>7}{'殖利率':>7}")
px={}
for s in NAMES:
    p=get("TaiwanStockPrice",s,"2026-08-20","2026-09-03")
    per=get("TaiwanStockPER",s,"2026-08-20","2026-09-03")
    c=p[-1]["close"] if p else None; px[s]=c
    pr=per[-1] if per else {}
    print(f"{s:6}{NAMES[s]:22}{str(c):>9}{str(pr.get('PER')):>8}{str(pr.get('PBR')):>7}{str(pr.get('dividend_yield')):>7}")
    time.sleep(0.4)
print("\n=== 月營收 YoY（近 6 個月）===")
for s in NAMES:
    d=get("TaiwanStockMonthRevenue",s,"2024-01-01","2026-09-30")
    m={(r['revenue_year'],r['revenue_month']):r['revenue'] for r in d}
    ks=sorted(m)[-6:]
    out=[]
    for y,mo in ks:
        pv=m.get((y-1,mo))
        out.append(f"{y}/{mo:02d} {'%+.0f%%'%((m[(y,mo)]/pv-1)*100) if pv else 'n/a'}")
    print(f"{s} {NAMES[s]:20} "+" | ".join(out))
    time.sleep(0.4)
print("\n=== 財務結構（最近可得年度/季度：毛利率、營益率）===")
for s in NAMES:
    fs=get("TaiwanStockFinancialStatements",s,"2025-01-01","2026-09-30")
    by={}
    for r in fs: by.setdefault(r["date"],{})[r["type"]]=r["value"]
    dates=sorted(by)[-2:]
    for dt in dates:
        v=by[dt]; rev=v.get("Revenue"); gp=v.get("GrossProfit"); op=v.get("OperatingIncome")
        if rev:
            gm=f"{gp/rev*100:.1f}%" if gp else "n/a"; om=f"{op/rev*100:.1f}%" if op else "n/a"
            print(f"{s} {NAMES[s]:20} {dt}  營收 {rev/1e8:,.1f}億  毛利率 {gm}  營益率 {om}")
    time.sleep(0.4)
