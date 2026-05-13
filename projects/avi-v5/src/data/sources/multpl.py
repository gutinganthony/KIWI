"""Multpl.com data source for AVI V5 valuation indicators."""

import logging
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Mapping of indicator keys to multpl.com table URLs
MULTPL_URLS = {
    "shiller-pe": "https://www.multpl.com/shiller-pe/table/by-month",
    "s-p-500-price-to-sales": "https://www.multpl.com/s-p-500-price-to-sales/table/by-month",
    "s-p-500-earnings-yield": "https://www.multpl.com/s-p-500-earnings-yield/table/by-month",
}

MULTPL_FALLBACK_URLS = {
    "s-p-500-price-to-sales": "https://www.multpl.com/s-p-500-price-to-sales/table/by-year",
}


class MultplSource:
    """Scrapes multpl.com for valuation indicators (CAPE, P/S, Earnings Yield).

    Multpl.com provides free monthly historical data tables for key
    S&P 500 valuation metrics not available on FRED.
    """

    def __init__(self, timeout: int = 30) -> None:
        """Initialize with request timeout.

        Args:
            timeout: HTTP request timeout in seconds.
        """
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
        )

    def fetch_indicator(
        self,
        indicator_slug: str,
        start_date: Optional[str] = None,
    ) -> pd.Series:
        """Fetch a monthly indicator series from multpl.com.

        Args:
            indicator_slug: Key into MULTPL_URLS (e.g., 'shiller-pe').
            start_date: Optional start date filter as 'YYYY-MM-DD'.

        Returns:
            pandas Series indexed by date with monthly values.

        Raises:
            ValueError: If indicator_slug is not recognized.
            RuntimeError: If scraping fails.
        """
        if indicator_slug not in MULTPL_URLS:
            raise ValueError(
                f"Unknown indicator slug '{indicator_slug}'. "
                f"Available: {list(MULTPL_URLS.keys())}"
            )

        url = MULTPL_URLS[indicator_slug]
        logger.info(f"Fetching {indicator_slug} from {url}")

        try:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(
                f"Failed to fetch {indicator_slug} from multpl.com: {e}"
            ) from e

        series = self._parse_table(response.text, indicator_slug, start_date)

        if len(series) < 50 and indicator_slug in MULTPL_FALLBACK_URLS:
            logger.warning(
                f"{indicator_slug}: only {len(series)} observations from monthly URL, "
                f"trying yearly fallback and interpolating..."
            )
            fallback_url = MULTPL_FALLBACK_URLS[indicator_slug]
            try:
                resp2 = self._session.get(fallback_url, timeout=self._timeout)
                resp2.raise_for_status()
                yearly = self._parse_table(resp2.text, indicator_slug, start_date)
                if len(yearly) > len(series):
                    series = yearly.resample("ME").interpolate(method="linear")
                    series = series.dropna()
                    logger.info(f"{indicator_slug}: interpolated to {len(series)} monthly from yearly")
            except Exception as e:
                logger.warning(f"Fallback for {indicator_slug} failed: {e}")

        return series

    def _parse_table(
        self,
        html: str,
        indicator_slug: str,
        start_date: Optional[str] = None,
    ) -> pd.Series:
        """Parse the HTML table from multpl.com into a pandas Series.

        Args:
            html: Raw HTML content.
            indicator_slug: Name for the resulting series.
            start_date: Optional start date filter.

        Returns:
            Parsed monthly series.
        """
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"id": "datatable"})

        if table is None:
            # Fallback: find any table with data
            table = soup.find("table")

        if table is None:
            raise RuntimeError(
                f"Could not find data table on multpl.com for {indicator_slug}"
            )

        dates = []
        values = []

        rows = table.find_all("tr")
        for row in rows[1:]:  # Skip header
            cells = row.find_all("td")
            if len(cells) >= 2:
                date_text = cells[0].get_text(strip=True)
                value_text = cells[1].get_text(strip=True)

                try:
                    date = pd.to_datetime(date_text)
                    # Remove % sign and other non-numeric chars
                    value_clean = (
                        value_text.replace("%", "")
                        .replace(",", "")
                        .replace("$", "")
                        .strip()
                    )
                    value = float(value_clean)
                    dates.append(date)
                    values.append(value)
                except (ValueError, TypeError):
                    continue

        if not dates:
            raise RuntimeError(
                f"No data parsed from multpl.com for {indicator_slug}"
            )

        series = pd.Series(values, index=pd.DatetimeIndex(dates), name=indicator_slug)
        series = series.sort_index()

        # Remove duplicates (keep last)
        series = series[~series.index.duplicated(keep="last")]

        # Apply start_date filter
        if start_date:
            series = series[series.index >= pd.to_datetime(start_date)]

        logger.info(f"Parsed {indicator_slug}: {len(series)} monthly observations")
        return series
