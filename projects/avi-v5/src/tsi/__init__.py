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
    """Daily tech sector stress scorer using 10 market-based proxies."""

    WEIGHTS = {
        "tech_crash_day":        0.14,   # NEW: 1-day shock detector (fastest)
        "vix_tech_correlation":  0.16,   # 3-day VIX+tech co-movement
        "sox_qqq_divergence":    0.10,   # 10-day semi vs tech divergence
        "memory_momentum":       0.10,   # 5+20-day MU trend
        "yield_shock":           0.12,   # 5-day 10Y spike
        "yield_30y_stress":      0.08,   # 30Y absolute level + speed
        "yield_curve_bear_steep": 0.06,  # 30Y-10Y steepening
        "ai_infra_rs":           0.08,   # 20-day SMH vs SPY
        "tech_breadth":          0.10,   # QQQ vs 20/50MA
        "cloud_rs":              0.06,   # 10-day QQQ vs SPY
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

        # 0. Single-day tech crash detector (fastest — must be first)
        ind = self._tech_crash_day(qqq_daily, sox_daily, vix_daily)
        indicators.append(ind)
        if ind.signal > 60:  # ~2%+ single-day drop — flash on its own
            flash_triggers.append(f"Tech crash: {ind.value:.1f}% single-day drop")

        # 1. SOX/QQQ Divergence
        ind = self._sox_qqq_divergence(sox_daily, qqq_daily)
        indicators.append(ind)
        if ind.signal > 70:
            flash_triggers.append(f"SOX lagging QQQ: {ind.value:.1f}%")

        # 2. Memory Stock Momentum (MU as proxy)
        ind = self._memory_momentum(mu_daily)
        indicators.append(ind)
        if ind.signal > 70:
            flash_triggers.append(f"Memory stocks breaking down")

        # 3. Treasury Yield Shock
        ind = self._yield_shock(treasury_10y)
        indicators.append(ind)
        if ind.signal > 70:
            flash_triggers.append(f"Yield spike: +{ind.value:.0f}bps in 5d")

        # 4. 30Y Yield Stress
        ind = self._yield_30y_stress(treasury_30y if treasury_30y is not None else treasury_10y)
        indicators.append(ind)
        if ind.signal > 70:
            flash_triggers.append(f"30Y yield at extreme: {ind.value:.2f}%")

        # 5. Yield Curve Bear Steepening (30Y-10Y spread rising under rising rates)
        ind = self._yield_curve_bear_steep(treasury_10y, treasury_30y)
        indicators.append(ind)

        # 6. AI Infra Relative Strength (SMH vs SPY)
        ind = self._ai_infra_rs(smh_daily, spy_daily)
        indicators.append(ind)

        # 5. Tech Breadth (QQQ internal momentum)
        ind = self._tech_breadth(qqq_daily)
        indicators.append(ind)

        # 6. Cloud RS (QQQ momentum as proxy)
        ind = self._cloud_rs(qqq_daily, spy_daily)
        indicators.append(ind)

        # 7. VIX-Tech Correlation
        ind = self._vix_tech_corr(vix_daily, qqq_daily)
        indicators.append(ind)
        if ind.signal > 75:
            flash_triggers.append(f"VIX surge + tech selloff")

        # Composite
        total = sum(ind.signal * self.WEIGHTS.get(ind.name, 0.1) for ind in indicators)
        score = min(100, max(0, total))

        # Consensus boost
        elevated = sum(1 for ind in indicators if ind.signal >= 50)
        if elevated >= 5:
            score = min(100, score * 1.25)
        elif elevated >= 3:
            score = min(100, score * 1.1)

        # Spike detection: when ANY indicator > 70, it's meaningful even if
        # trend indicators haven't caught up yet. Boost proportionally.
        max_signal = max(ind.signal for ind in indicators)
        high_signals = [ind.signal for ind in indicators if ind.signal >= 50]
        if len(high_signals) >= 2:
            # Two+ strong signals = minimum score should reflect urgency
            avg_high = sum(high_signals) / len(high_signals)
            min_score = avg_high * 0.65  # e.g., avg 68 → min 44
            score = max(score, min_score)
        elif max_signal >= 70:
            # Single very strong signal = at least moderate alert
            score = max(score, max_signal * 0.5)  # e.g., 77 → min 38.5

        # Multi-indicator breadth: when 3+ indicators > 25, stress is real
        mild_elevated = sum(1 for ind in indicators if ind.signal >= 25)
        if mild_elevated >= 4:
            score = max(score, 45)  # Force CAUTIOUS when broad stress
        elif mild_elevated >= 3:
            score = min(100, score * 1.15)

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
