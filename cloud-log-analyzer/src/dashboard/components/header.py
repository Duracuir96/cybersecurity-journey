# src/dashboard/components/header.py
#
# Top header bar — design spec section 5.

import streamlit as st
from datetime import datetime

from dashboard.config.render import html


def render_header(t, report, source_name="cloudtrail-prod-us-east-1"):
    """
    Renders the top header bar.
    Input  : t (theme dict), report (dict), source_name (str, shown as the
             source tag next to "Security Overview")
    Output : None — renders directly into Streamlit
    """
    summary = report.get("detection_summary", None)
    alert_count = 0
    if summary is not None and not summary.empty:
        alert_count = len(summary[summary["status"] == "ALERT"])

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if alert_count > 0:
        badge = (
            '<span class="cla-badge critical">'
            f'<span class="cla-pulse" style="width:5px;height:5px;border-radius:50%;'
            f'background:{t["critical"]};display:inline-block;"></span>'
            f'{alert_count} ACTIVE ALERTS</span>'
        )
    else:
        badge = ""

    html(
        '<div style="display:flex;align-items:center;justify-content:space-between;'
        f'height:56px;border-bottom:1px solid {t["bd_fine"]};margin-bottom:20px;">'
        # left
        '<div style="display:flex;align-items:center;gap:16px;">'
        '<div style="display:flex;align-items:center;gap:10px;">'
        f'<div style="width:26px;height:26px;background:{t["accent"]};border-radius:6px;'
        'display:flex;align-items:center;justify-content:center;">'
        '<span style="color:#0F1117;font-size:14px;font-weight:700;">C</span></div>'
        f'<span style="color:{t["text_primary"]};font-size:15px;font-weight:600;'
        'letter-spacing:-.01em;">Cloud Log Analyzer</span></div>'
        '<span style="width:1px;height:18px;background:#232733;display:inline-block;"></span>'
        f'<span style="color:{t["text_primary"]};font-size:14px;font-weight:600;">'
        'Security Overview</span>'
        f'<span style="font-family:var(--mono);font-size:10.5px;color:{t["fg3"]};">'
        f'{source_name}</span></div>'
        # right
        '<div style="display:flex;align-items:center;gap:16px;">'
        f'{badge}'
        '<div style="text-align:right;">'
        f'<div style="color:{t["mute"]};font-size:9px;font-weight:600;'
        'text-transform:uppercase;letter-spacing:.14em;margin-bottom:2px;">'
        'LAST SCAN — UTC</div>'
        f'<div style="font-family:var(--mono);font-size:11.5px;'
        f'color:{t["text_primary"]};">{now}</div></div></div>'
        '</div>'
    )