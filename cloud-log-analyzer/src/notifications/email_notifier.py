# src/notifications/email_notifier.py

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailNotifier:
    """
    Sends security alert emails based on detection results.
    Only fires when the risk score exceeds the threshold or critical events
    are detected.

    Layer 7 — notification only. No analysis, no detection, no UI.
    """

    # Risk score at or above this value triggers an email.
    DEFAULT_RISK_THRESHOLD = 25

    # ── Design tokens (mirror the dashboard spec) ─────────────
    _BG        = "#0F1117"   # page
    _PANEL     = "#151821"   # cards
    _BORDER    = "#1F2430"   # card border
    _FG        = "#E6E9EF"   # primary text
    _FG2       = "#B4BCCC"   # secondary text
    _LABEL     = "#6E7688"   # uppercase labels
    _MUTE      = "#5C6474"   # muted text
    _ACCENT    = "#00D4AA"   # accent
    _CRITICAL  = "#F04452"
    _HIGH      = "#FF8A3D"
    _MEDIUM    = "#F5C842"
    _LOW       = "#00D4AA"
    _MONO      = "'JetBrains Mono', 'Courier New', monospace"
    _SANS      = "Inter, Arial, sans-serif"

    def __init__(self):
        """Loads SMTP credentials from environment variables."""
        self.smtp_host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port     = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user     = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender        = os.getenv("ALERT_SENDER", self.smtp_user)
        self.recipient     = os.getenv("ALERT_RECIPIENT", "")

    def _is_configured(self):
        """True only when all required SMTP credentials are set."""
        return all([self.smtp_user, self.smtp_password, self.recipient])

    # ── Severity helpers ──────────────────────────────────────

    def _severity(self, score, has_critical):
        """
        Returns (label, colour) describing WHY the alert fired.
        A critical event always wins over the numeric score, so an alert
        is never labelled LOW.
        """
        if has_critical:
            return "CRITICAL EVENT", self._CRITICAL
        if score >= 75:
            return "CRITICAL", self._CRITICAL
        if score >= 50:
            return "HIGH", self._HIGH
        return "MEDIUM", self._MEDIUM

    def _risk_colour(self, score):
        """Colour for the numeric score block (factual, not the alert reason)."""
        if score >= 75:
            return self._CRITICAL
        if score >= 50:
            return self._HIGH
        if score >= 25:
            return self._MEDIUM
        return self._LOW

    def _build_subject(self, report, has_critical=False):
        """Builds the subject line from the reason the alert fired."""
        score = report.get("risk_score", 0)
        label, _ = self._severity(score, has_critical)
        return (
            f"[Cloud Log Analyzer] {label} — "
            f"Risk Score {score}/100 — "
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
        )

    # ── HTML fragments ────────────────────────────────────────

    def _dot(self, colour):
        """A small coloured status dot (replaces emoji)."""
        return (
            f"<span style='display:inline-block;width:8px;height:8px;"
            f"border-radius:50%;background:{colour};"
            f"vertical-align:middle;margin-right:8px;'></span>"
        )

    def _label(self, text):
        return (
            f"<p style='color:{self._LABEL};font-size:11px;font-weight:600;"
            f"text-transform:uppercase;letter-spacing:0.14em;"
            f"margin:0 0 14px 0;'>{text}</p>"
        )

    def _card_open(self, border=None):
        border = border or self._BORDER
        return (
            f"<div style='background:{self._PANEL};border:1px solid {border};"
            f"border-radius:6px;padding:22px;margin-bottom:14px;'>"
        )

    def _th(self, text, align="left"):
        return (
            f"<th style='padding:9px 12px;text-align:{align};color:{self._LABEL};"
            f"font-size:10px;font-weight:600;text-transform:uppercase;"
            f"letter-spacing:0.1em;border-bottom:1px solid {self._BORDER};'>"
            f"{text}</th>"
        )

    def _td(self, text, colour=None, mono=False, align="left", bold=False):
        colour = colour or self._FG2
        font = f"font-family:{self._MONO};" if mono else ""
        weight = "font-weight:700;" if bold else ""
        return (
            f"<td style='padding:9px 12px;border-bottom:1px solid {self._BORDER};"
            f"color:{colour};font-size:12px;{font}{weight}text-align:{align};'>"
            f"{text}</td>"
        )

    def _build_body(self, report, results, has_critical=False):
        """Builds a structured HTML email body matching the dashboard design."""
        score        = report.get("risk_score", 0)
        total_events = report.get("total_events", 0)
        unique_ips   = report.get("unique_ips", 0)
        summary      = report.get("detection_summary")
        entities     = report.get("cross_detection_entities")

        sev_label, sev_colour = self._severity(score, has_critical)
        risk_colour = self._risk_colour(score)

        # Active alerts rows
        alerts_rows = ""
        if summary is not None and not summary.empty:
            active = summary[summary["status"] == "ALERT"]
            for _, row in active.iterrows():
                alerts_rows += (
                    "<tr>"
                    + self._td(row["detection"], colour=self._FG, mono=True)
                    + self._td(str(row["count"]), colour=self._CRITICAL,
                               align="center", bold=True)
                    + self._td("ALERT", colour=self._CRITICAL, align="center")
                    + "</tr>"
                )

        alerts_block = ""
        if alerts_rows:
            alerts_block = (
                self._card_open()
                + self._label("Active alerts")
                + "<table style='width:100%;border-collapse:collapse;'>"
                + "<tr>"
                + self._th("Detection")
                + self._th("Count", "center")
                + self._th("Status", "center")
                + "</tr>"
                + alerts_rows
                + "</table></div>"
            )

        # Cross-detection entities rows
        entities_rows = ""
        if entities is not None and not entities.empty:
            for _, row in entities.iterrows():
                entities_rows += (
                    "<tr>"
                    + self._td(row["entity"], colour=self._FG, mono=True)
                    + self._td(str(row["detection_count"]),
                               colour=self._CRITICAL, align="center", bold=True)
                    + self._td(row["detections"], colour=self._MUTE)
                    + "</tr>"
                )

        entities_block = ""
        if entities_rows:
            entities_block = (
                self._card_open(border=self._CRITICAL)
                + self._label("High priority — cross-detection entities")
                + f"<p style='color:{self._FG2};font-size:12px;line-height:1.55;"
                  f"margin:0 0 14px 0;'>These entities were flagged by multiple "
                  f"independent detectors and warrant the highest investigation "
                  f"priority.</p>"
                + "<table style='width:100%;border-collapse:collapse;'>"
                + "<tr>"
                + self._th("Entity")
                + self._th("Detectors", "center")
                + self._th("Flagged by")
                + "</tr>"
                + entities_rows
                + "</table></div>"
            )

        return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:{self._BG};font-family:{self._SANS};">
