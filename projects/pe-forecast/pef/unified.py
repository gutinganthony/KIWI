"""統一模型（README §26）：軌道是模型本體，你的看法依「EPS_b 是什麼意思」決定怎麼放進去；不再依公司類型、預測距離在兩個模型間切換。

為什麼（REVIEW_2026-10-14.md §2.1、research/unified_lab.py）：
  只有共識、沒有自己的看法時，成長定價（§24）的三個成長項在代數上互相抵銷，剩下軌道；
  你給的是「基本面的 EPS 預估」時，軌道的小係數（β_s ≈ 0.03–0.11）最準——市場在目標日還不知道你預估的那個數字
  （B 模式 12 個月：軌道 0.157、成長定價 0.164、成長定價係數套在基本面預估上 0.172）；
  你給的是「市場在目標日會預期的下一年 EPS」時，成長定價的係數最準（A 模式 12 個月 0.143 vs 軌道 0.162）——這才是成長定價多出來的東西。

  市場的看法（沒有自己的看法時就是全部）：ln 股價_T ＝ ln 股價_0 ＋ 軌道 ＋ β_e × ln(共識_b ÷ 今天 EPS)      ← pef/orbit.py「預期b＋修正ab」、EPS＝共識
  EPS_b＝我的基本面預估（eb_kind="fund"，預設）：＋ β_sa × ln(EPS_a ÷ 共識_a) ＋ β_sb × ln(EPS_b ÷ 共識_b)       ← 軌道原本的看法項
  EPS_b＝市場在目標日會預期的數字（eb_kind="market"）：＋ (1 ＋ c_a) × Δa ＋ c_T × ΔT                           ← 成長定價的係數（§24.3）
      Δa ＝ ln(EPS_a ÷ 共識_a)，ΔT ＝ ln(EPS_b ÷ EPS_a) − 共識隱含的成長；對股價：EPS_a −0.16、EPS_b +0.61（12 個月非科技）
  本益比_T ＝ 股價_T ÷ EPS_a（沒給＝共識）。共識隱含的成長＝ln(共識_b ÷ 共識_a)；沒有下一財年共識時用回歸 GT ＝ a ＋ λ × ln(F_0 ÷ 今天 EPS)。
  6 個月沒有成長定價係數（market 退回 fund 並註明）；沒有共識或今天虧損 → 整個退回 pef/orbit.predict。
區間（依輸入模式）：
  共識模式（沒有任何看法）：conformal——用已到期配對在「只有共識」時的實際誤差校準（results/conformal.json，research/conformal_fit.py），
    乘 波動^α × exp(δ × |ln(共識 EPS_a ÷ 今天 EPS)|)。正式版區間是用「EPS 猜對」的殘差校準的，拿來包共識輸入太窄（§25.1 涵蓋 57–63%）。
  fund：軌道「預期b＋修正ab」的區間（假設你的 EPS 對，剩下的是模型誤差）；market：成長定價的區間（gm q、δ；A 模式的殘差）。
相對輸出（§26.3）由網頁／命令列用同一天全部 S&P 500 的共識模式預測算中位數與百分位，這裡不算。
"""
import json
import os

import numpy as np

from pef import orbit
from pef import growth_price as GP

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
BANDK = ("lo80", "lo50", "hi50", "hi80")
_C = {}


def pos(v):
    return v is not None and np.isfinite(v) and v > 0


def load_conformal(res=RES):
    p = os.path.join(res, "conformal.json")
    if p not in _C:
        _C[p] = json.load(open(p)) if os.path.exists(p) else None
    return _C[p]


def conformal_q(cq, h, grp):
    """共識模式的區間分位數那一組（dict：q＝本益比 [10, 25, 75, 90]%，pe／px／eps＝各水準的 [低, 高]；都已除以 波動^α × EPS 放寬，eps 除外）：
    組別（科技／非科技）樣本夠就用組別的，否則用全部。沒有 → (None, None)。"""
    if not cq or "h" not in cq or str(h) not in cq["h"]:
        return None, None
    c = cq["h"][str(h)]
    key = "tech" if grp != "other" else "other"
    if c.get(key) and c[key].get("n", 0) >= cq.get("min_n", 300):
        return c[key], ("科技" if key == "tech" else "非科技")
    return c["pooled"], "全部"


