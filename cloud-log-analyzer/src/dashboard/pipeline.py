# src/dashboard/pipeline.py

import sys
import os
import streamlit as st
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_collection.aws_connector import AWSConnector
from data_processing.log_parser import LogParser
from data_processing.data_validator import DataValidator
from analysis.heuristic_engine import HeuristicEngine
from analysis.statistics_engine import StatisticsEngine


def run_pipeline(source, file_path, hours, detection_config, thresholds):
    """
    Runs Layers 1-5 with real-time progress feedback.
    Output : df, results, report
    """
    progress = st.progress(0)
    status = st.empty()

    try:
        # ── Layer 1 — collect ─────────────────────────────────
        status.markdown(_status_text("Layer 1 — Collecting logs..."),
                        unsafe_allow_html=True)
        connector = AWSConnector()

        if source == "AWS CloudTrail":
            connector.connect()
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            raw_logs = connector.fetch_logs(
                source="aws", start_time=start_time,
                end_time=end_time, max_events=50,
            )
        else:
            raw_logs = connector.fetch_logs(source="file", file_path=file_path)

        progress.progress(20)

        if not raw_logs:
            status.empty()
            progress.empty()
            st.warning("No logs received — check your source configuration")
            return None, {}, {}

        # ── Layer 2 — parse ───────────────────────────────────
        status.markdown(_status_text("Layer 2 — Parsing events..."),
                        unsafe_allow_html=True)
        parser = LogParser()
        parsed_logs = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed_logs)
        progress.progress(40)

        # ── Layer 3 — validate ────────────────────────────────
        status.markdown(_status_text("Layer 3 — Validating data..."),
                        unsafe_allow_html=True)
        validator = DataValidator()
        is_valid = validator.validate_schema(df)

        if not is_valid:
            status.empty()
            progress.empty()
            st.error("Schema validation failed — check your log source")
            return None, {}, {}

        df = validator.clean_data(df)
        progress.progress(60)

        # ── Layer 4 — detect ──────────────────────────────────
        status.markdown(_status_text("Layer 4 — Running detections..."),
                        unsafe_allow_html=True)
        engine = HeuristicEngine()
        results = _run_detections(engine, df, detection_config, thresholds)
        progress.progress(80)

        # ── Layer 5 — statistics ──────────────────────────────
        status.markdown(_status_text("Layer 5 — Computing statistics..."),
                        unsafe_allow_html=True)
        stats = StatisticsEngine()
        report = stats.full_report(df, results)
        progress.progress(100)

        status.empty()
        progress.empty()
        return df, results, report

    except Exception as e:
        status.empty()
        progress.empty()
        st.error(f"Pipeline error: {e}")
        return None, {}, {}


def _run_detections(engine, df, detection_config, thresholds):
    """Runs only active detections with custom thresholds."""
    import pandas as pd
    results = {}

    detection_runners = {
        "failed_logins": lambda: engine.detect_failed_logins(
            df, threshold=thresholds.get("failed_logins", 3)),
        "iam_changes": lambda: engine.detect_iam_changes(df),
        "credential_abuse": lambda: engine.detect_credential_abuse(df),
        "critical_events": lambda: engine.detect_critical_events(df),
        "s3_exfiltration": lambda: engine.detect_s3_exfiltration(
            df, threshold=thresholds.get("s3_exfiltration", 5)),
        "ec2_suspicious": lambda: engine.detect_ec2_suspicious_activity(df),
        "lambda_abuse": lambda: engine.detect_lambda_abuse(df),
        "data_exfiltration": lambda: engine.detect_data_exfiltration(df),
        "role_chaining": lambda: engine.detect_role_chaining(
            df, threshold=thresholds.get("role_chaining", 3)),
        "iam_enumeration": lambda: engine.detect_iam_enumeration(
            df, threshold=thresholds.get("iam_enumeration", 3)),
        "api_calls_by_ip": lambda: engine.count_api_calls_by_ip(
            df, threshold=thresholds.get("api_calls", 10)),
    }

    for key, runner in detection_runners.items():
        if detection_config.get(key, True):
            results[key] = runner()
        else:
            results[key] = pd.DataFrame()

    return results


def _status_text(message):
    return (
        f"<p style='color:#6B7280;font-size:0.75rem;text-transform:uppercase;"
        f"letter-spacing:0.08em;margin:0;'>{message}</p>"
    )