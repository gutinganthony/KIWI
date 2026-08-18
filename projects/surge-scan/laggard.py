"""The question the whole extension exists to answer.

Price/volume screening caught 39% of wave leaders and structurally cannot catch
the rest: the DRAM/NAND names all started from the 52-week-low end, a bucket
whose base rate is well below average. So the real test is not "does margin or
revenue predict anything" -- it is:

    INSIDE the laggard bucket, do margin/revenue separate the ones that turn
    from the ones that keep rotting?

If yes, the gap is closable with free data. If no, the honest answer is that the
turn is only visible in industry pricing, which is behind a paywall.
"""
import json, os, statistics as st, random
BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'scan2.json')))
AUX = ['mgpct', 'mg20', 'srat', 'yoy', 'yoy3', 'rev_accel', 'mom']
have = [r for r in rows if any(r.get(f) is not None for f in AUX)]
print(f'observations with aux features: {len(have)} / {len(rows)}  stocks {len({r["id"] for r in have})}')

CAND = ['turn20', 'from52h', 'ret120', 'atrpct'] + AUX
bydate = {}
for r in have: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    for f in CAND:
        v = [x for x in rs if x.get(f) is not None]
        v.sort(key=lambda x: x[f])
        for k, x in enumerate(v): x['p_'+f] = k/max(1, len(v)-1)

# laggard = bottom third on distance-from-52w-high, computed within the aux sample
LAG = lambda x: x.get('from52h') is not None and x['from52h'] <= -0.30
lag = [x for x in have if LAG(x)]
print(f'laggard observations (>=30% below 52w high): {len(lag)}  '
      f'stocks {len({x["id"] for x in lag})}  BIG rate {sum(x["big"] for x in lag)/max(1,len(lag))*100:.1f}%'
      f'  (non-laggard {sum(x["big"] for x in have if not LAG(x))/max(1,len([x for x in have if not LAG(x)]))*100:.1f}%)')

random.seed(31); B = 400
def cb(sel, label, base=None):
    if len(sel) < 60: return f'{label:34} n={len(sel)} (too few)'
    bys = {}
    for x in sel: bys.setdefault(x['id'], []).append(x)
    ids = list(bys); bigs = []; meds = []
    for _ in range(B):
        s = [x for k in (random.choice(ids) for _ in ids) for x in bys[k]]
        bigs.append(sum(x['big'] for x in s)/len(s))
        meds.append(st.median([x['fwd_end'] for x in s]))
    q = lambda a: (sorted(a)[int(B*.025)], sorted(a)[int(B*.975)])
    lb, hb = q(bigs); lm, hm = q(meds)
    b0 = sum(x['big'] for x in sel)/len(sel)
    tag = ''
    if base is not None: tag = '  ***' if lb > base else ('  --' if hb < base else '')
    return (f'{label:34} n={len(sel):5} stk={len(ids):4}  BIG {b0*100:5.1f}% [{lb*100:4.1f},{hb*100:4.1f}]  '
            f'medEnd {st.median([x["fwd_end"] for x in sel])*100:+7.1f}% [{lm*100:+6.1f},{hm*100:+6.1f}]{tag}')

TESTS = [
 ('營收 3M動能 > 12M +10pp',  lambda x: x.get('rev_accel') is not None and x['rev_accel'] > 0.10),
 ('營收 3M動能 < 12M -10pp',  lambda x: x.get('rev_accel') is not None and x['rev_accel'] < -0.10),
 ('營收 3M YoY > +30%',       lambda x: x.get('yoy3') is not None and x['yoy3'] >= 0.30),
 ('營收 3M YoY < -10%',       lambda x: x.get('yoy3') is not None and x['yoy3'] <= -0.10),
 ('融資 20日 -10% 以上',       lambda x: x.get('mg20') is not None and x['mg20'] <= -0.10),
 ('融資 20日 +20% 以上',       lambda x: x.get('mg20') is not None and x['mg20'] >= 0.20),
 ('融資佔股本 < 2%',           lambda x: x.get('mgpct') is not None and x['mgpct'] < 2),
 ('融資佔股本 > 6%',           lambda x: x.get('mgpct') is not None and x['mgpct'] > 6),
 ('券資比 > 5%',              lambda x: x.get('srat') is not None and x['srat'] >= 5),
 ('成交金額前 30%',            lambda x: x.get('p_turn20') is not None and x['p_turn20'] >= 0.70),
 ('營收動能正 + 成交金額前30%',  lambda x: x.get('rev_accel') is not None and x['rev_accel'] > 0.10
                                      and x.get('p_turn20') is not None and x['p_turn20'] >= 0.70),
 ('營收動能正 + 融資減少',       lambda x: x.get('rev_accel') is not None and x['rev_accel'] > 0.10
                                      and x.get('mg20') is not None and x['mg20'] <= -0.05),
]
for pname, pf in [('TRAIN 2022-2023', lambda d: d < '2024-01-01'),
                  ('TEST 2024-2025 (out-of-sample)', lambda d: d >= '2024-01-01')]:
    sub = [x for x in lag if pf(x['dt'])]
    if len(sub) < 300:
        print(f'\n### {pname}: n={len(sub)} too few'); continue
    base = sum(x['big'] for x in sub)/len(sub)
    print(f'\n### {pname} — laggard bucket only   (*** 顯著優於落後股基準, -- 顯著劣於)')
    print(cb(sub, '【落後股基準】'))
    for lbl, f in TESTS: print(cb([x for x in sub if f(x)], lbl, base=base))
