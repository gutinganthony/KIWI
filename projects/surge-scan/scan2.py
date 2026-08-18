"""Extended scan: 2022-2026 (includes the 2022 bear), with margin and revenue
features added. Splits into half-year buckets so a regime that breaks the rule
shows up instead of being averaged away by 2026's bull run."""
import json, os, sys, statistics as st, datetime as dtm
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjust import shock_days, adjust

BASE = os.path.dirname(os.path.abspath(__file__))
PX = os.path.join(BASE, 'px_long.ndjson')
# The goal is catching a multi-month wave early (King Slide ran 13 months,
# Yageo leg 2 ran 3), so the label is a LONG forward window. Windows that run
# past the data end are kept only when the threshold was already cleared --
# a truncated window that has not yet hit is unknown, not a miss.
FWD, BIG, STEP, MIN_TURN = 250, 1.00, 10, 20_000_000
FWD_MID, BIG_MID = 120, 0.60
START, END = '2022-01-01', '2026-06-13'

def load(fn, key):
    d = {}
    p = os.path.join(BASE, fn)
    if os.path.exists(p):
        for line in open(p):
            r = json.loads(line)
            if r.get(key): d[r['id']] = r
    return d

INST = load('inst_long.ndjson', 'inst_dt')
MARG = load('margin_long.ndjson', 'mg_dt')
REV  = load('rev_long.ndjson', 'rv')
print(f'aux coverage: inst {len(INST)}  margin {len(MARG)}  rev {len(REV)}', flush=True)

def idx_le(a, v):
    lo, hi = 0, len(a)
    while lo < hi:
        m = (lo+hi)//2
        if a[m] <= v: lo = m+1
        else: hi = m
    return lo-1

def pub(y, m):
    y2, m2 = (y+1, 1) if m == 12 else (y, m+1)
    return f'{y2:04d}-{m2:02d}-11'      # revenue is public by the 10th of the next month

SHOCK, _ = shock_days(PX)
print('shock days:', sorted(SHOCK), flush=True)

