"""AVI V5 composite pipeline.

Orchestrates the full pipeline:
    1. Data collection (FRED, Multpl, yfinance)
    2. AVI V4 base score
    3. Regime classification (HMM)
    4. GARCH volatility forecast
    5. Composite V5 score
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yaml

from ..data.collector import IndicatorCollector
from ..engine.avi_core import AVIEngine, AVIResult
from ..garch.garch_model import GARCHEngine
from ..garch.vix_comparison import garch_adjustment
from ..regime.feature_builder import build_regime_features
from ..regime.regime_adjustment import compute_regime_adjustment
from ..regime.regime_engine import RegimeEngine

logger = logging.getLogger(__name__)

# Default paths
_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
_REGIME_CONFIG = _CONFIG_DIR / "regime_params.yaml"


@dataclass
class V5Result:
    """Full AVI V5 computation result."""

    # V4 base
    avi_v4_score: float

    # Regime
    regime_label: str
    regime_multiplier: float
    transition_premium: float

    # GARCH
    garch_forecast: float  # annualized vol (decimal)
    garch_persistence: float
    garch_adjustment: float

    # Composite
    avi_v5_score: float

    # Full V4 result for downstream consumers
    v4_result: AVIResult = field(repr=False)

    def summary(self) -> str:
        """Format a human-readable summary of the V5 result."""
        lines = [
            f"{'='*64}",
            f"  AVI V5 Composite Score: {self.avi_v5_score:.2f} / 10.0",
            f"  As of: {self.v4_result.as_of_date.strftime('%Y-%m-%d')}",
            f"{'='*64}",
            "",
            "  Component Breakdown:",
            f"  {'Component':<28} {'Value':>10}",
            f"  {'-'*42}",
            f"  {'AVI V4 Base':<28} {self.avi_v4_score:>10.2f}",
            f"  {'Regime':<28} {self.regime_label:>10}",
            f"  {'  x Multiplier':<28} {self.regime_multiplier:>10.2f}",
            f"  {'  + Transition Premium':<28} {self.transition_premium:>+10.3f}",
            f"  {'GARCH Vol Forecast':<28} {self.garch_forecast * 100:>9.1f}%",
            f"  {'  Persistence (a+b)':<28} {self.garch_persistence:>10.4f}",
            f"  {'  + GARCH Adjustment':<28} {self.garch_adjustment:>+10.3f}",
            f"  {'-'*42}",
            "",
            "  Formula:",
            f"    V5 = clip(V4 * regime_mult + garch_adj + trans_prem, 0, 10)",
            f"       = clip({self.avi_v4_score:.2f} * {self.regime_multiplier:.2f} "
            f"+ {self.garch_adjustment:+.3f} + {self.transition_premium:+.3f}, 0, 10)",
            f"       = {self.avi_v5_score:.2f}",
            "",
            f"  Interpretation: {self._interpret()}",
            f"{'='*64}",
        ]
        return "\n".join(lines)

    def _interpret(self) -> str:
        """Interpret the V5 composite score."""
        s = self.avi_v5_score
        if s < 3.0:
            return "LOW RISK - Market is cheap / undervalued"
        elif s < 5.0:
            return "NEUTRAL - Fair value / moderate risk"
        elif s < 7.0:
            return "ELEVATED - Caution warranted"
        elif s < 8.0:
            return "HIGH RISK - Significant overvaluation"
        else:
            return "EXTREME RISK - Historical extremes"


class AVIV5Pipeline:
    """Full AVI V5 pipeline: data -> V4 -> regime -> GARCH -> composite.

    Parameters
    ----------
    fred_api_key : str or None
        FRED API key.  If *None*, ``IndicatorCollector`` reads from
        the ``FRED_API_KEY`` environment variable.
    config_path : Path or None
        Path to ``regime_params.yaml``.  Uses default if *None*.
    """

    def __init__(
        self,
        fred_api_key: Optional[str] = None,
        config_path: Optional[Path] = None,
    ) -> None:
        self._fred_api_key = fred_api_key
        self._cfg = self._load_config(config_path or _REGIME_CONFIG)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_config(path: Path) -> dict:
        """Load regime_params.yaml."""
        with open(path) as fh:
            return yaml.safe_load(fh)

    def _collect_data(
        self,
        as_of_date: Optional[str],
        start_date: str,
    ) -> tuple[dict[str, pd.Series], pd.DataFrame, pd.Series, pd.Series]:
        """Collect all data needed for the V5 pipeline.

        Returns
        -------
        indicator_data : dict[str, pd.Series]
            Monthly indicators for V4 engine.
        sp500_daily : pd.DataFrame
            Daily S&P 500 with ``close`` column.
        vix_daily : pd.Series
            Daily VIX.
        credit_spread_daily : pd.Series
            Daily BAA-10Y credit spread.
        """
        collector = IndicatorCollector(fred_api_key=self._fred_api_key)

        # Collect monthly indicators for V4
        indicator_data = collector.collect_all(
            as_of_date=as_of_date,
            start_date=start_date,
        )

        # Collect daily data for regime and GARCH engines
        import yfinance as yf

        end = as_of_date or datetime.now().strftime("%Y-%m-%d")

        # S&P 500 daily
        sp500_raw = yf.download(
            "^GSPC", start=start_date, end=end,
            auto_adjust=True, progress=False,
        )
        if isinstance(sp500_raw.columns, pd.MultiIndex):
            sp500_raw.columns = sp500_raw.columns.get_level_values(0)
        sp500_daily = pd.DataFrame(
            {"close": sp500_raw["Close"]},
        )

        # VIX daily via FRED
        vix_daily = collector.fred.fetch_series(
            "VIXCLS", start_date, as_of_date
        ).dropna()

        # Credit spread daily (BAA-10Y)
        credit_spread_daily = collector.fred.fetch_series(
            "BAA10YM", start_date, as_of_date
        ).dropna()

        return indicator_data, sp500_daily, vix_daily, credit_spread_daily

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        as_of_date: Optional[str] = None,
        start_date: str = "2000-01-01",
        verbose: bool = False,
    ) -> V5Result:
        """Execute the full V5 pipeline.

        Parameters
        ----------
        as_of_date : str or None
            Target date (YYYY-MM-DD).  Defaults to latest available.
        start_date : str
            Historical lookback start.
        verbose : bool
            If True, prints intermediate results.

        Returns
        -------
        V5Result
        """
        regime_cfg = self._cfg.get("regime", {})
        garch_cfg = self._cfg.get("garch", {})

        # ----- Step 1: Data collection -----
        logger.info("V5 Step 1/4: Collecting data...")
        indicator_data, sp500_daily, vix_daily, credit_spread = (
            self._collect_data(as_of_date, start_date)
        )

        if not indicator_data:
            raise RuntimeError(
                "No indicator data collected. Check API keys and connectivity."
            )

        # ----- Step 2: AVI V4 base -----
        logger.info("V5 Step 2/4: Computing AVI V4 base score...")
        v4_engine = AVIEngine()
        v4_result = v4_engine.compute(indicator_data, as_of_date=as_of_date)
        avi_v4 = v4_result.total_score

        if verbose:
            print("\n--- AVI V4 Base ---")
            print(v4_result.summary())

        # ----- Step 3: Regime classification -----
        logger.info("V5 Step 3/4: Regime classification...")
        try:
            features = build_regime_features(
                sp500_daily, vix_daily, credit_spread,
            )

            n_regimes = regime_cfg.get("n_regimes", 4)
            regime_engine = RegimeEngine(n_regimes=n_regimes)
            regime_engine.fit(features)
            regime_state = regime_engine.predict_current(features)

            transition_risk_weight = regime_cfg.get("transition_risk_weight", 0.5)
            regime_adj = compute_regime_adjustment(
                avi_v4, regime_state, transition_risk_weight
            )
        except Exception as exc:
            logger.error(f"Regime classification failed: {exc}. Using defaults.")
            regime_state = {
                "label": "calm_trend",
                "probabilities": {"calm_trend": 1.0, "volatile_trend": 0.0,
                                  "chop": 0.0, "risk_off": 0.0},
                "multiplier": 1.0,
            }
            regime_adj = {
                "adjusted_avi": avi_v4,
                "multiplier": 1.0,
                "transition_premium": 0.0,
                "regime_label": "calm_trend",
            }

        regime_label = regime_adj["regime_label"]
        regime_multiplier = regime_adj["multiplier"]
        transition_premium = regime_adj["transition_premium"]

        if verbose:
            print(f"\n--- Regime: {regime_label} (mult={regime_multiplier:.2f}) ---")
            print(f"    Transition premium: {transition_premium:.3f}")
            print(f"    State probs: {regime_state['probabilities']}")

        # ----- Step 4: GARCH volatility forecast -----
        logger.info("V5 Step 4/4: GARCH volatility forecast...")
        try:
            daily_returns = sp500_daily["close"].pct_change().dropna()
            garch_p = garch_cfg.get("p", 1)
            garch_q = garch_cfg.get("q", 1)
            garch_dist = garch_cfg.get("distribution", "studentst")
            forecast_horizon = garch_cfg.get("forecast_horizon", 21)

            garch_engine = GARCHEngine(p=garch_p, q=garch_q, dist=garch_dist)
            garch_engine.fit(daily_returns)

            garch_vol = garch_engine.forecast_volatility(horizon=forecast_horizon)
            garch_pers = garch_engine.persistence

            # VIX as decimal for comparison (VIX is in % points)
            vix_current_raw = float(vix_daily.iloc[-1])
            vix_decimal = vix_current_raw / 100.0

            vol_gap_scale = garch_cfg.get("vol_gap_scale", 0.3)
            max_adj = garch_cfg.get("max_adjustment", 0.5)

            if np.isnan(garch_vol):
                # Fallback: no adjustment
                garch_adj = 0.0
                garch_vol = vix_decimal  # report VIX as forecast
            else:
                garch_adj = garch_adjustment(
                    garch_vol, vix_decimal,
                    scale=vol_gap_scale, max_adj=max_adj,
                )
        except Exception as exc:
            logger.error(f"GARCH forecast failed: {exc}. Using zero adjustment.")
            garch_vol = 0.0
            garch_pers = 0.0
            garch_adj = 0.0

        if np.isnan(garch_pers):
            garch_pers = 0.0

        if verbose:
            print(f"\n--- GARCH ---")
            print(f"    Forecast vol (ann): {garch_vol*100:.1f}%")
            print(f"    Persistence: {garch_pers:.4f}")
            print(f"    Adjustment: {garch_adj:+.3f}")

        # ----- Composite V5 -----
        raw_v5 = avi_v4 * regime_multiplier + garch_adj + transition_premium
        avi_v5 = float(np.clip(raw_v5, 0.0, 10.0))

        result = V5Result(
            avi_v4_score=avi_v4,
            regime_label=regime_label,
            regime_multiplier=regime_multiplier,
            transition_premium=transition_premium,
            garch_forecast=garch_vol,
            garch_persistence=garch_pers,
            garch_adjustment=garch_adj,
            avi_v5_score=avi_v5,
            v4_result=v4_result,
        )

        logger.info(
            f"V5 complete: V4={avi_v4:.2f} -> V5={avi_v5:.2f} "
            f"(regime={regime_label}, garch_adj={garch_adj:+.3f})"
        )
        return result
