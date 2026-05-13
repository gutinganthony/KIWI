"""Indicator collector that orchestrates all data sources."""

import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yaml

from .sources.fred import FREDSource
from .sources.multpl import MultplSource
from .sources.yfinance_source import YFinanceSource

logger = logging.getLogger(__name__)

# Default path to indicators config
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "indicators.yaml"


class IndicatorCollector:
    """Orchestrates data collection from all sources (FRED, Multpl, YFinance).

    Reads the indicators.yaml config to determine which source to call
    for each indicator, then returns a dict of pd.Series keyed by indicator name.
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        fred_api_key: Optional[str] = None,
    ) -> None:
        """Initialize collector with config and data sources.

        Args:
            config_path: Path to indicators.yaml. Uses default if None.
            fred_api_key: FRED API key. If None, reads from environment.
        """
        self._config_path = config_path or DEFAULT_CONFIG_PATH
        self._config = self._load_config()

        # Initialize sources lazily to allow partial collection
        self._fred: Optional[FREDSource] = None
        self._multpl: Optional[MultplSource] = None
        self._yfinance: Optional[YFinanceSource] = None

        self._fred_api_key = fred_api_key

    def _load_config(self) -> dict[str, Any]:
        """Load indicators config from YAML."""
        with open(self._config_path) as f:
            config = yaml.safe_load(f)
        return config["indicators"]

    @property
    def fred(self) -> FREDSource:
        """Lazy-initialize FRED source."""
        if self._fred is None:
            self._fred = FREDSource(api_key=self._fred_api_key)
        return self._fred

    @property
    def multpl(self) -> MultplSource:
        """Lazy-initialize Multpl source."""
        if self._multpl is None:
            self._multpl = MultplSource()
        return self._multpl

    @property
    def yfinance(self) -> YFinanceSource:
        """Lazy-initialize YFinance source."""
        if self._yfinance is None:
            self._yfinance = YFinanceSource()
        return self._yfinance

    def collect_all(
        self,
        as_of_date: Optional[str] = None,
        start_date: Optional[str] = None,
    ) -> dict[str, pd.Series]:
        """Collect all 14 indicators from their respective sources.

        Args:
            as_of_date: End date for data collection (YYYY-MM-DD).
                        If None, uses latest available data.
            start_date: Start date for data collection (YYYY-MM-DD).
                        Defaults to '2000-01-01' for 20+ year history.

        Returns:
            Dictionary mapping indicator key -> pd.Series of monthly values.
            Series that failed to fetch are omitted with a warning.
        """
        if start_date is None:
            start_date = "1970-01-01"

        results: dict[str, pd.Series] = {}

        for indicator_key, indicator_cfg in self._config.items():
            try:
                series = self._fetch_indicator(
                    indicator_key, indicator_cfg, start_date, as_of_date
                )
                if series is not None and not series.empty:
                    # Truncate to as_of_date if specified
                    if as_of_date:
                        series = series[series.index <= pd.to_datetime(as_of_date)]
                    results[indicator_key] = series
                    logger.info(
                        f"  [{indicator_key}] OK: {len(series)} observations"
                    )
                else:
                    logger.warning(f"  [{indicator_key}] returned empty series")
            except Exception as e:
                logger.error(f"  [{indicator_key}] FAILED: {e}")

        logger.info(
            f"Collection complete: {len(results)}/{len(self._config)} indicators"
        )
        return results

    def _fetch_indicator(
        self,
        key: str,
        cfg: dict[str, Any],
        start_date: str,
        end_date: Optional[str],
    ) -> Optional[pd.Series]:
        """Fetch a single indicator based on its config.

        Routes to the appropriate source and computation method.
        """
        source = cfg["source"]

        if source == "fred":
            return self._fetch_fred_indicator(key, cfg, start_date, end_date)
        elif source == "multpl":
            return self._fetch_multpl_indicator(key, cfg, start_date)
        elif source == "yfinance":
            return self._fetch_yfinance_indicator(key, cfg, start_date, end_date)
        else:
            logger.warning(f"Unknown source '{source}' for indicator {key}")
            return None

    def _fetch_fred_indicator(
        self,
        key: str,
        cfg: dict[str, Any],
        start_date: str,
        end_date: Optional[str],
    ) -> Optional[pd.Series]:
        """Fetch a FRED-based indicator, handling computed series."""
        computation = cfg.get("computation", "direct")

        if computation == "direct":
            series_id = cfg["fred_ids"][0]
            return self.fred.fetch_direct(series_id, start_date, end_date)

        elif computation == "ratio":
            if key == "buffett_indicator":
                return self.fred.fetch_buffett_indicator(start_date, end_date)
            elif key == "roic":
                return self.fred.fetch_roic(start_date, end_date)
            else:
                # Generic ratio: first / second
                ids = cfg["fred_ids"]
                s1 = self.fred.fetch_series(ids[0], start_date, end_date)
                s2 = self.fred.fetch_series(ids[1], start_date, end_date)
                s1_m = s1.resample("ME").last()
                s2_m = s2.resample("ME").last()
                common = s1_m.index.intersection(s2_m.index)
                result = s1_m.loc[common] / s2_m.loc[common]
                result.name = key
                return result

        elif computation == "pct_change_12":
            return self.fred.fetch_cpi_yoy(start_date, end_date)

        elif computation == "real_yield":
            return self.fred.fetch_real_yield(start_date, end_date)

        elif computation == "difference":
            return self.fred.fetch_baa_aaa_diff(start_date, end_date)

        else:
            logger.warning(f"Unknown computation '{computation}' for {key}")
            return None

    def _fetch_multpl_indicator(
        self,
        key: str,
        cfg: dict[str, Any],
        start_date: str,
    ) -> Optional[pd.Series]:
        """Fetch a multpl.com indicator."""
        slug = cfg["multpl_slug"]
        series = self.multpl.fetch_indicator(slug, start_date=start_date)
        series.name = key
        return series

    def _fetch_yfinance_indicator(
        self,
        key: str,
        cfg: dict[str, Any],
        start_date: str,
        end_date: Optional[str],
    ) -> Optional[pd.Series]:
        """Fetch a YFinance-based indicator."""
        computation = cfg.get("computation", "")

        if computation == "price_over_200ma":
            return self.yfinance.fetch_sp500_200ma_ratio(start_date, end_date)
        elif computation == "drawdown":
            return self.yfinance.fetch_sp500_drawdown(start_date, end_date)
        else:
            logger.warning(f"Unknown yfinance computation '{computation}' for {key}")
            return None
