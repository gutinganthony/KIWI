"""Yahoo Finance data source for S&P 500 momentum indicators."""

import logging
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class YFinanceSource:
    """Fetches S&P 500 price data from Yahoo Finance for momentum indicators.

    Computes:
    - S&P 500 / 200-day MA ratio (monthly)
    - S&P 500 drawdown from all-time high (monthly)
    """

    def __init__(self, ticker: str = "^GSPC") -> None:
        """Initialize with ticker symbol.

        Args:
            ticker: Yahoo Finance ticker. Default is S&P 500.
        """
        self._ticker = ticker

    def _fetch_price_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch daily OHLCV data from Yahoo Finance.

        Args:
            start_date: Start date as 'YYYY-MM-DD'. Defaults to 25 years ago.
            end_date: End date as 'YYYY-MM-DD'. Defaults to today.

        Returns:
            DataFrame with daily OHLCV data.
        """
        if start_date is None:
            start_date = "1998-01-01"  # Extra buffer for 200MA calculation

        try:
            data = yf.download(
                self._ticker,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True,
            )
            if data.empty:
                raise RuntimeError(f"No data returned for {self._ticker}")
            logger.info(
                f"Fetched {self._ticker}: {len(data)} daily observations "
                f"({data.index[0].date()} to {data.index[-1].date()})"
            )
            return data
        except Exception as e:
            raise RuntimeError(
                f"Failed to fetch {self._ticker} from Yahoo Finance: {e}"
            ) from e

    def fetch_sp500_200ma_ratio(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.Series:
        """Compute S&P 500 Price / 200-day Moving Average ratio.

        A ratio > 1 means price is above its 200MA (bullish but potentially
        overextended). Higher values indicate more extension above trend.

        Returns:
            Monthly series of price/200MA ratio.
        """
        data = self._fetch_price_data(start_date, end_date)

        # Handle multi-level columns from yfinance
        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        # Compute 200-day moving average
        ma_200 = close.rolling(window=200, min_periods=200).mean()

        # Compute ratio
        ratio = close / ma_200
        ratio = ratio.dropna()

        # Resample to monthly (end of month)
        monthly_ratio = ratio.resample("ME").last()
        monthly_ratio = monthly_ratio.dropna()
        monthly_ratio.name = "sp500_200ma_ratio"

        # Filter to start_date if it's after the buffer period
        if start_date and start_date > "1998-01-01":
            monthly_ratio = monthly_ratio[
                monthly_ratio.index >= pd.to_datetime(start_date)
            ]

        logger.info(
            f"Computed S&P/200MA ratio: {len(monthly_ratio)} monthly observations"
        )
        return monthly_ratio

    def fetch_sp500_drawdown(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.Series:
        """Compute S&P 500 drawdown from all-time high.

        Drawdown is expressed as a positive percentage (e.g., 0.20 = 20% below peak).
        Higher values mean the market is further from its peak.

        Note: Direction is 'up_is_safe' in config because larger drawdowns
        (already happened) mean risk has already materialized, creating
        potential for mean reversion (less forward risk).

        Returns:
            Monthly series of drawdown magnitude (0 to 1 scale).
        """
        data = self._fetch_price_data(start_date, end_date)

        # Handle multi-level columns from yfinance
        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        # Compute running maximum
        running_max = close.expanding().max()

        # Drawdown as positive magnitude (0 = at peak, 0.5 = 50% below peak)
        drawdown = (running_max - close) / running_max
        drawdown = drawdown.dropna()

        # Resample to monthly
        monthly_drawdown = drawdown.resample("ME").last()
        monthly_drawdown = monthly_drawdown.dropna()
        monthly_drawdown.name = "sp500_drawdown"

        if start_date and start_date > "1998-01-01":
            monthly_drawdown = monthly_drawdown[
                monthly_drawdown.index >= pd.to_datetime(start_date)
            ]

        logger.info(
            f"Computed S&P drawdown: {len(monthly_drawdown)} monthly observations"
        )
        return monthly_drawdown
