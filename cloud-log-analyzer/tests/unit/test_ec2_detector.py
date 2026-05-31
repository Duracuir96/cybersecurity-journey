# src/tests/unit/test_ec2_detector.py

import pytest
import pandas as pd
from src.analysis.detectors.ec2_detector import EC2Detector


@pytest.fixture
def detector():
    return EC2Detector()

@pytest.fixture
def empty_dataframe():
    return pd.DataFrame(columns=[
        "eventTime", "eventName", "eventSource",
        "sourceIPAddress", "userName"
    ])

@pytest.fixture
def ec2_suspicious_dataframe():
    """DataFrame with dangerous EC2 events mixed with normal ones"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "RunInstances",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:01:00Z"),
            "eventName":       "AuthorizeSecurityGroupIngress",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:02:00Z"),
            "eventName":       "CreateKeyPair",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:03:00Z"),
            "eventName":       "DescribeInstances",  # normal — must be excluded
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userName":        "normal_user"
        }
    ])


class TestEC2Detector:

    def test_returns_dataframe(self, detector, ec2_suspicious_dataframe):
        """Should always return a DataFrame"""
        result = detector.detect_ec2_suspicious_activity(ec2_suspicious_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_detects_dangerous_events(self, detector, ec2_suspicious_dataframe):
        """Should detect all dangerous EC2 events"""
        result = detector.detect_ec2_suspicious_activity(ec2_suspicious_dataframe)
        assert len(result) == 3

    def test_excludes_normal_events(self, detector, ec2_suspicious_dataframe):
        """Should not include normal EC2 events"""
        result = detector.detect_ec2_suspicious_activity(ec2_suspicious_dataframe)
        assert "DescribeInstances" not in result["eventName"].values

    def test_detects_run_instances(self, detector, ec2_suspicious_dataframe):
        """Should detect RunInstances as suspicious"""
        result = detector.detect_ec2_suspicious_activity(ec2_suspicious_dataframe)
        assert "RunInstances" in result["eventName"].values

    def test_detects_create_key_pair(self, detector, ec2_suspicious_dataframe):
        """Should detect CreateKeyPair as suspicious"""
        result = detector.detect_ec2_suspicious_activity(ec2_suspicious_dataframe)
        assert "CreateKeyPair" in result["eventName"].values

    def test_returns_empty_on_empty_input(self, detector, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        result = detector.detect_ec2_suspicious_activity(empty_dataframe)
        assert len(result) == 0

    def test_suspicious_events_list_defined(self, detector):
        """EC2_SUSPICIOUS_EVENTS must contain critical events"""
        assert "RunInstances" in detector.EC2_SUSPICIOUS_EVENTS
        assert "DeleteFlowLogs" in detector.EC2_SUSPICIOUS_EVENTS