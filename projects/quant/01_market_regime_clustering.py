"""
Project 1: Market Regime Clustering (HMM / K-Means)
====================================================
用 Hidden Markov Model 和 K-Means 把市場切成不同狀態 (regime)。

使用方式:
    pip install -r requirements.txt
    python 01_market_regime_clustering.py

輸出:
    - regime_clustering_results.png (視覺化圖表)
    - 終端機顯示各 regime 的統計摘要
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from hmmlearn.hmm import GaussianHMM
import warnings

warnings.filterwarnings("ignore")


def fetch_data(ticker: str = "SPY", period: str = "10y") -> pd.DataFrame:
    """拉取市場資料"""
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    df = df[["Close"]].copy()
    df.columns = ["close"]
    return df


def engineer_features(df: pd.DataFrame, window: int = 21) -> pd.DataFrame:
    """時間序列特徵工程"""
    df = df.copy()

    # 日報酬
    df["returns"] = df["close"].pct_change()

    # 滾動報酬 (月)
    df["rolling_return"] = df["returns"].rolling(window).mean()

    # 已實現波動率 (年化)
    df["realized_vol"] = df["returns"].rolling(window).std() * np.sqrt(252)

    # 回撤
    rolling_max = df["close"].rolling(252, min_periods=1).max()
    df["drawdown"] = (df["close"] - rolling_max) / rolling_max

    # 滾動 Sharpe (簡化版, 無風險利率=0)
    df["rolling_sharpe"] = (
        df["returns"].rolling(window).mean()
        / df["returns"].rolling(window).std()
    ) * np.sqrt(252)

    df.dropna(inplace=True)
    return df


def fit_hmm(features: np.ndarray, n_regimes: int = 3) -> np.ndarray:
    """用 Gaussian HMM 偵測市場狀態"""
    model = GaussianHMM(
        n_components=n_regimes,
        covariance_type="full",
        n_iter=200,
        random_state=42,
    )
    model.fit(features)
    regimes = model.predict(features)
    return regimes


def fit_kmeans(features: np.ndarray, n_regimes: int = 3) -> np.ndarray:
    """用 K-Means 分群"""
    model = KMeans(n_clusters=n_regimes, random_state=42, n_init=10)
    regimes = model.fit_predict(features)
    return regimes


def print_regime_stats(df: pd.DataFrame, regime_col: str):
    """印出各 regime 的統計資訊"""
    print(f"\n{'='*60}")
    print(f"  Regime Statistics ({regime_col})")
    print(f"{'='*60}")

    for regime in sorted(df[regime_col].unique()):
        subset = df[df[regime_col] == regime]
        ann_return = subset["returns"].mean() * 252
        ann_vol = subset["returns"].std() * np.sqrt(252)
        sharpe = ann_return / ann_vol if ann_vol > 0 else 0
        max_dd = subset["drawdown"].min()
        pct_time = len(subset) / len(df) * 100

        print(f"\n  Regime {regime}:")
        print(f"    佔比:         {pct_time:.1f}% of time")
        print(f"    年化報酬:     {ann_return:.2%}")
        print(f"    年化波動率:   {ann_vol:.2%}")
        print(f"    Sharpe Ratio: {sharpe:.2f}")
        print(f"    最大回撤:     {max_dd:.2%}")


def plot_results(df: pd.DataFrame, ticker: str):
    """視覺化結果"""
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    fig.suptitle(f"Market Regime Clustering — {ticker}", fontsize=14, fontweight="bold")

    colors_hmm = {0: "#2ecc71", 1: "#f39c12", 2: "#e74c3c"}
    colors_kmeans = {0: "#3498db", 1: "#9b59b6", 2: "#e67e22"}

    # 1. 價格 + HMM regimes
    ax = axes[0]
    for regime in sorted(df["regime_hmm"].unique()):
        mask = df["regime_hmm"] == regime
        ax.scatter(
            df.index[mask], df["close"][mask],
            c=colors_hmm.get(regime, "#95a5a6"), s=2, alpha=0.7, label=f"Regime {regime}"
        )
    ax.set_ylabel("Price")
    ax.set_title("HMM Regimes")
    ax.legend(loc="upper left", markerscale=5)

    # 2. 價格 + K-Means regimes
    ax = axes[1]
    for regime in sorted(df["regime_kmeans"].unique()):
        mask = df["regime_kmeans"] == regime
        ax.scatter(
            df.index[mask], df["close"][mask],
            c=colors_kmeans.get(regime, "#95a5a6"), s=2, alpha=0.7, label=f"Regime {regime}"
        )
    ax.set_ylabel("Price")
    ax.set_title("K-Means Regimes")
    ax.legend(loc="upper left", markerscale=5)

    # 3. 已實現波動率
    ax = axes[2]
    ax.plot(df.index, df["realized_vol"], color="#34495e", linewidth=0.8)
    ax.axhline(df["realized_vol"].median(), color="#e74c3c", linestyle="--", alpha=0.5)
    ax.set_ylabel("Realized Vol (ann.)")
    ax.set_title("Realized Volatility")

    # 4. 回撤
    ax = axes[3]
    ax.fill_between(df.index, df["drawdown"], 0, color="#e74c3c", alpha=0.3)
    ax.plot(df.index, df["drawdown"], color="#c0392b", linewidth=0.8)
    ax.set_ylabel("Drawdown")
    ax.set_title("Drawdown from Peak")

    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("regime_clustering_results.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n[OK] 圖表已存: regime_clustering_results.png")


def main():
    ticker = "SPY"
    print(f"[1/4] 下載 {ticker} 資料...")
    df = fetch_data(ticker)

    print("[2/4] 特徵工程...")
    df = engineer_features(df)

    feature_cols = ["rolling_return", "realized_vol", "drawdown", "rolling_sharpe"]
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(df[feature_cols])

    print("[3/4] 擬合模型...")
    df["regime_hmm"] = fit_hmm(features_scaled, n_regimes=3)
    df["regime_kmeans"] = fit_kmeans(features_scaled, n_regimes=3)

    # 重新排列 regime 編號 (按年化報酬排序, 0=最差)
    for col in ["regime_hmm", "regime_kmeans"]:
        regime_returns = df.groupby(col)["returns"].mean()
        rank_map = {r: i for i, r in enumerate(regime_returns.sort_values().index)}
        df[col] = df[col].map(rank_map)

    print("[4/4] 輸出結果...")
    print_regime_stats(df, "regime_hmm")
    print_regime_stats(df, "regime_kmeans")
    plot_results(df, ticker)

    print(f"\n{'='*60}")
    print("  完成! 你現在可以:")
    print("  1. 觀察不同 regime 的報酬/波動率特徵")
    print("  2. 用 regime 當作策略的開/關信號")
    print("  3. 搭配 Project 3 (CVaR) 做動態配置")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
