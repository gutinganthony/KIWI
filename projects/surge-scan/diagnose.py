"""Why did the momentum+volatility score never flag the actual wave leaders?
Look at where those names ranked on each feature just before their runs, and at
what the top-20 list was actually full of."""
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
SC = ['ret120','ret60','atrpct','accel','from52h']
for r in rows:
    ps = [r.get('p_'+f) for f in SC]
    r['score'] = sum(p for p in ps if p is not None)/max(1, sum(1 for p in ps if p is not None))

NAMES = {'2059':'川湖','2327':'國巨','2344':'華邦電','2337':'旺宏','3260':'威剛','2408':'南亞科'}
print('=== where the wave leaders ranked, on the observations that DID become BIG ===')
print(f"{'':6}{'date':12}{'turn':>6}{'r120':>6}{'atr':>6}{'accel':>6}{'f52h':>6}{'score':>7}{'rank/day':>10}{'fwdmax':>8}")
for sid, nm in NAMES.items():
    hits = [r for r in rows if r['id'] == sid and r['big']]
    if not hits:
        print(f'{nm:6} — no BIG observation in the evaluable window (entries end 2025-08)'); continue
    r = min(hits, key=lambda x: x['dt'])
    peers = sorted(bydate[r['dt']], key=lambda x: -x['score'])
    rank = next(i+1 for i, x in enumerate(peers) if x['id'] == sid)
    print(f"{nm:6}{r['dt']:12}{r.get('p_turn20',0)*100:5.0f}%{r.get('p_ret120',0)*100:5.0f}%"
          f"{r.get('p_atrpct',0)*100:5.0f}%{r.get('p_accel',0)*100:5.0f}%{r.get('p_from52h',0)*100:5.0f}%"
          f"{r['score']:7.2f}{rank:>6}/{len(peers):<4}{r['fwd_max']*100:+7.0f}%")

print('\n=== what the top-20 list actually held (2024-01 onward, sample months) ===')
test = [r for r in rows if r['dt'] >= '2024-01-01']
bym = {}
for r in test: bym.setdefault(r['dt'][:7], []).append(r)
for mo in ['2024-03', '2024-10', '2025-03', '2025-07']:
    if mo not in bym: continue
    seen = {}
    for r in sorted(bym[mo], key=lambda x: -x['score']):
        if r['id'] in seen: continue
        seen[r['id']] = r
        if len(seen) >= 8: break
    picks = list(seen.values())
    print(f"  {mo}: " + ', '.join(f"{x['name'][:6]}({x['fwd_max']*100:+.0f}%/{x['fwd_end']*100:+.0f}%)" for x in picks))

print('\n=== median market cap proxy (20d turnover, NT$m) of picks vs wave leaders ===')
top20 = []
for mo, rs in bym.items():
    seen = {}
    for r in sorted(rs, key=lambda x: -x['score']):
        if r['id'] in seen: continue
        seen[r['id']] = r
        if len(seen) >= 20: break
    top20.extend(seen.values())
bigs = [r for r in test if r['big']]
print(f"  top-20 picks: median turn20 {st.median([x['turn20'] for x in top20])/1e6:8.0f}m  "
      f"median atrpct {st.median([x['atrpct'] for x in top20])*100:.1f}%")
print(f"  all BIG obs : median turn20 {st.median([x['turn20'] for x in bigs])/1e6:8.0f}m  "
      f"median atrpct {st.median([x['atrpct'] for x in bigs])*100:.1f}%")
print(f"  all obs     : median turn20 {st.median([x['turn20'] for x in test])/1e6:8.0f}m  "
      f"median atrpct {st.median([x['atrpct'] for x in test])*100:.1f}%")
