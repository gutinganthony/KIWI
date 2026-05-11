"""AVI-signal-based portfolio simulator.

Implements a simple allocation strategy that reduces equity exposure
as the AVI score increases, reflecting higher perceived risk.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AVISignalPortfolio:
    """Monthly portfolio that adjusts SPY / cash allocation based on AVI level.

    Allocation rules map AVI score buckets to an equity weight.
    Cash earns 0 % (conservative assumption).  Allocations are set at
    month-end based on the AVI score and applied to the *following*
    month's return (no look-ahead).

    Attributes
    ----------
    ALLOCATION_RULES : dict
        Maps ``(lower, upper)`` AVI bucket to equity weight (0.0 -- 1.0).
    """

    ALLOCATION_RULES: dict[tuple[int, int], float] = {
        (0, 4): 1.00,   # AVI < 4:  100 % SPY
        (4, 5): 0.80,   # AVI 4-5:   80 % SPY
        (5, 6): 0.60,   # AVI 5-6:   60 % SPY
        (6, 7): 0.40,   # AVI 6-7:   40 % SPY
        (7, 8): 0.20,   # AVI 7-8:   20 % SPY
        (8, 10): 0.00,  # AVI >= 8:    0 % SPY (all cash)
    }

    def _get_allocation(self, avi_score: float) -> float:
        """Return equity allocation for a given AVI score."""
        for (lo, hi), weight in self.ALLOCATION_RULES.items():
            if lo <= avi_score < hi:
                return weight
        # AVI exactly 10.0 falls through; treat as max bucket
        if avi_score >= 10.0:
            return 0.0
        # Negative / NaN fallback
        return 1.0

    def run(
        self,
        avi_series: pd.Series,
        sp500_monthly_returns: pd.Series,
    ) -> pd.DataFrame:
        """Simulate portfolio returns driven by the AVI signal.

        The AVI score observed at month M determines the equity weight
        for the return earned in month M+1.  This ensures the signal is
        implementable without look-ahead.

        Parameters
        ----------
        avi_series : pd.Series
            Monthly AVI scores indexed by month-end date.
        sp500_monthly_returns : pd.Series
            Monthly simple returns for SPY / S&P 500 (e.g. 0.02 = +2 %).
            Index should be month-end dates.

        Returns
        -------
        pd.DataFrame
            Columns: ``date``, ``avi_score``, ``allocation``,
            ``portfolio_return``, ``cumulative_return``.
        """
        # Align on common dates
        common_dates = avi_series.index.intersection(sp500_monthly_returns.index)
        common_dates = common_dates.sort_values()

        if len(common_dates) < 2:
            logger.warning("Insufficient overlapping dates for portfolio simulation")
            return pd.DataFrame(
                columns=["date", "avi_score", "allocation",
                         "portfolio_return", "cumulative_return"]
            )

        rows: list[dict] = []
        cumulative = 1.0

        # For month i, the allocation is based on the AVI of month i-1
        # (signal at end of month i-1 determines allocation for month i).
        for idx in range(1, len(common_dates)):
            signal_date = common_dates[idx - 1]
            return_date = common_dates[idx]

            avi_score = float(avi_series.loc[signal_date])
            allocation = self._get_allocation(avi_score)
            mkt_return = float(sp500_monthly_returns.loc[return_date])

            # Portfolio return: equity portion earns market return, cash earns 0
            port_return = allocation * mkt_return
            cumulative *= (1.0 + port_return)

            rows.append({
                "date": return_date,
                "avi_score": avi_score,
                "allocation": allocation,
                "portfolio_return": port_return,
                "cumulative_return": cumulative,
            })

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        logger.info(
            f"Portfolio simulation: {len(df)} months, "
            f"final cumulative return = {cumulative:.2%}"
        )
        return df
