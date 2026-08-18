"""Two screens failed to flag the named winners. Before trying a third, look at
what those winners actually looked like at every point they were about to double
-- if their profiles contradict each other, no single price screen can hold them."""
import json, os, statistics as st
BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'scan2.json')))
CAND = ['turn20','ret120','ret60','from52h','atrpct','accel','squeeze']
bydate = {}
for r in rows: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    for f in CAND:
        v = [x for x in rs if x.get(f) is not None]
        v.sort(key=lambda x: x[f])
        for k, x in enumerate(v): x['p_'+f] = k/max(1, len(v)-1)
P = lambda x, f: (x.get('p_'+f) or 0)

NAMED = [('2059','川湖'),('2327','國巨'),('2344','華邦電'),('2337','旺宏'),
         ('2408','南亞科'),('3260','威剛'),('4967','十銓'),('3006','晶豪科'),
         ('8299','群聯'),('3661','世芯'),('6669','緯穎')]
print('=== every BIG entry point of the named winners (percentiles within that day) ===')
print(f"{'':6}{'date':12}{'turn':>6}{'r120':>6}{'f52h':>6}{'atr':>6}{'accel':>6}{'fwdmax':>8}")
prof = []
for sid, nm in NAMED:
    hits = sorted([r for r in rows if r['id'] == sid and r['big']], key=lambda x: x['dt'])
    if not hits: print(f'{nm:6} (no BIG entry in window)'); continue
    show = [hits[0]] + ([hits[len(hits)//2]] if len(hits) > 2 else []) + ([hits[-1]] if len(hits) > 1 else [])
    for r in show:
        prof.append(r)
        print(f"{nm:6}{r['dt']:12}{P(r,'turn20')*100:5.0f}%{P(r,'ret120')*100:5.0f}%"
              f"{P(r,'from52h')*100:5.0f}%{P(r,'atrpct')*100:5.0f}%{P(r,'accel')*100:5.0f}%"
              f"{r['fwd_max']*100:+7.0f}%")
print(f"\nspread of these winners: from52h pct min {min(P(r,'from52h') for r in prof)*100:.0f}% "
      f"max {max(P(r,'from52h') for r in prof)*100:.0f}%   |   ret120 pct min "
      f"{min(P(r,'ret120') for r in prof)*100:.0f}% max {max(P(r,'ret120') for r in prof)*100:.0f}%")

TRAIN = [r for r in rows if r['dt'] < '2024-01-01']; TEST = [r for r in rows if r['dt'] >= '2024-01-01']
def line(rs, label):
    if len(rs) < 100: return f'{label:30} n={len(rs)} (too few)'
    e = [x['fwd_end'] for x in rs]
    return (f'{label:30} n={len(rs):6}  BIG {sum(x["big"] for x in rs)/len(rs)*100:5.1f}%  '
            f'medEnd {st.median(e)*100:+7.1f}%  win {sum(1 for x in e if x>0)/len(e)*100:5.1f}%  '
            f'medDD {st.median([x["fwd_min"] for x in rs])*100:+7.1f}%')
print('\n=== the one combination that improved every metric in BOTH halves ===')
F = lambda x: P(x,'from52h') >= 0.80 and P(x,'turn20') >= 0.70
for lbl, sub in [('TRAIN', TRAIN), ('TEST', TEST)]:
    print(f'-- {lbl}'); print('   ' + line(sub, '基準')); print('   ' + line([x for x in sub if F(x)], '距高前20% + 成交金額前30%'))
for r in rows: r['s3'] = P(r,'from52h') + P(r,'turn20')
def monthly(sub, topn):
    bym = {}
    for r in sub: bym.setdefault(r['dt'][:7], []).append(r)
    out = []
    for mo, rs in sorted(bym.items()):
        seen = {}
        for r in sorted(rs, key=lambda x: -x['s3']):
            if r['id'] in seen: continue
            seen[r['id']] = r
            if len(seen) >= topn: break
        out.extend(seen.values())
    return out
print('\n=== watchlist on 距高+成交金額, out-of-sample ===')
base = sum(x['big'] for x in TEST)/len(TEST)
for topn in (20, 40):
    fl = monthly(TEST, topn); e = [x['fwd_end'] for x in fl]
    print(f'  top{topn}: picks {len(fl)}  BIG {sum(x["big"] for x in fl)/len(fl)*100:.1f}% (base {base*100:.1f}%)  '
          f'medEnd {st.median(e)*100:+.1f}%  win {sum(1 for x in e if x>0)/len(e)*100:.1f}%  '
          f'medDD {st.median([x["fwd_min"] for x in fl])*100:+.1f}%')
fl = monthly(TEST, 40); first = {}
for x in sorted(fl, key=lambda z: z['dt']): first.setdefault(x['id'], x)
bigst = {x['id'] for x in TEST if x['big']}
print(f"  recall {len({x['id'] for x in fl} & bigst)}/{len(bigst)} = {len({x['id'] for x in fl} & bigst)/len(bigst)*100:.0f}%")
print('  named:', ', '.join(f"{nm}={'✓'+first[sid]['dt'][:7] if sid in first else '✗'}" for sid, nm in NAMED))
