"""共識校正（README §19.1）：把 Yahoo 的本財年共識（調整後口徑）修正成「預期的實際 GAAP EPS」。

校正係數 ＝ exp(樹模型預測的 ln(實際 GAAP ÷ 共識))。線索和訓練時（lab_eps_correction.py 的「今天的線索」版）相同：
  共識隱含成長 ln(共識 ÷ 今天 GAAP 最近四季)、距離本財年年報幾個月、1／3 個月共識修正 ÷ 股價（Yahoo 的 30／90 天前共識）、
  這家公司過去的偏差與筆數（上限 8）、LTG（eps_correction_firm.csv）、營收成長、12 個月報酬、波動、市值在 S&P 500 的百分位、ln 本益比、
  公司類型、今天是否虧損。
走動式回測：EPS 誤差中位 0.144 → 0.112，12 個月本益比誤差（2022 以後）0.221 → 0.194（results/eps_correction.txt）。
假設：同一個係數也用在下一財年（EPS_b）——訓練資料只有本財年，這一步沒有驗證過。
"""
import json
import os
import pickle

import numpy as np
import pandas as pd

from pef import orbit

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "results")
_M = {}


def _load():
    if "m" not in _M:
        p = os.path.join(RES, "eps_correction_model.pkl")
        if not os.path.exists(p):
            _M.update(m=None)
            return None
        _M["m"] = pickle.load(open(p, "rb"))
        _M["meta"] = json.load(open(os.path.join(RES, "eps_correction_model.json")))
        f = pd.read_csv(os.path.join(RES, "eps_correction_firm.csv")).set_index("ticker")
        _M["firm"] = f
        n = pd.read_csv(os.path.join(RES, "now_all.csv"), usecols=["mc", "in_sp500"])
        _M["mc_ref"] = np.sort(n.loc[n["in_sp500"].astype(bool) & (n["mc"] > 0), "mc"].to_numpy(float))   # 市值百分位的參考：今天的 S&P 500
    return _M["m"]


def num(v):
    try:
        f = float(v)
        return f if np.isfinite(f) else np.nan
    except (TypeError, ValueError):
        return np.nan


def features(ticker, row, cons0, fy0_end, d30=None, d90=None, last_report=None, today=None):
    """row：今天的資料（px、eps0、g_rev、ret12、vol36、mc、sector）。cons0：本財年共識（調整後、每股）。fy0_end：本財年結束日。
    d30、d90：30／90 天前的本財年共識。last_report：最近一次年報日（90 天內換過財年就不算 3 個月修正）。"""
    _load()
    today = pd.Timestamp.now().normalize() if today is None else pd.Timestamp(today)
    f = _M["firm"].loc[ticker] if _M.get("firm") is not None and ticker in _M["firm"].index else None
    px, eps0 = num(row.get("px")), num(row.get("eps0"))
    lag = num(f["report_lag_days"]) if f is not None else np.nan
    report = pd.Timestamp(fy0_end) + pd.Timedelta(days=lag if np.isfinite(lag) else 60)
    lead = float(np.clip((report - today).days / 30.44, 0.5, 12.0))
    since = (today - pd.Timestamp(last_report)).days if last_report is not None and pd.notna(last_report) else 999
    rev = lambda old, days: float(np.clip((cons0 - old) / px, -0.2, 0.2)) if (np.isfinite(num(old)) and px > 0 and since > days) else np.nan
    mc = num(row.get("mc"))
    ref = _M.get("mc_ref")
    mc_rank = float(np.searchsorted(ref, mc, side="right") / len(ref)) if (ref is not None and len(ref) and mc > 0) else np.nan
    lpe = np.log(px / eps0) if (px > 0 and eps0 > 0) else np.nan
    return dict(cons_g=float(np.clip(np.log(cons0 / eps0), -2, 2)) if (cons0 > 0 and eps0 > 0) else np.nan,
                lead=lead, rev1=rev(d30, 30), rev3=rev(d90, 90),
                past_bias=num(f["past_bias"]) if f is not None else np.nan,
                n_past8=float(min(num(f["n_past"]), 8)) if f is not None else 0.0,
                ltg=num(f["ltg"]) if f is not None else np.nan, g_rev=num(row.get("g_rev")), ret12=num(row.get("ret12")),
                vol36=num(row.get("vol36")), mc_rank=mc_rank, ln_pe=lpe,
                grp_id=float(_M["meta"]["grp_id"].get(row.get("grp") or orbit.group_of(row.get("sector")), 3)), loss0=float(not eps0 > 0))


def correction(feats):
    """回傳 (係數 exp(預測), 預測的 ln 值)；沒有模型時回傳 (None, None)。"""
    m = _load()
    if m is None:
        return None, None
    X = np.array([[feats.get(c, np.nan) for c in _M["meta"]["features"]]], float)
    p = float(np.clip(m.predict(X)[0], -1.0, 0.7))
    return float(np.exp(p)), p
