"""Inside the laggard bucket the only thing that separated future wave leaders
was turnover -- and both are price features, so this screen can be evaluated on
the FULL 2,162-stock universe without the enriched-sample bias.

Two lanes, deliberately non-overlapping:
  lane A (leaders)  : near the 52-week high + heavy turnover
  lane B (laggards) : >=30% below the 52-week high + heavy turnover
"""
import json, os, statistics as st, random
BASE = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in json.load(open(os.path.join(BASE, 'scan2.json'))) if not r['id'].startswith('0')]
bydate = {}
for r in rows: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    for f in ('turn20', 'from52h'):
        v = [x for x in rs if x.get(f) is not None]
        v.sort(key=lambda x: x[f])
        for k, x in enumerate(v): x['p_'+f] = k/max(1, len(v)-1)
P = lambda x, f: (x.get('p_'+f) if x.get('p_'+f) is not None else 0.0)

LANE_A = lambda x: P(x,'from52h') >= 0.80 and P(x,'turn20') >= 0.70
LANE_B = lambda x: x.get('from52h') is not None and x['from52h'] <= -0.30 and P(x,'turn20') >= 0.70

random.seed(91); B = 400
def cb(sel, label, base=None):
    if len(sel) < 80: return f'{label:30} n={len(sel)} (樣本不足)'
    bys = {}
    for x in sel: bys.setdefault(x['id'], []).append(x)
    ids = list(bys); bigs = []; meds = []
    for _ in range(B):
        s = [x for k in (random.choice(ids) for _ in ids) for x in bys[k]]
        bigs.append(sum(x['big'] for x in s)/len(s)); meds.append(st.median([x['fwd_end'] for x in s]))
    q = lambda a: (sorted(a)[int(B*.025)], sorted(a)[int(B*.975)])
    lb, hb = q(bigs); lm, hm = q(meds)
    b0 = sum(x['big'] for x in sel)/len(sel)
    tag = '  ***' if (base is not None and lb > base) else ''
    return (f'{label:30} n={len(sel):6} stk={len(ids):4}  BIG {b0*100:5.1f}% [{lb*100:4.1f},{hb*100:4.1f}]  '
            f'medEnd {st.median([x["fwd_end"] for x in sel])*100:+7.1f}% [{lm*100:+6.1f},{hm*100:+6.1f}]  '
            f'medDD {st.median([x["fwd_min"] for x in sel])*100:+6.1f}%{tag}')

for pn, a, b in [('TRAIN 2022-2023', '2022-01-01', '2024-01-01'),
                 ('TEST 2024-2025 (out-of-sample)', '2024-01-01', '2026-01-01')]:
    sub = [x for x in rows if a <= x['dt'] < b]
    base = sum(x['big'] for x in sub)/len(sub)
    print(f'\n### {pn} — 全市場 {len({x["id"] for x in sub})} 檔')
    print(cb(sub, '【全市場基準】'))
    print(cb([x for x in sub if LANE_A(x)], 'A 高檔強勢 (距高前20%+量前30%)', base))
    print(cb([x for x in sub if LANE_B(x)], 'B 落後放量 (距高-30%以下+量前30%)', base))
    print(cb([x for x in sub if x.get('from52h') is not None and x['from52h'] <= -0.30
              and P(x,'turn20') < 0.70], '  對照: 落後但量小', base))

# monthly watchlist combining both lanes, and the named check
TEST = [x for x in rows if x['dt'] >= '2024-01-01']
baseT = sum(x['big'] for x in TEST)/len(TEST)
def monthly(pred, key, topn):
    bym = {}
    for r in TEST:
        if pred(r): bym.setdefault(r['dt'][:7], []).append(r)
    out = []
    for mo, rs in sorted(bym.items()):
        seen = {}
        for r in sorted(rs, key=key):
            if r['id'] in seen: continue
            seen[r['id']] = r
            if len(seen) >= topn: break
        out.extend(seen.values())
    return out
flA = monthly(LANE_A, lambda x: -(P(x,'from52h')+P(x,'turn20')), 20)
flB = monthly(LANE_B, lambda x: -P(x,'turn20'), 20)
print('\n### 每月各取 20 名的兩線清單（樣本外 2024-01 起）')
for nm, fl in [('A 高檔強勢', flA), ('B 落後放量', flB), ('A+B 合併', flA+flB)]:
    e = [x['fwd_end'] for x in fl]
    print(f'  {nm:10} picks {len(fl):5}  BIG {sum(x["big"] for x in fl)/len(fl)*100:5.1f}% (基準 {baseT*100:.1f}%)  '
          f'medEnd {st.median(e)*100:+7.1f}%  平均 {sum(e)/len(e)*100:+7.1f}%  '
          f'medDD {st.median([x["fwd_min"] for x in fl])*100:+6.1f}%')
bigst = {x['id'] for x in TEST if x['big']}
for nm, fl in [('A', flA), ('B', flB), ('A+B', flA+flB)]:
    got = {x['id'] for x in fl} & bigst
    print(f'  涵蓋率 {nm}: {len(got)}/{len(bigst)} = {len(got)/len(bigst)*100:.0f}%')
print('\n### 點名驗證（首次上榜）')
firstA = {}; firstB = {}
for x in sorted(flA, key=lambda z: z['dt']): firstA.setdefault(x['id'], x)
for x in sorted(flB, key=lambda z: z['dt']): firstB.setdefault(x['id'], x)
for sid, nm in [('2059','川湖'),('2327','國巨'),('2344','華邦電'),('2337','旺宏'),('2408','南亞科'),
                ('3260','威剛'),('4967','十銓'),('3006','晶豪科'),('8299','群聯'),('3661','世芯'),('6669','緯穎')]:
    a = firstA.get(sid); b = firstB.get(sid)
    parts = []
    if a: parts.append(f"A {a['dt']} @{a['px']:.0f} →{a['fwd_max']*100:+.0f}%")
    if b: parts.append(f"B {b['dt']} @{b['px']:.0f} →{b['fwd_max']*100:+.0f}%")
    print(f"  {nm:5} " + ('  |  '.join(parts) if parts else '未上榜'))
