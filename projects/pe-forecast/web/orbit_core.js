// 本益比軌道模型的計算核心：和 pef/orbit.py 的 reported_quarter、calendarize、predict 一模一樣（make_orbit_page.py 嵌進網頁；
// web/test_orbit_core.py 用 node 跑，對照 Python 的結果）。日期一律用 UTC；加月份照 pandas DateOffset 的規則（日子超過月底就截到月底）。
const OrbitCore = (() => {
  const DAY = 86400000;
  const utc = (s) => { const [y, m, d] = s.split("-").map(Number); return new Date(Date.UTC(y, m - 1, d)); };
  const iso = (d) => d.toISOString().slice(0, 10);
  const addDays = (d, n) => new Date(d.getTime() + n * DAY);
  function addMonths(d, n) {
    const m = d.getUTCMonth() + n;
    const y = d.getUTCFullYear() + Math.floor(m / 12);
    const mm = ((m % 12) + 12) % 12;
    const last = new Date(Date.UTC(y, mm + 1, 0)).getUTCDate();
    return new Date(Date.UTC(y, mm, Math.min(d.getUTCDate(), last)));
  }
  const pos = (v) => v !== null && v !== undefined && Number.isFinite(v) && v > 0;
  const clip = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

  // target 那天大概已公布到哪一季（季末 + 45 天內公布）
  function reportedQuarter(lastQ, target, lag = 45) {
    let q = lastQ;
    while (addDays(addMonths(q, 3), lag) <= target) q = addMonths(q, 3);
    return q;
  }

  // 會計年度 EPS（[[結束日, EPS], …]）→ target 那天已公布的最近四季 EPS。回傳 {eps, how} 或 null。
  function calendarize(fy, target, lastQ, epsNow, extrapolate = false) {
    const qr = reportedQuarter(lastQ, target);
    const quarters = [0, 1, 2, 3].map((k) => addMonths(qr, -3 * k));
    const ends = fy.map((x) => x[0]).sort((a, b) => a - b);
    const val = new Map(fy.map((x) => [x[0].getTime(), x[1]]));
    const v = (e) => val.get(e.getTime());
    let tot = 0;
    const parts = new Map();
    const add = (k) => parts.set(k, (parts.get(k) || 0) + 1);
    for (const q of quarters) {
      const hit = ends.find((e) => addDays(addMonths(e, -12), 15) < q && q <= addDays(e, 15));
      if (hit) { tot += v(hit) / 4; add(iso(hit)); continue; }
      if (ends.length && q <= addDays(ends[0], 15) && q <= addDays(lastQ, 15) && epsNow !== null && Number.isFinite(epsNow)) {
        tot += epsNow / 4; add("目前最近四季"); continue;
      }
      const eL = ends[ends.length - 1], eP = ends[ends.length - 2];
      if (extrapolate && ends.length >= 2 && q > eL && v(eL) > 0 && v(eP) > 0) {
        const g = clip(v(eL) / v(eP), 0.7, 1.5);
        let n = 1;
        while (q > addDays(addMonths(eL, 12 * n), 15)) n += 1;
        tot += (v(eL) * Math.pow(g, n)) / 4;
        add(`外推 ${iso(addMonths(eL, 12 * n))}（年成長 ${(g - 1 >= 0 ? "+" : "")}${Math.round((g - 1) * 100)}%）`);
        continue;
      }
      return null;
    }
    return { eps: tot, how: [...parts].map(([k, n]) => `${k}×${n}/4`).join("、") };
  }

  const NAMES = {
    "預期b＋修正ab": ["市場預期的成長（b，對今天）", "你和共識的差距（a）", "你和共識的差距（b）"],
    "預期＋修正a": ["市場預期的成長（a，對今天）", "你和共識的差距（a）"],
    "修正a": ["你和共識的差距（a）"],
    "原始成長ab": ["你的 EPS 成長（a）", "你的 EPS 成長（b）"],
    "原始成長a": ["你的 EPS 成長（a）"],
  };

  // row：{px, e（今天的最近四季 EPS）, y（10 年期殖利率）, dy, v（36 個月波動）, g（類型）}
  function predict(row, h, model, ea, eb = null, ca = null, cb = null) {
    const hm = model.h[String(h)];
    const g = row.g;
    const eps0 = row.e;
    const mk = ((row.y + model.erp - (row.dy || 0)) * h) / 12;
    const ok0 = Number.isFinite(eps0) && eps0 > 0;
    const useB = pos(eb);
    let spec = "軌道", xs = [];
    if (pos(ca) && pos(ea)) {
      spec = ok0 ? (useB && pos(cb) ? "預期b＋修正ab" : "預期＋修正a") : "修正a";
      if (spec === "預期b＋修正ab") xs = [Math.log(cb / eps0), Math.log(ea / ca), Math.log(eb / cb)];
      else if (spec === "預期＋修正a") xs = [Math.log(ca / eps0), Math.log(ea / ca)];
      else xs = [Math.log(ea / ca)];
    } else if (ok0 && pos(ea)) {
      spec = useB ? "原始成長ab" : "原始成長a";
      xs = [Math.log(ea / eps0)].concat(useB ? [Math.log(eb / eps0)] : []);
    }
    const b = spec === "軌道" ? [] : hm.beta[spec][g];
    xs = xs.map((x) => clip(x, -2, 2));
    let adj = 0;
    const parts = xs.map((x, i) => { adj += b[i] * x; return { name: NAMES[spec][i], x, beta: b[i], effect: b[i] * x }; });
    const lpx = Math.log(row.px) + mk + adj;
    const band = hm.bands[spec] || hm.bands["軌道"];
    const volKnown = Number.isFinite(row.v);
    const vol = volKnown ? row.v : band.vol_median;
    const [vlo, vhi] = model.vol_clip;
    const widen = pos(ea) ? 1 : (model.loss_widen && model.loss_widen[String(h)]) || 1.6;
    const sc = Math.pow(clip(vol, vlo, vhi), model.alpha) * widen;
    const out = {
      spec, mk, adj, parts, vol, volKnown, widen, px: Math.exp(lpx),
      width: sc / Math.pow(clip(band.vol_median, vlo, vhi), model.alpha),
    };
    ["lo80", "lo50", "hi50", "hi80"].forEach((k, i) => { out["px_" + k] = Math.exp(lpx + sc * band.q[i]); });
    out.pe = pos(ea) ? out.px / ea : null;
    if (out.pe !== null) ["lo80", "lo50", "hi50", "hi80"].forEach((k) => { out["pe_" + k] = out["px_" + k] / ea; });
    out.fwd = useB ? out.px / eb : null;
    return out;
  }

  return { utc, iso, addMonths, addDays, reportedQuarter, calendarize, predict };
})();
if (typeof module !== "undefined") module.exports = OrbitCore;
