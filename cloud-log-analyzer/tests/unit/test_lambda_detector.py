# src/tests/unit/test_lambda_detector.py

import pytest
import pandas as pd
from src.analysis.detectors.lambda_detector import LambdaDetector


@pytest.fixture
def detector():
    return LambdaDetector()

@pytest.fixture
def empty_dataframe():
    return pd.DataFrame(columns=[
        "eventTime", "eventName", "eventSource",
        "sourceIPAddress", "userName"
    ])

@pytest.fixture
def lambda_abuse_dataframe():
    """DataFrame with dangerous Lambda events mixed with normal ones"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "UpdateFunctionCode",  # code injection
            "eventSource":     "lambda.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:01:00Z"),
            "eventName":       "AddPermission",
            "eventSource":     "lambda.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:02:00Z"),
            "eventName":       "CreateFunction",
            "eventSource":     "lambda.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:03:00Z"),
            "eventName":       "GetFunction",  # normal — must be excluded
            "eventSource":     "lambda.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userName":        "normal_user"
        }
    ])


class TestLambdaDetector:

    def test_returns_dataframe(self, detector, lambda_abuse_dataframe):
        """Should always return a DataFrame"""
        result = detector.detect_lambda_abuse(lambda_abuse_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_detects_dangerous_lambda_events(self, detector, lambda_abuse_dataframe):
        """Should detect all dangerous Lambda events"""
        result = detector.detect_lambda_abuse(lambda_abuse_dataframe)
        assert len(result) == 3

    def test_excludes_normal_events(self, detector, lambda_abuse_dataframe):
        """Should not include normal Lambda events"""
        result = detector.detect_lambda_abuse(lambda_abuse_dataframe)
        assert "GetFunction" not in result["eventName"].values

    def test_detects_update_function_code(self, detector, lambda_abuse_dataframe):
        """Should detect UpdateFunctionCode as most critical Lambda event"""
        result = detector.detect_lambda_abuse(lambda_abuse_dataframe)
        assert "UpdateFunctionCode" in result["eventName"].values

    def test_detects_add_permission(self, detector, lambda_abuse_dataframe):
        """Should detect AddPermission as suspicious"""
        result = detector.detect_lambda_abuse(lambda_abuse_dataframe)
        assert "AddPermission" in result["eventName"].values

    def test_returns_empty_on_empty_input(self, detector, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        result = detector.detect_lambda_abuse(empty_dataframe)
        assert len(result) == 0

    def test_suspicious_events_list_defined(self, detector):
        """LAMBDA_SUSPICIOUS_EVENTS must contain critical events"""
        assert "UpdateFunctionCode" in detector.LAMBDA_SUSPICIOUS_EVENTS
        assert "AddPermission" in detector.LAMBDA_SUSPICIOUS_EVENTS