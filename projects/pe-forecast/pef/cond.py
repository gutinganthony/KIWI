"""給定未來 EPS，預測那時的本益比與股價（README §15）。

使用情境：你對「h 個月後、那時已公布的最近四季 EPS」有自己的預估。模型回答：到那時市場大概給幾倍本益比？
股價區間 ＝ 本益比區間 × 你的 EPS。

恆等式（每股口徑；本益比＝股價 ÷ 最近四季稀釋 EPS，兩邊用同一個股數）：

    ln PE(t+h) = ln[ P(t) ÷ EPS(t+h) ]  +  ln[ P(t+h) ÷ P(t) ]
               =  今天股價下的前瞻本益比   +  這段期間的股價報酬（不含股利）

EPS 給定之後，第一項就確定了，要預測的只剩股價報酬，而且是「已知盈餘會變成 EPS(t+h)」條件下的報酬。
回測（lab_cond.py）發現：盈餘變化大多早就反映在今天的股價裡，EPS 成長對同期股價的影響很小（Huber 斜率約 0.04）；
股價報酬裡「整個市場一起動」的部分預測不了，模型硬學會學到過去幾次大盤反彈（2016、2020），拿到新年度就失效。
所以正式模型把報酬拆成兩塊：

    股價報酬 ＝ 大盤部分（固定＝資金成本：10 年期 ＋ 5%，連續複利）＋ 個股相對大盤的部分（線性，Huber）

個股部分只用今天就算得出來的線索：EPS 成長、今天股價下的前瞻本益比、本益比相對同業、12 個月動能、營收成長、
股利殖利率、股價波動。另有「也知道再下一年 EPS」的版本（xs2，只有 12 個月）：兩年後的 EPS 比一年後的更能解釋
一年後的股價（市場看的是前面）。

目標的時間口徑：t+h 月底「已公布」的最近四季（和市場報價的 trailing 本益比一樣）。例：2027-09-30 時，
6 月底結束的那一季已經公布，9 月底結束的還沒 → 最近四季＝2026-07～2027-06。

時間界線（每一次訓練都檢查，見 walk）：
  - 特徵：只用 t 月底以前已公布的財報與 t 月底的股價。
  - 訓練標籤：t+h 月底 ≤ 訓練截止日（答案在訓練當時已揭曉）；橫斷面去平均用的「同月份報酬中位數」也是標籤的一部分。
  - 區間校準：只用訓練截止日以前已揭曉的樣本外誤差。
"""
import numpy as np
import pandas as pd

from . import lab
from .stats import huber_ols

HORIZONS = (6, 12, 18, 24, 36)
ERP = lab.ERP
VERSION = "cond-2026-09-30"
BAND_ALPHA = 0.7            # 區間寬度 ∝ 股價波動^0.7（lab_cond.py 只在選模期挑的，README §15.5）
VOL_CLIP = (0.1, 1.5)       # 波動先截在 10%～150%（年化）

# 研究用（lab_cond.py 比較用；正式模型是 xs、xs2）
FEATS_GBM = ["lfpe", "geps", "neg0", "ln_pe", "pe_sec", "pe_mkt", "pe_own", "ln_ps", "ey_ttm", "g_rev", "acc", "g_qoq", "gap",
             "m_ttm", "m_bar", "sigma", "ln_mc", "dy", "lev", "ret6", "ret12", "vol36", "y10", "sector_id"]
FEATS_GBM_XS = [f for f in FEATS_GBM if f not in ("pe_mkt", "y10", "pe_sec", "pe_own")] + ["pe_rel_sec", "pe_rel_own"]
FEATS_LIN_ABS = ["geps", "lfpe", "pe_rel_sec", "pe_rel_own", "ret12", "ret6", "g_rev", "gap", "dy", "y10", "vol36"]
# 正式模型：只用「現在的資料也算得出來」的線索（沒有「自己過去 5 年本益比」：非 S&P 500 公司現在沒有那麼長的股價）
FEATS_XS = ["geps", "lfpe", "pe_rel_sec", "ret12", "g_rev", "dy", "vol36"]
FEATS_XS2 = ["gpos", "gneg", "g2pos", "g2neg", "lfpe", "pe_rel_sec", "ret12", "g_rev", "dy", "vol36"]
GBM_PARAMS = dict(loss="absolute_error", learning_rate=0.05, max_iter=300, max_leaf_nodes=15, min_samples_leaf=80,
                  l2_regularization=1.0, random_state=0)
METHODS = ("unch", "coe", "coe_dy", "lin_abs", "gbm_abs", "gbm_xs", "xs")


