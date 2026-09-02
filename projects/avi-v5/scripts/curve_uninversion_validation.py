#!/usr/bin/env python3
"""
curve_uninversion_validation.py — 殖利率曲線「解除倒掛」訊號的完整回測

⚠️ 這支腳本需要 FRED 存取，**只能在 GitHub Actions 上跑**
   （Claude 雲端容器的網路政策擋掉 fred.stlouisfed.org）。
   本機執行會直接跳出提示並退出。

背景：2026-08 把 AVI 的 macro 維度裡 `yield_spread_10y2y`（T10Y2Y 水位百分位 +
up_is_risk）改成 `yield_curve_uninversion`（曾倒掛 + 正在快速變陡）。

改版理由：
  - 原設定效果等於「曲線越陡越危險」，會把 2010-2014 健康復甦期的陡峭曲線
    打成滿分風險，與註解宣稱的「倒掛=麻煩」完全相反
  - 但單純把方向翻成 up_is_safe 也是錯的：實證上倒掛後股市平均還會漲
    13-17 個月（到見頂約 +19%），2022-10 至 2024-12 史上最長倒掛更是無衰退
  - 「水位」這個形式本身就不對；真正貼近崩盤的是**解除倒掛的轉折**
    （Fed 開始降息通常代表有東西壞了）

上線前的初步驗證（SPY 1993-2026，4 次解除倒掛：2001/2007/2019/2024）：
    解除倒掛後 12 個月平均報酬 +3.5%（全樣本基準 +11.8%）
    期間平均最大回撤 -24.8%（全樣本基準 -14.4%）—— 4/4 成立
樣本數只有 4，所以需要這支腳本用完整 FRED 資料（1976-）做正式回測。

用法（在 Actions 內，需 FRED_API_KEY）：
    python scripts/curve_uninversion_validation.py
"""
import os
import sys

import numpy as np
import pandas as pd

FRED_KEY = os.environ.get("FRED_API_KEY", "")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(BASE, "data", "ext")

LOOKBACK_M = 24   # 「近期曾倒掛」的回看月數（與 fred.py 的預設一致）
STEEPEN_M = 6     # 陡化幅度的計算窗口


def build_signal(spread: pd.Series,
                 lookback: int = LOOKBACK_M,
                 steepen: int = STEEPEN_M) -> pd.Series:
    """與 src/data/sources/fred.py:fetch_curve_uninversion 完全相同的邏輯。"""
    was_inverted = spread.rolling(lookback, min_periods=6).min() < 0
    steepening = spread - spread.shift(steepen)
    return steepening.where(was_inverted, 0.0).clip(lower=0.0).dropna()


def load_spy_monthly() -> pd.Series:
    """SPY 月末價（合併 data/backtest 與 data/ext）。"""
    parts = []
    for sub in ("backtest", "ext"):
        p = os.path.join(BASE, "data", sub, "SPY.csv")
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()
        col = "Adj Close" if "Adj Close" in df.columns else "Close"
        parts.append(df[col].dropna())
    if not parts:
        raise FileNotFoundError("SPY not found")
    s = pd.concat(parts)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.resample("ME").last().dropna()


