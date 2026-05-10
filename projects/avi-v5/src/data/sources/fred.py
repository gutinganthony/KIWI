"""FRED API data source for AVI V5 indicators."""

import logging
import os
from datetime import datetime
from typing import Optional

import pandas as pd
from fredapi import Fred

logger = logging.getLogger(__name__)


class FREDSource:
    """Fetches economic indicator data from the FRED API.

    Handles both direct series pulls and computed indicators
    (ratios, differences, percent changes).
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize FRED client.

        Args:
            api_key: FRED API key. If None, reads from FRED_API_KEY env var.
        """
        key = api_key or os.environ.get("FRED_API_KEY")
        if not key:
            raise ValueError(
                "FRED API key required. Set FRED_API_KEY env var or pass api_key."
            )
        self._fred = Fred(api_key=key)

    def fetch_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.Series:
        """Fetch a single FRED series.

        Args:
            series_id: FRED series identifier (e.g., 'VIXCLS').
            start_date: Start date as 'YYYY-MM-DD'. Defaults to 20+ years ago.
            end_date: End date as 'YYYY-MM-DD'. Defaults to today.

        Returns:
            pandas Series indexed by date.

        Raises:
            RuntimeError: If the FRED API call fails.
        """
        if start_date is None:
            start_date = "2000-01-01"

        try:
            data = self._fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date,
            )
            data = data.dropna()
            data.name = series_id
            logger.info(f"Fetched {series_id}: {len(data)} observations")
            return data
        except Exception as e:
            raise RuntimeError(f"Failed to fetch FRED series {series_id}: {e}") from e

    def fetch_buffett_indicator(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.Series:
        """Compute Buffett Indicator: Wilshire 5000 / GDP.

        Both series are quarterly; we align and divide.

        Returns:
            Monthly-interpolated ratio series.
        """
        wilshire = self.fetch_series("WILL5000PRFC", start_date, end_date)
        gdp = self.fetch_series("GDP", start_date, end_date)

        # Align to quarterly frequency, then compute ratio
        # GDP is quarterly, Wilshire is daily — resample Wilshire to quarterly
        wilshire_q = wilshire.resample("QE").last()

        # Align indexes
        common_idx = wilshire_q.index.intersection(gdp.index)
        if common_idx.empty:
            # Try aligning by quarter period
            wilshire_q.index = wilshire_q.index.to_period("Q").to_timestamp("QE")
            gdp.index = gdp.index.to_period("Q").to_timestamp("QE")
            common_idx = wilshire_q.index.intersection(gdp.index)

        ratio = wilshire_q.loc[common_idx] / gdp.loc[common_idx]

        # Resample to monthly for consistent frequency
        result = ratio.resample("ME").ffill()
        result.name = "buffett_indicator"
        logger.info(f"Computed Buffett Indicator: {len(result)} monthly observations")
        return result

    def fetch_roic(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.Series:
        """Compute corporate ROIC: Profits / Net Worth.

        A446RC1Q027SBEA = Corporate profits after tax
        TNWMVBSNNCB = Net worth of nonfinancial corporate business

        Returns:
            Quarterly ratio series resampled to monthly.
        """
        profits = self.fetch_series("A446RC1Q027SBEA", start_date, end_date)
        net_worth = self.fetch_series("TNWMVBSNNCB", start_date, end_date)

        # Both are quarterly — align
        profits_q = profits.resample("QE").last()
        net_worth_q = net_worth.resample("QE").last()

        common_idx = profits_q.index.intersection(net_worth_q.index)
        if common_idx.empty:
            profits_q.index = profits_q.index.to_period("Q").to_timestamp("QE")
            net_worth_q.index = net_worth_q.index.to_period("Q").to_timestamp("QE")
            common_idx = profits_q.index.intersection(net_worth_q.index)

        # Annualize profits (multiply quarterly by 4) then divide by net worth
        ratio = (profits_q.loc[common_idx] * 4) / net_worth_q.loc[common_idx]

        result = ratio.resample("ME").ffill()
        result.name = "roic"
        logger.info(f"Computed ROIC: {len(result)} monthly observations")
        return result

    def fetch_cpi_yoy(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.Series:
        """Compute CPI Year-over-Year percent change.

        Returns:
            Monthly YoY inflation rate.
        """
        cpi = self.fetch_series("CPIAUCSL", start_date, end_date)
        yoy = cpi.pct_change(periods=12) * 100  # As percentage
        yoy = yoy.dropna()
        yoy.name = "cpi_yoy"
        logger.info(f"Computed CPI YoY: {len(yoy)} observations")
        return yoy

    def fetch_real_yield(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.Series:
        """Compute 10Y Real Yield: DGS10 - CPI YoY.

        Returns:
            Monthly real yield series.
        """
        dgs10 = self.fetch_series("DGS10", start_date, end_date)
        cpi_yoy = self.fetch_cpi_yoy(start_date, end_date)

        # DGS10 is daily, resample to monthly
        dgs10_m = dgs10.resample("ME").last()

        # Align indexes
        common_idx = dgs10_m.index.intersection(cpi_yoy.index)
        real_yield = dgs10_m.loc[common_idx] - cpi_yoy.loc[common_idx]
        real_yield.name = "real_yield_10y"
        logger.info(f"Computed Real Yield: {len(real_yield)} observations")
        return real_yield

    def fetch_baa_aaa_diff(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.Series:
        """Compute BAA-AAA credit spread differential.

        Returns:
            Monthly spread series.
        """
        baa = self.fetch_series("BAA", start_date, end_date)
        aaa = self.fetch_series("AAA", start_date, end_date)

        # Both are daily, resample to monthly
        baa_m = baa.resample("ME").last()
        aaa_m = aaa.resample("ME").last()

        common_idx = baa_m.index.intersection(aaa_m.index)
        diff = baa_m.loc[common_idx] - aaa_m.loc[common_idx]
        diff.name = "baa_aaa_diff"
        logger.info(f"Computed BAA-AAA Diff: {len(diff)} observations")
        return diff

    def fetch_direct(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        resample_monthly: bool = True,
    ) -> pd.Series:
        """Fetch a direct FRED series, optionally resampled to monthly.

        Args:
            series_id: FRED series ID.
            start_date: Start date.
            end_date: End date.
            resample_monthly: If True, resample daily data to month-end.

        Returns:
            Series of values.
        """
        data = self.fetch_series(series_id, start_date, end_date)
        if resample_monthly and not data.empty:
            # Check if data is already monthly or less frequent
            if len(data) > 0:
                avg_gap = (data.index[-1] - data.index[0]).days / max(len(data) - 1, 1)
                if avg_gap < 20:  # Likely daily data
                    data = data.resample("ME").last().dropna()
        return data
