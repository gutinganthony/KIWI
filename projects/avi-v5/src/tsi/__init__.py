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
    """Daily tech sector stress scorer using 7 market-based proxies."""

    WEIGHTS = {
        "sox_qqq_divergence": 0.18,
        "memory_momentum": 0.15,
        "yield_shock": 0.15,
        "ai_infra_rs": 0.12,
        "tech_breadth": 0.12,
        "cloud_rs": 0.10,
        "vix_tech_correlation": 0.18,
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

        date = sox_daily.index[-1].to_pydatetime()
        indicators = []
        flash_triggers = []

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

        # 4. AI Infra Relative Strength (SMH vs SPY)
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

        if score >= 65:
            bias = "BEARISH"
        elif score >= 45:
            bias = "CAUTIOUS"
        elif score >= 25:
            bias = "NEUTRAL"
        else:
            bias = "BULLISH"

        flash = len(flash_triggers) >= 2
        flash_reason = " + ".join(flash_triggers) if flash else ""

        return TSIResult(
            score=score, date=date, indicators=indicators,
            bias=bias, flash_alert=flash, flash_reason=flash_reason,
        )

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
        if vix_change > 3 and qqq_ret < -0.5:
            vix_signal = np.clip(vix_change / 15 * 50, 0, 50)
            qqq_signal = np.clip(abs(qqq_ret) / 3 * 50, 0, 50)
            signal = min(100, vix_signal + qqq_signal)
        elif vix_change > 5:
            signal = np.clip(vix_change / 20 * 60, 0, 60)
        else:
            signal = 0

        return TSIIndicator("vix_tech_correlation", vix_change, signal, 0.18, "bearish" if signal > 30 else "neutral")