def main() -> int:
    if not FRED_KEY:
        print("需要 FRED_API_KEY —— 本腳本只能在 GitHub Actions 上執行。")
        print("（Claude 雲端容器的網路政策擋掉 fred.stlouisfed.org）")
        return 0
    try:
        from fredapi import Fred
    except ImportError:
        print("fredapi 未安裝")
        return 0

    fred = Fred(api_key=FRED_KEY)
    spread = fred.get_series("T10Y2Y").dropna()
    spread = spread.resample("ME").last().dropna()
    print(f"T10Y2Y：{spread.index[0].date()} → {spread.index[-1].date()}"
          f"（{len(spread)} 個月）")

    sig = build_signal(spread)
    spy = load_spy_monthly()
    common = sig.index.intersection(spy.index)
    print(f"與 SPY 重疊可測區間：{common[0].date()} → {common[-1].date()}"
          f"（{len(common)} 個月）\n")

    # ── 未來 N 個月的報酬與最大回撤 ──
    def fwd(months: int):
        ret, mdd = {}, {}
        for d in common:
            loc = spy.index.get_loc(d)
            w = spy.iloc[loc:loc + months + 1]
            if len(w) < months:
                continue
            ret[d] = (w.iloc[-1] / w.iloc[0] - 1) * 100
            mdd[d] = ((w / w.cummax() - 1).min()) * 100
        return pd.Series(ret), pd.Series(mdd)

    print("=" * 78)
    print("  訊號亮燈 vs 未亮燈：未來報酬與最大回撤的差異")
    print("=" * 78)
    s = sig.loc[common]
    armed = s > 0
    print(f"  訊號亮燈的月份：{int(armed.sum())}/{len(s)} "
          f"({armed.mean()*100:.0f}%)\n")
    print(f"  {'視野':<10}{'亮燈:報酬':>12}{'未亮:報酬':>12}"
          f"{'亮燈:回撤':>12}{'未亮:回撤':>12}")
    print("  " + "-" * 58)
    for m in (6, 12, 24):
        r, dd = fwd(m)
        idx = r.index.intersection(s.index)
        a = armed.reindex(idx).fillna(False).values
        if a.sum() < 6 or (~a).sum() < 6:
            print(f"  {str(m)+'個月':<10}   樣本不足")
            continue
        print(f"  {str(m)+'個月':<10}{r[idx][a].mean():>11.1f}%"
              f"{r[idx][~a].mean():>11.1f}%"
              f"{dd[idx][a].mean():>11.1f}%{dd[idx][~a].mean():>11.1f}%")

    # ── 與原本的「水位」形式對照 ──
    print("\n" + "=" * 78)
    print("  與原設計（T10Y2Y 水位）對照：誰更能區分未來 12 個月的大回撤？")
    print("=" * 78)
    r12, dd12 = fwd(12)
    idx = dd12.index.intersection(s.index)
    label = (dd12[idx] <= -15).astype(int)   # 未來 12 個月回撤超過 15%

    def auc(x, y):
        x, y = np.asarray(x, float), np.asarray(y, int)
        ok = ~np.isnan(x)
        x, y = x[ok], y[ok]
        npos, nneg = y.sum(), len(y) - y.sum()
        if npos == 0 or nneg == 0:
            return np.nan
        order = np.argsort(x, kind="mergesort")
        ranks = np.empty(len(x), float)
        xs = x[order]
        i = 0
        while i < len(xs):
            j = i
            while j + 1 < len(xs) and xs[j + 1] == xs[i]:
                j += 1
            ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
            i = j + 1
        return (ranks[y == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg)

    print(f"  事件定義：未來 12 個月最大回撤 ≤ -15%"
          f"（基準率 {label.mean()*100:.0f}%）\n")
    print(f"  {'訊號形式':<34}{'AUC':>8}   判定")
    print("  " + "-" * 54)
    cands = {
        "新版：解除倒掛（曾倒掛+變陡）": s.loc[idx],
        "舊版：T10Y2Y 水位（up_is_risk）": spread.loc[idx],
        "舊版翻方向：−T10Y2Y（倒掛=風險）": -spread.loc[idx],
    }
    for nm, x in cands.items():
        a = auc(x.values, label.values)
        v = ("⭐ 有效" if a >= 0.60 else "✅ 尚可" if a >= 0.55
             else "🟡 微弱" if a >= 0.52 else "❌ 無效")
        print(f"  {nm:<34}{a:>8.3f}   {v}")

    # ── 逐次解除倒掛事件 ──
    print("\n" + "=" * 78)
    print("  逐次「解除倒掛」事件（spread 由負轉正的月份）")
    print("=" * 78)
    turned = (spread > 0) & (spread.shift(1) <= 0)
    evs = [d for d in spread.index[turned] if d in spy.index]
    print(f"  {'解除倒掛':<14}{'+6月':>9}{'+12月':>9}{'12月內最大回撤':>16}")
    print("  " + "-" * 50)
    rows = []
    for d in evs:
        loc = spy.index.get_loc(d)
        w6, w12 = spy.iloc[loc:loc + 7], spy.iloc[loc:loc + 13]
        if len(w12) < 12:
            continue
        r6 = (w6.iloc[-1] / w6.iloc[0] - 1) * 100
        r12 = (w12.iloc[-1] / w12.iloc[0] - 1) * 100
        md = ((w12 / w12.cummax() - 1).min()) * 100
        rows.append((r12, md))
        print(f"  {str(d.date()):<14}{r6:>8.1f}%{r12:>8.1f}%{md:>15.1f}%")
    if rows:
        print("  " + "-" * 50)
        print(f"  平均            {'':>9}{np.mean([r[0] for r in rows]):>8.1f}%"
              f"{np.mean([r[1] for r in rows]):>15.1f}%")
        allr = [((spy.iloc[i + 12] / spy.iloc[i]) - 1) * 100
                for i in range(len(spy) - 13)]
        alld = [((spy.iloc[i:i + 13] / spy.iloc[i:i + 13].cummax() - 1).min()) * 100
                for i in range(len(spy) - 13)]
        print(f"  全樣本基準      {'':>9}{np.mean(allr):>8.1f}%{np.mean(alld):>15.1f}%")

    print("\n若新版 AUC 明顯優於兩種舊版，代表改版有實證支持；"
          "若三者接近，應考慮甲案（直接移除這 4% 權重）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
