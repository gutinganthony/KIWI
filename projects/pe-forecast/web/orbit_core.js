// 本益比軌道模型的計算核心：和 pef/orbit.py 的 reported_quarter、calendarize、predict（以及 pef/growth_price.py 的 predict、pef/unified.py 的 predict）一模一樣（make_orbit_page.py 嵌進網頁；
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

  // 成長定價（和 pef/growth_price.py 的 predict 相同，README §24）：市場在目標日依「那時對下一年的成長預期」給新的本益比。
  // gp：results/growth_price.json 的 h（coef、q、delta、vol_median）；f0＝今天市場預期的下一個 12 個月 EPS；r12＝過去 12 個月 ln 報酬（沒有＝0）
  const GFEATS = ["ga", "GT", "G0", "ret12c"];
  const GNAMES = { ga: "交出的 EPS 成長（EPS_a ÷ 今天）", GT: "目標日的成長預期（EPS_b ÷ EPS_a）",
    G0: "今天已反映的成長預期（共識 ÷ 今天）", ret12c: "過去 12 個月報酬（ln）" };
  function predictGrowth(row, h, model, gp, ea, eb, f0, r12, rate = null, bandMult = 1) {
    const gh = gp && gp.h && gp.h[String(h)];
    const eps0 = row.e;
    if (!gh || !(pos(eps0) && pos(ea) && pos(eb) && pos(f0)) || !(row.px > 0)) return null;
    const r = r12 === null || r12 === undefined || !Number.isFinite(r12) ? 0 : r12;
    const x = { ga: clip(Math.log(ea / eps0), -2, 2), GT: clip(Math.log(eb / ea), -1.5, 1.5), G0: clip(Math.log(f0 / eps0), -1.5, 1.5), ret12c: clip(r, -1, 1) };
    const c = row.g === "other" && gh.coef.other ? gh.coef.other : gh.coef.all;
    const mk = ((row.y + model.erp - (row.dy || 0)) * h) / 12;
    let adj = c[0];
    const parts = [{ name: "常數（歷史上倍數的平均變化）", x: 1, beta: c[0], effect: c[0] }];
    GFEATS.forEach((k, i) => { adj += c[i + 1] * x[k]; parts.push({ name: GNAMES[k], x: x[k], beta: c[i + 1], effect: c[i + 1] * x[k] }); });
    if (rate && rate[0]) { adj += rate[0] * rate[1]; parts.push({ name: "你的利率看法（10 年期變化，百分點）", x: rate[0], beta: rate[1], effect: rate[0] * rate[1] }); }
    const lpx = Math.log(row.px / eps0) + mk + adj + Math.log(ea);
    const volKnown = Number.isFinite(row.v);
    const vol = volKnown ? row.v : gh.vol_median;
    const [vlo, vhi] = model.vol_clip;
    const epsWiden = Math.exp((gh.delta || 0) * Math.min(Math.abs(x.ga), 2));
    const sc = Math.pow(clip(vol, vlo, vhi), model.alpha) * bandMult * epsWiden;
    const out = { spec: "成長定價", mk, adj, parts, x, vol, volKnown, widen: 1, bandMult, epsWiden, px: Math.exp(lpx),
      width: sc / Math.pow(clip(gh.vol_median, vlo, vhi), model.alpha) };
    ["lo80", "lo50", "hi50", "hi80"].forEach((k, i) => { out["px_" + k] = Math.exp(lpx + sc * gh.q[i]); out["pe_" + k] = out["px_" + k] / ea; });
    out.pe = out.px / ea;
    out.fwd = out.px / eb;
    return out;
  }

  // 統一模型（和 pef/unified.py 的 predict 相同，README §26）：軌道是本體；你的 EPS_b 依「意思」分流——基本面預估走軌道的 β_s，
  // 市場在目標日會預期的數字走成長定價的係數 (1 ＋ c_a) × Δa ＋ c_T × ΔT；只有共識（沒有自己的看法）時區間改用 conformal（cq＝results/conformal.json）。
  // ea、eb：你的 EPS（null＝用共識）；ebKind："fund"（預設）或 "market"；ca、cb：共識（已乘係數、目標日口徑）；f0：今天共識的未來 12 個月 EPS（null＝ca）
  function conformalQ(cq, h, g) {
    if (!cq || !cq.h || !cq.h[String(h)]) return [null, null];
    const c = cq.h[String(h)];
    const key = g !== "other" ? "tech" : "other";
    if (c[key] && (c[key].n || 0) >= (cq.min_n || 300)) return [c[key].q, key === "tech" ? "科技" : "非科技"];
    return [c.pooled.q, "全部"];
  }
  const given = (v) => v !== null && v !== undefined && Number.isFinite(v);
  function predictUnified(row, h, model, gp, cq, ea, eb, ebKind = "fund", ca = null, cb = null, f0 = null, rate = null, bandMult = 1) {
    const eps0 = row.e, g = row.g;
    const haveCons = pos(ca);
    let eaU = given(ea) ? ea : haveCons ? ca : null;
    let ebU = given(eb) ? eb : (haveCons && pos(cb)) ? cb : null;
    const haveView = given(ea) || given(eb);
    const K = ["lo80", "lo50", "hi50", "hi80"];
    const [vlo, vhi] = model.vol_clip;
    if (!(haveCons && pos(eps0) && row.px > 0 && pos(eaU) && (ebU === null || pos(ebU)))) {
      const o = predict(row, h, model, eaU, ebU, haveCons ? ca : null, haveCons ? cb : null, rate, bandMult);
      Object.assign(o, { mode: haveCons ? (haveView ? "看法" : "共識") : "軌道", kind: haveView && haveCons ? "fund" : null, bandKind: "模型", bandGroup: null,
        epsA: eaU, epsB: ebU, gtCons: null, view: null, note: null });
      return o;
    }
    const gh = gp && gp.h && gp.h[String(h)];
    const growthOk = !!gh;
    const f0U = pos(f0) ? f0 : ca;
    let gtCons = null, cbU = null;
    if (pos(cb)) { gtCons = clip(Math.log(cb / ca), -1.5, 1.5); cbU = cb; }
    else if (growthOk) {                                                                  // 沒有下一財年共識：回歸的目標日成長預期（pef/growth_price.py eps_b_hat）
      const [a0, lam] = gh.gt_hat;
      cbU = ca * Math.exp(a0 + lam * clip(Math.log(f0U / eps0), -1.5, 1.5));
      gtCons = Math.log(cbU / ca);
    }
    if (!given(eb)) ebU = cbU;
    let note = null;
    let market = ebKind === "market" && pos(eb);
    if (market && !(growthOk && gtCons !== null)) { market = false; note = "6 個月沒有成長定價係數（或算不出共識隱含的成長）：EPS_b 當作基本面預估處理"; }
    let o;
    if (market) {
      const base = predict(row, h, model, ca, cbU, ca, cbU, rate, bandMult);
      const c = g === "other" && gh.coef.other ? gh.coef.other : gh.coef.all;
      const da = clip(Math.log(eaU / ca), -2, 2);
      const dT = clip(Math.log(ebU / eaU) - gtCons, -1.5, 1.5);
      const adjV = (1 + c[1]) * da + c[2] * dT;
      const lpx = Math.log(base.px) + adjV;
      const epsWiden = Math.exp((gh.delta || 0) * Math.min(Math.abs(Math.log(eaU / eps0)), 2));
      const sc = Math.pow(clip(base.vol, vlo, vhi), model.alpha) * bandMult * epsWiden;
      o = Object.assign({}, base, { spec: "統一模型：EPS_b＝市場預期", adj: base.adj + adjV, px: Math.exp(lpx), epsWiden, widen: 1,
        width: sc / Math.pow(clip(gh.vol_median, vlo, vhi), model.alpha),
        parts: base.parts.concat([{ name: "你的 EPS_a 和共識的差距（Δa）", x: da, beta: 1 + c[1], effect: (1 + c[1]) * da },
          { name: "你的 EPS_b（市場預期）隱含的成長和共識的差距（ΔT）", x: dT, beta: c[2], effect: c[2] * dT }]),
        view: { da, dT, cA: c[1], cT: c[2] }, kind: "market" });
      K.forEach((k, i) => { o["px_" + k] = Math.exp(lpx + sc * gh.q[i]); });
    } else {
      o = predict(row, h, model, eaU, ebU, ca, cbU, rate, bandMult);
      Object.assign(o, { spec: "統一模型：" + o.spec, view: null, kind: haveView ? "fund" : null });
    }
    Object.assign(o, { mode: haveView ? "看法" : "共識", epsA: eaU, epsB: ebU, gtCons, bandGroup: null, bandKind: "模型", note });
    if (!haveView) {                                                                       // 共識模式：conformal 區間
      const [q, grpLab] = conformalQ(cq, h, g);
      if (q) {
        const lpx = Math.log(o.px);
        const delta = (model.band_delta && model.band_delta[String(h)]) || 0;
        const epsWiden = Math.exp(delta * Math.min(Math.abs(Math.log(eaU / eps0)), 2));
        const sc = Math.pow(clip(o.vol, vlo, vhi), model.alpha) * bandMult * epsWiden;
        Object.assign(o, { bandKind: "conformal", bandGroup: grpLab, epsWiden, width: sc / Math.pow(clip(cq.h[String(h)].vol_median, vlo, vhi), model.alpha) });
        K.forEach((k, i) => { o["px_" + k] = Math.exp(lpx + sc * q[i]); });
      }
    }
    o.pe = pos(eaU) ? o.px / eaU : null;
    K.forEach((k) => { o["pe_" + k] = o.pe === null ? null : o["px_" + k] / eaU; });
    o.fwd = pos(ebU) ? o.px / ebU : null;
    return o;
  }

  return { utc, iso, addMonths, addDays, reportedQuarter, calendarize, predict, predictGrowth, predictUnified, conformalQ, rateSlope };
})();
if (typeof module !== "undefined") module.exports = OrbitCore;
