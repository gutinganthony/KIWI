"""實驗平台：用各種方法預測 h 個月後的本益比，走動式比較。

目標的第一性原理寫法：

    ln PE(t+h) = ln 市值(t) + 報酬(t→t+h) − ln 淨利TTM(t+h)
               = 報酬 − ln[ 淨利TTM(t+h) ÷ 市值(t) ]
                         └──────── y_h：「未來盈餘 ÷ 今天市值」＝前瞻盈餘殖利率 ────────┘

y_h 跨越零時連續（虧損公司也能訓練）、沒有規模問題（大小公司可以放在一起），
而且它就是「今天的價格買到的未來盈餘」——本益比預測只需要它和一個報酬假設。
"""
import numpy as np
import pandas as pd

from .features import attach_future
from .stats import huber_ols

HORIZONS = (3, 6, 9, 12, 18, 24, 36)
SECTORS = ["software", "internet", "semis", "semicap", "memory", "hardware", "itservices"]
# S&P 500 版加上的 GICS 產業（科技股名單內的公司仍用上面的細分產業；舊的 7 個編號不變）
SECTORS += ["gics_it", "gics_comm", "gics_discr", "gics_staples", "gics_health", "gics_fin", "gics_indu", "gics_energy",
            "gics_util", "gics_re", "gics_mat"]
ERP = 0.05


def _clip(s, lo, hi):
    return s.clip(lo, hi)


def quarter_extras(qf):
    """季表上的補充量：季營收成長（最新一季、前一季）、營業利益 TTM。"""
    q = qf.sort_values(["ticker", "period_end"]).copy()
    g = q.groupby("ticker", group_keys=False)
    gap_ok = (q["period_end"] - g["period_end"].shift(1)).dt.days.between(60, 120)
    q["rev_prev"] = g["rev"].shift(1).where(gap_ok)
    q["g_qoq"] = np.log(q["rev"] / q["rev_prev"])
    q["g_qoq_prev"] = q.groupby("ticker")["g_qoq"].shift(1)
    span3 = (q["period_end"] - g["period_end"].shift(3)).dt.days
    q["oi_ttm"] = g["oi"].transform(lambda s: s.rolling(4, min_periods=4).sum()).where(span3.between(250, 300))
    cols = ["ticker", "period_end", "g_qoq", "g_qoq_prev", "oi_ttm"]
    if "dps_now" in q:           # 每股股利 TTM（今日分割口徑；沒配息＝0）
        q["dps_ttm"] = g["dps_now"].transform(lambda s: s.fillna(0).rolling(4, min_periods=4).sum()).where(span3.between(250, 300))
        cols.append("dps_ttm")
    return q[cols]


def add_features(d):
    """t 時點的特徵（全部只用 t 已公告的財報與 t 的股價）。需要 ret12 欄（12 個月股價報酬）。"""
    mc = d["mc"]
    d["ey_ttm"] = _clip(d["ni_ttm"] / mc, -0.5, 0.5)
    d["ey_run"] = _clip(d["ni"] * 4 / mc, -0.5, 0.5)                       # 最新一季年化：現在的賺錢能力
    d["ey_core"] = _clip(d["oi_ttm"] * 0.85 / mc, -0.5, 0.5)               # 核心盈餘（營業利益×0.85）
    d["ey_core_run"] = _clip(d["oi"] * 4 * 0.85 / mc, -0.5, 0.5)
    d["ln_sy"] = np.log((d["rev_ttm"] / mc).clip(1e-3, 20))                # 營收殖利率 ＝ 1/(P/S)
    d["ln_sy_run"] = np.log((d["rev"] * 4 / mc).clip(1e-3, 20))
    d["gap"] = d["m_ttm"] - d["m_bar"]
    d["q_vs_ttm"] = d["m_q"] - d["m_ttm"]
    d["ln_mc"] = np.log(mc)
    d["info_age"] = (d["month_end"] - d["period_end"]).dt.days / 91.0
    d["sector_id"] = d["sector"].map({s: i for i, s in enumerate(SECTORS)}).fillna(len(SECTORS)).astype(int)
    # S&P 500 版的兩個額外特徵：股利殖利率、淨負債 ÷ 市值（成熟公司、槓桿公司的本益比規律不同）
    d["dy"] = (d["dps_ttm"] / d["px"]).clip(0, 0.2) if "dps_ttm" in d and "px" in d else np.nan
    d["lev"] = ((d["debt"].fillna(0) - d["cash"].fillna(0)) / mc).clip(-1, 3) if "debt" in d else np.nan
    return d


