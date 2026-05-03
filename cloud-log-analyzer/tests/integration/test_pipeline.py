# src/tests/integration/test_pipeline.py

import json
import pytest
import pandas as pd
from src.data_collection.aws_connector import AWSConnector
from src.data_processing.log_parser import LogParser
from src.data_processing.data_validator import DataValidator
from src.analysis.heuristic_engine import HeuristicEngine


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def connector():
    """Returns a fresh AWSConnector instance"""
    return AWSConnector()

@pytest.fixture
def parser():
    """Returns a fresh LogParser instance"""
    return LogParser()

@pytest.fixture
def validator():
    """Returns a fresh DataValidator instance"""
    return DataValidator()

@pytest.fixture
def valid_cloudtrail_file(tmp_path):
    """Creates a temporary valid CloudTrail JSON file with 3 clean events"""
    data = {
        "Records": [
            {
                "eventName":       "ConsoleLogin",
                "eventSource":     "signin.amazonaws.com",
                "sourceIPAddress": "1.2.3.4",
                "userIdentity":    {"type": "IAMUser", "userName": "alice"},
                "eventTime":       "2026-01-25T10:00:00Z"
            },
            {
                "eventName":       "GetBucketAcl",
                "eventSource":     "s3.amazonaws.com",
                "sourceIPAddress": "5.6.7.8",
                "userIdentity":    {"type": "IAMUser", "userName": "bob"},
                "eventTime":       "2026-01-25T11:00:00Z"
            },
            {
                "eventName":       "AssumeRole",
                "eventSource":     "sts.amazonaws.com",
                "sourceIPAddress": "unknown",
                "userIdentity":    {"type": "IAMUser", "userName": "charlie"},
                "eventTime":       "2026-01-25T12:00:00Z"
            }
        ]
    }
    file = tmp_path / "cloudtrail.json"
    file.write_text(json.dumps(data))
    return str(file)

@pytest.fixture
def dirty_cloudtrail_file(tmp_path):
    """Creates a CloudTrail file with mixed valid and invalid events"""
    data = {
        "Records": [
            {
                # valid event
                "eventName":       "ConsoleLogin",
                "eventSource":     "signin.amazonaws.com",
                "sourceIPAddress": "1.2.3.4",
                "userIdentity":    {"type": "IAMUser", "userName": "alice"},
                "eventTime":       "2026-01-25T10:00:00Z"
            },
            {
                # invalid event — no eventTime
                "eventName":       "CreateUser",
                "eventSource":     "iam.amazonaws.com",
                "sourceIPAddress": "5.6.7.8",
                "userIdentity":    {"type": "IAMUser", "userName": "bob"},
                "eventTime":       ""   # empty — will become NaT
            },
            {
                # invalid event — no eventName
                "eventName":       "",
                "eventSource":     "sts.amazonaws.com",
                "sourceIPAddress": "9.9.9.9",
                "userIdentity":    {"type": "IAMUser", "userName": "charlie"},
                "eventTime":       "2026-01-25T12:00:00Z"
            }
        ]
    }
    file = tmp_path / "dirty_cloudtrail.json"
    file.write_text(json.dumps(data))
    return str(file)

@pytest.fixture
def empty_cloudtrail_file(tmp_path):
    """Creates a CloudTrail file with no events"""
    data = {"Records": []}
    file = tmp_path / "empty_cloudtrail.json"
    file.write_text(json.dumps(data))
    return str(file)


# ─── Tests : Layer 1 → Layer 2 ───────────────────────────────

