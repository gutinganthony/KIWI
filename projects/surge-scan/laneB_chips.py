"""Lane B (laggard + heavy turnover) works after a market turns and inverts in a
bear. The open question: is the bear-period failure visible in the chips at the
time -- i.e. were those laggards being distributed by institutions rather than
accumulated? If yes, a per-stock chip filter can replace a macro on/off switch.

Sample note: institutional data covers the 655-stock enriched aux set, so read
contrasts within each period only, never the absolute levels.
"""
import json, os, statistics as st, random
BASE = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in json.load(open(os.path.join(BASE, 'scan2.json')))
        if not r['id'].startswith('0') and r.get('fi60_sh') is not None]
print(f'obs with institutional data: {len(rows)}  stocks {len({r["id"] for r in rows})}')
bydate = {}
for r in rows: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    v = [x for x in rs if x.get('turn20') is not None]
    v.sort(key=lambda x: x['turn20'])
    for k, x in enumerate(v): x['p_turn20'] = k/max(1, len(v)-1)
LANE_B = lambda x: (x.get('from52h') is not None and x['from52h'] <= -0.30
                    and (x.get('p_turn20') or 0) >= 0.70)

PERIODS = [('2022 空頭', '2022-01-01', '2023-01-01'),
           ('2023 復甦', '2023-01-01', '2024-01-01'),
           ('2024',      '2024-01-01', '2025-01-01'),
           ('2025H1',    '2025-01-01', '2025-09-01')]

print('\n=== B 線標的的法人流向：命中 vs 未命中（法人淨額佔成交量比重，中位數）===')
print(f"{'期間':10}{'B線n':>7}{'BIG率':>8}{'外資60d 命中':>13}{'外資60d 未中':>13}{'投信60d 命中':>13}{'投信60d 未中':>13}")
for pn, a, b in PERIODS:
    sub = [x for x in rows if a <= x['dt'] < b and LANE_B(x)]
    if len(sub) < 60: print(f'{pn:10}{len(sub):>7}  樣本不足'); continue
    hit = [x for x in sub if x['big']]; mis = [x for x in sub if not x['big']]
    f = lambda s, k: (st.median([x[k] for x in s])*100 if s else float('nan'))
    print(f'{pn:10}{len(sub):7}{sum(x["big"] for x in sub)/len(sub)*100:7.1f}%'
          f'{f(hit,"fi60_sh"):12.2f}%{f(mis,"fi60_sh"):12.2f}%'
          f'{f(hit,"it60_sh"):12.2f}%{f(mis,"it60_sh"):12.2f}%')

random.seed(13); B = 400
def cb(sel, label, base=None):
    if len(sel) < 60: return f'{label:34} n={len(sel)} (樣本不足)'
    bys = {}
    for x in sel: bys.setdefault(x['id'], []).append(x)
    ids = list(bys); a = []
    for _ in range(B):
        s = [x for k in (random.choice(ids) for _ in ids) for x in bys[k]]
        a.append(sum(x['big'] for x in s)/len(s))
    lo, hi = sorted(a)[int(B*.025)], sorted(a)[int(B*.975)]
    b0 = sum(x['big'] for x in sel)/len(sel)
    tag = '  ***' if (base is not None and lo > base) else ('  --' if (base is not None and hi < base) else '')
    return (f'{label:34} n={len(sel):5} stk={len(ids):4}  BIG {b0*100:5.1f}% [{lo*100:4.1f},{hi*100:4.1f}]  '
            f'medEnd {st.median([x["fwd_end"] for x in sel])*100:+7.1f}%{tag}')

print('\n=== 加上「外資沒在賣」這個過濾，能不能救回空頭期的 B 線？===')
for pn, a, b in PERIODS:
    sub = [x for x in rows if a <= x['dt'] < b]
    if len(sub) < 300: continue
    base = sum(x['big'] for x in sub)/len(sub)
    lb = [x for x in sub if LANE_B(x)]
    print(f'\n-- {pn}   該期基準 {base*100:.1f}%')
    print(cb(lb, 'B 線（全部）', base))
    print(cb([x for x in lb if x['fi60_sh'] >= 0], '  + 外資 60 日淨買 ≥ 0', base))
    print(cb([x for x in lb if x['fi60_sh'] < 0], '  + 外資 60 日淨賣', base))
    print(cb([x for x in lb if x.get('it60_sh') is not None and x['it60_sh'] > 0], '  + 投信 60 日淨買 > 0', base))
