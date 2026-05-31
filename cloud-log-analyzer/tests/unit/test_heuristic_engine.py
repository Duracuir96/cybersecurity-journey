# src/tests/unit/test_heuristic_engine.py

import pytest
import pandas as pd
from src.analysis.heuristic_engine import HeuristicEngine


@pytest.fixture
def engine():
    return HeuristicEngine()

@pytest.fixture
def empty_dataframe():
    return pd.DataFrame(columns=[
        "eventTime", "eventName", "eventSource",
        "sourceIPAddress", "userName"
    ])

@pytest.fixture
def full_attack_dataframe():
    """DataFrame containing all attack patterns at once"""
    return pd.DataFrame([
        # Brute force
        *[{
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }] * 4,
        # IAM change
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:01:00Z"),
            "eventName":       "CreateUser",
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        # S3 exfiltration
        *[{
            "eventTime":       pd.Timestamp("2026-01-25T10:02:00Z"),
            "eventName":       "GetObject",
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }] * 6,
        # EC2 suspicious
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:03:00Z"),
            "eventName":       "RunInstances",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        # Lambda abuse
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:04:00Z"),
            "eventName":       "UpdateFunctionCode",
            "eventSource":     "lambda.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        # Critical network
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:05:00Z"),
            "eventName":       "DeleteFlowLogs",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }
    ])


class TestHeuristicEngineFacade:

    def test_all_detectors_initialized(self, engine):
        """HeuristicEngine must initialize all detector instances"""
        assert engine.iam     is not None
        assert engine.s3      is not None
        assert engine.ec2     is not None
        assert engine.network is not None
        assert engine.lambda_ is not None

    def test_run_all_detections_returns_dict(self, engine, full_attack_dataframe):
        """run_all_detections must return a dict"""
        result = engine.run_all_detections(full_attack_dataframe)
        assert isinstance(result, dict)

    def test_run_all_detections_has_all_keys(self, engine, full_attack_dataframe):
        """run_all_detections dict must contain all detection keys"""
        result = engine.run_all_detections(full_attack_dataframe)
        expected_keys = {
            "failed_logins", "iam_changes", "iam_enumeration",
            "credential_abuse", "role_chaining", "api_calls_by_ip",
            "s3_exfiltration", "ec2_suspicious",
            "data_exfiltration", "critical_events", "lambda_abuse"
        }
        assert set(result.keys()) == expected_keys

    def test_run_all_detections_values_are_dataframes(
        self, engine, full_attack_dataframe
    ):
        """Every value in run_all_detections result must be a DataFrame"""
        result = engine.run_all_detections(full_attack_dataframe)
        for key, value in result.items():
            assert isinstance(value, pd.DataFrame), \
                f"{key} must return a DataFrame"

    def test_facade_delegates_failed_logins(self, engine, full_attack_dataframe):
        """detect_failed_logins must delegate to IAMDetector"""
        result = engine.detect_failed_logins(full_attack_dataframe, threshold=3)
        assert "1.2.3.4" in result["sourceIPAddress"].values

    def test_facade_delegates_s3_exfiltration(self, engine, full_attack_dataframe):
        """detect_s3_exfiltration must delegate to S3Detector"""
        result = engine.detect_s3_exfiltration(full_attack_dataframe, threshold=5)
        assert "alice" in result["userName"].values

    def test_facade_delegates_ec2_suspicious(self, engine, full_attack_dataframe):
        """detect_ec2_suspicious_activity must delegate to EC2Detector"""
        result = engine.detect_ec2_suspicious_activity(full_attack_dataframe)
        assert "RunInstances" in result["eventName"].values

    def test_facade_delegates_critical_events(self, engine, full_attack_dataframe):
        """detect_critical_events must delegate to NetworkDetector"""
        result = engine.detect_critical_events(full_attack_dataframe)
        assert "DeleteFlowLogs" in result["eventName"].values

    def test_facade_delegates_lambda_abuse(self, engine, full_attack_dataframe):
        """detect_lambda_abuse must delegate to LambdaDetector"""
        result = engine.detect_lambda_abuse(full_attack_dataframe)
        assert "UpdateFunctionCode" in result["eventName"].values

    def test_run_all_on_empty_input(self, engine, empty_dataframe):
        """run_all_detections must handle empty input without crash"""
        result = engine.run_all_detections(empty_dataframe)
        for key, value in result.items():
            assert isinstance(value, pd.DataFrame)
            assert len(value) == 0