# src/dashboard/sidebar/notification_config.py

import os
import streamlit as st
from dashboard.config.render import html


def render_notification_config(t):
    """
    Renders the email notification settings.
    Input  : theme dict
    Output : recipient (str), risk_threshold (int), auto_send (bool)
    """
    html('<div class="cla-label">NOTIFICATIONS</div>')

    with st.expander("Email settings", expanded=False):
        recipient = st.text_input(
            "RECIPIENT",
            value=os.getenv("ALERT_RECIPIENT", ""),
            placeholder="soc@company.com",
            key="notif_recipient",
        )
        risk_threshold = st.slider(
            "ALERT THRESHOLD",
            min_value=0, max_value=100, value=25, step=5,
            key="notif_threshold",
            help="Send alert when risk score exceeds this value",
        )
        auto_send = st.checkbox("Auto-send on load", value=False, key="notif_auto")

    return recipient, risk_threshold, auto_send


def render_ingesting_status(t, source):
    """Bottom-of-sidebar status indicator (green pulsing dot + label)."""
    if source == "AWS CloudTrail":
        color, label = t["status_ingesting"], "INGESTING"
    else:
        color, label = t["fg3"], "LOCAL FILE"

    html(
        '<div style="position:fixed;bottom:24px;left:0;width:260px;'
        f'padding:12px 16px;border-top:1px solid {t["border"]};'
        f'background:{t["panel"]};">'
        '<div class="ingesting-status">'
        f'<span class="cla-pulse" style="width:6px;height:6px;border-radius:50%;'
        f'background:{color};display:inline-block;"></span>'
        f'{label}</div></div>'
    )