def build(df, qf):
    """在月面板上加特徵與各預測距離的目標。"""
    d = df.merge(quarter_extras(qf), on=["ticker", "period_end"], how="left")
    d["ret12"] = d.groupby("ticker")["mc"].transform(lambda s: np.log(s / s.shift(12)))
    d = add_features(d)
    # 「歷史本益比」類特徵（檢驗舊思維：本益比會回到自己過去的水準／同業水準嗎？）——都只用 t 當月以前的資料
    d["pe_own"] = d.groupby("ticker")["ln_pe"].transform(lambda s: s.rolling(60, min_periods=24).median())
    d["pe_rel_own"] = d["ln_pe"] - d["pe_own"]
    d["pe_sec"] = d.groupby(["sector", "month"])["ln_pe"].transform("median")
    d["pe_rel_sec"] = d["ln_pe"] - d["pe_sec"]
    d["pe_mkt"] = d.groupby("month")["ln_pe"].transform("median")
    mc = d["mc"]
    for h in HORIZONS:
        f = attach_future(df, h)[["ticker", "month", f"ni_ttm_f{h}", f"ln_pe_f{h}", f"mc_f{h}"]]
        d = d.merge(f, on=["ticker", "month"], how="left")
        d[f"y_{h}"] = _clip(d[f"ni_ttm_f{h}"] / mc, -0.5, 0.5)
        d[f"z_{h}"] = d[f"ln_pe_f{h}"] - d["ln_pe"]
    return d


FEATS_LIN = ["ey_ttm", "ey_run", "ey_core", "ey_core_run", "ln_sy", "ln_sy_run", "g_rev", "acc", "g_qoq",
             "g_qoq_prev", "gap", "q_vs_ttm", "gm_slope", "d_inv", "sigma", "ret6", "ret12", "info_age"]
FEATS_GBM = FEATS_LIN + ["m_ttm", "m_bar", "sc", "ln_mc", "y10", "sector_id"]
FEATS_HIST = ["pe_own", "pe_rel_own", "pe_sec", "pe_rel_sec", "pe_mkt"]
FEATS_B = ["dy", "lev"]
# 中小型股的財報（loosygoosie v2）沒有毛利、營業利益、存貨 → 「精簡」版拿掉用到它們的特徵
REDUCED_OUT = {"gm_slope", "d_inv", "ey_core", "ey_core_run"}
FEATS_LIN_R = [f for f in FEATS_LIN if f not in REDUCED_OUT]
FEATS_GBM_R = [f for f in FEATS_GBM if f not in REDUCED_OUT]
GBM_PARAMS = dict(loss="absolute_error", learning_rate=0.05, max_iter=300, max_leaf_nodes=15, min_samples_leaf=80,
                  l2_regularization=1.0, random_state=0)


def _mat(d, cols, bounds=None):
    X = d[cols].to_numpy(float).copy()
    if bounds is None:
        bounds = [tuple(np.nanquantile(X[:, j], [0.01, 0.99])) if np.isfinite(X[:, j]).sum() > 20 else (-np.inf, np.inf)
                  for j in range(X.shape[1])]
    for j, (a, b) in enumerate(bounds):
        X[:, j] = np.clip(X[:, j], a, b)
    return X, bounds


def to_lnpe(y_hat, d, h, mu=None):
    """前瞻盈餘殖利率 → ln 本益比（報酬＝資金成本）。預測虧損或近零時本益比上限 500。"""
    ret = (d["y10"].to_numpy(float) + ERP) * h / 12 if mu is None else mu
    return ret - np.log(np.maximum(y_hat, 0.002)), y_hat > 0.002


def fit(method, tr, h):
    """用訓練列 tr 學「h 個月後」的預測器。回傳可重複套用的物件（dict）。"""
    fm = dict(method=method, h=h)
    if method in ("run_rate", "core_run"):
        return fm
    if method in ("huber", "huber_r"):
        feats = FEATS_LIN_R if method == "huber_r" else FEATS_LIN
        Xtr, b = _mat(tr, feats)
        Xtr = np.where(np.isfinite(Xtr), Xtr, 0.0)
        fm["beta"] = huber_ols(np.column_stack([np.ones(len(Xtr)), Xtr]), tr[f"y_{h}"].to_numpy(float))
        fm["bounds"] = b
        fm["feats"] = feats
        return fm
    if method in ("gbm", "gbm_z", "gbm_z_stack", "gbm_hist", "gbm_z_hist", "gbm_b", "gbm_z_b", "gbm_r", "gbm_z_r"):
        from sklearn.ensemble import HistGradientBoostingRegressor
        feats = FEATS_GBM + ([c for c in ("old_ey_12", "old_ey_h", "imp_gap")
                              if c in tr and tr[c].notna().sum() >= 50] if method == "gbm_z_stack" else [])
        base = method
        if method.endswith("_hist"):
            feats = feats + FEATS_HIST
            base = method[:-5]
        if method.endswith("_b"):
            feats = feats + FEATS_B
            base = method[:-2]
        if method.endswith("_r"):
            feats = list(FEATS_GBM_R)
            base = method[:-2]
        cat = [feats.index("sector_id")]
        m = HistGradientBoostingRegressor(categorical_features=cat, **GBM_PARAMS)
        if base == "gbm":
            m.fit(tr[feats].to_numpy(float), tr[f"y_{h}"].to_numpy(float))
        else:
            trz = tr[tr[f"z_{h}"].notna() & tr["ln_pe"].notna()]
            m.fit(trz[feats].to_numpy(float), trz[f"z_{h}"].clip(-2, 2).to_numpy(float))
        fm.update(model=m, feats=feats, base=base)
        return fm
    raise ValueError(method)


