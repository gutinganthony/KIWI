"""最終模型：四個預測器的等權平均（README §12）。

    成員                 預測什麼                                    為什麼放進來
    ─────────────────   ─────────────────────────────────────────   ─────────────────────────────
    old     兩階段盈餘模型  營收 × 淨利率 → 未來盈餘（只有 6/12/24/36 月）  可拆解、可做情境
    huber   線性            前瞻盈餘殖利率 y_h ＝ 淨利TTM(t+h) ÷ 市值(t)   穩健、外推溫和
    gbm     梯度提升樹      同上（非線性、可學產業差異）                  抓週期股的轉折
    gbm_z   梯度提升樹      直接學 ln PE 的變化量                         連報酬裡可預測的部分一起學

盈餘殖利率 → 本益比：ln PE(t+h) ＝ 報酬 − ln y_h，報酬＝資金成本（10 年期 + 5%）× h/12。
組合規則：成員預測「虧損或本益比 > 500」時不給數字；有效成員過半才給組合預測（4 個要 3 個、3 個要 2 個）。
站在 asof：每個預測距離 h 只用「t+h ≤ asof」已揭曉的配對訓練——和回測（lab_run.py）同一套程序。
"""
import os

import numpy as np
import pandas as pd

from . import lab
from .forecast import PEForecaster

MEMBERS = ("huber", "gbm", "gbm_z")
OLD_H = (6, 12, 24, 36)
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def combine(cols):
    """cols：成員 ln PE 預測的 DataFrame（NaN＝該成員不給數字）。過半有效才平均。"""
    n_ok = cols.notna().sum(axis=1)
    need = cols.shape[1] // 2 + 1
    return cols.mean(axis=1).where(n_ok >= need)


def members_for(h):
    return list(MEMBERS) + (["old"] if h in OLD_H else [])


class EnsembleForecaster:
    def __init__(self, horizons=lab.HORIZONS):
        self.horizons = tuple(horizons)

    def fit(self, df, qf, asof, old=None):
        """df, qf：pef.load.panel() 的輸出。old：已在同一 asof 擬合好的 PEForecaster（沒給就自己擬合）。"""
        self.asof = pd.Timestamp(asof)
        d = lab.build(df, qf)
        self.panel = d                              # 含特徵的完整面板：predict 的輸入列從這裡取
        if "train" in d:
            d = d[d["train"].astype(bool)]
        self.models = {}
        for h in self.horizons:
            tr = d[(d["month_end"] + pd.DateOffset(months=h) <= self.asof) & d[f"y_{h}"].notna() & d["m_bar"].notna()]
            self.models[h] = {m: lab.fit(m, tr, h) for m in MEMBERS}
        self.old = old or PEForecaster().fit(df, self.asof)
        return self

    def predict(self, rows, old_pred=None):
        """rows：t 時點的列，要有 lab.add_features 的特徵、ln_pe、y10。回傳每個 h 的成員與組合 ln PE。"""
        rows = rows.reset_index(drop=True)
        if old_pred is None:
            old_pred = self.old.predict(rows, OLD_H)
        out = pd.DataFrame({"ticker": rows["ticker"].to_numpy(), "month": rows["month"].to_numpy()})
        for h in self.horizons:
            for m in MEMBERS:
                lp, ok = lab.apply(self.models[h][m], rows)
                out[f"{m}_{h}"] = np.where(ok, lp, np.nan)
            if h in OLD_H:
                out[f"old_{h}"] = old_pred[f"lnpe_hat_{h}"].to_numpy(float)
            out[f"ens_{h}"] = combine(out[[f"{m}_{h}" for m in members_for(h)]])
        return out


def bands(asof, horizons=lab.HORIZONS, q=(0.1, 0.9)):
    """80% 區間：回測（results/lab_predictions.csv.gz）裡 asof 以前已揭曉的組合誤差（實際 − 預測）分位數。"""
    path = os.path.join(RES, "lab_predictions.csv.gz")
    if not os.path.exists(path):
        return {}
    p = pd.read_csv(path, parse_dates=["month"])
    p = p[p["ens"].notna() & p["actual"].notna()]
    out = {}
    for h in horizons:
        g = p[p["h"] == h]
        g = g[g["month"] + pd.offsets.MonthEnd(0) + pd.DateOffset(months=h) <= pd.Timestamp(asof)]
        if len(g) >= 300:
            e = g["actual"] - g["ens"]
            out[h] = (float(e.quantile(q[0])), float(e.quantile(q[1])))
    return out


def implied_earnings(lnpe, rows, h):
    """組合預測的本益比「隱含」的 h 月後盈餘TTM：市值 × e^(資金成本×h/12) ÷ 本益比。"""
    ret = (rows["y10"].to_numpy(float) + lab.ERP) * h / 12
    return np.exp(np.log(rows["mc"].to_numpy(float)) + ret - np.asarray(lnpe, float))


def return_surprise(d, h):
    """實際報酬 − 資金成本假設（ln），只取今天與 h 月後都有正盈餘的列（本益比有定義）。

    這正好是「盈餘完美預知」時本益比預測的誤差：ln PE(t+h) − [ln 市值 + 資金成本×h/12 − ln 真實盈餘]
    ＝ ln(市值(t+h)/市值(t)) − 資金成本×h/12。你自己給的盈餘若完全正確，剩下的誤差就只有這一項。
    """
    g = d[(d["ni_ttm"] > 0) & (d[f"ni_ttm_f{h}"] > 0) & d[f"mc_f{h}"].notna() & (d["mc"] > 0)]
    e = np.log(g[f"mc_f{h}"] / g["mc"]) - (g["y10"] + lab.ERP) * h / 12
    return pd.DataFrame({"month": g["month"], "month_end": g["month_end"], "e": e})


def return_bands(d, asof, horizons=lab.HORIZONS, q=(0.1, 0.9)):
    """情境（你給盈餘）的 80% 區間：asof 以前已揭曉的「報酬 − 資金成本」分位數。d＝lab.build 的面板。"""
    out = {}
    for h in horizons:
        r = return_surprise(d, h)
        r = r[r["month_end"] + pd.DateOffset(months=h) <= pd.Timestamp(asof)]
        if len(r) >= 300:
            out[h] = (float(r["e"].quantile(q[0])), float(r["e"].quantile(q[1])))
    return out


def horizon_stats():
    """每個預測距離的回測成績（lab_run.py 產生），給 CLI 顯示可信度。"""
    path = os.path.join(RES, "lab_horizon.csv")
    return pd.read_csv(path).set_index("h") if os.path.exists(path) else None
