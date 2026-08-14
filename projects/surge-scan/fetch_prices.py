import urllib.request, json, time, os, sys
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
INFO = json.load(open(os.path.join(BASE, '..', 'info.json')))['data']
META = {}
for r in INFO:
    sid = r['stock_id']
    if r.get('type') in ('twse', 'tpex') and len(sid) == 4 and sid.isdigit():
        META.setdefault(sid, {'name': r.get('stock_name', ''), 'market': r['type'],
                              'industry': r.get('industry_category', '')})
IDS = sorted(META)
OUT = os.path.join(BASE, 'prices.ndjson')
done = set()
if os.path.exists(OUT):
    for line in open(OUT):
        try: done.add(json.loads(line)['id'])
        except Exception: pass
todo = [s for s in IDS if s not in done]
print(f'universe {len(IDS)} done {len(done)} todo {len(todo)}', flush=True)

URL = ('https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice'
       '&data_id={}&start_date=2024-06-01&end_date=2026-08-13')

def fetch(sid):
    for attempt in range(4):
        try:
            r = json.load(urllib.request.urlopen(URL.format(sid), timeout=30))
            if r.get('status') == 200:
                d = r.get('data', [])
                if not d: return None
                return {'id': sid, **META[sid],
                        'dt': [x['date'] for x in d],
                        'o': [x['open'] for x in d], 'h': [x['max'] for x in d],
                        'l': [x['min'] for x in d], 'c': [x['close'] for x in d],
                        'v': [x['Trading_Volume'] for x in d],
                        'm': [x['Trading_money'] for x in d]}
            time.sleep(2 ** attempt * 3)
        except Exception:
            time.sleep(2 ** attempt * 2)
    return {'id': sid, 'error': True}

n = 0
with open(OUT, 'a') as fh, ThreadPoolExecutor(8) as ex:
    for rec in ex.map(fetch, todo):
        n += 1
        if rec: fh.write(json.dumps(rec, separators=(',', ':')) + '\n')
        if n % 200 == 0:
            fh.flush(); print(f'{n}/{len(todo)}', flush=True)
print('DONE', n, flush=True)
