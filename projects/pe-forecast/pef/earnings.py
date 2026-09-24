"""模組 E：盈餘路徑。

盈餘 = 營收 × 淨利率。兩者分開預測，因為物理機制不同：
  營收：需求 × 價格，有慣性（訂單、合約、產能爬坡都要好幾季）
  淨利率：價格 vs 成本，會回歸公司自己的結構水準；存貨堆積與毛利率斜率是領先訊號

係數用**所有公司**一起估（同一套物理規律），差別在各家的訊號值。
每個預測距離 k（季）各估一組（直接多步預測，不疊代，誤差不會滾雪球）。
"""
import numpy as np

from .features import HORIZONS_Q
from .stats import huber_ols

# 規格比較見 README §4 與 ablation.py（results/ablation.csv）。選模期 2015–2021 的本益比誤差各規格差距 <0.004；
# 採用「E/P＋兩階段隱含利潤率」是因為它的 24／36 個月盈餘誤差在選模期與保留期都最低。
REV_X = ["g_rev", "acc", "d_inv", "gm_slope", "ret6", "ln_ps", "ep_c"]
MAR_X = ["gap", "q_vs_ttm", "gm_slope", "d_inv", "ret6", "ln_ps", "ep_c"]
M_CLIP = (-1.0, 0.6)


def _design(df, cols, bounds=None):
    d = df.copy()
    d["gap"] = d["m_ttm"] - d["m_bar"]
    d["q_vs_ttm"] = d["m_q"] - d["m_ttm"]
    X = np.array(d[cols].to_numpy(float), copy=True)
    if bounds is None:
        bounds = []
        for j in range(X.shape[1]):
            v = X[:, j][np.isfinite(X[:, j])]
            bounds.append(tuple(np.quantile(v, [0.01, 0.99])) if len(v) > 20 else (-np.inf, np.inf))
    for j, (a, b) in enumerate(bounds):
        X[:, j] = np.clip(X[:, j], a, b)
    X = np.where(np.isfinite(X), X, 0.0)   # 缺值（例如沒有存貨的軟體公司）→ 訊號為 0
    return np.column_stack([np.ones(len(X)), X]), bounds


class EarningsModel:
    def __init__(self, rev_x=None, mar_x=None):
        self.coef = {}
        self.rev_x = rev_x or REV_X
        self.mar_x = mar_x or MAR_X

    def fit(self, train, asof):
        """train：月面板。只用 t+k 季財報在 asof 之前已公告的列。"""
        for k in HORIZONS_Q:
            ok = (train[f"avail_{k}"] <= asof) & train[f"y_rev_{k}"].notna() & train[f"y_m_{k}"].notna() \
                & train["m_bar"].notna()
            d = train[ok]
            if len(d) < 200:
                raise ValueError(f"k={k} 訓練樣本不足（{len(d)}）")
            Xr, br = _design(d, self.rev_x)
            yr = np.clip(d[f"y_rev_{k}"].to_numpy(), *np.quantile(d[f"y_rev_{k}"], [0.01, 0.99]))
            Xm, bm = _design(d, self.mar_x)
            ym = d[f"y_m_{k}"].to_numpy() - d["m_bar"].to_numpy()
            ym = np.clip(ym, *np.quantile(ym, [0.01, 0.99]))
            self.coef[k] = dict(rev=huber_ols(Xr, yr), rev_b=br, mar=huber_ols(Xm, ym), mar_b=bm, n=len(d))
        return self

    def predict(self, df, override=None):
        """回傳 {k: (TTM 營收, TTM 淨利率)}。override 見 forecast.py。"""
        out = {}
        for k in HORIZONS_Q:
            c = self.coef[k]
            Xr, _ = _design(df, self.rev_x, c["rev_b"])
            Xm, _ = _design(df, self.mar_x, c["mar_b"])
            rev = df["rev_ttm"].to_numpy() * np.exp(Xr @ c["rev"])
            m = np.clip(df["m_bar"].to_numpy() + Xm @ c["mar"], *M_CLIP)
            out[k] = (rev, m)
        if override:
            out = apply_override(df, out, override)
        return out


def apply_override(df, out, ov):
    """情境輸入：用你自己的假設取代模型的預測。

    ov 可含：
      rev_growth: [g1, g2, g3]  每年營收成長率（例 [0.5, 0.2, 0.1]）
      margin:     [m1, m2, m3]  每年 TTM 淨利率
    """
    R0 = df["rev_ttm"].to_numpy()
    if "rev_growth" in ov:
        g = ov["rev_growth"]
        lvl = {4: R0 * (1 + g[0]), 8: R0 * (1 + g[0]) * (1 + g[1]), 12: R0 * (1 + g[0]) * (1 + g[1]) * (1 + g[2])}
        lvl[2] = R0 * np.sqrt(1 + g[0])
        out = {k: (lvl[k], out[k][1]) for k in out}
    if "margin" in ov:
        m = ov["margin"]
        mm = {2: (df["m_ttm"].to_numpy() + m[0]) / 2, 4: np.full(len(df), m[0]),
              8: np.full(len(df), m[1]), 12: np.full(len(df), m[2])}
        out = {k: (out[k][0], mm[k]) for k in out}
    return out