def apply(fm, te):
    """回傳 (ln PE 預測, 可用遮罩)。"""
    method, h = fm["method"], fm["h"]
    if method == "run_rate":                                   # 第一性原理的最簡版：未來盈餘＝最新一季×4
        return to_lnpe(te["ey_run"].to_numpy(float), te, h)
    if method == "core_run":
        return to_lnpe(te["ey_core_run"].fillna(te["ey_run"]).to_numpy(float), te, h)
    if method in ("huber", "huber_r"):
        Xte, _ = _mat(te, fm.get("feats", FEATS_LIN), fm["bounds"])
        Xte = np.where(np.isfinite(Xte), Xte, 0.0)
        return to_lnpe(np.column_stack([np.ones(len(Xte)), Xte]) @ fm["beta"], te, h)
    pred = fm["model"].predict(te[fm["feats"]].to_numpy(float))
    if fm["base"] == "gbm":
        return to_lnpe(pred, te, h)
    return te["ln_pe"].to_numpy(float) + pred, te["ln_pe"].notna().to_numpy()


def fit_predict(method, tr, te, h):
    return apply(fit(method, tr, h), te)


def add_old(d, pred):
    """舊模型（兩階段盈餘模型）的樣本外預測當成特徵：它在 t 時點就算得出來（用 t 所在年度年初的模型）。"""
    old = pred[["ticker", "month", "implied_m", "mc"] + [f"ni_hat_{h}" for h in (6, 12, 24, 36)]].rename(columns={"mc": "mc_old"})
    d = d.merge(old, on=["ticker", "month"], how="left")
    d["old_ey_12"] = (d["ni_hat_12"] / d["mc"]).clip(-0.5, 0.5)
    for h in HORIZONS:
        near = min((6, 12, 24, 36), key=lambda k: abs(k - h))
        d[f"old_ey_h{h}"] = (d[f"ni_hat_{near}"] / d["mc"]).clip(-0.5, 0.5)
    d["imp_gap"] = (d["implied_m"] - d["m_bar"]).clip(-0.5, 0.8)
    return d


def walk(d, methods, horizons=HORIZONS, start=2015, end=2026, train_col=None):
    """每年 1 月用當時已揭曉的配對（t+h ≤ asof）訓練，預測當年每個月。train_col：只用這欄為真的列訓練（預測仍是全部）。"""
    out = []
    for h in horizons:
        for Y in range(start, end + 1):
            asof = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
            tr = d[(d["month_end"] + pd.DateOffset(months=h) <= asof) & d[f"y_{h}"].notna() & d["m_bar"].notna()]
            if train_col:
                tr = tr[tr[train_col].astype(bool)]
            te = d[(d["month_end"] > asof) & (d["month_end"] <= asof + pd.DateOffset(months=12)) & d["m_bar"].notna()
                   & (d["mc"] > 0)]
            if len(tr) < 500 or te.empty:
                continue
            res = te[["ticker", "month", "sector", "ln_pe", f"ln_pe_f{h}"]].copy()
            res["h"] = h
            res["fit_year"] = Y
            if "old_ey_h" not in d and f"old_ey_h{h}" in d:
                tr = tr.assign(old_ey_h=tr[f"old_ey_h{h}"])
                te = te.assign(old_ey_h=te[f"old_ey_h{h}"])
            for mth in methods:
                lp, ok = fit_predict(mth, tr, te, h)
                res[mth] = np.where(ok, lp, np.nan)
            out.append(res.rename(columns={f"ln_pe_f{h}": "actual"}))
    return pd.concat(out, ignore_index=True)


def score(p, methods, period=None, extra_mask=None):
    """共同樣本（實際為正、今天盈餘為正、所有方法都有預測）上的評分。"""
    rows = []
    for h, g in p.groupby("h"):
        if period:
            g = g[(g["month"] >= period[0]) & (g["month"] <= period[1])]
        if extra_mask is not None:
            g = g[extra_mask(g)]
        ok = g["actual"].notna() & g["ln_pe"].notna()
        for m in methods:
            ok &= g[m].notna()
        g = g[ok]
        if len(g) < 30:
            continue
        e_rw = g["ln_pe"] - g["actual"]
        for m in ["rw"] + list(methods):
            e = (g["ln_pe"] if m == "rw" else g[m]) - g["actual"]
            dirn = np.nan if m == "rw" else float(np.mean(np.sign(g[m] - g["ln_pe"]) == np.sign(g["actual"] - g["ln_pe"])))
            rows.append(dict(h=h, 方法=m, n=len(g), 中位絕對誤差=float(np.median(np.abs(e))),
                             相對隨機漫步=float(np.median(np.abs(e)) / np.median(np.abs(e_rw)) - 1),
                             OOS_R2=float(1 - np.sum(np.minimum(e ** 2, 4)) / np.sum(np.minimum(e_rw ** 2, 4))),
                             方向命中=dirn))
    return pd.DataFrame(rows)