def build(d, df, horizons=HORIZONS):
    """d：lab.build 的輸出（t 時點特徵）；df：月面板（接 t+h 的實際值）。回傳加上各距離欄位的 d。"""
    d = d.copy()
    # 股數一律用「市值 ÷ 股價」：市值本來就是股價 × 股數算出來的，這樣本益比 ＝ 股價 ÷ EPS ＝ 市值 ÷ 淨利 在每一列都精確成立
    d["sh_eff"] = d["mc"] / d["px"]
    d["eps0"] = d["ni_ttm"] / d["sh_eff"]
    d["neg0"] = (d["eps0"] <= 0).astype(float)
    d["pe_rel_sec"] = d["ln_pe"] - d["pe_sec"]
    d["pe_rel_own"] = d["ln_pe"] - d["pe_own"]
    d = d.sort_values(["ticker", "month"])
    d["vol36"] = d.groupby("ticker")["mret"].transform(lambda s: s.rolling(36, min_periods=24).std()) * np.sqrt(12)
    for h in sorted(set(horizons) | ({24} if 12 in horizons else set())):
        f = df[["ticker", "month", "px", "mc", "ni_ttm", "period_end", "ln_pe"]].copy()
        f["sh_now"] = f["mc"] / f["px"]
        f = f.drop(columns=["mc"])
        f["month"] = f["month"] - pd.DateOffset(months=h)
        f = f.rename(columns={"px": f"px_f{h}", "sh_now": f"sh_f{h}", "ni_ttm": f"ni_f{h}", "period_end": f"pend_f{h}",
                              "ln_pe": f"lpe_f{h}"})
        d = d.merge(f, on=["ticker", "month"], how="left")
        eps_f = d[f"ni_f{h}"] / d[f"sh_f{h}"]
        d[f"eps_f{h}"] = eps_f
        d[f"lfpe_{h}"] = np.log(d["px"] / eps_f.where(eps_f > 0))
        d[f"geps_{h}"] = np.log(eps_f.where(eps_f > 0) / d["eps0"].where(d["eps0"] > 0))
        d[f"rp_{h}"] = np.log(d[f"px_f{h}"] / d["px"])
    return d.reset_index(drop=True)


def view(d, h):
    """把距離 h 的欄位換成通用名稱，模型程式只看通用名稱。12 個月另外帶「再下一年」（24 個月）的 EPS。"""
    v = d.assign(lfpe=d[f"lfpe_{h}"], geps=d[f"geps_{h}"], rp=d[f"rp_{h}"], target=d[f"lpe_f{h}"])
    v["gpos"], v["gneg"] = v["geps"].clip(0, 1.5), v["geps"].clip(-1.5, 0)
    if h == 12 and "geps_24" in d:
        v["geps2"] = d["geps_24"]
        v["g2pos"], v["g2neg"] = v["geps2"].clip(0, 1.5), v["geps2"].clip(-1.5, 0)
    # 橫斷面去平均：同月份所有公司股價報酬的中位數（大盤部分），只在訓練標籤上用（t+h 已揭曉）
    v["rp_xs"] = v["rp"] - v.groupby("month")["rp"].transform("median")
    return v


def market_ret(te, h):
    """大盤部分：資金成本（10 年期 ＋ 5%）× h/12，連續複利。"""
    return (te["y10"] + ERP).to_numpy(float) * h / 12


def _xg(d, feats):
    X = d[feats].to_numpy(float)
    X[np.isinf(X)] = np.nan
    return X


def _lin_fit(tr, feats, y):
    ok = ((tr["neg0"] == 0) & tr["geps"].notna() & tr[feats].notna().any(axis=1)).to_numpy()
    X, b = lab._mat(tr[ok], feats)
    X = np.where(np.isfinite(X), X, 0.0)
    return huber_ols(np.column_stack([np.ones(len(X)), X]), y[ok]), b


def _lin_apply(beta, bounds, te, feats):
    X, _ = lab._mat(te, feats, bounds)
    X = np.where(np.isfinite(X), X, 0.0)
    r = np.column_stack([np.ones(len(X)), X]) @ beta
    return np.where((te["neg0"] == 0) & te["geps"].notna(), r, np.nan)


