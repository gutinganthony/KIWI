"""一行載入模型面板。"""
import os

import pandas as pd

from .data import load_macro
from .features import monthly_panel, quarterly_features

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")


def panel():
    q = pd.read_csv(os.path.join(DATA, "quarters.csv"), parse_dates=["period_end", "filed", "avail"])
    p = pd.read_csv(os.path.join(DATA, "prices_monthly.csv"), parse_dates=["month"])
    u = pd.read_csv(os.path.join(DATA, "universe.csv"), keep_default_na=False)
    macro = load_macro(DATA)
    qf = quarterly_features(q)
    df = monthly_panel(qf, p, macro)
    df = df.merge(u[["ticker", "sector"]], on="ticker", how="left")
    return df, qf
