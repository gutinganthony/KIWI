"""把模組接起來：站在 asof 這一天，只用那天以前的資料，預測 h 個月後的本益比。

    恆等式：  PE(t+h) = 市值(t) × exp(報酬 t→t+h) ÷ 盈餘TTM(t+h)

    模組 E（可預測的部分）：盈餘TTM(t+h)——營收 × 淨利率，面板迴歸
    報酬假設（不可預測的部分）：預設 = 資金成本（10 年期殖利率 + 5%）× h/12，可覆寫
    模組 V（不參與預測，回測證明它沒有預測力）：反推「市場隱含的長期淨利率」

回測證據與規格選擇見 README。
"""
import numpy as np
import pandas as pd

from .earnings import MAR_X, REV_X, EarningsModel
from .features import HORIZONS_Q
from .stats import huber_ols
from . import value

ERP = 0.05               # 股票風險溢酬：慣例值，刻意不用資料擬合（擬合出來的是這個樣本的倖存者報酬）
V_PARAMS = dict(theta0=ERP, theta1=0.0, H=5.0, g_inf=0.03)   # 反推用的 DCF 常數（第一性原理預設，可覆寫）
BELIEF_WINDOW_M = 120


def _inputs(df, E, m_bar=None):
    rev3 = np.column_stack([E[4][0], E[8][0], E[12][0]])
    m3 = np.column_stack([E[4][1], E[8][1], E[12][1]])
    mb = df["m_bar"].to_numpy(float) if m_bar is None else np.broadcast_to(np.asarray(m_bar, float), len(df)).copy()
    return (df["rev_ttm"].to_numpy(float), rev3, m3, mb,
            df["sc"].to_numpy(float), df["y10"].to_numpy(float), df["sigma"].to_numpy(float))


