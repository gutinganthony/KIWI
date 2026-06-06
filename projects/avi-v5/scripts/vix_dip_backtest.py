#!/usr/bin/env python3
"""
VIX 抄底回測 — VIX 突破 30 / 35 / 40 後買進 S&P 500 的勝率與平均報酬
================================================================

用法（在 projects/avi-v5/ 目錄下）：
  python scripts/vix_dip_backtest.py
  python scripts/vix_dip_backtest.py --start 1990-01-01 --thresholds 30 35 40 --gap 21
  python scripts/vix_dip_backtest.py --benchmark SOXX   # 換成半導體 ETF 看高 beta 版本

資料來源：yfinance 抓 ^VIX（1990 起）+ ^GSPC（或自訂 --benchmark）。
  ⚠️ 需要對外網路。雲端容器若封鎖 yfinance 會抓不到；請在 Mac 本機跑。

方法論（刻意保守、可重現）：
  事件定義 = VIX 收盤「由下向上」首次穿越門檻 T，且距離上一個已採計的同門檻事件 >= gap
            交易日（去叢集 de-clustering，避免把 2008/2020 一段連續高 VIX 算成數十次）。
  對每個事件日 t，計算基準指數在 +21 / 63 / 126 / 252 交易日後的「之後報酬」。
  另計「訊號後最大續跌」= 事件後 252 日內指數相對事件日的最低點（量化『你可能買太早』的幅度）。

輸出：每個門檻 × 每個持有期 → 樣本數 / 勝率(% 正報酬) / 平均 / 中位數 / 最差 / 最佳，
      以及訊號後平均與最差續跌，最後列出所有事件日。

注意：這是「無條件抄底」的純訊號回測，不含分批、不含停損、不含其他 ACT 指標確認。
      實務上應疊加 TSI 回落 / 廣度推力 / 200DMA 確認 + 分批（見 KIWI 加碼劇本）。
"""

import argparse
import sys
import warnings

warnings.filterwarnings("ignore")

try:
    import numpy as np
    import pandas as pd
    import yfinance as yf
except ImportError as e:
    sys.exit(f"缺套件：{e}. 請先 pip install pandas numpy yfinance")


HORIZONS = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}


def fetch_close(ticker: str, start: str) -> pd.Series:
    df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
    if df is None or df.empty:
        sys.exit(f"抓不到 {ticker}（網路被擋或代碼錯誤）。本機 Mac 重試。")
    if isinstance(df.columns, pd.MultiIndex):
        col = ("Close", ticker) if ("Close", ticker) in df.columns else df.columns[0]
        s = df[col]
    else:
        s = df["Close"]
    return s.dropna()


def find_events(vix: pd.Series, threshold: float, gap: int) -> pd.DatetimeIndex:
    """VIX 由下向上穿越 threshold，去叢集（相鄰事件至少間隔 gap 交易日）。"""
    above = vix >= threshold
    upcross = above & (~above.shift(1).fillna(False))
    candidates = list(vix.index[upcross])
    kept = []
    last_pos = None
    pos = {d: i for i, d in enumerate(vix.index)}
    for d in candidates:
        if last_pos is None or (pos[d] - last_pos) >= gap:
            kept.append(d)
            last_pos = pos[d]
    return pd.DatetimeIndex(kept)


def forward_stats(spx: pd.Series, events: pd.DatetimeIndex):
    idx = spx.index
    pos = {d: i for i, d in enumerate(idx)}
    rows = []
    for d in events:
        if d not in pos:
            # 對齊到下一個交易日
            later = idx[idx >= d]
            if len(later) == 0:
                continue
            d = later[0]
        i = pos[d]
        row = {"date": d.date(), "vix_day_close": None}
        # 各持有期之後報酬
        for name, h in HORIZONS.items():
            j = i + h
            row[name] = (spx.iloc[j] / spx.iloc[i] - 1.0) if j < len(spx) else np.nan
        # 訊號後 252 日內最大續跌
        j_end = min(i + 252, len(spx) - 1)
        if j_end > i:
            row["max_drawdown_after"] = spx.iloc[i:j_end + 1].min() / spx.iloc[i] - 1.0
        else:
            row["max_drawdown_after"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame, threshold: float, benchmark: str):
    print(f"\n{'='*72}")
    print(f"  VIX 突破 {threshold:.0f} 後買進 {benchmark} — 事件數：{len(df)}")
    print(f"{'='*72}")
    print(f"  {'持有期':<6}{'樣本':>5}{'勝率':>9}{'平均':>10}{'中位':>10}{'最差':>10}{'最佳':>10}")
    print(f"  {'-'*58}")
    for name in HORIZONS:
        col = df[name].dropna()
        if len(col) == 0:
            continue
        win = (col > 0).mean() * 100
        print(f"  {name:<6}{len(col):>5}{win:>8.0f}%{col.mean()*100:>9.1f}%"
              f"{col.median()*100:>9.1f}%{col.min()*100:>9.1f}%{col.max()*100:>9.1f}%")
    dd = df["max_drawdown_after"].dropna()
    if len(dd):
        print(f"  {'-'*58}")
        print(f"  訊號後 12 個月內續跌：平均 {dd.mean()*100:.1f}%、最差 {dd.min()*100:.1f}%"
              f"（衡量『買太早』的痛）")
    print(f"  事件日：{', '.join(str(d) for d in df['date'])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="1990-01-01")
    ap.add_argument("--thresholds", type=float, nargs="+", default=[30, 35, 40])
    ap.add_argument("--gap", type=int, default=21, help="去叢集間隔（交易日），預設 21≈1 個月")
    ap.add_argument("--benchmark", default="^GSPC", help="抄底標的，預設 S&P500；可換 SOXX/QQQ")
    args = ap.parse_args()

    print(f"抓資料：^VIX + {args.benchmark}（{args.start} 起）…")
    vix = fetch_close("^VIX", args.start)
    spx = fetch_close(args.benchmark, args.start)
    common = vix.index.intersection(spx.index)
    vix, spx = vix.loc[common], spx.loc[common]
    print(f"資料區間：{common.min().date()} ~ {common.max().date()}（{len(common)} 交易日）")

    for t in args.thresholds:
        events = find_events(vix, t, args.gap)
        df = forward_stats(spx, events)
        if len(df) == 0:
            print(f"\nVIX>{t:.0f}：區間內無事件。")
            continue
        summarize(df, t, args.benchmark)

    print("\n註：純訊號回測，未含分批/停損/其他 ACT 確認。實務請疊加 TSI 回落 + 廣度 + 200DMA + 分批。")


if __name__ == "__main__":
    main()
