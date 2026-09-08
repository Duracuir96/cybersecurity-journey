<!--
  Place this at: cloud-log-analyzer/README.md
  Before committing, replace every TODO marker:
    1. Screenshot URLs (upload images to docs/ in the repo, then link them)
    2. The exact test count (run: pytest --collect-only -q | wc -l)
    3. The CI badge workflow filename (see .github/workflows/*.yml)
  SECURITY: never commit your real .env. Commit .env.example instead.
  On the Gmail app-password screenshot, blur the 16-character code.
-->

<p align="center">
<img width="862" height="263" alt="image" src="https://github.com/user-attachments/assets/38cd4e17-c96f-4b26-a2b7-3dfebadd08ab" />

</p>

<h1 align="center">Cloud Log Analyzer</h1>

<p align="center">
  A mini-SIEM for AWS CloudTrail — 11 MITRE-mapped detections,
  entity-based Risk-Based Alerting, and a real-time dashboard.
</p>

<p align="center">
  <a href="https://github.com/Duracuir96/cybersecurity-journey/actions">
    <img src="https://github.com/Duracuir96/cybersecurity-journey/actions/workflows/ci.yml/badge.svg" alt="CI"/></a>
  <img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python"/>
  <img src="https://img.shields.io/badge/dashboard-Streamlit-ff4b4b" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/detections-11-00D4AA" alt="Detections"/>
  <img src="https://img.shields.io/badge/MITRE-ATT%26CK-red" alt="MITRE ATT&CK"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License"/>
</p>

---

## What it is

**Cloud Log Analyzer** ingests AWS CloudTrail logs, runs 11 heuristic detections
mapped to MITRE ATT&CK, scores risk **per entity** (the way a real SIEM does),
and surfaces everything in a dark, real-time Streamlit dashboard — with email
alerting and per-detection response playbooks.

It is built as a 7-layer pipeline, fully unit-tested, and designed around clean
single-responsibility modules.

<p align="center">
  <img src="docs/dashboard.png" alt="Dashboard preview" width="900"/>
</p>

---

## Features

- **Log analysis** — collects and parses AWS CloudTrail events (local file or live `lookup_events`).
- **11 detections** — brute force, IAM privilege escalation, credential abuse, log tampering, S3 exfiltration, and more — each mapped to a MITRE ATT&CK technique.
- **Risk-Based Alerting** — risk is accumulated **per entity** (IP / user); the global score reflects the single most dangerous actor.
- **Interactive dashboard** — hand-built SVG charts (log-scaled bars, donut, timeline), a cross-detection entities table, and per-detection drill-downs. Dark design system.
- **Email alerting** — an entity-aware *Risk Notable*: fires when an entity crosses the risk floor, and names the offending entities with their score.
- **Response playbooks** — one versioned `.md` runbook per detection (MITRE reference, investigation steps, AWS CLI remediation, common false positives), rendered inside the app.

---

## Detections (MITRE ATT&CK)

| Detection | MITRE technique | Default severity |
| --- | --- | --- |
| Brute Force Console Login | T1110 — Brute Force | High |
| IAM Privilege Escalation | T1098 — Account Manipulation | Critical |
| Access Key Usage Anomaly | T1078 — Valid Accounts | High |
| CloudTrail Logging Disabled | T1562 — Impair Defenses | Critical |
| S3 Mass Object Download | T1530 — Data from Cloud Storage | High |
| Unusual EC2 Instance Launch | T1578 — Modify Cloud Compute | High |
| Lambda Function Tampering | T1648 — Serverless Execution | High |
| Network Data Exfiltration | T1041 — Exfiltration Over C2 | High |
| Role Chaining | T1548 — Abuse Elevation Control | Medium |
| IAM Enumeration | T1087 — Account Discovery | Medium |
| Unauthorized API Calls | T1046 — Network Service Discovery | Medium |

---

## Risk scoring — from binary to Risk-Based Alerting

Most log tools score risk in a **binary** way: a detection either fired or it
didn't. That means **1 failed login and 1000 failed logins get the same score** —
the intensity of an attack is invisible. Cloud Log Analyzer fixes this in two steps.

**Volumetric scoring** — each detection contributes a base weight *plus* a bonus
that scales with intensity, capped per detection:

```
failed_logins:   3 attempts -> 7    50 attempts -> 17    100+ -> 21 (capped)
```

**Entity-based scoring** — risk is accumulated **per actor** (IP or username),
not per detection type. The global score is the score of the most dangerous entity:

```
attacker        -> 42/100   (credential_abuse + iam_enumeration)
185.220.101.44  -> 33/100   (failed_logins + api_calls_by_ip)
8.8.8.8         ->  7/100   (noise)
Global risk score = 42
```

This mirrors how Splunk RBA and Microsoft Sentinel reason: an incident is tied to
an **actor**, so the analyst knows *who* to investigate — not just that "risk is high".

<p align="center">
  <img src="docs/cross-detection.png" alt="Cross-detection entities with per-entity risk" width="900"/>
</p>

---

## Architecture — 7 layers

| Layer | Role | Status |
| --- | --- | --- |
| 1 — Data collection | `aws_connector` — local JSON or live CloudTrail (`lookup_events`) | Done |
| 2 — Parsing & normalization | flatten raw events into a tabular structure | Done |
| 3 — Data validation | schema checks, cleaning, required fields | Done |
| 4 — Detection (heuristics) | 11 MITRE-mapped detectors | Done |
| 5 — Statistics + Risk-Based Alerting | traffic stats + **volumetric & entity-based risk scoring** | Done |
| 6 — Interactive dashboard | Streamlit + SVG charts, dark design system | Done |
| 7 — Notification | entity-aware email *Risk Notable* | Done |
| + | Response playbooks (11 `.md`) | Done |
| + | Unit test suite | Done |

---

## Tech stack

- **Language:** Python 3.8+
- **Cloud:** AWS (CloudTrail, IAM, S3) via **boto3**
- **Data processing:** pandas
- **Dashboard:** Streamlit (custom SVG/HTML, no chart lib)
- **Alerting:** smtplib (HTML email)

---

## Quick start

**Prerequisites**

- Python 3.8+
- An AWS account with CloudTrail enabled (or the bundled sample file)
- AWS CLI configured with read permissions for CloudTrail

**Install & run**

```bash
git clone https://github.com/Duracuir96/cybersecurity-journey.git
cd cybersecurity-journey/cloud-log-analyzer

pip install -r requirements.txt

cp .env.example .env      # add SMTP + AWS settings

streamlit run src/dashboard/app.py
```

Then click **LOAD AND ANALYZE** in the sidebar. Start with the bundled local
sample (`data/sample_cloudtrail.json`) if you don't want to hit AWS yet.

---

## AWS setup

<!-- TODO: paste your setup screenshots here (IAM user, CloudTrail, S3 bucket) -->

1. Create an IAM user with programmatic access.
  <img width="1912" height="760" alt="image" src="https://github.com/user-attachments/assets/161f8ad3-9fb1-426c-aa1c-4daada4279b9" />


     
2. Grant read permissions for CloudTrail.
   
<img width="1867" height="747" alt="image" src="https://github.com/user-attachments/assets/6dd44e6c-cb69-45ea-b94c-e628379c3b13" />

3. Create an S3 bucket to store CloudTrail logs.
   <img width="1880" height="755" alt="image" src="https://github.com/user-attachments/assets/9a59150d-fd27-43d0-bb09-1a3ea8b6cb47" />

4. Enable a CloudTrail trail (region: `us-east-1`).
  <img width="1906" height="746" alt="image" src="https://github.com/user-attachments/assets/8b3b41af-45e3-455b-bc0a-ce0389942b67" />





---

## Email alerting setup (Layer 7)

The notifier sends an HTML *Risk Notable* over SMTP. With Gmail you **cannot** use
your normal password — you must generate a dedicated **app password**.

1. Enable **2-Step Verification** on your Google account.
2. Go to **Google Account → Security → App passwords** and generate a new one
   (16 characters). This becomes `SMTP_PASSWORD`.
3. Put your SMTP settings in `.env` (never commit this file — commit `.env.example`):

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-16-char-app-password
ALERT_SENDER=you@gmail.com
ALERT_RECIPIENT=soc@yourteam.com
```

4. In the dashboard sidebar, set a recipient, choose the **risk floor**, and either
   enable *auto-send* or use the **Send Alert Email** button.

> **Security note:** the app password is a secret. On any screenshot of the Google
> app-password screen, **blur the 16-character code**, and keep `.env` out of Git.

<!-- TODO: add the received Risk Notable email screenshot (mobile) -->
<p align="center">
  <img src="docs/alert-email.png" alt="Risk Notable email received on mobile" width="380"/>
</p>

---

## Tests

```bash
pytest src/tests/ -v
```

<!-- TODO: replace N with the real count: pytest --collect-only -q | wc -l -->
The suite covers general statistics, all detectors, the volumetric and
entity-based risk scoring, and the full report (**N unit tests**).

---

## Screenshots

- Full dashboard (dark)
- Brute Force detection tab (rule logic + matched events)
- Cross-detection entities table (RISK column)
- Risk Notable email received on mobile

---

## Roadmap

- [ ] **v2.5 — velocity**: detections clustered in a short time window raise the score.
- [ ] **v3.0 — ML anomaly detection** (Isolation Forest on historical baselines).
- [ ] `NextToken` pagination to go beyond the 50-event `lookup_events` cap.
- [ ] Multi-region ingestion.
- [ ] Slack / Teams alerting.
- [ ] Containerized deployment (Docker).

---

## License

MIT © Voldi BOKANGA