class PEForecaster:
    def __init__(self, rev_x=None, mar_x=None, mu_mode="coe", erp=ERP, belief_window=BELIEF_WINDOW_M,
                 v_params=None, two_stage=True):
        self.rev_x, self.mar_x = rev_x, mar_x
        self.two_stage = two_stage
        self.mu_mode, self.erp = mu_mode, erp
        self.belief_window = belief_window
        self.v_params = dict(V_PARAMS, **(v_params or {}))

    # ---------------------------------------------------------------- 估計
    def fit(self, panel, asof):
        asof = pd.Timestamp(asof)
        self.asof = asof
        past = panel[panel["month_end"] <= asof]
        self.E1 = EarningsModel(self.rev_x, self.mar_x).fit(past, asof)
        self.E = self.E1
        if self.two_stage:
            # 第二階段：把「市場現價隱含的長期淨利率」當成盈餘模型的輸入。
            # 回測發現：市場押注利潤率結構性變高時，24 個月後真的變高的機率約 80%（README §4）
            past = self._with_implied(past)
            rx = (self.rev_x or REV_X) + ["imp_gap"]
            mx = (self.mar_x or MAR_X) + ["imp_gap"]
            self.E = EarningsModel(rx, mx).fit(past, asof)

        # 診斷（不進預測）：歷史中位報酬 μ，以及「價值缺口能不能預測報酬」r = a + γ·u
        lo_b = asof - pd.DateOffset(months=self.belief_window)
        hist = panel[(panel["month_end"] <= asof) & (panel["month_end"] > lo_b)
                     & panel["sigma"].notna() & panel["m_bar"].notna() & (panel["mc"] > 0)].copy()
        hist["u"] = self.value_gap(hist)
        self.diag = {}
        for k in HORIZONS_Q:
            h = 3 * k
            fut = hist[["ticker", "month", "mc"]].copy()
            fut["month"] = fut["month"] - pd.DateOffset(months=h)
            pr = hist.merge(fut, on=["ticker", "month"], suffixes=("", "_f"))
            pr = pr[pr["month_end"] + pd.DateOffset(months=h) <= asof]
            ret = np.log(pr["mc_f"] / pr["mc"]).to_numpy()
            u = np.clip(pr["u"].to_numpy(), -3, 3)
            b = huber_ols(np.column_stack([np.ones(len(pr)), u]), ret) if len(pr) > 50 else np.array([np.nan, np.nan])
            self.diag[h] = dict(mu_hist=float(np.median(ret)) if len(ret) else 0.0, gamma=float(b[1]), n=len(pr))
        return self

    def _with_implied(self, df):
        df = df.copy()
        ok = df["sigma"].notna() & df["m_bar"].notna() & (df["mc"] > 0) & df["rev_ttm"].notna()
        imp = np.full(len(df), np.nan)
        if ok.any():
            sub = df[ok]
            imp[ok.to_numpy()] = self.implied_margin(sub, self.E1.predict(sub))
        df["implied_m"] = imp
        df["imp_gap"] = np.clip(df["implied_m"] - df["m_bar"], -0.5, 0.8)
        return df

    def value_gap(self, df, E=None):
        """u = ln 市值 − ln V（V 用第一性原理預設常數、公司自己的 5 年中位淨利率）。"""
        E = E or self.E1.predict(df)
        V, _ = value.intrinsic(*_inputs(df, E), self.v_params, s=0)
        return np.log(df["mc"].to_numpy(float)) - np.log(V)

    def implied_margin(self, df, E=None):
        """反推：市場現價隱含的長期淨利率 m*（前 3 年用模組 E 的預測，之後收斂到 m*）。

        V 對 m_bar 是線性的，所以用兩點求解，不需要迭代。
        """
        E = E or self.E1.predict(df)
        V0, _ = value.intrinsic(*_inputs(df, E, m_bar=0.0), self.v_params, s=0, floor=False)
        V1, _ = value.intrinsic(*_inputs(df, E, m_bar=0.10), self.v_params, s=0, floor=False)
        slope = (V1 - V0) / 0.10
        return (df["mc"].to_numpy(float) - V0) / np.where(np.abs(slope) > 1e-9, slope, np.nan)

    # ---------------------------------------------------------------- 預測
    def expected_return(self, df, h, mode=None, mu=None):
        mode = mode or self.mu_mode
        if mu is not None:                        # 使用者直接給年化報酬
            return np.full(len(df), mu * h / 12)
        if mode == "coe":
            return (df["y10"].to_numpy(float) + self.erp) * h / 12
        if mode == "hist":
            return np.full(len(df), self.diag[h]["mu_hist"])
        return np.zeros(len(df))

    def predict(self, df, horizons=(6, 12, 24, 36), override=None, mu=None):
        """df：t 時點的月面板列。回傳每個 h 的盈餘預測與本益比預測。

        override：盈餘情境（earnings.apply_override 的 rev_growth / margin），另可含 m_bar 覆寫。
        mu：年化報酬假設（覆寫預設的資金成本）。
        """
        df = df.copy()
        ov = dict(override or {})
        if "m_bar" in ov:
            df["m_bar"] = ov.pop("m_bar")
        if self.two_stage:
            df = self._with_implied(df)
        E = self.E.predict(df, override=ov or None)
        mc0 = df["mc"].to_numpy(float)
        out = pd.DataFrame({"ticker": df["ticker"].to_numpy(), "month": df["month"].to_numpy(),
                            "mc": mc0, "ni_ttm": df["ni_ttm"].to_numpy(float),
                            "m_ttm": df["m_ttm"].to_numpy(float), "m_bar": df["m_bar"].to_numpy(float)})
        out["implied_m"] = df["implied_m"].to_numpy(float) if self.two_stage else self.implied_margin(df)
        for h in horizons:
            k = h // 3
            ni_hat = E[k][0] * E[k][1]
            pos = ni_hat > 0
            safe = np.where(pos, ni_hat, 1.0)
            out[f"rev_hat_{h}"] = E[k][0]
            out[f"m_hat_{h}"] = E[k][1]
            out[f"ni_hat_{h}"] = ni_hat
            variants = {"hat": self.expected_return(df, h, mu=mu),        # 主模型：資金成本（或使用者給的 μ）
                        "hist": self.expected_return(df, h, mode="hist"),  # 敏感度：過去 10 年實際中位報酬
                        "flat": np.zeros(len(df))}                        # 敏感度：股價不動，純看盈餘
            for tag, ret in variants.items():
                mc_hat = mc0 * np.exp(ret)
                out[f"lnpe_{tag}_{h}"] = np.where(pos, np.log(mc_hat) - np.log(safe), np.nan)
                out[f"ep_{tag}_{h}"] = ni_hat / mc_hat
        return out
