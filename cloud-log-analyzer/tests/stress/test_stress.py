# src/tests/stress/test_stress.py

import json
import pytest
import pandas as pd
from src.data_collection.aws_connector import AWSConnector
from src.data_processing.log_parser import LogParser
from src.data_processing.data_validator import DataValidator
from src.analysis.heuristic_engine import HeuristicEngine
from src.analysis.statistics_engine import StatisticsEngine


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def connector():
    return AWSConnector()

@pytest.fixture
def parser():
    return LogParser()

@pytest.fixture
def validator():
    return DataValidator()

@pytest.fixture
def heuristic_engine():
    return HeuristicEngine()

@pytest.fixture
def stats_engine():
    return StatisticsEngine()


# ─── Layer 1 — AWSConnector under extreme conditions ─────────

class TestConnectorStress:

    def test_empty_json_object_returns_empty_list(self, connector, tmp_path):
        """A file containing just {} must return empty list, not crash"""
        # Arrange
        file = tmp_path / "empty_object.json"
        file.write_text("{}")

        # Act
        result = connector._load_from_file(str(file))

        # Assert
        assert result == []

    def test_severely_corrupted_json_returns_empty_list(self, connector, tmp_path):
        """Severely corrupted JSON must return empty list, not crash"""
        # Arrange
        file = tmp_path / "corrupted.json"
        file.write_text("{{{{{ not json at all !!! ###")

        # Act
        result = connector._load_from_file(str(file))

        # Assert
        assert result == []

    def test_binary_garbage_file_does_not_crash(self, connector, tmp_path):
        """A non-UTF8 binary file must not crash the connector (Fix 1)"""
        # Arrange
        file = tmp_path / "binary.json"
        file.write_bytes(b"\x80\x81\x82\x83\xff\xfe")

        # Act
        result = connector._load_from_file(str(file))

        # Assert
        assert result == []

    def test_aws_source_without_connection_returns_empty_list(self, connector):
        """fetch_logs with source=aws and no connect() must not crash"""
        # Arrange
        from datetime import datetime, timedelta
        end_time   = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)

        # Act
        result = connector.fetch_logs(
            source="aws", start_time=start_time, end_time=end_time
        )

        # Assert
        assert result == []

    def test_deeply_nested_garbage_records_does_not_crash(self, connector, tmp_path):
        """Records full of unexpected nested structures must not crash parser later"""
        # Arrange
        data = {"Records": [{"weird": {"a": {"b": {"c": [1, 2, {"d": None}]}}}}]}
        file = tmp_path / "nested.json"
        file.write_text(json.dumps(data))

        # Act
        result = connector._load_from_file(str(file))

        # Assert — returns the record as-is, doesn't crash
        assert len(result) == 1


# ─── Layer 3 — DataValidator under extreme conditions ────────

class TestValidatorStress:

    def test_all_nat_dataframe_returns_empty(self, validator):
        """A DataFrame where every eventTime is NaT must return empty cleanly"""
        # Arrange — 100 rows, all invalid timestamps
        df = pd.DataFrame([{
            "eventTime":       pd.NaT,
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }] * 100)

        # Act
        result = validator.clean_data(df)

        # Assert
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_missing_columns_returns_false(self, validator):
        """validate_schema must return False clearly, not crash"""
        # Arrange — DataFrame missing 4 of 5 required columns
        df = pd.DataFrame({"eventName": ["ConsoleLogin"]})

        # Act
        result = validator.validate_schema(df)

        # Assert
        assert result is False

    def test_all_empty_eventname_returns_empty(self, validator):
        """A DataFrame where every eventName is empty must return empty cleanly"""
        # Arrange
        df = pd.DataFrame([{
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }] * 50)

        # Act
        result = validator.clean_data(df)

        # Assert
        assert len(result) == 0

    def test_completely_empty_dataframe_with_schema_is_valid(self, validator):
        """An empty DataFrame with correct columns must pass validation"""
        # Arrange
        df = pd.DataFrame(columns=[
            "eventTime", "eventName", "eventSource",
            "sourceIPAddress", "userName"
        ])

        # Act
        is_valid = validator.validate_schema(df)
        cleaned  = validator.clean_data(df)

        # Assert
        assert is_valid is True
        assert len(cleaned) == 0


# ─── Layer 4 — HeuristicEngine under extreme conditions ──────

