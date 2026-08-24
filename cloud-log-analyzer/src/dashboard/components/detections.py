# src/dashboard/components/detections.py
#
# Detection tabs — design spec section 5.
# Layout per tab: left column (detail + rule + matched events),
# right column (MITRE / SERVICE / SIGNAL BREAKDOWN / RECOMMENDED ACTION).

import streamlit as st
import pandas as pd
from datetime import datetime

from dashboard.config.theme import (
    DETECTION_TAGS,
    MITRE_MAPPING,
    RULE_LOGIC,
    severity_class,
)
from dashboard.config.render import html
from dashboard.playbooks import load_playbook


DETECTION_META = {
    "failed_logins": {
        "name": "Brute Force Console Login",
        "description": "Multiple failed ConsoleLogin attempts from the same source IP. Indicates credential stuffing or brute force attack against IAM users.",
        "service": "signin.amazonaws.com", "window": "24 h"},
    "iam_changes": {
        "name": "IAM Privilege Escalation",
        "description": "Dangerous IAM modification events detected. Creating users, attaching policies or generating access keys can indicate privilege escalation.",
        "service": "iam.amazonaws.com", "window": "24 h"},
    "credential_abuse": {
        "name": "Access Key Usage Anomaly",
        "description": "GetCallerIdentity called from multiple distinct IPs for the same identity. Indicates a potentially compromised access key used from different locations.",
        "service": "sts.amazonaws.com", "window": "24 h"},
    "critical_events": {
        "name": "CloudTrail Logging Disabled",
        "description": "Critical audit trail tampering detected. Deleting flow logs, stopping or deleting CloudTrail indicates an attacker covering their tracks.",
        "service": "cloudtrail.amazonaws.com", "window": "24 h"},
    "s3_exfiltration": {
        "name": "S3 Mass Object Download",
        "description": "High volume of S3 read operations from a single identity. Consistent with data exfiltration or unauthorized bulk access to cloud storage.",
        "service": "s3.amazonaws.com", "window": "24 h"},
    "ec2_suspicious": {
        "name": "Unusual EC2 Instance Launch",
        "description": "Suspicious EC2 actions detected including instance launches, key pair creation or security group modifications. May indicate crypto-mining or backdoor installation.",
        "service": "ec2.amazonaws.com", "window": "24 h"},
    "lambda_abuse": {
        "name": "Lambda Function Tampering",
        "description": "Lambda function code or configuration modified unexpectedly. UpdateFunctionCode is a critical vector for serverless backdoor injection.",
        "service": "lambda.amazonaws.com", "window": "24 h"},
    "data_exfiltration": {
        "name": "Network Data Exfiltration",
        "description": "VPC peering connections, ACL modifications or flow log deletion detected. Indicates network-level data exfiltration or attacker covering tracks.",
        "service": "ec2.amazonaws.com", "window": "24 h"},
    "role_chaining": {
        "name": "Role Chaining — Priv Escalation",
        "description": "Single identity assuming multiple roles in sequence. Role chaining is a known technique for progressive privilege escalation in AWS environments.",
        "service": "sts.amazonaws.com", "window": "24 h"},
    "iam_enumeration": {
        "name": "IAM Enumeration Activity",
        "description": "High volume of IAM read operations from a single identity. ListUsers, ListRoles and GetAccountAuthorizationDetails indicate active environment reconnaissance.",
        "service": "iam.amazonaws.com", "window": "24 h"},
    "api_calls_by_ip": {
        "name": "Unauthorized API Calls",
        "description": "Single IP address making an abnormally high number of API calls across multiple services. Consistent with automated scanning or credential testing.",
        "service": "*.amazonaws.com", "window": "24 h"},
}


# Short tab labels (the full names collide in the tab bar).
SHORT_NAMES = {
    "failed_logins":     "Brute Force",
    "iam_changes":       "Priv Escalation",
    "credential_abuse":  "Key Anomaly",
    "critical_events":   "Trail Disabled",
    "s3_exfiltration":   "Mass Download",
    "ec2_suspicious":    "EC2 Launch",
    "lambda_abuse":      "Lambda Tamper",
    "data_exfiltration": "Net Exfil",
    "role_chaining":     "Role Chaining",
    "iam_enumeration":   "Enumeration",
    "api_calls_by_ip":   "API Volume",
}


