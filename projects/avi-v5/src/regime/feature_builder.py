"""Build feature matrix for regime detection.

Constructs a 6-feature DataFrame from daily market data used by the
HMM-based regime classifier.
"""

import logging

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# Trading days per year / month
_ANNUAL_FACTOR = 252
_WINDOW = 21  # ~1 month of trading days


def build_regime_features(
    sp500_daily: pd.DataFrame,
    vix: pd.Series,
    credit_spread: pd.Series,
) -> pd.DataFrame:
    """Build 6-feature matrix for regime detection.

    All features are computed on daily data, then resampled to **monthly**
    (last business day) for consistency with the AVI pipeline.

    Features
    --------
    1. rolling_return   -- 21-day rolling return, annualized
    2. realized_vol     -- 21-day realized volatility, annualized
    3. drawdown         -- 252-day drawdown from rolling peak
    4. rolling_sharpe   -- 21-day rolling Sharpe (risk-free = 0)
    5. vix_z            -- VIX level, standardized (z-score)
    6. credit_delta     -- BAA-10Y credit spread, 21-day change

    Parameters
    ----------
    sp500_daily : pd.DataFrame
        Must contain a ``"close"`` column with a DatetimeIndex.
    vix : pd.Series
        Daily VIX levels (e.g., VIXCLS from FRED).
    credit_spread : pd.Series
        Daily BAA-10Y credit spread (e.g., BAA10YM from FRED).

    Returns
    -------
    pd.DataFrame
        Monthly DataFrame with six standardized feature columns.
    """
    df = sp500_daily[["close"]].copy()
    df = df.sort_index()

    # Daily log returns
    df["returns"] = df["close"].pct_change()

    # Feature 1: 21-day rolling return, annualized
    df["rolling_return"] = (
        df["returns"].rolling(_WINDOW, min_periods=_WINDOW).mean() * _ANNUAL_FACTOR
    )

    # Feature 2: 21-day realized volatility, annualized
    df["realized_vol"] = (
        df["returns"].rolling(_WINDOW, min_periods=_WINDOW).std() * np.sqrt(_ANNUAL_FACTOR)
    )

    # Feature 3: 252-day drawdown from peak
    rolling_max = df["close"].rolling(_ANNUAL_FACTOR, min_periods=1).max()
    df["drawdown"] = (df["close"] - rolling_max) / rolling_max

    # Feature 4: 21-day rolling Sharpe (risk-free = 0)
    rolling_mean = df["returns"].rolling(_WINDOW, min_periods=_WINDOW).mean()
    rolling_std = df["returns"].rolling(_WINDOW, min_periods=_WINDOW).std()
    df["rolling_sharpe"] = (rolling_mean / rolling_std) * np.sqrt(_ANNUAL_FACTOR)
    # Replace infinities from zero-std periods
    df["rolling_sharpe"] = df["rolling_sharpe"].replace(
        [np.inf, -np.inf], np.nan
    )

    # Feature 5: VIX level, standardized
    vix_aligned = vix.reindex(df.index, method="ffill")
    vix_mean = vix_aligned.rolling(252, min_periods=60).mean()
    vix_std = vix_aligned.rolling(252, min_periods=60).std()
    df["vix_z"] = (vix_aligned - vix_mean) / vix_std
    df["vix_z"] = df["vix_z"].replace([np.inf, -np.inf], np.nan)

    # Feature 6: Credit spread change (21-day delta)
    credit_aligned = credit_spread.reindex(df.index, method="ffill")
    df["credit_delta"] = credit_aligned.diff(_WINDOW)

    # Select feature columns
    feature_cols = [
        "rolling_return",
        "realized_vol",
        "drawdown",
        "rolling_sharpe",
        "vix_z",
        "credit_delta",
    ]

    daily_features = df[feature_cols].dropna()

    if daily_features.empty:
        logger.warning("Feature matrix is empty after dropping NaN rows")
        return pd.DataFrame(columns=feature_cols)

    # Resample to monthly (last business day)
    monthly_features = daily_features.resample("BME").last().dropna()

    # Standardize features for HMM
    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(monthly_features.values)
    monthly_scaled = pd.DataFrame(
        scaled_values,
        index=monthly_features.index,
        columns=feature_cols,
    )

    logger.info(
        f"Built regime features: {len(monthly_scaled)} months, "
        f"{len(feature_cols)} features"
    )
    return monthly_scaled
