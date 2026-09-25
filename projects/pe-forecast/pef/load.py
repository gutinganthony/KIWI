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


def panel_sp500():
    """S&P 500 全體（build_broad.py 產出）。sector：科技股名單內用細分產業，其餘用 GICS；in_tech＝在 68 家科技股名單裡。"""
    q = pd.read_csv(os.path.join(DATA, "quarters_sp500.csv"), parse_dates=["period_end", "filed", "avail"])
    p = pd.read_csv(os.path.join(DATA, "prices_monthly_sp500.csv"), parse_dates=["month"])
    u = pd.read_csv(os.path.join(DATA, "universe_sp500.csv"), keep_default_na=False)
    tech = set(pd.read_csv(os.path.join(DATA, "universe.csv"), keep_default_na=False)["ticker"])
    u["train"] = True
    u["in_tech"] = u["ticker"].isin(tech)
    macro = load_macro(DATA)
    qf = quarterly_features(q)
    df = monthly_panel(qf, p, macro)
    # 財報斷掉（例：銀行換了營收標籤）時不能一直沿用舊財報：最新一季季末超過 240 天就不用那個月
    df = df[(df["month_end"] - df["period_end"]).dt.days <= 240].reset_index(drop=True)
    df = df.merge(u[["ticker", "sector", "gics", "train", "in_tech"]], on="ticker", how="left")
    return df, qf
