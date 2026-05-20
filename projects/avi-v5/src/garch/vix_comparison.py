"""Compare GARCH volatility forecast against implied volatility (VIX).

Provides two functions:
- ``vol_gap_signal`` -- raw gap between GARCH and VIX
- ``garch_adjustment`` -- clipped adjustment suitable for direct AVI addition
"""

import logging

logger = logging.getLogger(__name__)


def vol_gap_signal(garch_forecast: float, vix_current: float) -> float:
    """Compute the relative gap between GARCH forecast and VIX.

    A **positive** value means the GARCH model forecasts higher
    volatility than the market is pricing (VIX), suggesting the
    market is **under-pricing risk**.

    Parameters
    ----------
    garch_forecast : float
        Annualized volatility from the GARCH model (decimal, e.g. 0.20).
    vix_current : float
        Current VIX level expressed as a decimal (e.g. 0.18).
        If raw VIX is in percentage points (e.g. 18.0), the caller
        must divide by 100 before passing.

    Returns
    -------
    float
        ``(garch_forecast - vix_current) / vix_current``.
        Returns 0.0 if *vix_current* is zero or either input is NaN.
    """
    import math

    if math.isnan(garch_forecast) or math.isnan(vix_current) or vix_current == 0.0:
        return 0.0

    return (garch_forecast - vix_current) / vix_current


def garch_adjustment(
    garch_forecast: float,
    vix_current: float,
    scale: float = 0.3,
    max_adj: float = 0.5,
) -> float:
    """Compute clamped AVI adjustment from the GARCH / VIX gap.

    Positive adjustment means *adding* risk to AVI (GARCH sees more
    vol than VIX); negative means *reducing* risk.

    Parameters
    ----------
    garch_forecast : float
        Annualized GARCH vol (decimal).
    vix_current : float
        Current VIX as decimal.
    scale : float
        Scaling factor applied to the raw vol gap (default 0.3).
    max_adj : float
        Absolute maximum adjustment magnitude (default 0.5).

    Returns
    -------
    float
        ``clip(vol_gap * scale, -max_adj, +max_adj)``.
    """
    gap = vol_gap_signal(garch_forecast, vix_current)
    raw_adj = gap * scale
    clamped = max(-max_adj, min(max_adj, raw_adj))

    logger.debug(
        f"GARCH adj: gap={gap:.3f}, raw={raw_adj:.3f}, clamped={clamped:.3f}"
    )
    return clamped
