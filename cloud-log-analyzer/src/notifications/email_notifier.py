# src/notifications/email_notifier.py

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailNotifier:
    """
    Sends security alert emails based on detection results.
    Only fires when risk score exceeds threshold or critical events detected.

    Layer 7 — notification only. No analysis, no detection, no UI.
    """

    # Risk score above this value triggers an email
    DEFAULT_RISK_THRESHOLD = 25

    def __init__(self):
        """
        Loads SMTP credentials from environment variables.
        Never hardcode credentials in source code.
        """
        self.smtp_host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port     = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user     = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender        = os.getenv("ALERT_SENDER", self.smtp_user)
        self.recipient     = os.getenv("ALERT_RECIPIENT", "")

    def _is_configured(self):
        """
        Checks that all required SMTP credentials are set.
        Returns False if any credential is missing — prevents silent failures.
        """
        return all([
            self.smtp_user,
            self.smtp_password,
            self.recipient
        ])

    def _build_subject(self, report):
        """
        Builds email subject based on risk score severity.

        Input  : report dict from StatisticsEngine
        Output : subject string
        """
        score = report.get("risk_score", 0)

        if score >= 75:
            severity = "🔴 CRITICAL"
        elif score >= 50:
            severity = "🟠 HIGH"
        elif score >= 25:
            severity = "🟡 MEDIUM"
        else:
            severity = "🟢 LOW"

        return (
            f"[Cloud Log Analyzer] {severity} — "
            f"Risk Score {score}/100 — "
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
        )

    def _build_body(self, report, results):
        """
        Builds a structured HTML email body.

        Input  : report dict (Layer 5) + results dict (Layer 4)
        Output : HTML string
        """
        score        = report.get("risk_score", 0)
        total_events = report.get("total_events", 0)
        unique_ips   = report.get("unique_ips", 0)
        summary      = report.get("detection_summary")
        entities     = report.get("cross_detection_entities")

        # Risk color
        if score >= 75:
            risk_color = "#EF4444"
        elif score >= 50:
            risk_color = "#F97316"
        elif score >= 25:
            risk_color = "#EAB308"
        else:
            risk_color = "#22C55E"

        # Build active alerts section
        alerts_html = ""
        if summary is not None and not summary.empty:
            active = summary[summary["status"] == "ALERT"]
            for _, row in active.iterrows():
                alerts_html += f"""
                <tr>
                    <td style='padding:8px 12px;border-bottom:1px solid #374151;
                    font-family:Courier New;font-size:13px;color:#F9FAFB;'>
                    ⚠ {row['detection']}</td>
                    <td style='padding:8px 12px;border-bottom:1px solid #374151;
                    color:#EF4444;font-weight:bold;text-align:center;'>
                    {row['count']}</td>
                    <td style='padding:8px 12px;border-bottom:1px solid #374151;
                    color:#EF4444;text-align:center;font-size:12px;'>
                    ALERT</td>
                </tr>
                """

        # Build cross-detection entities section
        entities_html = ""
        if entities is not None and not entities.empty:
            for _, row in entities.iterrows():
                entities_html += f"""
                <tr>
                    <td style='padding:8px 12px;border-bottom:1px solid #374151;
                    font-family:Courier New;font-size:13px;color:#F9FAFB;'>
                    {row['entity']}</td>
                    <td style='padding:8px 12px;border-bottom:1px solid #374151;
                    color:#EF4444;font-weight:bold;text-align:center;'>
                    {row['detection_count']}</td>
                    <td style='padding:8px 12px;border-bottom:1px solid #374151;
                    color:#9CA3AF;font-size:11px;'>
                    {row['detections']}</td>
                </tr>
                """

        return f"""
        <!DOCTYPE html>
        <html>
        <body style='margin:0;padding:0;background:#0A0E1A;font-family:Arial,sans-serif;'>

        <div style='max-width:640px;margin:0 auto;padding:32px 16px;'>

            <!-- Header -->
            <div style='background:#111827;border:1px solid #374151;
            border-radius:8px;padding:24px;margin-bottom:16px;'>

                <p style='color:#00D4AA;font-family:Courier New;
                font-size:18px;font-weight:700;letter-spacing:0.1em;
                text-transform:uppercase;margin:0 0 4px 0;'>
                🔐 Cloud Log Analyzer
                </p>

                <p style='color:#9CA3AF;font-size:12px;margin:0;'>
                Security Alert — {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                </p>
            </div>

            <!-- Risk Score -->
            <div style='background:#111827;border:1px solid {risk_color};
            border-radius:8px;padding:24px;margin-bottom:16px;
            text-align:center;'>

                <p style='color:#9CA3AF;font-size:11px;text-transform:uppercase;
                letter-spacing:0.15em;margin:0 0 8px 0;'>GLOBAL RISK SCORE</p>

                <p style='color:{risk_color};font-family:Courier New;
                font-size:48px;font-weight:700;margin:0;'>{score}/100</p>

                <p style='color:#9CA3AF;font-size:12px;margin:8px 0 0 0;'>
                {total_events:,} events analyzed &nbsp;|&nbsp;
                {unique_ips} unique IPs
                </p>
            </div>

            <!-- Active Alerts -->
            {'<div style="background:#111827;border:1px solid #374151;border-radius:8px;padding:24px;margin-bottom:16px;"><p style="color:#9CA3AF;font-size:11px;text-transform:uppercase;letter-spacing:0.15em;margin:0 0 16px 0;">ACTIVE ALERTS</p><table style="width:100%;border-collapse:collapse;"><tr style="background:#1F2937;"><th style="padding:8px 12px;text-align:left;color:#9CA3AF;font-size:11px;text-transform:uppercase;">Detection</th><th style="padding:8px 12px;text-align:center;color:#9CA3AF;font-size:11px;text-transform:uppercase;">Count</th><th style="padding:8px 12px;text-align:center;color:#9CA3AF;font-size:11px;text-transform:uppercase;">Status</th></tr>' + alerts_html + '</table></div>'
            if alerts_html else ""}

            <!-- Cross-Detection Entities -->
            {'<div style="background:#111827;border:1px solid #EF4444;border-radius:8px;padding:24px;margin-bottom:16px;"><p style="color:#EF4444;font-size:11px;text-transform:uppercase;letter-spacing:0.15em;margin:0 0 16px 0;">⚠ HIGH PRIORITY — CROSS-DETECTION ENTITIES</p><p style="color:#9CA3AF;font-size:12px;margin:0 0 12px 0;">These entities were flagged by multiple independent detectors — highest investigation priority.</p><table style="width:100%;border-collapse:collapse;"><tr style="background:#1F2937;"><th style="padding:8px 12px;text-align:left;color:#9CA3AF;font-size:11px;text-transform:uppercase;">Entity</th><th style="padding:8px 12px;text-align:center;color:#9CA3AF;font-size:11px;text-transform:uppercase;">Detectors</th><th style="padding:8px 12px;text-align:left;color:#9CA3AF;font-size:11px;text-transform:uppercase;">Flagged By</th></tr>' + entities_html + '</table></div>'
            if entities_html else ""}

            <!-- Footer -->
            <div style='background:#111827;border:1px solid #374151;
            border-radius:8px;padding:16px;text-align:center;'>
                <p style='color:#6B7280;font-size:11px;margin:0;'>
                Cloud Log Analyzer v1.0 &nbsp;|&nbsp;
                Cloud Security Data Engineer &nbsp;|&nbsp;
                Voldi BOKANGA
                </p>
            </div>

        </div>
        </body>
        </html>
        """

    def send_alert(self, report, results):
        """
        Sends a security alert email if risk score exceeds threshold
        or critical events are detected.

        Input  : report dict (Layer 5) + results dict (Layer 4)
        Output : bool — True if email sent, False otherwise
        """
        if not self._is_configured():
            print("[WARN] EmailNotifier not configured — set SMTP env vars")
            return False

        score           = report.get("risk_score", 0)
        critical_events = results.get("critical_events", None)
        has_critical    = (
            critical_events is not None and
            not critical_events.empty
        )

        # Only send if risk is meaningful or critical events detected
        if score < self.DEFAULT_RISK_THRESHOLD and not has_critical:
            print(f"[INFO] Risk score {score}/100 below threshold — no alert sent")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = self._build_subject(report)
            msg["From"]    = self.sender
            msg["To"]      = self.recipient

            # Attach HTML body
            html_body = self._build_body(report, results)
            msg.attach(MIMEText(html_body, "html"))

            # Send via SMTP with TLS
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender, self.recipient, msg.as_string())

            print(f"[INFO] Alert sent to {self.recipient} — Risk Score {score}/100")
            return True

        except smtplib.SMTPAuthenticationError:
            print("[ERROR] SMTP authentication failed — check credentials")
            return False
        except smtplib.SMTPException as e:
            print(f"[ERROR] SMTP error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected error sending email: {e}")
            return False