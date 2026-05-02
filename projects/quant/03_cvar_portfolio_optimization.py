"""
Project 3: CVaR Portfolio Optimisation (Tail Risk)
==================================================
用 CVXPY 建立最小化 CVaR 的投資組合最佳化器。

使用方式:
    pip install -r requirements.txt
    python 03_cvar_portfolio_optimization.py

輸出:
    - cvar_portfolio_results.png (效率前緣 + 權重分配)
    - 終端機顯示最佳投組 vs. 等權重的比較
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import cvxpy as cp
import warnings

warnings.filterwarnings("ignore")


ASSETS = ["SPY", "QQQ", "TLT", "GLD", "VNQ", "EFA", "XLE", "HYG"]
ASSET_NAMES = {
    "SPY": "S&P 500",
    "QQQ": "Nasdaq 100",
    "TLT": "US Long Bond",
    "GLD": "Gold",
    "VNQ": "REITs",
    "EFA": "Intl Developed",
    "XLE": "Energy",
    "HYG": "High Yield",
}


def fetch_returns(tickers: list, period: str = "5y") -> pd.DataFrame:
    """拉取多資產歷史日報酬"""
    data = yf.download(tickers, period=period, auto_adjust=True, progress=False)["Close"]
    returns = data.pct_change().dropna()
    return returns


def cvar_optimization(
    returns: np.ndarray,
    alpha: float = 0.05,
    target_return: float = None,
) -> np.ndarray:
    """
    最小化 CVaR (Conditional Value at Risk)

    alpha: 尾部比例 (0.05 = 最差 5% 情境)
    """
    n_assets = returns.shape[1]
    n_scenarios = returns.shape[0]

    # 決策變數
    weights = cp.Variable(n_assets)
    var = cp.Variable()  # VaR threshold
    excess_loss = cp.Variable(n_scenarios, nonneg=True)

    # 投組報酬
    portfolio_returns = returns @ weights

    # CVaR 公式: CVaR = VaR + (1/alpha) * E[max(-R - VaR, 0)]
    cvar = var + (1.0 / (alpha * n_scenarios)) * cp.sum(excess_loss)

    # 約束
    constraints = [
        cp.sum(weights) == 1,
        weights >= 0,  # 不允許放空
        excess_loss >= -portfolio_returns - var,
    ]

    # 加入目標報酬約束 (如果指定)
    if target_return is not None:
        mean_returns = np.mean(returns, axis=0)
        constraints.append(mean_returns @ weights >= target_return)

    # 最佳化
    problem = cp.Problem(cp.Minimize(cvar), constraints)
    problem.solve(solver=cp.ECOS, verbose=False)

    if problem.status == "optimal":
        return weights.value
    else:
        return np.ones(n_assets) / n_assets


def mean_variance_optimization(returns: np.ndarray) -> np.ndarray:
    """傳統 Mean-Variance (Markowitz) 最佳化做比較"""
    n_assets = returns.shape[1]
    weights = cp.Variable(n_assets)

    mean_ret = np.mean(returns, axis=0)
    cov_matrix = np.cov(returns.T)

    portfolio_var = cp.quad_form(weights, cov_matrix)

    constraints = [
        cp.sum(weights) == 1,
        weights >= 0,
        mean_ret @ weights >= mean_ret.mean(),
    ]

    problem = cp.Problem(cp.Minimize(portfolio_var), constraints)
    problem.solve(solver=cp.ECOS, verbose=False)

    if problem.status == "optimal":
        return weights.value
    else:
        return np.ones(n_assets) / n_assets


def compute_portfolio_stats(returns: np.ndarray, weights: np.ndarray, alpha: float = 0.05) -> dict:
    """計算投組的績效指標"""
    port_returns = returns @ weights
    ann_return = np.mean(port_returns) * 252
    ann_vol = np.std(port_returns) * np.sqrt(252)
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0

    # VaR and CVaR
    sorted_returns = np.sort(port_returns)
    var_idx = int(alpha * len(sorted_returns))
    var = -sorted_returns[var_idx]
    cvar = -sorted_returns[:var_idx].mean()

    # Max Drawdown
    cum_returns = np.cumprod(1 + port_returns)
    running_max = np.maximum.accumulate(cum_returns)
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()

    return {
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "var_95": var,
        "cvar_95": cvar,
        "max_drawdown": max_dd,
    }


def plot_results(
    returns_df: pd.DataFrame,
    weights_cvar: np.ndarray,
    weights_mv: np.ndarray,
    weights_equal: np.ndarray,
    tickers: list,
):
    """視覺化比較三種配置"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("CVaR vs Mean-Variance vs Equal Weight Portfolio", fontsize=14, fontweight="bold")

    returns_np = returns_df.values

    # 1. 權重比較 (bar chart)
    ax = axes[0, 0]
    x = np.arange(len(tickers))
    width = 0.25
    ax.bar(x - width, weights_cvar, width, label="Min CVaR", color="#2ecc71", alpha=0.8)
    ax.bar(x, weights_mv, width, label="Min Variance", color="#3498db", alpha=0.8)
    ax.bar(x + width, weights_equal, width, label="Equal Weight", color="#95a5a6", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(tickers, fontsize=8)
    ax.set_ylabel("Weight")
    ax.set_title("Portfolio Weights Comparison")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    # 2. 累計報酬
    ax = axes[0, 1]
    for name, w, color in [
        ("Min CVaR", weights_cvar, "#2ecc71"),
        ("Min Variance", weights_mv, "#3498db"),
        ("Equal Weight", weights_equal, "#95a5a6"),
    ]:
        port_ret = returns_np @ w
        cum_ret = np.cumprod(1 + port_ret)
        ax.plot(returns_df.index, cum_ret, label=name, color=color, linewidth=1.5)

    ax.set_ylabel("Cumulative Return")
    ax.set_title("Cumulative Performance")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. 報酬分布比較
    ax = axes[1, 0]
    for name, w, color in [
        ("Min CVaR", weights_cvar, "#2ecc71"),
        ("Min Variance", weights_mv, "#3498db"),
    ]:
        port_ret = returns_np @ w
        ax.hist(port_ret, bins=80, alpha=0.5, color=color, label=name, density=True)
        # 標示 5% CVaR
        sorted_ret = np.sort(port_ret)
        var_idx = int(0.05 * len(sorted_ret))
        cvar_val = sorted_ret[:var_idx].mean()
        ax.axvline(cvar_val, color=color, linestyle="--", linewidth=2)

    ax.set_xlabel("Daily Return")
    ax.set_ylabel("Density")
    ax.set_title("Return Distribution (dashed = 5% CVaR)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. 回撤比較
    ax = axes[1, 1]
    for name, w, color in [
        ("Min CVaR", weights_cvar, "#2ecc71"),
        ("Min Variance", weights_mv, "#3498db"),
        ("Equal Weight", weights_equal, "#95a5a6"),
    ]:
        port_ret = returns_np @ w
        cum_ret = np.cumprod(1 + port_ret)
        running_max = np.maximum.accumulate(cum_ret)
        dd = (cum_ret - running_max) / running_max
        ax.plot(returns_df.index, dd, label=name, color=color, linewidth=1, alpha=0.8)

    ax.set_ylabel("Drawdown")
    ax.set_title("Drawdown Comparison")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("cvar_portfolio_results.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n[OK] 圖表已存: cvar_portfolio_results.png")


def main():
    tickers = ASSETS
    print(f"[1/4] 下載 {len(tickers)} 檔資產資料...")
    print(f"      {', '.join(tickers)}")
    returns_df = fetch_returns(tickers)
    returns_np = returns_df.values
    print(f"      期間: {returns_df.index[0].date()} — {returns_df.index[-1].date()}")
    print(f"      資料點: {len(returns_df)} 天")

    print("[2/4] CVaR 最佳化 (最差 5% 情境)...")
    weights_cvar = cvar_optimization(returns_np, alpha=0.05)

    print("[3/4] Mean-Variance 最佳化 (做比較)...")
    weights_mv = mean_variance_optimization(returns_np)

    weights_equal = np.ones(len(tickers)) / len(tickers)

    # 印出比較
    print(f"\n{'='*70}")
    print(f"  Portfolio Comparison")
    print(f"{'='*70}")
    print(f"\n  {'Asset':<8} {'CVaR Opt':>10} {'MV Opt':>10} {'Equal':>10}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*10}")
    for i, t in enumerate(tickers):
        print(f"  {t:<8} {weights_cvar[i]:>10.1%} {weights_mv[i]:>10.1%} {weights_equal[i]:>10.1%}")

    print(f"\n  {'Metric':<20} {'CVaR Opt':>12} {'MV Opt':>12} {'Equal':>12}")
    print(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*12}")

    for name, w in [("Min CVaR", weights_cvar), ("Min Variance", weights_mv), ("Equal", weights_equal)]:
        stats = compute_portfolio_stats(returns_np, w)
        if name == "Min CVaR":
            print(f"  {'Ann. Return':<20} {stats['ann_return']:>12.2%} ", end="")
        elif name == "Min Variance":
            s_cvar = compute_portfolio_stats(returns_np, weights_cvar)
            s_mv = compute_portfolio_stats(returns_np, weights_mv)
            s_eq = compute_portfolio_stats(returns_np, weights_equal)

    # 整齊印出
    for metric, key, fmt in [
        ("Ann. Return", "ann_return", ".2%"),
        ("Ann. Volatility", "ann_vol", ".2%"),
        ("Sharpe Ratio", "sharpe", ".2f"),
        ("VaR (95%)", "var_95", ".2%"),
        ("CVaR (95%)", "cvar_95", ".2%"),
        ("Max Drawdown", "max_drawdown", ".2%"),
    ]:
        s1 = compute_portfolio_stats(returns_np, weights_cvar)
        s2 = compute_portfolio_stats(returns_np, weights_mv)
        s3 = compute_portfolio_stats(returns_np, weights_equal)
        print(f"  {metric:<20} {s1[key]:>12{fmt}} {s2[key]:>12{fmt}} {s3[key]:>12{fmt}}")

    print("[4/4] 繪製圖表...")
    plot_results(returns_df, weights_cvar, weights_mv, weights_equal, tickers)

    print(f"\n{'='*70}")
    print("  完成! 你學到了:")
    print("  1. CVaR vs Variance: CVaR 關注尾部損失，更保守")
    print("  2. CVaR portfolio 通常重配債券和黃金 (避險資產)")
    print("  3. 凸最佳化 (CVXPY) 的實務操作")
    print("  4. 可以搭配 Project 1 的 regime 信號做動態切換")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
