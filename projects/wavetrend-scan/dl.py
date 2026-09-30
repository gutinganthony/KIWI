import json,re,time,gzip,sys,os,urllib.request,datetime,math
mode=sys.argv[1]
def save(path,obj):
    with gzip.open(path,'wt') as f: json.dump(obj,f,separators=(',',':'))
def get(u,hdr=None,tries=6):
    for k in range(tries):
        try:
            req=urllib.request.Request(u,headers=hdr or {'User-Agent':'Mozilla/5.0'})
            return urllib.request.urlopen(req,timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code==404: return None
            if e.code in (429,402,500,502,503): time.sleep(30*(k+1)); continue
            return None
        except Exception: time.sleep(10*(k+1))
    return None
if mode=='tw':
    d=json.load(open('scan/tw_info.json'))['data']; uni={}
    for x in d:
        if re.fullmatch(r'[1-9]\d{3}',x['stock_id']) and x['type'] in ('twse','tpex') and x['industry_category'] not in ('ETF','ETN','Index','大盤','所有證券','受益證券','存託憑證','創新板股票','創新版股票','上櫃指數股票型基金(ETF)','上櫃ETF','指數投資證券(ETN)'):
            uni.setdefault(x['stock_id'],(x['type'],x['industry_category'],x['stock_name']))
    json.dump(uni,open('scan/tw_universe.json','w'),ensure_ascii=False)
    p1=int(datetime.datetime(2008,1,1).timestamp()); p2=int(datetime.datetime(2026,10,1).timestamp())
    for n,(sid,(tp,ind,name)) in enumerate(sorted(uni.items())):
        out=f'scan/tw/{sid}.json.gz'
        if os.path.exists(out): continue
        sym=sid+('.TW' if tp=='twse' else '.TWO')
        raw=get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={p1}&period2={p2}&interval=1d&events=div%2Csplit")
        rec={'sym':sym,'ok':False}
        try:
            r=json.loads(raw)['chart']['result'][0]; off=r['meta'].get('gmtoffset',28800); q=r['indicators']['quote'][0]; a=r['indicators'].get('adjclose',[{}])[0].get('adjclose')
            rows=[(datetime.datetime.utcfromtimestamp(t+off).strftime('%Y-%m-%d'),h,l,c,aa,v) for t,h,l,c,aa,v in zip(r['timestamp'],q['high'],q['low'],q['close'],a or q['close'],q['volume']) if None not in (h,l,c,aa) and c>0]
            rec={'sym':sym,'ok':True,'d':[x[0] for x in rows],'h':[x[1] for x in rows],'l':[x[2] for x in rows],'c':[x[3] for x in rows],'a':[x[4] for x in rows],'v':[x[5] or 0 for x in rows]}
        except Exception as e: rec['err']=str(e)[:100]
        save(out,rec); time.sleep(0.8)
        if n%100==0: print(n,sid,rec['ok'],time.strftime('%H:%M:%S'),flush=True)
elif mode=='us':
    u=json.load(open('scan/us_info.json'))['data']; latest={}
    for x in u:
        if x['stock_id'] not in latest or x['date']>latest[x['stock_id']]['date']: latest[x['stock_id']]=x
    rec=[v for v in latest.values() if v['date']>='2026-01-01' and v.get('MarketCap') and re.fullmatch(r'[A-Z]{1,5}',v['stock_id']) and (v.get('IPOYear') is None or (isinstance(v['IPOYear'],float) and math.isnan(v['IPOYear'])) or v['IPOYear']<=2008)]
    rec=[v for v in rec if v['stock_id']!='GOOG']
    top=sorted(rec,key=lambda v:-v['MarketCap'])[:320]
    json.dump({v['stock_id']:(v['MarketCap'],v.get('Subsector'),v.get('Country'),v['stock_name']) for v in top},open('scan/us_universe.json','w'),ensure_ascii=False)
    for n,v in enumerate(top):
        sid=v['stock_id']; out=f'scan/us/{sid}.json.gz'
        if os.path.exists(out): continue
        raw=get(f"https://api.finmindtrade.com/api/v4/data?dataset=USStockPrice&data_id={sid}&start_date=2008-01-01&end_date=2026-09-30")
        rec2={'sym':sid,'ok':False}
        try:
            j=json.loads(raw)
            if j.get('status')!=200: rec2['err']=j.get('msg'); time.sleep(60)
            r=[x for x in j['data'] if x['Close'] and x['High'] and x['Low'] and x['Adj_Close']]
            rec2={'sym':sid,'ok':True,'d':[x['date'] for x in r],'h':[x['High'] for x in r],'l':[x['Low'] for x in r],'c':[x['Close'] for x in r],'a':[x['Adj_Close'] for x in r],'v':[x['Volume'] or 0 for x in r]}
        except Exception as e: rec2['err']=rec2.get('err') or str(e)[:100]
        save(out,rec2); time.sleep(0.3)
        if n%50==0: print(n,sid,rec2['ok'],time.strftime('%H:%M:%S'),flush=True)
print('DONE',mode,time.strftime('%H:%M:%S'),flush=True)
