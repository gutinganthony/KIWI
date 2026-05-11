"""4-state Hidden Markov Model regime classifier.

Classifies market environments into one of four regimes using a
Gaussian HMM trained on the 6-feature matrix from ``feature_builder``.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM

logger = logging.getLogger(__name__)


class RegimeEngine:
    """HMM-based market regime classifier.

    Regimes (sorted by ascending mean return after fit):
        0  risk_off        -- active drawdown / crisis
        1  chop            -- range-bound, noisy signals
        2  volatile_trend  -- trending but with whipsaw risk
        3  calm_trend      -- low-vol uptrend, neutral risk

    Attributes
    ----------
    REGIME_LABELS : list[str]
        Human-readable labels ordered from lowest to highest mean return.
    MULTIPLIERS : dict[str, float]
        AVI score multipliers per regime.
    """

    REGIME_LABELS: list[str] = [
        "calm_trend",
        "volatile_trend",
        "chop",
        "risk_off",
    ]

    MULTIPLIERS: dict[str, float] = {
        "calm_trend": 1.00,
        "volatile_trend": 1.08,
        "chop": 1.04,
        "risk_off": 1.15,
    }

    def __init__(self, n_regimes: int = 4) -> None:
        """Initialise the regime engine.

        Parameters
        ----------
        n_regimes : int
            Number of hidden states (default 4).
        """
        self._n_regimes = n_regimes
        self._model: Optional[GaussianHMM] = None
        self._sort_map: Optional[dict[int, int]] = None
        self._fitted = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self, features: pd.DataFrame) -> "RegimeEngine":
        """Fit the HMM on the standardized feature matrix.

        Parameters
        ----------
        features : pd.DataFrame
            Monthly standardized features from ``build_regime_features``.

        Returns
        -------
        RegimeEngine
            ``self`` for chaining.
        """
        if features.empty or len(features) < self._n_regimes * 2:
            logger.warning(
                "Insufficient data for HMM fitting "
                f"({len(features)} rows, need >= {self._n_regimes * 2}). "
                "Falling back to calm_trend default."
            )
            self._fitted = False
            return self

        X = features.values

        try:
            model = GaussianHMM(
                n_components=self._n_regimes,
                covariance_type="full",
                n_iter=200,
                random_state=42,
                tol=1e-4,
            )
            model.fit(X)
            self._model = model

            # Build sorting map: order states by mean of the first feature
            # (rolling_return). Lowest mean return -> risk_off (index 0 in
            # sorted order), highest -> calm_trend.
            mean_returns = model.means_[:, 0]  # first feature = rolling return
            sorted_indices = np.argsort(mean_returns)  # ascending

            # Map: raw_state -> sorted_position
            # sorted_indices[0] has the lowest mean return -> label index 3 (risk_off)
            # sorted_indices[-1] has the highest mean return -> label index 0 (calm_trend)
            label_order = list(range(self._n_regimes))[::-1]  # [3, 2, 1, 0]
            self._sort_map = {
                int(raw): label_order[pos]
                for pos, raw in enumerate(sorted_indices)
            }

            self._fitted = True
            logger.info(
                f"HMM fitted successfully ({self._n_regimes} states, "
                f"log-likelihood={model.score(X):.1f})"
            )

        except Exception as exc:
            logger.error(f"HMM fitting failed: {exc}. Falling back to calm_trend.")
            self._fitted = False

        return self

    def predict(self, features: pd.DataFrame) -> pd.Series:
        """Predict regime labels for each row.

        Parameters
        ----------
        features : pd.DataFrame
            Standardized feature matrix (same columns as fit).

        Returns
        -------
        pd.Series
            String regime labels with the same index as *features*.
        """
        if not self._fitted or self._model is None:
            logger.warning("Model not fitted; returning calm_trend for all rows")
            return pd.Series(
                "calm_trend", index=features.index, name="regime"
            )

        raw_states = self._model.predict(features.values)
        sorted_states = np.array([self._sort_map[s] for s in raw_states])
        labels = [self.REGIME_LABELS[s] for s in sorted_states]
        return pd.Series(labels, index=features.index, name="regime")

    def predict_current(self, features: pd.DataFrame) -> dict:
        """Classify the most recent observation and return full state info.

        Parameters
        ----------
        features : pd.DataFrame
            Standardized feature matrix; the **last row** is treated as
            the current observation.

        Returns
        -------
        dict
            ``label``          -- regime label string
            ``probabilities``  -- dict mapping label -> P(state)
            ``multiplier``     -- AVI multiplier for this regime
        """
        if not self._fitted or self._model is None:
            default_label = "calm_trend"
            return {
                "label": default_label,
                "probabilities": {lab: (1.0 if lab == default_label else 0.0)
                                  for lab in self.REGIME_LABELS},
                "multiplier": self.MULTIPLIERS[default_label],
            }

        X = features.values

        # Posterior state probabilities via the forward algorithm
        try:
            _, posteriors = self._model.score_samples(X)
            current_probs = posteriors[-1]  # last row
        except Exception:
            # Fallback: hard prediction
            raw_state = self._model.predict(X)[-1]
            current_probs = np.zeros(self._n_regimes)
            current_probs[raw_state] = 1.0

        # Map probabilities to sorted labels
        sorted_probs: dict[str, float] = {}
        for raw_idx in range(self._n_regimes):
            sorted_idx = self._sort_map[raw_idx]
            label = self.REGIME_LABELS[sorted_idx]
            sorted_probs[label] = float(current_probs[raw_idx])

        # Most likely regime
        best_label = max(sorted_probs, key=sorted_probs.get)  # type: ignore[arg-type]
        multiplier = self.MULTIPLIERS[best_label]

        return {
            "label": best_label,
            "probabilities": sorted_probs,
            "multiplier": multiplier,
        }

    def get_transition_matrix(self) -> np.ndarray:
        """Return the HMM transition matrix with rows/columns sorted by regime.

        Returns
        -------
        np.ndarray
            Shape ``(n_regimes, n_regimes)``; ``T[i, j]`` = P(regime_j | regime_i),
            where row/column order follows ``REGIME_LABELS``.
        """
        if not self._fitted or self._model is None:
            # Return uniform transitions as fallback
            n = self._n_regimes
            return np.ones((n, n)) / n

        raw_trans = self._model.transmat_
        n = self._n_regimes
        sorted_trans = np.zeros((n, n))

        for raw_i in range(n):
            for raw_j in range(n):
                si = self._sort_map[raw_i]
                sj = self._sort_map[raw_j]
                sorted_trans[si, sj] = raw_trans[raw_i, raw_j]

        return sorted_trans