class TestConnectorToParser:

    def test_parser_accepts_connector_output(
        self, connector, parser, valid_cloudtrail_file
    ):
        """Output of AWSConnector must be accepted by LogParser without error"""
        # Arrange
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=valid_cloudtrail_file
        )

        # Act — parser receives connector output directly
        result = parser.parse_json(raw_logs)

        # Assert — no crash, returns list
        assert isinstance(result, list)
        assert len(result) == 3

    def test_parsed_output_has_correct_fields(
        self, connector, parser, valid_cloudtrail_file
    ):
        """Parsed output must contain exactly the 5 required fields"""
        # Arrange
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=valid_cloudtrail_file
        )
        expected_keys = {
            "eventTime", "eventName", "eventSource",
            "sourceIPAddress", "userName"
        }

        # Act
        result = parser.parse_json(raw_logs)

        # Assert — every event has the right structure
        for event in result:
            assert set(event.keys()) == expected_keys

    def test_dataframe_produced_from_connector_output(
        self, connector, parser, valid_cloudtrail_file
    ):
        """to_dataframe() must succeed on connector output"""
        # Arrange
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=valid_cloudtrail_file
        )
        parsed = parser.parse_json(raw_logs)

        # Act
        df = parser.to_dataframe(parsed)

        # Assert
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 5)

    def test_empty_connector_output_produces_empty_dataframe(
        self, connector, parser, empty_cloudtrail_file
    ):
        """Empty connector output must produce empty DataFrame without crash"""
        # Arrange
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=empty_cloudtrail_file
        )

        # Act
        parsed = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed)

        # Assert
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


# ─── Tests : Layer 2 → Layer 3 ───────────────────────────────

class TestParserToValidator:

    def test_validator_accepts_parser_output(
        self, connector, parser, validator, valid_cloudtrail_file
    ):
        """Output of LogParser must pass schema validation"""
        # Arrange
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=valid_cloudtrail_file
        )
        parsed = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed)

        # Act
        result = validator.validate_schema(df)

        # Assert — schema must be valid
        assert result is True

    def test_clean_data_accepts_parser_output(
        self, connector, parser, validator, valid_cloudtrail_file
    ):
        """clean_data() must accept DataFrame from LogParser without error"""
        # Arrange
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=valid_cloudtrail_file
        )
        parsed = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed)

        # Act
        cleaned_df = validator.clean_data(df)

        # Assert
        assert isinstance(cleaned_df, pd.DataFrame)
        assert len(cleaned_df) == 3

    def test_validator_removes_invalid_rows_from_parser_output(
        self, connector, parser, validator, dirty_cloudtrail_file
    ):
        """Validator must remove invalid rows produced by parser"""
        # Arrange — dirty file has 3 events: 1 valid, 1 no date, 1 no name
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=dirty_cloudtrail_file
        )
        parsed = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed)

        # Act
        cleaned_df = validator.clean_data(df)

        # Assert — only 1 valid row survives
        assert len(cleaned_df) == 1
        assert cleaned_df.iloc[0]["userName"] == "alice"


# ─── Tests : Pipeline complet Layer 1 → 2 → 3 ───────────────

class TestFullPipeline:

    def test_full_pipeline_clean_data(
        self, connector, parser, validator, valid_cloudtrail_file
    ):
        """Full pipeline must produce a clean validated DataFrame"""
        # Arrange

        # Act — Layer 1
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=valid_cloudtrail_file
        )

        # Act — Layer 2
        parsed = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed)

        # Act — Layer 3
        is_valid = validator.validate_schema(df)
        cleaned_df = validator.clean_data(df)

        # Assert — end to end
        assert is_valid is True
        assert isinstance(cleaned_df, pd.DataFrame)
        assert len(cleaned_df) == 3
        assert pd.api.types.is_datetime64_any_dtype(cleaned_df["eventTime"])

    def test_full_pipeline_dirty_data(
        self, connector, parser, validator, dirty_cloudtrail_file
    ):
        """Full pipeline must filter invalid rows and return only clean data"""
        # Arrange

        # Act — Layer 1
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=dirty_cloudtrail_file
        )

        # Act — Layer 2
        parsed = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed)

        # Act — Layer 3
        is_valid = validator.validate_schema(df)
        cleaned_df = validator.clean_data(df)

        # Assert — 3 events in, only 1 valid out
        assert is_valid is True
        assert len(cleaned_df) == 1

    def test_full_pipeline_empty_file(
        self, connector, parser, validator, empty_cloudtrail_file
    ):
        """Full pipeline must handle empty input gracefully end to end"""
        # Arrange

        # Act — Layer 1
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=empty_cloudtrail_file
        )

        # Act — Layer 2
        parsed = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed)

        # Act — Layer 3
        is_valid = validator.validate_schema(df)
        cleaned_df = validator.clean_data(df)

        # Assert — no crash, empty output
        assert is_valid is True
        assert len(cleaned_df) == 0

    def test_full_pipeline_output_columns(
        self, connector, parser, validator, valid_cloudtrail_file
    ):
        """Final DataFrame must always have exactly the 5 required columns"""
        # Arrange
        expected_columns = {
            "eventTime", "eventName", "eventSource",
            "sourceIPAddress", "userName"
        }

        # Act
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=valid_cloudtrail_file
        )
        parsed = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed)
        cleaned_df = validator.clean_data(df)

        # Assert
        assert set(cleaned_df.columns) == expected_columns

    def test_full_pipeline_preserves_correct_values(
        self, connector, parser, validator, valid_cloudtrail_file
    ):
        """Final DataFrame must preserve correct original values end to end"""
        # Arrange

        # Act
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=valid_cloudtrail_file
        )
        parsed = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed)
        cleaned_df = validator.clean_data(df)

        # Assert — first event values preserved through all layers
        assert cleaned_df.iloc[0]["eventName"] == "ConsoleLogin"
        assert cleaned_df.iloc[0]["userName"] == "alice"
        assert cleaned_df.iloc[0]["sourceIPAddress"] == "1.2.3.4"