def fit(method, tr, h):
    fm = dict(method=method, h=h)
    if method in ("unch", "coe", "coe_dy"):
        return fm
    if method in ("xs", "xs2", "lin_abs"):
        feats = {"xs": FEATS_XS, "xs2": FEATS_XS2, "lin_abs": FEATS_LIN_ABS}[method]
        tr2 = tr[tr["geps2"].notna()] if method == "xs2" else tr
        y = (tr2["rp"] if method == "lin_abs" else tr2["rp_xs"]).clip(-2, 2).to_numpy(float)
        fm["beta"], fm["bounds"] = _lin_fit(tr2, feats, y)
        fm["feats"] = feats
        return fm
    if method in ("gbm_abs", "gbm_xs"):
        from sklearn.ensemble import HistGradientBoostingRegressor
        base = FEATS_GBM if method == "gbm_abs" else FEATS_GBM_XS
        X = _xg(tr, base)
        feats = [f for j, f in enumerate(base) if np.isfinite(X[:, j]).sum() >= 200]   # 早期年度算不出來的特徵先不用
        y = (tr["rp"] if method == "gbm_abs" else tr["rp_xs"]).clip(-2, 2).to_numpy(float)
        m = HistGradientBoostingRegressor(categorical_features=[feats.index("sector_id")], **GBM_PARAMS)
        m.fit(_xg(tr, feats), y)
        fm.update(model=m, feats=feats)
        return fm
    raise ValueError(method)


def predict_rp(fm, te):
    """股價報酬（ln）的預測；沒辦法預測的列是 NaN。xs、xs2：今天虧損（EPS 成長沒有定義）時退回資金成本。"""
    method, h = fm["method"], fm["h"]
    mk = market_ret(te, h)
    if method == "unch":                                   # 本益比不變 ⇔ 股價跟 EPS 一比一
        return np.where(te["neg0"] == 0, te["geps"], np.nan)
    if method == "coe":                                    # 股價照資金成本漲，完全不管 EPS
        return mk
    if method == "coe_dy":                                 # 同上，扣掉股利殖利率（股價報酬不含股利）
        return mk - te["dy"].fillna(0).to_numpy(float) * h / 12
    if method == "lin_abs":
        return _lin_apply(fm["beta"], fm["bounds"], te, fm["feats"])
    if method in ("xs", "xs2"):
        rel = _lin_apply(fm["beta"], fm["bounds"], te, fm["feats"])
        if method == "xs2":
            rel = np.where(te["geps2"].notna(), rel, np.nan)
            return mk + rel
        return mk + np.where(np.isfinite(rel), rel, 0.0)
    pred = fm["model"].predict(_xg(te, fm["feats"]))
    return pred if method == "gbm_abs" else mk + pred


def walk(d, horizons=HORIZONS, methods=METHODS, start=2012, end=2025, log=None):
    """每年 1 月重估：只用「t+h 月底 ≤ 訓練截止日」的配對訓練，預測當年每個月、每家公司（給定實際的 EPS(t+h)）。
    回傳逐筆預測（ln 本益比）與可追溯欄位。"""
    out = []
    for h in horizons:
        v = view(d, h)
        elig = v["lfpe"].notna() & v["px"].gt(0)
        ms = list(methods) + (["xs2"] if h == 12 and "geps2" in v else [])
        for Y in range(start, end + 1):
            cutoff = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
            tgt_end = v["month"] + pd.DateOffset(months=h) + pd.offsets.MonthEnd(0)   # 答案揭曉日＝t+h 那個月的月底
            tr = v[elig & (tgt_end <= cutoff) & v["target"].notna() & v["rp"].notna()]
            te = v[elig & (v["month_end"] > cutoff) & (v["month_end"] <= cutoff + pd.DateOffset(months=12))]
            if len(tr) < 1000 or te.empty:
                continue
            # 時間界線檢查：訓練答案已揭曉；測試列的財報在 t 月底以前已公布
            assert (tgt_end[tr.index] <= cutoff).all() and (tgt_end[tr.index] > tr["month_end"]).all()
            assert (te["avail"] <= te["month_end"]).all() and (tr["avail"] <= tr["month_end"]).all()
            res = pd.DataFrame({
                "ticker": te["ticker"], "sector": te["sector"], "h": h, "origin": te["month"],
                "training_cutoff": cutoff, "price_timestamp": te["month_end"],
                "feature_quarter_end": te["period_end"], "feature_available_at": te["avail"],
                "target_month": te["month"] + pd.DateOffset(months=h), "target_available_at": tgt_end[te.index],
                "target_quarter_end": te[f"pend_f{h}"], "eps0": te["eps0"], "eps_target": te[f"eps_f{h}"],
                "px0": te["px"], "px_target": te[f"px_f{h}"], "ln_pe": te["ln_pe"], "lfpe": te["lfpe"],
                "actual": te["target"], "vol36": te["vol36"], "y10": te["y10"], "dy": te["dy"],
                "shares_basis": "mc/px", "xs_rule": np.where((te["neg0"] == 0) & te["geps"].notna(), "linear", "coe_fallback"),
                "model_version": VERSION})
            for m in ms:
                fm = fit(m, tr, h)
                res[m] = te["lfpe"].to_numpy(float) + predict_rp(fm, te)
            out.append(res)
            if log:
                log(f"  h={h} {Y}：訓練 {len(tr):,} 筆（答案最晚 {tgt_end[tr.index].max():%Y-%m}）→ 預測 {len(te):,} 筆")
    return pd.concat(out, ignore_index=True)


