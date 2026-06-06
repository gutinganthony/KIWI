#!/usr/bin/env python3
"""
VIX 抄底回測 — VIX 突破 30 / 35 / 40 後買進 S&P 500 的勝率與平均報酬
（可疊加 200 日均線「牛熊指標」regime 過濾）
====================================================================

用法（在 projects/avi-v5/ 目錄下）：
  python scripts/vix_dip_backtest.py                       # 真實資料（需網路；Mac 本機）
  python scripts/vix_dip_backtest.py --benchmark SOXX      # 半導體高 beta 版
  python scripts/vix_dip_backtest.py --no-regime           # 關掉牛熊拆分，只看無條件抄底
  python scripts/vix_dip_backtest.py --synthetic           # 離線自我驗證（不需網路，固定預期答案）

資料來源：yfinance 抓 ^VIX（1990 起）+ ^GSPC（或 --benchmark）。
  ⚠️ 需要對外網路。雲端容器封鎖 yfinance 時用 --synthetic 驗證邏輯，真實數字請在 Mac 跑。

方法論（刻意保守、可重現）：
  事件 = VIX 收盤「由下向上」首次穿越門檻 T，且距上一個採計事件 >= gap 交易日（去叢集）。
  牛熊 regime（--regime，預設開）= 事件當日基準指數是否 >= 自身 200 日均線：
        >= 200DMA → 多頭(BULL)；< 200DMA → 空頭(BEAR)。
  對每事件計算基準在 +21/63/126/252 交易日後「之後報酬」，並算「訊號後 252 日內最大續跌」。

輸出：每門檻先看 ALL（不分牛熊），再拆 BULL / BEAR，比較勝率、平均報酬、買太早的續跌。

註：純訊號回測，不含分批/停損。實務應疊加 TSI 回落 + 廣度推力 + VIX 收回 10 日線 + 分批。
"""

import argparse
import sys
import warnings

warnings.filterwarnings("ignore")

try:
    import numpy as np
    import pandas as pd
except ImportError as e:
    sys.exit(f"缺套件：{e}. 請先 pip install pandas numpy yfinance")

HORIZONS = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}


# ── 資料 ──────────────────────────────────────────────────────────────────────
def fetch_close(ticker: str, start: str) -> pd.Series:
    import yfinance as yf
    df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
    if df is None or df.empty:
        sys.exit(f"抓不到 {ticker}（網路被擋或代碼錯誤）。本機 Mac 重試，或用 --synthetic。")
    if isinstance(df.columns, pd.MultiIndex):
        col = ("Close", ticker) if ("Close", ticker) in df.columns else df.columns[0]
        s = df[col]
    else:
        s = df["Close"]
    return s.dropna()


def synthetic_data():
    """離線固定資料：多頭段(漲) + 空頭段(跌)，各放一根 VIX=36 的尖刺。
    預期：VIX>30/35 各 2 事件 → BULL 1 筆(全正)、BEAR 1 筆(全負)；VIX>40 → 0 事件。
    這讓『牛熊拆分 + 勝率計算』可在無網路下被觀察驗證。"""
    n = 1200
    dates = pd.bdate_range("2015-01-01", periods=n)
    price = np.empty(n)
    price[:601] = np.linspace(100, 200, 601)          # day 0..600 多頭上升
    price[600:] = np.linspace(200, 120, n - 600)       # day 600..1199 空頭下降
    spx = pd.Series(price, index=dates)
    vix = pd.Series(15.0, index=dates)
    vix.iloc[350] = 36.0   # 多頭段尖刺
    vix.iloc[750] = 36.0   # 空頭段尖刺
    return vix, spx


# ── 事件偵測 + regime ─────────────────────────────────────────────────────────
def find_events(vix: pd.Series, threshold: float, gap: int) -> list:
    above = vix >= threshold
    upcross = above & (~above.shift(1).fillna(False))
    candidates = list(vix.index[upcross])
    pos = {d: i for i, d in enumerate(vix.index)}
    kept, last = [], None
    for d in candidates:
        if last is None or (pos[d] - last) >= gap:
            kept.append(d)
            last = pos[d]
    return kept


