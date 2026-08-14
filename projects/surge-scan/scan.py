"""Case-control scan: sample stock-days across the listed universe, compute
point-in-time features, label by forward 60-day max run-up. No lookahead."""
import json, os, math, statistics as st, datetime as dtm, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjust import shock_days, adjust

BASE = os.path.dirname(os.path.abspath(__file__))
FWD = 60
SURGE = 0.80
STEP = 5                       # sample every 5th trading day
MIN_TURN = 20_000_000          # NT$20M/day avg over prior 20d
START, END = '2025-06-01', '2026-06-13'

chips = {}
for line in open(os.path.join(BASE, 'chips.ndjson')):
    r = json.loads(line); chips[r['id']] = r

def pub_date(y, m):
    """monthly revenue for year y month m is public from the 11th of the next month"""
    y2, m2 = (y + 1, 1) if m == 12 else (y, m + 1)
    return f'{y2:04d}-{m2:02d}-11'

def build_rev(c):
    """-> sorted list of (available_from, y, m, revenue)"""
    out = []
    for d, y, m, rev in c.get('rv', []):
        out.append((pub_date(y, m), y, m, rev))
    out.sort()
    return out

def idx_le(arr, val):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] <= val: lo = mid + 1
        else: hi = mid
    return lo - 1

def main():
    rows = []
    nstock = 0
    SHOCK, _ = shock_days(os.path.join(BASE, 'prices.ndjson'))
    print('market shock days:', sorted(SHOCK))
    for line in open(os.path.join(BASE, 'prices.ndjson')):
        r = json.loads(line)
        if r.get('error') or len(r.get('c', [])) < 300: continue
        nstock += 1
        dt, raw, h, l, v, m = r['dt'], r['c'], r['h'], r['l'], r['v'], r['m']
        c, ca_flags = adjust(dt, raw, SHOCK)
        n = len(c)
        scale = [c[k]/raw[k] if raw[k] else 1.0 for k in range(n)]
        h = [h[k]*scale[k] for k in range(n)]
        l = [l[k]*scale[k] for k in range(n)]
        ch = chips.get(r['id'], {})
        rev = build_rev(ch)
        revpub = [x[0] for x in rev]
        idt, fi, it, dl = ch.get('inst_dt', []), ch.get('fi', []), ch.get('it', []), ch.get('dl', [])
        mdt, mbal, sbal, mlim = ch.get('mg_dt', []), ch.get('mgbal', []), ch.get('shbal', []), ch.get('mglimit', [])
        for i in range(130, n - FWD, STEP):
            if not (START <= dt[i] <= END): continue
            if c[i] <= 0 or c[i-20] <= 0 or c[i-60] <= 0 or c[i-120] <= 0: continue
            turn20 = sum(m[i-20:i]) / 20
            if turn20 < MIN_TURN: continue
            fwd = c[i+1:i+1+FWD]
            if not fwd: continue
            fwdmax = max(fwd) / c[i] - 1
            hi52 = max(c[max(0,i-240):i+1]); lo52 = min(c[max(0,i-240):i+1])
            def _atr(a, b):
                tr = [max(h[j]-l[j], abs(h[j]-c[j-1]), abs(l[j]-c[j-1])) for j in range(a, b)]
                return sum(tr)/len(tr) if tr else 0.0
            atr20, atr60 = _atr(i-20, i), _atr(i-60, i-20)
            v5 = sum(v[i-5:i])/5; v20 = sum(v[i-20:i])/20; v60 = sum(v[i-60:i])/60
            rets20 = [c[j]/c[j-1]-1 for j in range(i-19, i+1) if c[j-1] > 0]
            lu20 = sum(1 for x in rets20 if x >= 0.095)
            # --- shares outstanding (張) estimated from margin limit = 25% of shares
            shares = None
            mi = idx_le(mdt, dt[i]) if mdt else -1
            if mi >= 0 and mlim[mi]: shares = mlim[mi] * 4
            # --- institutional nets over prior 20 / 60 sessions (張)
            f20 = t20 = f60 = t60 = None; itdays = None
            ii = idx_le(idt, dt[i]) if idt else -1
            if ii >= 20:
                f20 = sum(fi[ii-19:ii+1])/1000; t20 = sum(it[ii-19:ii+1])/1000
            if ii >= 60:
                f60 = sum(fi[ii-59:ii+1])/1000; t60 = sum(it[ii-59:ii+1])/1000
                itdays = sum(1 for x in it[ii-59:ii+1] if x != 0)
            # --- margin
            mg20 = mgpct = srat = None
            if mi >= 20 and mbal[mi-20]:
                mg20 = mbal[mi]/mbal[mi-20] - 1
            if mi >= 0 and shares:
                mgpct = mbal[mi]/shares*100
                srat = (sbal[mi]/mbal[mi]*100) if mbal[mi] else 0.0
            # --- revenue known as of dt[i]
            yoy = yoy3 = mom = None; rev_age = None
            ri = idx_le(revpub, dt[i])
            if ri >= 12:
                cur = rev[ri][3]; prev = rev[ri-1][3]; yr = rev[ri-12][3]
                if yr: yoy = cur/yr - 1
                if prev: mom = cur/prev - 1
                s3 = sum(x[3] for x in rev[ri-2:ri+1]); s3y = sum(x[3] for x in rev[ri-14:ri-11])
                if s3y: yoy3 = s3/s3y - 1
                d0 = dtm.date.fromisoformat(revpub[ri]); d1 = dtm.date.fromisoformat(dt[i])
                rev_age = (d1 - d0).days
            rows.append({
                'id': r['id'], 'name': r['name'], 'ind': r['industry'], 'dt': dt[i],
                'px': c[i], 'surge': 1 if fwdmax >= SURGE else 0, 'fwdmax': fwdmax,
                'fwd60': c[min(i+FWD, n-1)]/c[i]-1,
                'ret20': c[i]/c[i-20]-1, 'ret60': c[i]/c[i-60]-1, 'ret120': c[i]/c[i-120]-1,
                'from52h': c[i]/hi52-1, 'above52l': c[i]/lo52-1,
                'atrpct': atr20/c[i], 'squeeze': atr20/atr60 if atr60 else None,
                'v5v60': v5/v60 if v60 else None, 'v20v60': v20/v60 if v60 else None,
                'turn20': turn20, 'lu20': lu20,
                'mcap': (c[i]*shares*1000/1e8) if shares else None,   # 億元
                'fi20pct': (f20/shares*100) if (f20 is not None and shares) else None,
                'it20pct': (t20/shares*100) if (t20 is not None and shares) else None,
                'fi60pct': (f60/shares*100) if (f60 is not None and shares) else None,
                'it60pct': (t60/shares*100) if (t60 is not None and shares) else None,
                'itdays60': itdays, 'mg20': mg20, 'mgpct': mgpct, 'srat': srat,
                'yoy': yoy, 'yoy3': yoy3, 'mom': mom, 'rev_age': rev_age,
            })
    json.dump(rows, open(os.path.join(BASE, 'scan.json'), 'w'), ensure_ascii=False)
    ns = sum(x['surge'] for x in rows)
    print(f'stocks {nstock}  observations {len(rows)}  surges {ns} ({ns/len(rows)*100:.2f}%)')
    print('unique surge stocks', len({x["id"] for x in rows if x["surge"]}))

main()
