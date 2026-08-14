"""Which point-in-time features actually discriminate future +80% surges?"""
import json, os, math, statistics as st
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'scan.json')))
SPLIT = '2026-01-01'
train = [r for r in rows if r['dt'] < SPLIT]
test  = [r for r in rows if r['dt'] >= SPLIT]

FEATS = ['ret20','ret60','ret120','from52h','above52l','atrpct','squeeze','v5v60','v20v60',
         'turn20','lu20','mcap','fi20pct','it20pct','fi60pct','it60pct','itdays60',
         'mg20','mgpct','srat','yoy','yoy3','mom']

def base_rate(rs): 
    return sum(r['surge'] for r in rs)/len(rs) if rs else 0

def deciles(rs, f, nb=10):
    vals = [(r[f], r['surge']) for r in rs if r.get(f) is not None]
    if len(vals) < 500: return None
    vals.sort(key=lambda x: x[0])
    n = len(vals); out = []
    for b in range(nb):
        chunk = vals[n*b//nb:n*(b+1)//nb]
        if not chunk: continue
        out.append((chunk[0][0], chunk[-1][0], len(chunk),
                    sum(x[1] for x in chunk)/len(chunk)))
    return out

print('='*72)
br_all, br_tr, br_te = base_rate(rows), base_rate(train), base_rate(test)
print(f'obs {len(rows)}  base surge rate {br_all*100:.2f}%   '
      f'train {len(train)} ({br_tr*100:.2f}%)  test {len(test)} ({br_te*100:.2f}%)')
print('='*72)

# rank features by best-decile lift on TRAIN only
rank = []
for f in FEATS:
    d = deciles(train, f)
    if not d: continue
    rates = [x[3] for x in d]
    top = max(rates); bot = min(rates)
    lift = top/br_tr if br_tr else 0
    # is it monotone-ish? correlation between decile index and rate
    idxs = list(range(len(rates)))
    mu_i = sum(idxs)/len(idxs); mu_r = sum(rates)/len(rates)
    num = sum((i-mu_i)*(r-mu_r) for i, r in zip(idxs, rates))
    den = math.sqrt(sum((i-mu_i)**2 for i in idxs)*sum((r-mu_r)**2 for r in rates)) or 1
    rank.append((lift, f, d, num/den, top, bot))
rank.sort(reverse=True)

print(f"\n{'feature':10}{'topLift':>8}{'monot':>7}   decile surge-rate % (low -> high)")
for lift, f, d, mono, top, bot in rank:
    bars = ' '.join(f'{x[3]*100:4.1f}' for x in d)
    print(f'{f:10}{lift:7.2f}x{mono:7.2f}   {bars}')

print('\n' + '='*72)
print('TOP-5 FEATURES: train-fitted cutoffs, validated out-of-sample on test')
print('='*72)
for lift, f, d, mono, top, bot in rank[:8]:
    # pick the direction & threshold from train's best decile
    best = max(d, key=lambda x: x[3])
    hi_side = d.index(best) >= len(d)//2
    thr = best[0] if hi_side else best[1]
    def sel(rs):
        v = [r for r in rs if r.get(f) is not None]
        s = [r for r in v if (r[f] >= thr if hi_side else r[f] <= thr)]
        return s, v
    s_tr, v_tr = sel(train); s_te, v_te = sel(test)
    if not s_te: continue
    op = '>=' if hi_side else '<='
    print(f'{f:10} {op}{thr:>10.4g} | train {base_rate(s_tr)*100:5.2f}% (n={len(s_tr)}) '
          f'| TEST {base_rate(s_te)*100:5.2f}% (n={len(s_te)}) vs base {br_te*100:.2f}% '
          f'=> lift {base_rate(s_te)/br_te if br_te else 0:.2f}x')
