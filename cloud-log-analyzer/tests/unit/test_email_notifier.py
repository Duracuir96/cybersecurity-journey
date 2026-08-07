# src/tests/unit/test_email_notifier.py

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.notifications.email_notifier import EmailNotifier


@pytest.fixture
def notifier():
    """Returns a configured EmailNotifier with test credentials"""
    n = EmailNotifier()
    n.smtp_user     = "test@gmail.com"
    n.smtp_password = "testpassword"
    n.sender        = "test@gmail.com"
    n.recipient     = "recipient@gmail.com"
    return n

@pytest.fixture
def high_risk_report():
    """Report with risk score 75 — triggers email"""
    return {
        "risk_score":    75,
        "total_events":  100,
        "unique_ips":    12,
        "detection_summary": pd.DataFrame([
            {"detection": "critical_events", "count": 1, "status": "ALERT"},
            {"detection": "iam_changes",     "count": 2, "status": "ALERT"},
        ]),
        "cross_detection_entities": pd.DataFrame([
            {"entity": "1.2.3.4", "detection_count": 3,
             "detections": "failed_logins, iam_enumeration, api_calls_by_ip"}
        ])
    }

@pytest.fixture
def low_risk_report():
    """Report with risk score 0 — no email"""
    return {
        "risk_score":    0,
        "total_events":  10,
        "unique_ips":    2,
        "detection_summary": pd.DataFrame(columns=["detection","count","status"]),
        "cross_detection_entities": pd.DataFrame(columns=["entity","detection_count","detections"])
    }

@pytest.fixture
def empty_results():
    """All detections empty"""
    return {
        "failed_logins":     pd.DataFrame(),
        "iam_changes":       pd.DataFrame(),
        "critical_events":   pd.DataFrame(),
        "credential_abuse":  pd.DataFrame(),
        "iam_enumeration":   pd.DataFrame(),
        "role_chaining":     pd.DataFrame(),
        "s3_exfiltration":   pd.DataFrame(),
        "ec2_suspicious":    pd.DataFrame(),
        "data_exfiltration": pd.DataFrame(),
        "lambda_abuse":      pd.DataFrame(),
        "api_calls_by_ip":   pd.DataFrame(),
    }

@pytest.fixture
def critical_results(empty_results):
    """Results with critical event"""
    results = empty_results.copy()
    results["critical_events"] = pd.DataFrame([{
        "eventTime": pd.Timestamp("2026-01-25T10:00:00Z"),
        "eventName": "DeleteFlowLogs",
        "eventSource": "ec2.amazonaws.com",
        "sourceIPAddress": "1.2.3.4",
        "userName": "attacker"
    }])
    return results


# ─── Tests : _is_configured() ────────────────────────────────

class TestIsConfigured:

    def test_returns_true_when_all_credentials_set(self, notifier):
        """Should return True when all SMTP credentials are present"""
        assert notifier._is_configured() is True

    def test_returns_false_when_user_missing(self, notifier):
        """Should return False when SMTP user is empty"""
        notifier.smtp_user = ""
        assert notifier._is_configured() is False

    def test_returns_false_when_password_missing(self, notifier):
        """Should return False when SMTP password is empty"""
        notifier.smtp_password = ""
        assert notifier._is_configured() is False

    def test_returns_false_when_recipient_missing(self, notifier):
        """Should return False when recipient is empty"""
        notifier.recipient = ""
        assert notifier._is_configured() is False


# ─── Tests : _build_subject() ────────────────────────────────

class TestBuildSubject:

    def test_critical_score_has_critical_label(self, notifier, high_risk_report):
        """Risk score >= 75 must produce CRITICAL subject"""
        subject = notifier._build_subject(high_risk_report)
        assert "CRITICAL" in subject

    def test_subject_contains_risk_score(self, notifier, high_risk_report):
        """Subject must contain the risk score"""
        subject = notifier._build_subject(high_risk_report)
        assert "75" in subject

    def test_low_score_has_low_label(self, notifier, low_risk_report):
        """Risk score 0 must produce LOW subject"""
        subject = notifier._build_subject(low_risk_report)
        assert "LOW" in subject

    def test_subject_contains_cloud_log_analyzer(self, notifier, high_risk_report):
        """Subject must identify the sender application"""
        subject = notifier._build_subject(high_risk_report)
        assert "Cloud Log Analyzer" in subject


# ─── Tests : _build_body() ───────────────────────────────────

class TestBuildBody:

    def test_returns_string(self, notifier, high_risk_report, critical_results):
        """Body must be a non-empty string"""
        body = notifier._build_body(high_risk_report, critical_results)
        assert isinstance(body, str)
        assert len(body) > 0

    def test_body_contains_risk_score(self, notifier, high_risk_report, critical_results):
        """Body must display the risk score"""
        body = notifier._build_body(high_risk_report, critical_results)
        assert "75/100" in body

    def test_body_contains_total_events(self, notifier, high_risk_report, critical_results):
        """Body must display total events count"""
        body = notifier._build_body(high_risk_report, critical_results)
        assert "100" in body

    def test_body_is_html(self, notifier, high_risk_report, critical_results):
        """Body must be valid HTML"""
        body = notifier._build_body(high_risk_report, critical_results)
        assert "<!DOCTYPE html>" in body
        assert "</html>" in body


# ─── Tests : send_alert() ────────────────────────────────────

class TestSendAlert:

    def test_returns_false_when_not_configured(self, high_risk_report, critical_results):
        """Should return False when credentials are missing"""
        # Arrange — notifier with no credentials
        notifier = EmailNotifier()
        notifier.smtp_user     = ""
        notifier.smtp_password = ""
        notifier.recipient     = ""

        # Act
        result = notifier.send_alert(high_risk_report, critical_results)

        # Assert
        assert result is False

    def test_returns_false_when_risk_below_threshold(
        self, notifier, low_risk_report, empty_results
    ):
        """Should not send email when risk score is below threshold"""
        # Arrange — risk score 0, no critical events

        # Act
        result = notifier.send_alert(low_risk_report, empty_results)

        # Assert
        assert result is False

    def test_sends_when_critical_event_detected(
        self, notifier, low_risk_report, critical_results
    ):
        """Should send email even with low score if critical event detected"""
        # Arrange — low score but DeleteFlowLogs detected
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Act
            result = notifier.send_alert(low_risk_report, critical_results)

            # Assert — email sent despite low score
            assert result is True
            mock_server.sendmail.assert_called_once()

    def test_sends_when_risk_above_threshold(
        self, notifier, high_risk_report, critical_results
    ):
        """Should send email when risk score exceeds threshold"""
        # Arrange — risk score 75
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Act
            result = notifier.send_alert(high_risk_report, critical_results)

            # Assert
            assert result is True

    def test_returns_false_on_smtp_auth_error(
        self, notifier, high_risk_report, critical_results
    ):
        """Should return False on SMTP authentication failure"""
        import smtplib
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.side_effect = \
                smtplib.SMTPAuthenticationError(535, "Auth failed")

            # Act
            result = notifier.send_alert(high_risk_report, critical_results)

            # Assert
            assert result is False

    def test_returns_false_on_unexpected_error(
        self, notifier, high_risk_report, critical_results
    ):
        """Should return False on any unexpected error — never crash"""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.side_effect = \
                Exception("Network unreachable")

            # Act
            result = notifier.send_alert(high_risk_report, critical_results)

            # Assert
            assert result is False