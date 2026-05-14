"""CPI Dashboard generator — renders CPI results as a self-contained HTML file.

Reads the template.html, fills in CPI data, and writes a standalone dashboard
that can be opened in any browser (no external dependencies).

Usage:
    from dashboard.cpi_dashboard import generate_dashboard
    html_path = generate_dashboard(cpi_result)
"""

import html
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# Avoid 3.10+ union syntax for Python 3.9 compat
from src.cpi import CPIResult

TEMPLATE_PATH = Path(__file__).parent / "template.html"
OUTPUT_DIR = Path(__file__).parent / "output"


def _score_color(score: float) -> str:
    """Return hex color for a CPI score."""
    if score >= 50:
        return "#ef5350"
    elif score >= 35:
        return "#ff9800"
    elif score >= 20:
        return "#f7c948"
    return "#26a69a"


def _bar_color(signal: float) -> str:
    """Return hex color for an indicator signal bar."""
    if signal >= 80:
        return "#ef5350"
    elif signal >= 50:
        return "#ff9800"
    elif signal >= 30:
        return "#f7c948"
    return "#26a69a"


def _status_class(status: str) -> str:
    """Map indicator status to CSS class."""
    return "status-" + status  # normal, elevated, critical


def _avi_color(avi_score: Optional[float]) -> str:
    """Color for AVI V5 context score."""
    if avi_score is None:
        return "#787b86"
    if avi_score >= 7.0:
        return "#ef5350"
    elif avi_score >= 5.0:
        return "#ff9800"
    elif avi_score >= 3.0:
        return "#f7c948"
    return "#26a69a"


def _avi_description(avi_score: Optional[float]) -> str:
    """Human-readable AVI interpretation."""
    if avi_score is None:
        return "AVI V5 score not available. Run the monthly pipeline to include valuation context."
    if avi_score >= 8.0:
        return "Extreme overvaluation. Market is priced for perfection &mdash; any shock could trigger outsized correction."
    elif avi_score >= 6.0:
        return "High overvaluation. Elevated long-term risk amplifies any CPI signal."
    elif avi_score >= 4.0:
        return "Moderate valuation. Standard risk levels; CPI signals are self-contained."
    elif avi_score >= 2.0:
        return "Fair to undervalued. Long-term risk is low; corrections tend to be shallow."
    return "Deeply undervalued. Strong margin of safety; crashes likely offer buying opportunities."


def _action_text(level: str) -> str:
    """Action guidance text based on CPI level."""
    actions = {
        "CRITICAL": "Immediate risk reduction recommended. Consider hedging via puts, "
                     "raising cash allocation, and tightening all stops. Review portfolio "
                     "for concentrated positions.",
        "HIGH": "Tighten stop-losses across all positions. Avoid initiating new long exposure. "
                "Reduce leverage if applicable. Monitor CPI daily for escalation.",
        "ELEVATED": "Stay alert and review stop-loss levels. Avoid adding risk in extended "
                    "sectors. Monitor CPI and flash alerts daily.",
        "MODERATE": "Mild caution warranted. Maintain normal position sizing but be aware "
                    "of developing stress signals. Review weekly.",
        "LOW": "Normal market conditions. Standard risk management applies. "
               "Follow regular rebalancing schedule.",
    }
    return actions.get(level, actions["LOW"])


def _indicator_display_name(name: str) -> str:
    """Convert snake_case indicator name to display name."""
    replacements = {
        "vix_term_structure": "VIX Term Structure",
        "vix_spike": "VIX Spike",
        "garch_vix_gap": "GARCH-VIX Gap",
        "credit_acceleration": "Credit Acceleration",
        "breadth_divergence": "Breadth Divergence",
        "distribution_days": "Distribution Days",
        "rsi_divergence": "RSI Divergence",
        "ma_distance_reversal": "MA Distance Reversal",
        "yield_curve_steepening": "Yield Curve Steepening",
        "momentum_collapse": "Momentum Collapse",
    }
    return replacements.get(name, name.replace("_", " ").title())


