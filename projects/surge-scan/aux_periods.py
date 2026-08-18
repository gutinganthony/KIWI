"""Margin and revenue features, tested across five regimes including the 2022
bear. Sample is the enriched aux set (400 wave leaders + 250 controls), so read
CONTRASTS against the period's own base only -- the absolute BIG rate here is
far above the market's."""
import json, os, statistics as st, random
BASE = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in json.load(open(os.path.join(BASE, 'scan2.json')))
        if any(r.get(f) is not None for f in ('mgpct', 'yoy3'))]
print(f'aux-covered observations {len(rows)}  stocks {len({r["id"] for r in rows})}')
bydate = {}
for r in rows: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    for f in ('turn20', 'from52h'):
        v = [x for x in rs if x.get(f) is not None]
        v.sort(key=lambda x: x[f])
        for k, x in enumerate(v): x['p_'+f] = k/max(1, len(v)-1)

random.seed(77); B = 400
def cb(sel, label, base=None):
    if len(sel) < 60: return f'{label:28} n={len(sel)} (樣本不足)'
    bys = {}
    for x in sel: bys.setdefault(x['id'], []).append(x)
    ids = list(bys); bigs = []
    for _ in range(B):
        s = [x for k in (random.choice(ids) for _ in ids) for x in bys[k]]
        bigs.append(sum(x['big'] for x in s)/len(s))
    lo, hi = sorted(bigs)[int(B*.025)], sorted(bigs)[int(B*.975)]
    b0 = sum(x['big'] for x in sel)/len(sel)
    tag = '  ***' if (base is not None and lo > base) else ('  --' if (base is not None and hi < base) else '')
    return (f'{label:28} n={len(sel):5} stk={len(ids):4}  BIG {b0*100:5.1f}% [{lo*100:4.1f},{hi*100:4.1f}]  '
            f'medEnd {st.median([x["fwd_end"] for x in sel])*100:+7.1f}%{tag}')

TESTS = [
 ('營收 3M動能 >12M +10pp', lambda x: x.get('rev_accel') is not None and x['rev_accel'] > 0.10),
 ('營收 3M YoY >+30%',     lambda x: x.get('yoy3') is not None and x['yoy3'] >= 0.30),
 ('營收 3M YoY <-10%',     lambda x: x.get('yoy3') is not None and x['yoy3'] <= -0.10),
 ('營收 MoM >+20%',        lambda x: x.get('mom') is not None and x['mom'] >= 0.20),
 ('融資 20日 -10%',        lambda x: x.get('mg20') is not None and x['mg20'] <= -0.10),
 ('融資 20日 +20%',        lambda x: x.get('mg20') is not None and x['mg20'] >= 0.20),
 ('融資佔股本 <2%',         lambda x: x.get('mgpct') is not None and x['mgpct'] < 2),
 ('融資佔股本 >6%',         lambda x: x.get('mgpct') is not None and x['mgpct'] > 6),
 ('券資比 >5%',            lambda x: x.get('srat') is not None and x['srat'] >= 5),
]
PERIODS = [('2022 空頭', '2022-01-01', '2023-01-01'), ('2023 復甦', '2023-01-01', '2024-01-01'),
           ('2024', '2024-01-01', '2025-01-01'), ('2025H1', '2025-01-01', '2025-09-01')]
for pn, a, b in PERIODS:
    sub = [x for x in rows if a <= x['dt'] < b]
    if len(sub) < 400: print(f'\n### {pn}: n={len(sub)} 樣本不足'); continue
    base = sum(x['big'] for x in sub)/len(sub)
    print(f'\n### {pn}  (*** 顯著優於該期基準, -- 顯著劣於)')
    print(cb(sub, '【該期基準】'))
    for lbl, f in TESTS: print(cb([x for x in sub if f(x)], lbl, base=base))
