"""Institutional net buy/sell for surge stocks + control sample.
Two passes so a kill mid-run still leaves the load-bearing dataset complete:
pass 1 = institutional (the actual hypothesis), pass 2 = monthly revenue.
Throttled to stay inside FinMind's free tier -- unthrottled bursts get the IP banned."""
import urllib.request, json, time, os, random, sys

BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'scan.json')))
surge_ids = sorted({r['id'] for r in rows if r['surge']})
other_ids = sorted({r['id'] for r in rows} - set(surge_ids))
random.seed(42)
IDS = sorted(set(surge_ids) | set(random.sample(other_ids, min(260, len(other_ids)))))

DS = sys.argv[1]                      # 'inst' or 'rev'
CFG = {'inst': ('TaiwanStockInstitutionalInvestorsBuySell', 'inst.ndjson'),
       'rev':  ('TaiwanStockMonthRevenue', 'rev.ndjson')}[DS]
DATASET, OUTNAME = CFG
OUT = os.path.join(BASE, OUTNAME)
done = set()
if os.path.exists(OUT):
    for line in open(OUT):
        try: done.add(json.loads(line)['id'])
        except Exception: pass
todo = [s for s in IDS if s not in done]
print(f'{DS}: target {len(IDS)}, done {len(done)}, todo {len(todo)}', flush=True)

API = ('https://api.finmindtrade.com/api/v4/data?dataset={}&data_id={}'
       '&start_date=2024-06-01&end_date=2026-08-13')
PACE = 5.0

def get(sid):
    for a in range(40):
        try:
            r = json.load(urllib.request.urlopen(API.format(DATASET, sid), timeout=30))
            time.sleep(PACE)
            s = r.get('status')
            if s == 200: return r.get('data', [])
            if s == 403:
                w = int(r.get('retry_after') or 900) + 30
                print(f'ip banned, sleeping {w}s', flush=True); time.sleep(w); continue
            if s == 402:
                print('quota hit, sleeping 600s', flush=True); time.sleep(600); continue
            time.sleep(30)
        except Exception:
            time.sleep(30)
    return None

FOREIGN = {'Foreign_Investor', 'Foreign_Dealer_Self'}
DEALER = {'Dealer_self', 'Dealer_Hedging'}
n = 0
with open(OUT, 'a') as fh:
    for sid in todo:
        d = get(sid)
        rec = {'id': sid}
        if d and DS == 'inst':
            agg = {}
            for x in d:
                k = agg.setdefault(x['date'], [0, 0, 0])
                net = x['buy'] - x['sell']
                if x['name'] in FOREIGN: k[0] += net
                elif x['name'] == 'Investment_Trust': k[1] += net
                elif x['name'] in DEALER: k[2] += net
            ks = sorted(agg)
            rec.update(inst_dt=ks, fi=[agg[k][0] for k in ks],
                       it=[agg[k][1] for k in ks], dl=[agg[k][2] for k in ks])
        elif d and DS == 'rev':
            rec['rv'] = [[x['date'], x['revenue_year'], x['revenue_month'], x['revenue']] for x in d]
        fh.write(json.dumps(rec, separators=(',', ':')) + '\n'); fh.flush()
        n += 1
        if n % 20 == 0: print(f'{n}/{len(todo)}', flush=True)
print('DONE', n, flush=True)
