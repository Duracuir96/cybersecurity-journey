# src/dashboard/app.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from dotenv import load_dotenv

from dashboard.config.theme import THEMES
from dashboard.config.css import apply_css
from dashboard.config.render import html
from dashboard.pipeline import run_pipeline
from dashboard.components.header import render_header
from dashboard.components.metrics import render_metrics
from dashboard.components.charts import render_charts
from dashboard.components.cross_detection import render_cross_detection
from dashboard.components.detections import render_detections
from dashboard.sidebar.source_config import render_source_config
from dashboard.sidebar.detection_config import render_detection_config
from dashboard.sidebar.notification_config import (
    render_notification_config,
    render_ingesting_status,
)
from notifications.email_notifier import EmailNotifier

load_dotenv()

st.set_page_config(
    page_title="Cloud Log Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_session_state():
    defaults = {"df": None, "results": {}, "report": {}, "theme": "dark"}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_sidebar():
    with st.sidebar:
        theme_choice = st.selectbox(
            "THEME", options=["dark", "light"], index=0, key="theme_select"
        )
        t = THEMES[theme_choice]

        html("<div style='height:4px;'></div>")
        source, file_path, hours, source_name = render_source_config(t)

        html(f"<hr style='border-color:{t['border']};margin:12px 0;'>")
        detection_config, thresholds = render_detection_config(t)

        html(f"<hr style='border-color:{t['border']};margin:12px 0;'>")
        recipient, risk_threshold, auto_send = render_notification_config(t)

        html("<div style='height:8px;'></div>")
        load_btn = st.button(
            "LOAD AND ANALYZE", type="primary",
            use_container_width=True, key="load_btn",
        )

        render_ingesting_status(t, source)

    return (theme_choice, source, file_path, hours, source_name,
            detection_config, thresholds,
            recipient, risk_threshold, auto_send, load_btn)


def _render_empty_state(t):
    html("<div style='height:32px;'></div>")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        html(
            f'<div style="background:{t["card"]};border:1px solid {t["border"]};'
            'border-radius:8px;padding:48px 40px;text-align:center;">'
            f'<div style="width:48px;height:48px;background:{t["accent"]}22;'
            f'border:1px solid {t["accent"]}44;border-radius:10px;display:flex;'
            'align-items:center;justify-content:center;margin:0 auto 20px auto;">'
            f'<span style="color:{t["accent"]};font-size:20px;font-weight:700;">C</span></div>'
            f'<div style="color:{t["text_primary"]};font-size:1rem;font-weight:600;'
            'margin-bottom:8px;">Cloud Log Analyzer</div>'
            f'<div style="color:{t["fg2"]};font-size:0.8rem;margin-bottom:28px;">'
            'AWS CloudTrail Security Intelligence</div>'
            f'<hr style="border:none;border-top:1px solid {t["border"]};margin:24px 0;">'
            '<div style="text-align:left;">'
            '<div class="cla-col" style="margin-bottom:12px;">GETTING STARTED</div>'
            + _step(t, "01", "Select a log source in the sidebar")
            + _step(t, "02", "Configure detection rules and thresholds")
            + _step(t, "03", "Click LOAD AND ANALYZE")
            + _step(t, "04", "Review detections and risk score")
            + '</div></div>'
        )


def _step(t, number, text):
    return (
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">'
        f'<div style="width:20px;height:20px;border-radius:4px;background:{t["chip"]};'
        'display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
        f'<span style="color:{t["accent"]};font-size:0.6rem;font-weight:700;'
        f'font-family:var(--mono);">{number}</span></div>'
        f'<span style="color:{t["fg2"]};font-size:0.78rem;">{text}</span></div>'
    )


def main():
    _init_session_state()

    (theme_choice, source, file_path, hours, source_name,
     detection_config, thresholds,
     recipient, risk_threshold, auto_send, load_btn) = _render_sidebar()

    t = THEMES[theme_choice]
    apply_css(t)

    if load_btn:
        df, results, report = run_pipeline(
            source=source, file_path=file_path, hours=hours,
            detection_config=detection_config, thresholds=thresholds,
        )
        if df is not None:
            st.session_state.df = df
            st.session_state.results = results
            st.session_state.report = report
            st.success(
                f"{report.get('total_events', 0):,} events analyzed "
                f"— Risk Score {report.get('risk_score', 0)}/100"
            )
            if auto_send and recipient:
                notifier = EmailNotifier()
                notifier.recipient = recipient
                notifier.DEFAULT_RISK_THRESHOLD = risk_threshold
                if notifier.send_alert(report, results):
                    st.info(f"Alert email sent to {recipient}")

    if st.session_state.report:
        report = st.session_state.report
        results = st.session_state.results

        render_header(t, report, source_name)
        render_metrics(t, report)
        html("<div style='height:16px;'></div>")
        render_charts(t, report)
        html("<div style='height:16px;'></div>")
        render_cross_detection(t, report)
        html("<div style='height:16px;'></div>")
        render_detections(t, results, detection_config)

        if recipient:
            c1, c2, c3 = st.columns([3, 1, 3])
            with c2:
                if st.button("Send Alert Email", use_container_width=True):
                    notifier = EmailNotifier()
                    notifier.recipient = recipient
                    notifier.DEFAULT_RISK_THRESHOLD = risk_threshold
                    if notifier.send_alert(st.session_state.report,
                                           st.session_state.results):
                        st.success(f"Alert sent to {recipient}")
                    else:
                        st.warning("Email not sent — check .env config")
    else:
        render_header(t, {}, source_name)
        _render_empty_state(t)


if __name__ == "__main__":
    main()