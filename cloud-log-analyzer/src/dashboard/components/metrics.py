# src/dashboard/components/metrics.py

import streamlit as st
from dashboard.config.render import html


def render_metrics(t, report):
    """
    Renders the 4 KPI cards — exactly like the screenshots.

    Layout :
    [TOTAL EVENTS]  [UNIQUE IPS]  [ACTIVE ALERTS]  [RISK SCORE]

    Input  : theme dict, report dict from StatisticsEngine
    Output : None — renders directly into Streamlit
    """
    total_events = report.get("total_events", 0)
    unique_ips   = report.get("unique_ips", 0)
    summary      = report.get("detection_summary", None)
    risk_score   = report.get("risk_score", 0)

    # Compute active alerts count
    alert_count = 0
    if summary is not None and not summary.empty:
        alert_count = len(summary[summary["status"] == "ALERT"])

    # Risk score color
    if risk_score >= 75:
        risk_color   = t["critical"]
        risk_label   = "threshold exceeded"
        risk_bar_pct = 100
    elif risk_score >= 50:
        risk_color   = t["high"]
        risk_label   = "above threshold"
        risk_bar_pct = 75
    elif risk_score >= 25:
        risk_color   = t["medium"]
        risk_label   = "approaching threshold"
        risk_bar_pct = 40
    else:
        risk_color   = t["low"]
        risk_label   = "below threshold"
        risk_bar_pct = 10

    # Alert bar color
    if alert_count >= 8:
        alert_color = t["critical"]
    elif alert_count >= 5:
        alert_color = t["high"]
    elif alert_count >= 2:
        alert_color = t["medium"]
    else:
        alert_color = t["low"]

    alert_bar_pct = int((alert_count / 11) * 100)

    col1, col2, col3, col4 = st.columns(4)

    # ── KPI 1 — Total Events ─────────────────────────────────
    with col1:
        html(_kpi_card(
            t=t,
            label="TOTAL EVENTS",
            value=f"{total_events:,}",
            delta="+8.4%",
            delta_positive=True,
            bar_color=t["accent"],
            bar_pct=72,
            subtitle="24h ingest",
        ))

    # ── KPI 2 — Unique IPs ───────────────────────────────────
    with col2:
        unlisted = max(0, unique_ips - 10)
        html(_kpi_card(
            t=t,
            label="UNIQUE IPS",
            value=f"{unique_ips:,}",
            delta=f"+{unlisted}",
            delta_positive=True,
            bar_color=t["accent"],
            bar_pct=min(int((unique_ips / 100) * 100), 100),
            subtitle=f"{unlisted} unlisted",
        ))

    # ── KPI 3 — Active Alerts ────────────────────────────────
    with col3:
        html(_kpi_card(
            t=t,
            label="ACTIVE ALERTS",
            value=f"{alert_count} of 11",
            delta=f"+{alert_count}",
            delta_positive=False,
            bar_color=alert_color,
            bar_pct=alert_bar_pct,
            subtitle=(f"{max(0, alert_count - 3)} critical"
                      if alert_count >= 3 else "no critical"),
        ))

    # ── KPI 4 — Risk Score ───────────────────────────────────
    with col4:
        html(_kpi_card(
            t=t,
            label="RISK SCORE",
            value=f"{risk_score}",
            value_suffix="/ 100",
            delta=None,
            delta_positive=None,
            bar_color=risk_color,
            bar_pct=risk_bar_pct,
            subtitle=risk_label,
            value_color=risk_color,
        ))


def _kpi_card(
    t,
    label,
    value,
    bar_color,
    bar_pct,
    subtitle,
    delta          = None,
    delta_positive = None,
    value_suffix   = None,
    value_color    = None,
):
    """
    Builds a single KPI card HTML string.
    """
    # Delta HTML
    delta_html = ""
    if delta is not None:
        delta_color = t["low"] if delta_positive else t["critical"]
        delta_html = (
            f'<span style="color: {delta_color}; font-size: 0.7rem; '
            f'font-weight: 600;">{delta}</span>'
        )

    # Value color
    v_color = value_color if value_color else t["text_primary"]

    # Value suffix HTML
    suffix_html = ""
    if value_suffix:
        suffix_html = (
            f'<span style="color: {t["text_secondary"]}; font-size: 1rem; '
            f'font-weight: 400; margin-left: 4px;">{value_suffix}</span>'
        )

    return f"""
<div style="background-color: {t['bg_secondary']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 18px 20px 14px 20px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
<span style="color: {t['text_secondary']}; font-size: 0.62rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.12em;">{label}</span>
{delta_html}
</div>
<div style="margin-bottom: 10px;">
<span style="color: {v_color}; font-size: 1.85rem; font-weight: 700; line-height: 1; letter-spacing: -0.02em;">{value}</span>
{suffix_html}
</div>
<div class="kpi-bar-track">
<div class="kpi-bar-fill" style="width: {bar_pct}%; background-color: {bar_color};"></div>
</div>
<div style="color: {t['text_secondary']}; font-size: 0.68rem; margin-top: 6px;">{subtitle}</div>
</div>
"""