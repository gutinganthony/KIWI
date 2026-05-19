"""Pine Script generation utilities — shared by run_dashboard.py and pine_tools.py."""

from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def generate_cpi_pine(cpi_result) -> str:
    """Fill CPI Pine template with current values and write to pine/.

    Returns the absolute path to the generated file.
    """
    template_path = PROJECT_ROOT / "pine" / "cpi_indicator.pine"
    output_path = PROJECT_ROOT / "pine" / "cpi_indicator_current.pine"

    template = template_path.read_text(encoding="utf-8")

    sig_map = {ind.name: round(ind.signal, 1) for ind in cpi_result.indicators}
    avi_ctx = cpi_result.avi_context

    replacements = {
        "{{CPI_SCORE}}": f"{cpi_result.score:.1f}",
        "{{CPI_DATE}}": cpi_result.date.strftime("%Y-%m-%d"),
        "{{FLASH_ALERT}}": "true" if cpi_result.flash_alert.triggered else "false",
        "{{FLASH_SEVERITY}}": cpi_result.flash_alert.severity,
        "{{AVI_CONTEXT}}": f"{avi_ctx:.1f}" if avi_ctx is not None else "0.0",
        "{{SIG_VIX_TERM}}": str(sig_map.get("vix_term_structure", 0.0)),
        "{{SIG_VIX_SPIKE}}": str(sig_map.get("vix_spike", 0.0)),
        "{{SIG_GARCH}}": str(sig_map.get("garch_vix_gap", 0.0)),
        "{{SIG_CREDIT}}": str(sig_map.get("credit_acceleration", 0.0)),
        "{{SIG_BREADTH}}": str(sig_map.get("breadth_divergence", 0.0)),
        "{{SIG_DISTRIB}}": str(sig_map.get("distribution_days", 0.0)),
        "{{SIG_RSI}}": str(sig_map.get("rsi_divergence", 0.0)),
        "{{SIG_MA_DIST}}": str(sig_map.get("ma_distance_reversal", 0.0)),
        "{{SIG_YIELD}}": str(sig_map.get("yield_curve_steepening", 0.0)),
        "{{SIG_MOMENTUM}}": str(sig_map.get("momentum_collapse", 0.0)),
    }

    output = template
    for k, v in replacements.items():
        output = output.replace(k, v)

    output_path.write_text(output, encoding="utf-8")
    return str(output_path.resolve())


def generate_tsi_pine(tsi_result) -> str:
    """Fill TSI Pine template with current values.

    Returns the absolute path to the generated file.
    """
    template_path = PROJECT_ROOT / "pine" / "tsi_indicator.pine"
    output_path = PROJECT_ROOT / "pine" / "tsi_indicator_current.pine"

    template = template_path.read_text(encoding="utf-8")

    sig_map = {ind.name: round(ind.signal, 1) for ind in tsi_result.indicators}

    replacements = {
        "{{TSI_SCORE}}": f"{tsi_result.score:.1f}",
        "{{TSI_DATE}}": tsi_result.date.strftime("%Y-%m-%d"),
        "{{TSI_BIAS}}": tsi_result.bias,
        "{{FLASH_ALERT}}": "true" if tsi_result.flash_alert else "false",
        "{{FLASH_REASON}}": tsi_result.flash_reason or "",
        "{{SIG_SOX_QQQ}}": str(sig_map.get("sox_qqq_divergence", 0.0)),
        "{{SIG_MEMORY}}": str(sig_map.get("memory_momentum", 0.0)),
        "{{SIG_YIELD}}": str(sig_map.get("yield_shock", 0.0)),
        "{{SIG_YIELD_30Y}}": str(sig_map.get("yield_30y_stress", 0.0)),
        "{{SIG_BEAR_STEEP}}": str(sig_map.get("yield_curve_bear_steep", 0.0)),
        "{{SIG_AI_INFRA}}": str(sig_map.get("ai_infra_rs", 0.0)),
        "{{SIG_BREADTH}}": str(sig_map.get("tech_breadth", 0.0)),
        "{{SIG_CLOUD_RS}}": str(sig_map.get("cloud_rs", 0.0)),
        "{{SIG_VIX_TECH}}": str(sig_map.get("vix_tech_correlation", 0.0)),
    }

    output = template
    for k, v in replacements.items():
        output = output.replace(k, v)

    output_path.write_text(output, encoding="utf-8")
    return str(output_path.resolve())


def generate_composite_pine(cpi_result, tsi_result, avi_score: Optional[float]) -> str:
    """Fill composite (CPI + TSI + AVI) Pine template.

    Returns the absolute path to the generated file.
    """
    template_path = PROJECT_ROOT / "pine" / "avi_composite.pine"
    output_path = PROJECT_ROOT / "pine" / "avi_composite_current.pine"

    template = template_path.read_text(encoding="utf-8")

    avi_raw = avi_score if avi_score is not None else 0.0
    avi_x10 = round(avi_raw * 10, 1)

    cpi_level = (
        cpi_result.level if hasattr(cpi_result, "level") else
        "CRITICAL" if cpi_result.score >= 70 else
        "HIGH" if cpi_result.score >= 50 else
        "ELEVATED" if cpi_result.score >= 35 else
        "MODERATE" if cpi_result.score >= 20 else "LOW"
    )
    avi_label = (
        "EXTREME" if avi_raw >= 8 else
        "HIGH" if avi_raw >= 7 else
        "ELEVATED" if avi_raw >= 6 else
        "MODERATE" if avi_raw >= 5 else
        "NEUTRAL" if avi_raw >= 4 else "LOW"
    )

    replacements = {
        "{{CPI_SCORE}}": f"{cpi_result.score:.1f}",
        "{{TSI_SCORE}}": f"{tsi_result.score:.1f}",
        "{{AVI_SCORE_X10}}": str(avi_x10),
        "{{AVI_SCORE_RAW}}": f"{avi_raw:.2f}",
        "{{UPDATE_DATE}}": cpi_result.date.strftime("%Y-%m-%d"),
        "{{CPI_LEVEL}}": cpi_level,
        "{{TSI_BIAS}}": tsi_result.bias,
        "{{AVI_LABEL}}": avi_label,
    }

    output = template
    for k, v in replacements.items():
        output = output.replace(k, v)

    output_path.write_text(output, encoding="utf-8")
    return str(output_path.resolve())
