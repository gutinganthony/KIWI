"""Targeted chip pull: every surge stock + a random control sample.
FinMind's free tier caps requests per hour and answers 402 when exhausted,
so back off long and keep going instead of dropping the stock."""
import urllib.request, json, time, os, random

BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'scan.json')))
surge_ids = sorted({r['id'] for r in rows if r['surge']})
other_ids = sorted({r['id'] for r in rows} - set(surge_ids))
random.seed(42)
controls = random.sample(other_ids, min(260, len(other_ids)))
IDS = sorted(set(surge_ids) | set(controls))

OUT = os.path.join(BASE, 'chips.ndjson')
done = set()
if os.path.exists(OUT):
    for line in open(OUT):
        try:
            r = json.loads(line)
            if r.get('complete'): done.add(r['id'])
        except Exception: pass
todo = [s for s in IDS if s not in done]
print(f'surge {len(surge_ids)} controls {len(controls)} -> target {len(IDS)}, todo {len(todo)}', flush=True)

API = 'https://api.finmindtrade.com/api/v4/data?dataset={}&data_id={}&start_date=2024-06-01&end_date=2026-08-13'

PACE = 6.0        # <=600 req/hr: stay inside the free tier instead of getting banned

def get(ds, sid):
    for a in range(40):
        try:
            r = json.load(urllib.request.urlopen(API.format(ds, sid), timeout=30))
            time.sleep(PACE)
            if r.get('status') == 200:
                return r.get('data', [])
            if r.get('status') == 403:          # ip banned, server tells us for how long
                w = int(r.get('retry_after') or 900) + 30
                print(f'ip banned, sleeping {w}s', flush=True); time.sleep(w); continue
            if r.get('status') == 402:          # hourly quota exhausted
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
        rec = {'id': sid, 'complete': True}
        inst = get('TaiwanStockInstitutionalInvestorsBuySell', sid)
        if inst:
            agg = {}
            for x in inst:
                d = agg.setdefault(x['date'], [0, 0, 0])
                net = x['buy'] - x['sell']
                if x['name'] in FOREIGN: d[0] += net
                elif x['name'] == 'Investment_Trust': d[1] += net
                elif x['name'] in DEALER: d[2] += net
            ks = sorted(agg)
            rec.update(inst_dt=ks, fi=[agg[k][0] for k in ks],
                       it=[agg[k][1] for k in ks], dl=[agg[k][2] for k in ks])
        rv = get('TaiwanStockMonthRevenue', sid)
        if rv:
            rec['rv'] = [[x['date'], x['revenue_year'], x['revenue_month'], x['revenue']] for x in rv]
        fh.write(json.dumps(rec, separators=(',', ':')) + '\n'); fh.flush()
        n += 1
        if n % 25 == 0: print(f'{n}/{len(todo)}', flush=True)
print('DONE', n, flush=True)
