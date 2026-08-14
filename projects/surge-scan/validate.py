import json, os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjust import shock_days, adjust
BASE = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in json.load(open(os.path.join(BASE, 'scan.json')))
        if not r['id'].startswith('0')]                       # drop ETFs
SHOCK, _ = shock_days(os.path.join(BASE, 'prices.ndjson'))
px = {}
for line in open(os.path.join(BASE, 'prices.ndjson')):
    r = json.loads(line)
    if r.get('error'): continue
    c, _ = adjust(r['dt'], r['c'], SHOCK)
    px[r['id']] = (r['dt'], c, r['m'])
for r in rows:
    dt, c, m = px[r['id']]; i = dt.index(r['dt'])
    r['fwd_end'] = c[min(i+60, len(c)-1)]/c[i]-1
    r['fwd_min'] = min(c[i+1:i+61])/c[i]-1
bydate = {}
for r in rows: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    rs.sort(key=lambda x: x['turn20'])
    for k, r in enumerate(rs): r['turn_pct'] = k/max(1, len(rs)-1)

def stats(rs, label):
    if len(rs) < 30: return f'{label:44} n={len(rs)} (too few)'
    e = sorted(r['fwd_end'] for r in rs); d = sorted(r['fwd_min'] for r in rs); n = len(rs)
    return (f"{label:44} n={n:5}  hold60 med {st.median(e)*100:+6.1f}%  win {sum(1 for x in e if x>0)/n*100:4.1f}%  "
            f"medDD {st.median(d)*100:+6.1f}%  P(+80%) {sum(r['surge'] for r in rs)/n*100:4.1f}%")

for lbl, sub in [('2025H2', [r for r in rows if r['dt'] < '2026-01-01']),
                 ('2026H1', [r for r in rows if r['dt'] >= '2026-01-01'])]:
    print(f'--- {lbl} (ETFs excluded) ---')
    print(stats(sub, 'ALL (base)'))
    tp = sorted(r['turn_pct'] for r in sub); rp = sorted(r['ret120'] for r in sub if r.get('ret120') is not None)
    t90, t75, r75 = tp[int(len(tp)*.9)], tp[int(len(tp)*.75)], rp[int(len(rp)*.75)]
    print(stats([r for r in sub if r['turn_pct'] >= t90], 'turnover top 10%'))
    # does it survive OUTSIDE the mega caps? band = 75th-90th percentile only
    print(stats([r for r in sub if t75 <= r['turn_pct'] < t90], 'turnover 75-90th pct (中大型，非權值)'))
    print(stats([r for r in sub if r['turn_pct'] >= t75 and r.get('ret120') is not None
                 and r['ret120'] >= r75], 'turnover top25% AND ret120 top25%'))
    print(stats([r for r in sub if r['turn_pct'] < t75 and r.get('ret120') is not None
                 and r['ret120'] >= r75], 'ret120 top25% but turnover LOW'))
    print()

print('='*112)
print('CASE CHECK: would the screen have flagged the three names at their real breakout?')
print('='*112)
CASES = [('2059', '川湖', '2025-07-18'), ('2327', '國巨*', '2025-09-03'),
         ('2327', '國巨*', '2026-04-01'), ('2426', '鼎元', '2026-02-09'),
         ('8358', '金居', '2025-07-08')]
for sid, nm, d in CASES:
    cand = [r for r in rows if r['id'] == sid and r['dt'] >= d]
    if not cand: print(f'{nm} {d}: no sampled observation near that date'); continue
    r = min(cand, key=lambda x: x['dt'])
    peers = bydate[r['dt']]
    rp = sorted(x['ret120'] for x in peers if x.get('ret120') is not None)
    rrank = sum(1 for x in rp if x <= r['ret120'])/len(rp)
    print(f"{nm:5} {r['dt']}  turnover pct {r['turn_pct']*100:5.1f}  ret120 pct {rrank*100:5.1f}  "
          f"ret120 {r['ret120']*100:+6.1f}%  from52h {r['from52h']*100:+6.1f}%  "
          f"lu20 {r['lu20']}  -> next60 max {r['fwdmax']*100:+6.0f}% end {r['fwd_end']*100:+6.0f}%")