def _build_indicator_rows(result: CPIResult) -> str:
    """Generate HTML for indicator bar chart rows."""
    # Sort by weighted_signal descending
    sorted_indicators = sorted(result.indicators, key=lambda x: -x.weighted_signal)

    rows = []
    for ind in sorted_indicators:
        display_name = _indicator_display_name(ind.name)
        color = _bar_color(ind.signal)
        status_cls = _status_class(ind.status)
        width_pct = min(100, max(1, ind.signal))

        row = (
            '<div class="indicator-row">'
            '  <div class="indicator-name">{name}</div>'
            '  <div class="bar-track">'
            '    <div class="bar-fill" style="width:{width}%;background:{color};"></div>'
            '  </div>'
            '  <div class="indicator-signal" style="color:{color};">{signal:.0f}</div>'
            '  <div class="indicator-status {status_cls}">{status}</div>'
            '</div>'
        ).format(
            name=html.escape(display_name),
            width=width_pct,
            color=color,
            signal=ind.signal,
            status_cls=status_cls,
            status=ind.status.upper(),
        )
        rows.append(row)

    return "\n    ".join(rows)


def _build_flash_alert(result: CPIResult) -> Tuple[str, str, str]:
    """Return (css_class, title, triggers_html) for the flash alert banner."""
    fa = result.flash_alert
    if not fa.triggered:
        return ("", "", "")

    css_class = "visible " + fa.severity
    title = "FLASH ALERT: " + fa.severity.upper()
    triggers_html = "<br>".join(html.escape(t) for t in fa.triggers)
    return (css_class, title, triggers_html)


def generate_dashboard(
    result: CPIResult,
    history: Optional[List[Tuple[str, float]]] = None,
    output_path: Optional[str] = None,
) -> str:
    """Generate a self-contained HTML dashboard from a CPIResult.

    Args:
        result: CPIResult from CrashProbabilityIndex.compute()
        history: Optional list of (date_str, score) tuples for the line chart.
                 If None, only the current reading is shown.
        output_path: Where to write the HTML file. Defaults to
                     dashboard/output/cpi_dashboard.html

    Returns:
        Absolute path to the generated HTML file.
    """
    # Read template
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Score and level
    score = result.score
    level = result.level
    score_color = _score_color(score)
    score_display = "{:.0f}".format(score)

    # Flash alert
    flash_class, flash_title, flash_triggers = _build_flash_alert(result)

    # AVI context
    avi_score = result.avi_context
    avi_display = "{:.1f}".format(avi_score) if avi_score is not None else "--"
    avi_color = _avi_color(avi_score)
    avi_desc = _avi_description(avi_score)

    # Action guidance
    action_text = _action_text(level)

    # Indicator rows
    indicator_rows = _build_indicator_rows(result)

    # Chart data (JSON array of [date, score])
    if history and len(history) > 1:
        chart_data_str = "[" + ",".join(
            '["{}", {}]'.format(d, round(s, 1)) for d, s in history
        ) + "]"
        chart_content = ""
    else:
        chart_data_str = "null"
        chart_content = '<div class="chart-empty">No historical data available. Run CPI daily to build history.</div>'

    # Date
    date_str = result.date.strftime("%B %d, %Y")

    # Fill template
    output = template
    output = output.replace("{{DATE}}", html.escape(date_str))
    output = output.replace("{{SCORE}}", score_display)
    output = output.replace("{{SCORE_RAW}}", str(round(score, 1)))
    output = output.replace("{{SCORE_COLOR}}", score_color)
    output = output.replace("{{LEVEL}}", level)
    output = output.replace("{{FLASH_CLASS}}", flash_class)
    output = output.replace("{{FLASH_TITLE}}", flash_title)
    output = output.replace("{{FLASH_TRIGGERS}}", flash_triggers)
    output = output.replace("{{AVI_SCORE}}", avi_display)
    output = output.replace("{{AVI_COLOR}}", avi_color)
    output = output.replace("{{AVI_DESCRIPTION}}", avi_desc)
    output = output.replace("{{ACTION_TEXT}}", action_text)
    output = output.replace("{{INDICATOR_ROWS}}", indicator_rows)
    output = output.replace("{{CHART_DATA}}", chart_data_str)
    output = output.replace("{{CHART_CONTENT}}", chart_content)

    # Determine output path
    if output_path is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_file = OUTPUT_DIR / "cpi_dashboard.html"
    else:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

    out_file.write_text(output, encoding="utf-8")
    return str(out_file.resolve())
