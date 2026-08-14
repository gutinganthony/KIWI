"""The max-return-in-60-days definition flatters volatile stocks mechanically:
you cannot sell at the max. Re-score every feature on outcomes you could
actually realise -- buy and hold 60 sessions -- plus the drawdown you'd sit through."""
import json, os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjust import shock_days, adjust

BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'scan.json')))
SHOCK, _ = shock_days(os.path.join(BASE, 'prices.ndjson'))

# recompute realistic forward outcomes
px = {}
for line in open(os.path.join(BASE, 'prices.ndjson')):
    r = json.loads(line)
    if r.get('error'): continue
    c, _ = adjust(r['dt'], r['c'], SHOCK)
    px[r['id']] = (r['dt'], c)

for r in rows:
    dt, c = px[r['id']]
    i = dt.index(r['dt'])
    fwd = c[i+1:i+61]
    r['fwd_end'] = c[min(i+60, len(c)-1)]/c[i]-1
    r['fwd_min'] = min(fwd)/c[i]-1
    r['fwd_max'] = max(fwd)/c[i]-1

SPLIT = '2026-01-01'
test = [r for r in rows if r['dt'] >= SPLIT]

def stats(rs, label):
    e = sorted(r['fwd_end'] for r in rs)
    d = sorted(r['fwd_min'] for r in rs)
    n = len(rs)
    return (f"{label:26} n={n:6}  hold60 median {st.median(e)*100:+6.1f}%  mean {sum(e)/n*100:+6.1f}%  "
            f"win {sum(1 for x in e if x>0)/n*100:4.1f}%  |  median max-DD {st.median(d)*100:+6.1f}%  "
            f"worst-decile DD {d[n//10]*100:+6.1f}%  |  P(+80% max) {sum(r['surge'] for r in rs)/n*100:4.1f}%")

print('OUT-OF-SAMPLE PERIOD ONLY (2026-01-01 ~ 2026-06-13), buy & hold 60 sessions')
print('='*140)
print(stats(test, 'ALL (base)'))
print()
CUTS = [('ret120', 0.5867, '>='), ('above52l', 1.201, '>='), ('ret60', 0.4183, '>='),
        ('turn20', 1.606e9, '>='), ('atrpct', 0.05619, '>='), ('lu20', 1, '>='),
        ('from52h', -0.04186, '>=')]
for f, thr, op in CUTS:
    sel = [r for r in test if r.get(f) is not None and r[f] >= thr]
    if sel: print(stats(sel, f'{f} {op} {thr:.4g}'))
print()
# the opposite side -- the "buy the dip / laggard" instinct
for f, thr, lbl in [('from52h', -0.35, 'from52h <= -35% (深跌落後股)'),
                    ('ret120', 0.0, 'ret120 <= 0 (半年沒漲)'),
                    ('atrpct', 0.025, 'atrpct <= 2.5% (低波動牛皮股)')]:
    sel = [r for r in test if r.get(f) is not None and r[f] <= thr]
    if sel: print(stats(sel, lbl))
print()
# stack the two strongest independent legs
sel = [r for r in test if r.get('ret120') is not None and r['ret120'] >= 0.5867
       and r.get('turn20') is not None and r['turn20'] >= 1.606e9]
print(stats(sel, 'ret120 hi AND turn20 hi'))
sel2 = [r for r in sel if r.get('atrpct') is not None and r['atrpct'] >= 0.05619]
print(stats(sel2, '  + atrpct hi (3 legs)'))
