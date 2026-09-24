"""一行載入模型面板。"""
import os

import pandas as pd

from .data import load_macro
from .features import monthly_panel, quarterly_features

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")


def _read(tag):
    q = pd.read_csv(os.path.join(DATA, f"quarters{tag}.csv"), parse_dates=["period_end", "filed", "avail"])
    p = pd.read_csv(os.path.join(DATA, f"prices_monthly{tag}.csv"), parse_dates=["month"])
    u = pd.read_csv(os.path.join(DATA, "universe.csv" if not tag else f"universe{tag}.csv"), keep_default_na=False)
    return q, p, u


def panel(include_ext=False):
    """月面板。include_ext=True 會加上 universe_ext.csv 的非科技公司，並標 train=False：
    模型只從科技股學（train=True），外加的公司只拿來「樣本外領域」測試與套用。"""
    q, p, u = _read("")
    u["train"] = True
    if include_ext:
        q2, p2, u2 = _read("_ext")
        u2["train"] = False
        q, p, u = pd.concat([q, q2]), pd.concat([p, p2]), pd.concat([u, u2])
    macro = load_macro(DATA)
    qf = quarterly_features(q)
    df = monthly_panel(qf, p, macro)
    df = df.merge(u[["ticker", "sector", "train"]], on="ticker", how="left")
    return df, qf
