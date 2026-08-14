"""Does institutional flow lead a surge? The three case studies all pointed at
'investment trust flips from selling to buying' as the one early signal
(King Slide: 9 sessions before the breakout). Test it against a control group.

Normalisation note: shares outstanding needs the margin dataset, which was
dropped to halve the request count. Institutional nets are instead expressed as
a share of the stock's own traded volume -- how much of the tape each investor
type absorbed -- which needs no share count and is directly comparable."""
import json, os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjust import shock_days, adjust

BASE = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in json.load(open(os.path.join(BASE, 'scan.json')))
        if not r['id'].startswith('0')]
inst = {}
for fn in ('inst.ndjson', 'chips.ndjson'):
    p = os.path.join(BASE, fn)
    if not os.path.exists(p): continue
    for line in open(p):
        r = json.loads(line)
        if r.get('inst_dt'): inst.setdefault(r['id'], r)
print(f'institutional coverage: {len(inst)} stocks')

SHOCK, _ = shock_days(os.path.join(BASE, 'prices.ndjson'))
px = {}
for line in open(os.path.join(BASE, 'prices.ndjson')):
    r = json.loads(line)
    if r.get('error'): continue
    c, _ = adjust(r['dt'], r['c'], SHOCK)
    px[r['id']] = (r['dt'], c, r['v'], r['m'])

def idx_le(arr, val):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo+hi)//2
        if arr[mid] <= val: lo = mid+1
        else: hi = mid
    return lo-1

use = []
for r in rows:
    ch = inst.get(r['id'])
    if not ch: continue
    dt, c, v, m = px[r['id']]
    i = dt.index(r['dt'])
    r['fwd_end'] = c[min(i+60, len(c)-1)]/c[i]-1
    r['fwd_min'] = min(c[i+1:i+61])/c[i]-1
    idt, fi, it, dl = ch['inst_dt'], ch['fi'], ch['it'], ch['dl']
    j = idx_le(idt, r['dt'])
    if j < 60: continue
    vol20 = sum(v[i-20:i]) or 1
    vol60 = sum(v[i-60:i]) or 1
    r['fi20_sh'] = sum(fi[j-19:j+1])/vol20
    r['it20_sh'] = sum(it[j-19:j+1])/vol20
    r['dl20_sh'] = sum(dl[j-19:j+1])/vol20
    r['fi60_sh'] = sum(fi[j-59:j+1])/vol60
    r['it60_sh'] = sum(it[j-59:j+1])/vol60
    r['it_days60'] = sum(1 for x in it[j-59:j+1] if x != 0)
    prev30, last10 = sum(it[j-39:j-9]), sum(it[j-9:j+1])
    r['it_flip'] = 1 if (prev30 <= 0 and last10 > 0) else 0      # the King Slide signal
    pf30, lf10 = sum(fi[j-39:j-9]), sum(fi[j-9:j+1])
    r['fi_flip'] = 1 if (pf30 <= 0 and lf10 > 0) else 0
    r['it_zero'] = 1 if r['it_days60'] == 0 else 0
    use.append(r)
print(f'usable observations: {len(use)}  (surge {sum(x["surge"] for x in use)})')

def stats(rs, label):
    if len(rs) < 40: return f'{label:40} n={len(rs)} (too few)'
    e = sorted(x['fwd_end'] for x in rs); d = sorted(x['fwd_min'] for x in rs); n = len(rs)
    return (f"{label:40} n={n:5}  hold60 med {st.median(e)*100:+6.1f}%  win {sum(1 for x in e if x>0)/n*100:4.1f}%  "
            f"medDD {st.median(d)*100:+6.1f}%  P(+80%) {sum(x['surge'] for x in rs)/n*100:4.1f}%")

