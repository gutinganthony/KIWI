"""成長定價（README §24）：市場在目標日依「那時對下一年的成長預期」給新的本益比。

軌道模型（pef/orbit.py）的股價對 EPS 反應很小，EPS 調高 → 本益比往下。但市場大致是「對下一年的 EPS 給倍數」：
同一個月橫斷面，ln(本益比) 對 ln(下一年預期 ÷ 最近四季 EPS) 的斜率約 1.0（research/rerating_lab.py §0）。
所以目標日的本益比要看「目標日那時，市場對再下一年的成長預期」——這個模型把它放進來：

  ln 本益比_h ＝ ln 今天本益比 ＋ 軌道 ＋ a ＋ c_a × ln(EPS_a ÷ 今天 EPS)        交出的成長（越多，本益比越被稀釋）
                                         ＋ c_T × ln(EPS_b ÷ EPS_a)           目標日的成長預期（越高，本益比越高＝重新評價）
                                         ＋ c_0 × ln(F_0 ÷ 今天 EPS)           今天已經反映的成長預期（已經在今天的本益比裡）
                                         ＋ c_r × 過去 12 個月 ln 報酬          （漲多的，之後倍數被追上來的獲利稀釋）
  股價 ＝ 本益比 × EPS_a。EPS_a＝h 個月後已公布的最近四季 EPS；EPS_b＝目標日時市場預期的下一個 12 個月 EPS
  （＝h＋12 個月後的最近四季 EPS）；F_0＝今天市場預期的下一個 12 個月 EPS（共識 × 校正係數）。都是 GAAP 口徑。
係數：research/growth_price_fit.py 用 I/B/E/S 共識配對（S&P 500，起點 2012–2023）估（Huber），results/growth_price.json。
只有 12、24 個月；需要 今天 EPS、EPS_a、EPS_b、F_0 都 > 0。區間＝走動式誤差的分位數 × 波動^α × exp(δ × min(|ga|, 2))（和軌道模型同一套做法）。
"""
import json
import os

import numpy as np
import pandas as pd

from pef import orbit

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
FEATS = ["ga", "GT", "G0", "ret12c"]
CLIP = {"ga": 2.0, "GT": 1.5, "G0": 1.5, "ret12c": 1.0}
NAMES = {"ga": "交出的 EPS 成長（EPS_a ÷ 今天）", "GT": "目標日的成長預期（EPS_b ÷ EPS_a）",
         "G0": "今天已反映的成長預期（共識 ÷ 今天）", "ret12c": "過去 12 個月報酬（ln）"}
_C = {}


def adr_ret12(ticker, px_now, d_now):
    """外國 ADR 的過去 12 個月 ln 報酬（data/adr_hist.csv.gz 的月底股價，12～14 個月前那個月底）；沒有資料回傳 None。網頁和命令列共用。"""
    p = os.path.join(os.path.dirname(RES), "data", "adr_hist.csv.gz")
    if "adr_hist" not in _C:
        _C["adr_hist"] = pd.read_csv(p, parse_dates=["month_end"], usecols=["ticker", "month_end", "px"]) if os.path.exists(p) else None
    h = _C["adr_hist"]
    if h is None or not px_now or not px_now > 0:
        return None
    d_now = pd.Timestamp(d_now)
    g = h[(h["ticker"] == ticker) & (h["month_end"] <= d_now - pd.DateOffset(months=12))].sort_values("month_end")
    if g.empty or g["month_end"].iloc[-1] < d_now - pd.DateOffset(months=14) or not g["px"].iloc[-1] > 0:
        return None
    return float(np.log(px_now / float(g["px"].iloc[-1])))


def load(res=RES):
    p = os.path.join(res, "growth_price.json")
    if p not in _C:
        _C[p] = json.load(open(p)) if os.path.exists(p) else None
    return _C[p]


def coefs(gm, h, grp, year=None):
    """組別 grp 的係數 [a, c_a, c_T, c_0, c_r]：非科技用自己的，科技三組共用全部一起估的（科技樣本太小）。
    year 給了就用走動式版本（只用目標日在 year 年以前的配對估；回測用）。"""
    src = gm["by_year"][str(h)][str(year)] if year is not None else gm["h"][str(h)]["coef"]
    return src["other"] if grp == "other" and "other" in src else src["all"]


