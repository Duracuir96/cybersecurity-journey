# src/tests/unit/test_network_detector.py

import pytest
import pandas as pd
from src.analysis.detectors.network_detector import NetworkDetector


@pytest.fixture
def detector():
    return NetworkDetector()

@pytest.fixture
def empty_dataframe():
    return pd.DataFrame(columns=[
        "eventTime", "eventName", "eventSource",
        "sourceIPAddress", "userName"
    ])

@pytest.fixture
def network_exfiltration_dataframe():
    """DataFrame with dangerous network events mixed with normal ones"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "DeleteFlowLogs",  # critical — covering tracks
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:01:00Z"),
            "eventName":       "CreateVpcPeeringConnection",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:02:00Z"),
            "eventName":       "StopLogging",  # critical — disabling audit
            "eventSource":     "cloudtrail.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:03:00Z"),
            "eventName":       "DescribeVpcs",  # normal — must be excluded
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userName":        "normal_user"
        }
    ])


class TestNetworkDetector:

    def test_returns_dataframe(self, detector, network_exfiltration_dataframe):
        """Should always return a DataFrame"""
        result = detector.detect_data_exfiltration(network_exfiltration_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_detects_dangerous_network_events(
        self, detector, network_exfiltration_dataframe
    ):
        """Should detect all dangerous network events"""
        result = detector.detect_data_exfiltration(network_exfiltration_dataframe)
        assert len(result) == 3

    def test_excludes_normal_events(self, detector, network_exfiltration_dataframe):
        """Should not include normal network events"""
        result = detector.detect_data_exfiltration(network_exfiltration_dataframe)
        assert "DescribeVpcs" not in result["eventName"].values

    def test_detects_delete_flow_logs(self, detector, network_exfiltration_dataframe):
        """Should detect DeleteFlowLogs as exfiltration indicator"""
        result = detector.detect_data_exfiltration(network_exfiltration_dataframe)
        assert "DeleteFlowLogs" in result["eventName"].values

    def test_critical_events_detects_only_critical(
        self, detector, network_exfiltration_dataframe
    ):
        """detect_critical_events must return only critical events"""
        result = detector.detect_critical_events(network_exfiltration_dataframe)
        assert len(result) == 2  # DeleteFlowLogs + StopLogging
        for event in result["eventName"]:
            assert event in detector.CRITICAL_EVENTS

    def test_returns_empty_on_empty_input(self, detector, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        result = detector.detect_data_exfiltration(empty_dataframe)
        assert len(result) == 0

    def test_critical_events_list_defined(self, detector):
        """CRITICAL_EVENTS must contain the most dangerous events"""
        assert "DeleteFlowLogs" in detector.CRITICAL_EVENTS
        assert "StopLogging" in detector.CRITICAL_EVENTS
        assert "DeleteTrail" in detector.CRITICAL_EVENTS