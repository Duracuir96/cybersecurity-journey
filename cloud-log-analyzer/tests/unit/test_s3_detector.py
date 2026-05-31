# src/tests/unit/test_s3_detector.py

import pytest
import pandas as pd
from src.analysis.detectors.s3_detector import S3Detector


@pytest.fixture
def detector():
    return S3Detector()

@pytest.fixture
def empty_dataframe():
    return pd.DataFrame(columns=[
        "eventTime", "eventName", "eventSource",
        "sourceIPAddress", "userName"
    ])

@pytest.fixture
def s3_exfiltration_dataframe():
    """DataFrame with one user making mass S3 access"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "GetObject",
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        }
    ] * 6 + [
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:05:00Z"),
            "eventName":       "ListBuckets",
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userName":        "normal_user"  # only 1 event — not suspicious
        }
    ])


class TestS3Detector:

    def test_returns_dataframe(self, detector, s3_exfiltration_dataframe):
        """Should always return a DataFrame"""
        result = detector.detect_s3_exfiltration(s3_exfiltration_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_detects_attacker(self, detector, s3_exfiltration_dataframe):
        """Should detect user with S3 event count above threshold"""
        result = detector.detect_s3_exfiltration(
            s3_exfiltration_dataframe, threshold=5
        )
        assert "attacker" in result["userName"].values

    def test_excludes_normal_user(self, detector, s3_exfiltration_dataframe):
        """Should not flag user with S3 event count below threshold"""
        result = detector.detect_s3_exfiltration(
            s3_exfiltration_dataframe, threshold=5
        )
        assert "normal_user" not in result["userName"].values

    def test_s3_event_count_is_correct(self, detector, s3_exfiltration_dataframe):
        """s3_event_count must match actual number of S3 events"""
        result = detector.detect_s3_exfiltration(
            s3_exfiltration_dataframe, threshold=5
        )
        attacker_row = result[result["userName"] == "attacker"]
        assert attacker_row.iloc[0]["s3_event_count"] == 6

    def test_returns_empty_on_empty_input(self, detector, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        result = detector.detect_s3_exfiltration(empty_dataframe)
        assert len(result) == 0

    def test_exfiltration_events_list_defined(self, detector):
        """S3_EXFILTRATION_EVENTS must contain key S3 events"""
        assert "GetObject" in detector.S3_EXFILTRATION_EVENTS
        assert "ListBuckets" in detector.S3_EXFILTRATION_EVENTS