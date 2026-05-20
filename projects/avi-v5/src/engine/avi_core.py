"""AVI V4 core computation engine."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yaml

from .percentile import rolling_percentile

logger = logging.getLogger(__name__)

# Default config paths
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
INDICATORS_CONFIG = CONFIG_DIR / "indicators.yaml"
WEIGHTS_CONFIG = CONFIG_DIR / "avi_weights.yaml"


@dataclass
class IndicatorScore:
    """Score details for a single indicator."""

    name: str
    key: str
    dimension: str
    raw_value: float
    percentile: float  # 0.0 to 1.0
    direction: str
    adjusted_percentile: float  # After direction adjustment
    weight: float
    weighted_contribution: float  # adjusted_percentile * weight * 10


@dataclass
class DimensionScore:
    """Aggregated score for a dimension."""

    name: str
    score: float  # 0-10 scale
    weight: float
    weighted_contribution: float
    indicators: list[IndicatorScore] = field(default_factory=list)


@dataclass
class AVIResult:
    """Complete AVI computation result."""

    total_score: float  # 0-10 composite score
    as_of_date: datetime
    dimension_scores: dict[str, DimensionScore]
    indicator_scores: dict[str, IndicatorScore]
    indicators_available: int
    indicators_total: int

    def summary(self) -> str:
        """Format a human-readable summary of the AVI result."""
        lines = [
            f"{'='*60}",
            f"  AVI V4 Score: {self.total_score:.2f} / 10.0",
            f"  As of: {self.as_of_date.strftime('%Y-%m-%d')}",
            f"  Indicators: {self.indicators_available}/{self.indicators_total}",
            f"{'='*60}",
            "",
            "  Dimension Breakdown:",
            f"  {'Dimension':<15} {'Score':>6} {'Weight':>7} {'Contrib':>8}",
            f"  {'-'*40}",
        ]
        for dim_key, dim in sorted(
            self.dimension_scores.items(), key=lambda x: -x[1].weighted_contribution
        ):
            lines.append(
                f"  {dim.name:<15} {dim.score:>6.2f} {dim.weight*100:>6.1f}% "
                f"{dim.weighted_contribution:>7.3f}"
            )
        lines.append("")
        lines.append("  Top Contributing Indicators:")
        lines.append(
            f"  {'Indicator':<25} {'Pctile':>7} {'Dir':>6} "
            f"{'AdjPct':>7} {'Wt':>5} {'Contrib':>7}"
        )
        lines.append(f"  {'-'*60}")

        sorted_indicators = sorted(
            self.indicator_scores.values(),
            key=lambda x: -x.weighted_contribution,
        )
        for ind in sorted_indicators:
            dir_symbol = "+" if ind.direction == "up_is_risk" else "-"
            lines.append(
                f"  {ind.key:<25} {ind.percentile:>6.1%} {dir_symbol:>6} "
                f"{ind.adjusted_percentile:>6.1%} {ind.weight*100:>4.0f}% "
                f"{ind.weighted_contribution:>7.3f}"
            )

        lines.append("")
        lines.append(f"  Interpretation: {self._interpret()}")
        lines.append(f"{'='*60}")
        return "\n".join(lines)

    def _interpret(self) -> str:
        """Interpret the AVI score."""
        if self.total_score < 3.0:
            return "LOW RISK - Market is cheap / undervalued"
        elif self.total_score < 5.0:
            return "NEUTRAL - Fair value / moderate risk"
        elif self.total_score < 7.0:
            return "ELEVATED - Caution warranted"
        elif self.total_score < 8.0:
            return "HIGH RISK - Significant overvaluation"
        else:
            return "EXTREME RISK - Historical extremes"


class AVIEngine:
    """Core AVI V4 computation engine.

    Takes indicator data (dict of pd.Series), applies:
    1. Rolling 20-year percentile scoring
    2. Direction adjustment (up_is_risk vs up_is_safe)
    3. Weighted aggregation across dimensions

    Produces a 0-10 composite score.
    """

    def __init__(
        self,
        indicators_config_path: Optional[Path] = None,
        weights_config_path: Optional[Path] = None,
    ) -> None:
        """Initialize engine with configuration.

        Args:
            indicators_config_path: Path to indicators.yaml.
            weights_config_path: Path to avi_weights.yaml.
        """
        ind_path = indicators_config_path or INDICATORS_CONFIG
        wt_path = weights_config_path or WEIGHTS_CONFIG

        with open(ind_path) as f:
            self._indicators_cfg: dict[str, Any] = yaml.safe_load(f)["indicators"]

        with open(wt_path) as f:
            weights_data = yaml.safe_load(f)
            self._dimensions_cfg: dict[str, Any] = weights_data["dimensions"]
            self._scoring_cfg: dict[str, Any] = weights_data["scoring"]

        self._window_months: int = self._scoring_cfg["percentile_window_months"]

    def compute(
        self,
        indicator_data: dict[str, pd.Series],
        as_of_date: Optional[str] = None,
    ) -> AVIResult:
        """Compute AVI V4 score from indicator data.

        Args:
            indicator_data: Dict mapping indicator key -> monthly pd.Series.
            as_of_date: Date to compute score for (YYYY-MM-DD).
                        If None, uses the latest date with data.

        Returns:
            AVIResult with total score, dimension scores, and indicator details.
        """
        # Determine as-of date
        if as_of_date:
            target_date = pd.to_datetime(as_of_date)
        else:
            # Use the latest common date across available indicators
            latest_dates = [s.index[-1] for s in indicator_data.values() if len(s) > 0]
            if not latest_dates:
                raise ValueError("No indicator data available")
            target_date = min(latest_dates)  # Conservative: use earliest "latest"

        logger.info(f"Computing AVI as of {target_date.date()}")

        # Score each indicator
        indicator_scores: dict[str, IndicatorScore] = {}
        dimension_contributions: dict[str, list[IndicatorScore]] = {
            dim: [] for dim in self._dimensions_cfg
        }

        for key, cfg in self._indicators_cfg.items():
            if key not in indicator_data:
                logger.debug(f"  Skipping {key}: no data available")
                continue

            series = indicator_data[key]

            # Ensure we have data up to target date
            series_to_date = series[series.index <= target_date]
            min_periods = 60  # 5 years minimum for expanding window
            if len(series_to_date) < min_periods:
                logger.debug(
                    f"  Skipping {key}: insufficient history "
                    f"({len(series_to_date)} < {min_periods})"
                )
                continue

            # Compute rolling percentile (expanding window for early periods)
            pctile_series = rolling_percentile(
                series_to_date, self._window_months, min_periods=min_periods
            )

            # Get the percentile at target date (or closest prior)
            valid_pctiles = pctile_series.dropna()
            if valid_pctiles.empty:
                logger.debug(f"  Skipping {key}: no valid percentiles")
                continue

            # Find closest date <= target_date
            valid_at_target = valid_pctiles[valid_pctiles.index <= target_date]
            if valid_at_target.empty:
                continue

            percentile_value = valid_at_target.iloc[-1]
            raw_value = series_to_date.iloc[-1]

            # Apply direction logic
            direction = cfg["direction"]
            if direction == "up_is_risk":
                # Higher percentile = higher risk = higher AVI score
                adjusted_percentile = percentile_value
            else:  # up_is_safe
                # Higher percentile = lower risk = invert for AVI
                adjusted_percentile = 1.0 - percentile_value

            weight = cfg["weight"]
            # Contribution to AVI score (0-10 scale)
            weighted_contribution = adjusted_percentile * weight * 10.0

            score = IndicatorScore(
                name=cfg["name"],
                key=key,
                dimension=cfg["dimension"],
                raw_value=float(raw_value),
                percentile=float(percentile_value),
                direction=direction,
                adjusted_percentile=float(adjusted_percentile),
                weight=weight,
                weighted_contribution=weighted_contribution,
            )
            indicator_scores[key] = score
            dimension_contributions[cfg["dimension"]].append(score)

        # Aggregate by dimension
        dimension_scores: dict[str, DimensionScore] = {}
        total_score = 0.0

        for dim_key, dim_cfg in self._dimensions_cfg.items():
            indicators_in_dim = dimension_contributions.get(dim_key, [])
            dim_weight = dim_cfg["total_weight"]

            if indicators_in_dim:
                # Dimension score = weighted average of its indicators, scaled to 0-10
                dim_weighted_sum = sum(
                    ind.adjusted_percentile * ind.weight for ind in indicators_in_dim
                )
                actual_weight_sum = sum(ind.weight for ind in indicators_in_dim)

                if actual_weight_sum > 0:
                    # Normalize: if some indicators missing, scale up remaining
                    dim_score = (dim_weighted_sum / actual_weight_sum) * 10.0
                else:
                    dim_score = 5.0  # Neutral if no data

                dim_contribution = sum(
                    ind.weighted_contribution for ind in indicators_in_dim
                )
            else:
                dim_score = 5.0  # Neutral default
                dim_contribution = 0.0

            dimension_scores[dim_key] = DimensionScore(
                name=dim_cfg["name"],
                score=dim_score,
                weight=dim_weight,
                weighted_contribution=dim_contribution,
                indicators=indicators_in_dim,
            )
            total_score += dim_contribution

        # Clip to [0, 10]
        total_score = max(0.0, min(10.0, total_score))

        result = AVIResult(
            total_score=total_score,
            as_of_date=target_date.to_pydatetime(),
            dimension_scores=dimension_scores,
            indicator_scores=indicator_scores,
            indicators_available=len(indicator_scores),
            indicators_total=len(self._indicators_cfg),
        )

        logger.info(f"AVI Score: {result.total_score:.2f}")
        return result