def score(p, methods, base="coe", period=None, sample=None):
    """共同樣本上的評分。e ＝ ln(預測 ÷ 實際)。
    中位絕對誤差：median |e|；命中 ±20%：|預測 ÷ 實際 − 1| ≤ 20%；
    技能（相對基準）＝ 1 − Σe² ÷ Σe_基準²（不截尾；另列每筆 e² 截在 4 的版本）；
    方向：預測的本益比變化方向（相對今天）與實際相同；平手（預測不變）算錯。"""
    rows = []
    for h, g in p.groupby("h"):
        if period:
            g = g[(g["origin"] >= period[0]) & (g["origin"] <= period[1])]
        if sample is not None:
            g = g[sample(g)]
        ok = g["actual"].notna()
        for m in set(methods) | {base}:
            if m not in g:
                ok &= False
                continue
            ok &= g[m].notna()
        g = g[ok]
        if len(g) < 100:
            continue
        eb = (g[base] - g["actual"]).to_numpy()
        for m in methods:
            e = (g[m] - g["actual"]).to_numpy()
            d_pred = np.sign(g[m] - g["ln_pe"]).to_numpy()
            d_act = np.sign(g["actual"] - g["ln_pe"]).to_numpy()
            has = np.isfinite(d_pred) & np.isfinite(d_act)
            rows.append(dict(h=h, 方法=m, n=len(g), 公司數=g["ticker"].nunique(),
                             中位絕對誤差=float(np.median(np.abs(e))), 平均絕對誤差=float(np.mean(np.abs(e))),
                             命中20=float(np.mean(np.abs(np.exp(e) - 1) <= 0.2)),
                             技能=float(1 - np.sum(e ** 2) / np.sum(eb ** 2)),
                             技能_截尾=float(1 - np.sum(np.minimum(e ** 2, 4)) / np.sum(np.minimum(eb ** 2, 4))),
                             方向=float(np.mean((d_pred == d_act)[has] & (d_pred[has] != 0))) if has.any() else np.nan))
    return pd.DataFrame(rows)


def fit_production(c, cutoff, horizons=HORIZONS):
    """正式模型：用 cutoff 以前已揭曉的全部配對估計 xs（每個距離）與 xs2（12 個月）。
    回傳 {"xs": {h: 係數}, "xs2": {12: 係數}}，係數＝{"feats", "beta"（第一個是常數）, "bounds"（每個特徵的截斷上下限）}。"""
    out = {"xs": {}, "xs2": {}}
    for h in horizons:
        v = view(c, h)
        tgt_end = v["month"] + pd.DateOffset(months=h) + pd.offsets.MonthEnd(0)      # 答案揭曉日（和 walk 一樣）
        tr = v[v["lfpe"].notna() & v["px"].gt(0) & (tgt_end <= cutoff) & v["target"].notna() & v["rp"].notna()]
        for m in (("xs", "xs2") if h == 12 else ("xs",)):
            fm = fit(m, tr, h)
            out[m][h] = dict(feats=list(fm["feats"]), beta=[float(b) for b in fm["beta"]],
                             bounds=[[float(a), float(b)] for a, b in fm["bounds"]], n_train=int(len(tr)),
                             last_target=str((tr["month"] + pd.DateOffset(months=h)).max().date()))
    return out


def linear_rel(coef, x):
    """用 fit_production 的係數算「相對大盤」的部分。x：dict 或 DataFrame（欄位＝coef["feats"]）。缺值當 0（和訓練一樣）。"""
    tot = coef["beta"][0]
    for f, b, (lo, hi) in zip(coef["feats"], coef["beta"][1:], coef["bounds"]):
        val = np.clip(np.asarray(x[f], float), lo, hi)
        tot = tot + b * np.where(np.isfinite(val), val, 0.0)
    return tot