rows = []
nst = 0
for line in open(PX):
    r = json.loads(line)
    if r.get('error') or len(r.get('c', [])) < 400 or r['id'].startswith('0'): continue
    nst += 1
    dt, raw, h0, l0, v, m = r['dt'], r['c'], r['h'], r['l'], r['v'], r['m']
    c, _ = adjust(dt, raw, SHOCK)
    n = len(c)
    sc = [c[k]/raw[k] if raw[k] else 1.0 for k in range(n)]
    h = [h0[k]*sc[k] for k in range(n)]; l = [l0[k]*sc[k] for k in range(n)]
    ch = INST.get(r['id']); mg = MARG.get(r['id']); rv = REV.get(r['id'])
    revlist = sorted((pub(y, mo), rev) for _, y, mo, rev in rv['rv']) if rv else []
    revpub = [x[0] for x in revlist]
    for i in range(130, n - FWD, STEP):
        if not (START <= dt[i] <= END) or c[i] <= 0: continue
        if min(c[i-120], c[i-60], c[i-20]) <= 0: continue
        turn20 = sum(m[i-20:i])/20
        if turn20 < MIN_TURN: continue
        fwd = c[i+1:i+1+FWD]
        if not fwd: continue
        truncated = (i+1+FWD) > n
        if truncated: continue                    # unbiased: no partial windows at all
        big = 1 if max(fwd)/c[i]-1 >= BIG else 0
        fwd_mid = c[i+1:i+1+FWD_MID]
        mid_trunc = (i+1+FWD_MID) > n
        mid = 1 if (fwd_mid and max(fwd_mid)/c[i]-1 >= BIG_MID) else 0
        if mid_trunc and not mid: mid = None
        hi52 = max(c[max(0, i-240):i+1]); lo52 = min(c[max(0, i-240):i+1])
        def atr(a, b):
            tr = [max(h[j]-l[j], abs(h[j]-c[j-1]), abs(l[j]-c[j-1])) for j in range(a, b)]
            return sum(tr)/len(tr) if tr else 0.0
        a20, a60 = atr(i-20, i), atr(i-60, i-20)
        v5, v20, v60 = sum(v[i-5:i])/5, sum(v[i-20:i])/20, sum(v[i-60:i])/60
        base120 = st.median(m[max(0, i-120):i]) or 1
        d = {'id': r['id'], 'name': r.get('name', ''), 'ind': r.get('industry', ''), 'dt': dt[i],
             'px': c[i], 'big': big, 'mid': mid,
             'fwd_max': max(fwd)/c[i]-1, 'trunc': 1 if truncated else 0,
             'fwd_end': c[min(i+FWD, n-1)]/c[i]-1, 'fwd_min': min(fwd)/c[i]-1,
             'peak_gap': (fwd.index(max(fwd))+1),
             'ret20': c[i]/c[i-20]-1, 'ret60': c[i]/c[i-60]-1, 'ret120': c[i]/c[i-120]-1,
             'from52h': c[i]/hi52-1, 'atrpct': a20/c[i], 'squeeze': a20/a60 if a60 else None,
             'v5v60': v5/v60 if v60 else None, 'v20v60': v20/v60 if v60 else None,
             'turn20': turn20, 'accel': turn20/base120,
             'lu20': sum(1 for j in range(i-19, i+1) if c[j-1] > 0 and c[j]/c[j-1]-1 >= 0.095),
             'newhigh60': 1 if c[i] >= max(c[i-60:i]) else 0}
        shares = None
        if mg:
            j = idx_le(mg['mg_dt'], dt[i])
            if j >= 0 and mg['mglimit'][j]:
                shares = mg['mglimit'][j]*4
                d['mgpct'] = mg['mgbal'][j]/shares*100
                d['srat'] = (mg['shbal'][j]/mg['mgbal'][j]*100) if mg['mgbal'][j] else 0.0
                d['mcap'] = c[i]*shares*1000/1e8
            if j >= 20 and mg['mgbal'][j-20]:
                d['mg20'] = mg['mgbal'][j]/mg['mgbal'][j-20]-1
        if ch:
            j = idx_le(ch['inst_dt'], dt[i])
            if j >= 60:
                fi, it = ch['fi'], ch['it']
                vol20 = sum(v[i-20:i]) or 1; vol60 = sum(v[i-60:i]) or 1
                d['fi20_sh'] = sum(fi[j-19:j+1])/vol20
                d['fi60_sh'] = sum(fi[j-59:j+1])/vol60
                d['it60_sh'] = sum(it[j-59:j+1])/vol60
                d['it_flip'] = 1 if (sum(it[j-39:j-9]) <= 0 < sum(it[j-9:j+1])) else 0
                d['it_zero'] = 1 if all(x == 0 for x in it[j-59:j+1]) else 0
        if revpub:
            k = idx_le(revpub, dt[i])
            if k >= 14:
                cur = revlist[k][1]; prev = revlist[k-1][1]; yr = revlist[k-12][1]
                if yr: d['yoy'] = cur/yr-1
                if prev: d['mom'] = cur/prev-1
                s3 = sum(x[1] for x in revlist[k-2:k+1]); s3y = sum(x[1] for x in revlist[k-14:k-11])
                s12 = sum(x[1] for x in revlist[k-11:k+1]); s12y = sum(x[1] for x in revlist[k-23:k-11])
                if s3y: d['yoy3'] = s3/s3y-1
                if s3y and s12y and s12y > 0:
                    d['rev_accel'] = (s3/s3y-1) - (s12/s12y-1)
        rows.append(d)
json.dump(rows, open(os.path.join(BASE, 'scan2.json'), 'w'), ensure_ascii=False)
print(f'stocks {nst}  observations {len(rows)}  BIG(+100%/250d) {sum(x["big"] for x in rows)} '
      f'({sum(x["big"] for x in rows)/max(1,len(rows))*100:.2f}%)')
bk = {}
for x in rows:
    y, mo = int(x['dt'][:4]), int(x['dt'][5:7])
    bk.setdefault(f'{y}H{1 if mo <= 6 else 2}', []).append(x)
print(f"\n{'bucket':9}{'n':>7}{'medRet':>9}{'win':>7}{'BIG%':>8}")
for k in sorted(bk):
    s = bk[k]; e = sorted(x['fwd_end'] for x in s)
    print(f'{k:9}{len(s):7}{st.median(e)*100:+8.1f}%{sum(1 for x in e if x>0)/len(s)*100:6.1f}%'
          f'{sum(x["big"] for x in s)/len(s)*100:7.1f}%')
