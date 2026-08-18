"""Lane B beat the market in 2024-25 and lagged it in 2022-23. Before treating it
as a rule, check whether the 2024-25 result is one sector's cycle wearing a
screen's clothes: split by half-year, and look at what the hits actually were."""
import json, os, statistics as st, random
from collections import Counter
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
LANE_B = lambda x: x.get('from52h') is not None and x['from52h'] <= -0.30 and P(x,'turn20') >= 0.70

def bk(d):
    y, m = int(d[:4]), int(d[5:7]); return f'{y}H{1 if m<=6 else 2}'
buckets = {}
for r in rows: buckets.setdefault(bk(r['dt']), []).append(r)

print(f"{'期間':10}{'基準BIG':>9}{'B線BIG':>9}{'倍數':>7}{'基準medEnd':>12}{'B線medEnd':>11}{'B線n':>8}")
for k in sorted(buckets):
    sub = buckets[k]
    b = [x for x in sub if LANE_B(x)]
    if len(b) < 80: print(f'{k:10}{"":>9}{"樣本不足 n=" + str(len(b)):>25}'); continue
    br = sum(x['big'] for x in sub)/len(sub); lr = sum(x['big'] for x in b)/len(b)
    print(f'{k:10}{br*100:8.1f}%{lr*100:8.1f}%{lr/br if br else 0:6.2f}x'
          f'{st.median([x["fwd_end"] for x in sub])*100:+11.1f}%'
          f'{st.median([x["fwd_end"] for x in b])*100:+10.1f}%{len(b):8}')

print('\n=== 2024-2025 B 線命中者的產業構成 ===')
hits = [x for x in rows if x['dt'] >= '2024-01-01' and LANE_B(x) and x['big']]
print(f'命中觀察值 {len(hits)}，涉及 {len({x["id"] for x in hits})} 檔')
ind = Counter(x['ind'] or '?' for x in hits)
for k, v in ind.most_common(8): print(f'   {k:14} {v:5} ({v/len(hits)*100:.0f}%)')
print('\n   前 12 檔（依命中觀察值數）:',
      ', '.join(f'{n}' for (i, n), c in Counter((x['id'], x['name']) for x in hits).most_common(12)))

print('\n=== 拿掉半導體/電子零組件後，B 線還成立嗎？（2024-2025）===')
sub = [x for x in rows if x['dt'] >= '2024-01-01']
SEMI = ('半導體', '電子零組件', '電腦及週邊', '光電')
non = [x for x in sub if not any(s in (x['ind'] or '') for s in SEMI)]
nb = [x for x in non if LANE_B(x)]
random.seed(5); B = 400
def ci(sel):
    bys = {}
    for x in sel: bys.setdefault(x['id'], []).append(x)
    ids = list(bys); a = []
    for _ in range(B):
        s = [x for k in (random.choice(ids) for _ in ids) for x in bys[k]]
        a.append(sum(x['big'] for x in s)/len(s))
    return sorted(a)[int(B*.025)], sorted(a)[int(B*.975)]
for lbl, base_set, lane_set in [('全部產業', sub, [x for x in sub if LANE_B(x)]),
                                ('排除半導體/零組件/電腦/光電', non, nb)]:
    if len(lane_set) < 80: print(f'  {lbl}: B 線 n={len(lane_set)} 樣本不足'); continue
    br = sum(x['big'] for x in base_set)/len(base_set)
    lr = sum(x['big'] for x in lane_set)/len(lane_set)
    lo, hi = ci(lane_set)
    print(f'  {lbl:28} 基準 {br*100:5.1f}%  B線 {lr*100:5.1f}% [{lo*100:4.1f},{hi*100:4.1f}]  '
          f'medEnd {st.median([x["fwd_end"] for x in lane_set])*100:+6.1f}%  '
          f'{"顯著" if lo > br else "不顯著"}')
