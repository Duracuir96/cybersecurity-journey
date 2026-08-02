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

def _run_pipeline(raw_logs):
    """
    Runs Layers 2-5 with real-time progress feedback.
    Input  : raw_logs list[dict] from Layer 1
    Output : df, results, report
    """
    progress_bar = st.progress(0)
    status_text  = st.empty()

    try:
        # Layer 2 — parse
        status_text.caption("⚙ Layer 2 — Parsing events...")
        parser      = LogParser()
        parsed_logs = parser.parse_json(raw_logs)
        df          = parser.to_dataframe(parsed_logs)
        progress_bar.progress(25)

        # Layer 3 — validate
        status_text.caption("⚙ Layer 3 — Validating data...")
        validator = DataValidator()
        is_valid  = validator.validate_schema(df)
        if not is_valid:
            st.error("❌ Schema validation failed — check your log source")
            return None, {}, {}
        df = validator.clean_data(df)
        progress_bar.progress(50)

        # Layer 4 — detect
        status_text.caption("⚙ Layer 4 — Running detections...")
        engine  = HeuristicEngine()
        results = engine.run_all_detections(df)
        progress_bar.progress(75)

        # Layer 5 — statistics
        status_text.caption("⚙ Layer 5 — Computing statistics...")
        stats  = StatisticsEngine()
        report = stats.full_report(df, results)
        progress_bar.progress(100)

        # Clear progress UI after completion
        status_text.empty()
        progress_bar.empty()

        return df, results, report

    except Exception as e:
        status_text.empty()
        progress_bar.empty()
        st.error(f"❌ Pipeline error: {e}")
        return None, {}, {}


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
    """Top KPI row with tooltips"""
    score      = report.get("risk_score", 0)
    risk_color = get_risk_color(score, t)
    risk_label = get_risk_label(score)

    summary     = report.get("detection_summary", pd.DataFrame())
    alert_count = len(summary[summary["status"] == "ALERT"]) \
                  if not summary.empty else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="TOTAL EVENTS",
            value=f"{report.get('total_events', 0):,}",
            help="Total number of CloudTrail events after validation and cleaning"
        )
    with col2:
        st.metric(
            label="UNIQUE IPs",
            value=f"{report.get('unique_ips', 0)}",
            help="Number of distinct source IP addresses in this dataset"
        )
    with col3:
        st.metric(
            label="ACTIVE ALERTS",
            value=f"{alert_count} / 11",
            help="Number of detectors that found at least one suspicious event"
        )
    with col4:
        st.markdown(
            f"<div style='background:{t['bg_secondary']};"
            f"border:1px solid {risk_color};"
            f"border-radius:8px;padding:16px;'>"
            f"<p style='color:{t['text_secondary']};font-size:0.75rem;"
            f"text-transform:uppercase;letter-spacing:0.1em;margin:0 0 4px 0;'>"
            f"RISK SCORE"
            f"<span style='color:{t['text_secondary']};font-size:0.7rem;"
            f"margin-left:6px;' title='Weighted score across 11 detections."
            f" Critical=25pts, High=15pts, Medium=7pts, Low=5pts'>ⓘ</span>"
            f"</p>"
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


def render_tables(results, detection_config, t):
    """
    Detection detail tabs — one tab per ACTIVE detection.
    Each tab has export CSV button.
    """
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:{t['text_secondary']};font-size:0.75rem;"
        f"text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;'>"
        f"DETECTION DETAILS</p>",
        unsafe_allow_html=True
    )

    detection_labels = {
        "failed_logins":     "🔴 Brute Force",
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

    # Only show tabs for active detections
    active_detections = {
        key: label
        for key, label in detection_labels.items()
        if detection_config.get(key, True) and key in results
    }

    if not active_detections:
        st.info("No detections active — enable at least one in the sidebar")
        return

    tabs = st.tabs(list(active_detections.values()))

    for tab, (key, label) in zip(tabs, active_detections.items()):
        with tab:
            result_df = results[key]

            if result_df.empty:
                st.markdown(
                    f"<div class='alert-clear'>"
                    f"✓ CLEAR — No threats detected</div>",
                    unsafe_allow_html=True
                )
            else:
                # Alert header
                st.markdown(
                    f"<div class='alert-critical'>"
                    f"⚠ ALERT — {len(result_df)} suspicious "
                    f"{'entities' if len(result_df) > 1 else 'entity'} detected"
                    f"</div>",
                    unsafe_allow_html=True
                )

                st.markdown("<br>", unsafe_allow_html=True)

                # Export button + DataFrame side by side
                col_data, col_export = st.columns([4, 1])

                with col_data:
                    st.dataframe(
                        result_df,
                        use_container_width=True,
                        hide_index=True
                    )

                with col_export:
                    csv = result_df.to_csv(index=False)
                    st.download_button(
                        label="⬇ Export CSV",
                        data=csv,
                        file_name=f"{key}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help=f"Download {label} results as CSV"
                    )


# ─── Sidebar ─────────────────────────────────────────────────
def render_sidebar():
    """
    Sidebar with theme, source selector, detection config and thresholds.
    Returns all user config needed by main().
    """
    with st.sidebar:
        st.markdown(
            f"<p style='font-size:0.7rem;text-transform:uppercase;"
            f"letter-spacing:0.15em;color:gray;margin:0;'>"
            f"⚙ CONFIGURATION</p>",
            unsafe_allow_html=True
        )
        st.markdown("---")

        # ── Theme ────────────────────────────────────────────
        theme_choice = st.selectbox("THEME", options=["dark", "light"], index=0)

        st.markdown("---")

        # ── Data source ──────────────────────────────────────
        st.markdown(
            f"<p style='font-size:0.7rem;text-transform:uppercase;"
            f"letter-spacing:0.15em;color:gray;margin:0;'>"
            f"📡 DATA SOURCE</p>",
            unsafe_allow_html=True
        )

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
                min_value=1, max_value=72, value=24, step=1
            )

        st.markdown("---")

        # ── Active detections ─────────────────────────────────
        st.markdown(
            f"<p style='font-size:0.7rem;text-transform:uppercase;"
            f"letter-spacing:0.15em;color:gray;margin:0 0 8px 0;'>"
            f"🎯 ACTIVE DETECTIONS</p>",
            unsafe_allow_html=True
        )

        # Select all / Deselect all
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ All", use_container_width=True):
                for key in st.session_state:
                    if key.startswith("det_"):
                        st.session_state[key] = True
        with col_b:
            if st.button("⬜ None", use_container_width=True):
                for key in st.session_state:
                    if key.startswith("det_"):
                        st.session_state[key] = False

        # Detection checkboxes
        detection_config = {
            "failed_logins":     st.checkbox("🔴 Brute Force",       key="det_failed",    value=True),
            "iam_changes":       st.checkbox("🔴 IAM Changes",       key="det_iam",       value=True),
            "credential_abuse":  st.checkbox("🔴 Credential Abuse",  key="det_cred",      value=True),
            "critical_events":   st.checkbox("🔴 Critical Events",   key="det_critical",  value=True),
            "s3_exfiltration":   st.checkbox("🟠 S3 Exfiltration",   key="det_s3",        value=True),
            "ec2_suspicious":    st.checkbox("🟠 EC2 Suspicious",    key="det_ec2",       value=True),
            "lambda_abuse":      st.checkbox("🟠 Lambda Abuse",      key="det_lambda",    value=True),
            "data_exfiltration": st.checkbox("🟠 Data Exfiltration", key="det_net",       value=True),
            "role_chaining":     st.checkbox("🟡 Role Chaining",     key="det_role",      value=True),
            "iam_enumeration":   st.checkbox("🟡 IAM Enumeration",   key="det_enum",      value=True),
            "api_calls_by_ip":   st.checkbox("🟡 API Volume",        key="det_api",       value=True),
        }

        st.markdown("---")

        # ── Thresholds ────────────────────────────────────────
        st.markdown(
            f"<p style='font-size:0.7rem;text-transform:uppercase;"
            f"letter-spacing:0.15em;color:gray;margin:0 0 8px 0;'>"
            f"⚙ DETECTION THRESHOLDS</p>",
            unsafe_allow_html=True
        )

        with st.expander("Configure thresholds", expanded=False):
            thresholds = {
                "failed_logins": st.slider(
                    "Brute Force — min attempts",
                    min_value=2, max_value=20, value=3,
                    help="Flag an IP after this many ConsoleLogin attempts"
                ),
                "api_calls": st.slider(
                    "API Volume — min calls",
                    min_value=5, max_value=100, value=10,
                    help="Flag an IP making more than this many API calls"
                ),
                "s3_exfiltration": st.slider(
                    "S3 Exfiltration — min events",
                    min_value=2, max_value=50, value=5,
                    help="Flag a user downloading more than this many S3 objects"
                ),
                "iam_enumeration": st.slider(
                    "IAM Enumeration — min calls",
                    min_value=2, max_value=10, value=3,
                    help="Flag a user making more than this many enumeration calls"
                ),
                "role_chaining": st.slider(
                    "Role Chaining — min assumes",
                    min_value=2, max_value=10, value=3,
                    help="Flag a user assuming more than this many roles"
                ),
            }
    
            thresholds = {
                "failed_logins":    3,
                "api_calls":        10,
                "s3_exfiltration":  5,
                "iam_enumeration":  3,
                "role_chaining":    3,
            }

        st.markdown("---")

        # ── Load button ───────────────────────────────────────
        load_btn = st.button(
            "🔄 LOAD & ANALYZE",
            type="primary",
            use_container_width=True
        )

        st.markdown("---")
        st.markdown(
            "<p style='font-size:0.7rem;text-align:center;color:gray;'>"
            "Cloud Log Analyzer v1.0<br>"
            "Cloud Security Data Engineer<br>"
            "Voldi BOKANGA</p>",
            unsafe_allow_html=True
        )

    return theme_choice, source, file_path, hours, \
           detection_config, thresholds, load_btn


    
