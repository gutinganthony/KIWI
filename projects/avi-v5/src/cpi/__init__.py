"""
Crash Probability Index (CPI) — Short-term crash prediction system.

Unlike AVI (monthly, long-term valuation), CPI runs DAILY and predicts:
  - Major crashes (20%+ drops) 15-30 days before peak
  - Minor corrections (3-5% drops) 3-5 days before

Uses 8 daily indicators across 4 dimensions:
  1. Volatility Stress (VIX term structure, GARCH gap)
  2. Credit Acceleration (BAA spread velocity, HY stress)
  3. Market Internals (breadth divergence, distribution days)
  4. Momentum Exhaustion (RSI divergence, distance from MA)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class CPIIndicator:
    name: str
    value: float
    signal: float  # 0-100 contribution
    weight: float
    weighted_signal: float
    status: str  # "normal", "elevated", "critical"


@dataclass
class FlashAlert:
    triggered: bool
    triggers: list[str] = field(default_factory=list)
    severity: str = "none"  # "none", "warning", "critical"


@dataclass
class CPIResult:
    score: float  # 0-100
    date: datetime
    indicators: list[CPIIndicator]
    flash_alert: FlashAlert
    avi_context: Optional[float] = None  # AVI V5 score for context

    @property
    def level(self) -> str:
        if self.score >= 70:
            return "CRITICAL"
        elif self.score >= 50:
            return "HIGH"
        elif self.score >= 35:
            return "ELEVATED"
        elif self.score >= 20:
            return "MODERATE"
        return "LOW"

    def summary(self) -> str:
        lines = [
            f"{'='*65}",
            f"  Crash Probability Index (CPI): {self.score:.0f}/100 — {self.level}",
            f"  Date: {self.date.strftime('%Y-%m-%d')}",
        ]
        if self.avi_context is not None:
            lines.append(f"  AVI V5 Context: {self.avi_context:.1f}/10")
        lines.append(f"{'='*65}")

        if self.flash_alert.triggered:
            lines.append(f"\n  ⚡ FLASH ALERT: {self.flash_alert.severity.upper()}")
            for t in self.flash_alert.triggers:
                lines.append(f"     → {t}")
            lines.append("")

        lines.append(f"  {'Indicator':<30} {'Value':>8} {'Signal':>8} {'Status':>10}")
        lines.append(f"  {'-'*58}")
        for ind in sorted(self.indicators, key=lambda x: -x.weighted_signal):
            lines.append(
                f"  {ind.name:<30} {ind.value:>8.2f} {ind.signal:>7.0f}/100 "
                f"{ind.status:>10}"
            )

        lines.append(f"\n  Action Guidance:")
        if self.score >= 70:
            lines.append(f"  🔴 Immediate risk reduction. Consider hedging or raising cash.")
        elif self.score >= 50:
            lines.append(f"  🟠 Tighten stops. No new long positions. Reduce leverage.")
        elif self.score >= 35:
            lines.append(f"  🟡 Stay alert. Review stop-losses. Monitor daily.")
        else:
            lines.append(f"  🟢 Normal conditions. Standard risk management.")

        lines.append(f"{'='*65}")
        return "\n".join(lines)


class CrashProbabilityIndex:
    """Daily crash probability scorer using 10 short-term indicators.

    Score boosting mechanisms (applied after weighted sum):
      - AVI boost: CPI * 1.2 when AVI > 6 and CPI > 40
      - Consensus boost: CPI * 1.15-1.3 when 3-5+ indicators elevated
      - Short-term stress boost: CPI * 1.25-1.3 when momentum_collapse
        and/or vix_spike fire, to improve 7-day detection window
    """

    # Indicator weights (sum to 1.0) — 10 indicators
    WEIGHTS = {
        "vix_term_structure": 0.14,
        "vix_spike": 0.10,           # NEW: absolute VIX level surge
        "garch_vix_gap": 0.10,
        "credit_acceleration": 0.12,
        "breadth_divergence": 0.10,
        "distribution_days": 0.10,
        "rsi_divergence": 0.08,
        "ma_distance_reversal": 0.08,
        "yield_curve_steepening": 0.08,
        "momentum_collapse": 0.10,    # NEW: 5-day price momentum breakdown
    }

    def compute(
        self,
        sp500_daily: pd.DataFrame,
        vix_daily: pd.Series,
        vix3m_daily: pd.Series,
        baa_daily: pd.Series,
        aaa_daily: pd.Series,
        treasury_10y: pd.Series,
        treasury_2y: pd.Series,
        sp500_breadth: Optional[pd.Series] = None,
        as_of: Optional[str] = None,
        avi_score: Optional[float] = None,
    ) -> CPIResult:
        """Compute CPI score for a given date.

        Args:
            sp500_daily: DataFrame with 'close' and 'volume' columns
            vix_daily: Daily VIX (spot)
            vix3m_daily: Daily VIX 3-month (VIX3M). If None, uses VIX MA proxy.
            baa_daily: Moody's BAA yield
            aaa_daily: Moody's AAA yield
            treasury_10y: 10Y Treasury yield
            treasury_2y: 2Y Treasury yield
            sp500_breadth: % of S&P 500 stocks above 200MA (optional)
            as_of: Date to compute (YYYY-MM-DD). None = latest.
            avi_score: Current AVI V5 score for context.
        """
        if as_of:
            cutoff = pd.Timestamp(as_of)
            sp500_daily = sp500_daily[sp500_daily.index <= cutoff]
            vix_daily = vix_daily[vix_daily.index <= cutoff]
            if vix3m_daily is not None:
                vix3m_daily = vix3m_daily[vix3m_daily.index <= cutoff]
            baa_daily = baa_daily[baa_daily.index <= cutoff]
            aaa_daily = aaa_daily[aaa_daily.index <= cutoff]
            treasury_10y = treasury_10y[treasury_10y.index <= cutoff]
            treasury_2y = treasury_2y[treasury_2y.index <= cutoff]
            if sp500_breadth is not None:
                sp500_breadth = sp500_breadth[sp500_breadth.index <= cutoff]

        date = sp500_daily.index[-1].to_pydatetime()
        indicators = []
        flash_triggers = []

        # --- 1. VIX Term Structure ---
        sig_vts, ind_vts, flash = self._vix_term_structure(vix_daily, vix3m_daily)
        indicators.append(ind_vts)
        if flash:
            flash_triggers.append(flash)

        # --- 2. GARCH-VIX Gap ---
        sig_garch, ind_garch, flash = self._garch_vix_gap(sp500_daily, vix_daily)
        indicators.append(ind_garch)
        if flash:
            flash_triggers.append(flash)

        # --- 3. Credit Spread Acceleration ---
        sig_credit, ind_credit, flash = self._credit_acceleration(baa_daily, aaa_daily)
        indicators.append(ind_credit)
        if flash:
            flash_triggers.append(flash)

        # --- 4. Breadth Divergence ---
        sig_breadth, ind_breadth, flash = self._breadth_divergence(
            sp500_daily, sp500_breadth
        )
        indicators.append(ind_breadth)
        if flash:
            flash_triggers.append(flash)

        # --- 5. Distribution Days ---
        sig_dist, ind_dist, flash = self._distribution_days(sp500_daily)
        indicators.append(ind_dist)
        if flash:
            flash_triggers.append(flash)

        # --- 6. RSI Divergence ---
        sig_rsi, ind_rsi, flash = self._rsi_divergence(sp500_daily)
        indicators.append(ind_rsi)
        if flash:
            flash_triggers.append(flash)

        # --- 7. MA Distance + Reversal ---
        sig_ma, ind_ma, flash = self._ma_distance_reversal(sp500_daily)
        indicators.append(ind_ma)
        if flash:
            flash_triggers.append(flash)

        # --- 8. Yield Curve Steepening ---
        sig_yc, ind_yc, flash = self._yield_curve_steepening(treasury_10y, treasury_2y)
        indicators.append(ind_yc)
        if flash:
            flash_triggers.append(flash)

        # --- 9. VIX Spike (absolute level surge) ---
        sig_vs, ind_vs, flash = self._vix_spike(vix_daily)
        indicators.append(ind_vs)
        if flash:
            flash_triggers.append(flash)

        # --- 10. Momentum Collapse (5-day price breakdown) ---
        sig_mc, ind_mc, flash = self._momentum_collapse(sp500_daily)
        indicators.append(ind_mc)
        if flash:
            flash_triggers.append(flash)

        # Composite CPI score
        total = sum(ind.weighted_signal for ind in indicators)
        cpi_score = min(100.0, max(0.0, total))

        # AVI boost: if AVI > 6 and CPI > 40, multiply CPI by 1.2
        if avi_score is not None and avi_score > 6.0 and cpi_score > 40:
            cpi_score = min(100.0, cpi_score * 1.2)

        # Consensus boost: when 3+ indicators are elevated, amplify
        elevated_count = sum(1 for ind in indicators if ind.signal >= 40)
        if elevated_count >= 5:
            cpi_score = min(100.0, cpi_score * 1.3)
        elif elevated_count >= 3:
            cpi_score = min(100.0, cpi_score * 1.15)

        # Short-term stress boost: compensate for slow indicators fading
        # in the final 7 days before a crash. When fast-moving indicators
        # (momentum_collapse, vix_spike, vix_term_structure) fire together,
        # it strongly suggests imminent price dislocation — boost CPI to
        # prevent false negatives in the critical 7-day window.
        mc_signal = sig_mc    # momentum_collapse signal
        vs_signal = sig_vs    # vix_spike signal
        vts_signal = sig_vts  # vix_term_structure signal

        # Tier 1: strong momentum collapse alone (>2.5% drop in 3-5 days)
        if mc_signal > 50:
            cpi_score = min(100.0, cpi_score * 1.3)

        # Tier 2: VIX surging + momentum weakening together = flash crash setup
        if vs_signal > 60 and mc_signal > 30:
            cpi_score = min(100.0, cpi_score * 1.25)

        # Tier 3: extreme VIX regime — backwardation + elevated VIX level
        # Even without momentum collapse, this pattern reliably precedes
        # crashes (e.g., VIX term structure inverted + VIX spiking above 20).
        # This catches the scenario where CPI peaks 2-4 weeks out but the
        # VIX stress is still present/intensifying in the final week.
        if vts_signal > 80 and vs_signal > 50:
            cpi_score = min(100.0, cpi_score * 1.15)

        # Flash Alert
        flash_alert = FlashAlert(
            triggered=len(flash_triggers) >= 2,
            triggers=flash_triggers,
            severity="critical" if len(flash_triggers) >= 3 else
                     "warning" if len(flash_triggers) >= 2 else "none",
        )

        return CPIResult(
            score=cpi_score,
            date=date,
            indicators=indicators,
            flash_alert=flash_alert,
            avi_context=avi_score,
        )

    def _make_indicator(
        self, name: str, value: float, signal: float
    ) -> CPIIndicator:
        weight = self.WEIGHTS[name]
        weighted = signal * weight
        status = "critical" if signal >= 80 else "elevated" if signal >= 50 else "normal"
        return CPIIndicator(
            name=name, value=value, signal=signal,
            weight=weight, weighted_signal=weighted, status=status,
        )

    # ─── Indicator Implementations ───

    def _vix_term_structure(
        self, vix: pd.Series, vix3m: Optional[pd.Series]
    ) -> tuple[float, CPIIndicator, Optional[str]]:
        """VIX spot vs VIX 3-month. Backwardation = stress."""
        if vix3m is not None and len(vix3m) > 0:
            ratio = vix.iloc[-1] / max(vix3m.iloc[-1], 1)
        else:
            # Proxy: VIX vs its own 63-day (3-month) moving average
            vix_ma63 = vix.rolling(63).mean()
            ratio = vix.iloc[-1] / max(vix_ma63.iloc[-1], 1)

        # ratio > 1.0 = backwardation (stress)
        # Map: 0.92 → 0, 1.0 → 60, 1.10 → 100
        signal = np.clip((ratio - 0.92) / 0.18 * 100, 0, 100)

        ind = self._make_indicator("vix_term_structure", ratio, signal)
        flash = "VIX in backwardation (spot > 3M)" if ratio > 1.05 else None
        return signal, ind, flash

    def _garch_vix_gap(
        self, sp500: pd.DataFrame, vix: pd.Series
    ) -> tuple[float, CPIIndicator, Optional[str]]:
        """GARCH-forecasted vol vs VIX-implied. Gap = hidden stress."""
        try:
            from src.garch.garch_model import GARCHEngine

            close = sp500["close"] if "close" in sp500.columns else sp500.iloc[:, 0]
            returns = close.pct_change().dropna().tail(504)  # 2 years

            engine = GARCHEngine(p=1, q=1)
            engine.fit(returns)
            garch_vol = engine.forecast_volatility(horizon=21)

            vix_current = vix.iloc[-1] / 100  # VIX is in % terms
            gap = (garch_vol - vix_current) / max(vix_current, 0.01)

            # gap > 0 means GARCH sees more risk than VIX prices
            signal = np.clip(gap / 0.30 * 100, 0, 100)
        except Exception:
            gap = 0.0
            signal = 0.0

        ind = self._make_indicator("garch_vix_gap", gap * 100, signal)
        flash = "GARCH vol >> VIX: hidden stress building" if signal > 70 else None
        return signal, ind, flash

    def _credit_acceleration(
        self, baa: pd.Series, aaa: pd.Series
    ) -> tuple[float, CPIIndicator, Optional[str]]:
        """Rate of change of BAA-AAA spread. Fast widening = stress."""
        spread = baa - aaa
        spread = spread.dropna()

        if len(spread) < 20:
            ind = self._make_indicator("credit_acceleration", 0, 0)
            return 0.0, ind, None

        # 10-day change in spread (basis points)
        spread_change_10d = (spread.iloc[-1] - spread.iloc[-10]) * 100  # bps
        # 20-day change
        spread_change_20d = (spread.iloc[-1] - spread.iloc[-20]) * 100 if len(spread) >= 20 else 0

        # Use the worse of 10d and 20d
        change = max(spread_change_10d, spread_change_20d / 2)

        # Map: 0 bps → 0, 8 bps → 50, 20+ bps → 100
        signal = np.clip(change / 20 * 100, 0, 100)

        ind = self._make_indicator("credit_acceleration", spread_change_10d, signal)
        flash = f"Credit spread widening fast (+{spread_change_10d:.0f}bps in 10d)" if spread_change_10d > 20 else None
        return signal, ind, flash

    def _breadth_divergence(
        self, sp500: pd.DataFrame, breadth: Optional[pd.Series]
    ) -> tuple[float, CPIIndicator, Optional[str]]:
        """Index at highs but breadth declining = narrow/fragile market."""
        close = sp500["close"] if "close" in sp500.columns else sp500.iloc[:, 0]

        if breadth is not None and len(breadth) >= 20:
            # Use actual breadth data
            price_20d_return = (close.iloc[-1] / close.iloc[-20] - 1)
            breadth_20d_change = breadth.iloc[-1] - breadth.iloc[-20]

            # Divergence: price up but breadth down
            if price_20d_return > 0 and breadth_20d_change < -5:
                divergence = abs(breadth_20d_change)
                signal = np.clip(divergence / 15 * 100, 0, 100)
            else:
                divergence = 0
                signal = 0
        else:
            # Proxy: use new highs/lows approximation from price action
            # Check if index is near 52-week high but recent returns are weak
            high_252 = close.rolling(252).max()
            distance_from_high = (close.iloc[-1] / high_252.iloc[-1] - 1) * 100

            # Volatility of returns increasing while price flat = stress
            vol_10d = close.pct_change().tail(10).std() * np.sqrt(252)
            vol_60d = close.pct_change().tail(60).std() * np.sqrt(252)
            vol_ratio = vol_10d / max(vol_60d, 0.01)

            # Near highs but volatility expanding
            if distance_from_high > -3 and vol_ratio > 1.3:
                divergence = vol_ratio
                signal = np.clip((vol_ratio - 1.0) / 0.5 * 50, 0, 100)
            else:
                divergence = 0
                signal = 0

        ind = self._make_indicator("breadth_divergence", divergence if 'divergence' in dir() else 0, signal)
        flash = "Market breadth deteriorating while index at highs" if signal > 70 else None
        return signal, ind, flash

    def _distribution_days(
        self, sp500: pd.DataFrame
    ) -> tuple[float, CPIIndicator, Optional[str]]:
        """Count of distribution days (down on higher volume) in last 25 sessions."""
        close = sp500["close"] if "close" in sp500.columns else sp500.iloc[:, 0]
        volume = sp500["volume"] if "volume" in sp500.columns else None

        if volume is None or len(close) < 26:
            ind = self._make_indicator("distribution_days", 0, 0)
            return 0.0, ind, None

        recent = close.tail(26)
        recent_vol = volume.tail(26)

        dist_count = 0
        for i in range(1, len(recent)):
            price_change = (recent.iloc[i] / recent.iloc[i - 1] - 1)
            vol_change = recent_vol.iloc[i] > recent_vol.iloc[i - 1]
            if price_change < -0.002 and vol_change:  # Down >0.2% on higher volume
                dist_count += 1

        # Map: 0-1 → 0, 3 → 50, 5 → 80, 6+ → 100
        signal = np.clip((dist_count - 1) / 5 * 100, 0, 100)

        ind = self._make_indicator("distribution_days", dist_count, signal)
        flash = f"{dist_count} distribution days in 25 sessions" if dist_count >= 5 else None
        return signal, ind, flash

    def _rsi_divergence(
        self, sp500: pd.DataFrame
    ) -> tuple[float, CPIIndicator, Optional[str]]:
        """Price making new highs but RSI declining = bearish divergence."""
        close = sp500["close"] if "close" in sp500.columns else sp500.iloc[:, 0]

        if len(close) < 60:
            ind = self._make_indicator("rsi_divergence", 0, 0)
            return 0.0, ind, None

        # Compute 14-day RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.dropna()

        if len(rsi) < 30:
            ind = self._make_indicator("rsi_divergence", 0, 0)
            return 0.0, ind, None

        # Check: price higher than 20 days ago, but RSI lower
        price_change_20d = close.iloc[-1] / close.iloc[-20] - 1
        rsi_change_20d = rsi.iloc[-1] - rsi.iloc[-20]

        divergence = 0.0
        if price_change_20d > 0.01 and rsi_change_20d < -5:
            # Bearish divergence
            divergence = abs(rsi_change_20d)
            signal = np.clip(divergence / 15 * 100, 0, 100)
        elif rsi.iloc[-1] > 70:
            # Overbought
            signal = np.clip((rsi.iloc[-1] - 70) / 15 * 50, 0, 50)
            divergence = rsi.iloc[-1]
        else:
            signal = 0.0

        ind = self._make_indicator("rsi_divergence", divergence, signal)
        flash = "Bearish RSI divergence: price up, momentum down" if signal > 70 else None
        return signal, ind, flash

    def _ma_distance_reversal(
        self, sp500: pd.DataFrame
    ) -> tuple[float, CPIIndicator, Optional[str]]:
        """Overextended above MAs + starting to reverse = crash setup."""
        close = sp500["close"] if "close" in sp500.columns else sp500.iloc[:, 0]

        if len(close) < 200:
            ind = self._make_indicator("ma_distance_reversal", 0, 0)
            return 0.0, ind, None

        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1]
        price = close.iloc[-1]

        dist_50 = (price / ma50 - 1) * 100  # % above 50MA
        dist_200 = (price / ma200 - 1) * 100  # % above 200MA

        # Check for reversal: was extended, now rolling over
        price_5d_return = (price / close.iloc[-5] - 1) * 100

        signal = 0.0
        if dist_200 > 10 and price_5d_return < -2:
            # Extended + reversing
            signal = np.clip(dist_200 / 15 * 50 + abs(price_5d_return) / 3 * 50, 0, 100)
        elif dist_50 > 5 and price_5d_return < -1.5:
            signal = np.clip(dist_50 / 8 * 30 + abs(price_5d_return) / 2 * 30, 0, 60)

        ind = self._make_indicator("ma_distance_reversal", dist_200, signal)
        flash = f"Reversal from extended level ({dist_200:.0f}% above 200MA, -{abs(price_5d_return):.1f}% in 5d)" if signal > 70 else None
        return signal, ind, flash

    def _yield_curve_steepening(
        self, t10y: pd.Series, t2y: pd.Series
    ) -> tuple[float, CPIIndicator, Optional[str]]:
        """Rapid steepening after inversion = recession/crash approaching."""
        spread = t10y - t2y
        spread = spread.dropna()

        if len(spread) < 60:
            ind = self._make_indicator("yield_curve_steepening", 0, 0)
            return 0.0, ind, None

        current = spread.iloc[-1]
        min_60d = spread.tail(60).min()
        change_20d = current - spread.iloc[-20]

        # Signal fires when: curve WAS inverted (min < 0) and is NOW steepening fast
        signal = 0.0
        if min_60d < 0 and change_20d > 0.15:
            signal = np.clip(change_20d / 0.40 * 100, 0, 100)
        elif min_60d < -0.2 and current > 0:
            # Just un-inverted — classic recession signal
            signal = 60.0

        ind = self._make_indicator("yield_curve_steepening", change_20d * 100, signal)
        flash = "Yield curve rapid steepening after inversion" if signal > 70 else None
        return signal, ind, flash

    def _vix_spike(
        self, vix: pd.Series
    ) -> tuple[float, CPIIndicator, Optional[str]]:
        """VIX absolute level and rate of change. High VIX + rising = imminent risk."""
        if len(vix) < 20:
            ind = self._make_indicator("vix_spike", 0, 0)
            return 0.0, ind, None

        current = vix.iloc[-1]
        vix_5d_ago = vix.iloc[-5]
        vix_change_5d = current - vix_5d_ago

        # Signal: combination of level and speed
        # VIX above 18 + rising = danger signal
        level_signal = np.clip((current - 14) / 12 * 50, 0, 50)  # VIX 14→0, 26→50
        speed_signal = np.clip(vix_change_5d / 5 * 50, 0, 50)    # +5pts in 5d → 50
        signal = min(100, level_signal + speed_signal)

        ind = self._make_indicator("vix_spike", current, signal)
        flash = f"VIX surge: {current:.0f} (+{vix_change_5d:.1f} in 5d)" if current > 19 and vix_change_5d > 2 else None
        return signal, ind, flash

    def _momentum_collapse(
        self, sp500: pd.DataFrame
    ) -> tuple[float, CPIIndicator, Optional[str]]:
        """Rapid 5-day price decline — direct crash signal for 3-5 day prediction."""
        close = sp500["close"] if "close" in sp500.columns else sp500.iloc[:, 0]

        if len(close) < 20:
            ind = self._make_indicator("momentum_collapse", 0, 0)
            return 0.0, ind, None

        # 5-day return
        ret_5d = (close.iloc[-1] / close.iloc[-5] - 1) * 100

        # 3-day return (even shorter for flash crashes)
        ret_3d = (close.iloc[-1] / close.iloc[-3] - 1) * 100

        # Use the worse of the two
        worst_ret = min(ret_5d, ret_3d)

        # Map: 0% → 0, -1.5% → 35, -3% → 60, -5%+ → 100
        if worst_ret < 0:
            signal = np.clip(abs(worst_ret) / 5 * 100, 0, 100)
        else:
            signal = 0.0

        ind = self._make_indicator("momentum_collapse", worst_ret, signal)
        flash = f"Sharp decline: {worst_ret:.1f}% in {3 if ret_3d < ret_5d else 5}d" if worst_ret < -2.0 else None
        return signal, ind, flash
