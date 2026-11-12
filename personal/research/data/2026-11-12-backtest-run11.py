import json,datetime as dt,bisect
P='/tmp/claude-0/-home-user-KIWI/81241006-b795-558c-9ffa-398e87d3c614/scratchpad/bt/ceo/'
def L(s):
    r=json.load(open(P+s+'.json'))['chart']['result'][0]; m={}
    adj=r['indicators'].get('adjclose',[{}])[0].get('adjclose') or r['indicators']['quote'][0]['close']
    for t,c in zip(r['timestamp'],adj):
        if c: m[dt.datetime.utcfromtimestamp(t).date().isoformat()]=c
    k=sorted(m); return k,[m[x] for x in k]
SD,SC=L('SPY'); GD,GC=L('GSPC')
E=[('創辦人交棒','微軟','蓋茲卸任執行長','MSFT','2000-01-14'),('創辦人交棒','甲骨文','艾利森卸任執行長','ORCL','2014-09-19'),('創辦人交棒','Alphabet','佩吉、布林卸下職務','GOOGL','2019-12-04'),('創辦人交棒','星巴克','舒茲卸任執行長','SBUX','2016-12-02'),('創辦人交棒','蘋果','賈伯斯辭任執行長','AAPL','2011-08-25'),('創辦人交棒','亞馬遜','貝佐斯卸任執行長','AMZN','2021-02-03'),
   ('傳奇執行長卸任','迪士尼','艾格卸任執行長','DIS','2020-02-26'),
   ('醜聞或撤換','惠普','赫德（不當關係）','HPQ','2010-08-09'),('醜聞或撤換','永利','史蒂夫永利（性騷擾指控）','WYNN','2018-01-26'),('醜聞或撤換','英特爾','柯再奇（與員工關係）','INTC','2018-06-21'),('醜聞或撤換','棒約翰','創辦人施納特（不當言論）','PZZA','2018-07-12'),('醜聞或撤換','麥當勞','伊斯特布魯克（與員工關係）','MCD','2019-11-04'),('醜聞或撤換','英特爾','季辛格（被董事會撤換）','INTC','2024-12-02')]
def r(D,C,d,h):
    i=bisect.bisect_left(D,d)
    if h=='now': return (C[-1]/C[i-1]-1)*100
    return None if i+h>=len(C) else (C[i+h]/C[i-1]-1)*100
def mdd(d,h=252):
    i=bisect.bisect_left(GD,d); w=GC[i-1:i+h]; pk=w[0]; m=0
    for x in w: pk=max(pk,x); m=min(m,x/pk-1)
    return m*100
f=lambda x:'NA' if x is None else '%+.0f%%'%x
print('類型|公司|事件|日期|個股 1月/12月/24月/至今|相對標普(含息) 12月/24月/至今|之後12個月標普最大回撤')
for typ,co,ev,t,d in E:
    D,C=L(t); a=[r(D,C,d,h) for h in (21,252,504,'now')]; s=[r(SD,SC,d,h) for h in (21,252,504,'now')]
    rel=[None if x is None or y is None else ((1+x/100)/(1+y/100)-1)*100 for x,y in zip(a,s)]
    print(f"{typ}|{co}|{ev}|{d}|{'/'.join(map(f,a))}|{'/'.join(map(f,rel[1:]))}|{mdd(d):.0f}%")
print('資料最後一天',SD[-1])
