# src/tests/integration/test_pipeline.py

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
def engine():
    """Returns a fresh HeuristicEngine facade instance"""
    return HeuristicEngine()

@pytest.fixture
def valid_cloudtrail_file(tmp_path):
    """Clean CloudTrail file with normal activity only"""
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
                "eventName":       "ListBuckets",
                "eventSource":     "s3.amazonaws.com",
                "sourceIPAddress": "1.2.3.4",
                "userIdentity":    {"type": "IAMUser", "userName": "alice"},
                "eventTime":       "2026-01-25T10:01:00Z"
            },
            {
                "eventName":       "DescribeInstances",
                "eventSource":     "ec2.amazonaws.com",
                "sourceIPAddress": "5.6.7.8",
                "userIdentity":    {"type": "IAMUser", "userName": "bob"},
                "eventTime":       "2026-01-25T10:02:00Z"
            }
        ]
    }
    file = tmp_path / "valid_cloudtrail.json"
    file.write_text(json.dumps(data))
    return str(file)

@pytest.fixture
def dirty_cloudtrail_file(tmp_path):
    """CloudTrail file with mixed valid and invalid events"""
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
                "eventName":       "CreateUser",
                "eventSource":     "iam.amazonaws.com",
                "sourceIPAddress": "5.6.7.8",
                "userIdentity":    {"type": "IAMUser", "userName": "bob"},
                "eventTime":       ""   # invalid — becomes NaT
            },
            {
                "eventName":       "",  # invalid — empty event name
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
    """CloudTrail file with no events"""
    data = {"Records": []}
    file = tmp_path / "empty_cloudtrail.json"
    file.write_text(json.dumps(data))
    return str(file)

@pytest.fixture
def suspicious_cloudtrail_file(tmp_path):
    """
    CloudTrail file with realistic attack scenario covering all detectors:
    - 4x ConsoleLogin from same IP          → brute force
    - CreateUser + AttachUserPolicy          → IAM privilege escalation
    - ListUsers + ListRoles + ListPolicies   → IAM enumeration
    - GetCallerIdentity from 2 IPs          → credential abuse
    - 3x AssumeRole from same user          → role chaining
    - 6x GetObject from same user           → S3 exfiltration
    - RunInstances + CreateKeyPair          → EC2 compromise
    - DeleteFlowLogs                        → covering tracks
    - UpdateFunctionCode                    → Lambda abuse
    - 12x API calls from same IP            → high volume scanner
    """
    records = []

    # Brute force — 4 ConsoleLogin from same IP
    for i in range(4):
        records.append({
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
            "eventTime": f"2026-01-25T10:{i:02d}:00Z"
        })

    # IAM privilege escalation
    records.append({
        "eventName":       "CreateUser",
        "eventSource":     "iam.amazonaws.com",
        "sourceIPAddress": "1.2.3.4",
        "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
        "eventTime":       "2026-01-25T10:05:00Z"
    })
    records.append({
        "eventName":       "AttachUserPolicy",
        "eventSource":     "iam.amazonaws.com",
        "sourceIPAddress": "1.2.3.4",
        "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
        "eventTime":       "2026-01-25T10:06:00Z"
    })

    # IAM enumeration
    for event in ["ListUsers", "ListRoles", "ListPolicies"]:
        records.append({
            "eventName":       event,
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
            "eventTime":       "2026-01-25T10:07:00Z"
        })

    # Credential abuse — GetCallerIdentity from 2 different IPs
    for ip in ["1.2.3.4", "9.9.9.9"]:
        records.append({
            "eventName":       "GetCallerIdentity",
            "eventSource":     "sts.amazonaws.com",
            "sourceIPAddress": ip,
            "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
            "eventTime":       "2026-01-25T10:08:00Z"
        })

    # Role chaining — 3x AssumeRole from same user
    for i in range(3):
        records.append({
            "eventName":       "AssumeRole",
            "eventSource":     "sts.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
            "eventTime": f"2026-01-25T10:{(i+9):02d}:00Z"
        })

    # S3 exfiltration — 6x GetObject from same user
    for i in range(6):
        records.append({
            "eventName":       "GetObject",
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
           "eventTime": f"2026-01-25T11:{i:02d}:00Z"
        })

    # EC2 compromise
    records.append({
        "eventName":       "RunInstances",
        "eventSource":     "ec2.amazonaws.com",
        "sourceIPAddress": "1.2.3.4",
        "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
        "eventTime":       "2026-01-25T11:10:00Z"
    })
    records.append({
        "eventName":       "CreateKeyPair",
        "eventSource":     "ec2.amazonaws.com",
        "sourceIPAddress": "1.2.3.4",
        "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
        "eventTime":       "2026-01-25T11:11:00Z"
    })

    # Covering tracks — delete logs
    records.append({
        "eventName":       "DeleteFlowLogs",
        "eventSource":     "ec2.amazonaws.com",
        "sourceIPAddress": "1.2.3.4",
        "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
        "eventTime":       "2026-01-25T11:12:00Z"
    })

    # Lambda abuse
    records.append({
        "eventName":       "UpdateFunctionCode",
        "eventSource":     "lambda.amazonaws.com",
        "sourceIPAddress": "1.2.3.4",
        "userIdentity":    {"type": "IAMUser", "userName": "attacker"},
        "eventTime":       "2026-01-25T11:13:00Z"
    })

    # High volume scanner — 12 API calls from same IP
    for i in range(12):
        records.append({
            "eventName":       "DescribeInstances",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "5.5.5.5",
            "userIdentity":    {"type": "IAMUser", "userName": "scanner"},
            "eventTime": f"2026-01-25T12:{i:02d}:00Z"
        })

    data = {"Records": records}
    file = tmp_path / "suspicious_cloudtrail.json"
    file.write_text(json.dumps(data))
    return str(file)


# ─── Helper ──────────────────────────────────────────────────

def run_pipeline(connector, parser, validator, file_path):
    """
    Runs Layers 1, 2, 3 and returns a clean DataFrame.
    Reusable helper to avoid repeating the pipeline in every test.
    """
    raw_logs = connector.fetch_logs(source="file", file_path=file_path)
    parsed   = parser.parse_json(raw_logs)
    df       = parser.to_dataframe(parsed)
    return validator.clean_data(df)


# ─── Tests : Layer 1 → Layer 2 ───────────────────────────────

class TestConnectorToParser:

    def test_parser_accepts_connector_output(
        self, connector, parser, valid_cloudtrail_file
    ):
        """Output of AWSConnector must be accepted by LogParser"""
        # Arrange
        raw_logs = connector.fetch_logs(
            source="file", file_path=valid_cloudtrail_file
        )

        # Act
        result = parser.parse_json(raw_logs)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3

    def test_parsed_output_has_correct_fields(
        self, connector, parser, valid_cloudtrail_file
    ):
        """Parsed output must contain exactly the 5 required fields"""
        # Arrange
        raw_logs = connector.fetch_logs(
            source="file", file_path=valid_cloudtrail_file
        )
        expected_keys = {
            "eventTime", "eventName", "eventSource",
            "sourceIPAddress", "userName"
        }

        # Act
        result = parser.parse_json(raw_logs)

        # Assert
        for event in result:
            assert set(event.keys()) == expected_keys

    def test_dataframe_produced_from_connector_output(
        self, connector, parser, valid_cloudtrail_file
    ):
        """to_dataframe() must succeed on connector output"""
        # Arrange
        raw_logs = connector.fetch_logs(
            source="file", file_path=valid_cloudtrail_file
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
        """Empty connector output must produce empty DataFrame"""
        # Arrange
        raw_logs = connector.fetch_logs(
            source="file", file_path=empty_cloudtrail_file
        )

        # Act
        parsed = parser.parse_json(raw_logs)
        df     = parser.to_dataframe(parsed)

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
            source="file", file_path=valid_cloudtrail_file
        )
        parsed = parser.parse_json(raw_logs)
        df     = parser.to_dataframe(parsed)

        # Act
        result = validator.validate_schema(df)

        # Assert
        assert result is True

    def test_validator_removes_invalid_rows_from_parser_output(
        self, connector, parser, validator, dirty_cloudtrail_file
    ):
        """Validator must remove invalid rows from parser output"""
        # Arrange — 3 events: 1 valid, 1 NaT, 1 empty eventName
        raw_logs = connector.fetch_logs(
            source="file", file_path=dirty_cloudtrail_file
        )
        parsed = parser.parse_json(raw_logs)
        df     = parser.to_dataframe(parsed)

        # Act
        cleaned_df = validator.clean_data(df)

        # Assert — only 1 valid row survives
        assert len(cleaned_df) == 1
        assert cleaned_df.iloc[0]["userName"] == "alice"


# ─── Tests : Layer 3 → Layer 4 ───────────────────────────────

class TestValidatorToHeuristicEngine:

    def test_engine_accepts_validator_output(
        self, connector, parser, validator, engine, valid_cloudtrail_file
    ):
        """HeuristicEngine must accept clean DataFrame from DataValidator"""
        # Arrange
        df = run_pipeline(connector, parser, validator, valid_cloudtrail_file)

        # Act — run all detections
        results = engine.run_all_detections(df)

        # Assert — returns dict with all expected keys
        assert isinstance(results, dict)
        assert "failed_logins"    in results
        assert "iam_changes"      in results
        assert "iam_enumeration"  in results
        assert "credential_abuse" in results
        assert "role_chaining"    in results
        assert "s3_exfiltration"  in results
        assert "ec2_suspicious"   in results
        assert "data_exfiltration" in results
        assert "critical_events"  in results
        assert "lambda_abuse"     in results
        assert "api_calls_by_ip"  in results

    def test_all_detection_results_are_dataframes(
        self, connector, parser, validator, engine, valid_cloudtrail_file
    ):
        """Every detection result must be a DataFrame"""
        # Arrange
        df = run_pipeline(connector, parser, validator, valid_cloudtrail_file)

        # Act
        results = engine.run_all_detections(df)

        # Assert
        for name, result in results.items():
            assert isinstance(result, pd.DataFrame), \
                f"{name} did not return a DataFrame"


# ─── Tests : Full Pipeline Layer 1 → 2 → 3 → 4 ──────────────

class TestFullPipeline:

    def test_full_pipeline_clean_data(
        self, connector, parser, validator, engine, valid_cloudtrail_file
    ):
        """Full pipeline must produce a clean validated DataFrame"""
        # Arrange

        # Act
        df      = run_pipeline(connector, parser, validator, valid_cloudtrail_file)
        results = engine.run_all_detections(df)

        # Assert
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert isinstance(results, dict)

    def test_full_pipeline_empty_file(
        self, connector, parser, validator, engine, empty_cloudtrail_file
    ):
        """Full pipeline must handle empty input gracefully end to end"""
        # Arrange

        # Act
        df      = run_pipeline(connector, parser, validator, empty_cloudtrail_file)
        results = engine.run_all_detections(df)

        # Assert — no crash, empty output, all detections return empty DataFrames
        assert len(df) == 0
        for name, result in results.items():
            assert len(result) == 0, \
                f"{name} should return empty DataFrame on empty input"

    def test_full_pipeline_output_columns(
        self, connector, parser, validator, engine, valid_cloudtrail_file
    ):
        """Final DataFrame must always have exactly the 5 required columns"""
        # Arrange
        expected_columns = {
            "eventTime", "eventName", "eventSource",
            "sourceIPAddress", "userName"
        }

        # Act
        df = run_pipeline(connector, parser, validator, valid_cloudtrail_file)

        # Assert
        assert set(df.columns) == expected_columns


# ─── Tests : Attack Scenario — All Detectors ─────────────────

class TestAttackScenario:

    def test_pipeline_detects_brute_force(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must detect brute force login attempts end to end"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.detect_failed_logins(df, threshold=3)

        # Assert — attacker IP flagged
        assert "1.2.3.4" in result["sourceIPAddress"].values

    def test_pipeline_detects_iam_changes(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must detect dangerous IAM modifications end to end"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.detect_iam_changes(df)

        # Assert — CreateUser and AttachUserPolicy detected
        assert "CreateUser"       in result["eventName"].values
        assert "AttachUserPolicy" in result["eventName"].values

    def test_pipeline_detects_iam_enumeration(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must detect IAM reconnaissance end to end"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.detect_iam_enumeration(df, threshold=3)

        # Assert — attacker performed 3 enumeration calls
        assert "attacker" in result["userName"].values

    def test_pipeline_detects_credential_abuse(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must detect stolen credentials used from multiple IPs"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.detect_credential_abuse(df, ip_threshold=2)

        # Assert — attacker used key from 2 different IPs
        assert "attacker" in result["userName"].values

    def test_pipeline_detects_role_chaining(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must detect role chaining privilege escalation"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.detect_role_chaining(df, threshold=3)

        # Assert — attacker assumed 3 roles
        assert "attacker" in result["userName"].values

    def test_pipeline_detects_s3_exfiltration(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must detect mass S3 data access end to end"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.detect_s3_exfiltration(df, threshold=5)

        # Assert — attacker downloaded 6 objects
        assert "attacker" in result["userName"].values

    def test_pipeline_detects_ec2_suspicious_activity(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must detect EC2 compromise indicators end to end"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.detect_ec2_suspicious_activity(df)

        # Assert — RunInstances and CreateKeyPair detected
        assert "RunInstances" in result["eventName"].values
        assert "CreateKeyPair" in result["eventName"].values

    def test_pipeline_detects_data_exfiltration(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must detect network exfiltration and log tampering"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.detect_data_exfiltration(df)

        # Assert — DeleteFlowLogs detected
        assert "DeleteFlowLogs" in result["eventName"].values

    def test_pipeline_detects_critical_events(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must flag critical log-deletion events immediately"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.detect_critical_events(df)

        # Assert — DeleteFlowLogs is a critical event
        assert "DeleteFlowLogs" in result["eventName"].values

    def test_pipeline_detects_lambda_abuse(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must detect Lambda function tampering end to end"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.detect_lambda_abuse(df)

        # Assert — UpdateFunctionCode detected
        assert "UpdateFunctionCode" in result["eventName"].values

    def test_pipeline_detects_high_volume_ip(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """Pipeline must detect high volume API scanner end to end"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        result = engine.count_api_calls_by_ip(df, threshold=10)

        # Assert — scanner IP flagged
        assert "5.5.5.5" in result["sourceIPAddress"].values

    def test_run_all_detections_covers_full_scenario(
        self, connector, parser, validator, engine,
        suspicious_cloudtrail_file
    ):
        """run_all_detections must surface threats across all categories"""
        # Arrange
        df = run_pipeline(
            connector, parser, validator, suspicious_cloudtrail_file
        )

        # Act
        results = engine.run_all_detections(df)

        # Assert — every detector must find something in the attack scenario
        assert len(results["failed_logins"])    > 0
        assert len(results["iam_changes"])      > 0
        assert len(results["iam_enumeration"])  > 0
        assert len(results["credential_abuse"]) > 0
        assert len(results["role_chaining"])    > 0
        assert len(results["s3_exfiltration"])  > 0
        assert len(results["ec2_suspicious"])   > 0
        assert len(results["data_exfiltration"]) > 0
        assert len(results["critical_events"])  > 0
        assert len(results["lambda_abuse"])     > 0
        assert len(results["api_calls_by_ip"])  > 0 

@pytest.fixture
def stats_engine():
    """Returns a fresh StatisticsEngine facade instance"""
    return StatisticsEngine()


class TestHeuristicEngineToStatisticsEngine:

    def test_stats_engine_accepts_heuristic_results(
        self, connector, parser, validator, engine, stats_engine,
        valid_cloudtrail_file
    ):
        """StatisticsEngine must accept results from HeuristicEngine"""
        # Arrange
        df      = run_pipeline(connector, parser, validator, valid_cloudtrail_file)
        results = engine.run_all_detections(df)

        # Act
        report = stats_engine.full_report(df, results)

        # Assert
        assert isinstance(report, dict)
        assert report["total_events"] == 3

    def test_clean_pipeline_produces_zero_risk_score(
        self, connector, parser, validator, engine, stats_engine,
        valid_cloudtrail_file
    ):
        """Clean environment must produce risk score of 0"""
        # Arrange
        df      = run_pipeline(connector, parser, validator, valid_cloudtrail_file)
        results = engine.run_all_detections(df)

        # Act
        report = stats_engine.full_report(df, results)

        # Assert
        assert report["risk_score"] == 0

    def test_full_pipeline_attack_scenario_max_risk_score(
        self, connector, parser, validator, engine, stats_engine,
        suspicious_cloudtrail_file
    ):
        """Full attack scenario fires all 11 detectors — risk score capped at 100"""
        # Arrange
        df      = run_pipeline(connector, parser, validator, suspicious_cloudtrail_file)
        results = engine.run_all_detections(df)

        # Act
        report = stats_engine.full_report(df, results)

        # Assert — all 11 detectors fire, weights sum to 130, capped at 100
        assert report["risk_score"] == 100

    def test_full_pipeline_detects_cross_detection_entity(
        self, connector, parser, validator, engine, stats_engine,
        suspicious_cloudtrail_file
    ):
        """'attacker' must appear across multiple detections end to end"""
        # Arrange
        df      = run_pipeline(connector, parser, validator, suspicious_cloudtrail_file)
        results = engine.run_all_detections(df)

        # Act
        report = stats_engine.full_report(df, results)

        # Assert
        entities = report["cross_detection_entities"]["entity"].values
        assert "attacker" in entities
        assert "1.2.3.4" in entities

    def test_full_pipeline_empty_file_statistics(
        self, connector, parser, validator, engine, stats_engine,
        empty_cloudtrail_file
    ):
        """Empty input must produce empty statistics without crash"""
        # Arrange
        df      = run_pipeline(connector, parser, validator, empty_cloudtrail_file)
        results = engine.run_all_detections(df)

        # Act
        report = stats_engine.full_report(df, results)

        # Assert
        assert report["total_events"] == 0
        assert report["unique_ips"] == 0
        assert report["risk_score"] == 0
        assert len(report["detection_summary"]) == 11