"""Only one feature improved hit rate, median return, win rate AND drawdown at
the same time: proximity to the 52-week high. Test what it combines with, then
rebuild the watchlist around whatever survives on TRAIN and re-run the named check."""
import json, os, statistics as st
BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'scan2.json')))
CAND = ['turn20','ret120','ret60','from52h','atrpct','accel','squeeze','v20v60']
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
    if len(rs) < 100: return f'{label:34} n={len(rs)} (too few)'
    e = [x['fwd_end'] for x in rs]; d = [x['fwd_min'] for x in rs]
    return (f'{label:34} n={len(rs):6}  BIG {sum(x["big"] for x in rs)/len(rs)*100:5.1f}%  '
            f'medEnd {st.median(e)*100:+7.1f}%  win {sum(1 for x in e if x>0)/len(e)*100:5.1f}%  '
            f'medDD {st.median(d)*100:+7.1f}%')

P = lambda x, f: x.get('p_'+f)
COMBOS = [
 ('距高前20%',                  lambda x: P(x,'from52h') is not None and P(x,'from52h')>=0.80),
 ('距高前20% + 低波動(<50%)',    lambda x: P(x,'from52h') is not None and P(x,'from52h')>=0.80
                                          and P(x,'atrpct') is not None and P(x,'atrpct')<=0.50),
 ('距高前20% + 高波動(>70%)',    lambda x: P(x,'from52h') is not None and P(x,'from52h')>=0.80
                                          and P(x,'atrpct') is not None and P(x,'atrpct')>=0.70),
 ('距高前20% + 動能前30%',       lambda x: P(x,'from52h') is not None and P(x,'from52h')>=0.80
                                          and P(x,'ret120') is not None and P(x,'ret120')>=0.70),
 ('距高前20% + 未爆量(<70%)',    lambda x: P(x,'from52h') is not None and P(x,'from52h')>=0.80
                                          and P(x,'accel') is not None and P(x,'accel')<=0.70),
 ('距高前20% + 低波動 + 未爆量',  lambda x: P(x,'from52h') is not None and P(x,'from52h')>=0.80
                                          and P(x,'atrpct') is not None and P(x,'atrpct')<=0.50
                                          and P(x,'accel') is not None and P(x,'accel')<=0.70),
 ('距高前20% + 成交金額前30%',    lambda x: P(x,'from52h') is not None and P(x,'from52h')>=0.80
                                          and P(x,'turn20') is not None and P(x,'turn20')>=0.70),
]
for lbl, sub in [('TRAIN 2022-23', TRAIN), ('TEST 2024-25 (out-of-sample)', TEST)]:
    print(f'=== {lbl} ===')
    print(line(sub, '全體基準'))
    for nm, f in COMBOS: print(line([x for x in sub if f(x)], nm))
    print()

# rebuild the watchlist on the combination that held up, and re-run the named check
BEST = lambda x: (P(x,'from52h') is not None and P(x,'from52h')>=0.80
                  and P(x,'atrpct') is not None and P(x,'atrpct')<=0.50
                  and P(x,'accel') is not None and P(x,'accel')<=0.70)
for r in rows:
    r['score2'] = (P(r,'from52h') or 0) - 0.5*(P(r,'atrpct') or 0.5) - 0.3*(P(r,'accel') or 0.5)
def monthly(sub, topn, keyf='score2', filt=None):
    bym = {}
    for r in sub:
        if filt and not filt(r): continue
        bym.setdefault(r['dt'][:7], []).append(r)
    out = []
    for mo, rs in sorted(bym.items()):
        seen = {}
        for r in sorted(rs, key=lambda x: -x[keyf]):
            if r['id'] in seen: continue
            seen[r['id']] = r
            if len(seen) >= topn: break
        out.extend(seen.values())
    return out
print('=== rebuilt watchlist, OUT-OF-SAMPLE 2024-01 onward ===')
base = sum(x['big'] for x in TEST)/len(TEST)
for topn in (10, 20, 30):
    fl = monthly(TEST, topn, filt=BEST)
    if len(fl) < 50: continue
    e = [x['fwd_end'] for x in fl]
    print(f'  top{topn:3}  picks {len(fl):5}  BIG {sum(x["big"] for x in fl)/len(fl)*100:5.1f}% '
          f'(base {base*100:.1f}%)  medEnd {st.median(e)*100:+7.1f}%  '
          f'win {sum(1 for x in e if x>0)/len(e)*100:5.1f}%  medDD {st.median([x["fwd_min"] for x in fl])*100:+7.1f}%')
fl20 = monthly(TEST, 20, filt=BEST)
bigst = {x['id'] for x in TEST if x['big']}; fst = {x['id'] for x in fl20}
print(f'  recall {len(bigst & fst)}/{len(bigst)} = {len(bigst & fst)/max(1,len(bigst))*100:.0f}%')
first = {}
for x in sorted(fl20, key=lambda z: z['dt']): first.setdefault(x['id'], x)
print('\n=== named check ===')
for sid, nm in [('2059','川湖'),('2327','國巨'),('2344','華邦電'),('2337','旺宏'),
                ('2408','南亞科'),('3260','威剛'),('4967','十銓'),('3006','晶豪科'),
                ('8299','群聯'),('3661','世芯'),('6669','緯穎'),('2454','聯發科')]:
    x = first.get(sid)
    print(f"  {nm:5} " + (f"flagged {x['dt']}  px {x['px']:>8.1f} -> 250d max {x['fwd_max']*100:+6.0f}%  BIG={x['big']}"
                          if x else 'never flagged'))
