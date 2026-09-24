#!/usr/bin/env python3
"""前瞻本益比模型 —— 指令入口。

  python3 pe_forecast.py predict MU                       # 用最新資料預測 6/12/24/36 個月後的本益比
  python3 pe_forecast.py predict MU --asof 2025-09        # 站在 2025-09（只用當時資料）預測
  python3 pe_forecast.py predict MU --rev-growth 0.3,0.1,0 --margin 0.35,0.3,0.25 --mu 0.0
                                                          # 用你自己的盈餘與報酬假設（情境）
  python3 pe_forecast.py implied MU NVDA MSFT GOOGL       # 市場現價隱含的長期淨利率 vs 公司歷史
  python3 pe_forecast.py backtest                          # 全部回測，寫進 results/
  python3 pe_forecast.py history MU --h 12                 # 過去每個月「12 個月前的預測」vs 實際

設計見 DESIGN.md，回測證據與限制見 README.md。
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pef import backtest as bt          # noqa: E402
from pef.features import attach_future  # noqa: E402
from pef.forecast import PEForecaster   # noqa: E402
from pef.load import panel              # noqa: E402

RES = os.path.join(HERE, "results")
H_ALL = (6, 12, 24, 36)
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)


def _pe(x):
    if x is None or not np.isfinite(x):
        return "—"
    return "虧損" if x <= 0 else f"{x:.1f}"


def _implied_read(m, m_bar):
    if not np.isfinite(m):
        return "無法反推"
    if m > 0.8:
        return "只靠利潤率撐不起現價 → 市場在賭成長延續得比模型久（利潤率框架失效）"
    if m > m_bar * 1.25:
        return "市場在賭利潤率結構性變高"
    if m > m_bar * 0.8:
        return "市場大致照歷史利潤率定價"
    return "市場在賭利潤率會變差（典型：週期高點）"


def _row(df, ticker, asof):
    g = df[df["ticker"] == ticker]
    if g.empty:
        sys.exit(f"找不到 {ticker}。可用：{', '.join(sorted(df['ticker'].unique()))}")
    if asof:
        g = g[g["month"] <= pd.Timestamp(asof + "-01")]
    g = g[g["sigma"].notna() & g["m_bar"].notna()]
    if g.empty:
        sys.exit(f"{ticker} 在 {asof} 之前沒有足夠資料（至少要 8 季財報）")
    return g.tail(1)


def cmd_predict(a):
    df, _ = panel()
    row = _row(df, a.ticker, a.asof)
    asof = row["month_end"].iloc[0]
    fc = PEForecaster().fit(df, asof)
    ov = {}
    if a.rev_growth:
        ov["rev_growth"] = [float(x) for x in a.rev_growth.split(",")]
    if a.margin:
        ov["margin"] = [float(x) for x in a.margin.split(",")]
    if a.m_bar is not None:
        ov["m_bar"] = a.m_bar
    p = fc.predict(row, H_ALL, override=ov or None, mu=a.mu).iloc[0]
    r = row.iloc[0]
    print(f"\n{a.ticker}  站在 {asof.date()}（只用這天以前公告的財報與股價）")
    print(f"  最新一季財報：季末 {r['period_end'].date()}，公告 {r['avail'].date()}")
    print(f"  市值 ${r['mc']/1e9:,.1f}B；TTM 淨利 ${r['ni_ttm']/1e9:,.2f}B；"
          f"TTM 淨利率 {r['m_ttm']:.1%}（5 年中位 {r['m_bar']:.1%}）")
    print(f"  今天的本益比（TTM）：{_pe(r['pe'])}")
    y10 = r["y10"]
    y10_note = f"，{r['y10_asof']:%Y-%m} 的值" if r["y10_asof"] < r["month"] else ""
    mu_txt = f"你給的 {a.mu:+.1%}/年" if a.mu is not None else f"資金成本 {y10 + fc.erp:.1%}/年（10 年期 {y10:.2%}{y10_note} + 5%）"
    print(f"  報酬假設：{mu_txt}；情境覆寫：{ov if ov else '無（用模型的盈餘預測）'}\n")
    rows = []
    for h in H_ALL:
        rows.append({"幾個月後": h,
                     "預測營收TTM $B": p[f"rev_hat_{h}"] / 1e9,
                     "預測淨利率": f"{p[f'm_hat_{h}']:.1%}",
                     "預測淨利TTM $B": p[f"ni_hat_{h}"] / 1e9,
                     "盈餘變化": f"{p[f'ni_hat_{h}']/r['ni_ttm']-1:+.0%}" if r["ni_ttm"] > 0 else "—",
                     "預測PE（主）": "虧損" if p[f"ni_hat_{h}"] <= 0 else _pe(np.exp(p[f"lnpe_hat_{h}"])),
                     "若股價不動": "虧損" if p[f"ni_hat_{h}"] <= 0 else _pe(np.exp(p[f"lnpe_flat_{h}"])),
                     "若照過去10年報酬": "虧損" if p[f"ni_hat_{h}"] <= 0 else _pe(np.exp(p[f"lnpe_hist_{h}"]))})
    print(pd.DataFrame(rows).round(2).to_string(index=False))
    print(f"\n  市場現價隱含的長期淨利率：{p['implied_m']:.1%}（公司 5 年中位 {r['m_bar']:.1%}）——{_implied_read(p['implied_m'], r['m_bar'])}")
    print("  讀法：本益比的變化 ＝ 股價報酬 − 盈餘成長。盈餘那一項是模型預測的；報酬那一項不可預測，")
    print("        所以同時列出三種報酬假設。回測誤差見 README §3。")


def cmd_implied(a):
    df, _ = panel()
    out = []
    for t in a.tickers:
        row = _row(df, t, a.asof)
        fc = PEForecaster().fit(df, row["month_end"].iloc[0])
        p = fc.predict(row, (12,)).iloc[0]
        r = row.iloc[0]
        out.append({"公司": t, "時點": str(row["month_end"].iloc[0].date()), "PE": _pe(r["pe"]),
                    "TTM淨利率": f"{r['m_ttm']:.1%}", "5年中位淨利率": f"{r['m_bar']:.1%}",
                    "市場隱含長期淨利率": f"{p['implied_m']:.1%}", "隱含/歷史": f"{p['implied_m']/r['m_bar']:.2f}x" if r["m_bar"] > 0 else "—",
                    "解讀": _implied_read(p["implied_m"], r["m_bar"]),
                    "前瞻倍數(市值/12月後淨利)": f"{r['mc']/p['ni_hat_12']:.1f}" if p["ni_hat_12"] > 0 else "—",
                    "模型12月後盈餘變化": f"{p['ni_hat_12']/r['ni_ttm']-1:+.0%}" if r["ni_ttm"] > 0 else "—"})
    print(pd.DataFrame(out).to_string(index=False))
    print("\n隱含長期淨利率：在模型的 3 年盈餘路徑、成長 5 年半衰、資金成本 10 年期+5% 之下，要多高的長期淨利率才撐得起現價。")


def cmd_backtest(a):
    os.makedirs(RES, exist_ok=True)
    df, _ = panel()
    pred, fits = bt.run(df, start_year=a.start)
    keep = ["ticker", "month", "fit_year", "mc", "ni_ttm", "implied_m"] + \
           [f"{c}_{h}" for h in H_ALL for c in ("ni_hat", "lnpe_hat", "lnpe_hist", "lnpe_flat")]
    pred[keep].to_csv(os.path.join(RES, "predictions.csv.gz"), index=False, float_format="%.5g", compression="gzip")
    fits.to_csv(os.path.join(RES, "fits.csv"), index=False)
    tabs = []
    for nm, per in (("全期", None), ("選模期2015-21", bt.SELECT), ("保留期2022-26", bt.HOLDOUT)):
        s = bt.evaluate(df, pred, period=per)
        s.insert(0, "期間", nm)
        tabs.append(s)
    sc = pd.concat(tabs)
    sc.to_csv(os.path.join(RES, "scores.csv"), index=False, float_format="%.4f")
    sec = []
    for s_ in sorted(df["sector"].dropna().unique()):
        s = bt.evaluate(df, pred, sectors=[s_])
        s.insert(0, "產業", s_)
        sec.append(s)
    pd.concat(sec).to_csv(os.path.join(RES, "scores_by_sector.csv"), index=False, float_format="%.4f")
    bt.ep_scores(df, pred).to_csv(os.path.join(RES, "scores_ep.csv"), index=False, float_format="%.4f")
    bt.earnings_scores(df, pred).to_csv(os.path.join(RES, "scores_earnings.csv"), index=False, float_format="%.4f")
    bt.decompose(df, 12).to_csv(os.path.join(RES, "decompose_12m.csv"), index=False, float_format="%.4f")
    main = sc[(sc["期間"] == "全期")].pivot(index="方法", columns="h", values="中位絕對誤差")
    print("\nln PE 中位絕對誤差（全期；越小越好）\n", main.round(3).to_string())
    print(f"\n已寫入 {RES}/")


def cmd_history(a):
    path = os.path.join(RES, "predictions.csv.gz")
    if not os.path.exists(path):
        sys.exit("先跑 python3 pe_forecast.py backtest")
    pred = pd.read_csv(path, parse_dates=["month"])
    df, _ = panel()
    h = a.h
    f = attach_future(df, h)[["ticker", "month", f"ln_pe_f{h}", "ln_pe", "ep"]]
    d = pred[pred["ticker"] == a.ticker].merge(f, on=["ticker", "month"])
    d["預測於"] = d["month"].dt.strftime("%Y-%m")
    d["目標月"] = (d["month"] + pd.DateOffset(months=h)).dt.strftime("%Y-%m")
    d["當時PE"] = np.where(d["ep"] <= 0, "虧損", np.exp(d["ln_pe"]).map(_pe))
    d["模型預測PE"] = np.exp(d[f"lnpe_hat_{h}"]).map(_pe)
    ep_f = attach_future(df, h)[["ticker", "month", f"ep_f{h}"]]
    d = d.merge(ep_f, on=["ticker", "month"], how="left")
    d["實際PE"] = np.where(d[f"ep_f{h}"].isna(), "（未到）", np.where(d[f"ep_f{h}"] <= 0, "虧損", np.exp(d[f"ln_pe_f{h}"]).map(_pe)))
    d["模型預測PE"] = np.where(d[f"ni_hat_{h}"] <= 0, "虧損", d["模型預測PE"])
    d = d[d["month"].dt.month.isin([3, 6, 9, 12])]
    print(d[["預測於", "目標月", "當時PE", "模型預測PE", "實際PE"]].to_string(index=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("predict")
    p.add_argument("ticker")
    p.add_argument("--asof", help="YYYY-MM；預設＝最新")
    p.add_argument("--mu", type=float, help="年化報酬假設（預設＝資金成本）")
    p.add_argument("--rev-growth", help="未來 1/2/3 年營收成長，例 0.3,0.1,0.05")
    p.add_argument("--margin", help="未來 1/2/3 年 TTM 淨利率，例 0.35,0.3,0.25")
    p.add_argument("--m-bar", type=float, help="結構淨利率（覆寫 5 年中位數）")
    p.set_defaults(fn=cmd_predict)
    p = sp.add_parser("implied")
    p.add_argument("tickers", nargs="+")
    p.add_argument("--asof")
    p.set_defaults(fn=cmd_implied)
    p = sp.add_parser("backtest")
    p.add_argument("--start", type=int, default=2015)
    p.set_defaults(fn=cmd_backtest)
    p = sp.add_parser("history")
    p.add_argument("ticker")
    p.add_argument("--h", type=int, default=12, choices=H_ALL)
    p.set_defaults(fn=cmd_history)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
