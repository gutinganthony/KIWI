"""TWSE/TPEx normally trade inside a +-10% daily band, so a larger close-to-close
move usually means a corporate action (capital reduction, split, big ex-dividend)
rather than a tradeable gain. Exception: on market-wide shock days the band did
not hold for every stock (2024-08-05 yen unwind, 2025-04-07 tariff crash), so an
out-of-band move is only neutralised when the market itself was calm that day.
Market state is measured from the data: the cross-sectional MEDIAN return."""
import json, statistics as st
LIMIT = 0.115
SHOCK = 0.045          # |median return across all stocks| >= 4.5% => market-wide day

def out_of_band(c, i):
    return i > 0 and c[i-1] > 0 and c[i] > 0 and abs(c[i]/c[i-1] - 1) > LIMIT

def shock_days(path):
    daily = {}
    for line in open(path):
        r = json.loads(line)
        if r.get('error'): continue
        c, dt = r['c'], r['dt']
        for i in range(1, len(c)):
            if c[i-1] > 0 and c[i] > 0:
                daily.setdefault(dt[i], []).append(c[i]/c[i-1]-1)
    med = {d: st.median(v) for d, v in daily.items() if len(v) > 100}
    return {d for d, m in med.items() if abs(m) >= SHOCK}, med

def adjust(dt, c, shock):
    adj = [c[0]]; flags = []
    for i in range(1, len(c)):
        r = c[i]/c[i-1] if (c[i-1] > 0 and c[i] > 0) else 1.0
        if out_of_band(c, i) and dt[i] not in shock:
            flags.append(i); r = 1.0
        adj.append(adj[-1]*r)
    return adj, flags
