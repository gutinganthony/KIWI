"""The actual deliverable: a monthly watchlist that flags future wave leaders
BEFORE the move, scored on precision / recall / how much of the move is left.

Design guards:
  * every feature is converted to a WITHIN-DATE percentile, so thresholds adapt
    to the regime instead of being frozen at 2026 levels;
  * weights are fixed by hand (equal), not fitted -- with ~10 candidate features
    and a few hundred events, a fitted model would mostly memorise;
  * feature SELECTION uses 2022-2023 only; 2024-2025 is untouched until scoring.
"""
import json, os, sys, statistics as st, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in json.load(open(os.path.join(BASE, 'scan2.json')))]
TRAIN_END = '2024-01-01'

# ---- within-date percentile ranks -----------------------------------------
CAND = ['turn20', 'ret120', 'ret60', 'ret20', 'from52h', 'atrpct', 'accel',
        'fi60_sh', 'fi20_sh', 'it60_sh', 'mgpct', 'mg20', 'srat',
        'yoy3', 'rev_accel', 'yoy', 'mcap', 'squeeze', 'v20v60']
bydate = {}
for r in rows: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    for f in CAND:
        v = [x for x in rs if x.get(f) is not None]
        v.sort(key=lambda x: x[f])
        for k, x in enumerate(v): x['p_' + f] = k/max(1, len(v)-1)

train = [r for r in rows if r['dt'] < TRAIN_END]
test  = [r for r in rows if r['dt'] >= TRAIN_END]
br_tr = sum(r['big'] for r in train)/max(1, len(train))
br_te = sum(r['big'] for r in test)/max(1, len(test))
print(f'train {len(train)} obs, BIG rate {br_tr*100:.2f}%   |   '
      f'test {len(test)} obs, BIG rate {br_te*100:.2f}%\n')

print('--- univariate lift on TRAIN ONLY (top vs bottom decile of within-date rank) ---')
picks = []
for f in CAND:
    v = [x for x in train if x.get('p_'+f) is not None]
    if len(v) < 2000: continue
    hi = [x for x in v if x['p_'+f] >= 0.9]; lo = [x for x in v if x['p_'+f] <= 0.1]
    if not hi or not lo: continue
    rh = sum(x['big'] for x in hi)/len(hi); rl = sum(x['big'] for x in lo)/len(lo)
    picks.append((abs(rh-rl), f, rh, rl))
picks.sort(reverse=True)
for gap, f, rh, rl in picks:
    print(f'  {f:12} top-decile BIG {rh*100:5.1f}%   bottom-decile {rl*100:5.1f}%   '
          f'gap {(rh-rl)*100:+5.1f}pp   {"HI better" if rh>rl else "LO better"}')

SCORE = [(f, 1 if rh > rl else -1) for gap, f, rh, rl in picks[:5]]
print('\nscore features (chosen on train only):', SCORE)

for r in rows:
    tot = w = 0
    for f, sgn in SCORE:
        p = r.get('p_'+f)
        if p is None: continue
        tot += p if sgn > 0 else (1-p); w += 1
    r['score'] = tot/w if w >= 3 else None

# ---- monthly watchlist, out-of-sample -------------------------------------
def monthly(sub, topn):
    bym = {}
    for r in sub:
        if r.get('score') is None: continue
        bym.setdefault(r['dt'][:7], []).append(r)
    flagged = []
    for mo, rs in sorted(bym.items()):
        seen = {}
        for r in sorted(rs, key=lambda x: -x['score']):
            if r['id'] in seen: continue
            seen[r['id']] = r
            if len(seen) >= topn: break
        flagged.extend(seen.values())
    return flagged

print('\n--- OUT-OF-SAMPLE (2024-01 onward): monthly top-N watchlist ---')
print(f'{"topN":>6}{"picks":>7}{"hit%":>8}{"base%":>8}{"lift":>7}{"medMax":>9}{"medEnd":>9}{"medDD":>8}')
for topn in (10, 20, 30, 50):
    fl = monthly(test, topn)
    if not fl: continue
    hit = sum(x['big'] for x in fl)/len(fl)
    mx = st.median([x['fwd_max'] for x in fl]); en = st.median([x['fwd_end'] for x in fl])
    dd = st.median([x['fwd_min'] for x in fl])
    print(f'{topn:6}{len(fl):7}{hit*100:7.1f}%{br_te*100:7.1f}%{hit/br_te:6.2f}x'
          f'{mx*100:+8.1f}%{en*100:+8.1f}%{dd*100:+7.1f}%')

# ---- recall: of all wave leaders, how many were ever flagged first? --------
fl20 = monthly(test, 20)
flag_keys = {(x['id'], x['dt']) for x in fl20}
bigs = [x for x in test if x['big']]
bigstocks = {x['id'] for x in bigs}
flagstocks = {x['id'] for x in fl20}
print(f'\nrecall: {len(bigstocks & flagstocks)}/{len(bigstocks)} '
      f'({len(bigstocks & flagstocks)/max(1,len(bigstocks))*100:.0f}%) of wave-leader stocks '
      f'appeared on some monthly top-20 list')

print('\n--- named check: when did the known names first appear on a top-20 list? ---')
first = {}
for x in sorted(fl20, key=lambda z: z['dt']):
    first.setdefault(x['id'], x)
WATCH = ['2059', '2327', '2344', '2337', '3260', '3006', '2408', '4967', '3661', '6669']
for sid in WATCH:
    x = first.get(sid)
    if x:
        print(f"  {sid} {x['name'][:8]:9} first flagged {x['dt']}  px {x['px']:>8.1f}  "
              f"-> next 250d max {x['fwd_max']*100:+6.0f}%  BIG={x['big']}")
    else:
        anyrow = next((r for r in test if r['id'] == sid), None)
        print(f"  {sid} {(anyrow['name'][:8] if anyrow else '?'):9} never flagged")
