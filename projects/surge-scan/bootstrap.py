"""Point estimates alone overstate certainty here: observations are sampled every
5 sessions, so rows from the same stock are heavily autocorrelated and the naive
n flatters the precision. Resample whole STOCKS with replacement (cluster
bootstrap) so the interval reflects the real number of independent units."""
import json, os, sys, random, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjust import shock_days, adjust

BASE = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in json.load(open(os.path.join(BASE, 'scan.json')))
        if not r['id'].startswith('0')]
SHOCK, _ = shock_days(os.path.join(BASE, 'prices.ndjson'))
px = {}
for line in open(os.path.join(BASE, 'prices.ndjson')):
    r = json.loads(line)
    if r.get('error'): continue
    c, _ = adjust(r['dt'], r['c'], SHOCK)
    px[r['id']] = (r['dt'], c)
for r in rows:
    dt, c = px[r['id']]; i = dt.index(r['dt'])
    r['fwd_end'] = c[min(i+60, len(c)-1)]/c[i]-1
bydate = {}
for r in rows: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    rs.sort(key=lambda x: x['turn20'])
    for k, r in enumerate(rs): r['tp'] = k/max(1, len(rs)-1)
for r in rows:
    dt, c = px[r['id']]; i = dt.index(r['dt'])
    r['accel'] = None
rows2 = []
for line in open(os.path.join(BASE, 'prices.ndjson')):
    r0 = json.loads(line)
    if r0.get('error'): continue
    m = r0['m']; dt = r0['dt']
    for r in rows:
        if r['id'] != r0['id']: continue
        i = dt.index(r['dt'])
        b = st.median(m[max(0, i-120):i]) or 1
        r['accel'] = (sum(m[i-20:i])/20)/b
random.seed(7)
B = 600

def boot(sub, pred, label):
    sel = [r for r in sub if pred(r)]
    if len(sel) < 40: return f'{label:34} n={len(sel)} (too few)'
    bystock = {}
    for r in sel: bystock.setdefault(r['id'], []).append(r)
    ids = list(bystock)
    meds, wins, surg = [], [], []
    for _ in range(B):
        samp = [x for k in (random.choice(ids) for _ in ids) for x in bystock[k]]
        e = [x['fwd_end'] for x in samp]
        meds.append(st.median(e))
        wins.append(sum(1 for x in e if x > 0)/len(e))
        surg.append(sum(x['surge'] for x in samp)/len(samp))
    def ci(a):
        a = sorted(a); return a[int(B*0.025)], a[int(B*0.975)]
    e0 = [x['fwd_end'] for x in sel]
    m0, w0 = st.median(e0), sum(1 for x in e0 if x > 0)/len(e0)
    s0 = sum(x['surge'] for x in sel)/len(sel)
    lm, hm = ci(meds); lw, hw = ci(wins); ls, hs = ci(surg)
    return (f'{label:34} n={len(sel):5} stocks={len(ids):4}  '
            f'med {m0*100:+6.1f}% [{lm*100:+6.1f},{hm*100:+6.1f}]  '
            f'win {w0*100:4.1f}% [{lw*100:4.1f},{hw*100:4.1f}]  '
            f'P(+80%) {s0*100:4.1f}% [{ls*100:4.1f},{hs*100:4.1f}]')

for lbl, key in [('2025H2', lambda r: r['dt'] < '2026-01-01'),
                 ('2026H1 (out-of-sample)', lambda r: r['dt'] >= '2026-01-01')]:
    sub = [r for r in rows if key(r)]
    print(f'\n=== {lbl} — cluster bootstrap, 95% CI over {B} resamples of stocks ===')
    print(boot(sub, lambda r: True, 'ALL (base)'))
    print(boot(sub, lambda r: r['tp'] >= 0.90, '成交金額前 10%'))
    print(boot(sub, lambda r: r['accel'] is not None and r['accel'] >= 7.0, '爆量（量能放大 >7x）'))
    print(boot(sub, lambda r: r['from52h'] <= -0.35, '落後股（距高 <= -35%）'))
    print(boot(sub, lambda r: r['lu20'] >= 1, '20 日內出現過漲停'))
