#!/usr/bin/env python3
"""對照 web/orbit_core.js（網頁試算器）和 pef/orbit.py、pef/growth_price.py、pef/unified.py（命令列）算出來的結果是否一致；
也對照網頁的 consFor（共識 → 目標日 EPS）和 make_orbit_page.cons_for（算相對輸出的分布用）。

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
from pef import growth_price as GP                       # noqa: E402
from pef import unified                                  # noqa: E402
import make_orbit_page as MP                             # noqa: E402

model = orbit.load_model(os.path.join(HERE, "results"))
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
            cases.append(dict(i=i, h=h, ea=ea, eb=eb, ca=ca, cb=cb, rt=None, bm=1.0))
        cases.append(dict(i=i, h=h, ea=r["e"] * 1.1, eb=None, ca=r["e"] * 1.05, cb=None, rt=[-1.0, -0.06], bm=1.0))   # 利率情境
        cases.append(dict(i=i, h=h, ea=r["e"] * 1.2, eb=r["e"] * 1.4, ca=None, cb=None, rt=None, bm=1.17))     # 區間放寬
gpm = GP.load(os.path.join(HERE, "results"))
gp_js = dict(h={h: dict(coef=v["coef"], q=v["q"], levels=v.get("levels"), delta=v["delta"], vol_median=v["vol_median"]) for h, v in gpm["h"].items()})
gcases = []                                              # 成長定價（README §24）
for i, r in enumerate(rows):
    for h in (6, 12, 24):
        for ea, eb, f0, r12 in ((r["e"] * 1.2, r["e"] * 1.5, r["e"] * 1.15, 0.3), (r["e"] * 1.1, r["e"] * 1.1, r["e"] * 1.3, None),
                                (r["e"] * 3.0, r["e"] * 4.5, r["e"] * 2.0, -1.4), (r["e"] * 0.8, r["e"] * 1.2, r["e"] * 0.9, 0.05),
                                (2.0, 3.0, 2.5, 0.1), (-1.0, 2.0, 1.0, 0.0)):
            gcases.append(dict(i=i, h=h, ea=ea, eb=eb, f0=f0, r12=r12, rt=None, bm=1.0))
        gcases.append(dict(i=i, h=h, ea=r["e"] * 1.2, eb=r["e"] * 1.4, f0=r["e"] * 1.1, r12=0.2, rt=[-1.0, -0.06], bm=1.17))
gp_js = dict(h={h: dict(gp_js["h"][h], gt_hat=v["gt_hat"]) for h, v in gpm["h"].items()})
cq = unified.load_conformal(os.path.join(HERE, "results"))
cq_js = MP.slim_cq(cq)
ucases = []                                              # 統一模型（README §26）
for i, r in enumerate(rows):
    e = r["e"]
    for h in (6, 12, 24):
        for ea, eb, kind, ca, cb, f0 in ((None, None, "fund", e * 1.15, e * 1.35, e * 1.1), (None, None, "fund", e * 1.15, None, e * 1.1),
                                         (None, None, "fund", e * 1.15, e * 1.35, None), (e * 1.1, None, "fund", e * 1.15, e * 1.35, None),
                                         (e * 1.1, e * 1.4, "fund", e * 1.15, e * 1.35, e * 1.1), (e * 1.1, e * 1.4, "market", e * 1.15, e * 1.35, e * 1.1),
                                         (e * 1.1, e * 1.4, "market", e * 1.15, None, e * 1.1), (None, e * 1.5, "market", e * 1.15, e * 1.35, e * 1.1),
                                         (e * 1.2, e * 1.4, "fund", None, None, None), (e * 1.2, None, "market", None, None, None),
                                         (-1.0, 2.0, "fund", 2.5, 3.2, None), (2.0, 3.0, "market", 2.5, 3.2, 2.4)):
            ucases.append(dict(i=i, h=h, ea=ea, eb=eb, kind=kind, ca=ca, cb=cb, f0=f0, rt=None, bm=1.0))
        ucases.append(dict(i=i, h=h, ea=e * 1.1, eb=e * 1.4, kind="market", ca=e * 1.15, cb=e * 1.35, f0=e * 1.1, rt=[-1.0, -0.06], bm=1.17))
        ucases.append(dict(i=i, h=h, ea=None, eb=None, kind="fund", ca=e * 1.15, cb=e * 1.35, f0=e * 1.1, rt=[0.5, -0.05], bm=1.17))
cf_t = [dict(d="2026-10-10", q="2026-08-31", e=74.33, c=dict(f0="2027-08-31", f1="2028-08-31", c0=176.15, c1=206.33, k=0.95, cf=0.91)),
        dict(d="2026-10-10", q="2026-08-31", e=74.33, c=dict(f0="2027-08-31", f1="2028-08-31", c0=176.15, c1=206.33, k=0.9)),
        dict(d="2026-10-10", q="2026-06-30", e=11.09, c=dict(f0="2027-01-31", f1="2028-01-31", c0=16.75, c1=16.02, k=1.02)),
        dict(d="2026-10-10", q="2026-06-30", e=6.0, c=dict(f0="2026-12-31", f1="2027-12-31", c0=5.0, c1=6.0, k=0.3)),
        dict(d="2026-10-10", q="2026-06-30", e=6.0, c=dict(f0="2026-12-31", f1="2027-12-31", c0=5.0, c1=6.0, k=0.3, cg="中小型股：距離年報 10 個月，不校正")),
        dict(d="2026-10-10", q="2026-06-27", e=8.72, c=dict(f0="2026-09-27", f1="2027-09-27", c0=8.82, c1=None, k=None)),
        dict(d="2026-10-10", q="2026-06-27", e=-2.0, c=dict(f0="2026-09-27", f1="2027-09-27", c0=1.0, c1=2.5, k=None, cf=1.1)),
        dict(d="2026-10-10", q="2026-06-27", e=8.72, c=None)]
cfcases = [dict(j=j, h=h, ku=ku) for j in range(len(cf_t)) for h in (6, 12, 24) for ku in (None, 0.91, 0.8, 1.0)]
page = open(os.path.join(HERE, "web", "orbit_page.html")).read()
cons_for_js = page[page.index("function consFor("):page.index("function fillFrom(")]
rsens = json.load(open(os.path.join(HERE, "results", "rate_sensitivity.json")))
slopes = [dict(h=h, rg=rg, pr=pr) for h in (6, 12, 24) for rg in ("2022", "2012") for pr in (None, 0.02, 0.4, 0.97)]
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
const out = {{pred: [], cal: [], sl: [], gp: [], un: [], cf: []}};
const CQ = {json.dumps(cq_js)}; const GPJ = {json.dumps(gp_js)};
const UK = ["spec", "mode", "kind", "bandKind", "bandGroup", "px", "px_lo80", "px_lo50", "px_hi80", "pe", "pe_hi80", "fwd", "epsA", "epsB", "gtCons", "note", "adj", "width", "epsWiden",
  "px_lo70", "px_hi60", "px_lo90", "pe_lo70", "pe_hi90", "pe_lo60", "eps_lo80", "eps_hi80", "eps_lo50", "fwd_lo80", "fwd_hi80", "fwd_lo60"];
for (const c of {json.dumps(ucases)}) {{ const o = C.predictUnified(rows[c.i], c.h, model, GPJ, CQ, c.ea, c.eb, c.kind, c.ca, c.cb, c.f0, c.rt, c.bm);
  out.un.push(UK.map(k => o[k] === undefined ? null : o[k]).concat(["eps_g", "pe_ch", "total"].map(k => o.decomp ? o.decomp[k] : null), [(o.bandLevels || []).join(",")])); }}
{cons_for_js}
const CFT = {json.dumps(cf_t)};
for (const c of {json.dumps(cfcases)}) {{ const t = CFT[c.j]; const r = consFor(t, c.h, c.ku);
  out.cf.push(r ? [r.a ? r.a.eps : null, r.a ? r.a.how : null, r.b ? r.b.eps : null, r.b ? r.b.how : null, r.k, r.k0, r.kBad] : null); }}
for (const c of {json.dumps(gcases)}) {{ const o = C.predictGrowth(rows[c.i], c.h, model, {json.dumps(gp_js)}, c.ea, c.eb, c.f0, c.r12, c.rt, c.bm);
  out.gp.push(o ? [o.spec, o.px, o.px_lo80, o.px_hi80, o.pe, o.fwd, o.px_lo70, o.pe_hi90] : null); }}
for (const c of {json.dumps(slopes)}) out.sl.push(C.rateSlope({json.dumps(rsens)}, c.h, c.rg, c.pr));
for (const c of {json.dumps(cases)}) {{ const o = C.predict(rows[c.i], c.h, model, c.ea, c.eb, c.ca, c.cb, c.rt, c.bm);
  out.pred.push([o.spec, o.px, o.px_lo80, o.px_hi80, o.pe, o.fwd, o.px_lo70, o.px_hi60, o.pe_lo90 === undefined ? null : o.pe_lo90]); }}
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
                      c["h"], model, c["ea"], c["eb"], c["ca"], c["cb"], rate=c["rt"], band_mult=c["bm"])
    py = [o["spec"], o["px"], o["px_lo80"], o["px_hi80"], o["pe"], o["fwd_pe"], o["px_lo70"], o["px_hi60"], o.get("pe_lo90")]
    same = py[0] == j[0] and all((a is None and b is None) or (a is not None and b is not None and abs(a - b) <= 1e-9 * max(1, abs(a)))
                                  for a, b in zip(py[1:], j[1:]))
    bad += not same
    if not same:
        print("不一致", c, py, j)
for c, j in zip(gcases, res["gp"]):
    r = rows[c["i"]]
    o = GP.predict(dict(px=r["px"], eps0=r["e"], y10=r["y"], dy=r["dy"], vol36=r["v"], grp=r["g"]), c["h"], c["ea"], c["eb"], c["f0"], c["r12"],
                   model=model, gm=gpm, rate=c["rt"], band_mult=c["bm"])
    py = None if o is None else [o["spec"], o["px"], o["px_lo80"], o["px_hi80"], o["pe"], o["fwd_pe"], o["px_lo70"], o["pe_hi90"]]
    same = (py is None and j is None) or (py is not None and j is not None and py[0] == j[0]
                                          and all(abs(a - b) <= 1e-9 * max(1, abs(a)) for a, b in zip(py[1:], j[1:])))
    bad += not same
    if not same:
        print("成長定價不一致", c, py, j)
UKP = ["spec", "mode", "kind", "band_kind", "band_group", "px", "px_lo80", "px_lo50", "px_hi80", "pe", "pe_hi80", "fwd_pe", "eps_a", "eps_b", "gt_cons", "note", "adj", "width", "eps_widen",
       "px_lo70", "px_hi60", "px_lo90", "pe_lo70", "pe_hi90", "pe_lo60", "eps_lo80", "eps_hi80", "eps_lo50", "fwd_lo80", "fwd_hi80", "fwd_lo60"]
def same_val(a, b):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    return abs(a - b) <= 1e-9 * max(1, abs(a))
for c, j in zip(ucases, res["un"]):
    r = rows[c["i"]]
    o = unified.predict(dict(px=r["px"], eps0=r["e"], y10=r["y"], dy=r["dy"], vol36=r["v"], grp=r["g"]), c["h"], model=model, gm=gpm, cq=cq,
                        eps_a=c["ea"], eps_b=c["eb"], eb_kind=c["kind"], cons_a=c["ca"], cons_b=c["cb"], fwd0=c["f0"], rate=c["rt"], band_mult=c["bm"])
    py = [o.get(k) for k in UKP] + [None if o.get("decomp") is None else o["decomp"][k] for k in ("eps_g", "pe_ch", "total")] + [",".join(str(L) for L in o.get("band_levels", []))]
    py = [None if (isinstance(v, float) and not np.isfinite(v)) else v for v in py]
    same = all(same_val(a, b) for a, b in zip(py, j))
    bad += not same
    if not same:
        print("統一模型不一致", c, [(k, a, b) for k, a, b in zip(UKP, py, j) if not same_val(a, b)])
for c, j in zip(cfcases, res["cf"]):
    r = MP.cons_for(cf_t[c["j"]], c["h"], c["ku"])
    py = None if r is None else [r["a"][0] if r["a"] else None, r["a"][1] if r["a"] else None, r["b"][0] if r["b"] else None, r["b"][1] if r["b"] else None,
                                 r["k"], r["k0"], r["k_bad"]]
    same = (py is None and j is None) or (py is not None and j is not None and all(same_val(a, b) for a, b in zip(py, j)))
    bad += not same
    if not same:
        print("consFor 不一致", c, py, j)
for c, j in zip(slopes, res["sl"]):
    py = orbit.rate_slope(c["h"], c["rg"], c["pr"])[0]
    same = abs(py - j) < 1e-12
    bad += not same
    if not same:
        print("利率斜率不一致", c, py, j)
for c, j in zip(cal, res["cal"]):
    p = orbit.calendarize({T(k): v for k, v in c["fy"]}, T(c["t"]), T(c["q"]), c["e"], extrapolate=c["x"])
    py = None if p[0] is None else [p[0], p[1]]
    same = (py is None and j is None) or (py is not None and j is not None and abs(py[0] - j[0]) < 1e-9 and py[1] == j[1])
    bad += not same
    print(("一致" if same else "不一致"), c["t"], py, j)
print(f"predict {len(cases)} 組（含利率情境）、成長定價 {len(gcases)} 組、統一模型 {len(ucases)} 組、consFor {len(cfcases)} 組、利率斜率 {len(slopes)} 組、calendarize {len(cal)} 組；不一致 {bad}")
sys.exit(1 if bad else 0)
