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
    "虧損：EPS 變化": ["EPS 變化 ÷ 今天股價（虧損版）"],
  };

  // 利率情境：每升 1 個百分點的 ln 影響（和 pef/orbit.py 的 rate_slope 相同）。rs＝results/rate_sensitivity.json；pr＝本益比百分位（null＝0.5）
  function rateSlope(rs, h, regime, pr) {
    const c = rs.regimes[String(regime)].h[String(h)];
    const p = pr === null || pr === undefined || !Number.isFinite(pr) ? 0.5 : clip(pr, 1 / 6, 5 / 6);
    return c.mkt + (c.dur * (p - 0.5)) / (2 / 3);
  }

  // row：{px, e（今天的最近四季 EPS）, y（10 年期殖利率）, dy, v（36 個月波動）, g（類型）}；rate：[10 年期變化（百分點）, 斜率] 或 null
  // bandMult：區間再乘的倍數（中小型股、外國 ADR；pef/orbit.py 的 band_widen）
  function predict(row, h, model, ea, eb = null, ca = null, cb = null, rate = null, bandMult = 1) {
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
    } else if (Number.isFinite(eps0) && ea !== null && Number.isFinite(ea) && row.px > 0 && model.loss_beta && model.loss_beta[String(h)] !== undefined) {
      spec = "虧損：EPS 變化";                                    // 成長率算不出來：EPS 變化 ÷ 今天股價（§20.5）
      xs = [clip((ea - eps0) / row.px, -1, 1)];
    }
    const b = spec === "軌道" ? [] : spec === "虧損：EPS 變化" ? [model.loss_beta[String(h)]] : hm.beta[spec][g];
    xs = xs.map((x) => clip(x, -2, 2));
    let adj = 0;
    const parts = xs.map((x, i) => { adj += b[i] * x; return { name: NAMES[spec][i], x, beta: b[i], effect: b[i] * x }; });
    if (rate && rate[0]) { adj += rate[0] * rate[1]; parts.push({ name: "你的利率看法（10 年期變化，百分點）", x: rate[0], beta: rate[1], effect: rate[0] * rate[1] }); }
    const lpx = Math.log(row.px) + mk + adj;
    const band = hm.bands[spec] || hm.bands["軌道"];
    const volKnown = Number.isFinite(row.v);
    const vol = volKnown ? row.v : band.vol_median;
    const [vlo, vhi] = model.vol_clip;
    const widen = !pos(ea) ? (model.loss_widen && model.loss_widen[String(h)]) || 1.6
      : !ok0 ? (model.turn_widen && model.turn_widen[String(h)]) || 1 : 1;            // 今天虧損、EPS_a > 0（轉盈）
    let epsWiden = 1;                                                                 // EPS 變化越大區間越寬（README §22.4）
    if (spec !== "軌道" && spec !== "虧損：EPS 變化" && ok0 && pos(ea) && model.band_delta)
      epsWiden = Math.exp((model.band_delta[String(h)] || 0) * Math.min(Math.abs(Math.log(ea / row.e)), 2));
    const sc = Math.pow(clip(vol, vlo, vhi), model.alpha) * widen * bandMult * epsWiden;
    const out = {
      spec, mk, adj, parts, vol, volKnown, widen, bandMult, epsWiden, px: Math.exp(lpx),
      width: sc / Math.pow(clip(band.vol_median, vlo, vhi), model.alpha),
    };
    ["lo80", "lo50", "hi50", "hi80"].forEach((k, i) => { out["px_" + k] = Math.exp(lpx + sc * band.q[i]); });
    out.pe = pos(ea) ? out.px / ea : null;
    if (out.pe !== null) ["lo80", "lo50", "hi50", "hi80"].forEach((k) => { out["pe_" + k] = out["px_" + k] / ea; });
    out.fwd = useB ? out.px / eb : null;
    return out;
  }

  return { utc, iso, addMonths, addDays, reportedQuarter, calendarize, predict, rateSlope };
})();
if (typeof module !== "undefined") module.exports = OrbitCore;