class TestHeuristicEngineStress:

    def test_run_all_detections_on_empty_dataframe(self, heuristic_engine):
        """run_all_detections on completely empty DataFrame must not crash"""
        # Arrange
        df = pd.DataFrame(columns=[
            "eventTime", "eventName", "eventSource",
            "sourceIPAddress", "userName"
        ])

        # Act
        results = heuristic_engine.run_all_detections(df)

        # Assert — every detector returns empty DataFrame
        assert isinstance(results, dict)
        for name, result_df in results.items():
            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) == 0

    def test_run_all_detections_on_single_row(self, heuristic_engine):
        """run_all_detections must handle a single-row DataFrame gracefully"""
        # Arrange
        df = pd.DataFrame([{
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }])

        # Act
        results = heuristic_engine.run_all_detections(df)

        # Assert — no crash, single login below threshold
        assert isinstance(results, dict)
        assert len(results["failed_logins"]) == 0

    def test_dataframe_with_all_unknown_values(self, heuristic_engine):
        """A DataFrame where every value is 'unknown' must not crash detectors"""
        # Arrange
        df = pd.DataFrame([{
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "AssumeRole",
            "eventSource":     "sts.amazonaws.com",
            "sourceIPAddress": "unknown",
            "userName":        "unknown"
        }] * 10)

        # Act
        results = heuristic_engine.run_all_detections(df)

        # Assert — runs without crashing
        assert isinstance(results, dict)
        for name, result_df in results.items():
            assert isinstance(result_df, pd.DataFrame)


# ─── Layer 5 — StatisticsEngine under extreme conditions ─────

class TestStatisticsEngineStress:

    def test_risk_score_on_empty_results_dict(self, stats_engine):
        """risk_score on a completely empty dict must return 0"""
        # Arrange
        results = {}

        # Act
        score = stats_engine.risk_score(results)

        # Assert
        assert score == 0

    def test_detection_summary_on_empty_results_dict(self, stats_engine):
        """detection_summary on empty dict must return empty DataFrame"""
        # Arrange
        results = {}

        # Act
        result = stats_engine.detection_summary(results)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_cross_detection_entities_with_nan_values(self, stats_engine):
        """Detection results containing NaN entities must not crash"""
        # Arrange — sourceIPAddress contains NaN
        results = {
            "failed_logins": pd.DataFrame([
                {"sourceIPAddress": float("nan"), "login_count": 5},
                {"sourceIPAddress": "1.2.3.4",    "login_count": 3}
            ]),
            "api_calls_by_ip": pd.DataFrame([
                {"sourceIPAddress": "1.2.3.4", "call_count": 12}
            ])
        }

        # Act
        result = stats_engine.cross_detection_entities(results, min_detections=2)

        # Assert — NaN dropped, "1.2.3.4" still detected
        assert "1.2.3.4" in result["entity"].values

    def test_full_report_on_completely_empty_inputs(self, stats_engine):
        """full_report must not crash with empty DataFrame and empty results dict"""
        # Arrange
        df = pd.DataFrame(columns=[
            "eventTime", "eventName", "eventSource",
            "sourceIPAddress", "userName"
        ])
        results = {}

        # Act
        report = stats_engine.full_report(df, results)

        # Assert
        assert report["total_events"] == 0
        assert report["risk_score"] == 0
        assert len(report["detection_summary"]) == 0

    def test_events_per_hour_with_single_event(self, stats_engine):
        """events_per_hour must work correctly with exactly one event"""
        # Arrange
        df = pd.DataFrame([{
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }])

        # Act
        result = stats_engine.events_per_hour(df)

        # Assert
        assert len(result) == 1
        assert result.iloc[0]["count"] == 1


# ─── Full pipeline under extreme conditions ──────────────────

class TestFullPipelineStress:

    def test_pipeline_with_malformed_records(
        self, connector, parser, validator, heuristic_engine, stats_engine,
        tmp_path
    ):
        """
        Pipeline must survive a file mixing well-formed and malformed records:
        - completely empty record
        - record missing all fields except eventName
        - record with empty userIdentity
        - one fully valid record
        """
        # Arrange
        data = {
            "Records": [
                {},                                  # completely empty
                {"eventName": "ConsoleLogin"},        # missing eventTime
                {
                    "eventName":       "CreateUser",
                    "eventSource":     "iam.amazonaws.com",
                    "sourceIPAddress": "1.2.3.4",
                    "userIdentity":    {},             # empty userIdentity
                    "eventTime":       "2026-01-25T10:00:00Z"
                },
                {
                    "eventName":       "ListBuckets",
                    "eventSource":     "s3.amazonaws.com",
                    "sourceIPAddress": "5.6.7.8",
                    "userIdentity":    {"type": "IAMUser", "userName": "alice"},
                    "eventTime":       "2026-01-25T11:00:00Z"
                }
            ]
        }
        file = tmp_path / "malformed.json"
        file.write_text(json.dumps(data))

        # Act
        raw_logs = connector.fetch_logs(source="file", file_path=str(file))
        parsed   = parser.parse_json(raw_logs)
        df       = parser.to_dataframe(parsed)
        df       = validator.clean_data(df)
        results  = heuristic_engine.run_all_detections(df)
        report   = stats_engine.full_report(df, results)

        # Assert — only the 2 records with valid eventTime+eventName survive
        assert len(df) == 2
        assert report["total_events"] == 2
        assert isinstance(results, dict)
        assert isinstance(report, dict)