# ─── Fixture ─────────────────────────────────────────────────

@pytest.fixture
def engine():
    """Returns a fresh HeuristicEngine instance"""
    return HeuristicEngine()

@pytest.fixture
def cloudtrail_file_with_suspicious_activity(tmp_path):
    """
    CloudTrail file containing:
    - 4 ConsoleLogin from same IP  → brute force
    - 2 dangerous IAM events       → privilege escalation
    - 12 API calls from one IP     → scanner
    """
    high_volume_calls = [
        {
            "eventName":       "DescribeInstances",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userIdentity":    {"type": "IAMUser", "userName": "scanner"},
            "eventTime": f"2026-01-25T12:{i:02d}:00Z"
        }
        for i in range(12)  
    ]


    data = {
        "Records": [
            # Brute force attempts — 4 logins from same IP
            {
                "eventName":       "ConsoleLogin",
                "eventSource":     "signin.amazonaws.com",
                "sourceIPAddress": "1.2.3.4",
                "userIdentity":    {"type": "IAMUser", "userName": "alice"},
                "eventTime":       "2026-01-25T10:00:00Z"
            },
            {
                "eventName":       "ConsoleLogin",
                "eventSource":     "signin.amazonaws.com",
                "sourceIPAddress": "1.2.3.4",
                "userIdentity":    {"type": "IAMUser", "userName": "alice"},
                "eventTime":       "2026-01-25T10:01:00Z"
            },
            {
                "eventName":       "ConsoleLogin",
                "eventSource":     "signin.amazonaws.com",
                "sourceIPAddress": "1.2.3.4",
                "userIdentity":    {"type": "IAMUser", "userName": "alice"},
                "eventTime":       "2026-01-25T10:02:00Z"
            },
            {
                "eventName":       "ConsoleLogin",
                "eventSource":     "signin.amazonaws.com",
                "sourceIPAddress": "1.2.3.4",
                "userIdentity":    {"type": "IAMUser", "userName": "alice"},
                "eventTime":       "2026-01-25T10:03:00Z"
            },
            # Dangerous IAM events
            {
                "eventName":       "CreateUser",
                "eventSource":     "iam.amazonaws.com",
                "sourceIPAddress": "5.6.7.8",
                "userIdentity":    {"type": "IAMUser", "userName": "bob"},
                "eventTime":       "2026-01-25T11:00:00Z"
            },
            {
                "eventName":       "AttachUserPolicy",
                "eventSource":     "iam.amazonaws.com",
                "sourceIPAddress": "5.6.7.8",
                "userIdentity":    {"type": "IAMUser", "userName": "bob"},
                "eventTime":       "2026-01-25T11:01:00Z"
            },
            # High volume API calls — 12 calls from same IP
            
            *high_volume_calls  
        ]
    }
    file = tmp_path / "suspicious_cloudtrail.json"
    file.write_text(json.dumps(data))
    return str(file)


