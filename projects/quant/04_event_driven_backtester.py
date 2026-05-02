"""
Project 4: Event-Driven Backtester (Earnings / Macro)
=====================================================
對真實事件 (Fed 決議、CPI、財報) 做事件研究，分析事件前後的報酬分布。

使用方式:
    pip install -r requirements.txt
    python 04_event_driven_backtester.py

輸出:
    - event_study_results.png (事件效應圖表)
    - 終端機顯示事件統計
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")


# 2023-2024 FOMC 決議日 (重大事件範例)
FOMC_DATES = [
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14",
    "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
    "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
]

# 2023-2024 CPI 發布日
CPI_DATES = [
    "2023-01-12", "2023-02-14", "2023-03-14", "2023-04-12",
    "2023-05-10", "2023-06-13", "2023-07-12", "2023-08-10",
    "2023-09-13", "2023-10-12", "2023-11-14", "2023-12-12",
    "2024-01-11", "2024-02-13", "2024-03-12", "2024-04-10",
    "2024-05-15", "2024-06-12", "2024-07-11", "2024-08-14",
    "2024-09-11", "2024-10-10", "2024-11-13", "2024-12-11",
]

# NFP (Non-Farm Payroll) 發布日
NFP_DATES = [
    "2023-01-06", "2023-02-03", "2023-03-10", "2023-04-07",
    "2023-05-05", "2023-06-02", "2023-07-07", "2023-08-04",
    "2023-09-01", "2023-10-06", "2023-11-03", "2023-12-08",
    "2024-01-05", "2024-02-02", "2024-03-08", "2024-04-05",
    "2024-05-03", "2024-06-07", "2024-07-05", "2024-08-02",
    "2024-09-06", "2024-10-04", "2024-11-01", "2024-12-06",
]


def fetch_data(ticker: str = "SPY", period: str = "3y") -> pd.DataFrame:
    """拉取市場資料"""
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    df = df[["Close"]].copy()
    df.columns = ["close"]
    df["returns"] = df["close"].pct_change()
    return df


def run_event_study(
    df: pd.DataFrame,
    event_dates: list,
    window_before: int = 5,
    window_after: int = 5,
) -> pd.DataFrame:
    """
    對每個事件計算事件窗口內的報酬

    回傳: DataFrame with columns [-window_before, ..., 0, ..., window_after]
    """
    df_indexed = df.copy()
    trading_dates = df_indexed.index

    results = []

    for event_date_str in event_dates:
        event_date = pd.Timestamp(event_date_str)

        # 找最近的交易日
        if event_date not in trading_dates:
            mask = trading_dates >= event_date
            if mask.any():
                event_date = trading_dates[mask][0]
            else:
                continue

        event_idx = trading_dates.get_loc(event_date)

        start_idx = event_idx - window_before
        end_idx = event_idx + window_after

        if start_idx < 0 or end_idx >= len(trading_dates):
            continue

        # 取事件窗口的報酬
        window_returns = df_indexed["returns"].iloc[start_idx:end_idx + 1].values

        if len(window_returns) == window_before + window_after + 1:
            results.append(window_returns)

    if not results:
        return pd.DataFrame()

    columns = list(range(-window_before, window_after + 1))
    return pd.DataFrame(results, columns=columns)


def compute_event_stats(event_returns: pd.DataFrame) -> dict:
    """計算事件效應的統計指標"""
    if event_returns.empty:
        return {}

    # 事件當日 (t=0) 的統計
    day0 = event_returns[0]
    # 事件後 1-5 天累計報酬
    post_event = event_returns[[1, 2, 3, 4, 5]].sum(axis=1) if 5 in event_returns.columns else event_returns[[1, 2, 3]].sum(axis=1)

    stats = {
        "n_events": len(event_returns),
        "day0_mean": day0.mean(),
        "day0_std": day0.std(),
        "day0_hit_rate": (day0 > 0).mean(),
        "day0_median": day0.median(),
        "post5d_mean": post_event.mean(),
        "post5d_std": post_event.std(),
        "post5d_hit_rate": (post_event > 0).mean(),
        "post5d_worst": post_event.min(),
        "post5d_best": post_event.max(),
    }
    return stats


def print_event_stats(stats_dict: dict):
    """印出所有事件類型的統計"""
    print(f"\n{'='*75}")
    print(f"  Event Study Results")
    print(f"{'='*75}")

    print(f"\n  {'Event Type':<12} {'N':>4} {'Day0 Mean':>10} {'Day0 Hit%':>10} "
          f"{'Post-5d Mean':>13} {'Post-5d Hit%':>13} {'Worst':>8}")
    print(f"  {'-'*12} {'-'*4} {'-'*10} {'-'*10} {'-'*13} {'-'*13} {'-'*8}")

    for event_name, stats in stats_dict.items():
        if not stats:
            continue
        print(
            f"  {event_name:<12} {stats['n_events']:>4} "
            f"{stats['day0_mean']:>10.3%} {stats['day0_hit_rate']:>10.1%} "
            f"{stats['post5d_mean']:>13.3%} {stats['post5d_hit_rate']:>13.1%} "
            f"{stats['post5d_worst']:>8.2%}"
        )


def plot_event_study(all_event_returns: dict, ticker: str):
    """視覺化事件效應"""
    n_events = len(all_event_returns)
    fig, axes = plt.subplots(n_events, 2, figsize=(14, 4 * n_events))
    fig.suptitle(f"Event Study — {ticker}", fontsize=14, fontweight="bold")

    if n_events == 1:
        axes = axes.reshape(1, -1)

    colors = {"FOMC": "#e74c3c", "CPI": "#3498db", "NFP": "#2ecc71"}

    for idx, (event_name, event_df) in enumerate(all_event_returns.items()):
        if event_df.empty:
            continue

        color = colors.get(event_name, "#34495e")

        # 左圖: 平均累計報酬 (event window)
        ax = axes[idx, 0]
        cum_returns = event_df.cumsum(axis=1)
        mean_cum = cum_returns.mean()
        std_cum = cum_returns.std()

        ax.plot(mean_cum.index, mean_cum.values * 100, color=color, linewidth=2, label="Mean")
        ax.fill_between(
            mean_cum.index,
            (mean_cum - std_cum).values * 100,
            (mean_cum + std_cum).values * 100,
            alpha=0.2, color=color
        )
        ax.axvline(0, color="gray", linestyle="--", alpha=0.7)
        ax.axhline(0, color="gray", linestyle="-", alpha=0.3)
        ax.set_xlabel("Days relative to event")
        ax.set_ylabel("Cumulative Return (%)")
        ax.set_title(f"{event_name}: Average Cumulative Return (N={len(event_df)})")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 右圖: 事件後 1-5 天報酬分布
        ax = axes[idx, 1]
        if 5 in event_df.columns:
            post_returns = event_df[[1, 2, 3, 4, 5]].sum(axis=1) * 100
        else:
            post_returns = event_df[[1, 2, 3]].sum(axis=1) * 100

        ax.hist(post_returns, bins=20, color=color, alpha=0.6, edgecolor="white")
        ax.axvline(post_returns.mean(), color=color, linestyle="--", linewidth=2, label=f"Mean: {post_returns.mean():.2f}%")
        ax.axvline(0, color="gray", linestyle="-", alpha=0.5)
        ax.set_xlabel("Post-event 5-day Return (%)")
        ax.set_ylabel("Count")
        ax.set_title(f"{event_name}: Post-Event Return Distribution")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("event_study_results.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n[OK] 圖表已存: event_study_results.png")


def main():
    ticker = "SPY"
    print(f"[1/4] 下載 {ticker} 資料...")
    df = fetch_data(ticker, period="3y")
    print(f"      期間: {df.index[0].date()} — {df.index[-1].date()}")

    print("[2/4] 執行事件研究...")
    events = {
        "FOMC": FOMC_DATES,
        "CPI": CPI_DATES,
        "NFP": NFP_DATES,
    }

    all_event_returns = {}
    all_stats = {}

    for event_name, dates in events.items():
        event_returns = run_event_study(df, dates, window_before=5, window_after=5)
        all_event_returns[event_name] = event_returns
        all_stats[event_name] = compute_event_stats(event_returns)
        print(f"      {event_name}: {len(event_returns)} events analyzed")

    print("[3/4] 統計結果...")
    print_event_stats(all_stats)

    # 額外分析: 事件日 vs 非事件日的波動率比較
    all_event_dates = set()
    for dates in events.values():
        all_event_dates.update(pd.Timestamp(d) for d in dates)

    event_day_vol = df[df.index.isin(all_event_dates)]["returns"].std() * np.sqrt(252)
    non_event_vol = df[~df.index.isin(all_event_dates)]["returns"].std() * np.sqrt(252)

    print(f"\n  事件日年化波動率:     {event_day_vol:.2%}")
    print(f"  非事件日年化波動率:   {non_event_vol:.2%}")
    print(f"  波動率倍數:           {event_day_vol/non_event_vol:.2f}x")

    print("\n[4/4] 繪製圖表...")
    plot_event_study(all_event_returns, ticker)

    print(f"\n{'='*75}")
    print("  完成! 你學到了:")
    print("  1. 事件研究 (event study) 的標準方法論")
    print("  2. 條件報酬分析: 在特定事件下市場的行為模式")
    print("  3. Hit rate + distribution 比 mean 更重要")
    print("  4. 事件日波動率通常高於非事件日 (risk premium)")
    print("")
    print("  下一步:")
    print("  - 加入更多事件 (地緣政治、選舉、大型 IPO)")
    print("  - 用 Project 1 的 regime label 做條件分析")
    print("  - 加入事件前的 positioning 策略")
    print(f"{'='*75}")


if __name__ == "__main__":
    main()
