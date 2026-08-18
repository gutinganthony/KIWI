"""The entry-timing question, which is NOT the screening question.

Screening asks: which stocks beat the market. Its control group is the market.
Timing asks: given a stock that is already strong, which DAY is the entry. Its
control group must be the other days of those same strong stocks -- otherwise
any 'signal' is just re-detecting that strong stocks outperform.

Everything below is measured against the strong-universe baseline: buying a
random day in a stock that already passes the strength screen.
"""
import json, os, sys, statistics as st, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, 'scan2.json')))
random.seed(23); B = 400

def bucket(d):
    y, m = int(d[:4]), int(d[5:7])
    return f'{y}H{1 if m <= 6 else 2}'

# strength screen is ranked WITHIN each date, so it adapts to the regime
bydate = {}
for r in rows: bydate.setdefault(r['dt'], []).append(r)
for d, rs in bydate.items():
    rs.sort(key=lambda x: x['turn20'])
    for k, x in enumerate(rs): x['tp'] = k/max(1, len(rs)-1)
    v = [x for x in rs if x.get('ret120') is not None]
    v.sort(key=lambda x: x['ret120'])
    for k, x in enumerate(v): x['rp'] = k/max(1, len(v)-1)

STRONG = lambda x: x.get('tp', 0) >= 0.75 and x.get('rp', 0) >= 0.75

TRIGGERS = [
    ('突破 60 日新高',        lambda x: x.get('newhigh60') == 1),
    ('量縮打底後放量',        lambda x: x.get('v20v60') is not None and x['v20v60'] <= 0.85
                                        and x.get('v5v60') is not None and x['v5v60'] >= 1.5),
    ('波動壓縮 (squeeze<0.8)', lambda x: x.get('squeeze') is not None and x['squeeze'] <= 0.8),
    ('投信由賣轉買',          lambda x: x.get('it_flip') == 1),
    ('外資 60 日買超高',       lambda x: x.get('fi60_sh') is not None and x['fi60_sh'] >= 0.05),
    ('融資 20 日減少 >10%',    lambda x: x.get('mg20') is not None and x['mg20'] <= -0.10),
    ('融資 20 日增加 >20%',    lambda x: x.get('mg20') is not None and x['mg20'] >= 0.20),
    ('融資佔股本 <3%',        lambda x: x.get('mgpct') is not None and x['mgpct'] < 3),
    ('券資比 >5%',            lambda x: x.get('srat') is not None and x['srat'] >= 5),
    ('營收 3M 動能 > 12M',     lambda x: x.get('rev_accel') is not None and x['rev_accel'] > 0.10),
    ('營收 3M YoY >30%',       lambda x: x.get('yoy3') is not None and x['yoy3'] >= 0.30),
    ('尚未出現漲停 (lu20=0)',  lambda x: x.get('lu20') == 0),
]

def cb(sel, label, base_med=None):
    if len(sel) < 60: return f'{label:26} n={len(sel)} (too few)'
    bys = {}
    for x in sel: bys.setdefault(x['id'], []).append(x)
    ids = list(bys); meds = []; surs = []
    for _ in range(B):
        s = [x for k in (random.choice(ids) for _ in ids) for x in bys[k]]
        meds.append(st.median([x['fwd_end'] for x in s]))
        surs.append(sum(x['big'] for x in s)/len(s))
    q = lambda a: (sorted(a)[int(B*.025)], sorted(a)[int(B*.975)])
    lm, hm = q(meds); ls, hs = q(surs)
    e = [x['fwd_end'] for x in sel]; d = sorted(x['fwd_min'] for x in sel)
    tag = ''
    if base_med is not None:
        tag = '  ***' if lm > base_med else ('  --' if hm < base_med else '')
    return (f'{label:26} n={len(sel):5} stk={len(ids):4}  med {st.median(e)*100:+6.1f}% '
            f'[{lm*100:+6.1f},{hm*100:+6.1f}]  win {sum(1 for x in e if x>0)/len(e)*100:4.1f}%  '
            f'DD {st.median(d)*100:+6.1f}%  P(+100%/250d) {sum(x["big"] for x in sel)/len(sel)*100:4.1f}%{tag}')

# 250-day forward windows mean the last usable entry date is ~2025-08; later
# entries were dropped as truncated, so there is no 2026 bucket here.
PERIODS = [('2022 空頭', lambda d: d < '2023-01-01'),
           ('2023 復甦', lambda d: '2023-01-01' <= d < '2024-01-01'),
           ('2024 多頭', lambda d: '2024-01-01' <= d < '2025-01-01'),
           ('2025', lambda d: '2025-01-01' <= d < '2026-01-01'),
           ('全期', lambda d: True)]

for pname, pf in PERIODS:
    sub = [x for x in rows if pf(x['dt'])]
    strong = [x for x in sub if STRONG(x)]
    if len(strong) < 200:
        print(f'\n### {pname}: strong n={len(strong)} — too few, skipped'); continue
    allmed = st.median([x['fwd_end'] for x in sub])
    smed = st.median([x['fwd_end'] for x in strong])
    print(f'\n### {pname}  |  全市場中位數 {allmed*100:+.1f}%  |  強勢股基準 {smed*100:+.1f}% '
          f'(n={len(strong)})   *** = 顯著優於強勢股基準, -- = 顯著劣於')
    print(cb(strong, '【強勢股基準】'))
    for lbl, f in TRIGGERS:
        sel = [x for x in strong if f(x)]
        print(cb(sel, lbl, base_med=smed))
