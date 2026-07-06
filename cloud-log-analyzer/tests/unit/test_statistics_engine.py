# src/tests/unit/test_statistics_engine.py

import pytest
import pandas as pd
from src.analysis.statistics_engine import StatisticsEngine


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def engine():
    """Returns a fresh StatisticsEngine instance"""
    return StatisticsEngine()

@pytest.fixture
def sample_dataframe():
    """5 events: 3 from S3, 1 EC2, 1 signin — 3 unique IPs, 3 users"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:30:00Z"),
            "eventName":       "ListBuckets",
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T11:00:00Z"),
            "eventName":       "DescribeInstances",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "5.6.7.8",
            "userName":        "bob"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T11:15:00Z"),
            "eventName":       "GetObject",
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "5.6.7.8",
            "userName":        "bob"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T12:00:00Z"),
            "eventName":       "ListObjects",
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userName":        "charlie"
        }
    ])

@pytest.fixture
def empty_dataframe():
    """Empty DataFrame with correct columns"""
    return pd.DataFrame(columns=[
        "eventTime", "eventName", "eventSource",
        "sourceIPAddress", "userName"
    ])

@pytest.fixture
def empty_detection_results():
    """All 11 detectors return empty DataFrames — clean environment"""
    return {
        "failed_logins":     pd.DataFrame(columns=["sourceIPAddress", "login_count"]),
        "iam_changes":       pd.DataFrame(columns=["eventTime", "eventName", "eventSource", "sourceIPAddress", "userName"]),
        "iam_enumeration":   pd.DataFrame(columns=["userName", "enumeration_count"]),
        "credential_abuse":  pd.DataFrame(columns=["userName", "unique_ip_count"]),
        "role_chaining":     pd.DataFrame(columns=["userName", "assume_role_count"]),
        "api_calls_by_ip":   pd.DataFrame(columns=["sourceIPAddress", "call_count"]),
        "s3_exfiltration":   pd.DataFrame(columns=["userName", "s3_event_count"]),
        "ec2_suspicious":    pd.DataFrame(columns=["eventTime", "eventName", "eventSource", "sourceIPAddress", "userName"]),
        "data_exfiltration": pd.DataFrame(columns=["eventTime", "eventName", "eventSource", "sourceIPAddress", "userName"]),
        "critical_events":   pd.DataFrame(columns=["eventTime", "eventName", "eventSource", "sourceIPAddress", "userName"]),
        "lambda_abuse":      pd.DataFrame(columns=["eventTime", "eventName", "eventSource", "sourceIPAddress", "userName"]),
    }

@pytest.fixture
def results_with_critical_event(empty_detection_results):
    """Only critical_events fires — highest weight (25)"""
    results = empty_detection_results.copy()
    results["critical_events"] = pd.DataFrame([{
        "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
        "eventName":       "DeleteFlowLogs",
        "eventSource":     "ec2.amazonaws.com",
        "sourceIPAddress": "1.2.3.4",
        "userName":        "attacker"
    }])
    return results

@pytest.fixture
def results_with_cross_detection(empty_detection_results):
    """
    '1.2.3.4' appears in failed_logins AND api_calls_by_ip.
    'attacker' appears in iam_enumeration AND credential_abuse.
    """
    results = empty_detection_results.copy()

    results["failed_logins"] = pd.DataFrame([
        {"sourceIPAddress": "1.2.3.4", "login_count": 4}
    ])
    results["api_calls_by_ip"] = pd.DataFrame([
        {"sourceIPAddress": "1.2.3.4", "call_count": 12}
    ])
    results["iam_enumeration"] = pd.DataFrame([
        {"userName": "attacker", "enumeration_count": 3}
    ])
    results["credential_abuse"] = pd.DataFrame([
        {"userName": "attacker", "unique_ip_count": 2}
    ])

    return results


# ─── Tests : total_events() ──────────────────────────────────

class TestTotalEvents:

    def test_counts_all_rows(self, engine, sample_dataframe):
        """Should return the total number of rows"""
        # Arrange — 5 events

        # Act
        result = engine.total_events(sample_dataframe)

        # Assert
        assert result == 5

    def test_returns_zero_on_empty_dataframe(self, engine, empty_dataframe):
        """Should return 0 for empty DataFrame"""
        # Arrange

        # Act
        result = engine.total_events(empty_dataframe)

        # Assert
        assert result == 0

    def test_returns_integer(self, engine, sample_dataframe):
        """Should return a native Python int"""
        # Arrange

        # Act
        result = engine.total_events(sample_dataframe)

        # Assert
        assert isinstance(result, int)


# ─── Tests : top_services() ──────────────────────────────────

class TestTopServices:

    def test_returns_dataframe(self, engine, sample_dataframe):
        """Should always return a DataFrame"""
        # Arrange

        # Act
        result = engine.top_services(sample_dataframe)

        # Assert
        assert isinstance(result, pd.DataFrame)

    def test_has_correct_columns(self, engine, sample_dataframe):
        """Result must have eventSource and count columns"""
        # Arrange

        # Act
        result = engine.top_services(sample_dataframe)

        # Assert
        assert "eventSource" in result.columns
        assert "count" in result.columns

    def test_most_used_service_is_first(self, engine, sample_dataframe):
        """s3.amazonaws.com appears 3 times — must rank first"""
        # Arrange — s3=3, ec2=1, signin=1

        # Act
        result = engine.top_services(sample_dataframe)

        # Assert
        assert result.iloc[0]["eventSource"] == "s3.amazonaws.com"
        assert result.iloc[0]["count"] == 3

    def test_respects_top_n_limit(self, engine, sample_dataframe):
        """Should return at most top_n rows"""
        # Arrange — 3 distinct services, ask for top 2

        # Act
        result = engine.top_services(sample_dataframe, top_n=2)

        # Assert
        assert len(result) == 2

    def test_returns_empty_on_empty_dataframe(self, engine, empty_dataframe):
        """Should return empty DataFrame when input is empty"""
        # Arrange

        # Act
        result = engine.top_services(empty_dataframe)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


# ─── Tests : unique_ip_count() ───────────────────────────────

class TestUniqueIPCount:

    def test_counts_distinct_ips(self, engine, sample_dataframe):
        """Should count distinct IPs, not total occurrences"""
        # Arrange — 5 rows but only 3 distinct IPs

        # Act
        result = engine.unique_ip_count(sample_dataframe)

        # Assert
        assert result == 3

    def test_returns_zero_on_empty_dataframe(self, engine, empty_dataframe):
        """Should return 0 for empty DataFrame"""
        # Arrange

        # Act
        result = engine.unique_ip_count(empty_dataframe)

        # Assert
        assert result == 0

    def test_returns_integer(self, engine, sample_dataframe):
        """Should return a native Python int, not numpy.int64"""
        # Arrange

        # Act
        result = engine.unique_ip_count(sample_dataframe)

        # Assert
        assert isinstance(result, int)


# ─── Tests : top_users() ─────────────────────────────────────

class TestTopUsers:

    def test_returns_dataframe(self, engine, sample_dataframe):
        """Should always return a DataFrame"""
        # Arrange

        # Act
        result = engine.top_users(sample_dataframe)

        # Assert
        assert isinstance(result, pd.DataFrame)

    def test_has_correct_columns(self, engine, sample_dataframe):
        """Result must have userName and count columns"""
        # Arrange

        # Act
        result = engine.top_users(sample_dataframe)

        # Assert
        assert "userName" in result.columns
        assert "count" in result.columns

    def test_most_active_user_is_first(self, engine, sample_dataframe):
        """alice and bob both have 2 events, charlie has 1"""
        # Arrange

        # Act
        result = engine.top_users(sample_dataframe)

        # Assert — top user has 2 events
        assert result.iloc[0]["count"] == 2

    def test_returns_empty_on_empty_dataframe(self, engine, empty_dataframe):
        """Should return empty DataFrame when input is empty"""
        # Arrange

        # Act
        result = engine.top_users(empty_dataframe)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


# ─── Tests : events_per_hour() ───────────────────────────────

class TestEventsPerHour:

    def test_returns_dataframe(self, engine, sample_dataframe):
        """Should always return a DataFrame"""
        # Arrange

        # Act
        result = engine.events_per_hour(sample_dataframe)

        # Assert
        assert isinstance(result, pd.DataFrame)

    def test_has_correct_columns(self, engine, sample_dataframe):
        """Result must have hour and count columns"""
        # Arrange

        # Act
        result = engine.events_per_hour(sample_dataframe)

        # Assert
        assert "hour" in result.columns
        assert "count" in result.columns

    def test_groups_by_hour_correctly(self, engine, sample_dataframe):
        """10:00 and 10:30 must be grouped into the same hour bucket"""
        # Arrange — 2 events at hour 10, 2 at hour 11, 1 at hour 12

        # Act
        result = engine.events_per_hour(sample_dataframe)

        # Assert — 3 distinct hour buckets
        assert len(result) == 3
        assert result.iloc[0]["count"] == 2  # hour 10

    def test_sorted_chronologically(self, engine, sample_dataframe):
        """Result must be sorted by hour ascending"""
        # Arrange

        # Act
        result = engine.events_per_hour(sample_dataframe)

        # Assert
        hours = result["hour"].tolist()
        assert hours == sorted(hours)

    def test_returns_empty_on_empty_dataframe(self, engine, empty_dataframe):
        """Should return empty DataFrame when input is empty"""
        # Arrange

        # Act
        result = engine.events_per_hour(empty_dataframe)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


# ─── Tests : detection_summary() ─────────────────────────────

class TestDetectionSummary:

    def test_returns_dataframe(self, engine, empty_detection_results):
        """Should always return a DataFrame"""
        # Arrange

        # Act
        result = engine.detection_summary(empty_detection_results)

        # Assert
        assert isinstance(result, pd.DataFrame)

    def test_has_correct_columns(self, engine, empty_detection_results):
        """Result must have detection, count and status columns"""
        # Arrange

        # Act
        result = engine.detection_summary(empty_detection_results)

        # Assert
        assert "detection" in result.columns
        assert "count" in result.columns
        assert "status" in result.columns

    def test_all_clear_on_empty_results(self, engine, empty_detection_results):
        """All detections must be CLEAR when nothing is detected"""
        # Arrange — all empty DataFrames

        # Act
        result = engine.detection_summary(empty_detection_results)

        # Assert
        assert (result["status"] == "CLEAR").all()
        assert (result["count"] == 0).all()

    def test_flags_alert_on_non_empty_detection(
        self, engine, results_with_critical_event
    ):
        """A detection with rows must be marked ALERT"""
        # Arrange — critical_events has 1 row

        # Act
        result = engine.detection_summary(results_with_critical_event)

        # Assert
        critical_row = result[result["detection"] == "critical_events"]
        assert critical_row.iloc[0]["status"] == "ALERT"
        assert critical_row.iloc[0]["count"] == 1

    def test_covers_all_eleven_detections(self, engine, empty_detection_results):
        """Summary must include all 11 detections from HeuristicEngine"""
        # Arrange — 11 keys in results

        # Act
        result = engine.detection_summary(empty_detection_results)

        # Assert
        assert len(result) == 11


# ─── Tests : risk_score() ────────────────────────────────────

class TestRiskScore:

    def test_returns_zero_on_clean_environment(
        self, engine, empty_detection_results
    ):
        """Risk score must be 0 when no detection fires"""
        # Arrange — all empty

        # Act
        result = engine.risk_score(empty_detection_results)

        # Assert
        assert result == 0

    def test_critical_event_adds_highest_weight(
        self, engine, results_with_critical_event
    ):
        """critical_events has weight 25 — single detection score"""
        # Arrange — only critical_events fires

        # Act
        result = engine.risk_score(results_with_critical_event)

        # Assert
        assert result == 25

    def test_score_is_capped_at_100(self, engine, empty_detection_results):
        """Score must never exceed 100 even if all detections fire"""
        # Arrange — fill ALL 11 detections (sum of weights = 130)
        results = empty_detection_results.copy()
        for name in results:
            results[name] = pd.DataFrame([{"dummy": "value"}])

        # Act
        result = engine.risk_score(results)

        # Assert — capped at 100
        assert result == 100

    def test_returns_integer(self, engine, empty_detection_results):
        """Risk score must be a native Python int"""
        # Arrange

        # Act
        result = engine.risk_score(empty_detection_results)

        # Assert
        assert isinstance(result, int)

    def test_unknown_detection_uses_default_weight(
        self, engine, empty_detection_results
    ):
        """A detection key not in DETECTION_WEIGHTS uses default weight 5"""
        # Arrange — add a future detector not yet weighted
        results = empty_detection_results.copy()
        results["some_future_detector"] = pd.DataFrame([{"dummy": "value"}])

        # Act
        result = engine.risk_score(results)

        # Assert — default weight applied
        assert result == 5


# ─── Tests : cross_detection_entities() ──────────────────────

class TestCrossDetectionEntities:

    def test_returns_dataframe(self, engine, empty_detection_results):
        """Should always return a DataFrame"""
        # Arrange

        # Act
        result = engine.cross_detection_entities(empty_detection_results)

        # Assert
        assert isinstance(result, pd.DataFrame)

    def test_returns_empty_on_clean_environment(
        self, engine, empty_detection_results
    ):
        """No cross-detection entity when nothing is detected"""
        # Arrange — all empty

        # Act
        result = engine.cross_detection_entities(empty_detection_results)

        # Assert
        assert len(result) == 0

    def test_detects_ip_in_multiple_detections(
        self, engine, results_with_cross_detection
    ):
        """'1.2.3.4' appears in failed_logins AND api_calls_by_ip"""
        # Arrange

        # Act
        result = engine.cross_detection_entities(
            results_with_cross_detection, min_detections=2
        )

        # Assert
        assert "1.2.3.4" in result["entity"].values

    def test_detects_user_in_multiple_detections(
        self, engine, results_with_cross_detection
    ):
        """'attacker' appears in iam_enumeration AND credential_abuse"""
        # Arrange

        # Act
        result = engine.cross_detection_entities(
            results_with_cross_detection, min_detections=2
        )

        # Assert
        assert "attacker" in result["entity"].values

    def test_detection_count_is_correct(
        self, engine, results_with_cross_detection
    ):
        """'1.2.3.4' must show detection_count == 2"""
        # Arrange

        # Act
        result = engine.cross_detection_entities(
            results_with_cross_detection, min_detections=2
        )

        # Assert
        ip_row = result[result["entity"] == "1.2.3.4"]
        assert ip_row.iloc[0]["detection_count"] == 2

    def test_excludes_entities_below_min_detections(
        self, engine, results_with_cross_detection
    ):
        """min_detections=3 must exclude entities appearing in only 2"""
        # Arrange — nothing in this fixture reaches 3 detections

        # Act
        result = engine.cross_detection_entities(
            results_with_cross_detection, min_detections=3
        )

        # Assert
        assert len(result) == 0

    def test_has_correct_columns(self, engine, results_with_cross_detection):
        """Result must have entity, detection_count, detections columns"""
        # Arrange

        # Act
        result = engine.cross_detection_entities(results_with_cross_detection)

        # Assert
        assert "entity" in result.columns
        assert "detection_count" in result.columns
        assert "detections" in result.columns


# ─── Tests : full_report() ───────────────────────────────────

class TestFullReport:

    def test_returns_dict_with_all_keys(
        self, engine, sample_dataframe, empty_detection_results
    ):
        """Should return a dict with all expected keys"""
        # Arrange

        # Act
        report = engine.full_report(sample_dataframe, empty_detection_results)

        # Assert
        assert isinstance(report, dict)
        expected_keys = {
            "total_events", "unique_ips", "top_services", "top_users",
            "events_per_hour", "detection_summary", "risk_score",
            "cross_detection_entities"
        }
        assert expected_keys.issubset(report.keys())

    def test_full_report_on_empty_input(
        self, engine, empty_dataframe, empty_detection_results
    ):
        """Should not crash on empty DataFrame and empty results"""
        # Arrange

        # Act
        report = engine.full_report(empty_dataframe, empty_detection_results)

        # Assert
        assert report["total_events"] == 0
        assert report["unique_ips"] == 0
        assert report["risk_score"] == 0
        assert len(report["top_services"]) == 0
        assert len(report["cross_detection_entities"]) == 0