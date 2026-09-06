# src/tests/unit/test_risk_score_entity.py
#
# v2.0 — validates entity-based Risk-Based Alerting.

import pandas as pd
import pytest

from src.analysis.statistics.security_statistics import SecurityStatistics


@pytest.fixture
def sec():
    return SecurityStatistics()


def _empty():
    return {k: pd.DataFrame() for k in SecurityStatistics.DETECTION_WEIGHTS}


# ── Entity accumulation ──────────────────────────────────────

def test_entity_score_accumulates_across_detections(sec):
    """Same IP flagged by 3 detectors must accumulate their contributions."""
    ip = "1.2.3.4"
    r = _empty()
    r["failed_logins"]   = pd.DataFrame({"sourceIPAddress": [ip], "login_count": [3]})
    r["api_calls_by_ip"] = pd.DataFrame({"sourceIPAddress": [ip], "call_count": [10]})
    r["ec2_suspicious"]  = pd.DataFrame({"sourceIPAddress": [ip], "eventName": ["RunInstances"]})

    scores = sec.risk_score_by_entity(r)
    # 7 (failed) + 5 (api) + 10 (ec2 base) = 22
    assert scores[ip] == 22


def test_global_score_equals_max_entity_score(sec):
    """Global score must equal the most dangerous entity's score."""
    r = _empty()
    r["failed_logins"]  = pd.DataFrame({"sourceIPAddress": ["weak"], "login_count": [3]})   # 7
    r["credential_abuse"] = pd.DataFrame({"userName": ["strong"], "unique_ip_count": [2]})  # 30
    scores = sec.risk_score_by_entity(r)
    assert sec.risk_score(r) == max(scores.values()) == 30


def test_clean_environment_produces_zero(sec):
    """No detections = no entity scores and global score 0."""
    assert sec.risk_score_by_entity(_empty()) == {}
    assert sec.risk_score(_empty()) == 0


def test_volumetric_weight_reused_per_entity(sec):
    """An intense actor scores higher than a light one for the same detector."""
    light = _empty(); light["failed_logins"] = pd.DataFrame({"sourceIPAddress": ["a"], "login_count": [3]})
    heavy = _empty(); heavy["failed_logins"] = pd.DataFrame({"sourceIPAddress": ["a"], "login_count": [200]})
    assert sec.risk_score(heavy) > sec.risk_score(light)


def test_two_entities_scored_independently(sec):
    """Different IPs in the same detection are scored separately, not summed."""
    r = _empty()
    r["failed_logins"] = pd.DataFrame({
        "sourceIPAddress": ["1.1.1.1", "2.2.2.2"],
        "login_count":     [3, 200],
    })
    scores = sec.risk_score_by_entity(r)
    assert scores["1.1.1.1"] == 7      # 7 + 3//5
    assert scores["2.2.2.2"] == 21     # 7 + 200//5, capped at 21
    assert sec.risk_score(r) == 21


def test_entity_score_capped_at_100(sec):
    """A single entity flagged everywhere never exceeds 100."""
    ip = "evil"; user = "evil"
    r = {
        "failed_logins":     pd.DataFrame({"sourceIPAddress": [ip], "login_count": [99999]}),
        "api_calls_by_ip":   pd.DataFrame({"sourceIPAddress": [ip], "call_count": [99999]}),
        "ec2_suspicious":    pd.DataFrame({"sourceIPAddress": [ip], "eventName": ["RunInstances"]}),
        "data_exfiltration": pd.DataFrame({"sourceIPAddress": [ip], "eventName": ["DeleteFlowLogs"]}),
        "credential_abuse":  pd.DataFrame({"userName": [user], "unique_ip_count": [50]}),
        "iam_changes":       pd.DataFrame({"userName": [user] * 50, "eventName": ["CreateUser"] * 50}),
        "critical_events":   pd.DataFrame({"userName": [user], "eventName": ["DeleteTrail"]}),
    }
    scores = sec.risk_score_by_entity(r)
    assert all(s <= 100 for s in scores.values())
    assert sec.risk_score(r) == 100


def test_risk_score_returns_int(sec):
    r = _empty(); r["failed_logins"] = pd.DataFrame({"sourceIPAddress": ["a"], "login_count": [10]})
    assert isinstance(sec.risk_score(r), int)


def test_cross_detection_has_risk_score_column(sec):
    """cross_detection_entities now carries a real per-entity risk score."""
    ip = "1.2.3.4"
    r = _empty()
    r["failed_logins"]   = pd.DataFrame({"sourceIPAddress": [ip], "login_count": [200]})
    r["api_calls_by_ip"] = pd.DataFrame({"sourceIPAddress": [ip], "call_count": [900]})
    cd = sec.cross_detection_entities(r)
    assert "risk_score" in cd.columns
    assert cd.iloc[0]["entity"] == ip
    assert cd.iloc[0]["risk_score"] == 33   # 21 (failed cap) + 12 (api cap)