"""Unified, resumable, quota-adaptive FinMind fetcher.

usage: fetch_all.py <dataset-key> [ids-file]

The free tier answers 402 when the hourly quota is spent and 403 'ip banned'
(with retry_after) when hit too hard. Rather than guess the ceiling, run a few
workers and let the server's own responses set the pace: back off on 402/403,
speed back up when a run of calls succeeds.
"""
import urllib.request, urllib.error, json, time, os, sys, threading
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
START, END = '2021-06-01', '2026-08-13'
KEYS = {
    'price': ('TaiwanStockPrice', 'px_long.ndjson'),
    'inst':  ('TaiwanStockInstitutionalInvestorsBuySell', 'inst_long.ndjson'),
    'margin':('TaiwanStockMarginPurchaseShortSale', 'margin_long.ndjson'),
    'rev':   ('TaiwanStockMonthRevenue', 'rev_long.ndjson'),
}
KEY = sys.argv[1]
DATASET, OUTNAME = KEYS[KEY]
OUT = os.path.join(BASE, OUTNAME)

if len(sys.argv) > 2:
    IDS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
else:
    INFO = json.load(open(os.path.join(BASE, '..', 'info.json')))['data']
    IDS = sorted({r['stock_id'] for r in INFO
                  if r.get('type') in ('twse', 'tpex')
                  and len(r['stock_id']) == 4 and r['stock_id'].isdigit()})
META = {}
for r in json.load(open(os.path.join(BASE, '..', 'info.json')))['data']:
    META.setdefault(r['stock_id'], {'name': r.get('stock_name', ''), 'market': r.get('type', ''),
                                    'industry': r.get('industry_category', '')})

done = set()
if os.path.exists(OUT):
    for line in open(OUT):
        try: done.add(json.loads(line)['id'])
        except Exception: pass
todo = [s for s in IDS if s not in done]
# Sorted order means a partial run leaves a systematically biased sample (all
# low stock numbers = traditional industries). Pull the names under study first,
# then shuffle the rest so any early stop still yields a random cross-section.
import random as _rnd
PRIORITY = ['2059','2327','2344','2337','2408','8299','3260','4967','5289','2455',
            '3006','3661','6669','2454','2330','3034','3037','3231','2382','6488',
            '3529','8046','2368','2383','1815','1802','1303','3481','2303','2360']
head = [x for x in PRIORITY if x in todo]
rest = [x for x in todo if x not in set(head)]
_rnd.seed(5); _rnd.shuffle(rest)
todo = head + rest
print(f'{KEY}: total {len(IDS)}, done {len(done)}, todo {len(todo)}', flush=True)

URL = ('https://api.finmindtrade.com/api/v4/data?dataset={}&data_id={}'
       '&start_date=' + START + '&end_date=' + END)

RATE_PER_HOUR = 850          # raised after 30min at 370/hr drew zero 402s; the block() handler is the safety net
INTERVAL = 3600.0 / RATE_PER_HOUR
lock = threading.Lock()
state = {'next_slot': 0.0, 'blocked_until': 0.0}

def wait_turn():
    while True:
        with lock:
            now = time.time()
            t = max(now, state['next_slot'], state['blocked_until'])
            state['next_slot'] = t + INTERVAL
        w = t - time.time()
        if w > 0: time.sleep(w)
        with lock:
            if time.time() >= state['blocked_until']: return
        time.sleep(1)

def block(seconds, why):
    with lock:
        state['blocked_until'] = max(state['blocked_until'], time.time() + seconds)
        print(f'{why}: pausing {seconds}s', flush=True)

def ok():
    pass

def fetch(sid):
    # FinMind signals quota state with real HTTP codes (402 quota, 403 ip ban),
    # which urlopen raises rather than returns -- read the body off the error.
    for _ in range(80):
        wait_turn()
        try:
            r = json.load(urllib.request.urlopen(URL.format(DATASET, sid), timeout=40))
            if r.get('status') == 200:
                ok(); return r.get('data', [])
            block(60, f"payload status {r.get('status')}"); continue
        except urllib.error.HTTPError as e:
            body = {}
            try: body = json.loads(e.read().decode() or '{}')
            except Exception: pass
            if e.code == 403:
                block(int(body.get('retry_after') or 900) + 30, 'ip banned'); continue
            if e.code == 402:
                block(int(body.get('retry_after') or 300) + 20, 'hourly quota'); continue
            block(45, f'http {e.code}'); continue
        except Exception as ex:
            block(20, f'network {type(ex).__name__}'); continue
    return None

FOREIGN = {'Foreign_Investor', 'Foreign_Dealer_Self'}
DEALER = {'Dealer_self', 'Dealer_Hedging'}

def pack(sid, d):
    rec = {'id': sid}
    if not d: return rec
    if KEY == 'price':
        rec.update(META.get(sid, {}),
                   dt=[x['date'] for x in d], h=[x['max'] for x in d], l=[x['min'] for x in d],
                   c=[x['close'] for x in d], v=[x['Trading_Volume'] for x in d],
                   m=[x['Trading_money'] for x in d])
    elif KEY == 'inst':
        agg = {}
        for x in d:
            k = agg.setdefault(x['date'], [0, 0, 0]); net = x['buy'] - x['sell']
            if x['name'] in FOREIGN: k[0] += net
            elif x['name'] == 'Investment_Trust': k[1] += net
            elif x['name'] in DEALER: k[2] += net
        ks = sorted(agg)
        rec.update(inst_dt=ks, fi=[agg[k][0] for k in ks],
                   it=[agg[k][1] for k in ks], dl=[agg[k][2] for k in ks])
    elif KEY == 'margin':
        rec.update(mg_dt=[x['date'] for x in d],
                   mgbal=[x['MarginPurchaseTodayBalance'] for x in d],
                   shbal=[x['ShortSaleTodayBalance'] for x in d],
                   mglimit=[x['MarginPurchaseLimit'] for x in d])
    elif KEY == 'rev':
        rec['rv'] = [[x['date'], x['revenue_year'], x['revenue_month'], x['revenue']] for x in d]
    return rec

n = 0
wlock = threading.Lock()
with open(OUT, 'a') as fh, ThreadPoolExecutor(3) as ex:
    def job(sid):
        global n
        rec = pack(sid, fetch(sid))
        with wlock:
            fh.write(json.dumps(rec, separators=(',', ':')) + '\n'); fh.flush()
            n += 1
            if n % 100 == 0: print(f'{n}/{len(todo)}', flush=True)
    list(ex.map(job, todo))
print('DONE', n, flush=True)
