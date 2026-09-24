"""把逐季財報＋月股價變成「月 × 公司」的面板，每一列只含那個月**已經公告**的資訊。

標準輸入格式（data.py 負責把各種來源轉成這個樣子）：

  quarters：ticker, period_end, avail, rev, gp, ni, inv, equity, debt, cash   （單季流量、期末存量）
  prices  ：ticker, month, mc                                              （月底市值）
  macro   ：month, y10, infl

avail ＝ 這一季財報可被使用的日期（有申報日就用申報日，沒有就季末 + 60 天）。
"""
import numpy as np
import pandas as pd

HORIZONS_Q = (2, 4, 8, 12)      # 預測幾季後：6、12、24、36 個月
WIN = 20                        # 「結構水準」與「波動」用近 20 季（5 年）
MINWIN = 8


def quarterly_features(q):
    """每家公司、每一季的衍生量。只往回看，不用未來資料。"""
    out = []
    for t, g in q.sort_values("period_end").groupby("ticker", sort=False):
        g = g.copy().reset_index(drop=True)
        # 早期 XBRL 會缺季：四季加總必須真的橫跨一年，否則作廢
        span3 = (g["period_end"] - g["period_end"].shift(3)).dt.days
        span4 = (g["period_end"] - g["period_end"].shift(4)).dt.days
        ok4 = span3.between(250, 300)
        roll4 = lambda s: s.rolling(4, min_periods=4).sum().where(ok4)
        g["rev_ttm"] = roll4(g["rev"])
        g["ni_ttm"] = roll4(g["ni"])
        g["gp_ttm"] = roll4(g["gp"])
        g["m_q"] = g["ni"] / g["rev"]
        g["m_ttm"] = g["ni_ttm"] / g["rev_ttm"]
        g["gm_q"] = g["gp"] / g["rev"]
        yoy = span4.between(330, 400)
        g["g_rev"] = np.log(g["rev_ttm"] / g["rev_ttm"].shift(4)).where(yoy)
        g["acc"] = (np.log(g["rev"] / g["rev"].shift(4)) - g["g_rev"]).where(yoy)
        g["gm_slope"] = (g["gm_q"] - g["gm_q"].shift(2)).where(
            (g["period_end"] - g["period_end"].shift(2)).dt.days.between(160, 200))
        cogs_ttm = (g["rev_ttm"] - g["gp_ttm"]).where(lambda s: s > 0)
        inv_days = g["inv"] / (cogs_ttm / 365.0)
        g["d_inv"] = np.log(inv_days / inv_days.shift(4)).where((inv_days > 1) & yoy)
        g["m_bar"] = g["m_q"].rolling(WIN, min_periods=MINWIN).median()
        g["sigma"] = g["m_q"].rolling(WIN, min_periods=MINWIN).std()
        ic = g["equity"].fillna(0) + g["debt"].fillna(0) - g["cash"].fillna(0)
        g["sc"] = (g["rev_ttm"] / ic.where(ic > 0)).clip(0.5, 5.0).fillna(5.0)
        g["qidx"] = np.arange(len(g))
        # 目標：k 季後的 TTM 營收（log 成長）與 TTM 淨利率、TTM 淨利（評估用）
        for k in HORIZONS_Q:
            fwd_ok = (g["period_end"].shift(-k) - g["period_end"]).dt.days.between(91 * k - 25, 91 * k + 25)
            g[f"y_rev_{k}"] = np.log(g["rev_ttm"].shift(-k) / g["rev_ttm"]).where(fwd_ok)
            g[f"y_m_{k}"] = g["m_ttm"].shift(-k).where(fwd_ok)
            g[f"avail_{k}"] = g["avail"].shift(-k)
        out.append(g)
    return pd.concat(out, ignore_index=True)


def monthly_panel(qf, prices, macro):
    """每個（公司, 月）接上「那個月底為止最新已公告的一季」。"""
    rows = []
    qf = qf.dropna(subset=["rev_ttm"]).sort_values("avail")
    for t, p in prices.groupby("ticker"):
        g = qf[qf["ticker"] == t]
        if g.empty:
            continue
        p = p.sort_values("month").copy()
        p["month_end"] = p["month"] + pd.offsets.MonthEnd(0)
        m = pd.merge_asof(p, g.drop(columns=["ticker"]), left_on="month_end", right_on="avail",
                          direction="backward")
        rows.append(m)
    df = pd.concat(rows, ignore_index=True).dropna(subset=["rev_ttm"])
    df = df.merge(macro, on="month", how="left")
    df = df.sort_values(["ticker", "month"]).reset_index(drop=True)
    # 市場資訊：股價動能、股價營收比（市場對未來利潤率×成長的定價）
    df["ret6"] = df.groupby("ticker")["mc"].transform(lambda s: np.log(s / s.shift(6)))
    df["ln_ps"] = np.log(df["mc"] / df["rev_ttm"])
    df["pe"] = df["mc"] / df["ni_ttm"]
    df["ln_pe"] = np.where(df["ni_ttm"] > 0, np.log(df["mc"] / df["ni_ttm"].where(df["ni_ttm"] > 0)), np.nan)
    df["ep"] = df["ni_ttm"] / df["mc"]
    df["ep_c"] = df["ep"].clip(-0.3, 0.3)      # 市場對「現在盈餘」的定價：低 E/P ＝ 市場預期盈餘會長
    return df


def attach_future(df, h_months):
    """把 t+h 月的實際值接到 t 列上（評估用；模型本身不准讀這些欄位）。"""
    key = df[["ticker", "month", "mc", "ni_ttm", "rev_ttm", "ln_pe", "ep", "qidx"]].copy()
    key["month"] = key["month"] - pd.DateOffset(months=h_months)
    key = key.rename(columns={c: f"{c}_f{h_months}" for c in key.columns if c not in ("ticker", "month")})
    return df.merge(key, on=["ticker", "month"], how="left")
