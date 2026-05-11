"""GARCH(1,1) volatility forecasting engine.

Uses the ``arch`` library to fit a GARCH(1,1) model on S&P 500 daily
returns with a Student-t innovation distribution for fat-tail capture.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from arch import arch_model

logger = logging.getLogger(__name__)

# Trading days per year
_ANNUAL_FACTOR = 252


class GARCHEngine:
    """GARCH(1,1) volatility model with Student-t innovations.

    Attributes
    ----------
    persistence : float
        alpha + beta (volatility persistence).  Values > 0.97 indicate
        a "sticky" volatility regime.
    half_life : float
        Number of trading days for a volatility shock to decay 50%.
    """

    def __init__(
        self,
        p: int = 1,
        q: int = 1,
        dist: str = "studentst",
    ) -> None:
        """Initialise GARCH parameters.

        Parameters
        ----------
        p : int
            GARCH lag order (default 1).
        q : int
            ARCH lag order (default 1).
        dist : str
            Innovation distribution.  One of ``"normal"``, ``"studentst"``,
            ``"skewt"`` (default ``"studentst"``).
        """
        self._p = p
        self._q = q
        self._dist = dist
        self._result: Optional[object] = None
        self._returns_pct: Optional[pd.Series] = None
        self._fitted = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self, returns: pd.Series) -> "GARCHEngine":
        """Fit GARCH model on daily returns.

        Parameters
        ----------
        returns : pd.Series
            Daily simple returns (e.g., 0.01 for +1 %).  Will be
            internally scaled to percentage points for numerical
            stability (the ``arch`` library convention).

        Returns
        -------
        GARCHEngine
            ``self`` for chaining.
        """
        if returns.empty or len(returns) < 100:
            logger.warning(
                f"Insufficient return data ({len(returns)} obs). "
                "GARCH fitting skipped."
            )
            self._fitted = False
            return self

        # Scale to percentage points (0.01 -> 1.0)
        returns_clean = returns.dropna()
        self._returns_pct = returns_clean * 100.0

        try:
            model = arch_model(
                self._returns_pct,
                vol="Garch",
                p=self._p,
                q=self._q,
                dist=self._dist,
                mean="Constant",
                rescale=False,
            )
            self._result = model.fit(disp="off", show_warning=False)
            self._fitted = True

            logger.info(
                f"GARCH({self._p},{self._q}) fitted: "
                f"persistence={self.persistence:.4f}, "
                f"half_life={self.half_life:.1f} days"
            )

        except Exception as exc:
            logger.error(f"GARCH fitting failed: {exc}. Model unavailable.")
            self._fitted = False

        return self

    def forecast_volatility(self, horizon: int = 21) -> float:
        """Forecast annualized volatility over *horizon* trading days.

        Uses the analytic multi-step GARCH forecast and annualizes
        the terminal daily standard deviation.

        Parameters
        ----------
        horizon : int
            Forecast horizon in trading days (default 21 = ~1 month).

        Returns
        -------
        float
            Annualized volatility forecast (in decimal, e.g., 0.18 = 18 %).
            Returns ``np.nan`` if the model is not fitted.
        """
        if not self._fitted or self._result is None:
            logger.warning("Model not fitted; cannot forecast volatility")
            return np.nan

        try:
            fcast = self._result.forecast(horizon=horizon, reindex=False)
            # variance column contains per-step conditional variance (pct^2)
            # Take mean variance across the horizon as representative daily var
            variance_array = fcast.variance.values[-1, :]  # last obs forecast
            mean_daily_var_pct = np.mean(variance_array)
            # Convert from pct^2 to decimal^2, then annualize
            daily_vol_decimal = np.sqrt(mean_daily_var_pct) / 100.0
            annual_vol = daily_vol_decimal * np.sqrt(_ANNUAL_FACTOR)
            return float(annual_vol)

        except Exception as exc:
            logger.error(f"GARCH forecast failed: {exc}")
            return np.nan

    @property
    def persistence(self) -> float:
        """Volatility persistence (alpha + beta).

        A value close to 1.0 means shocks persist for a long time.
        Returns ``np.nan`` if the model is not fitted.
        """
        if not self._fitted or self._result is None:
            return np.nan

        params = self._result.params
        alpha = params.get("alpha[1]", 0.0)
        beta = params.get("beta[1]", 0.0)
        return float(alpha + beta)

    @property
    def half_life(self) -> float:
        """Number of trading days for a volatility shock to decay 50 %.

        Computed as ``log(0.5) / log(persistence)``.
        Returns ``np.nan`` if the model is not fitted or persistence >= 1.
        """
        p = self.persistence
        if np.isnan(p) or p <= 0.0 or p >= 1.0:
            return np.nan
        return float(np.log(0.5) / np.log(p))
