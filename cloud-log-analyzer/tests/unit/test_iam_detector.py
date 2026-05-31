# src/tests/unit/test_iam_detector.py

import pytest
import pandas as pd
from src.analysis.detectors.iam_detector import IAMDetector


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def detector():
    """Returns a fresh IAMDetector instance for each test"""
    return IAMDetector()

@pytest.fixture
def empty_dataframe():
    """Empty DataFrame with correct columns"""
    return pd.DataFrame(columns=[
        "eventTime", "eventName", "eventSource",
        "sourceIPAddress", "userName"
    ])

@pytest.fixture
def brute_force_dataframe():
    """DataFrame with one IP attempting ConsoleLogin 4 times"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }
    ] * 4 + [
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:05:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",  # only 1 login — not suspicious
            "userName":        "bob"
        }
    ])

@pytest.fixture
def iam_changes_dataframe():
    """DataFrame with dangerous IAM events mixed with normal events"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "CreateUser",
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:01:00Z"),
            "eventName":       "DeleteUser",
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:02:00Z"),
            "eventName":       "GetBucketAcl",  # normal — must be excluded
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "5.6.7.8",
            "userName":        "bob"
        }
    ])

@pytest.fixture
def enumeration_dataframe():
    """DataFrame with one user performing IAM reconnaissance"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ListUsers",
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:01:00Z"),
            "eventName":       "ListRoles",
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:02:00Z"),
            "eventName":       "GetAccountAuthorizationDetails",
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:03:00Z"),
            "eventName":       "ListPolicies",
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:04:00Z"),
            "eventName":       "GetBucketAcl",  # normal — not enumeration
            "eventSource":     "s3.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userName":        "normal_user"
        }
    ])

@pytest.fixture
def credential_abuse_dataframe():
    """DataFrame with same user calling GetCallerIdentity from multiple IPs"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "GetCallerIdentity",
            "eventSource":     "sts.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",   # IP 1
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:05:00Z"),
            "eventName":       "GetCallerIdentity",
            "eventSource":     "sts.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",   # IP 2 — same user, different IP
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:10:00Z"),
            "eventName":       "GetCallerIdentity",
            "eventSource":     "sts.amazonaws.com",
            "sourceIPAddress": "5.5.5.5",   # only 1 IP — not suspicious
            "userName":        "bob"
        }
    ])

