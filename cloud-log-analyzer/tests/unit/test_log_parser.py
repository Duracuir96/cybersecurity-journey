# src/tests/unit/test_log_parser.py

import pytest
import pandas as pd
from src.data_processing.log_parser import LogParser


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def parser():
    """Returns a fresh LogParser instance for each test"""
    return LogParser()

@pytest.fixture
def local_format_logs():
    """Sample logs in local JSON format (lowercase keys, nested userIdentity)"""
    return [
        {
            "eventName": "ConsoleLogin",
            "eventSource": "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userIdentity": {"type": "IAMUser", "userName": "alice"},
            "eventTime": "2026-01-25T10:00:00Z"
        },
        {
            "eventName": "CreateUser",
            "eventSource": "iam.amazonaws.com",
            "sourceIPAddress": "5.6.7.8",
            "userIdentity": {"type": "IAMUser", "userName": "bob"},
            "eventTime": "2026-01-25T11:00:00Z"
        }
    ]

@pytest.fixture
def aws_format_logs():
    """Sample logs in real AWS API format (PascalCase keys, Username direct)"""
    import json
    import datetime
    return [
        {
            "EventName": "LookupEvents",
            "EventSource": "cloudtrail.amazonaws.com",
            "EventTime": datetime.datetime(2026, 3, 15, 17, 54, 12),
            "Username": "tester96",
            "SourceIPAddress": "92.223.30.29"
        },
        {
            "EventName": "DescribeFpgaImages",
            "EventSource": "ec2.amazonaws.com",
            "EventTime": datetime.datetime(2026, 3, 15, 17, 51, 25),
            "Username": "resource-explorer-2",
            "SourceIPAddress": "resource-explorer-2.amazonaws.com"
        }
    ]

@pytest.fixture
def logs_with_missing_fields():
    """Logs where optional fields are absent — tests .get() safety"""
    return [
        {
            "eventName": "ConsoleLogin",
            # eventSource missing
            # sourceIPAddress missing
            "userIdentity": {"type": "IAMUser"},  # userName missing
            "eventTime": "2026-01-25T10:00:00Z"
        }
    ]

@pytest.fixture
def empty_logs():
    """Empty list — edge case"""
    return []


# ─── Tests : parse_json() — local format ─────────────────────

class TestParseJsonLocalFormat:

    def test_returns_list_of_dicts(self, parser, local_format_logs):
        """Should return a list of dicts from local format logs"""
        # Arrange — local_format_logs fixture

        # Act
        result = parser.parse_json(local_format_logs)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2

    def test_extracts_all_five_fields(self, parser, local_format_logs):
        """Each parsed event must contain exactly the 5 required fields"""
        # Arrange
        expected_keys = {"eventTime", "eventName", "eventSource",
                         "sourceIPAddress", "userName"}

        # Act
        result = parser.parse_json(local_format_logs)

        # Assert
        assert set(result[0].keys()) == expected_keys

    def test_extracts_correct_values(self, parser, local_format_logs):
        """Parsed values must match the original log content"""
        # Arrange — known first event: alice, ConsoleLogin, 1.2.3.4

        # Act
        result = parser.parse_json(local_format_logs)

        # Assert
        assert result[0]["eventName"] == "ConsoleLogin"
        assert result[0]["sourceIPAddress"] == "1.2.3.4"
        assert result[0]["userName"] == "alice"

    def test_extracts_nested_username(self, parser, local_format_logs):
        """Should correctly extract userName from nested userIdentity dict"""
        # Arrange — userIdentity is a nested dict

        # Act
        result = parser.parse_json(local_format_logs)

        # Assert — both users extracted correctly
        assert result[0]["userName"] == "alice"
        assert result[1]["userName"] == "bob"

    def test_handles_missing_fields_with_defaults(self, parser, logs_with_missing_fields):
        """Missing optional fields should return default values, not crash"""
        # Arrange — log missing eventSource, sourceIPAddress, userName

        # Act
        result = parser.parse_json(logs_with_missing_fields)

        # Assert — defaults applied
        assert result[0]["eventSource"] == ""
        assert result[0]["sourceIPAddress"] == "unknown"
        assert result[0]["userName"] == "unknown"

    def test_returns_empty_list_on_empty_input(self, parser, empty_logs):
        """Should return empty list when input is empty"""
        # Arrange — empty list

        # Act
        result = parser.parse_json(empty_logs)

        # Assert
        assert result == []


