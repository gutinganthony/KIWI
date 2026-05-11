"""Translate regime state into AVI score adjustments.

Given a base AVI V4 score and the current regime state (from
``RegimeEngine.predict_current``), produces the regime-adjusted AVI
along with a transition risk premium.
"""

import logging

logger = logging.getLogger(__name__)


def compute_regime_adjustment(
    base_avi: float,
    regime_state: dict,
    transition_risk_weight: float = 0.5,
) -> dict:
    """Compute regime-based AVI adjustment.

    Parameters
    ----------
    base_avi : float
        Raw AVI V4 score (0--10).
    regime_state : dict
        Output from ``RegimeEngine.predict_current()``, containing:
        ``label``, ``probabilities``, ``multiplier``.
    transition_risk_weight : float
        Weight applied to P(risk_off) to form the transition premium.
        Default 0.5 per architecture spec.

    Returns
    -------
    dict
        ``adjusted_avi``      -- AVI after regime multiplier
        ``multiplier``        -- regime multiplier applied
        ``transition_premium``-- P(risk_off | current) * weight
        ``regime_label``      -- current regime label
    """
    label: str = regime_state.get("label", "calm_trend")
    multiplier: float = regime_state.get("multiplier", 1.0)
    probabilities: dict[str, float] = regime_state.get("probabilities", {})

    # Multiplicative adjustment
    adjusted_avi = base_avi * multiplier

    # Transition risk premium: probability of being in / transitioning to
    # risk_off, weighted by the risk weight parameter.
    p_risk_off = probabilities.get("risk_off", 0.0)
    transition_premium = p_risk_off * transition_risk_weight

    logger.debug(
        f"Regime adjustment: {base_avi:.2f} * {multiplier:.2f} = {adjusted_avi:.2f}, "
        f"transition_premium={transition_premium:.3f} "
        f"(P(risk_off)={p_risk_off:.3f}), regime={label}"
    )

    return {
        "adjusted_avi": adjusted_avi,
        "multiplier": multiplier,
        "transition_premium": transition_premium,
        "regime_label": label,
    }