def render_detections(t, results, detection_config):
    """
    Renders detection tabs.
    Input  : theme dict, results dict (Layer 4), detection_config dict
    Output : None — renders directly into Streamlit
    """
    html('<div style="margin-top:8px;"><span class="cla-label">'
         'DETECTION DETAILS</span></div>')
    html('<div style="margin-top:8px;"></div>')

    active_keys = [
        key for key, is_active in detection_config.items()
        if is_active and key in results
    ]

    if not active_keys:
        st.info("No detections active — enable at least one in the sidebar")
        return

    tab_labels = []
    for key in active_keys:
        status = "ALERT" if not results[key].empty else "CLEAR"
        dot    = "\u25CF" if status == "ALERT" else "\u25CB"
        short  = SHORT_NAMES.get(key, DETECTION_META.get(key, {}).get("name", key))
        tab_labels.append(f"{dot} {short}")

    tabs = st.tabs(tab_labels)

    for tab, key in zip(tabs, active_keys):
        with tab:
            result_df = results[key]
            meta      = DETECTION_META.get(key, {})
            status    = "ALERT" if not result_df.empty else "CLEAR"
            matches   = len(result_df)
            mitre_id, mitre_name = MITRE_MAPPING.get(key, ("—", "—"))
            rule      = RULE_LOGIC.get(key, "")
            _render_detection_tab(t, key, result_df, meta, status,
                                  matches, mitre_id, mitre_name, rule)


