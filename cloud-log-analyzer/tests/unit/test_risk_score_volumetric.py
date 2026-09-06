# src/tests/unit/test_risk_score_volumetric.py
#
# v1.5 — validates that the risk score scales with attack intensity,
# not just presence/absence.

import pandas as pd
import pytest

from src.analysis.statistics.security_statistics import SecurityStatistics


@pytest.fixture
def sec():
    return SecurityStatistics()


def _failed(login_count):
    return pd.DataFrame({"sourceIPAddress": ["1.2.3.4"], "login_count": [login_count]})


def _iam_changes(n):
    return pd.DataFrame({"eventName": ["CreateUser"] * n, "userName": ["x"] * n})


def _empty_results():
    return {k: pd.DataFrame() for k in SecurityStatistics.DETECTION_WEIGHTS}


# ── Volumetric behaviour ─────────────────────────────────────

def test_high_volume_login_produces_higher_score(sec):
    """1000 failed logins must score higher than 3."""
    low  = _empty_results();  low["failed_logins"]  = _failed(3)
    high = _empty_results();  high["failed_logins"] = _failed(1000)
    assert sec.risk_score(high) > sec.risk_score(low)


def test_score_increases_with_iam_event_count(sec):
    """5 IAM events must score higher than 1."""
    one  = _empty_results(); one["iam_changes"]  = _iam_changes(1)
    five = _empty_results(); five["iam_changes"] = _iam_changes(5)
    assert sec.risk_score(five) > sec.risk_score(one)


def test_critical_events_always_maximum(sec):
    """A critical event contributes its full weight (25)."""
    r = _empty_results()
    r["critical_events"] = pd.DataFrame({"eventName": ["StopLogging"]})
    assert sec.risk_score(r) == 25


# ── Safety / interface guarantees ────────────────────────────

def test_clean_results_score_zero(sec):
    """No detections = score 0."""
    assert sec.risk_score(_empty_results()) == 0


def test_empty_dict_score_zero(sec):
    """An empty results dict must not crash and scores 0."""
    assert sec.risk_score({}) == 0


def test_score_never_exceeds_100(sec):
    """Even a full-blown attack caps at 100."""
    r = {
        "failed_logins":     _failed(100000),
        "iam_changes":       _iam_changes(50),
        "critical_events":   pd.DataFrame({"eventName": ["DeleteTrail"]}),
        "s3_exfiltration":   pd.DataFrame({"userName": ["a"], "s3_event_count": [9999]}),
        "credential_abuse":  pd.DataFrame({"userName": ["a"], "unique_ip_count": [50]}),
        "role_chaining":     pd.DataFrame({"userName": ["a"], "assume_role_count": [50]}),
        "iam_enumeration":   pd.DataFrame({"userName": ["a"], "enumeration_count": [999]}),
        "api_calls_by_ip":   pd.DataFrame({"sourceIPAddress": ["a"], "call_count": [99999]}),
        "ec2_suspicious":    pd.DataFrame({"eventName": ["RunInstances"]}),
        "lambda_abuse":      pd.DataFrame({"eventName": ["UpdateFunctionCode"]}),
        "data_exfiltration": pd.DataFrame({"eventName": ["DeleteFlowLogs"]}),
    }
    assert sec.risk_score(r) == 100


def test_returns_int(sec):
    """The public interface must return a plain int."""
    r = _empty_results(); r["failed_logins"] = _failed(10)
    assert isinstance(sec.risk_score(r), int)


def test_per_detection_cap_is_respected(sec):
    """failed_logins alone never exceeds its cap of 21."""
    r = _empty_results(); r["failed_logins"] = _failed(1_000_000)
    assert sec.risk_score(r) == 21


def test_missing_intensity_column_does_not_crash(sec):
    """A non-empty df without the expected column falls back gracefully."""
    r = _empty_results()
    r["failed_logins"] = pd.DataFrame({"sourceIPAddress": ["1.2.3.4"]})  # no login_count
    # base weight applied, bonus 0
    assert sec.risk_score(r) == 7