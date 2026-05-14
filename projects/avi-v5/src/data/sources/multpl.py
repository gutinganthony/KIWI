"""Multpl.com data source for AVI V5 valuation indicators."""

import logging
from typing import Optional

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MULTPL_URLS = {
    "shiller-pe": "https://www.multpl.com/shiller-pe/table/by-month",
    "s-p-500-price-to-sales": "https://www.multpl.com/s-p-500-price-to-sales/table/by-month",
    "s-p-500-earnings-yield": "https://www.multpl.com/s-p-500-earnings-yield/table/by-month",
}


class MultplSource:
    """Scrapes multpl.com for valuation indicators (CAPE, P/S, Earnings Yield)."""

    def __init__(self, timeout: int = 30) -> None:
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                )
            }
        )

    def fetch_indicator(
        self,
        indicator_slug: str,
        start_date: Optional[str] = None,
    ) -> pd.Series:
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

        if len(series) > 0:
            avg_gap_days = (series.index[-1] - series.index[0]).days / max(len(series) - 1, 1)
            if avg_gap_days > 180 and len(series) >= 5:
                logger.info(
                    f"{indicator_slug}: detected yearly data ({len(series)} pts, "
                    f"avg gap {avg_gap_days:.0f} days), interpolating to monthly..."
                )
                series = series.resample("ME").interpolate(method="linear")
                series = series.dropna()
                logger.info(f"{indicator_slug}: interpolated to {len(series)} monthly observations")

        return series

    def _parse_table(
        self,
        html: str,
        indicator_slug: str,
        start_date: Optional[str] = None,
    ) -> pd.Series:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"id": "datatable"})

        if table is None:
            table = soup.find("table")

        if table is None:
            raise RuntimeError(
                f"Could not find data table on multpl.com for {indicator_slug}"
            )

        dates = []
        values = []

        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) >= 2:
                date_text = cells[0].get_text(strip=True)
                value_text = cells[1].get_text(strip=True)

                try:
                    date = pd.to_datetime(date_text)
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
        series = series[~series.index.duplicated(keep="last")]

        if start_date:
            series = series[series.index >= pd.to_datetime(start_date)]

        logger.info(f"Parsed {indicator_slug}: {len(series)} observations")
        return series
