import sys 
import os 

# add src/ to Python path so all layers are importable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st 
import pandas as pd 
import plotly.express as px 
import plotly.graph_objects as go 
from datetime import datetime , timedelta 
from data_collection.aws_connector import AWSConnector 
from data_processing.log_parser import LogParser 
from data_processing.data_validator import DataValidator
from analysis.heuristic_engine import HeuristicEngine
from analysis.statistics_engine import StatisticsEngine 


# ─── Page config ─────────────────────────────────────────────
st.set_page_config (
    page_title="Cloud log Analyzer",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Theme definitions ───────────────────────────────────────
THEMES = {
    "dark": {
        "bg_primary":   "#0A0E1A",
        "bg_secondary": "#111827",
        "bg_tertiary":  "#1F2937",
        "text_primary": "#F9FAFB",
        "text_secondary": "#9CA3AF",
        "accent":       "#00D4AA",
        "critical":     "#EF4444",
        "high":         "#F97316",
        "medium":       "#EAB308",
        "low":          "#22C55E",
        "border":       "#374151",
        "chart_bg":     "#111827",
    },
    "light": {
        "bg_primary":   "#F3F4F6",
        "bg_secondary": "#FFFFFF",
        "bg_tertiary":  "#E5E7EB",
        "text_primary": "#111827",
        "text_secondary": "#6B7280",
        "accent":       "#0D9488",
        "critical":     "#DC2626",
        "high":         "#EA580C",
        "medium":       "#CA8A04",
        "low":          "#16A34A",
        "border":       "#D1D5DB",
        "chart_bg":     "#FFFFFF",
    }
}


# ─── CSS injection ───────────────────────────────────────────
def apply_theme(t):
    """Injects custom CSS to override Streamlit default styles"""
    st.markdown(f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {t['bg_primary']};
            color: {t['text_primary']};
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {t['bg_secondary']};
            border-right: 1px solid {t['border']};
        }}

        /* Metric cards */
        [data-testid="stMetric"] {{
            background-color: {t['bg_secondary']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 16px;
        }}

        [data-testid="stMetricValue"] {{
            color: {t['accent']};
            font-size: 2rem;
            font-weight: 700;
            font-family: 'Courier New', monospace;
        }}

        [data-testid="stMetricLabel"] {{
            color: {t['text_secondary']};
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        /* Tab styling */
        [data-testid="stTabs"] button {{
            color: {t['text_secondary']};
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        [data-testid="stTabs"] button[aria-selected="true"] {{
            color: {t['accent']};
            border-bottom: 2px solid {t['accent']};
        }}

        /* Dataframe */
        [data-testid="stDataFrame"] {{
            background-color: {t['bg_secondary']};
        }}

        /* Headers */
        h1, h2, h3 {{
            color: {t['text_primary']};
            font-family: 'Courier New', monospace;
        }}

        /* Section divider */
        hr {{
            border-color: {t['border']};
        }}

        /* Select boxes and inputs */
        [data-testid="stSelectbox"] {{
            background-color: {t['bg_secondary']};
        }}

        /* Alert badges */
        .alert-critical {{
            background-color: {t['critical']}22;
            border-left: 3px solid {t['critical']};
            color: {t['critical']};
            padding: 8px 12px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.85rem;
        }}

        .alert-clear {{
            background-color: {t['low']}22;
            border-left: 3px solid {t['low']};
            color: {t['low']};
            padding: 8px 12px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.85rem;
        }}

        .risk-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-weight: 700;
            font-size: 1.2rem;
        }}
    </style>
    """, unsafe_allow_html=True)


# ─── Helper functions ─────────────────────────────────────────

def get_risk_color(score, t ):
    """Returns color based on risk score  """

    if score >= 75:
        return t["critical"]
    elif score >=50:
        return t["high"]
    elif score >= 25:
        return t["medium"]
    return t["low"]

def get_risk_label(score):
    """Returns severity label based on risk score """
    if score >= 75: 
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    return "LOW"

def load_data_from_file(file_path, t):
    "Runs full pipeline from local file"
    connector = AWSConnector()
    raw_logs = connector.fetch_logs(source="file", file_path=file_path)
    return _run_pipeline(raw_logs,t)

def load_data_from_aws(hours, t):
    """Runs full pipeline from AWS CloudTrail"""
    connector = AWSConnector()
    connector.connect()
    end_time = datetime.utcnow()
    start_time = end_time -timedelta(hours=hours)
    raw_logs = connector.fetch_logs(
        source="aws",
        start_time = start_time,
        end_time=end_time,
        max_events=50
    )
    return _run_pipeline(raw_logs, t)

def _run_pipeline(raw_logs, t):
    """Shared pipeline : parse → validate → detect → stats """

    parser = LogParser()
    validator = DataValidator()
    engine = HeuristicEngine()
    stats = StatisticsEngine()

    parsed = parser.parse_json(raw_logs)
    df = parser.to_dataframe(parsed)

    if df.empty:
        return df, {},  {}
    is_valid = validator.validate_schema(df)
    if not is_valid:
        st.error("❌ schema validation failed - check your log source ")
        return df, {}, {}

    df = validator.clean_data(df)
    results = engine.run_all_detections(df)
    report = stats.full_report(df, results)

    return df , results, report 

# ─── Render functions ─────────────────────────────────────────

def render_header(t):
    """Top header with title and live timestamp"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"<h1 style='color:{t['accent']};font-family:Courier New;'>"
            f"🔐 CLOUD LOG ANALYZER</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='color:{t['text_secondary']};font-size:0.8rem;"
            f"text-transform:uppercase;letter-spacing:0.1em;'>"
            f"AWS CloudTrail Security Intelligence Platform</p>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<p style='color:{t['text_secondary']};font-size:0.75rem;"
            f"text-align:right;margin-top:20px;'>"
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>",
            unsafe_allow_html=True
        )
    st.markdown(f"<hr style='border-color:{t['border']};margin:0 0 24px 0;'>",
                unsafe_allow_html=True)


def render_metrics(report, t):
    """Top KPI row: total events, unique IPs, risk score, active alerts"""
    score       = report.get("risk_score", 0)
    risk_color  = get_risk_color(score, t)
    risk_label  = get_risk_label(score)

    summary     = report.get("detection_summary", pd.DataFrame())
    alert_count = len(summary[summary["status"] == "ALERT"]) if not summary.empty else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="TOTAL EVENTS",
            value=f"{report.get('total_events', 0):,}"
        )
    with col2:
        st.metric(
            label="UNIQUE IPs",
            value=f"{report.get('unique_ips', 0)}"
        )
    with col3:
        st.metric(
            label="ACTIVE ALERTS",
            value=f"{alert_count} / 11"
        )
    with col4:
        st.markdown(
            f"<div style='background:{t['bg_secondary']};"
            f"border:1px solid {risk_color};"
            f"border-radius:8px;padding:16px;'>"
            f"<p style='color:{t['text_secondary']};font-size:0.75rem;"
            f"text-transform:uppercase;letter-spacing:0.1em;margin:0 0 4px 0;'>"
            f"RISK SCORE</p>"
            f"<p style='color:{risk_color};font-size:2rem;font-weight:700;"
            f"font-family:Courier New;margin:0;'>{score}/100</p>"
            f"<p style='color:{risk_color};font-size:0.75rem;"
            f"text-transform:uppercase;margin:4px 0 0 0;'>{risk_label}</p>"
            f"</div>",
            unsafe_allow_html=True
        )


def render_charts(report, t):
    """Charts row: detection summary, top services, timeline"""
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.2, 1.2, 1.6])

    # Detection summary — horizontal bar
    with col1:
        st.markdown(
            f"<p style='color:{t['text_secondary']};font-size:0.75rem;"
            f"text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'>"
            f"DETECTION STATUS</p>",
            unsafe_allow_html=True
        )
        summary = report.get("detection_summary", pd.DataFrame())
        if not summary.empty:
            colors = [
                t["critical"] if s == "ALERT" else t["low"]
                for s in summary["status"]
            ]
            fig = go.Figure(go.Bar(
                x=summary["count"],
                y=summary["detection"],
                orientation="h",
                marker_color=colors,
                text=summary["status"],
                textposition="auto",
                textfont=dict(color="white", size=10)
            ))
            fig.update_layout(
                paper_bgcolor=t["chart_bg"],
                plot_bgcolor=t["chart_bg"],
                font=dict(color=t["text_secondary"], size=10),
                margin=dict(l=0, r=10, t=10, b=10),
                height=320,
                xaxis=dict(gridcolor=t["border"], zerolinecolor=t["border"]),
                yaxis=dict(gridcolor=t["border"])
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No detection data")

    # Top services — donut chart
    with col2:
        st.markdown(
            f"<p style='color:{t['text_secondary']};font-size:0.75rem;"
            f"text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'>"
            f"TOP SERVICES</p>",
            unsafe_allow_html=True
        )
        top_services = report.get("top_services", pd.DataFrame())
        if not top_services.empty:
            fig = go.Figure(go.Pie(
                labels=top_services["eventSource"],
                values=top_services["count"],
                hole=0.6,
                marker=dict(colors=[
                    t["accent"], t["high"], t["medium"],
                    t["critical"], t["low"]
                ]),
                textfont=dict(color=t["text_primary"], size=10)
            ))
            fig.update_layout(
                paper_bgcolor=t["chart_bg"],
                plot_bgcolor=t["chart_bg"],
                font=dict(color=t["text_secondary"], size=10),
                margin=dict(l=0, r=0, t=10, b=10),
                height=320,
                showlegend=True,
                legend=dict(
                    font=dict(color=t["text_secondary"], size=9),
                    bgcolor=t["chart_bg"]
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No service data")

    # Timeline — line chart
    with col3:
        st.markdown(
            f"<p style='color:{t['text_secondary']};font-size:0.75rem;"
            f"text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'>"
            f"ACTIVITY TIMELINE</p>",
            unsafe_allow_html=True
        )
        def hex_to_rgba(hex_color, alpha=0.13):
                """Converts #RRGGBB to rgba(r, g, b, alpha) for Plotly"""
                hex_color = hex_color.lstrip("#")
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return f"rgba({r}, {g}, {b}, {alpha})"
        timeline = report.get("events_per_hour", pd.DataFrame())
        if not timeline.empty:
            fig = go.Figure(go.Scatter(
                x=timeline["hour"],
                y=timeline["count"],
                mode="lines+markers",
                line=dict(color=t["accent"], width=2),
                marker=dict(color=t["accent"], size=6),
                fill="tozeroy",
                fillcolor=hex_to_rgba(t["accent"], alpha=0.13)
            ))
            fig.update_layout(
                paper_bgcolor=t["chart_bg"],
                plot_bgcolor=t["chart_bg"],
                font=dict(color=t["text_secondary"], size=10),
                margin=dict(l=0, r=10, t=10, b=10),
                height=320,
                xaxis=dict(
                    gridcolor=t["border"],
                    zerolinecolor=t["border"]
                ),
                yaxis=dict(
                    gridcolor=t["border"],
                    zerolinecolor=t["border"]
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data")


def render_cross_detection(report, t):
    """Cross-detection entities — the most powerful insight"""
    st.markdown(
        f"<p style='color:{t['text_secondary']};font-size:0.75rem;"
        f"text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'>"
        f"⚠ CROSS-DETECTION ENTITIES — High Priority Targets</p>",
        unsafe_allow_html=True
    )
    entities = report.get("cross_detection_entities", pd.DataFrame())
    if not entities.empty:
        for _, row in entities.iterrows():
            score_bar = "█" * min(row["detection_count"], 11)
            st.markdown(
                f"<div class='alert-critical'>"
                f"<b>{row['entity']}</b> — "
                f"flagged by {row['detection_count']} detectors: "
                f"{row['detections']}"
                f"</div><br>",
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            f"<div class='alert-clear'>✓ No entity flagged by multiple detectors</div>",
            unsafe_allow_html=True
        )


def render_tables(results, t):
    """Detection detail tabs — one tab per active detection"""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:{t['text_secondary']};font-size:0.75rem;"
        f"text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;'>"
        f"DETECTION DETAILS</p>",
        unsafe_allow_html=True
    )

    # Build tab list — show ALL detections, ALERT first
    detection_labels = {
        "failed_logins":     "🔴 Failed Logins",
        "iam_changes":       "🔴 IAM Changes",
        "credential_abuse":  "🔴 Credential Abuse",
        "critical_events":   "🔴 Critical Events",
        "s3_exfiltration":   "🟠 S3 Exfiltration",
        "ec2_suspicious":    "🟠 EC2 Suspicious",
        "lambda_abuse":      "🟠 Lambda Abuse",
        "data_exfiltration": "🟠 Data Exfiltration",
        "role_chaining":     "🟡 Role Chaining",
        "iam_enumeration":   "🟡 IAM Enumeration",
        "api_calls_by_ip":   "🟡 API Volume",
    }

    tab_names = [
        label for key, label in detection_labels.items()
        if key in results
    ]
    tabs = st.tabs(tab_names)

    for tab, (key, label) in zip(tabs, detection_labels.items()):
        if key not in results:
            continue
        with tab:
            df_result = results[key]
            if df_result.empty:
                st.markdown(
                    f"<div class='alert-clear'>✓ CLEAR — No threats detected</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div class='alert-critical'>"
                    f"⚠ ALERT — {len(df_result)} suspicious "
                    f"{'entities' if len(df_result) > 1 else 'entity'} detected"
                    f"</div><br>",
                    unsafe_allow_html=True
                )
                st.dataframe(
                    df_result,
                    use_container_width=True,
                    hide_index=True
                )


# ─── Sidebar ─────────────────────────────────────────────────

def render_sidebar():
    """Sidebar: theme, source selector, controls"""
    with st.sidebar:
        st.markdown("### ⚙ CONFIGURATION")
        st.markdown("---")

        # Theme selector
        theme_choice = st.selectbox(
            "THEME",
            options=["dark", "light"],
            index=0
        )

        st.markdown("---")
        st.markdown("### 📡 DATA SOURCE")

        source = st.radio(
            "Source",
            options=["Local File", "AWS CloudTrail"],
            label_visibility="collapsed"
        )

        file_path = None
        hours     = 24

        if source == "Local File":
            file_path = st.text_input(
                "FILE PATH",
                value="../data/sample_cloudtrail.json",
                placeholder="path/to/cloudtrail.json"
            )
        else:
            hours = st.slider(
                "TIME WINDOW (hours)",
                min_value=1,
                max_value=72,
                value=24,
                step=1
            )
            st.markdown(
                f"<p style='font-size:0.75rem;'>Fetching last {hours}h</p>",
                unsafe_allow_html=True
            )

        st.markdown("---")

        load_btn = st.button(
            "🔄 LOAD & ANALYZE",
            type="primary",
            use_container_width=True
        )

        st.markdown("---")
        st.markdown(
            "<p style='font-size:0.7rem;text-align:center;'>"
            "Cloud Log Analyzer v1.0<br>"
            "Cloud Security Data Engineer<br>"
            "Voldi BOKANGA</p>",
            unsafe_allow_html=True
        )

    return theme_choice, source, file_path, hours, load_btn
    

# ─── Main ────────────────────────────────────────────────────

def main():
    # Sidebar - get config 

    theme_choice, source , file_path, hours, load_btn = render_sidebar()

    # apply theme 

    t = THEMES[theme_choice]
    apply_theme(t)

    # Header

    render_header(t)

    # Session state — persist data between Streamlit reruns
    if "df" not in st.session_state:
        st.session_state.df      = None
        st.session_state.results = {}
        st.session_state.report  = {}

    # Load data when button clicked
    if load_btn:
        with st.spinner("🔄 Running pipeline..."):
            if source == "Local File":
                if not file_path:
                    st.error("Please provide a file path")
                    return
                df, results, report = load_data_from_file(file_path, t)
            else:
                df, results, report = load_data_from_aws(hours, t)

            st.session_state.df      = df
            st.session_state.results = results
            st.session_state.report  = report

    # Render dashboard if data is loaded
    if st.session_state.report:
        report  = st.session_state.report
        results = st.session_state.results

        # Row 1 — KPIs
        render_metrics(report, t)

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 2 — Charts
        render_charts(report, t)

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 3 — Cross-detection entities
        render_cross_detection(report, t)

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 4 — Detection detail tabs
        render_tables(results, t)

    else:
        # Empty state — before first load
        st.markdown(
            f"<div style='text-align:center;padding:80px 0;"
            f"color:{t['text_secondary']};'>"
            f"<p style='font-size:3rem;'>🔐</p>"
            f"<p style='font-size:1rem;text-transform:uppercase;"
            f"letter-spacing:0.2em;'>Select a data source and click LOAD & ANALYZE</p>"
            f"</div>",
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()