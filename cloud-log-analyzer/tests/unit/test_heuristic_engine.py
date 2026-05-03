# src/tests/unit/test_heuristic_engine.py

import pytest
import pandas as pd
from src.analysis.heuristic_engine import HeuristicEngine


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def engine():
    """Returns a fresh HeuristicEngine instance for each test"""
    return HeuristicEngine()

@pytest.fixture
def dataframe_with_multiple_logins():
    """DataFrame with one suspicious IP attempting ConsoleLogin 4 times"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:01:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:02:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:03:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            # different IP — only 1 login, not suspicious
            "eventTime":       pd.Timestamp("2026-01-25T10:04:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userName":        "bob"
        }
    ])

@pytest.fixture
def dataframe_with_iam_events():
    """DataFrame mixing dangerous IAM events with normal events"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "CreateUser",          # dangerous
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:01:00Z"),
            "eventName":       "DeleteUser",          # dangerous
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:02:00Z"),
            "eventName":       "AttachUserPolicy",    # dangerous
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "5.6.7.8",
            "userName":        "bob"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:03:00Z"),
            "eventName":       "GetBucketAcl",        # normal
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "5.6.7.8",
            "userName":        "bob"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:04:00Z"),
            "eventName":       "ListObjects",         # normal
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userName":        "charlie"
        }
    ])

@pytest.fixture
def dataframe_with_high_volume_ip():
    """DataFrame with one IP making many API calls"""
    # IP 1.2.3.4 makes 15 calls — above threshold of 10
    rows = []
    for i in range(15):
        rows.append({
            "eventTime":       pd.Timestamp(f"2026-01-25T{10}:0{i % 10}:00Z"),
            "eventName":       "DescribeInstances",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "scanner"
        })
    # IP 9.9.9.9 makes 3 calls — below threshold
    for i in range(3):
        rows.append({
            "eventTime":       pd.Timestamp("2026-01-25T11:00:00Z"),
            "eventName":       "ListBuckets",
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userName":        "alice"
        })
    return pd.DataFrame(rows)

@pytest.fixture
def empty_dataframe():
    """Empty DataFrame with correct columns"""
    return pd.DataFrame(columns=[
        "eventTime", "eventName", "eventSource",
        "sourceIPAddress", "userName"
    ])

@pytest.fixture
def dataframe_no_logins():
    """DataFrame with no ConsoleLogin events"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ListBuckets",
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }
    ])

@pytest.fixture
def dataframe_no_iam_events():
    """DataFrame with no dangerous IAM events"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "GetBucketAcl",
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }
    ])


# ─── Tests : detect_failed_logins() ──────────────────────────