def eps_b_hat(gm, h, eps_a, eps0, fwd0, year=None):
    """沒有自己看法時的 EPS_b（目標日時市場預期的下一年）：EPS_a × exp(a ＋ λ × ln(F_0 ÷ 今天 EPS))。
    市場的成長預期會強烈回歸（正式版 λ 12 個月約 0.16、24 個月約 0.09，README §24.7）；直接把今天的成長率延伸一年會高估。"""
    src = gm["by_year"][str(h)][str(year)] if year is not None else gm["h"][str(h)]
    a, lam = src["gt_hat"]
    if not (eps_a and eps_a > 0 and eps0 and eps0 > 0 and fwd0 and fwd0 > 0):
        return None
    return float(eps_a * np.exp(a + lam * float(np.clip(np.log(fwd0 / eps0), -CLIP["G0"], CLIP["G0"]))))


def features(eps0, eps_a, eps_b, fwd0, ret12):
    pos = lambda v: v is not None and np.isfinite(v) and v > 0
    if not (pos(eps0) and pos(eps_a) and pos(eps_b) and pos(fwd0)):
        return None
    r = 0.0 if ret12 is None or not np.isfinite(ret12) else float(ret12)
    x = dict(ga=np.log(eps_a / eps0), GT=np.log(eps_b / eps_a), G0=np.log(fwd0 / eps0), ret12c=r)
    return {k: float(np.clip(v, -CLIP[k], CLIP[k])) for k, v in x.items()}


def predict(row, h, eps_a, eps_b, fwd0, ret12, model=None, gm=None, rate=None, band_mult=1.0, year=None):
    """row：px、eps0、y10、dy、vol36、sector 或 grp（和 orbit.predict 一樣）。回傳和 orbit.predict 同樣欄位的 dict；不適用時回傳 None。"""
    model = model or orbit.load_model()
    gm = gm or load()
    if gm is None or str(h) not in gm["h"]:
        return None
    px, eps0 = float(row["px"]), float(row.get("eps0", np.nan))
    x = features(eps0, eps_a, eps_b, fwd0, ret12)
    if x is None or not px > 0:
        return None
    g = row.get("grp") if row.get("grp") in orbit.GNAME else orbit.group_of(row.get("sector"))
    c = coefs(gm, h, g, year)
    mk = (float(row["y10"]) + model["erp"] - float(row.get("dy", 0) or 0)) * h / 12
    parts = [dict(項目="常數（歷史上倍數的平均變化）", 數值=1.0, β=c[0], 影響=c[0])]
    adj = c[0]
    for k, cc in zip(FEATS, c[1:]):
        adj += cc * x[k]
        parts.append(dict(項目=NAMES[k], 數值=x[k], β=cc, 影響=cc * x[k]))
    if rate is not None and rate[0]:
        adj += float(rate[0]) * float(rate[1])
        parts.append(dict(項目="你的利率看法（10 年期變化，百分點）", 數值=float(rate[0]), β=float(rate[1]), 影響=float(rate[0]) * float(rate[1])))
    lpe = np.log(px / eps0) + mk + adj
    lpx = lpe + np.log(eps_a)
    b = gm["h"][str(h)]
    vol = row.get("vol36")
    vol_known = vol is not None and np.isfinite(vol)
    vol = float(vol) if vol_known else b["vol_median"]
    eps_widen = float(np.exp(float(b.get("delta", 0.0)) * min(abs(x["ga"]), 2.0)))            # EPS 變化越大區間越寬
    sc = float(np.clip(vol, *orbit.VOL_CLIP) ** model["alpha"]) * band_mult * eps_widen
    out = dict(spec="成長定價", group=orbit.GNAME[g], group_key=g, widen=1.0, band_mult=band_mult, eps_widen=eps_widen, mk=mk, adj=adj, parts=parts,
               px=float(np.exp(lpx)), vol=vol, vol_known=vol_known,
               width=sc / float(np.clip(b["vol_median"], *orbit.VOL_CLIP) ** model["alpha"]), x=x)
    for k, qq in zip(("lo80", "lo50", "hi50", "hi80"), b["q"]):
        out[f"px_{k}"] = float(np.exp(lpx + sc * qq))
        out[f"pe_{k}"] = out[f"px_{k}"] / eps_a
    out["pe"] = out["px"] / eps_a
    out["fwd_pe"] = out["px"] / eps_b
    out["pe_today"] = px / eps0
    return out
