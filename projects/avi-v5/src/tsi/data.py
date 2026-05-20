"""TSI data collector — fetches all required daily data from yfinance + FRED."""

import logging
import os

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class TSIDataCollector:
    """Collects daily stock/ETF/yield data for TSI computation."""

    def collect_all(self, start: str = "2024-01-01", end: str = None) -> dict:
        data = {}

        # Stock/ETF tickers via yfinance
        tickers = {
            "sox": "^SOX",      # Philadelphia Semiconductor Index
            "qqq": "QQQ",       # Nasdaq 100 ETF
            "mu": "MU",         # Micron (memory proxy)
            "smh": "SMH",       # VanEck Semiconductor ETF (AI infra proxy)
            "spy": "SPY",       # S&P 500 ETF
            "vix": "^VIX",      # VIX
        }

        for key, ticker in tickers.items():
            try:
                logger.info(f"Fetching {ticker}...")
                df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    close = df[("Close", ticker)]
                else:
                    close = df["Close"]
                data[key] = close.dropna()
                logger.info(f"  {ticker}: {len(data[key])} days")
            except Exception as e:
                logger.error(f"  {ticker} failed: {e}")
                data[key] = pd.Series(dtype=float)

        # 10Y + 30Y Treasury from FRED
        try:
            from fredapi import Fred
            fred_key = os.environ.get("FRED_API_KEY", "")
            if fred_key:
                fred = Fred(api_key=fred_key)
                logger.info("Fetching 10Y Treasury from FRED...")
                t10y = fred.get_series("DGS10", observation_start=start).dropna()
                data["t10y"] = t10y
                logger.info(f"  10Y: {len(t10y)} days")

                logger.info("Fetching 30Y Treasury from FRED...")
                t30y = fred.get_series("DGS30", observation_start=start).dropna()
                data["t30y"] = t30y
                logger.info(f"  30Y: {len(t30y)} days")
            else:
                logger.warning("No FRED_API_KEY, using ^TNX/^TYX as proxy")
                tnx = yf.download("^TNX", start=start, end=end, auto_adjust=True, progress=False)
                if isinstance(tnx.columns, pd.MultiIndex):
                    data["t10y"] = tnx[("Close", "^TNX")].dropna() / 10
                else:
                    data["t10y"] = tnx["Close"].dropna() / 10
                tyx = yf.download("^TYX", start=start, end=end, auto_adjust=True, progress=False)
                if isinstance(tyx.columns, pd.MultiIndex):
                    data["t30y"] = tyx[("Close", "^TYX")].dropna() / 10
                else:
                    data["t30y"] = tyx["Close"].dropna() / 10
        except Exception as e:
            logger.error(f"  Treasury failed: {e}")
            data["t10y"] = pd.Series(dtype=float)
            data["t30y"] = pd.Series(dtype=float)

        return data
