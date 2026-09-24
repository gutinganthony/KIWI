#!/usr/bin/env python3
"""用最終模型跑一次「現在」快照：四大 CSP、記憶體、光通訊、半導體設備、能源、電力、軍工、其他那斯達克。

    python3 snapshot_run.py --raw <scratchpad 原始資料根目錄>

原始資料（不進版控）來源見 data/SOURCES.md 與 results/snapshot_*.md 的「資料來源」欄。
模型：只用 68 家科技股（data/universe.csv）訓練到今天；非科技股是「套用」，不是訓練對象（README §4b）。
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef.data import load_macro, stooq_monthly, unadjust_dividends   # noqa: E402
from pef.forecast import PEForecaster                                 # noqa: E402
from pef.load import panel                                            # noqa: E402
from pef import snapshot as sn                                        # noqa: E402

DATA = os.path.join(HERE, "data")
NOW = pd.Timestamp("2026-09-30")

# 名單：(ticker, 群組, CIK)。群組只用於報表分組。
LIST = [
    ("MSFT", "四大CSP", 789019), ("AMZN", "四大CSP", 1018724), ("GOOGL", "四大CSP", 1652044), ("META", "四大CSP", 1326801),
    ("ORCL", "四大CSP", 1341439),
    ("MU", "記憶體", 723125), ("SNDK", "記憶體", 2023554), ("WDC", "記憶體", 106040), ("STX", "記憶體", 1137789),
    ("COHR", "光通訊", 820318), ("LITE", "光通訊", 1633978), ("CIEN", "光通訊", 936395), ("FN", "光通訊", 1408710),
    ("AAOI", "光通訊", 1158114), ("CRDO", "光通訊", 1807794), ("ANET", "光通訊", 1596532), ("GLW", "光通訊", 24741),
    ("MRVL", "光通訊", 1835632),
    ("AMAT", "半導體設備", 6951), ("LRCX", "半導體設備", 707549), ("KLAC", "半導體設備", 319201), ("TER", "半導體設備", 97210),
    ("XOM", "能源", 34088), ("CVX", "能源", 93410), ("COP", "能源", 1163165),
    ("VST", "電力", 1692819), ("CEG", "電力", 1868275), ("NRG", "電力", 1013871), ("GEV", "電力", 1996810),
    ("LMT", "軍工", 936468), ("NOC", "軍工", 1133421), ("RTX", "軍工", 101829), ("GD", "軍工", 40533),
    ("LHX", "軍工", 202058), ("AVAV", "軍工", 1368622), ("KTOS", "軍工", 1069258), ("PLTR", "軍工", 1321655),
    ("NVDA", "那斯達克其他", 1045810), ("AVGO", "那斯達克其他", 1730168), ("AAPL", "那斯達克其他", 320193),
    ("AMD", "那斯達克其他", 2488), ("TSLA", "那斯達克其他", 1318605), ("NFLX", "那斯達克其他", 1065280),
    ("CRWD", "那斯達克其他", 1535527), ("INTC", "那斯達克其他", 50863), ("CSCO", "那斯達克其他", 858877),
]
YEN = {"SNDK", "WDC", "VST", "PLTR", "AVAV", "KTOS", "MRVL"}   # yennanliu 財報（到 2026 年中、Q4 已拆出）


def load_repo_quarters():
    q = []
    for tag in ("", "_ext"):
        f = os.path.join(DATA, f"quarters{tag}.csv")
        if os.path.exists(f):
            q.append(pd.read_csv(f, parse_dates=["period_end", "filed", "avail"]))
    return pd.concat(q, ignore_index=True)


def price_series(raw, t):
    """依序找：只分割還原（blake）→ yennanliu → Stell0 → natezone。回傳 (月底收盤, 最後交易日, 來源)。"""
    for kind, path in (("blake", f"{raw}/ext/px/{t}.csv"), ("yen", f"{raw}/yen/p/{t.lower()}.csv"),
                       ("stell0", f"{raw}/px_now/stell0_{t}.csv"), ("natezone", f"{raw}/px_now/natezone_{t}.csv")):
        if os.path.exists(path) and os.path.getsize(path) > 200:
            m, last = sn.monthly_close(path, kind)
            if len(m) >= 7:
                return m, last, kind
    return None, None, None


def split_factor_since(raw, t, new_m):
    """財報口徑（2025 年中）到現價口徑之間有沒有分割：用 Stooq（2025-09 口徑）對新來源在重疊月份的比值。"""
    sp = f"{raw}/src_hj/data/sp500_stooq_ohcl/{t.lower()}.us.txt"
    if not os.path.exists(sp):
        return 1.0
    old = stooq_monthly(sp)
    ov = pd.concat([old.rename("o"), new_m.rename("n")], axis=1).dropna()
    ov = ov[(ov.index >= "2025-05-01") & (ov.index <= "2025-08-31")]
    if ov.empty:
        return 1.0
    r = float(np.median(ov["o"] / ov["n"]))
    for s in (2, 3, 4, 5, 7, 8, 10, 15, 20):
        if abs(np.log(r / s)) < 0.08:
            return float(s)
    return 1.0


CORE_TAX = 0.15   # 核心淨利 ＝ 營業利益 × (1 − 15%)：固定假設，忽略利息收支——只用來辨識與粗估一次性項目


def core_adjust(Q):
    """辨識 TTM 內的一次性項目，產生「調整後」季表。

    有營業利益的季：核心淨利 ＝ 營業利益 × 0.85。GAAP 淨利偏離核心淨利超過「營收的 3%」且超過「核心淨利的 30%」
                    → 視為含一次性項目（投資評價利得、出售資產、稅務或減損費用——都在營業利益以下）。
    沒有營業利益的季（AXIOM 補的最新季）：淨利率偏離前 8 季中位 > max(15pp, 50%)，且營收季變化在 0.85–1.2 倍。
    調整後淨利：有營業利益用核心淨利；沒有就用 營收 × 前 8 季中位淨利率。
    回傳 (調整後季表, {ticker: [(季末, GAAP 淨利, 調整後淨利, 依據)]})。
    """
    out, notes = [], {}
    for t, g in Q.sort_values("period_end").groupby("ticker"):
        g = g.reset_index(drop=True).copy()
        m = g["ni"] / g["rev"]
        for i in range(max(0, len(g) - 5), len(g)):
            oi, ni, rev = g.loc[i, "oi"], g.loc[i, "ni"], g.loc[i, "rev"]
            if np.isfinite(oi):
                core = oi * (1 - CORE_TAX)
                gap = ni - core
                if abs(gap) > 0.03 * rev and abs(gap) > 0.30 * abs(core):
                    notes.setdefault(t, []).append((g.loc[i, "period_end"], ni, core,
                                                    f"GAAP 淨利比 營業利益×0.85 {'多' if gap > 0 else '少'} {abs(gap) / rev:.0%} 營收"))
                    g.loc[i, "ni"] = core
            elif i >= 8:
                mbar = m.iloc[i - 8:i].median()
                rr = rev / g.loc[i - 1, "rev"]
                if mbar > 0 and abs(m.iloc[i] - mbar) > max(0.15, 0.5 * mbar) and 0.85 < rr < 1.2:
                    core = rev * mbar
                    notes.setdefault(t, []).append((g.loc[i, "period_end"], ni, core,
                                                    f"淨利率 {m.iloc[i]:.0%} vs 前 8 季中位 {mbar:.0%}（此季無營業利益資料）"))
                    g.loc[i, "ni"] = core
        out.append(g)
    return pd.concat(out, ignore_index=True), notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    a = ap.parse_args()
    raw = a.raw
    repo_q = load_repo_quarters()
    macro = load_macro(DATA)
    quarters, prices, meta = [], {}, []
    for t, grp, cik in LIST:
        src = []
        if t in YEN and os.path.exists(f"{raw}/yen/f/{t.lower()}.csv"):
            q = sn.yen_quarters(f"{raw}/yen/f/{t.lower()}.csv", t)
            src.append("yennanliu")
        elif os.path.exists(f"{raw}/optical_probe/loosygoosie/{cik}.json") and t not in ("SNDK", "MRVL"):
            q = sn.lg_quarters(f"{raw}/optical_probe/loosygoosie/{cik}.json", t)
            src.append("loosygoosie(12季)")
        elif os.path.exists(f"{raw}/ext/facts/CIK{cik:010d}.json") and (
                not (repo_q["ticker"] == t).any() or repo_q[repo_q["ticker"] == t]["period_end"].max() < pd.Timestamp("2025-12-01")):
            q = sn.facts_quarters(f"{raw}/ext/facts/CIK{cik:010d}.json", t)      # kotoba 2026-07 快照比 repo 新
            src.append("SEC鏡像(2026-07)")
        elif (repo_q["ticker"] == t).any():
            q = repo_q[repo_q["ticker"] == t].sort_values("period_end").reset_index(drop=True)
            src.append("SEC鏡像")
        elif os.path.exists(f"{raw}/src_hj/data/company_facts/CIK{cik:010d}.json"):
            q = sn.facts_quarters(f"{raw}/src_hj/data/company_facts/CIK{cik:010d}.json", t)
            if q is None or q["rev"].notna().sum() < 6:
                meta.append(dict(ticker=t, group=grp, status="財報季數不足"))
                continue
            src.append("SEC鏡像")
        else:
            meta.append(dict(ticker=t, group=grp, status="沒有財報歷史"))
            continue
        ax = f"{raw}/axiom/{cik:010d}.json"
        if os.path.exists(ax):
            q, n_add = sn.axiom_append(q, ax)
            if n_add:
                src.append(f"AXIOM+{n_add}季")
        m, last, kind = price_series(raw, t)
        if m is None:
            meta.append(dict(ticker=t, group=grp, status="沒有股價"))
            continue
        fac = split_factor_since(raw, t, m) if "SEC鏡像" in src else 1.0
        if fac != 1.0:
            # 財報最後一季若仍是分割前口徑（股數與 2025 年中相近），乘上分割比例
            base = q[q["filed"] <= "2025-09-30"]["sh"].dropna()
            if len(base):
                q["sh_now"] = np.where(q["sh"] < base.iloc[-1] * np.sqrt(fac), q["sh_now"] * fac, q["sh_now"])
        if "oi" not in q:
            q["oi"] = np.nan
        quarters.append(q[["ticker", "period_end", "filed", "avail", "rev", "gp", "oi", "ni", "sh", "sh_now", "inv",
                           "equity", "cash", "debt"]])
        prices[t] = (m, last)
        meta.append(dict(ticker=t, group=grp, status="ok", fin_src="+".join(src), px_src=kind, split_adj=fac))
    Q = pd.concat(quarters, ignore_index=True)
    Qc, notes = core_adjust(Q)
    sectors = {t: g for t, g, _ in LIST}
    df, _ = panel()
    fc = PEForecaster().fit(df, NOW)
    res = {}
    for tag, QQ in (("gaap", Q), ("core", Qc)):
        res[tag] = run_rows(QQ, prices, macro, sectors, fc)
    out = res["gaap"]
    core = res["core"].set_index("ticker")
    out["adj"] = out["ticker"].isin(notes)
    for c in ("pe_now", "lnpe_hat_12", "lnpe_hat_24", "ni_hat_12", "ni_ttm", "implied_m"):
        out[f"core_{c}"] = out["ticker"].map(core[c])
    meta = pd.DataFrame(meta)
    out = out.merge(meta, on="ticker", how="left")
    out.to_csv(os.path.join(HERE, "results", "snapshot_2026-09.csv"), index=False, float_format="%.6g")
    write_md(out, meta, notes)


def run_rows(Q, prices, macro, sectors, fc):
    rows = sn.snapshot_rows(Q, prices, macro, sectors, NOW)
    # 財報落後的：把錨點移回「那一季還是最新」的月份，用那個月的股價，避免拿一年前的盈餘配今天的股價
    anchored = []
    for i, r in rows.iterrows():
        if r["stale"]:
            anchor = r["period_end"] + pd.Timedelta(days=136)
            m, _ = prices[r["ticker"]]
            m = m[m.index <= anchor]
            if len(m) >= 7:
                p = m.iloc[-1]
                p6 = m[m.index <= m.index[-1] - pd.DateOffset(months=6)].iloc[-1]
                rows.loc[i, "price"] = p              # 錨點月的股價（市值、本益比都用這個）
                rows.loc[i, "mc"] = p * r["sh_now"]
                rows.loc[i, "ret6"] = np.log(p / p6)
                rows.loc[i, "month"] = pd.Timestamp(m.index[-1].year, m.index[-1].month, 1)
                rows.loc[i, "month_end"] = m.index[-1]
                anchored.append(r["ticker"])
    rows["ln_ps"] = np.log(rows["mc"] / rows["rev_ttm"])
    rows["pe_now"] = rows["mc"] / rows["ni_ttm"]
    rows["ep"] = rows["ni_ttm"] / rows["mc"]
    rows["ep_c"] = rows["ep"].clip(-0.3, 0.3)
    rows = rows[rows["sigma"].notna() & rows["m_bar"].notna()].reset_index(drop=True)
    p = fc.predict(rows, (6, 12, 24))
    return rows[["ticker", "sector", "period_end", "month_end", "price", "mc", "ni_ttm", "pe_now", "m_ttm", "m_bar",
                 "stale", "n_quarters", "fin_age_days"]].join(
        p[["implied_m", "ni_hat_12", "lnpe_hat_6", "lnpe_hat_12", "lnpe_hat_24", "lnpe_flat_12", "m_hat_12", "ni_hat_6",
           "ni_hat_24"]])


def _pe(x):
    return "虧損" if not np.isfinite(x) or x <= 0 else f"{x:.1f}"


def write_md(out, meta, notes):
    L = ["# 前瞻本益比快照：2026-09（最終模型，只從 68 家科技股學到的規律）", "",
         "> 由 `snapshot_run.py` 產生。**不是投資建議，是模型輸出**：本益比 ＝ 市值 ÷ 預測盈餘，報酬假設＝資金成本 9.6%/年。",
         "> 「若股價不動」那一欄＝純粹盈餘變化造成的本益比變化；兩欄的差＝報酬假設。",
         "> ⏳＝財報只到較早的季度：錨點移回那一季仍是最新的月份（「錨點」欄），用那個月的股價，預測期間從錨點起算。",
         "> ⚠️＝TTM 內有一次性項目（投資評價利得、出售資產、稅務或減損費用）：辨識方法與逐季明細見文末。",
         ">   「調整後」＝把那幾季換成「營業利益 × 0.85」（或營收 × 近 8 季中位淨利率）再跑一次模型——**是估計，不是財報數字**。",
         "> 能源、電力、軍工、TSLA 不在訓練名單裡（模型只學過科技股），樣本外測試結果見 README §4b。", ""]
    for grp in out["group"].dropna().unique():
        g = out[out["group"] == grp]
        L += [f"## {grp}", "",
              "| 公司 | 錨點 | 最新財報季末 | 目前本益比 | 12 月後盈餘變化 | **12 月後本益比** | 若股價不動 | 24 月後本益比 | 隱含長期淨利率／5 年中位 | 調整後：目前 → 12 月後 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for r in g.itertuples():
            chg = f"{r.ni_hat_12 / r.ni_ttm - 1:+.0%}" if r.ni_ttm > 0 and r.ni_hat_12 > 0 else ("轉虧" if r.ni_hat_12 <= 0 else "由虧轉盈")
            imp = f"{r.implied_m:.0%} / {r.m_bar:.0%}" if np.isfinite(r.implied_m) else "—"
            if np.isfinite(r.implied_m) and r.implied_m > 0.8:
                imp += "（框架失效）"
            adj = "—"
            if r.adj:
                adj = f"{_pe(r.core_pe_now)} → {_pe(np.exp(r.core_lnpe_hat_12)) if r.core_ni_hat_12 > 0 else '虧損'}"
            tag = ("⏳ " if r.stale else "") + ("⚠️ " if r.adj else "")
            L.append(f"| {tag}{r.ticker} | {pd.Timestamp(r.month_end):%Y-%m} | {pd.Timestamp(r.period_end):%Y-%m-%d} | "
                     f"{_pe(r.pe_now)} | {chg} | **{_pe(np.exp(r.lnpe_hat_12)) if r.ni_hat_12 > 0 else '虧損'}** | "
                     f"{_pe(np.exp(r.lnpe_flat_12)) if r.ni_hat_12 > 0 else '虧損'} | "
                     f"{_pe(np.exp(r.lnpe_hat_24)) if r.ni_hat_24 > 0 else '虧損'} | {imp} | {adj} |")
        L.append("")
    L += ["## 一次性項目明細（⚠️ 的依據）", "",
          "辨識：核心淨利 ＝ 營業利益 × 0.85（假設 15% 稅、忽略利息）。GAAP 淨利偏離核心淨利超過營收的 3% 且超過核心的 30% → 一次性項目",
          "（一次性項目都在營業利益以下）。沒有營業利益資料的季（AXIOM 補的最新季）：淨利率偏離前 8 季中位 > max(15pp, 50%)。", "",
          "| 公司 | 季末 | GAAP 淨利 $B | 調整後淨利 $B（估計） | 依據 |", "|---|---|---|---|---|"]
    for t in sorted(notes):
        for pe_, ni, core, why in notes[t]:
            L.append(f"| {t} | {pd.Timestamp(pe_):%Y-%m-%d} | {ni / 1e9:,.2f} | {core / 1e9:,.2f} | {why} |")
    L += ["", "## 資料來源", "", "| 公司 | 財報 | 可用季數 | 股價 |", "|---|---|---|---|"]
    for r in out.itertuples():
        L.append(f"| {r.ticker} | {r.fin_src} | {r.n_quarters} | {r.px_src}（{pd.Timestamp(r.month_end):%Y-%m} 的月底收盤；最新 2026-09-23） |")
    L += ["", "季數 < 20 的公司，「5 年中位淨利率」實際上是可用季數的中位（例：光通訊多數只有 12 季＝3 年）。"]
    miss = meta[meta["status"] != "ok"]
    if len(miss):
        L += ["", "## 沒跑到的", "", "| 公司 | 群組 | 原因 |", "|---|---|---|"]
        L += [f"| {r.ticker} | {r.group} | {r.status} |" for r in miss.itertuples()]
    open(os.path.join(HERE, "results", "snapshot_2026-09.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
