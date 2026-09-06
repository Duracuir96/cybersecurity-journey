# src/notifications/email_notifier.py

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailNotifier:
    """
    Sends security alert emails based on detection results.

    v2.0 Risk-Based Alerting: the alert fires when at least one ENTITY
    (an IP or a username) crosses the risk floor, or when a critical event
    is detected. The email is a Risk Notable — it names the entities that
    crossed the floor, with their score, so the analyst knows who to chase.

    Layer 7 — notification only. No analysis, no detection, no UI.
    """

    # Risk floor: an entity scoring at or above this triggers an alert.
    DEFAULT_RISK_THRESHOLD = 70

    # ── Design tokens (mirror the dashboard spec) ─────────────
    _BG        = "#0F1117"
    _PANEL     = "#151821"
    _BORDER    = "#1F2430"
    _FG        = "#E6E9EF"
    _FG2       = "#B4BCCC"
    _LABEL     = "#6E7688"
    _MUTE      = "#5C6474"
    _ACCENT    = "#00D4AA"
    _CRITICAL  = "#F04452"
    _HIGH      = "#FF8A3D"
    _MEDIUM    = "#F5C842"
    _LOW       = "#00D4AA"
    _MONO      = "'JetBrains Mono', 'Courier New', monospace"
    _SANS      = "Inter, Arial, sans-serif"

    def __init__(self):
        self.smtp_host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port     = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user     = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender        = os.getenv("ALERT_SENDER", self.smtp_user)
        self.recipient     = os.getenv("ALERT_RECIPIENT", "")

    def _is_configured(self):
        return all([self.smtp_user, self.smtp_password, self.recipient])

    # ── Decision (entity-based, testable without SMTP) ────────

    def _evaluate(self, report, results, force=False):
        """
        Decides whether to alert and which entities crossed the floor.

        Returns (should_send, flagged, has_critical) where `flagged` is a
        {entity: score} dict of entities at or above the risk floor.
        """
        threshold = self.DEFAULT_RISK_THRESHOLD
        entity_scores = report.get("risk_score_by_entity", {}) or {}

        flagged = {e: s for e, s in entity_scores.items() if s >= threshold}

        critical = results.get("critical_events")
        has_critical = critical is not None and not critical.empty

        if force:
            return True, flagged, has_critical

        if entity_scores:
            should_send = bool(flagged) or has_critical
        else:
            # Report predates v2.0 — fall back to the global score.
            should_send = report.get("risk_score", 0) >= threshold or has_critical

        return should_send, flagged, has_critical

    # ── Severity helpers ──────────────────────────────────────

    def _severity(self, score, has_critical):
        if has_critical:
            return "CRITICAL EVENT", self._CRITICAL
        if score >= 75:
            return "CRITICAL", self._CRITICAL
        if score >= 50:
            return "HIGH", self._HIGH
        return "MEDIUM", self._MEDIUM

    def _risk_colour(self, score):
        if score >= 75:
            return self._CRITICAL
        if score >= 50:
            return self._HIGH
        if score >= 25:
            return self._MEDIUM
        return self._LOW

    def _entity_colour(self, score):
        return self._risk_colour(score)

    def _build_subject(self, report, has_critical=False):
        score = report.get("risk_score", 0)
        label, _ = self._severity(score, has_critical)
        return (
            f"[Cloud Log Analyzer] {label} — "
            f"Risk Score {score}/100 — "
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
        )

    # ── HTML fragments ────────────────────────────────────────

    def _dot(self, colour):
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

    def _build_body(self, report, results, has_critical=False, flagged=None):
        score        = report.get("risk_score", 0)
        total_events = report.get("total_events", 0)
        unique_ips   = report.get("unique_ips", 0)
        summary      = report.get("detection_summary")
        flagged      = flagged or {}

        sev_label, sev_colour = self._severity(score, has_critical)
        risk_colour = self._risk_colour(score)

        # Risk Notable — entities that crossed the floor
        notable_rows = ""
        for entity, esc in sorted(flagged.items(), key=lambda kv: kv[1], reverse=True):
            notable_rows += (
                "<tr>"
                + self._td(str(entity), colour=self._FG, mono=True)
                + self._td(f"{int(esc)}/100", colour=self._entity_colour(esc),
                           align="right", bold=True)
                + "</tr>"
            )
        notable_block = ""
        if notable_rows:
            notable_block = (
                self._card_open(border=self._CRITICAL)
                + self._label("Risk notable — entities above the floor "
                              f"({self.DEFAULT_RISK_THRESHOLD})")
                + "<table style='width:100%;border-collapse:collapse;'>"
                + "<tr>" + self._th("Entity") + self._th("Risk", "right") + "</tr>"
                + notable_rows + "</table></div>"
            )

        # Active alerts
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
                + "<tr>" + self._th("Detection") + self._th("Count", "center")
                + self._th("Status", "center") + "</tr>"
                + alerts_rows + "</table></div>"
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

{notable_block}
{alerts_block}

<div style="background:{self._PANEL};border:1px solid {self._BORDER};
border-radius:6px;padding:16px;text-align:center;">
<p style="color:{self._MUTE};font-size:11px;margin:0;">
Cloud Log Analyzer v1.0 &nbsp;|&nbsp; Cloud Security Data Engineer &nbsp;|&nbsp; Voldi BOKANGA</p>
</div>

</div>
</body>
</html>"""

    def send_alert(self, report, results, force=False):
        """
        Sends a Risk Notable email when an entity crosses the risk floor,
        when a critical event is detected, or when force=True (manual send).

        Input  : report dict (Layer 5) + results dict (Layer 4)
        Output : bool — True if email sent, False otherwise
        """
        if not self._is_configured():
            print("[WARN] EmailNotifier not configured — set SMTP env vars")
            return False

        should_send, flagged, has_critical = self._evaluate(report, results, force)

        if not should_send:
            score = report.get("risk_score", 0)
            print(f"[INFO] No entity above floor "
                  f"{self.DEFAULT_RISK_THRESHOLD} (top score {score}) — no alert")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = self._build_subject(report, has_critical=has_critical)
            msg["From"]    = self.sender
            msg["To"]      = self.recipient

            html_body = self._build_body(report, results,
                                         has_critical=has_critical, flagged=flagged)
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender, self.recipient, msg.as_string())

            n = len(flagged)
            print(f"[INFO] Alert sent to {self.recipient} "
                  f"— {n} entity(ies) above floor")
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