class TestDetectFailedLogins:

    def test_returns_dataframe(self, engine, dataframe_with_multiple_logins):
        """Should always return a DataFrame"""
        # Arrange

        # Act
        result = engine.detect_failed_logins(dataframe_with_multiple_logins)

        # Assert
        assert isinstance(result, pd.DataFrame)

    def test_detects_suspicious_ip_above_threshold(
        self, engine, dataframe_with_multiple_logins
    ):
        """Should detect IP with login count above threshold"""
        # Arrange — 1.2.3.4 attempts login 4 times, threshold=3

        # Act
        result = engine.detect_failed_logins(
            dataframe_with_multiple_logins, threshold=3
        )

        # Assert
        assert "1.2.3.4" in result["sourceIPAddress"].values

    def test_excludes_ip_below_threshold(
        self, engine, dataframe_with_multiple_logins
    ):
        """Should not flag IP with login count below threshold"""
        # Arrange — 9.9.9.9 only attempts login once

        # Act
        result = engine.detect_failed_logins(
            dataframe_with_multiple_logins, threshold=3
        )

        # Assert
        assert "9.9.9.9" not in result["sourceIPAddress"].values

    def test_result_has_correct_columns(
        self, engine, dataframe_with_multiple_logins
    ):
        """Result must have sourceIPAddress and login_count columns"""
        # Arrange

        # Act
        result = engine.detect_failed_logins(dataframe_with_multiple_logins)

        # Assert
        assert "sourceIPAddress" in result.columns
        assert "login_count" in result.columns

    def test_login_count_is_correct(
        self, engine, dataframe_with_multiple_logins
    ):
        """login_count must match the actual number of attempts"""
        # Arrange — 1.2.3.4 made exactly 4 attempts

        # Act
        result = engine.detect_failed_logins(
            dataframe_with_multiple_logins, threshold=3
        )

        # Assert
        ip_row = result[result["sourceIPAddress"] == "1.2.3.4"]
        assert ip_row.iloc[0]["login_count"] == 4

    def test_returns_empty_on_no_logins(self, engine, dataframe_no_logins):
        """Should return empty DataFrame when no ConsoleLogin events exist"""
        # Arrange — no ConsoleLogin events

        # Act
        result = engine.detect_failed_logins(dataframe_no_logins, threshold=3)

        # Assert
        assert len(result) == 0

    def test_returns_empty_on_empty_input(self, engine, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        # Arrange

        # Act
        result = engine.detect_failed_logins(empty_dataframe)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_sorted_by_login_count_descending(
        self, engine, dataframe_with_multiple_logins
    ):
        """Results must be sorted from most attempts to least"""
        # Arrange — add a second suspicious IP with 5 attempts
        extra_rows = pd.DataFrame([
            {
                "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
                "eventName":       "ConsoleLogin",
                "eventSource":     "signin.amazonaws.com",
                "sourceIPAddress": "5.5.5.5",
                "userName":        "charlie"
            }
        ] * 5)
        df = pd.concat(
            [dataframe_with_multiple_logins, extra_rows],
            ignore_index=True
        )

        # Act
        result = engine.detect_failed_logins(df, threshold=3)

        # Assert — 5.5.5.5 (5 attempts) must come before 1.2.3.4 (4 attempts)
        assert result.iloc[0]["sourceIPAddress"] == "5.5.5.5"
        assert result.iloc[1]["sourceIPAddress"] == "1.2.3.4"


# ─── Tests : detect_iam_changes() ────────────────────────────

class TestDetectIAMChanges:

    def test_returns_dataframe(self, engine, dataframe_with_iam_events):
        """Should always return a DataFrame"""
        # Arrange

        # Act
        result = engine.detect_iam_changes(dataframe_with_iam_events)

        # Assert
        assert isinstance(result, pd.DataFrame)

    def test_detects_all_dangerous_iam_events(
        self, engine, dataframe_with_iam_events
    ):
        """Should detect all dangerous IAM events in the DataFrame"""
        # Arrange — 3 dangerous events: CreateUser, DeleteUser, AttachUserPolicy

        # Act
        result = engine.detect_iam_changes(dataframe_with_iam_events)

        # Assert
        assert len(result) == 3

    def test_excludes_normal_events(self, engine, dataframe_with_iam_events):
        """Should not include normal events like GetBucketAcl or ListObjects"""
        # Arrange

        # Act
        result = engine.detect_iam_changes(dataframe_with_iam_events)

        # Assert
        assert "GetBucketAcl" not in result["eventName"].values
        assert "ListObjects" not in result["eventName"].values

    def test_includes_create_user(self, engine, dataframe_with_iam_events):
        """Should include CreateUser as a dangerous event"""
        # Arrange

        # Act
        result = engine.detect_iam_changes(dataframe_with_iam_events)

        # Assert
        assert "CreateUser" in result["eventName"].values

    def test_includes_delete_user(self, engine, dataframe_with_iam_events):
        """Should include DeleteUser as a dangerous event"""
        # Arrange

        # Act
        result = engine.detect_iam_changes(dataframe_with_iam_events)

        # Assert
        assert "DeleteUser" in result["eventName"].values

    def test_returns_empty_on_no_iam_events(
        self, engine, dataframe_no_iam_events
    ):
        """Should return empty DataFrame when no IAM events exist"""
        # Arrange

        # Act
        result = engine.detect_iam_changes(dataframe_no_iam_events)

        # Assert
        assert len(result) == 0

    def test_returns_empty_on_empty_input(self, engine, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        # Arrange

        # Act
        result = engine.detect_iam_changes(empty_dataframe)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_dangerous_events_list_is_defined(self, engine):
        """HeuristicEngine must define a non-empty list of dangerous events"""
        # Arrange

        # Act — check class constant directly
        dangerous = engine.IAM_DANGEROUS_EVENTS

        # Assert
        assert isinstance(dangerous, list)
        assert len(dangerous) > 0
        assert "CreateUser" in dangerous
        assert "DeleteUser" in dangerous
        assert "AttachUserPolicy" in dangerous


# ─── Tests : count_api_calls_by_ip() ─────────────────────────

class TestCountAPICallsByIP:

    def test_returns_dataframe(self, engine, dataframe_with_high_volume_ip):
        """Should always return a DataFrame"""
        # Arrange

        # Act
        result = engine.count_api_calls_by_ip(dataframe_with_high_volume_ip)

        # Assert
        assert isinstance(result, pd.DataFrame)

    def test_detects_high_volume_ip(self, engine, dataframe_with_high_volume_ip):
        """Should detect IP making more calls than threshold"""
        # Arrange — 1.2.3.4 makes 15 calls, threshold=10

        # Act
        result = engine.count_api_calls_by_ip(
            dataframe_with_high_volume_ip, threshold=10
        )

        # Assert
        assert "1.2.3.4" in result["sourceIPAddress"].values

    def test_excludes_low_volume_ip(self, engine, dataframe_with_high_volume_ip):
        """Should not flag IP making fewer calls than threshold"""
        # Arrange — 9.9.9.9 makes only 3 calls, threshold=10

        # Act
        result = engine.count_api_calls_by_ip(
            dataframe_with_high_volume_ip, threshold=10
        )

        # Assert
        assert "9.9.9.9" not in result["sourceIPAddress"].values

    def test_result_has_correct_columns(
        self, engine, dataframe_with_high_volume_ip
    ):
        """Result must have sourceIPAddress and call_count columns"""
        # Arrange

        # Act
        result = engine.count_api_calls_by_ip(dataframe_with_high_volume_ip)

        # Assert
        assert "sourceIPAddress" in result.columns
        assert "call_count" in result.columns

    def test_call_count_is_correct(self, engine, dataframe_with_high_volume_ip):
        """call_count must match the actual number of API calls"""
        # Arrange — 1.2.3.4 made exactly 15 calls

        # Act
        result = engine.count_api_calls_by_ip(
            dataframe_with_high_volume_ip, threshold=10
        )

        # Assert
        ip_row = result[result["sourceIPAddress"] == "1.2.3.4"]
        assert ip_row.iloc[0]["call_count"] == 15

    def test_sorted_by_call_count_descending(
        self, engine, dataframe_with_high_volume_ip
    ):
        """Results must be sorted from most calls to least"""
        # Arrange — add a second high volume IP with 20 calls
        extra_rows = pd.DataFrame([{
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "DescribeInstances",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "7.7.7.7",
            "userName":        "scanner2"
        }] * 20)
        df = pd.concat(
            [dataframe_with_high_volume_ip, extra_rows],
            ignore_index=True
        )

        # Act
        result = engine.count_api_calls_by_ip(df, threshold=10)

        # Assert — 7.7.7.7 (20 calls) must come before 1.2.3.4 (15 calls)
        assert result.iloc[0]["sourceIPAddress"] == "7.7.7.7"
        assert result.iloc[1]["sourceIPAddress"] == "1.2.3.4"

    def test_returns_empty_on_empty_input(self, engine, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        # Arrange

        # Act
        result = engine.count_api_calls_by_ip(empty_dataframe)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0