def predict(row, h, model=None, gm=None, cq=None, eps_a=None, eps_b=None, eb_kind="fund", cons_a=None, cons_b=None, fwd0=None,
            rate=None, band_mult=1.0, year=None, erp=None):
    """row：px、eps0、y10、dy、vol36、sector 或 grp。eps_a／eps_b＝你的 EPS（可空＝用共識）；eb_kind＝EPS_b 的意思（"fund" 基本面預估／"market" 市場在目標日會預期的數字）；
    cons_a／cons_b＝共識（已乘係數、目標日口徑）；fwd0＝今天共識的未來 12 個月 EPS（算回歸的成長預期用；空＝cons_a）；year＝回測用的走動式係數年份。
    回傳 dict：和 orbit.predict 同樣的欄位，另有 mode（共識／看法／軌道）、kind（fund／market／None）、band_kind（conformal／模型）、band_group、
    eps_a、eps_b（實際用的）、gt_cons（共識隱含的目標日成長）、view（market 時的 Δa、ΔT 與係數）、note。"""
    model = model or orbit.load_model()
    gm = gm or GP.load()
    cq = load_conformal() if cq is None else cq
    px, eps0 = float(row["px"]), float(row.get("eps0", np.nan))
    g = row.get("grp") if row.get("grp") in orbit.GNAME else orbit.group_of(row.get("sector"))
    given = lambda v: v is not None and np.isfinite(v)
    have_cons = pos(cons_a)
    ea = float(eps_a) if given(eps_a) else (float(cons_a) if have_cons else None)
    eb = float(eps_b) if given(eps_b) else (float(cons_b) if (have_cons and pos(cons_b)) else None)
    have_view = given(eps_a) or given(eps_b)
    if not (have_cons and pos(eps0) and px > 0 and pos(ea) and (eb is None or pos(eb))):
        # 沒有共識、今天虧損、或你的 EPS ≤ 0：和以前一樣交給軌道那一套（含虧損版、轉盈放寬）；沒有 conformal
        o = orbit.predict(row, h, model, ea, eb, cons_a if have_cons else None, cons_b if have_cons else None, erp=erp, rate=rate, band_mult=band_mult)
        o.update(mode=("看法" if have_view else "共識") if have_cons else "軌道", kind="fund" if (have_view and have_cons) else None,
                 band_kind="模型", band_group=None, eps_a=ea, eps_b=eb, gt_cons=None, view=None, note=None)
        o["decomp"] = _decomp(o, row, ea)
        return o
    growth_ok = gm is not None and str(h) in gm["h"] and (year is None or str(year) in gm["by_year"][str(h)])
    f0 = float(fwd0) if pos(fwd0) else float(cons_a)
    if pos(cons_b):                                      # 共識隱含的「目標日時下一年的成長」
        gt_cons, cb = float(np.clip(np.log(cons_b / cons_a), -1.5, 1.5)), float(cons_b)
    elif growth_ok:
        ebh = GP.eps_b_hat(gm, h, cons_a, eps0, f0, year)
        gt_cons = float(np.log(ebh / cons_a)) if ebh else None
        cb = float(ebh) if ebh else None
    else:
        gt_cons, cb = None, None
    if not given(eps_b):
        eb = cb                                          # 沒給 EPS_b：用共識的（沒有下一財年共識時用回歸的 EPS_b）
    note = None
    market = eb_kind == "market" and pos(eps_b)
    if market and not (growth_ok and gt_cons is not None):
        market, note = False, "6 個月沒有成長定價係數（或算不出共識隱含的成長）：EPS_b 當作基本面預估處理"
    if market:                                           # EPS_b＝市場在目標日會預期的數字：成長定價的係數，相對於共識
        base = orbit.predict(row, h, model, cons_a, cb, cons_a, cb, erp=erp, rate=rate, band_mult=band_mult)
        c = GP.coefs(gm, h, g, year)
        da = float(np.clip(np.log(ea / cons_a), -2, 2))
        dT = float(np.clip(np.log(eb / ea) - gt_cons, -1.5, 1.5))
        adj_v = (1 + c[1]) * da + c[2] * dT
        lpx = np.log(base["px"]) + adj_v
        b = gm["h"][str(h)]
        eps_widen = float(np.exp(float(b.get("delta", 0.0)) * min(abs(np.log(ea / eps0)), 2.0)))
        sc = float(np.clip(base["vol"], *orbit.VOL_CLIP) ** model["alpha"]) * band_mult * eps_widen
        o = dict(base)
        o.update(spec="統一模型：EPS_b＝市場預期", adj=base["adj"] + adj_v, px=float(np.exp(lpx)), eps_widen=eps_widen, widen=1.0,
                 width=sc / float(np.clip(b["vol_median"], *orbit.VOL_CLIP) ** model["alpha"]),
                 parts=[p for p in base["parts"] if not p["項目"].startswith("你和共識的差距")]      # 基準是共識本身，差距項恆為 0
                 + [dict(項目="你的 EPS_a 和共識的差距（Δa）", 數值=da, β=1 + c[1], 影響=(1 + c[1]) * da),
                                              dict(項目="你的 EPS_b（市場預期）隱含的成長和共識的差距（ΔT）", 數值=dT, β=c[2], 影響=c[2] * dT)],
                 view=dict(da=da, dT=dT, c_a=c[1], c_T=c[2]), kind="market")
        orbit.apply_band(o, lpx, sc, b["q"], b.get("levels"))                       # px_lo50…px_hi90（本益比在 _pe 算）
    else:                                                # 基本面預估（或只有共識）：軌道的看法項
        o = orbit.predict(row, h, model, ea, eb, cons_a, cb, erp=erp, rate=rate, band_mult=band_mult)
        o.update(spec="統一模型：" + o["spec"], view=None, kind="fund" if have_view else None)
    o.update(mode="看法" if have_view else "共識", eps_a=ea, eps_b=eb, gt_cons=gt_cons, band_group=None, band_kind="模型", note=note)
    pe_own = _conformal_band(o, h, g, model, cq, band_mult, ea, eps0) if not have_view else False
    _pe(o, ea, eb, skip_band=pe_own)
    o["decomp"] = _decomp(o, row, ea)
    return o


