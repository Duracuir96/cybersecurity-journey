# src/dashboard/sidebar/source_config.py

import os
import streamlit as st
from dashboard.config.render import html


def render_source_config(t):
    """
    Renders the log source selector. Two real sources: local file / AWS.
    Input  : theme dict
    Output : source (str), file_path (str|None), hours (int), source_tag (str)
    """
    html('<div class="cla-label">LOG SOURCE</div>')

    source = st.radio(
        "log_source",
        options=["Local File", "AWS CloudTrail"],
        label_visibility="collapsed",
        key="source_choice",
    )

    file_path = None

    if source == "Local File":
        file_path = st.text_input(
            "FILE PATH",
            value="../data/sample_cloudtrail.json",
            placeholder="path/to/cloudtrail.json",
            key="file_path_input",
        )
        source_tag = os.path.basename(file_path) if file_path else "local-file"
    else:
        source_tag = "aws-cloudtrail"

    # Read the current window from state so the RANGE strip is accurate even
    # though it is rendered above the slider.
    hours = st.session_state.get("hours_slider", 24)

    html(
        '<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:8px 0;border-top:1px solid {t["border"]};'
        f'border-bottom:1px solid {t["border"]};margin:8px 0 12px 0;">'
        '<span class="cla-col">RANGE</span>'
        f'<span style="color:{t["text_primary"]};font-size:0.72rem;font-weight:600;'
        f'font-family:var(--mono);">LAST {hours}H</span></div>'
    )

    if source == "AWS CloudTrail":
        hours = st.slider(
            "TIME WINDOW",
            min_value=1, max_value=168, value=24, step=1,
            format="%dh", key="hours_slider",
        )
    else:
        hours = 24

    return source, file_path, hours, source_tag