# ─── Tests : Layer 1 → 2 → 3 → 4 ────────────────────────────

class TestFullPipelineWithHeuristics:

    def test_pipeline_feeds_heuristic_engine(
        self, connector, parser, validator, engine,
        cloudtrail_file_with_suspicious_activity
    ):
        """Full pipeline output must be accepted by HeuristicEngine"""
        # Arrange

        # Act — Layers 1, 2, 3
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=cloudtrail_file_with_suspicious_activity
        )
        parsed = parser.parse_json(raw_logs)
        df = parser.to_dataframe(parsed)
        df = validator.clean_data(df)

        # Act — Layer 4
        failed_logins = engine.detect_failed_logins(df, threshold=3)
        iam_changes   = engine.detect_iam_changes(df)
        api_calls     = engine.count_api_calls_by_ip(df, threshold=10)

        # Assert — all three return DataFrames without crash
        assert isinstance(failed_logins, pd.DataFrame)
        assert isinstance(iam_changes,   pd.DataFrame)
        assert isinstance(api_calls,     pd.DataFrame)

    def test_pipeline_detects_brute_force(
        self, connector, parser, validator, engine,
        cloudtrail_file_with_suspicious_activity
    ):
        """Pipeline must detect brute force IP end to end"""
        # Arrange

        # Act
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=cloudtrail_file_with_suspicious_activity
        )
        parsed  = parser.parse_json(raw_logs)
        df      = parser.to_dataframe(parsed)
        df      = validator.clean_data(df)
        result  = engine.detect_failed_logins(df, threshold=3)

        # Assert — 1.2.3.4 must be flagged
        assert "1.2.3.4" in result["sourceIPAddress"].values

    def test_pipeline_detects_iam_changes(
        self, connector, parser, validator, engine,
        cloudtrail_file_with_suspicious_activity
    ):
        """Pipeline must detect dangerous IAM events end to end"""
        # Arrange

        # Act
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=cloudtrail_file_with_suspicious_activity
        )
        parsed  = parser.parse_json(raw_logs)
        df      = parser.to_dataframe(parsed)
        df      = validator.clean_data(df)
        result  = engine.detect_iam_changes(df)

        # Assert — 2 dangerous IAM events detected
        assert len(result) == 2
        assert "CreateUser"       in result["eventName"].values
        assert "AttachUserPolicy" in result["eventName"].values

    def test_pipeline_detects_high_volume_ip(
        self, connector, parser, validator, engine,
        cloudtrail_file_with_suspicious_activity
    ):
        """Pipeline must detect high volume API caller end to end"""
        # Arrange

        # Act
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=cloudtrail_file_with_suspicious_activity
        )
        parsed  = parser.parse_json(raw_logs)
        df      = parser.to_dataframe(parsed)
        df      = validator.clean_data(df)
        result  = engine.count_api_calls_by_ip(df, threshold=10)

        # Assert — 9.9.9.9 must be flagged
        assert "9.9.9.9" in result["sourceIPAddress"].values

    def test_pipeline_clean_data_produces_no_detections(
        self, connector, parser, validator, engine,
        valid_cloudtrail_file
    ):
        """Pipeline with clean data must produce no suspicious detections"""
        # Arrange — valid_cloudtrail_file has normal activity only

        # Act
        raw_logs = connector.fetch_logs(
            source="file",
            file_path=valid_cloudtrail_file
        )
        parsed       = parser.parse_json(raw_logs)
        df           = parser.to_dataframe(parsed)
        df           = validator.clean_data(df)
        failed_logins = engine.detect_failed_logins(df, threshold=3)
        iam_changes   = engine.detect_iam_changes(df)

        # Assert — no threats detected in clean data
        assert len(failed_logins) == 0
        assert len(iam_changes)   == 0