def _render_detection_tab(t, key, result_df, meta, status,
                          matches, mitre_id, mitre_name, rule):
    name        = meta.get("name", key)
    description = meta.get("description", "")
    service     = meta.get("service", "")
    window      = meta.get("window", "24 h")

    sev_cls = severity_class(status, matches)
    if matches == 0:
        severity, sev_color = "CLEAR", t["low"]
    elif matches >= 10:
        severity, sev_color = "CRITICAL", t["critical"]
    elif matches >= 5:
        severity, sev_color = "HIGH", t["high"]
    elif matches >= 2:
        severity, sev_color = "MEDIUM", t["medium"]
    else:
        severity, sev_color = "LOW", t["medium"]

    left, right = st.columns([1, 0.5])

    # ── LEFT ─────────────────────────────────────────────────
    with left:
        html(
            '<div class="cla-card" style="margin-bottom:12px;">'
            '<div style="display:flex;align-items:center;justify-content:space-between;'
            'margin-bottom:10px;">'
            '<div style="display:flex;align-items:center;gap:12px;">'
            f'<span style="color:{t["text_primary"]};font-size:15px;font-weight:600;'
            f'letter-spacing:-.01em;">{name}</span>'
            f'<span class="cla-badge {sev_cls}">{status}</span>'
            '</div>'
            '<div style="display:flex;gap:28px;">'
            + _stat(t, "SEVERITY", severity, sev_color)
            + _stat(t, "MATCHES", str(matches), t["text_primary"], mono=True)
            + _stat(t, "WINDOW", window, t["text_primary"])
            + '</div></div>'
            f'<p style="color:{t["fg2"]};font-size:12px;line-height:1.55;margin:0;'
            f'max-width:640px;">{description}</p>'
            '</div>'
        )

        if rule:
            html('<div class="cla-col" style="margin:0 0 6px;">RULE LOGIC</div>')
            # Rendered directly (flush-left) so the rule's own indentation
            # is preserved by white-space:pre-wrap.
            st.markdown(f'<div class="cla-code">{rule}</div>',
                        unsafe_allow_html=True)

        if not result_df.empty:
            html(
                '<div style="display:flex;justify-content:space-between;'
                'align-items:center;margin:14px 0 6px;">'
                '<span class="cla-col">MATCHED EVENTS</span>'
                f'<span style="font-family:var(--mono);font-size:10px;'
                f'color:{t["mute"]};">SHOWING {min(len(result_df), 50)} '
                f'OF {len(result_df)}</span></div>'
            )
            st.dataframe(result_df.head(50), use_container_width=True,
                         hide_index=True)
            st.download_button(
                "Export CSV",
                data=result_df.to_csv(index=False),
                file_name=(f"{key}_"
                           f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"),
                mime="text/csv",
            )
        else:
            html(
                f'<div style="margin:14px 0 12px;border-left:3px solid {t["low"]};'
                f'background:{t["low_bg"]};border-radius:0 4px 4px 0;'
                f'padding:12px 16px;color:{t["low"]};font-size:.78rem;'
                'font-weight:500;">CLEAR — No matched events in the selected '
                'time window</div>'
            )

        # Response playbook — read from the versioned .md file.
        with st.expander("Response playbook", expanded=False):
            st.markdown(load_playbook(key))

    # ── RIGHT (meta sidebar) ─────────────────────────────────
    with right:
        html(
            '<div class="cla-card" style="margin-bottom:10px;">'
            '<div class="cla-col" style="margin-bottom:10px;">MITRE ATT&amp;CK</div>'
            f'<div style="font-family:var(--mono);font-size:.8rem;font-weight:600;'
            f'color:{t["accent"]};">{mitre_id}</div>'
            f'<div style="color:{t["fg2"]};font-size:.72rem;margin-top:4px;'
            f'line-height:1.4;">{mitre_name}</div></div>'
        )
        html(
            '<div class="cla-card" style="margin-bottom:10px;">'
            '<div class="cla-col" style="margin-bottom:10px;">SERVICE</div>'
            f'<div style="font-family:var(--mono);font-size:.8rem;'
            f'color:{t["text_primary"]};word-break:break-all;">{service}</div></div>'
        )
        html(
            '<div class="cla-card">'
            '<div class="cla-col" style="margin-bottom:10px;">SIGNAL BREAKDOWN</div>'
            + _build_signal_breakdown(t, key, result_df)
            + '</div>'
        )


def _stat(t, label, val, color, mono=False):
    mf = "font-family:var(--mono);" if mono else ""
    return (
        '<div style="text-align:center;">'
        f'<div class="cla-col" style="margin-bottom:3px;">{label}</div>'
        f'<div style="color:{color};font-size:12px;font-weight:700;{mf}">{val}</div>'
        '</div>'
    )


def _build_signal_breakdown(t, key, result_df):
    if result_df.empty:
        return (f'<div style="color:{t["mute"]};font-size:.72rem;">'
                'No signals detected</div>')

    rows = ""
    cols = result_df.columns
    if "login_count" in cols:
        m = int(result_df["login_count"].max())
        rows += _signal_row(t, "Max attempts", str(m), m, 20, t["critical"])
        rows += _signal_row(t, "IPs flagged", str(len(result_df)), len(result_df), 10, t["high"])
    elif "enumeration_count" in cols:
        m = int(result_df["enumeration_count"].max())
        rows += _signal_row(t, "Max enum calls", str(m), m, 10, t["high"])
        rows += _signal_row(t, "Users flagged", str(len(result_df)), len(result_df), 5, t["medium"])
    elif "unique_ip_count" in cols:
        m = int(result_df["unique_ip_count"].max())
        rows += _signal_row(t, "Max unique IPs", str(m), m, 5, t["critical"])
        rows += _signal_row(t, "Users affected", str(len(result_df)), len(result_df), 5, t["high"])
    elif "call_count" in cols:
        m = int(result_df["call_count"].max())
        rows += _signal_row(t, "Max API calls", str(m), m, 100, t["high"])
        rows += _signal_row(t, "IPs flagged", str(len(result_df)), len(result_df), 10, t["medium"])
    elif "s3_event_count" in cols:
        m = int(result_df["s3_event_count"].max())
        rows += _signal_row(t, "Max S3 ops", str(m), m, 50, t["critical"])
        rows += _signal_row(t, "Users flagged", str(len(result_df)), len(result_df), 5, t["high"])
    elif "assume_role_count" in cols:
        m = int(result_df["assume_role_count"].max())
        rows += _signal_row(t, "Max role hops", str(m), m, 10, t["high"])
        rows += _signal_row(t, "Users flagged", str(len(result_df)), len(result_df), 5, t["medium"])
    else:
        rows += _signal_row(t, "Events matched", str(len(result_df)), len(result_df), 20, t["critical"])
    return rows


def _signal_row(t, label, value_str, value, max_value, color):
    pct = min(int((value / max(max_value, 1)) * 100), 100)
    return (
        '<div class="signal-row">'
        f'<span class="signal-label">{label}</span>'
        '<div class="signal-bar-track">'
        f'<div class="signal-bar-fill" style="width:{pct}%;background:{color};"></div>'
        '</div>'
        f'<span class="signal-value">{value_str}</span></div>'
    )