def _pe(o, ea, eb, skip_band=False):
    o["pe"] = o["px"] / ea if pos(ea) else None
    if not skip_band:
        for L in o.get("band_levels") or (50, 80):
            o[f"pe_lo{L}"] = o[f"px_lo{L}"] / ea if pos(ea) else None
            o[f"pe_hi{L}"] = o[f"px_hi{L}"] / ea if pos(ea) else None
    o["fwd_pe"] = o["px"] / eb if pos(eb) else None


def _decomp(o, row, ea):
    """§27：股價變化 ＝ EPS 成長 ＋ 本益比重估（ln）：ln(預測股價 ÷ 今天) ＝ ln(EPS_a ÷ 今天 EPS) ＋ ln(預測本益比 ÷ 今天本益比)。本益比沒有定義時 None。"""
    px0, eps0 = float(row["px"]), float(row.get("eps0", np.nan))
    if not (pos(ea) and pos(eps0) and px0 > 0 and o.get("pe")):
        return None
    pe0 = px0 / eps0
    return dict(eps_g=float(np.log(ea / eps0)), pe_ch=float(np.log(o["pe"] / pe0)), total=float(np.log(o["px"] / px0)), pe0=pe0)


def _conformal_band(o, h, g, model, cq, band_mult, ea, eps0):
    """共識模式的區間：conformal 分位數 × 波動^α × exp(δ × |ln(共識 EPS_a ÷ 今天 EPS)|) × 放寬倍數。沒有 conformal.json 時保留原本的區間。
    §27：股價（px）與本益比（pe）各自校準、每個水準都給；另給共識 EPS 本身的區間 eps_lo{L}／eps_hi{L}（＝共識 × exp(歷史共識誤差的分位數)）。
    舊的 conformal.json 只有本益比的 q：照舊套在股價上、本益比 ＝ 股價 ÷ EPS_a。回傳 True ＝ 本益比區間已自己寫好（_pe 不要再用股價除）。"""
    gq, grp_lab = conformal_q(cq, h, g)
    if gq is None:
        return False
    lpx = np.log(o["px"])
    delta = float((model.get("band_delta") or {}).get(str(h), 0.0))
    eps_widen = float(np.exp(delta * min(abs(np.log(ea / eps0)), 2.0)))
    sc = float(np.clip(o["vol"], *orbit.VOL_CLIP) ** model["alpha"]) * band_mult * eps_widen
    vmed = cq["h"][str(h)]["vol_median"]
    o.update(band_kind="conformal", band_group=grp_lab, eps_widen=eps_widen, width=sc / float(np.clip(vmed, *orbit.VOL_CLIP) ** model["alpha"]))
    if gq.get("px") and gq.get("pe"):
        lpe = lpx - np.log(ea)
        o["band_levels"] = sorted(int(k) for k in gq["px"])
        for L, (lo, hi) in gq["px"].items():
            o[f"px_lo{L}"], o[f"px_hi{L}"] = float(np.exp(lpx + sc * lo)), float(np.exp(lpx + sc * hi))
        for L, (lo, hi) in gq["pe"].items():
            o[f"pe_lo{L}"], o[f"pe_hi{L}"] = float(np.exp(lpe + sc * lo)), float(np.exp(lpe + sc * hi))
        for L, (lo, hi) in (gq.get("eps") or {}).items():
            o[f"eps_lo{L}"], o[f"eps_hi{L}"] = float(ea * np.exp(lo)), float(ea * np.exp(hi))
        return True
    o["band_levels"] = [50, 80]
    for k, qq in zip(BANDK, gq["q"]):
        o[f"px_{k}"] = float(np.exp(lpx + sc * qq))
    return False
