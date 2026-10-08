#!/usr/bin/env python3
"""對照 web/orbit_core.js（網頁試算器）和 pef/orbit.py（命令列）算出來的結果是否一致。

    python3 web/test_orbit_core.py        # 要 node；全部一致才回傳 0
"""
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from pef import orbit                                    # noqa: E402

model = json.load(open(os.path.join(HERE, "results", "orbit_model.json")))
T = pd.Timestamp
rows = [dict(px=1045.56, e=74.33, y=0.0413, dy=0.0004, v=0.67, g="cyclical"),
        dict(px=224.56, e=11.09, y=0.0413, dy=0.007, v=0.42, g="growth"),
        dict(px=335.95, e=-3.12, y=0.0413, dy=0.0, v=0.73, g="tech_other"),
        dict(px=150.0, e=6.0, y=0.0413, dy=0.02, v=float("nan"), g="other")]
cases = []
for i, r in enumerate(rows):
    for h in (6, 12, 24):
        for ea, eb, ca, cb in ((r["e"] * 1.2, r["e"] * 1.4, None, None), (r["e"] * 1.2, None, None, None),
                               (r["e"] * 1.1, r["e"] * 1.3, r["e"] * 1.15, r["e"] * 1.35), (r["e"] * 1.1, None, r["e"] * 1.05, None),
                               (2.0, 3.0, 2.5, 3.2), (-1.0, 2.0, None, None)):
            cases.append(dict(i=i, h=h, ea=ea, eb=eb, ca=ca, cb=cb))
cal = [dict(fy=[["2027-09-03", 176.15], ["2028-09-03", 206.33]], t="2027-10-07", q="2026-09-03", e=74.33, x=True),
       dict(fy=[["2027-09-03", 176.15], ["2028-09-03", 206.33]], t="2028-10-07", q="2026-09-03", e=74.33, x=True),
       dict(fy=[["2027-01-31", 16.75], ["2028-01-31", 16.02]], t="2029-10-07", q="2026-07-31", e=11.09, x=True),
       dict(fy=[["2026-12-31", 5.0], ["2027-12-31", 6.0]], t="2027-06-30", q="2026-06-30", e=4.0, x=False),
       dict(fy=[["2029-08-31", 170.0]], t="2027-10-06", q="2026-08-28", e=74.33, x=False),
       dict(fy=[["2026-09-27", 8.82], ["2027-09-27", 9.58]], t="2028-01-15", q="2026-06-27", e=8.72, x=True)]

js = os.path.join(HERE, "web", "orbit_core.js")
prog = f"""
const C = require({json.dumps(js)}); const model = {json.dumps(model)};
const rows = {json.dumps(rows).replace('NaN', 'null')}; rows.forEach(r => {{ if (r.v === null) r.v = NaN; }});
const out = {{pred: [], cal: []}};
for (const c of {json.dumps(cases)}) {{ const o = C.predict(rows[c.i], c.h, model, c.ea, c.eb, c.ca, c.cb);
  out.pred.push([o.spec, o.px, o.px_lo80, o.px_hi80, o.pe, o.fwd]); }}
for (const c of {json.dumps(cal)}) {{ const r = C.calendarize(c.fy.map(x => [C.utc(x[0]), x[1]]), C.utc(c.t), C.utc(c.q), c.e, c.x);
  out.cal.push(r ? [r.eps, r.how] : null); }}
console.log(JSON.stringify(out));
"""
res = json.loads(subprocess.run(["node", "-e", prog], capture_output=True, text=True, check=True).stdout)
bad = 0
for c, j in zip(cases, res["pred"]):
    o = orbit.predict(dict(px=rows[c["i"]]["px"], eps0=rows[c["i"]]["e"], y10=rows[c["i"]]["y"], dy=rows[c["i"]]["dy"],
                           vol36=rows[c["i"]]["v"], sector={"cyclical": "semis", "growth": "software", "tech_other": "hardware",
                                                            "other": "x"}[rows[c["i"]]["g"]]),
                      c["h"], model, c["ea"], c["eb"], c["ca"], c["cb"])
    py = [o["spec"], o["px"], o["px_lo80"], o["px_hi80"], o["pe"], o["fwd_pe"]]
    same = py[0] == j[0] and all((a is None and b is None) or (a is not None and b is not None and abs(a - b) <= 1e-9 * max(1, abs(a)))
                                  for a, b in zip(py[1:], j[1:]))
    bad += not same
    if not same:
        print("不一致", c, py, j)
for c, j in zip(cal, res["cal"]):
    p = orbit.calendarize({T(k): v for k, v in c["fy"]}, T(c["t"]), T(c["q"]), c["e"], extrapolate=c["x"])
    py = None if p[0] is None else [p[0], p[1]]
    same = (py is None and j is None) or (py is not None and j is not None and abs(py[0] - j[0]) < 1e-9 and py[1] == j[1])
    bad += not same
    print(("一致" if same else "不一致"), c["t"], py, j)
print(f"predict {len(cases)} 組、calendarize {len(cal)} 組；不一致 {bad}")
sys.exit(1 if bad else 0)
