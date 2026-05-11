"""Signal generators for AVI backtest comparison.

Produces monthly AVI time series for three model versions:
  - V4:   Base AVI (14 indicators, rolling percentile, weighted sum)
  - V4.1: V4 + Markov regime adjustment
  - V4.2: V4 + Regime + GARCH adjustment (full V5 composite)

Each generator iterates month-by-month using only data available up to
that month (no look-ahead bias).  This is intentionally slow for
accuracy; progress is logged every 12 months.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import yaml

# Ensure project root is on sys.path so ``from src.…`` works regardless
# of how this module is imported.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.engine.avi_core import AVIEngine
from src.engine.percentile import rolling_percentile
from src.garch.garch_model import GARCHEngine
from src.garch.vix_comparison import garch_adjustment
from src.regime.feature_builder import build_regime_features
from src.regime.regime_adjustment import compute_regime_adjustment
from src.regime.regime_engine import RegimeEngine

logger = logging.getLogger(__name__)

# Window sizes
_FULL_WINDOW = 240           # Standard 20-year percentile window
_MIN_EXPANDING_WINDOW = 60   # Minimum 5 years before we produce a score

# Config paths (for the manual percentile-based scorer)
_CONFIG_DIR = _PROJECT_ROOT / "config"
_INDICATORS_CFG = _CONFIG_DIR / "indicators.yaml"
_WEIGHTS_CFG = _CONFIG_DIR / "avi_weights.yaml"


def _load_indicator_config() -> tuple[dict[str, Any], dict[str, Any]]:
    """Load indicators.yaml and avi_weights.yaml config dicts."""
    with open(_INDICATORS_CFG) as f:
        ind_cfg = yaml.safe_load(f)["indicators"]
    with open(_WEIGHTS_CFG) as f:
        wt_data = yaml.safe_load(f)
        dim_cfg = wt_data["dimensions"]
    return ind_cfg, dim_cfg


# Cache config at module level (loaded once)
_IND_CFG: Optional[dict] = None
_DIM_CFG: Optional[dict] = None


def _get_config() -> tuple[dict[str, Any], dict[str, Any]]:
    global _IND_CFG, _DIM_CFG
    if _IND_CFG is None:
        _IND_CFG, _DIM_CFG = _load_indicator_config()
    return _IND_CFG, _DIM_CFG


def _month_range(start: str, end: str) -> pd.DatetimeIndex:
    """Generate month-end dates between *start* and *end* (inclusive)."""
    return pd.date_range(start=start, end=end, freq="ME")


def _expanding_percentile(series: pd.Series, min_window: int = _MIN_EXPANDING_WINDOW) -> pd.Series:
    """Percentile using an expanding window.

    For each point i, the percentile is computed over [0..i-1].
    Only produces values for i >= min_window.
    """
    values = series.values
    n = len(values)
    pctiles = np.full(n, np.nan)

    for i in range(min_window, n):
        window = values[:i]
        current = values[i]
        rank = np.sum(window < current) / len(window)
        pctiles[i] = rank

    return pd.Series(pctiles, index=series.index)


def _compute_avi_at_date(
    indicator_data: dict[str, pd.Series],
    engine: AVIEngine,
    as_of: pd.Timestamp,
) -> Optional[float]:
    """Compute an AVI V4 score as of *as_of*.

    For dates where the standard 240-month rolling window is available,
    delegates to the engine directly.  For earlier dates (expanding
    window period), computes the score manually using expanding
    percentiles, mirroring the engine's logic but relaxing the window
    requirement.

    Returns ``None`` if insufficient data.
    """
    ind_cfg, dim_cfg = _get_config()

    # First, try the standard engine (fast path).
    # Check if we have at least one indicator with a full 240-month window.
    has_full = False
    for key, series in indicator_data.items():
        s = series[series.index <= as_of]
        if len(s) >= _FULL_WINDOW:
            has_full = True
            break

    if has_full:
        # The engine can handle this date for indicators with enough data.
        truncated: dict[str, pd.Series] = {}
        for key, series in indicator_data.items():
            s = series[series.index <= as_of]
            if len(s) >= _FULL_WINDOW:
                truncated[key] = s
        if truncated:
            try:
                result = engine.compute(truncated, as_of_date=as_of.strftime("%Y-%m-%d"))
                return result.total_score
            except Exception as exc:
                logger.debug(f"Engine compute failed at {as_of.date()}: {exc}")

    # Expanding-window fallback for early dates (or if engine failed).
    total_score = 0.0
    total_weight_available = 0.0

    for key, cfg in ind_cfg.items():
        if key not in indicator_data:
            continue

        series = indicator_data[key]
        s = series[series.index <= as_of]

        if len(s) < _MIN_EXPANDING_WINDOW:
            continue

        # Choose window: full rolling if enough data, else expanding
        if len(s) >= _FULL_WINDOW:
            pctile_series = rolling_percentile(s, _FULL_WINDOW)
        else:
            pctile_series = _expanding_percentile(s, _MIN_EXPANDING_WINDOW)

        valid = pctile_series.dropna()
        valid_at_target = valid[valid.index <= as_of]
        if valid_at_target.empty:
            continue

        percentile_value = float(valid_at_target.iloc[-1])

        # Apply direction
        direction = cfg["direction"]
        if direction == "up_is_risk":
            adj_pctile = percentile_value
        else:
            adj_pctile = 1.0 - percentile_value

        weight = cfg["weight"]
        contribution = adj_pctile * weight * 10.0

        total_score += contribution
        total_weight_available += weight

    if total_weight_available == 0:
        return None

    # Normalize: if not all indicators available, scale proportionally
    # so the score remains on a 0-10 scale.
    # The engine does this per-dimension; here we do a simpler global
    # normalization for the expanding-window case.
    normalized_score = total_score / total_weight_available * 1.0
    # total_score is already sum(adj_pctile * weight * 10), and if all
    # weights summed to 1.0 the max would be 10.0.  When some are
    # missing we need to rescale: effective_max = total_weight_available * 10.
    # We want the score on the same scale as if all were present.
    # Actually the score is already correct if we just return it, because
    # each contribution is adj_pctile * weight * 10.  The sum when all
    # weights sum to 1.0 gives a 0-10 range.  If some are missing the
    # sum is lower but the conceptual range is also lower.  The engine
    # normalizes per dimension; for simplicity here, rescale globally.
    if total_weight_available < 0.99:
        # Rescale to full-weight equivalent
        total_score = total_score / total_weight_available

    return float(max(0.0, min(10.0, total_score)))


# ─────────────────────────────────────────────────────────────────────
# V4 signal
# ─────────────────────────────────────────────────────────────────────

def generate_v4_signal(
    indicator_histories: dict[str, pd.Series],
    engine: AVIEngine,
    start: str,
    end: str,
) -> pd.Series:
    """Compute AVI V4 for each month in [start, end].

    Parameters
    ----------
    indicator_histories : dict[str, pd.Series]
        Full historical series for each indicator (pre-fetched).
    engine : AVIEngine
        Configured V4 engine.
    start, end : str
        Date range (YYYY-MM-DD).

    Returns
    -------
    pd.Series
        Monthly AVI V4 scores indexed by month-end date.
    """
    months = _month_range(start, end)
    scores: dict[pd.Timestamp, float] = {}

    logger.info(f"Generating V4 signal: {months[0].date()} -> {months[-1].date()} "
                f"({len(months)} months)")

    for i, m in enumerate(months):
        score = _compute_avi_at_date(indicator_histories, engine, m)
        if score is not None:
            scores[m] = score

        if (i + 1) % 12 == 0 or i == len(months) - 1:
            logger.info(f"  V4 progress: {i + 1}/{len(months)} months")

    result = pd.Series(scores, name="avi_v4")
    result.index.name = "date"
    return result.sort_index()


# ─────────────────────────────────────────────────────────────────────
# V4.1 signal  (V4 + Regime)
# ─────────────────────────────────────────────────────────────────────

def generate_v41_signal(
    indicator_histories: dict[str, pd.Series],
    engine: AVIEngine,
    sp500_daily: pd.DataFrame,
    vix_series: pd.Series,
    credit_series: pd.Series,
    start: str,
    end: str,
) -> pd.Series:
    """Compute AVI V4.1 (V4 + regime adjustment) for each month.

    For every month M the HMM is fit on an expanding window of feature
    data up to M, then the regime multiplier and transition premium are
    applied to the base V4 score.

    Parameters
    ----------
    indicator_histories : dict[str, pd.Series]
        Full historical indicators.
    engine : AVIEngine
        Configured V4 engine.
    sp500_daily : pd.DataFrame
        Daily S&P 500 with ``close`` column (full history).
    vix_series : pd.Series
        Daily VIX levels (full history).
    credit_series : pd.Series
        Daily BAA-10Y credit spread (full history).
    start, end : str
        Date range.

    Returns
    -------
    pd.Series
        Monthly AVI V4.1 scores.
    """
    months = _month_range(start, end)
    scores: dict[pd.Timestamp, float] = {}

    logger.info(f"Generating V4.1 signal: {months[0].date()} -> {months[-1].date()} "
                f"({len(months)} months)")

    for i, m in enumerate(months):
        # --- Base V4 score ---
        v4_score = _compute_avi_at_date(indicator_histories, engine, m)
        if v4_score is None:
            continue

        # --- Regime adjustment (expanding window up to month M) ---
        try:
            sp_to_m = sp500_daily[sp500_daily.index <= m]
            vix_to_m = vix_series[vix_series.index <= m]
            credit_to_m = credit_series[credit_series.index <= m]

            if len(sp_to_m) < 252 or len(vix_to_m) < 60:
                # Not enough daily data for regime features
                scores[m] = v4_score
                continue

            features = build_regime_features(sp_to_m, vix_to_m, credit_to_m)
            if features.empty or len(features) < 12:
                scores[m] = v4_score
                continue

            regime_engine = RegimeEngine(n_regimes=4)
            regime_engine.fit(features)
            regime_state = regime_engine.predict_current(features)

            regime_adj = compute_regime_adjustment(
                v4_score, regime_state, transition_risk_weight=0.5
            )

            adjusted = v4_score * regime_adj["multiplier"] + regime_adj["transition_premium"]
            scores[m] = float(np.clip(adjusted, 0.0, 10.0))

        except Exception as exc:
            logger.debug(f"V4.1 regime failed at {m.date()}: {exc}")
            scores[m] = v4_score

        if (i + 1) % 12 == 0 or i == len(months) - 1:
            logger.info(f"  V4.1 progress: {i + 1}/{len(months)} months")

    result = pd.Series(scores, name="avi_v41")
    result.index.name = "date"
    return result.sort_index()


# ─────────────────────────────────────────────────────────────────────
# V4.2 signal  (V4 + Regime + GARCH — full V5)
# ─────────────────────────────────────────────────────────────────────

def generate_v42_signal(
    indicator_histories: dict[str, pd.Series],
    engine: AVIEngine,
    sp500_daily: pd.DataFrame,
    vix_series: pd.Series,
    credit_series: pd.Series,
    start: str,
    end: str,
) -> pd.Series:
    """Compute AVI V4.2 (V4 + regime + GARCH) for each month.

    Full V5 composite formula applied month-by-month:
        V4.2 = clip(V4 * regime_mult + garch_adj + transition_premium, 0, 10)

    Parameters
    ----------
    indicator_histories : dict[str, pd.Series]
        Full historical indicators.
    engine : AVIEngine
        Configured V4 engine.
    sp500_daily : pd.DataFrame
        Daily S&P 500 with ``close`` column (full history).
    vix_series : pd.Series
        Daily VIX levels (full history).
    credit_series : pd.Series
        Daily BAA-10Y credit spread (full history).
    start, end : str
        Date range.

    Returns
    -------
    pd.Series
        Monthly AVI V4.2 scores.
    """
    months = _month_range(start, end)
    scores: dict[pd.Timestamp, float] = {}

    logger.info(f"Generating V4.2 signal: {months[0].date()} -> {months[-1].date()} "
                f"({len(months)} months)")

    for i, m in enumerate(months):
        # --- Base V4 score ---
        v4_score = _compute_avi_at_date(indicator_histories, engine, m)
        if v4_score is None:
            continue

        # --- Regime adjustment ---
        regime_mult = 1.0
        transition_premium = 0.0
        try:
            sp_to_m = sp500_daily[sp500_daily.index <= m]
            vix_to_m = vix_series[vix_series.index <= m]
            credit_to_m = credit_series[credit_series.index <= m]

            if len(sp_to_m) >= 252 and len(vix_to_m) >= 60:
                features = build_regime_features(sp_to_m, vix_to_m, credit_to_m)
                if not features.empty and len(features) >= 12:
                    regime_engine = RegimeEngine(n_regimes=4)
                    regime_engine.fit(features)
                    regime_state = regime_engine.predict_current(features)
                    regime_adj = compute_regime_adjustment(
                        v4_score, regime_state, transition_risk_weight=0.5
                    )
                    regime_mult = regime_adj["multiplier"]
                    transition_premium = regime_adj["transition_premium"]
        except Exception as exc:
            logger.debug(f"V4.2 regime failed at {m.date()}: {exc}")

        # --- GARCH adjustment ---
        garch_adj = 0.0
        try:
            sp_to_m = sp500_daily[sp500_daily.index <= m]
            if len(sp_to_m) >= 504:  # ~2 years of daily data minimum
                daily_returns = sp_to_m["close"].pct_change().dropna()
                garch_eng = GARCHEngine(p=1, q=1, dist="studentst")
                garch_eng.fit(daily_returns)

                garch_vol = garch_eng.forecast_volatility(horizon=21)

                # Current VIX (last value available up to month M)
                vix_to_m = vix_series[vix_series.index <= m]
                if not vix_to_m.empty and not np.isnan(garch_vol):
                    vix_current = float(vix_to_m.iloc[-1]) / 100.0  # VIX is in pct points
                    if vix_current > 0:
                        garch_adj = garch_adjustment(
                            garch_vol, vix_current,
                            scale=0.3, max_adj=0.5,
                        )
        except Exception as exc:
            logger.debug(f"V4.2 GARCH failed at {m.date()}: {exc}")

        # --- Composite ---
        raw = v4_score * regime_mult + garch_adj + transition_premium
        scores[m] = float(np.clip(raw, 0.0, 10.0))

        if (i + 1) % 12 == 0 or i == len(months) - 1:
            logger.info(f"  V4.2 progress: {i + 1}/{len(months)} months")

    result = pd.Series(scores, name="avi_v42")
    result.index.name = "date"
    return result.sort_index()
