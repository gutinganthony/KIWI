"""Round 1 selected features by hit-rate gap alone, which structurally favours
high-volatility names: they double often AND halve often. Re-score every feature
on the whole return distribution -- median outcome and drawdown, not just P(BIG).

Then test the pattern the actual wave leaders shared before their runs:
liquid enough to matter, but momentum near the FLOOR (they had been going
nowhere), low volatility, no volume spike."""
import json, os, statistics as st
BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'scan2.json')))
CAND = ['turn20','ret120','ret60','ret20','from52h','atrpct','accel','squeeze','v20v60']
bydate = {}
for r in rows: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    for f in CAND:
        v = [x for x in rs if x.get(f) is not None]
        v.sort(key=lambda x: x[f])
        for k, x in enumerate(v): x['p_'+f] = k/max(1, len(v)-1)

TRAIN = [r for r in rows if r['dt'] < '2024-01-01']
TEST  = [r for r in rows if r['dt'] >= '2024-01-01']

def line(rs, label):
    if len(rs) < 100: return f'{label:30} n={len(rs)} (too few)'
    e = [x['fwd_end'] for x in rs]; d = [x['fwd_min'] for x in rs]
    return (f'{label:30} n={len(rs):6}  BIG {sum(x["big"] for x in rs)/len(rs)*100:5.1f}%  '
            f'medEnd {st.median(e)*100:+7.1f}%  win {sum(1 for x in e if x>0)/len(e)*100:5.1f}%  '
            f'medDD {st.median(d)*100:+7.1f}%')

print('=== TRAIN 2022-2023: each feature by decile, judged on the WHOLE distribution ===')
for f in CAND:
    v = [x for x in TRAIN if x.get('p_'+f) is not None]
    if len(v) < 5000: continue
    print(f'-- {f}')
    for q0, q1, lb in [(0.0,0.2,'bottom 20%'), (0.4,0.6,'middle'), (0.8,1.01,'top 20%')]:
        sel = [x for x in v if q0 <= x['p_'+f] < q1]
        print('   ' + line(sel, lb))

print('\n=== 2D grid: turnover percentile x 120d-momentum percentile (TRAIN) ===')
hdr = 'turn / mom'
print(f'{hdr:>12}' + ''.join(f'{lb:>22}' for lb in ['mom low 0-30%','mom mid 30-70%','mom high 70-100%']))
for t0, t1, tl in [(0.0,0.4,'turn 0-40%'), (0.4,0.7,'turn 40-70%'), (0.7,0.9,'turn 70-90%'), (0.9,1.01,'turn 90-100%')]:
    cells = []
    for m0, m1 in [(0.0,0.3),(0.3,0.7),(0.7,1.01)]:
        sel = [x for x in TRAIN if x.get('p_turn20') is not None and x.get('p_ret120') is not None
               and t0 <= x['p_turn20'] < t1 and m0 <= x['p_ret120'] < m1]
        if len(sel) < 100: cells.append('        --            '); continue
        e = [x['fwd_end'] for x in sel]
        cells.append(f'  BIG{sum(x["big"] for x in sel)/len(sel)*100:5.1f}% end{st.median(e)*100:+6.1f}%')
    print(f'{tl:>12}' + ''.join(f'{c:>22}' for c in cells))

print('\n=== the wave-leader pattern, TRAIN then TEST ===')
COILED = lambda x: (x.get('p_turn20') is not None and x['p_turn20'] >= 0.60
                    and x.get('p_ret120') is not None and x['p_ret120'] <= 0.35
                    and x.get('p_atrpct') is not None and x['p_atrpct'] <= 0.60
                    and x.get('p_accel') is not None and x['p_accel'] <= 0.70)
CHASE = lambda x: (x.get('p_turn20') is not None and x['p_turn20'] >= 0.60
                   and x.get('p_ret120') is not None and x['p_ret120'] >= 0.80)
for lbl, sub in [('TRAIN 2022-23', TRAIN), ('TEST 2024-25', TEST)]:
    print(f'-- {lbl}')
    print('   ' + line(sub, 'all'))
    print('   ' + line([x for x in sub if COILED(x)], '盤久 (液性佳+動能低+低波動)'))
    print('   ' + line([x for x in sub if CHASE(x)], '追強 (液性佳+動能高)'))
