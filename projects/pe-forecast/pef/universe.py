"""S&P 500 歷史成分股：某一天某個代號是不是成分股（用來檢查倖存者偏誤）。

資料：data/sp500_membership_spells.csv（github.com/fja05680/sp500 的 sp500_ticker_start_end.csv；
每列＝一段連續在指數裡的期間，end_date 空白＝到現在還在）。
名單裡的代號是「當時的代號」；我們的面板用現在的代號，所以改過代號的公司要對回舊代號（RENAMED；
每一組都核對過：舊代號離開那天＝新代號加入那天）。
"""
import os

import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# 現在的代號 → 以前在指數裡用過的代號（同一家公司、同一個法人）
RENAMED = {
    "LHX": ["HRS"], "GL": ["TMK"], "BKR": ["BHGE"], "RTX": ["UTX"], "HWM": ["ARNC"], "VTRS": ["MYL"],
    "CTRA": ["COG"], "WTW": ["WLTW"], "WBD": ["DISCA", "DISCK"], "BALL": ["BLL"], "META": ["FB"], "ELV": ["ANTM"],
    "GEN": ["NLOK", "SYMC"], "RVTY": ["PKI"], "FI": ["FISV"], "EG": ["RE"], "COR": ["ABC"], "DAY": ["CDAY"],
    "DOC": ["PEAK", "HCP"], "CPAY": ["FLT"],
}


def _norm(t):
    return str(t).upper().replace(".", "-")


def spells():
    s = pd.read_csv(os.path.join(DATA, "sp500_membership_spells.csv"), parse_dates=["start_date", "end_date"])
    s["ticker"] = s["ticker"].map(_norm)
    s["end_date"] = s["end_date"].fillna(pd.Timestamp("2100-01-01"))
    return s


def member_at(tickers, dates):
    """每一列：這個（現在的）代號在那一天是不是 S&P 500 成分股。tickers、dates 等長。"""
    s = spells()
    by = {t: g[["start_date", "end_date"]].to_numpy() for t, g in s.groupby("ticker")}
    out = []
    for t, d in zip(tickers, pd.to_datetime(dates)):
        names = [_norm(t)] + RENAMED.get(_norm(t), [])
        out.append(any(a <= d < b for n in names for a, b in by.get(n, [])))
    return pd.Series(out, dtype=bool)
