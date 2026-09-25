#!/usr/bin/env python3
"""前瞻本益比模型 —— 指令入口。

  python3 pe_forecast.py predict MU                       # 用最新資料預測 3–36 個月後的本益比（組合模型＋盈餘拆解）
  python3 pe_forecast.py predict MU --asof 2025-09        # 站在 2025-09（只用當時資料）預測
  python3 pe_forecast.py predict MU --rev-growth 0.3,0.1,0 --margin 0.35,0.3,0.25 --mu 0.0
                                                          # 用你自己的盈餘與報酬假設（情境）
  python3 pe_forecast.py implied MU NVDA MSFT GOOGL       # 市場現價隱含的長期淨利率 vs 公司歷史
  python3 pe_forecast.py backtest                          # 全部回測，寫進 results/
  python3 pe_forecast.py history MU --h 12                 # 過去每季「12 個月前的預測」vs 實際
  python3 lab_run.py                                       # 改良實驗：哪個距離、哪個方法最有效（README §12）

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
from pef import ensemble as en          # noqa: E402
from pef.lab import HORIZONS            # noqa: E402
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


def _error_quantiles(df, asof):
    """80% 區間：用回測裡「asof 以前已揭曉」的模型誤差（實際 − 預測，ln）的 10/90 分位數。先跑 backtest。"""
    path = os.path.join(RES, "predictions.csv.gz")
    if not os.path.exists(path):
        return {}
    pred = pd.read_csv(path, parse_dates=["month"])
    out = {}
    for h in H_ALL:
        j = bt.joined(df, pred, h)
        j = j[j[f"ln_pe_f{h}"].notna() & j[f"lnpe_hat_{h}"].notna()]
        j = j[j["month"] + pd.offsets.MonthEnd(0) + pd.DateOffset(months=h) <= asof]
        if len(j) >= 300:
            e = j[f"ln_pe_f{h}"] - j[f"lnpe_hat_{h}"]
            out[h] = (float(e.quantile(0.1)), float(e.quantile(0.9)))
    return out


def _print_ensemble(df, qf, fc, r, asof):
    """主預測：組合模型（README §12）。"""
    ens = en.EnsembleForecaster().fit(df, qf, asof, old=fc)
    rows = ens.panel[(ens.panel["ticker"] == r["ticker"]) & (ens.panel["month"] == r["month"])]
    e = ens.predict(rows).iloc[0]
    band = en.bands(asof)
    st = en.horizon_stats()
    out = []
    for h in HORIZONS:
        lp = e[f"ens_{h}"]
        pe_h = np.exp(lp) if np.isfinite(lp) else np.nan
        o = {"幾個月後": h, "組合預測PE": _pe(pe_h),
             "80%區間": f"{pe_h * np.exp(band[h][0]):.1f}–{pe_h * np.exp(band[h][1]):.1f}" if h in band and np.isfinite(pe_h) else "—",
             "相對今天": f"{pe_h / r['pe'] - 1:+.0%}" if np.isfinite(pe_h) and r["pe"] > 0 else "—"}
        for m, nm in (("old", "盈餘模型"), ("huber", "線性"), ("gbm", "樹-盈餘"), ("gbm_z", "樹-變化")):
            v = e.get(f"{m}_{h}", np.nan)
            o[nm] = _pe(np.exp(v)) if np.isfinite(v) else ("—" if m == "old" and h not in en.OLD_H else "虧/>500")
        if st is not None and h in st.index:
            s = st.loc[h]
            o["回測誤差：組合/不變"] = f"±{np.exp(s['組合_誤差']) - 1:.0%} / ±{np.exp(s['隨機漫步_誤差']) - 1:.0%}"
            o["方向命中"] = f"{s['方向命中']:.0%}"
        out.append(o)
    print("【主預測】組合模型：四個預測器等權平均（盈餘模型 3/9/18 月沒有 → 三個平均）")
    print(pd.DataFrame(out).to_string(index=False))
    print("  回測誤差＝2015–2026 走動式樣本外的中位 |ln 誤差|，換成 ±%；「不變」＝直接拿今天的本益比當預測。")
    print("  有效性（README §12）：3 個月幾乎贏不了「本益比不變」；9–12 個月是誤差與改善幅度的最佳平衡；")
    print("  24–36 個月相對改善最大，但絕對誤差也最大（±34–36%）。\n")


def cmd_predict(a):
    df, qf = panel()
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
    if not a.no_ensemble:
        _print_ensemble(df, qf, fc, r, asof)
        if ov or a.mu is not None:
            print("  （情境覆寫與 --mu 只作用在下面的盈餘拆解表；組合模型用的是模型自己的預測。）\n")
    print("【盈餘拆解】兩階段盈餘模型：營收 × 淨利率 → 未來盈餘，再配上報酬假設")
    band = _error_quantiles(df, asof) if a.mu is None and not ov else {}
    rows = []
    for h in H_ALL:
        pe_main = np.exp(p[f"lnpe_hat_{h}"]) if p[f"ni_hat_{h}"] > 0 else np.nan
        rows.append({"幾個月後": h,
                     "預測營收TTM $B": p[f"rev_hat_{h}"] / 1e9,
                     "預測淨利率": f"{p[f'm_hat_{h}']:.1%}",
                     "預測淨利TTM $B": p[f"ni_hat_{h}"] / 1e9,
                     "盈餘變化": f"{p[f'ni_hat_{h}']/r['ni_ttm']-1:+.0%}" if r["ni_ttm"] > 0 else "—",
                     "預測PE（主）": "虧損" if p[f"ni_hat_{h}"] <= 0 else _pe(np.exp(p[f"lnpe_hat_{h}"])),
                     "若股價不動": "虧損" if p[f"ni_hat_{h}"] <= 0 else _pe(np.exp(p[f"lnpe_flat_{h}"])),
                     "若照過去10年報酬": "虧損" if p[f"ni_hat_{h}"] <= 0 else _pe(np.exp(p[f"lnpe_hist_{h}"])),
                     "80%區間": (f"{pe_main * np.exp(band[h][0]):.1f}–{pe_main * np.exp(band[h][1]):.1f}"
                                if h in band and np.isfinite(pe_main) else "—")})
        if a.target_pe and p[f"ni_hat_{h}"] > 0:
            need = (np.log(a.target_pe) + np.log(p[f"ni_hat_{h}"]) - np.log(r["mc"])) * 12 / h
            rows[-1][f"要到本益比{a.target_pe:g}需要的年報酬"] = f"{np.exp(need) - 1:+.0%}"
    print(pd.DataFrame(rows).round(2).to_string(index=False))
    if band:
        print("\n  80% 區間：回測裡同一預測距離、當時以前已揭曉的模型誤差 10%–90% 分位數（走動式實測涵蓋率 79–83%，README §11）。")
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
    print("\nln PE 中位絕對誤差（全期；越小越好）\n", main.round(4).to_string())
    print(f"\n已寫入 {RES}/")


def cmd_history(a):
    h = a.h
    df, _ = panel()
    d = attach_future(df, h)
    d = d[d["ticker"] == a.ticker][["ticker", "month", "ln_pe", "ep", f"ln_pe_f{h}", f"ep_f{h}"]]
    have = False
    lab_path = os.path.join(RES, "lab_predictions.csv.gz")
    if os.path.exists(lab_path):
        lp = pd.read_csv(lab_path, parse_dates=["month"])
        d = d.merge(lp[(lp["h"] == h) & (lp["ticker"] == a.ticker)][["month", "ens"]], on="month", how="left")
        have = True
    old_path = os.path.join(RES, "predictions.csv.gz")
    if h in H_ALL and os.path.exists(old_path):
        pred = pd.read_csv(old_path, parse_dates=["month"])
        d = d.merge(pred[pred["ticker"] == a.ticker][["month", f"lnpe_hat_{h}", f"ni_hat_{h}"]], on="month", how="left")
        have = True
    if not have:
        sys.exit("先跑 python3 pe_forecast.py backtest 與 python3 lab_run.py")
    d["預測於"] = d["month"].dt.strftime("%Y-%m")
    d["目標月"] = (d["month"] + pd.DateOffset(months=h)).dt.strftime("%Y-%m")
    d["當時PE"] = np.where(d["ep"] <= 0, "虧損", np.exp(d["ln_pe"]).map(_pe))
    cols = ["預測於", "目標月", "當時PE"]
    if "ens" in d:
        d["組合預測PE"] = np.exp(d["ens"]).map(_pe)
        cols.append("組合預測PE")
    if f"lnpe_hat_{h}" in d:
        d["盈餘模型PE"] = np.where(d[f"ni_hat_{h}"] <= 0, "虧損", np.exp(d[f"lnpe_hat_{h}"]).map(_pe))
        cols.append("盈餘模型PE")
    d["實際PE"] = np.where(d[f"ep_f{h}"].isna(), "（未到）", np.where(d[f"ep_f{h}"] <= 0, "虧損", np.exp(d[f"ln_pe_f{h}"]).map(_pe)))
    cols.append("實際PE")
    d = d[d["month"].dt.month.isin([3, 6, 9, 12]) & (d["month"] >= "2015-01-01")]
    print(d[cols].to_string(index=False))


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
    p.add_argument("--target-pe", type=float, help="反推：要在各預測距離達到這個本益比，每年需要多少報酬")
    p.add_argument("--no-ensemble", action="store_true", help="不跑組合模型（快；只看盈餘拆解）")
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
    p.add_argument("--h", type=int, default=12, choices=HORIZONS)
    p.set_defaults(fn=cmd_history)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
