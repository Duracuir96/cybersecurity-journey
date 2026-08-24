# src/dashboard/sidebar/detection_config.py

import streamlit as st
from dashboard.config.render import html


DETECTION_DEFS = [
    ("failed_logins",     "Brute Force Console Login",   "critical"),
    ("iam_changes",       "IAM Privilege Escalation",    "critical"),
    ("credential_abuse",  "Access Key Usage Anomaly",    "critical"),
    ("critical_events",   "CloudTrail Logging Disabled", "critical"),
    ("s3_exfiltration",   "S3 Mass Object Download",     "high"),
    ("ec2_suspicious",    "Unusual EC2 Instance Launch", "high"),
    ("data_exfiltration", "Security Group Modification", "high"),
    ("lambda_abuse",      "Lambda Function Tampering",   "high"),
    ("role_chaining",     "Root Account Activity",       "medium"),
    ("iam_enumeration",   "IAM Enumeration Activity",    "medium"),
    ("api_calls_by_ip",   "Unauthorized API Calls",      "medium"),
]


def render_detection_config(t):
    """
    Renders detection rule toggles + threshold steppers.
    Input  : theme dict
    Output : detection_config dict, thresholds dict
    """
    all_keys = [d[0] for d in DETECTION_DEFS]

    # ── Header + active counter ───────────────────────────────
    active_count = sum(
        1 for k in all_keys if st.session_state.get(f"det_{k}", True)
    )
    col_label, col_count = st.columns([2, 1])
    with col_label:
        html('<div class="cla-label" style="margin-bottom:6px;">DETECTION RULES</div>')
    with col_count:
        html(
            f'<div style="color:{t["accent"]};font-size:0.65rem;font-weight:700;'
            f'text-align:right;padding-top:2px;font-family:var(--mono);">'
            f'{active_count}/11 ON</div>'
        )

    # ── Quick toggles ─────────────────────────────────────────
    col_all, col_none = st.columns(2)
    with col_all:
        if st.button("All on", key="all_on", use_container_width=True):
            for k in all_keys:
                st.session_state[f"det_{k}"] = True
            st.rerun()
    with col_none:
        if st.button("All off", key="all_off", use_container_width=True):
            for k in all_keys:
                st.session_state[f"det_{k}"] = False
            st.rerun()

    html("<div style='height:6px;'></div>")

    # ── Rule checkboxes ───────────────────────────────────────
    detection_config = {}
    for key, name, _severity in DETECTION_DEFS:
        detection_config[key] = st.checkbox(name, value=True, key=f"det_{key}")

    html(f"<div style='border-top:1px solid {t['border']};margin:12px 0;'></div>")

    # ── Thresholds ────────────────────────────────────────────
    html('<div class="cla-label">THRESHOLDS</div>')

    thresholds = {
        "failed_logins":   _threshold_row(t, "Failed logins",   "thr_failed", 5, 2, 20),
        "api_calls":       _threshold_row(t, "API calls / IP",  "thr_api",   10, 5, 100),
        "s3_exfiltration": _threshold_row(t, "S3 objects",      "thr_s3",     5, 2, 50),
        "iam_enumeration": _threshold_row(t, "IAM enum calls",  "thr_enum",   3, 2, 10),
        "role_chaining":   _threshold_row(t, "Role hops",       "thr_role",   3, 2, 10),
        "risk_floor":      _threshold_row(t, "Risk alert floor","thr_risk",  70, 0, 100, step=5),
    }

    return detection_config, thresholds


def _threshold_row(t, label, key, default, min_val, max_val, step=1):
    """
    Renders a threshold as a labelled number input with native -/+ steppers.
    (A manual st.button("+") renders blank because Streamlit parses button
    labels as Markdown, where a lone "+" is an empty bullet. number_input's
    built-in steppers avoid that entirely.)
    Returns the current int value.
    """
    html(f'<div style="color:{t["fg2"]};font-size:0.72rem;margin:10px 0 2px;">{label}</div>')

    # Avoid the "default value + session_state" warning on reruns.
    kwargs = {} if key in st.session_state else {"value": default}

    return st.number_input(
        label,
        min_value=min_val,
        max_value=max_val,
        step=step,
        key=key,
        label_visibility="collapsed",
        **kwargs,
    )