def forward_stats(spx: pd.Series, events: list, use_regime: bool) -> pd.DataFrame:
    idx = spx.index
    pos = {d: i for i, d in enumerate(idx)}
    sma200 = spx.rolling(200).mean() if use_regime else None
    rows = []
    for d in events:
        if d not in pos:
            later = idx[idx >= d]
            if len(later) == 0:
                continue
            d = later[0]
        i = pos[d]
        regime = "ALL"
        if use_regime:
            m = sma200.iloc[i]
            regime = "BULL" if (pd.notna(m) and spx.iloc[i] >= m) else \
                     ("BEAR" if pd.notna(m) else "N/A")
        row = {"date": d.date(), "regime": regime}
        for name, h in HORIZONS.items():
            j = i + h
            row[name] = (spx.iloc[j] / spx.iloc[i] - 1.0) if j < len(spx) else np.nan
        j_end = min(i + 252, len(spx) - 1)
        row["dd_after"] = (spx.iloc[i:j_end + 1].min() / spx.iloc[i] - 1.0) if j_end > i else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


# ── 輸出 ──────────────────────────────────────────────────────────────────────
def print_block(df: pd.DataFrame, label: str):
    if len(df) == 0:
        print(f"  [{label:<4}] 無事件")
        return
    print(f"  [{label:<4}] 事件數 {len(df)}　日期：{', '.join(str(d) for d in df['date'])}")
    print(f"  {'持有期':<6}{'勝率':>8}{'平均':>9}{'中位':>9}{'最差':>9}{'最佳':>9}")
    for name in HORIZONS:
        col = df[name].dropna()
        if len(col) == 0:
            continue
        win = (col > 0).mean() * 100
        print(f"  {name:<6}{win:>7.0f}%{col.mean()*100:>8.1f}%{col.median()*100:>8.1f}%"
              f"{col.min()*100:>8.1f}%{col.max()*100:>8.1f}%")
    dd = df["dd_after"].dropna()
    if len(dd):
        print(f"  訊號後續跌：平均 {dd.mean()*100:.1f}%、最差 {dd.min()*100:.1f}%（買太早的痛）")


def summarize(df: pd.DataFrame, threshold: float, benchmark: str, use_regime: bool):
    print(f"\n{'='*70}\n  VIX 突破 {threshold:.0f} 後買進 {benchmark}\n{'='*70}")
    print_block(df, "ALL")
    if use_regime and len(df):
        for reg in ("BULL", "BEAR"):
            print()
            print_block(df[df["regime"] == reg].reset_index(drop=True), reg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="1990-01-01")
    ap.add_argument("--thresholds", type=float, nargs="+", default=[30, 35, 40])
    ap.add_argument("--gap", type=int, default=21, help="去叢集間隔(交易日)，預設 21≈1月")
    ap.add_argument("--benchmark", default="^GSPC", help="抄底標的，預設 S&P500；可換 SOXX/QQQ")
    ap.add_argument("--no-regime", dest="regime", action="store_false", help="關掉牛熊拆分")
    ap.add_argument("--synthetic", action="store_true", help="離線固定資料自我驗證")
    args = ap.parse_args()

    if args.synthetic:
        print("== 離線驗證模式（synthetic）==")
        vix, spx = synthetic_data()
    else:
        print(f"抓資料：^VIX + {args.benchmark}（{args.start} 起）…")
        vix, spx = fetch_close("^VIX", args.start), fetch_close(args.benchmark, args.start)
        common = vix.index.intersection(spx.index)
        vix, spx = vix.loc[common], spx.loc[common]
    print(f"資料區間：{spx.index.min().date()} ~ {spx.index.max().date()}（{len(spx)} 交易日）"
          f"｜牛熊過濾：{'ON (200DMA)' if args.regime else 'OFF'}")

    for t in args.thresholds:
        df = forward_stats(spx, find_events(vix, t, args.gap), args.regime)
        summarize(df, t, args.benchmark, args.regime)

    print("\n註：純訊號回測，未含分批/停損/其他 ACT 確認。實務請疊加 TSI 回落 + 廣度 + 200DMA + 分批。")


if __name__ == "__main__":
    main()
