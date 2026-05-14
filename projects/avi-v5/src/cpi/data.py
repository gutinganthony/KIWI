"""Data collection for CPI indicators — all daily frequency."""

import logging
import os
from typing import Optional

import pandas as pd
import yfinance as yf
from fredapi import Fred

logger = logging.getLogger(__name__)


class CPIDataCollector:
    """Collects daily data needed for Crash Probability Index."""

    def __init__(self, fred_api_key: Optional[str] = None):
        key = fred_api_key or os.environ.get("FRED_API_KEY")
        if not key:
            raise ValueError("FRED_API_KEY required")
        self._fred = Fred(api_key=key)

    def collect_all(
        self, start: str = "2000-01-01", end: Optional[str] = None
    ) -> dict:
        """Collect all daily data sources for CPI computation.

        Returns dict with keys: sp500, vix, vix3m, baa, aaa, t10y, t2y
        """
        data = {}

        logger.info("Fetching S&P 500 daily (price + volume)...")
        sp = yf.download("^GSPC", start=start, end=end, auto_adjust=True, progress=False)
        if not sp.empty:
            sp.columns = [c.lower() if isinstance(c, str) else c[0].lower() for c in sp.columns]
            data["sp500"] = sp[["close", "volume"]] if "volume" in sp.columns else sp[["close"]]
            logger.info(f"  S&P 500: {len(sp)} days")

        logger.info("Fetching VIX daily...")
        try:
            vix = self._fred.get_series("VIXCLS", observation_start=start, observation_end=end).dropna()
            data["vix"] = vix
            logger.info(f"  VIX: {len(vix)} days")
        except Exception as e:
            logger.error(f"  VIX failed: {e}")

        logger.info("Fetching VIX3M (3-month VIX)...")
        try:
            vix3m_data = yf.download("^VIX3M", start=start, end=end, progress=False)
            if not vix3m_data.empty:
                if isinstance(vix3m_data.columns, pd.MultiIndex):
                    vix3m = vix3m_data[("Close", "^VIX3M")]
                else:
                    vix3m = vix3m_data["Close"]
                data["vix3m"] = vix3m.dropna()
                logger.info(f"  VIX3M: {len(data['vix3m'])} days")
            else:
                data["vix3m"] = None
                logger.warning("  VIX3M: no data, will use VIX MA proxy")
        except Exception:
            data["vix3m"] = None
            logger.warning("  VIX3M: failed, will use VIX MA proxy")

        logger.info("Fetching Moody's BAA yield...")
        try:
            baa = self._fred.get_series("DBAA", observation_start=start, observation_end=end).dropna()
            data["baa"] = baa
            logger.info(f"  BAA: {len(baa)} days")
        except Exception as e:
            logger.error(f"  BAA failed: {e}")

        logger.info("Fetching Moody's AAA yield...")
        try:
            aaa = self._fred.get_series("DAAA", observation_start=start, observation_end=end).dropna()
            data["aaa"] = aaa
            logger.info(f"  AAA: {len(aaa)} days")
        except Exception as e:
            logger.error(f"  AAA failed: {e}")

        logger.info("Fetching 10Y Treasury yield...")
        try:
            t10y = self._fred.get_series("DGS10", observation_start=start, observation_end=end).dropna()
            data["t10y"] = t10y
            logger.info(f"  10Y: {len(t10y)} days")
        except Exception as e:
            logger.error(f"  10Y failed: {e}")

        logger.info("Fetching 2Y Treasury yield...")
        try:
            t2y = self._fred.get_series("DGS2", observation_start=start, observation_end=end).dropna()
            data["t2y"] = t2y
            logger.info(f"  2Y: {len(t2y)} days")
        except Exception as e:
            logger.error(f"  2Y failed: {e}")

        return data
