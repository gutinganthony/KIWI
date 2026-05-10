"""Rolling percentile computation for AVI scoring."""

import numpy as np
import pandas as pd


def rolling_percentile(
    series: pd.Series,
    window_months: int = 240,
) -> pd.Series:
    """Compute rolling percentile rank of each value within its lookback window.

    For each point at time t, computes the percentile rank of the value at t
    within the window [t-window : t-1]. This tells us where the current value
    sits historically — e.g., a 90th percentile CAPE means it's higher than
    90% of the values in the past 20 years.

    Args:
        series: Monthly time series of indicator values.
        window_months: Lookback window in months (default 240 = 20 years).

    Returns:
        Series of percentile ranks (0.0 to 1.0) with the same index.
        First `window_months` values will be NaN (insufficient history).
    """
    if series.empty:
        return pd.Series(dtype=float, name=f"{series.name}_pctile")

    values = series.values
    n = len(values)
    percentiles = np.full(n, np.nan)

    for i in range(window_months, n):
        # Lookback window: [i - window_months, i - 1] (exclusive of current)
        window = values[i - window_months : i]
        current = values[i]

        # Percentile rank: fraction of window values that are <= current
        # Using strict less-than for rank to avoid self-inclusion bias
        rank = np.sum(window < current) / len(window)
        percentiles[i] = rank

    result = pd.Series(percentiles, index=series.index, name=f"{series.name}_pctile")
    return result
