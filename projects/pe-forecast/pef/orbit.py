"""本益比軌道模型（README §16）：給你的 EPS（和市場共識，可選），算 h 個月後的本益比與股價區間。

h 個月後股價 ＝ 今天股價 × exp[(r − 股利殖利率) × h/12 ＋ 調整]，本益比 ＝ 股價 ÷ h 個月後那時已公布的最近四季 EPS
  軌道（Leibowitz 1999）：市場看法不變時，股價照資金成本漲（扣股利）。r ＝ 10 年期公債殖利率 ＋ 股權風險溢酬（預設 5%）
  調整（係數 β 依公司類型、預測距離估，results/orbit_model.json）：
    沒有共識 EPS：β_a × ln(EPS_a ÷ 今天 EPS) ［＋ β_b × ln(EPS_b ÷ 今天 EPS)］
    有共識 EPS：  β_e × ln(共識 ÷ 今天 EPS) ＋ β_s × ln(你的 EPS ÷ 共識)
                  有 b 時點時：β_e × ln(共識_b ÷ 今天 EPS) ＋ β_sa × ln(你的_a ÷ 共識_a) ＋ β_sb × ln(你的_b ÷ 共識_b)
                  （市場預期只放 b：a、b 兩個預期高度相關，一起放係數會互相抵銷、正負亂跳，見 lab_orbit.py）
  EPS_a＝h 個月後、EPS_b＝h＋12 個月後那時已公布的最近四季 EPS（GAAP 稀釋）。
區間：回測的樣本外誤差除以 波動^α、置中後的分位數（和 README §15.5 同一個做法），乘回這家的 波動^α。
虧損：EPS_a ≤ 0 → 本益比沒有定義，只給股價（方案 A），區間依回測放寬（model["loss_widen"]，約 1.3 倍）；
      EPS_b > 0 時另給 h 個月後的 forward 本益比（方案 B）。今天虧損但有共識：只用「你和共識的差距」那一項（修正a）。
"""
import numpy as np
import pandas as pd

GROUPS = {"software": "growth", "internet": "growth", "semis": "cyclical", "semicap": "cyclical", "memory": "cyclical",
          "hardware": "tech_other", "itservices": "tech_other", "gics_it": "tech_other"}
GNAME = {"cyclical": "半導體／設備／記憶體", "growth": "軟體／網路", "tech_other": "其他科技", "other": "非科技"}
LOSS_WIDEN = 1.6          # model.json 沒有 loss_widen 時的預設（舊版 README §15.4 的估計）；正式版用 orbit_fit.py 的實測值
VOL_CLIP = (0.1, 1.5)


def group_of(sector):
    return GROUPS.get(str(sector), "other")


def reported_quarter(last_qend, target, lag_days=45):
    """target 那天大概已公布到哪一季（季末 + 45 天內公布）。last_qend＝目前最新一季的季末。"""
    q = pd.Timestamp(last_qend)
    while q + pd.DateOffset(months=3) + pd.Timedelta(days=lag_days) <= pd.Timestamp(target):
        q = q + pd.DateOffset(months=3)
    return q


def calendarize(fy, target, last_qend, eps_ttm_now=None, lag_days=45, extrapolate=False):
    """會計年度 EPS 換算成「target 那天已公布的最近四季」EPS。
    fy：{會計年度結束日: EPS}（例如分析師 FY1、FY2 預估，可含已公布的 FY0 實際值）。
    做法：找出 target 那天已公布的最近四季（4 個季度），每一季算它落在哪個會計年度，按季數加權平均各年度 EPS。
    比最早的已知年度還早、而且已經公布的季（≤ last_qend），用 eps_ttm_now（目前最近四季）補；還沒公布又不在已知年度的季 → None；
    比最晚的已知年度還晚的季：
    extrapolate=True 時用最後兩年的成長率外推（每年截在 −30%～+50%），否則回傳 None（不要拿今天的 EPS 冒充未來）。
    回傳 (EPS, 用到的年度權重說明)。"""
    qr = reported_quarter(last_qend, target, lag_days)
    quarters = [qr - pd.DateOffset(months=3 * k) for k in range(4)]
    ends = sorted(pd.Timestamp(k) for k in fy)
    val = {pd.Timestamp(k): float(v) for k, v in fy.items()}
    tol = pd.Timedelta(days=15)
    tot, parts = 0.0, {}
    for q in quarters:
        # 這一季屬於「結束日 e」的年度：e − 12 個月 < 季末 ≤ e（兩邊各容許 15 天：52／53 週制的季末可能差幾天）
        hit = [e for e in ends if e - pd.DateOffset(months=12) + tol < q <= e + tol]
        if hit:
            e = hit[0]
            tot += val[e] / 4
            parts[str(e.date())] = parts.get(str(e.date()), 0) + 1
        elif ends and q <= ends[0] + tol and q <= pd.Timestamp(last_qend) + tol and eps_ttm_now is not None:  # 只補「已公布」的季
            tot += eps_ttm_now / 4
            parts["目前最近四季"] = parts.get("目前最近四季", 0) + 1
        elif extrapolate and len(ends) >= 2 and q > ends[-1] and val[ends[-1]] > 0 and val[ends[-2]] > 0:
            g = float(np.clip(val[ends[-1]] / val[ends[-2]], 0.7, 1.5))
            n = 1
            while q > ends[-1] + pd.DateOffset(months=12 * n) + tol:
                n += 1
            tot += val[ends[-1]] * g ** n / 4
            k = f"外推 {(ends[-1] + pd.DateOffset(months=12 * n)).date()}（年成長 {g - 1:+.0%}）"
            parts[k] = parts.get(k, 0) + 1
        else:
            return None, None
    return tot, "、".join(f"{k}×{v}/4" for k, v in parts.items())