@pytest.fixture
def role_chaining_dataframe():
    """DataFrame with one user assuming multiple roles"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "AssumeRole",
            "eventSource":     "sts.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "attacker"
        }
    ] * 4 + [
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:05:00Z"),
            "eventName":       "AssumeRole",
            "eventSource":     "sts.amazonaws.com",
            "sourceIPAddress": "9.9.9.9",
            "userName":        "normal_user"  # only 1 AssumeRole — not suspicious
        }
    ])

@pytest.fixture
def high_volume_dataframe():
    """DataFrame with one IP making 15 API calls"""
    rows = [{
        "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
        "eventName":       "DescribeInstances",
        "eventSource":     "ec2.amazonaws.com",
        "sourceIPAddress": "1.2.3.4",
        "userName":        "scanner"
    }] * 15 + [{
        "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
        "eventName":       "ListBuckets",
        "eventSource":     "s3.amazonaws.com",
        "sourceIPAddress": "9.9.9.9",  # only 3 calls — not suspicious
        "userName":        "alice"
    }] * 3
    return pd.DataFrame(rows)


# ─── Tests : detect_failed_logins() ──────────────────────────

class TestDetectFailedLogins:

    def test_returns_dataframe(self, detector, brute_force_dataframe):
        """Should always return a DataFrame"""
        result = detector.detect_failed_logins(brute_force_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_detects_suspicious_ip(self, detector, brute_force_dataframe):
        """Should detect IP with login count above threshold"""
        result = detector.detect_failed_logins(brute_force_dataframe, threshold=3)
        assert "1.2.3.4" in result["sourceIPAddress"].values

    def test_excludes_ip_below_threshold(self, detector, brute_force_dataframe):
        """Should not flag IP with login count below threshold"""
        result = detector.detect_failed_logins(brute_force_dataframe, threshold=3)
        assert "9.9.9.9" not in result["sourceIPAddress"].values

    def test_login_count_is_correct(self, detector, brute_force_dataframe):
        """login_count must match actual number of attempts"""
        result = detector.detect_failed_logins(brute_force_dataframe, threshold=3)
        ip_row = result[result["sourceIPAddress"] == "1.2.3.4"]
        assert ip_row.iloc[0]["login_count"] == 4

    def test_returns_empty_on_empty_input(self, detector, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        result = detector.detect_failed_logins(empty_dataframe)
        assert len(result) == 0

    def test_sorted_descending(self, detector, brute_force_dataframe):
        """Results must be sorted from most attempts to least"""
        extra = pd.DataFrame([{
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "5.5.5.5",
            "userName":        "charlie"
        }] * 6)
        df = pd.concat([brute_force_dataframe, extra], ignore_index=True)
        result = detector.detect_failed_logins(df, threshold=3)
        assert result.iloc[0]["sourceIPAddress"] == "5.5.5.5"


# ─── Tests : detect_iam_changes() ────────────────────────────

class TestDetectIAMChanges:

    def test_returns_dataframe(self, detector, iam_changes_dataframe):
        """Should always return a DataFrame"""
        result = detector.detect_iam_changes(iam_changes_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_detects_dangerous_events(self, detector, iam_changes_dataframe):
        """Should detect all dangerous IAM events"""
        result = detector.detect_iam_changes(iam_changes_dataframe)
        assert len(result) == 2

    def test_excludes_normal_events(self, detector, iam_changes_dataframe):
        """Should not include normal events"""
        result = detector.detect_iam_changes(iam_changes_dataframe)
        assert "GetBucketAcl" not in result["eventName"].values

    def test_returns_empty_on_empty_input(self, detector, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        result = detector.detect_iam_changes(empty_dataframe)
        assert len(result) == 0

    def test_dangerous_events_list_defined(self, detector):
        """IAM_DANGEROUS_EVENTS must contain critical events"""
        assert "CreateUser" in detector.IAM_DANGEROUS_EVENTS
        assert "DeleteUser" in detector.IAM_DANGEROUS_EVENTS
        assert "AttachUserPolicy" in detector.IAM_DANGEROUS_EVENTS


# ─── Tests : detect_iam_enumeration() ────────────────────────

class TestDetectIAMEnumeration:

    def test_returns_dataframe(self, detector, enumeration_dataframe):
        """Should always return a DataFrame"""
        result = detector.detect_iam_enumeration(enumeration_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_detects_attacker(self, detector, enumeration_dataframe):
        """Should detect user performing IAM enumeration above threshold"""
        result = detector.detect_iam_enumeration(enumeration_dataframe, threshold=3)
        assert "attacker" in result["userName"].values

    def test_excludes_normal_user(self, detector, enumeration_dataframe):
        """Should not flag user with enumeration count below threshold"""
        result = detector.detect_iam_enumeration(enumeration_dataframe, threshold=3)
        assert "normal_user" not in result["userName"].values

    def test_enumeration_count_is_correct(self, detector, enumeration_dataframe):
        """enumeration_count must match actual number of recon events"""
        result = detector.detect_iam_enumeration(enumeration_dataframe, threshold=3)
        attacker_row = result[result["userName"] == "attacker"]
        assert attacker_row.iloc[0]["enumeration_count"] == 4

    def test_returns_empty_on_empty_input(self, detector, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        result = detector.detect_iam_enumeration(empty_dataframe)
        assert len(result) == 0

    def test_enumeration_events_list_defined(self, detector):
        """IAM_ENUMERATION_EVENTS must contain recon events"""
        assert "ListUsers" in detector.IAM_ENUMERATION_EVENTS
        assert "GetAccountAuthorizationDetails" in detector.IAM_ENUMERATION_EVENTS


# ─── Tests : detect_credential_abuse() ───────────────────────

class TestDetectCredentialAbuse:

    def test_returns_dataframe(self, detector, credential_abuse_dataframe):
        """Should always return a DataFrame"""
        result = detector.detect_credential_abuse(credential_abuse_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_detects_user_with_multiple_ips(self, detector, credential_abuse_dataframe):
        """Should detect user calling from multiple IPs"""
        result = detector.detect_credential_abuse(
            credential_abuse_dataframe, ip_threshold=2
        )
        assert "alice" in result["userName"].values

    def test_excludes_user_with_single_ip(self, detector, credential_abuse_dataframe):
        """Should not flag user calling from single IP"""
        result = detector.detect_credential_abuse(
            credential_abuse_dataframe, ip_threshold=2
        )
        assert "bob" not in result["userName"].values

    def test_unique_ip_count_is_correct(self, detector, credential_abuse_dataframe):
        """unique_ip_count must match actual number of distinct IPs"""
        result = detector.detect_credential_abuse(
            credential_abuse_dataframe, ip_threshold=2
        )
        alice_row = result[result["userName"] == "alice"]
        assert alice_row.iloc[0]["unique_ip_count"] == 2

    def test_returns_empty_on_empty_input(self, detector, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        result = detector.detect_credential_abuse(empty_dataframe)
        assert len(result) == 0


# ─── Tests : detect_role_chaining() ──────────────────────────

class TestDetectRoleChaining:

    def test_returns_dataframe(self, detector, role_chaining_dataframe):
        """Should always return a DataFrame"""
        result = detector.detect_role_chaining(role_chaining_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_detects_attacker(self, detector, role_chaining_dataframe):
        """Should detect user assuming roles above threshold"""
        result = detector.detect_role_chaining(role_chaining_dataframe, threshold=3)
        assert "attacker" in result["userName"].values

    def test_excludes_normal_user(self, detector, role_chaining_dataframe):
        """Should not flag user with single AssumeRole"""
        result = detector.detect_role_chaining(role_chaining_dataframe, threshold=3)
        assert "normal_user" not in result["userName"].values

    def test_assume_role_count_is_correct(self, detector, role_chaining_dataframe):
        """assume_role_count must match actual number of AssumeRole calls"""
        result = detector.detect_role_chaining(role_chaining_dataframe, threshold=3)
        attacker_row = result[result["userName"] == "attacker"]
        assert attacker_row.iloc[0]["assume_role_count"] == 4

    def test_returns_empty_on_empty_input(self, detector, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        result = detector.detect_role_chaining(empty_dataframe)
        assert len(result) == 0


# ─── Tests : count_api_calls_by_ip() ─────────────────────────

class TestCountAPICallsByIP:

    def test_returns_dataframe(self, detector, high_volume_dataframe):
        """Should always return a DataFrame"""
        result = detector.count_api_calls_by_ip(high_volume_dataframe)
        assert isinstance(result, pd.DataFrame)

    def test_detects_high_volume_ip(self, detector, high_volume_dataframe):
        """Should detect IP making more calls than threshold"""
        result = detector.count_api_calls_by_ip(high_volume_dataframe, threshold=10)
        assert "1.2.3.4" in result["sourceIPAddress"].values

    def test_excludes_low_volume_ip(self, detector, high_volume_dataframe):
        """Should not flag IP below threshold"""
        result = detector.count_api_calls_by_ip(high_volume_dataframe, threshold=10)
        assert "9.9.9.9" not in result["sourceIPAddress"].values

    def test_call_count_is_correct(self, detector, high_volume_dataframe):
        """call_count must match actual number of calls"""
        result = detector.count_api_calls_by_ip(high_volume_dataframe, threshold=10)
        ip_row = result[result["sourceIPAddress"] == "1.2.3.4"]
        assert ip_row.iloc[0]["call_count"] == 15

    def test_returns_empty_on_empty_input(self, detector, empty_dataframe):
        """Should return empty DataFrame on empty input"""
        result = detector.count_api_calls_by_ip(empty_dataframe)
        assert len(result) == 0

    def test_sorted_descending(self, detector, high_volume_dataframe):
        """Results must be sorted from most calls to least"""
        extra = pd.DataFrame([{
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "DescribeInstances",
            "eventSource":     "ec2.amazonaws.com",
            "sourceIPAddress": "7.7.7.7",
            "userName":        "scanner2"
        }] * 20)
        df = pd.concat([high_volume_dataframe, extra], ignore_index=True)
        result = detector.count_api_calls_by_ip(df, threshold=10)
        assert result.iloc[0]["sourceIPAddress"] == "7.7.7.7"