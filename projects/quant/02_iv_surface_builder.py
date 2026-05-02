"""
Project 2: Implied Volatility Surface Builder
=============================================
從選擇權鏈計算隱含波動率，建立 3D 曲面、skew 和 term structure。

使用方式:
    pip install -r requirements.txt
    python 02_iv_surface_builder.py

輸出:
    - iv_surface.png (3D 曲面 + skew + term structure)
    - 終端機顯示 IV 摘要統計
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.stats import norm
from scipy.optimize import brentq
import yfinance as yf
import warnings

warnings.filterwarnings("ignore")


def black_scholes_price(S, K, T, r, sigma, option_type="call"):
    """Black-Scholes 選擇權定價"""
    if T <= 0 or sigma <= 0:
        return max(S - K, 0) if option_type == "call" else max(K - S, 0)

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def implied_volatility(market_price, S, K, T, r, option_type="call"):
    """用 Brent 方法反解隱含波動率"""
    if T <= 0:
        return np.nan

    intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
    if market_price <= intrinsic:
        return np.nan

    def objective(sigma):
        return black_scholes_price(S, K, T, r, sigma, option_type) - market_price

    try:
        iv = brentq(objective, 1e-6, 5.0, xtol=1e-8)
        return iv
    except (ValueError, RuntimeError):
        return np.nan


def fetch_options_data(ticker: str = "SPY") -> tuple:
    """從 yfinance 拉取選擇權鏈"""
    stock = yf.Ticker(ticker)
    spot = stock.history(period="1d")["Close"].iloc[-1]
    expirations = stock.options

    # 取前 6 個到期日
    expirations = expirations[:6]

    all_options = []
    for exp in expirations:
        chain = stock.option_chain(exp)
        calls = chain.calls.copy()
        calls["option_type"] = "call"
        calls["expiration"] = exp
        puts = chain.puts.copy()
        puts["option_type"] = "put"
        puts["expiration"] = exp
        all_options.append(calls)
        all_options.append(puts)

    df = pd.concat(all_options, ignore_index=True)
    return df, spot, expirations


def compute_iv_surface(df: pd.DataFrame, spot: float, r: float = 0.05) -> pd.DataFrame:
    """計算整個 IV surface"""
    today = pd.Timestamp.now()
    results = []

    for _, row in df.iterrows():
        exp_date = pd.Timestamp(row["expiration"])
        T = (exp_date - today).days / 365.0

        if T <= 0.01:
            continue

        K = row["strike"]
        moneyness = K / spot

        # 只取 moneyness 在合理範圍
        if moneyness < 0.7 or moneyness > 1.3:
            continue

        mid_price = (row["bid"] + row["ask"]) / 2 if row["bid"] > 0 and row["ask"] > 0 else row["lastPrice"]
        if mid_price <= 0:
            continue

        iv = implied_volatility(mid_price, spot, K, T, r, row["option_type"])

        if iv is not None and not np.isnan(iv) and 0.01 < iv < 3.0:
            results.append({
                "strike": K,
                "expiration": row["expiration"],
                "T": T,
                "moneyness": moneyness,
                "iv": iv,
                "option_type": row["option_type"],
                "volume": row.get("volume", 0),
            })

    return pd.DataFrame(results)


def plot_iv_surface(iv_df: pd.DataFrame, spot: float, ticker: str):
    """繪製 IV 曲面、skew、term structure"""
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle(f"Implied Volatility Surface — {ticker} (Spot: ${spot:.2f})", fontsize=14, fontweight="bold")

    # 1. 3D Surface (calls only)
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    calls = iv_df[iv_df["option_type"] == "call"]

    if len(calls) > 10:
        sc = ax1.scatter(
            calls["moneyness"], calls["T"] * 365, calls["iv"] * 100,
            c=calls["iv"] * 100, cmap="RdYlGn_r", s=15, alpha=0.8
        )
        ax1.set_xlabel("Moneyness (K/S)")
        ax1.set_ylabel("Days to Expiry")
        ax1.set_zlabel("IV (%)")
        ax1.set_title("3D IV Surface (Calls)")
        ax1.view_init(elev=25, azim=45)

    # 2. Volatility Smile / Skew (per expiration)
    ax2 = fig.add_subplot(2, 2, 2)
    expirations = sorted(calls["expiration"].unique())
    colors = plt.cm.viridis(np.linspace(0, 1, len(expirations)))

    for exp, color in zip(expirations, colors):
        subset = calls[calls["expiration"] == exp].sort_values("moneyness")
        if len(subset) >= 3:
            ax2.plot(
                subset["moneyness"], subset["iv"] * 100,
                "o-", color=color, markersize=3, linewidth=1.2, label=exp, alpha=0.8
            )

    ax2.axvline(1.0, color="gray", linestyle="--", alpha=0.5, label="ATM")
    ax2.set_xlabel("Moneyness (K/S)")
    ax2.set_ylabel("Implied Volatility (%)")
    ax2.set_title("Volatility Skew by Expiration")
    ax2.legend(fontsize=7, loc="upper right")
    ax2.grid(True, alpha=0.3)

    # 3. Term Structure (ATM)
    ax3 = fig.add_subplot(2, 2, 3)
    atm_iv = calls[(calls["moneyness"] > 0.97) & (calls["moneyness"] < 1.03)]
    if len(atm_iv) > 0:
        term_struct = atm_iv.groupby("expiration").agg({"iv": "mean", "T": "first"}).sort_values("T")
        ax3.plot(
            term_struct["T"] * 365, term_struct["iv"] * 100,
            "s-", color="#2c3e50", markersize=8, linewidth=2
        )
        ax3.set_xlabel("Days to Expiry")
        ax3.set_ylabel("ATM IV (%)")
        ax3.set_title("Term Structure (ATM ±3%)")
        ax3.grid(True, alpha=0.3)

    # 4. Put-Call IV comparison (skew indicator)
    ax4 = fig.add_subplot(2, 2, 4)
    # 25-delta skew proxy: OTM put IV vs OTM call IV
    otm_puts = iv_df[(iv_df["option_type"] == "put") & (iv_df["moneyness"] < 0.97)]
    otm_calls = iv_df[(iv_df["option_type"] == "call") & (iv_df["moneyness"] > 1.03)]

    if len(otm_puts) > 0 and len(otm_calls) > 0:
        put_iv_by_exp = otm_puts.groupby("expiration")["iv"].mean()
        call_iv_by_exp = otm_calls.groupby("expiration")["iv"].mean()
        skew_df = pd.DataFrame({"put_iv": put_iv_by_exp, "call_iv": call_iv_by_exp}).dropna()
        skew_df["skew"] = (skew_df["put_iv"] - skew_df["call_iv"]) * 100

        if len(skew_df) > 0:
            ax4.bar(range(len(skew_df)), skew_df["skew"], color="#e74c3c", alpha=0.7)
            ax4.set_xticks(range(len(skew_df)))
            ax4.set_xticklabels(skew_df.index, rotation=45, fontsize=7)
            ax4.set_ylabel("Put IV - Call IV (%)")
            ax4.set_title("Skew (OTM Put - OTM Call IV)")
            ax4.axhline(0, color="gray", linestyle="--", alpha=0.5)
            ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("iv_surface.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\n[OK] 圖表已存: iv_surface.png")


def print_iv_summary(iv_df: pd.DataFrame):
    """印出 IV 摘要"""
    print(f"\n{'='*60}")
    print(f"  Implied Volatility Summary")
    print(f"{'='*60}")

    calls = iv_df[iv_df["option_type"] == "call"]
    puts = iv_df[iv_df["option_type"] == "put"]

    atm = calls[(calls["moneyness"] > 0.97) & (calls["moneyness"] < 1.03)]

    print(f"\n  資料點總數:    {len(iv_df)}")
    print(f"  Calls:         {len(calls)}")
    print(f"  Puts:          {len(puts)}")
    print(f"  到期日數量:    {iv_df['expiration'].nunique()}")
    print(f"\n  ATM IV (calls): {atm['iv'].mean()*100:.1f}% (mean)")
    print(f"  IV 範圍:        {iv_df['iv'].min()*100:.1f}% — {iv_df['iv'].max()*100:.1f}%")

    print(f"\n  按到期日:")
    for exp in sorted(iv_df["expiration"].unique()):
        subset = calls[calls["expiration"] == exp]
        if len(subset) > 0:
            print(f"    {exp}: mean IV = {subset['iv'].mean()*100:.1f}%, "
                  f"strikes = {len(subset)}")


def main():
    ticker = "SPY"
    print(f"[1/4] 下載 {ticker} 選擇權鏈...")
    df, spot, expirations = fetch_options_data(ticker)
    print(f"      Spot: ${spot:.2f}, 到期日: {len(expirations)} 個")

    print("[2/4] 計算隱含波動率 (Brent method)...")
    iv_df = compute_iv_surface(df, spot)
    print(f"      成功計算 {len(iv_df)} 個 IV 資料點")

    if len(iv_df) < 10:
        print("[ERROR] IV 資料點太少，可能是市場休市或資料不可用。")
        return

    print("[3/4] 統計摘要...")
    print_iv_summary(iv_df)

    print("[4/4] 繪製 IV Surface...")
    plot_iv_surface(iv_df, spot, ticker)

    print(f"\n{'='*60}")
    print("  完成! 你學到了:")
    print("  1. Black-Scholes 反解 IV (數值求根)")
    print("  2. Volatility Smile / Skew 的含義")
    print("  3. Term Structure 的解讀")
    print("  4. Put-Call skew 作為市場恐懼指標")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
