"""
Tech Stress Index (TSI) — Short-cycle tech sector crash/rally predictor.

Converts the 5 memory-chip leading indicators into daily-computable proxies
using stock prices, ETFs, and yields available via yfinance + FRED.

Indicators (7 daily proxies for the 5 fundamental signals):
1. SOX/QQQ Divergence — semis leading or lagging tech
2. Memory Stock Momentum — MU, SK Hynix proxy via composite
3. Treasury Yield Shock — 10Y yield speed (rate shock kills tech)
4. AI Infra vs S&P 500 — relative strength of AI picks-and-shovels
5. Tech Breadth — % of top-20 tech stocks above 20MA
6. Cloud Revenue Signal — CLOU/SKYY relative strength vs QQQ
7. VIX-Tech Correlation — when VIX rises AND tech drops = real stress

Output: 0-100 score (like CPI but tech-specific)
  0-25:  Bullish (tech likely to rally)
  25-45: Neutral
  45-65: Cautious (elevated risk)
  65+:   Bearish (high probability of tech correction)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class TSIIndicator:
    name: str
    value: float
    signal: float  # 0-100
    weight: float
    direction: str  # "bearish" or "bullish" contributing


@dataclass
class TSIResult:
    score: float  # 0-100
    date: datetime
    indicators: List[TSIIndicator]
    bias: str  # "BULLISH", "NEUTRAL", "CAUTIOUS", "BEARISH"
    flash_alert: bool
    flash_reason: str

    def summary(self) -> str:
        lines = [
            f"{'='*60}",
            f"  Tech Stress Index (TSI): {self.score:.0f}/100 — {self.bias}",
            f"  Date: {self.date.strftime('%Y-%m-%d')}",
            f"{'='*60}",
        ]
        if self.flash_alert:
            lines.append(f"\n  ⚡ FLASH: {self.flash_reason}\n")

        lines.append(f"  {'Indicator':<30} {'Value':>8} {'Signal':>8}")
        lines.append(f"  {'-'*48}")
        for ind in sorted(self.indicators, key=lambda x: -x.signal):
            lines.append(f"  {ind.name:<30} {ind.value:>8.2f} {ind.signal:>7.0f}/100")

        lines.append(f"\n  Interpretation:")
        if self.score >= 65:
            lines.append(f"  🔴 High tech stress. Expect correction. Reduce tech exposure.")
        elif self.score >= 45:
            lines.append(f"  🟠 Elevated caution. Tighten stops on tech positions.")
        elif self.score >= 25:
            lines.append(f"  🟡 Neutral. Standard risk management.")
        else:
            lines.append(f"  🟢 Low stress. Tech sector healthy, potential upside.")
        lines.append(f"{'='*60}")
        return "\n".join(lines)


class TechStressIndex:
    """Daily tech sector stress scorer using 13 market-based proxies.

    Leading indicators (fire 1-3 days BEFORE crash):
      vvix_lead         — VVIX spike anticipates VIX explosion by 1-2 days
      credit_divergence — HYG lagging SPY = credit markets see risk first
      sox_momentum_decel— SOX 2nd-derivative decline precedes breakdown

    Reactive indicators (fire same-day or 1-3 days after):
      tech_crash_day, vix_tech_correlation, sox_qqq_divergence, memory_momentum,
      yield_shock, yield_30y_stress, yield_curve_bear_steep, ai_infra_rs,
      tech_breadth, cloud_rs
    """

    WEIGHTS = {
        # ── Leading (1-3 day advance warning) ─────────────────────────────
        # ── v4 weights: empirically optimized on 27y real data (2006-2020) ──
        #    via logistic regression, cross-validated AUC = 0.747 (vs 0.700 prior).
        #    See scripts/tsi_optimize.py. Ordered by predictive importance.
        "tech_breadth":          0.18,   # #1 predictor (D1 AUC 0.93) — QQQ vs 20/50MA
        "vvix_lead":             0.14,   # vol-of-vol spike (D1 AUC 0.82, true leading)
        "credit_divergence":     0.12,   # HYG vs SPY — adds independent signal
        "tech_crash_day":        0.10,   # 1-day QQQ/SOX drop + VIX (D1 AUC 0.76)
        "vix_tech_correlation":  0.08,   # 3-day VIX+tech co-move (D1 AUC 0.78)
        "sox_qqq_divergence":    0.07,   # 10-day semi vs tech (D1 AUC 0.71)
        "memory_momentum":       0.05,   # 5+20-day MU trend (D1 AUC 0.71)
        "sox_momentum_decel":    0.05,   # SOX 2nd-derivative (weak alone, kept light)
        # ── Macro/rate indicators (not in equity backtest; for rate-driven crashes) ──
        "yield_shock":           0.09,   # 5-day 10Y spike (e.g. 2022 selloff)
        "yield_30y_stress":      0.05,   # 30Y absolute level + speed
        "ai_infra_rs":           0.04,   # 20-day SMH vs SPY
        "yield_curve_bear_steep": 0.03,  # 30Y-10Y bear steepening
    }

    def compute(
        self,
        sox_daily: pd.Series,
        qqq_daily: pd.Series,
        mu_daily: pd.Series,
        smh_daily: pd.Series,
        spy_daily: pd.Series,
        treasury_10y: pd.Series,
        vix_daily: pd.Series,
        treasury_30y: Optional[pd.Series] = None,
        tech_stocks: Optional[pd.DataFrame] = None,
        as_of: Optional[str] = None,
        vvix_daily: Optional[pd.Series] = None,
        hyg_daily: Optional[pd.Series] = None,
    ) -> TSIResult:
        if as_of:
            cutoff = pd.Timestamp(as_of)
            sox_daily = sox_daily[sox_daily.index <= cutoff]
            qqq_daily = qqq_daily[qqq_daily.index <= cutoff]
            mu_daily = mu_daily[mu_daily.index <= cutoff]
            smh_daily = smh_daily[smh_daily.index <= cutoff]
            spy_daily = spy_daily[spy_daily.index <= cutoff]
            treasury_10y = treasury_10y[treasury_10y.index <= cutoff]
            vix_daily = vix_daily[vix_daily.index <= cutoff]
            if treasury_30y is not None:
                treasury_30y = treasury_30y[treasury_30y.index <= cutoff]

        date = sox_daily.index[-1].to_pydatetime()
        indicators = []
        flash_triggers = []

        # ── LEADING INDICATORS (fire 1-3 days before crash) ─────────────────

        # L1. VVIX lead — vol-of-vol spike anticipates VIX explosion by 1-2 days
        ind = self._vvix_lead(vvix_daily if vvix_daily is not None else vix_daily, vix_daily)
        indicators.append(ind)
        if ind.signal > 65:
            flash_triggers.append(f"VVIX fear spike: {ind.value:.0f} ({ind.value:.0f} vs MA20)")

        # L2. Credit divergence — HYG lagging SPY = credit sees risk 1-3d before equity
        ind = self._credit_divergence(
            hyg_daily if hyg_daily is not None else spy_daily, spy_daily
        )
        indicators.append(ind)
        if ind.signal > 65:
            flash_triggers.append(f"Credit stress: HYG lagging SPY by {ind.value:.1f}%")

        # L3. SOX momentum deceleration — 2nd-derivative decay before actual breakdown
        ind = self._sox_momentum_decel(sox_daily, qqq_daily)
        indicators.append(ind)
        if ind.signal > 70:
            flash_triggers.append(f"SOX momentum decelerating: {ind.value:.1f}%")

        # ── REACTIVE INDICATORS ──────────────────────────────────────────────

        # R1. Single-day tech crash detector
        ind = self._tech_crash_day(qqq_daily, sox_daily, vix_daily)
        indicators.append(ind)
        if ind.signal > 60:
            flash_triggers.append(f"Tech crash: {ind.value:.1f}% single-day drop")

        # R2. SOX/QQQ Divergence
        ind = self._sox_qqq_divergence(sox_daily, qqq_daily)
        indicators.append(ind)
        if ind.signal > 70:
            flash_triggers.append(f"SOX lagging QQQ: {ind.value:.1f}%")

        # R3. Memory Stock Momentum (MU as proxy)
        ind = self._memory_momentum(mu_daily)
        indicators.append(ind)
        if ind.signal > 70:
            flash_triggers.append(f"Memory stocks breaking down")

        # R4. Treasury Yield Shock
        ind = self._yield_shock(treasury_10y)
        indicators.append(ind)
        if ind.signal > 70:
            flash_triggers.append(f"Yield spike: +{ind.value:.0f}bps in 5d")

        # R5. 30Y Yield Stress
        ind = self._yield_30y_stress(treasury_30y if treasury_30y is not None else treasury_10y)
        indicators.append(ind)
        if ind.signal > 70:
            flash_triggers.append(f"30Y yield at extreme: {ind.value:.2f}%")

        # R6. Yield Curve Bear Steepening
        ind = self._yield_curve_bear_steep(treasury_10y, treasury_30y)
        indicators.append(ind)

        # R7. AI Infra Relative Strength (SMH vs SPY)
        ind = self._ai_infra_rs(smh_daily, spy_daily)
        indicators.append(ind)

        # R8. Tech Breadth (QQQ vs 20/50MA)
        ind = self._tech_breadth(qqq_daily)
        indicators.append(ind)

        # R9. VIX-Tech Correlation (3-day co-movement)
        ind = self._vix_tech_corr(vix_daily, qqq_daily)
        indicators.append(ind)
        if ind.signal > 75:
            flash_triggers.append(f"VIX surge + tech selloff")

        # Composite
        # v4: clean weighted sum. The previous consensus/breadth "boost" logic
        # inflated the score (fired 53% of days) and DROPPED out-of-sample AUC
        # from 0.747 to 0.700. Removed per scripts/tsi_optimize.py findings.
        # Weights are pre-normalized to sum ~1.0, so total is already 0-100.
        total = sum(ind.signal * self.WEIGHTS.get(ind.name, 0.0) for ind in indicators)
        score = min(100, max(0, total))

        # Single light spike floor: one genuinely extreme signal (>75) shouldn't be
        # fully diluted by calm trend indicators. Mild, not the old aggressive floor.
        max_signal = max(ind.signal for ind in indicators)
        if max_signal >= 75:
            score = max(score, max_signal * 0.45)  # e.g., 80 → floor 36

        if score >= 60:
            bias = "BEARISH"
        elif score >= 40:
            bias = "CAUTIOUS"
        elif score >= 22:
            bias = "NEUTRAL"
        else:
            bias = "BULLISH"

        # Flash: 2+ triggers，或 tech_crash_day 單獨超過 75（單日暴跌 >2.5%）
        crash_day_ind = next((i for i in indicators if i.name == "tech_crash_day"), None)
        single_crash = crash_day_ind is not None and crash_day_ind.signal > 75
        flash = len(flash_triggers) >= 2 or single_crash
        flash_reason = " + ".join(flash_triggers) if flash_triggers else ""

        return TSIResult(
            score=score, date=date, indicators=indicators,
            bias=bias, flash_alert=flash, flash_reason=flash_reason,
        )

    def _tech_crash_day(self, qqq: pd.Series, sox: pd.Series, vix: pd.Series) -> TSIIndicator:
        """Single-day tech/semi crash — fastest-reacting indicator (1-day window).

        Catches shocks that trend indicators miss for 3-10 days.
        Logic: worst of QQQ/SOX 1-day return, amplified by VIX spike.
        -1% → ~33,  -2% → ~67,  -3% → ~100
        VIX rising same day adds up to 50% amplification.
        Flash fires independently when signal > 75 (~2.5% single-day drop).
        """
        if len(qqq) < 2 or len(sox) < 2 or len(vix) < 2:
            return TSIIndicator("tech_crash_day", 0, 0, 0.14, "neutral")

        qqq_1d = (qqq.iloc[-1] / qqq.iloc[-2] - 1) * 100
        sox_1d = (sox.iloc[-1] / sox.iloc[-2] - 1) * 100
        vix_1d = vix.iloc[-1] - vix.iloc[-2]  # absolute VIX change

        worst_1d = min(qqq_1d, sox_1d)

        if worst_1d < 0:
            base_signal = np.clip(abs(worst_1d) / 3 * 100, 0, 100)
            # VIX rising same day confirms real selling pressure (not sector rotation)
            if vix_1d > 0:
                vix_amp = np.clip(vix_1d / 3, 0, 0.5)  # up to 50% amplification
                signal = min(100, base_signal * (1 + vix_amp))
            else:
                signal = base_signal
        else:
            signal = 0.0

        return TSIIndicator("tech_crash_day", worst_1d, signal, 0.14,
                            "bearish" if signal > 30 else "neutral")

    def _sox_qqq_divergence(self, sox: pd.Series, qqq: pd.Series) -> TSIIndicator:
        """When SOX (semis) underperforms QQQ (tech), trouble ahead."""
        if len(sox) < 20 or len(qqq) < 20:
            return TSIIndicator("sox_qqq_divergence", 0, 0, 0.18, "neutral")

        sox_ret_10d = (sox.iloc[-1] / sox.iloc[-10] - 1) * 100
        qqq_ret_10d = (qqq.iloc[-1] / qqq.iloc[-10] - 1) * 100
        divergence = qqq_ret_10d - sox_ret_10d  # positive = SOX lagging

        # SOX lagging QQQ by >2% in 10d = stress
        signal = np.clip(divergence / 4 * 100, 0, 100) if divergence > 0 else 0
        # SOX outperforming = bullish, reduce signal
        if divergence < -1:
            signal = max(0, signal - 20)

        return TSIIndicator("sox_qqq_divergence", divergence, signal, 0.18, "bearish" if signal > 40 else "bullish")

    def _memory_momentum(self, mu: pd.Series) -> TSIIndicator:
        """Memory stock (Micron) momentum breakdown = demand concern."""
        if len(mu) < 20:
            return TSIIndicator("memory_momentum", 0, 0, 0.15, "neutral")

        ret_5d = (mu.iloc[-1] / mu.iloc[-5] - 1) * 100
        ret_20d = (mu.iloc[-1] / mu.iloc[-20] - 1) * 100

        # RSI-like: is MU in a downtrend?
        sma20 = mu.tail(20).mean()
        below_sma = (mu.iloc[-1] / sma20 - 1) * 100

        # Combine: 5d drop + below 20MA = stress
        drop_signal = np.clip(abs(min(ret_5d, 0)) / 5 * 60, 0, 60)
        trend_signal = np.clip(abs(min(below_sma, 0)) / 8 * 40, 0, 40)
        signal = min(100, drop_signal + trend_signal)

        return TSIIndicator("memory_momentum", ret_5d, signal, 0.15, "bearish" if signal > 40 else "bullish")

    def _yield_shock(self, t10y: pd.Series) -> TSIIndicator:
        """Rapid yield rise kills tech valuations."""
        if len(t10y) < 20:
            return TSIIndicator("yield_shock", 0, 0, 0.15, "neutral")

        current = t10y.iloc[-1]
        change_5d = (current - t10y.iloc[-5]) * 100  # in bps

        # 1Y percentile
        if len(t10y) >= 252:
            pctile = (t10y.tail(252) < current).sum() / 252
        else:
            pctile = 0.5

        speed = np.clip(change_5d / 15 * 50, 0, 50)
        level = np.clip(pctile * 50, 0, 50)
        signal = min(100, speed + level)

        return TSIIndicator("yield_shock", change_5d, signal, 0.15, "bearish" if signal > 40 else "neutral")

    def _ai_infra_rs(self, smh: pd.Series, spy: pd.Series) -> TSIIndicator:
        """AI infrastructure (SMH) vs broad market. Underperformance = warning."""
        if len(smh) < 20 or len(spy) < 20:
            return TSIIndicator("ai_infra_rs", 0, 0, 0.12, "neutral")

        smh_ret = (smh.iloc[-1] / smh.iloc[-20] - 1) * 100
        spy_ret = (spy.iloc[-1] / spy.iloc[-20] - 1) * 100
        rs = smh_ret - spy_ret  # negative = SMH lagging

        signal = np.clip(abs(min(rs, 0)) / 5 * 100, 0, 100) if rs < 0 else 0

        return TSIIndicator("ai_infra_rs", rs, signal, 0.12, "bearish" if rs < -1 else "bullish")

    def _tech_breadth(self, qqq: pd.Series) -> TSIIndicator:
        """QQQ internal momentum — proxy for tech breadth."""
        if len(qqq) < 50:
            return TSIIndicator("tech_breadth", 0, 0, 0.12, "neutral")

        sma20 = qqq.rolling(20).mean()
        sma50 = qqq.rolling(50).mean()

        above_20 = 1 if qqq.iloc[-1] > sma20.iloc[-1] else 0
        above_50 = 1 if qqq.iloc[-1] > sma50.iloc[-1] else 0

        # Recent trend: how many of last 10 days were QQQ above 20MA?
        recent_above = sum(1 for i in range(-10, 0) if qqq.iloc[i] > sma20.iloc[i]) / 10

        breadth_score = (above_20 * 0.3 + above_50 * 0.3 + recent_above * 0.4)
        signal = (1 - breadth_score) * 100  # Inverted: low breadth = high stress

        return TSIIndicator("tech_breadth", breadth_score * 100, signal, 0.12, "bearish" if signal > 50 else "bullish")

    def _cloud_rs(self, qqq: pd.Series, spy: pd.Series) -> TSIIndicator:
        """Cloud/tech relative strength vs broad market."""
        if len(qqq) < 10 or len(spy) < 10:
            return TSIIndicator("cloud_rs", 0, 0, 0.10, "neutral")

        qqq_ret = (qqq.iloc[-1] / qqq.iloc[-10] - 1) * 100
        spy_ret = (spy.iloc[-1] / spy.iloc[-10] - 1) * 100
        rs = qqq_ret - spy_ret

        # Tech underperforming broad market = stress
        signal = np.clip(abs(min(rs, 0)) / 3 * 100, 0, 100) if rs < 0 else 0

        return TSIIndicator("cloud_rs", rs, signal, 0.10, "bearish" if rs < -0.5 else "bullish")

    def _vix_tech_corr(self, vix: pd.Series, qqq: pd.Series) -> TSIIndicator:
        """When VIX spikes AND tech drops = confirmed stress."""
        if len(vix) < 5 or len(qqq) < 5:
            return TSIIndicator("vix_tech_correlation", 0, 0, 0.18, "neutral")

        vix_change = (vix.iloc[-1] - vix.iloc[-3]) / vix.iloc[-3] * 100
        qqq_ret = (qqq.iloc[-1] / qqq.iloc[-3] - 1) * 100

        # VIX up + QQQ down = stress
        if vix_change > 2 and qqq_ret < -0.3:
            vix_signal = np.clip(vix_change / 10 * 50, 0, 50)
            qqq_signal = np.clip(abs(qqq_ret) / 2 * 50, 0, 50)
            signal = min(100, vix_signal + qqq_signal)
        elif vix_change > 3:
            signal = np.clip(vix_change / 12 * 50, 0, 50)
        elif qqq_ret < -0.8:
            signal = np.clip(abs(qqq_ret) / 2.5 * 40, 0, 40)
        else:
            signal = 0

        return TSIIndicator("vix_tech_correlation", vix_change, signal, 0.18, "bearish" if signal > 30 else "neutral")

    def _yield_30y_stress(self, t30y: pd.Series) -> TSIIndicator:
        """30Y Treasury at extreme levels = long-duration tech gets crushed.

        May 15, 2026: 30Y hit 5.12% (highest since 2007). This directly
        impacts growth/tech via DCF discount rate.
        """
        if len(t30y) < 20:
            return TSIIndicator("yield_30y_stress", 0, 0, 0.08, "neutral")

        current = t30y.iloc[-1]
        change_5d = (current - t30y.iloc[-5]) * 100  # bps
        change_20d = (current - t30y.iloc[-20]) * 100

        # Level signal: 30Y above 4.5% is elevated, above 5% is extreme
        level_signal = np.clip((current - 4.0) / 1.5 * 50, 0, 50)
        # Speed signal: rapid rise
        speed_signal = np.clip(change_5d / 15 * 50, 0, 50)
        signal = min(100, level_signal + speed_signal)

        return TSIIndicator("yield_30y_stress", current, signal, 0.08, "bearish" if signal > 30 else "neutral")

    def _yield_curve_bear_steep(self, t10y: pd.Series, t30y: Optional[pd.Series]) -> TSIIndicator:
        """Bear steepening: 30Y-10Y spread WIDENING while BOTH yields rise.

        This is the most toxic scenario for tech:
        - Rising rates = lower valuations
        - Steepening = market pricing in higher long-term inflation/rates
        - Means rate cuts are NOT coming to save tech

        May 15: 10Y 4.55%, 30Y 5.12% → spread 57bps and widening
        """
        if t30y is None or len(t10y) < 10 or len(t30y) < 10:
            return TSIIndicator("yield_curve_bear_steep", 0, 0, 0.08, "neutral")

        # Current spread
        spread = t30y.iloc[-1] - t10y.iloc[-1]
        spread_5d_ago = t30y.iloc[-5] - t10y.iloc[-5]
        spread_change = (spread - spread_5d_ago) * 100  # bps

        # Both yields rising?
        t10y_rising = t10y.iloc[-1] > t10y.iloc[-5]
        t30y_rising = t30y.iloc[-1] > t30y.iloc[-5]
        both_rising = t10y_rising and t30y_rising

        # Bear steepening = spread widening + both rising
        if both_rising and spread_change > 0:
            signal = np.clip(spread_change / 10 * 70, 0, 70)
            # Extra penalty if 30Y is above 5%
            if t30y.iloc[-1] > 5.0:
                signal = min(100, signal + 30)
        elif spread_change > 5:
            # Spread widening even if not both rising
            signal = np.clip(spread_change / 15 * 50, 0, 50)
        else:
            signal = 0

        return TSIIndicator("yield_curve_bear_steep", spread_change, signal, 0.08, "bearish" if signal > 30 else "neutral")

    # ── Leading Indicator Methods ──────────────────────────────────────────────

    def _vvix_lead(self, vvix: pd.Series, vix: pd.Series) -> TSIIndicator:
        """VVIX (vol-of-vol) spike → VIX explosion 1-2 days later → tech selloff.

        VVIX measures implied volatility of VIX options. When VVIX rises above
        its 20-day mean while VIX is still calm, it signals institutional hedgers
        are buying VIX calls in anticipation of a shock — typically 1-2 days early.

        Historical: VVIX >120 has preceded major VIX spikes in 2018, 2020, 2022.
        """
        if len(vvix) < 20 or len(vix) < 5:
            return TSIIndicator("vvix_lead", 0, 0, 0.12, "neutral")

        vvix_now = vvix.iloc[-1]
        vvix_ma20 = vvix.tail(20).mean()
        pct_above_ma = (vvix_now / vvix_ma20 - 1) * 100

        vvix_3d_change = (vvix.iloc[-1] / vvix.iloc[-3] - 1) * 100
        vix_3d_change  = (vix.iloc[-1]  / vix.iloc[-3]  - 1) * 100

        # Base signal: VVIX elevated above its own 20-day mean
        base = np.clip(pct_above_ma / 20 * 60, 0, 60)

        # Leading bonus: VVIX rising FASTER than VIX (anticipatory divergence)
        if vvix_3d_change > 5 and vvix_3d_change > vix_3d_change * 2:
            divergence_bonus = np.clip(vvix_3d_change / 15 * 40, 0, 40)
            signal = min(100, base + divergence_bonus)
        else:
            signal = base

        return TSIIndicator("vvix_lead", vvix_now, signal, 0.12,
                            "bearish" if signal > 30 else "neutral")

    def _credit_divergence(self, hyg: pd.Series, spy: pd.Series) -> TSIIndicator:
        """HYG (high yield bonds) lagging SPY → equity weakness 1-3 days ahead.

        Credit markets are populated by more-informed institutional money.
        When HY spreads widen while equities hold, it's early-warning that
        risk appetite is deteriorating before equities catch up.

        Signal: spy_5d_return - hyg_5d_return > 0 (SPY outperforming HYG = warning)
        Extra: HYG falling while SPY flat/up = strongest warning (divergence peak)
        """
        if len(hyg) < 10 or len(spy) < 10:
            return TSIIndicator("credit_divergence", 0, 0, 0.10, "neutral")

        hyg_5d = (hyg.iloc[-1] / hyg.iloc[-5] - 1) * 100
        spy_5d = (spy.iloc[-1] / spy.iloc[-5] - 1) * 100
        divergence = spy_5d - hyg_5d  # positive = SPY outperforming HYG

        if divergence > 0:
            signal = np.clip(divergence / 3 * 80, 0, 80)
            # Extra if HYG actually falling while SPY flat/up (strongest divergence)
            if hyg_5d < -0.3 and spy_5d > -0.3:
                signal = min(100, signal + 20)
        else:
            signal = 0

        return TSIIndicator("credit_divergence", divergence, signal, 0.10,
                            "bearish" if signal > 30 else "neutral")

    def _sox_momentum_decel(self, sox: pd.Series, qqq: pd.Series) -> TSIIndicator:
        """SOX momentum deceleration (2nd derivative) → breakdown 1-2 days ahead.

        When SOX's rate-of-gain SLOWS while still positive, sellers are absorbing
        buyers without moving the price down yet. Actual breakdown follows 1-2d.

        Logic: compare 3-day vs 7-day momentum. If 7d was strong but 3d collapsed →
        momentum lost steam → high probability of reversal or gap-down tomorrow.
        Extra: if QQQ still strong while SOX decelerates → SOX-specific weakness.
        """
        if len(sox) < 15 or len(qqq) < 10:
            return TSIIndicator("sox_momentum_decel", 0, 0, 0.08, "neutral")

        sox_3d = (sox.iloc[-1] / sox.iloc[-3] - 1) * 100
        sox_7d = (sox.iloc[-1] / sox.iloc[-7] - 1) * 100
        qqq_3d = (qqq.iloc[-1] / qqq.iloc[-3] - 1) * 100

        if sox_7d > 1.5 and sox_3d < sox_7d * 0.35:
            # Strong 7d momentum collapsed in last 3d — deceleration
            decel = sox_7d - sox_3d
            signal = np.clip(decel / 3 * 70, 0, 70)
            if qqq_3d > sox_3d + 1.0:  # QQQ still strong, SOX specifically weakening
                signal = min(100, signal + 20)
        elif sox_3d < -1.0 and sox_7d > 0:
            # Recently turned negative from positive — momentum flip
            signal = np.clip(abs(sox_3d) / 2 * 60, 0, 60)
        else:
            signal = 0

        return TSIIndicator("sox_momentum_decel", sox_3d - sox_7d, signal, 0.08,
                            "bearish" if signal > 30 else "neutral")