def predict_now(row, eps, h, model, eps2=None):
    """用 cond_model.json（model）替一家公司算「給定 EPS」的本益比與股價。
    row：results/now_all.csv 的一列（px、eps0、y10、pe_rel_sec、ret12、g_rev、dy、vol36）；eps：h 個月後那時已公布的
    最近四季 EPS（每股、GAAP 稀釋）；eps2：再下一年的 EPS（只有 h=12 用得到，給了就用 xs2）。
    回傳 dict：pe（中位）、pe_lo80/hi80/lo50/hi50、px（股價中位）與區間、用了哪個模型、波動與區間寬度（相對中位波動）。EPS ≤ 0 → None。"""
    if eps is None or not np.isfinite(eps) or eps <= 0:
        return None
    px, eps0 = float(row["px"]), float(row["eps0"])
    lfpe = np.log(px / eps)
    x = {f: row.get(f, np.nan) for f in ("pe_rel_sec", "ret12", "g_rev", "dy", "vol36")}
    x["lfpe"] = lfpe
    geps = np.log(eps / eps0) if eps0 > 0 else np.nan
    x["geps"], x["gpos"], x["gneg"] = geps, np.clip(geps, 0, 1.5), np.clip(geps, -1.5, 0)
    use2 = h == 12 and eps2 is not None and np.isfinite(eps2) and eps2 > 0 and eps0 > 0
    if use2:
        g2 = np.log(eps2 / eps0)
        x["g2pos"], x["g2neg"] = np.clip(g2, 0, 1.5), np.clip(g2, -1.5, 0)
        coef, band, name = model["xs2"]["12"], model["bands2"]["12"], "xs2"
    else:
        coef, band, name = model["xs"][str(h)], model["bands"][str(h)], "xs"
    rel = float(linear_rel(coef, x)) if eps0 > 0 else 0.0          # 今天虧損：EPS 成長沒有定義 → 只用資金成本
    mk = (float(row["y10"]) + model["erp"]) * h / 12
    lpe = lfpe + mk + rel
    vol = row.get("vol36", np.nan)
    vol_known = vol is not None and np.isfinite(vol)
    vol = float(vol) if vol_known else band["vol_median"]              # 沒有股價歷史：用校準樣本的中位波動
    sc = float(band_scale(vol, band["alpha"]))
    out = dict(model=name, vol=vol, vol_known=bool(vol_known), width=sc / float(band_scale(band["vol_median"], band["alpha"])),
               mk=mk, rel=rel, lpe=lpe, pe=np.exp(lpe), px=np.exp(lpe) * eps)
    for k, qq in zip(("lo80", "lo50", "hi50", "hi80"), band["q"]):
        out[f"pe_{k}"] = np.exp(lpe + sc * qq)
        out[f"px_{k}"] = np.exp(lpe + sc * qq) * eps
    return out


def band_scale(vol, alpha=BAND_ALPHA):
    """區間的寬度係數：股價波動（年化，過去 36 個月）的 alpha 次方。波動 2 倍 → 區間寬 2^0.7 ≈ 1.6 倍。"""
    return np.clip(np.asarray(vol, float), *VOL_CLIP) ** alpha


def calib_table(p, method, cutoff, h, cal_start="2012-01-01", q=(0.1, 0.25, 0.75, 0.9), alpha=BAND_ALPHA):
    """區間校準表：「cutoff 以前已揭曉」的樣本外誤差 e ＝ ln(實際 ÷ 預測)，先除以 波動^alpha，再減掉中位數（置中），
    取分位數。區間 ＝ 點預測 × exp(波動^alpha × 分位數)。
    置中：只保留誤差的「寬度」，不保留歷史的平均偏差（2012–2021 多頭＋倖存者讓實際股價常比資金成本高，2022 以後反過來；
    那是預測不了的大盤部分，不該寫進區間）。
    為什麼用波動^0.7 而不是分三組：分三組時最高那組（波動 28% 以上）混了 30% 和 70% 的股票，波動 45% 以上的 80% 區間
    實測只涵蓋 49–70%；波動^0.7 讓各種波動的涵蓋率差不多（lab_cond.py 的「區間」表）。
    回傳 dict(alpha, vol_clip, vol_median（沒有波動資料時用）, q［len(q)］, n)。"""
    g = p[(p["h"] == h) & p[method].notna() & p["actual"].notna() & (p["target_available_at"] <= cutoff)
          & (p["origin"] >= cal_start)]
    e = (g["actual"] - g[method]).to_numpy()
    vmed = float(g["vol36"].median())
    u = e / band_scale(g["vol36"].fillna(vmed).to_numpy(), alpha)
    u = u - np.median(u)
    return dict(alpha=alpha, vol_clip=list(VOL_CLIP), vol_median=vmed, q=[float(x) for x in np.quantile(u, q)], n=int(len(u)))
