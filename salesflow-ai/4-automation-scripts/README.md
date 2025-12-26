# ⚙️ SalesFlow Automation & Pipelines 

This module presents the **automation layers and data pipelines actually implemented** in the **SalesFlow-Lite Python backend**.  
It focuses on **real backend automation**, **analytics pipelines**, and **ML-assisted workflows**, integrated with a Java backend and Redis.

---

## ✅ Implemented Automation Classes

### 🔹 1. Task & Script Automation
**Type:** Batch / On-demand automation

**Implemented:**
- PDF / Excel report generation (ReportLab, OpenPyXL)
- File export and download workflows
- Batch-style execution triggered via API

**Value:**
- Removes repetitive manual reporting
- Ensures consistent output formats

---

### 🔹 2. Tool & API Automation
**Type:** Service-to-service automation

**Implemented:**
- Automated Python ↔ Java API calls (httpx)
- Secure JWT forwarding (Java-issued token)
- Centralized timeout and error handling

**Value:**
- Enables secure microservice communication
- Reduces coupling between systems

---

### 🔹 3. Automated Pipelines (Core of the Backend)
**Type:** ETL-like backend pipelines

**Pipelines implemented:**

- **Analytics Pipeline**
  - Java sales data → aggregation → KPI computation → Redis cache → API response

- **Reports Pipeline**
  - Analytics → report generation → async job (`job_id`) → status polling → download

- **Excel Import Pipeline**
  - Upload → schema validation → preview → batch commit to Java

- **ML Pipeline**
  - Historical data → preprocessing → model training/fallback → forecast & anomalies output

**Value:**
- End-to-end automation of business workflows
- Reduced manual intervention
- Predictable and traceable data flows

---

### 🔹 4. Scheduled Automation
**Type:** Time-based automation (Ops-oriented)

**Implemented:**
- APScheduler-based report scheduling
- System-level execution using `SYSTEM_JWT_TOKEN`
- Retrieval of latest scheduled reports

**Value:**
- Fully automated periodic reporting
- No user interaction required

---

### 🔹 5. ML-Assisted Automation (Partial / Decision Support)
**Type:** Intelligent assistance (non-autonomous)

**Implemented:**
- Sales forecasting (Linear Regression / Random Forest + fallback)
- Anomaly detection (Z-score + rule-based classification)
- **Automatic anomaly alert generation** based on severity class:
  - `LOW` → logged for monitoring
  - `MEDIUM` → flagged in analytics output
  - `HIGH` → automatic alert trigger (ready for notification integration)

**Value:**
- Early detection of abnormal business behavior
- Reduced cognitive load for users
- Safe, human-in-the-loop automation (no auto-remediation)

---

## 🧠 Automation Maturity Summary

| Level | Status | Description |
|------|--------|-------------|
| Scripts | ✅ | Batch tasks & exports |
| Tool Automation | ✅ | Secure API orchestration |
| Pipelines | ✅ | Analytics, Reports, Excel, ML |
| Scheduling | ✅ | Periodic automated jobs |
| Intelligent Automation | ⚠️ Partial | ML-based alerts & insights |
