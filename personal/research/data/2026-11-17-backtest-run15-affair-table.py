"""run15：比對網傳圖〈When a CEO's affair comes out〉。同一組 12 案＋輝達，算原始報酬（還原價）與相對 SPY（含息）的超額報酬。
起點＝消息曝光前一個收盤（與該圖相同定義）。終點：1 週＝5 個交易日、1 年＝252 個交易日、至今＝2026-11-12（圖的終點）。"""
import json,datetime as dt
P='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/affair/'
def L(s):
    r=json.load(open(P+s+'.json'))['chart']['result'][0]
    ts=[dt.datetime.utcfromtimestamp(t).date() for t in r['timestamp']]
    a=r['indicators']['adjclose'][0]['adjclose']
    return [(d,c) for d,c in zip(ts,a) if c]
# (公司, 代號, 消息曝光前一個收盤日, 圖上 1週/1年/至今, 黃仁勳式「離職」與否, 註)
E=[("Google","GOOGL","2013-08-27",(2.7,36.6,1320),False,"布林（共同創辦人，非 CEO）婚變曝光；未離職"),
   ("Lockheed Martin","LMT","2012-11-08",(-2.6,60.8,904),True,"候任 CEO Kubasik 因與下屬關係被迫辭職"),
   ("Best Buy","BBY","2012-04-09",(-3.5,19.0,672),True,"CEO Dunn 辭職，事後調查揭露與下屬關係"),
   ("Boeing","BA","2005-03-04",(-1.5,27.7,318),True,"CEO Stonecipher 因與下屬關係被要求辭職"),
   ("Kohl's","KSS","2025-04-30",(-2.7,119,269),True,"CEO Buchanan 因與供應商伴侶的利益衝突被開除"),
   ("Amazon","AMZN","2019-01-08",(1.1,14.2,223),False,"貝佐斯宣布離婚、婚外情曝光；續任 CEO"),
   ("Cboe","CBOE","2023-09-15",(2.4,42.5,150),True,"CEO Tilly 因未揭露與同事關係辭職"),
   ("HP","HPQ","2010-08-06",(-12.6,-28.9,123),True,"CEO Hurd 因與外部承包商關係及費用問題辭職"),
   ("McDonald's","MCD","2019-11-01",(-0.2,12.6,66.3),True,"CEO Easterbrook 因與員工關係被開除"),
   ("BP","BP","2023-09-12",(1.9,-13.6,41.4),True,"CEO Looney 因未完整揭露與同事關係辭職"),
   ("Intel","INTC","2018-06-20",(-8.8,-9.5,34.7),True,"CEO Krzanich 因與員工關係辭職"),
   ("Nestlé","NESN.SW","2025-09-01",(0.3,7.6,14.5),True,"CEO Freixe 因未揭露與下屬關係被開除"),
   ("Nvidia","NVDA","2026-11-06",(-11.0,None,-11.0),True,"黃仁勳 11/12 辭職")]
spy=L('SPY'); SD={d:c for d,c in spy}
END=dt.date(2026,11,12)
def at(ser,i): return ser[i] if 0<=i<len(ser) else None
def r(ser,d0,k=None,end=None):
    i0=max(i for i,(d,c) in enumerate(ser) if d<=d0)
    if end: i1=max(i for i,(d,c) in enumerate(ser) if d<=end)
    else:
        i1=i0+k
        if i1>=len(ser): return None,None,None
    a,b=ser[i0],ser[i1]
    sa=SD.get(a[0]); sb=SD.get(b[0])
    # 非美股（NESN）日期對不上時，用不晚於該日的 SPY
    if sa is None: sa=[c for d,c in spy if d<=a[0]][-1]
    if sb is None: sb=[c for d,c in spy if d<=b[0]][-1]
    raw=(b[1]/a[1]-1)*100; sp=(sb/sa-1)*100
    yrs=(b[0]-a[0]).days/365.25
    return raw,raw-sp,(sp,yrs)
print("公司|起點|圖:1週/1年/至今|我算原始:1週/1年/至今|相對SPY:1週/1年/至今|同期SPY至今|年數")
rows=[]
for n,s,d,img,left,note in E:
    ser=L(s); d0=dt.date.fromisoformat(d)
    w=r(ser,d0,5); y=r(ser,d0,252); t=r(ser,d0,end=END)
    f=lambda x:'—' if x is None else f'{x:+.1f}'
    print(f"{n}|{d}|{img}|{f(w[0])}/{f(y[0])}/{f(t[0])}|{f(w[1])}/{f(y[1])}/{f(t[1])}|{f(t[2][0])}|{t[2][1]:.1f}")
    rows.append((n,y[1],t[1],left))
ys=[x[1] for x in rows if x[1] is not None and x[0]!='Nvidia']; ts=[x[2] for x in rows if x[0]!='Nvidia']
import statistics as st
print('12 案 1年相對SPY：贏',sum(v>0 for v in ys),'/',len(ys),'中位',round(st.median(ys),1))
print('12 案 至今相對SPY：贏',sum(v>0 for v in ts),'/',len(ts),'中位',round(st.median(ts),1))
lv=[x for x in rows if x[3] and x[0]!='Nvidia']
print('真的離職的',len(lv),'案 1年相對SPY：贏',sum(x[1]>0 for x in lv if x[1] is not None),'/',sum(x[1] is not None for x in lv),'中位',round(st.median([x[1] for x in lv if x[1] is not None]),1))
print('真的離職的',len(lv),'案 至今相對SPY：贏',sum(x[2]>0 for x in lv),'/',len(lv),'中位',round(st.median([x[2] for x in lv]),1))