for lbl, sub in [('2025H2 (train)', [x for x in use if x['dt'] < '2026-01-01']),
                 ('2026H1 (out-of-sample)', [x for x in use if x['dt'] >= '2026-01-01'])]:
    if len(sub) < 200: print(f'--- {lbl}: only {len(sub)} obs, skipping ---'); continue
    print(f'\n--- {lbl} ---')
    print(stats(sub, 'ALL (base)'))
    for f in ['fi20_sh', 'it20_sh', 'fi60_sh', 'it60_sh']:
        vals = sorted(x[f] for x in sub)
        hi = vals[int(len(vals)*0.9)]; lo = vals[int(len(vals)*0.1)]
        print(stats([x for x in sub if x[f] >= hi], f'{f} top 10% (>= {hi*100:.1f}% of tape)'))
        print(stats([x for x in sub if x[f] <= lo], f'{f} bottom 10%'))
    print(stats([x for x in sub if x['it_flip']], '投信由賣轉買 (it_flip)'))
    print(stats([x for x in sub if x['fi_flip']], '外資由賣轉買 (fi_flip)'))
    print(stats([x for x in sub if x['it_zero']], '投信 60 日完全零進出'))
    # does institutional flow add anything on top of the turnover signal?
    bd = {}
    for x in sub: bd.setdefault(x['dt'], []).append(x)
    for d0, rs in bd.items():
        rs.sort(key=lambda z: z['turn20'])
        for k, z in enumerate(rs): z['tp'] = k/max(1, len(rs)-1)
    big = [x for x in sub if x['tp'] >= 0.75]
    print(stats(big, '成交金額前 25%'))
    vv = sorted(x['fi20_sh'] for x in big)
    if len(vv) > 40:
        print(stats([x for x in big if x['fi20_sh'] >= vv[int(len(vv)*0.5)]], '  + 外資買超高於中位數'))
        print(stats([x for x in big if x['fi20_sh'] < vv[int(len(vv)*0.5)]], '  + 外資買超低於中位數'))

# ---------------------------------------------------------------------------
# IMPORTANT: this subsample is CASE-CONTROL ENRICHED (328 surge stocks vs 260
# controls), so its P(+80%) is far above the population rate measured on the
# full universe. Only the CONTRASTS below are meaningful; the absolute levels
# are not population probabilities. Confidence intervals use the same cluster
# bootstrap as bootstrap.py -- resampling whole stocks, not stock-days.
import random
random.seed(11); B = 600

def cboot(sub, pred, label):
    sel = [x for x in sub if pred(x)]
    if len(sel) < 40: return f'{label:32} n={len(sel)} (too few)'
    bys = {}
    for x in sel: bys.setdefault(x['id'], []).append(x)
    ids = list(bys)
    meds, surg = [], []
    for _ in range(B):
        s = [x for k in (random.choice(ids) for _ in ids) for x in bys[k]]
        meds.append(st.median([x['fwd_end'] for x in s]))
        surg.append(sum(x['surge'] for x in s)/len(s))
    f = lambda a: (sorted(a)[int(B*.025)], sorted(a)[int(B*.975)])
    lm, hm = f(meds); ls, hs = f(surg)
    e0 = [x['fwd_end'] for x in sel]
    return (f'{label:32} n={len(sel):5} stocks={len(ids):4}  '
            f'med {st.median(e0)*100:+6.1f}% [{lm*100:+6.1f},{hm*100:+6.1f}]  '
            f'P(+80%) {sum(x["surge"] for x in sel)/len(sel)*100:4.1f}% [{ls*100:4.1f},{hs*100:4.1f}]')

for lbl, sub in [('2025H2', [x for x in use if x['dt'] < '2026-01-01']),
                 ('2026H1 out-of-sample', [x for x in use if x['dt'] >= '2026-01-01'])]:
    if len(sub) < 200: continue
    print(f'\n=== {lbl} — cluster bootstrap 95% CI (enriched sample: contrasts only) ===')
    bd = {}
    for x in sub: bd.setdefault(x['dt'], []).append(x)
    for d0, rs in bd.items():
        rs.sort(key=lambda z: z['turn20'])
        for k, z in enumerate(rs): z['tp'] = k/max(1, len(rs)-1)
    v = sorted(x['fi60_sh'] for x in sub)
    hi, lo = v[int(len(v)*.9)], v[int(len(v)*.1)]
    print(cboot(sub, lambda x: True, 'ALL (enriched base)'))
    print(cboot(sub, lambda x: x['fi60_sh'] >= hi, '外資 60 日買超前 10%'))
    print(cboot(sub, lambda x: x['fi60_sh'] <= lo, '外資 60 日買超後 10%'))
    print(cboot(sub, lambda x: x['it_flip'] == 1, '投信由賣轉買'))
    print(cboot(sub, lambda x: x['it_zero'] == 1, '投信 60 日零進出'))
    big = [x for x in sub if x['tp'] >= 0.75]
    vv = sorted(x['fi60_sh'] for x in big); mid = vv[len(vv)//2]
    print(cboot(sub, lambda x: x['tp'] >= 0.75, '成交金額前 25%'))
    print(cboot(sub, lambda x: x['tp'] >= 0.75 and x['fi60_sh'] >= mid, '  + 外資買超高於中位數'))
    print(cboot(sub, lambda x: x['tp'] >= 0.75 and x['fi60_sh'] < mid, '  + 外資買超低於中位數'))