# ─── Tests : parse_json() — AWS real format ──────────────────

class TestParseJsonAWSFormat:

    def test_detects_aws_format_correctly(self, parser, aws_format_logs):
        """Should detect AWS real format via PascalCase EventName key"""
        # Arrange — AWS format logs with PascalCase keys

        # Act
        result = parser.parse_json(aws_format_logs)

        # Assert — should parse without crash and return 2 events
        assert len(result) == 2

    def test_extracts_username_from_aws_format(self, parser, aws_format_logs):
        """Should extract Username directly from AWS format (not userIdentity)"""
        # Arrange — AWS format has Username key directly

        # Act
        result = parser.parse_json(aws_format_logs)

        # Assert
        assert result[0]["userName"] == "tester96"
        assert result[1]["userName"] == "resource-explorer-2"

    def test_extracts_ip_from_cloudtrail_event_string(self, parser, aws_format_logs):
        """Should extract sourceIPAddress from nested CloudTrailEvent JSON string"""
        # Arrange — sourceIPAddress is inside a JSON string

        # Act
        result = parser.parse_json(aws_format_logs)

        # Assert
        assert result[0]["sourceIPAddress"] == "92.223.30.29"

    def test_extracts_event_name_from_aws_format(self, parser, aws_format_logs):
        """Should extract EventName from PascalCase AWS format"""
        # Arrange

        # Act
        result = parser.parse_json(aws_format_logs)

        # Assert
        assert result[0]["eventName"] == "LookupEvents"
        assert result[1]["eventName"] == "DescribeFpgaImages"


# ─── Tests : to_dataframe() ──────────────────────────────────

class TestToDataFrame:

    def test_returns_dataframe(self, parser, local_format_logs):
        """Should return a pandas DataFrame"""
        # Arrange
        parsed = parser.parse_json(local_format_logs)

        # Act
        df = parser.to_dataframe(parsed)

        # Assert
        assert isinstance(df, pd.DataFrame)

    def test_dataframe_has_correct_shape(self, parser, local_format_logs):
        """DataFrame should have correct number of rows and columns"""
        # Arrange
        parsed = parser.parse_json(local_format_logs)

        # Act
        df = parser.to_dataframe(parsed)

        # Assert — 2 events, 5 columns
        assert df.shape == (2, 5)

    def test_dataframe_has_correct_columns(self, parser, local_format_logs):
        """DataFrame must contain exactly the 5 required columns"""
        # Arrange
        parsed = parser.parse_json(local_format_logs)
        expected_columns = {"eventTime", "eventName", "eventSource",
                            "sourceIPAddress", "userName"}

        # Act
        df = parser.to_dataframe(parsed)

        # Assert
        assert set(df.columns) == expected_columns

    def test_eventtime_is_datetime_type(self, parser, local_format_logs):
        """eventTime column should be converted to datetime type"""
        # Arrange
        parsed = parser.parse_json(local_format_logs)

        # Act
        df = parser.to_dataframe(parsed)

        # Assert — must be datetime, not string
        assert pd.api.types.is_datetime64_any_dtype(df["eventTime"])

    def test_string_columns_are_object_type(self, parser, local_format_logs):
        """String columns should be object dtype in pandas"""
        # Arrange
        parsed = parser.parse_json(local_format_logs)

        # Act
        df = parser.to_dataframe(parsed)

        # Assert
        assert df["eventName"].dtype == object
        assert df["userName"].dtype == object
        assert df["sourceIPAddress"].dtype == object

    def test_returns_empty_dataframe_on_empty_input(self, parser):
        """Should return empty DataFrame when input list is empty"""
        # Arrange
        parsed = []

        # Act
        df = parser.to_dataframe(parsed)

        # Assert
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0