# src/main.py

from datetime import datetime, timedelta
from data_collection.aws_connector import AWSConnector
from data_processing.log_parser import LogParser
from data_processing.data_validator import DataValidator
from analysis.heuristic_engine import HeuristicEngine
from analysis.statistics_engine import StatisticsEngine


# ── SOURCE SELECTOR ──────────────────────────────────────────
# Change this line to switch data source in terminal mode
# "file" → local JSON file (development)
# "aws"  → real AWS CloudTrail API (production)
SOURCE    = "aws"
FILE_PATH = "../data/sample_cloudtrail.json"
HOURS     = 24
MAX_EVENTS = 10
# ─────────────────────────────────────────────────────────────


def run_pipeline(source="file", file_path=None, hours=24, max_events=50):
    """
    Runs the complete pipeline Layers 1-5.
    Used by both main.py (terminal) and dashboard/app.py.

    Input  : source ("file" or "aws"), optional params
    Output : df (DataFrame), results (dict), report (dict)
    """
    connector = AWSConnector()
    parser    = LogParser()
    validator = DataValidator()
    engine    = HeuristicEngine()
    stats     = StatisticsEngine()

    # Layer 1 — collect
    if source == "aws":
        connector.connect()
        end_time   = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        logs = connector.fetch_logs(
            source="aws",
            start_time=start_time,
            end_time=end_time,
            max_events=max_events
        )
    else:
        logs = connector.fetch_logs(
            source="file",
            file_path=file_path
        )

    if not logs:
        print("[WARN] No logs received")
        return None, {}, {}

    print(f"[INFO] {len(logs)} logs received")

    # Layer 2 — parse
    parsed_logs = parser.parse_json(logs)
    df          = parser.to_dataframe(parsed_logs)

    print(f"[INFO] DataFrame shape: {df.shape}")

    # Layer 3 — validate
    is_valid = validator.validate_schema(df)

    if not is_valid:
        print("[STOP] Invalid DataFrame — check the parser")
        return df, {}, {}

    df = validator.clean_data(df)

    # Layer 4 — analyze
    results = engine.run_all_detections(df)

    # Layer 5 — statistics
    report = stats.full_report(df, results)

    return df, results, report


if __name__ == "__main__":
    """
    Terminal mode.
    Change SOURCE at the top of this file to switch data source.
    For dashboard: streamlit run src/dashboard/app.py
    """

    df, results, report = run_pipeline(
        source=SOURCE,
        file_path=FILE_PATH,
        hours=HOURS,
        max_events=MAX_EVENTS
    )

    if df is None or df.empty:
        print("[STOP] No data to display")
        exit()

    # Layer 4 — print detections
    for detection_name, result_df in results.items():
        print(f"\n── {detection_name} ────────────────")
        if not result_df.empty:
            print(result_df)
        else:
            print("No threats detected")

    # Layer 5 — print statistics
    print(f"\n── Total Events : {report['total_events']} ────────")
    print(f"── Unique IPs   : {report['unique_ips']} ──────────")
    print(f"── Risk Score   : {report['risk_score']}/100 ──────")

    print("\n── Top Services ─────────────────────────")
    print(report["top_services"])

    print("\n── Detection Summary ────────────────────")
    print(report["detection_summary"])

    print("\n── Cross-Detection Entities ─────────────")
    if not report["cross_detection_entities"].empty:
        print(report["cross_detection_entities"])
    else:
        print("No entity flagged by multiple detectors")