<div style="max-width:640px;margin:0 auto;padding:32px 16px;">

<div style="{self._card_open()[5:-1]}">
<p style="color:{self._ACCENT};font-family:{self._MONO};font-size:16px;
font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 6px 0;">
{self._dot(sev_colour)}Cloud Log Analyzer</p>
<p style="color:{self._MUTE};font-size:12px;margin:0;">
Security Alert &nbsp;|&nbsp; {sev_label} &nbsp;|&nbsp;
{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
</div>

<div style="background:{self._PANEL};border:1px solid {risk_colour};
border-radius:6px;padding:24px;margin-bottom:14px;text-align:center;">
{self._label('Global risk score')}
<p style="color:{risk_colour};font-family:{self._MONO};font-size:46px;
font-weight:700;margin:0;">{score}<span style="font-size:20px;color:{self._MUTE};">/100</span></p>
<p style="color:{self._MUTE};font-size:12px;margin:10px 0 0 0;font-family:{self._MONO};">
{total_events:,} events analyzed &nbsp;|&nbsp; {unique_ips} unique IPs</p>
</div>

{alerts_block}
{entities_block}

<div style="background:{self._PANEL};border:1px solid {self._BORDER};
border-radius:6px;padding:16px;text-align:center;">
<p style="color:{self._MUTE};font-size:11px;margin:0;">
Cloud Log Analyzer v1.0 &nbsp;|&nbsp; Cloud Security Data Engineer &nbsp;|&nbsp; Voldi BOKANGA</p>
</div>

</div>
</body>
</html>"""

    def send_alert(self, report, results):
        """
        Sends a security alert email if the risk score exceeds the threshold
        or critical events are detected.
        Output : bool — True if email sent, False otherwise.
        """
        if not self._is_configured():
            print("[WARN] EmailNotifier not configured — set SMTP env vars")
            return False

        score           = report.get("risk_score", 0)
        critical_events = results.get("critical_events", None)
        has_critical    = (
            critical_events is not None and not critical_events.empty
        )

        if score < self.DEFAULT_RISK_THRESHOLD and not has_critical:
            print(f"[INFO] Risk score {score}/100 below threshold — no alert sent")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = self._build_subject(report, has_critical=has_critical)
            msg["From"]    = self.sender
            msg["To"]      = self.recipient

            html_body = self._build_body(report, results, has_critical=has_critical)
            msg.attach(MIMEText(html_body, "html"))

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