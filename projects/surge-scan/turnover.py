"""Is 'high turnover' just 'big liquid stock', or is it money ACCELERATING into
a name? The first is useless for finding a surge early, the second is actionable.
Separate them: absolute level vs the stock's own 6-month baseline."""
import json, os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjust import shock_days, adjust

BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'scan.json')))
SHOCK, _ = shock_days(os.path.join(BASE, 'prices.ndjson'))
px = {}
for line in open(os.path.join(BASE, 'prices.ndjson')):
    r = json.loads(line)
    if r.get('error'): continue
    c, _ = adjust(r['dt'], r['c'], SHOCK)
    px[r['id']] = (r['dt'], c, r['m'])

for r in rows:
    dt, c, m = px[r['id']]
    i = dt.index(r['dt'])
    fwd = c[i+1:i+61]
    r['fwd_end'] = c[min(i+60, len(c)-1)]/c[i]-1
    r['fwd_min'] = min(fwd)/c[i]-1
    base120 = st.median(m[max(0, i-120):i]) or 1
    r['turn_accel'] = (sum(m[i-20:i])/20) / base120      # own-baseline expansion
    r['turn_accel5'] = (sum(m[i-5:i])/5) / base120

# cross-sectional percentile of absolute turnover, per date
bydate = {}
for r in rows: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    rs.sort(key=lambda x: x['turn20'])
    for k, r in enumerate(rs): r['turn_pct'] = k/max(1, len(rs)-1)

test = [r for r in rows if r['dt'] >= '2026-01-01']

def stats(rs, label):
    if not rs: return f'{label}: empty'
    e = sorted(r['fwd_end'] for r in rs); d = sorted(r['fwd_min'] for r in rs); n = len(rs)
    return (f"{label:34} n={n:6}  hold60 med {st.median(e)*100:+6.1f}%  win {sum(1 for x in e if x>0)/n*100:4.1f}%  "
            f"medDD {st.median(d)*100:+6.1f}%  P(+80%) {sum(r['surge'] for r in rs)/n*100:4.1f}%")

print('OUT-OF-SAMPLE 2026-01-01 ~ 2026-06-13')
print('='*118)
print(stats(test, 'ALL (base)')); print()
for f in ['turn_pct', 'turn_accel', 'turn_accel5']:
    vals = sorted(r[f] for r in test if r.get(f) is not None)
    for q, lbl in [(0.9, 'top 10%'), (0.75, 'top 25%')]:
        thr = vals[int(len(vals)*q)]
        print(stats([r for r in test if r.get(f) is not None and r[f] >= thr], f'{f} {lbl} (>= {thr:.3g})'))
    print()
# does own-baseline expansion add anything ON TOP of absolute size?
vt = sorted(r['turn_pct'] for r in test); va = sorted(r['turn_accel'] for r in test)
t90, a75 = vt[int(len(vt)*0.9)], va[int(len(va)*0.75)]
big = [r for r in test if r['turn_pct'] >= t90]
print(stats(big, 'big & liquid only'))
print(stats([r for r in big if r['turn_accel'] >= a75], '  + money accelerating'))
print(stats([r for r in big if r['turn_accel'] < a75], '  + money NOT accelerating'))
small = [r for r in test if r['turn_pct'] < t90]
print(stats([r for r in small if r['turn_accel'] >= a75], 'NOT big, but money accelerating'))

print('\n' + '='*118)
print('REGIME ROBUSTNESS: same cuts on the earlier half (2025-06 ~ 2025-12)')
print('='*118)
tr = [r for r in rows if r['dt'] < '2026-01-01']
print(stats(tr, 'ALL (base, 2025H2)'))
vt2 = sorted(r['turn_pct'] for r in tr); va2 = sorted(r['turn_accel'] for r in tr)
print(stats([r for r in tr if r['turn_pct'] >= vt2[int(len(vt2)*0.9)]], 'turn_pct top 10%'))
print(stats([r for r in tr if r['turn_accel'] >= va2[int(len(va2)*0.9)]], 'turn_accel top 10% (爆量)'))
v3 = sorted(r['ret120'] for r in tr if r.get('ret120') is not None)
print(stats([r for r in tr if r.get('ret120') is not None and r['ret120'] >= v3[int(len(v3)*0.9)]], 'ret120 top 10%'))
print(stats([r for r in tr if r.get('from52h') is not None and r['from52h'] <= -0.35], 'from52h <= -35% (落後股)'))

print('\nWHO are the top-10%-turnover names? (2026H1, most frequent)')
from collections import Counter
big2 = [r for r in test if r['turn_pct'] >= t90]
cnt = Counter((r['id'], r['name']) for r in big2)
print(', '.join(f'{n}({k})x{c}' for (k, n), c in cnt.most_common(18)))
print('\nsurge rate among those names:',
      f"{sum(r['surge'] for r in big2)/len(big2)*100:.1f}%")