# ─── Main ────────────────────────────────────────────────────

def main():
    # Sidebar — get full config
    theme_choice, source, file_path, hours, \
    detection_config, thresholds, load_btn = render_sidebar()

    # Apply theme
    t = THEMES[theme_choice]
    apply_theme(t)

    # Header
    render_header(t)

    # Session state
    if "df" not in st.session_state:
        st.session_state.df      = None
        st.session_state.results = {}
        st.session_state.report  = {}

    # Load data when button clicked
    if load_btn:
        with st.spinner(""):
            if source == "Local File":
                if not file_path:
                    st.error("❌ Please provide a file path")
                    return
                # Layer 1
                connector = AWSConnector()
                raw_logs  = connector.fetch_logs(
                    source="file", file_path=file_path
                )
            else:
                # Layer 1
                connector = AWSConnector()
                connector.connect()
                end_time   = datetime.utcnow()
                start_time = end_time - timedelta(hours=hours)
                raw_logs   = connector.fetch_logs(
                    source="aws",
                    start_time=start_time,
                    end_time=end_time,
                    max_events=50
                )

            if not raw_logs:
                st.warning("⚠ No logs received — check your source configuration")
                return

            st.success(f"✅ {len(raw_logs)} events collected from {source}")

            # Layers 2-5 with progress
            df, results, report = _run_pipeline(raw_logs)

            if df is None:
                return

            # Filter results based on active detections + thresholds
            # Re-run only active detections with custom thresholds
            engine = HeuristicEngine()
            filtered_results = {}

            for key, is_active in detection_config.items():
                if not is_active:
                    # Inactive — replace with empty DataFrame
                    filtered_results[key] = pd.DataFrame()
                    continue

                # Re-run with custom threshold if applicable
                if key == "failed_logins":
                    filtered_results[key] = engine.detect_failed_logins(
                        df, threshold=thresholds["failed_logins"]
                    )
                elif key == "api_calls_by_ip":
                    filtered_results[key] = engine.count_api_calls_by_ip(
                        df, threshold=thresholds["api_calls"]
                    )
                elif key == "s3_exfiltration":
                    filtered_results[key] = engine.detect_s3_exfiltration(
                        df, threshold=thresholds["s3_exfiltration"]
                    )
                elif key == "iam_enumeration":
                    filtered_results[key] = engine.detect_iam_enumeration(
                        df, threshold=thresholds["iam_enumeration"]
                    )
                elif key == "role_chaining":
                    filtered_results[key] = engine.detect_role_chaining(
                        df, threshold=thresholds["role_chaining"]
                    )
                else:
                    filtered_results[key] = results[key]

            # Recompute report with filtered results
            stats  = StatisticsEngine()
            report = stats.full_report(df, filtered_results)

            st.session_state.df      = df
            st.session_state.results = filtered_results
            st.session_state.report  = report

    # Render dashboard if data is loaded
    if st.session_state.report:
        report  = st.session_state.report
        results = st.session_state.results

        render_metrics(report, t)
        st.markdown("<br>", unsafe_allow_html=True)
        render_charts(report, t)
        st.markdown("<br>", unsafe_allow_html=True)
        render_cross_detection(report, t)
        st.markdown("<br>", unsafe_allow_html=True)
        render_tables(results, detection_config, t)

    else:

        # ── Empty state ──────────────────────────────────────
        st.markdown("<br><br>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                f"""
                <div style='text-align:center;padding:48px 32px;
                background:{t['bg_secondary']};border:1px solid {t['border']};
                border-radius:12px;'>

                <p style='font-size:3rem;margin:0;'>🔐</p>

                <p style='color:{t['accent']};font-size:1.1rem;
                font-family:Courier New;font-weight:700;
                text-transform:uppercase;letter-spacing:0.15em;
                margin:16px 0 8px 0;'>
                Cloud Log Analyzer
                </p>

                <p style='color:{t['text_secondary']};font-size:0.85rem;
                margin:0 0 24px 0;'>
                AWS CloudTrail Security Intelligence Platform
                </p>

                <hr style='border-color:{t['border']};margin:24px 0;'>

                <p style='color:{t['text_primary']};font-size:0.9rem;
                text-align:left;margin:0 0 12px 0;font-weight:600;'>
                🚀 Getting Started
                </p>

                <p style='color:{t['text_secondary']};font-size:0.82rem;
                text-align:left;line-height:1.8;margin:0;'>
                1️⃣ Select a <b style='color:{t['accent']};'>data source</b>
                in the sidebar<br>
                2️⃣ Configure the <b style='color:{t['accent']};'>parameters</b><br>
                3️⃣ Click <b style='color:{t['accent']};'>LOAD & ANALYZE</b><br>
                4️⃣ Review the <b style='color:{t['accent']};'>
                detections and risk score</b>
                </p>

                <hr style='border-color:{t['border']};margin:24px 0;'>

                <p style='color:{t['text_secondary']};font-size:0.78rem;
                text-align:left;line-height:1.8;margin:0;'>
                📁 <b>Local File</b> — development & testing<br>
                ☁️ <b>AWS CloudTrail</b> — real production logs<br>
                🎯 <b>11 detections</b> covering IAM, S3, EC2, Lambda, Network<br>
                📊 <b>Risk Score</b> 0–100 weighted by severity
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )
        


if __name__ == "__main__":
    main()