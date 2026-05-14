"""Rolling percentile computation for AVI scoring."""

import numpy as np
import pandas as pd


def rolling_percentile(
    series: pd.Series,
    window_months: int = 240,
    min_periods: int = 60,
) -> pd.Series:
    """Compute rolling percentile rank of each value within its lookback window.

    For each point at time t, computes the percentile rank of the value at t
    within the window [t-window : t-1].

    Uses expanding window for early periods: when fewer than `window_months`
    data points are available but at least `min_periods` exist, uses all
    available history instead of returning NaN.

    Args:
        series: Monthly time series of indicator values.
        window_months: Target lookback window in months (default 240 = 20 years).
        min_periods: Minimum months of history before producing a percentile
                     (default 60 = 5 years). Below this, returns NaN.

    Returns:
        Series of percentile ranks (0.0 to 1.0) with the same index.
    """
    if series.empty:
        return pd.Series(dtype=float, name=f"{series.name}_pctile")

    values = series.values
    n = len(values)
    percentiles = np.full(n, np.nan)

    for i in range(min_periods, n):
        lookback = min(i, window_months)
        window = values[i - lookback : i]
        current = values[i]

        rank = np.sum(window < current) / len(window)
        percentiles[i] = rank

    result = pd.Series(percentiles, index=series.index, name=f"{series.name}_pctile")
    return result
