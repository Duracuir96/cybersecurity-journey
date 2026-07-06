# src/tests/load/test_load.py

import time
import pytest
from src.data_processing.log_parser import LogParser
from src.data_processing.data_validator import DataValidator
from src.analysis.heuristic_engine import HeuristicEngine
from src.analysis.statistics_engine import StatisticsEngine


# ─── Helper ──────────────────────────────────────────────────

def generate_raw_logs(count):
    """
    Generates synthetic CloudTrail-like raw events for load testing.
    Spreads events across 24 hours, 255 IPs, and 50 users.
    """
    logs = []
    for i in range(count):
        logs.append({
            "eventName":   "DescribeInstances" if i % 2 == 0 else "ConsoleLogin",
            "eventSource": "ec2.amazonaws.com",
            "sourceIPAddress": f"10.0.{i % 255}.{i % 100}",
            "userIdentity": {"type": "IAMUser", "userName": f"user{i % 50}"},
            "eventTime": f"2026-01-25T{(i % 24):02d}:{(i % 60):02d}:00Z"
        })
    return logs


# ─── Fixtures ────────────────────────────────────────────────

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


# ─── Layer 2 — LogParser under volume ────────────────────────

class TestParserLoad:

    def test_parse_10000_events_under_threshold(self, parser):
        """Parsing 10,000 events must complete in under 5 seconds"""
        # Arrange
        raw_logs = generate_raw_logs(10_000)

        # Act
        start  = time.time()
        parsed = parser.parse_json(raw_logs)
        duration = time.time() - start

        # Assert
        assert len(parsed) == 10_000
        assert duration < 5.0, f"Too slow: {duration:.2f}s"

    def test_to_dataframe_10000_events_under_threshold(self, parser):
        """to_dataframe on 10,000 events must complete in under 5 seconds"""
        # Arrange
        raw_logs = generate_raw_logs(10_000)
        parsed   = parser.parse_json(raw_logs)

        # Act
        start = time.time()
        df    = parser.to_dataframe(parsed)
        duration = time.time() - start

        # Assert
        assert df.shape == (10_000, 5)
        assert duration < 5.0, f"Too slow: {duration:.2f}s"


# ─── Layer 3 — DataValidator under volume ────────────────────

class TestValidatorLoad:

    def test_clean_data_50000_rows_under_threshold(self, parser, validator):
        """Validating 50,000 rows must complete in under 10 seconds"""
        # Arrange
        raw_logs = generate_raw_logs(50_000)
        parsed   = parser.parse_json(raw_logs)
        df       = parser.to_dataframe(parsed)

        # Act
        start       = time.time()
        cleaned_df  = validator.clean_data(df)
        duration    = time.time() - start

        # Assert
        assert len(cleaned_df) == 50_000
        assert duration < 10.0, f"Too slow: {duration:.2f}s"


# ─── Layer 4 — HeuristicEngine under volume ──────────────────

class TestHeuristicEngineLoad:

    def test_run_all_detections_10000_rows_under_threshold(
        self, parser, validator, heuristic_engine
    ):
        """run_all_detections on 10,000 rows must complete in under 10 seconds"""
        # Arrange
        raw_logs = generate_raw_logs(10_000)
        parsed   = parser.parse_json(raw_logs)
        df       = parser.to_dataframe(parsed)
        df       = validator.clean_data(df)

        # Act
        start   = time.time()
        results = heuristic_engine.run_all_detections(df)
        duration = time.time() - start

        # Assert
        assert isinstance(results, dict)
        assert duration < 10.0, f"Too slow: {duration:.2f}s"


# ─── Layer 5 — StatisticsEngine under volume ─────────────────

class TestStatisticsEngineLoad:

    def test_full_report_10000_rows_under_threshold(
        self, parser, validator, heuristic_engine, stats_engine
    ):
        """full_report on 10,000 rows must complete in under 10 seconds"""
        # Arrange
        raw_logs = generate_raw_logs(10_000)
        parsed   = parser.parse_json(raw_logs)
        df       = parser.to_dataframe(parsed)
        df       = validator.clean_data(df)
        results  = heuristic_engine.run_all_detections(df)

        # Act
        start  = time.time()
        report = stats_engine.full_report(df, results)
        duration = time.time() - start

        # Assert
        assert isinstance(report, dict)
        assert duration < 10.0, f"Too slow: {duration:.2f}s"


# ─── Full pipeline under volume ──────────────────────────────

class TestFullPipelineLoad:

    def test_full_pipeline_10000_events_under_threshold(
        self, parser, validator, heuristic_engine, stats_engine
    ):
        """Complete pipeline Layer 2-5 on 10,000 events under 15 seconds"""
        # Arrange
        raw_logs = generate_raw_logs(10_000)

        # Act
        start    = time.time()
        parsed   = parser.parse_json(raw_logs)
        df       = parser.to_dataframe(parsed)
        df       = validator.clean_data(df)
        results  = heuristic_engine.run_all_detections(df)
        report   = stats_engine.full_report(df, results)
        duration = time.time() - start

        # Assert
        assert len(df) == 10_000
        assert isinstance(report, dict)
        assert duration < 15.0, f"Too slow: {duration:.2f}s"