def _band_scale(vol, alpha):
    return float(np.clip(vol, *VOL_CLIP) ** alpha)


def predict(row, h, model, eps_a, eps_b=None, cons_a=None, cons_b=None, erp=None):
    """row：今天的資料（px、eps0、y10、dy、vol36、sector）。h：6、12 或 24。
    eps_a、eps_b：你的 h、h＋12 個月後 EPS；cons_a、cons_b：市場共識（同口徑），沒有就 None。
    回傳 dict：股價中位與 50%／80% 區間、本益比（EPS_a ≤ 0 時為 None）、forward 本益比（方案 B）、各項拆解、用了哪個寫法。"""
    hm = model["h"][str(h)]
    g = group_of(row.get("sector"))
    px, eps0 = float(row["px"]), float(row.get("eps0", np.nan))
    y10, dy = float(row["y10"]), float(row.get("dy", 0) or 0)
    erp = model["erp"] if erp is None else erp
    mk = (y10 + erp - dy) * h / 12                                    # 軌道
    ok0 = np.isfinite(eps0) and eps0 > 0
    pos = lambda v: v is not None and np.isfinite(v) and v > 0
    use_b = pos(eps_b)
    parts, spec = [], None
    if pos(cons_a) and pos(eps_a):                                    # 有共識：預期＋修正
        spec = ("預期b＋修正ab" if (use_b and pos(cons_b)) else "預期＋修正a") if ok0 else "修正a"
        b = hm["beta"][spec][g]
        if spec == "預期b＋修正ab":
            xs = [np.log(cons_b / eps0), np.log(eps_a / cons_a), np.log(eps_b / cons_b)]
            names = ["市場預期的成長（b，對今天）", "你和共識的差距（a）", "你和共識的差距（b）"]
        elif spec == "預期＋修正a":
            xs = [np.log(cons_a / eps0), np.log(eps_a / cons_a)]
            names = ["市場預期的成長（a，對今天）", "你和共識的差距（a）"]
        else:
            xs = [np.log(eps_a / cons_a)]
            names = ["你和共識的差距（a）"]
    elif ok0 and pos(eps_a):                                          # 沒有共識：原始成長（a、b 一起給時 b 的係數較大）
        spec = "原始成長ab" if use_b else "原始成長a"
        b = hm["beta"][spec][g]
        xs = [np.log(eps_a / eps0)] + ([np.log(eps_b / eps0)] if use_b else [])
        names = ["你的 EPS 成長（a）"] + (["你的 EPS 成長（b）"] if use_b else [])
    else:                                                             # 今天或目標日虧損：只用軌道
        spec, b, xs, names = "軌道", [], [], []
    xs = [float(np.clip(v, -2, 2)) for v in xs]
    adj = float(np.dot(b, xs)) if xs else 0.0
    for n_, v, bb in zip(names, xs, b):
        parts.append(dict(項目=n_, 數值=v, β=bb, 影響=bb * v))
    lpx = np.log(px) + mk + adj
    band = hm["bands"].get(spec) or hm["bands"]["軌道"]
    vol = row.get("vol36")
    vol_known = vol is not None and np.isfinite(vol)
    vol = float(vol) if vol_known else band["vol_median"]
    widen = float(model.get("loss_widen", {}).get(str(h), LOSS_WIDEN)) if not pos(eps_a) else 1.0
    sc = _band_scale(vol, model["alpha"]) * widen
    q = band["q"]                                                     # 10/25/75/90% 分位數（ln、已除以波動^α、置中）
    out = dict(spec=spec, group=GNAME[g], group_key=g, widen=widen, mk=mk, adj=adj, parts=parts, px=float(np.exp(lpx)), vol=vol, vol_known=vol_known,
               width=sc / _band_scale(band["vol_median"], model["alpha"]))
    for k, qq in zip(("lo80", "lo50", "hi50", "hi80"), q):
        out[f"px_{k}"] = float(np.exp(lpx + sc * qq))
    if pos(eps_a):
        out["pe"] = out["px"] / eps_a
        for k in ("lo80", "lo50", "hi50", "hi80"):
            out[f"pe_{k}"] = out[f"px_{k}"] / eps_a
    else:
        out["pe"] = None
    out["fwd_pe"] = out["px"] / eps_b if use_b else None              # 方案 B：h 個月後的 forward 本益比（用 EPS_b）
    return out
