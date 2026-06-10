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
            start_date = "1970-01-01"

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
        """Compute Buffett Indicator: total equity market value / GDP.

        修正：FRED 於 2024-06-03 下架所有 Wilshire 5000 系列（WILL5000IND 已不存在、
        會回 "series does not exist"）。改用 Z.1 資產負債表「非金融企業權益市值」
        NCBEILQ027S（$百萬, 季度）作為市值代理 / GDP（$十億, 季度）。百分位評分對
        絕對尺度不敏感，趨勢與相對高低和 Wilshire 版一致（絕對值較低，因僅含非金融
        企業）。

        Returns:
            Monthly ratio series (%).
        """
        # NCBEILQ027S = Nonfinancial Corporate Business; Corporate Equities; Market Value ($M)
        mktcap = self.fetch_series("NCBEILQ027S", start_date, end_date)
        gdp = self.fetch_series("GDP", start_date, end_date)

        mktcap_q = mktcap.resample("ME").last().dropna()  # $百萬, 季度
        gdp_q = gdp.resample("ME").last().dropna()         # $十億, 季度

        # 兩者皆季度、發布時點略不同 → 把最近一筆 GDP 前填(ffill)到市值的每個月份，
        # 避免「GDP 還沒出」的最近月份被 dropna 丟掉（同 multpl P/S dagger 的卡舊季問題）。
        gdp_aligned = gdp_q.reindex(mktcap_q.index, method="ffill")
        combined = pd.DataFrame({"mktcap": mktcap_q, "gdp": gdp_aligned}).dropna()
        if combined.empty:
            raise RuntimeError("No overlapping data for Buffett Indicator")

        # 單位對齊：市值 $百萬 / (GDP $十億 × 1000) = 比率；×100 為 %
        ratio = (combined["mktcap"] / (combined["gdp"] * 1000.0)) * 100
        # 季度→月度(前填到當月)，粒度與其他月度指標一致、且 as-of 跟得上當月
        monthly_idx = pd.date_range(
            ratio.index.min(), pd.Timestamp.today().normalize(), freq="ME"
        )
        result = ratio.reindex(monthly_idx, method="ffill").dropna()
        result.name = "buffett_indicator"
        logger.info(
            f"Computed Buffett Indicator (NCBEILQ027S/GDP): {len(result)} monthly obs, "
            f"latest={result.index[-1].date()} = {result.iloc[-1]:.1f}%"
        )
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

        profits_m = profits.resample("ME").last().ffill().dropna()
        nw_m = net_worth.resample("ME").last().ffill().dropna()

        combined = pd.DataFrame({"profits": profits_m, "nw": nw_m}).dropna()
        if combined.empty:
            raise RuntimeError("No overlapping data for ROIC")

        result = (combined["profits"] * 4) / combined["nw"]
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

        dgs10_m = dgs10.resample("ME").last().dropna()
        cpi_m = cpi_yoy.resample("ME").last().dropna()

        combined = pd.DataFrame({"dgs10": dgs10_m, "cpi": cpi_m}).dropna()
        if combined.empty:
            raise RuntimeError("No overlapping data for Real Yield")

        result = combined["dgs10"] - combined["cpi"]
        result.name = "real_yield_10y"
        logger.info(f"Computed Real Yield: {len(result)} observations")
        return result

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
