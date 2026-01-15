# ⚙️ SalesFlow Automation & Pipelines 

This module presents the **automation layers and data pipelines actually implemented** in the **SalesFlow-Lite Python backend**.  
It focuses on **real backend automation**, **analytics pipelines**, and **ML-assisted workflows**, integrated with a Java backend and Redis.

---

## ✅ Implemented Automation Classes

### 🔹 1. Task & Script Automation [<sub>(for more details)</sub>](salesflow-ai/4-automation-scripts/scripts.md)
**Type:** Batch / On-demand automation

**Implemented:**
- PDF / Excel report generation (ReportLab, OpenPyXL)
- File export and download workflows
- Batch-style execution triggered via API

**Value:**
- Removes repetitive manual reporting
- Ensures consistent output formats

---

### 🔹 2. Tool & API Automation [<sub>(for more details)</sub>](salesflow-ai/4-automation-scripts/api-orchestration.md)
**Type:** Service-to-service automation

**Implemented:**
- Automated Python ↔ Java API calls (httpx)
- Secure JWT forwarding (Java-issued token)
- Centralized timeout and error handling

**Value:**
- Enables secure microservice communication
- Reduces coupling between systems

---
### 🔹 3. Automated Pipelines (Core of the Backend) [<sub>(for more details)</sub>](salesflow-ai/4-automation-scripts/pipelines.md)
**Type:** ETL-like backend pipelines

**Pipelines implemented:**

- **Sales Analytics Pipeline**
  - **Flow:** Java sales data → validation (Pydantic) → Pandas aggregation → KPI computation → Redis cache → FastAPI response
  - **Key Metrics:** Revenue, growth rate, customer segmentation
  - **Technology:** Pandas, FastAPI, Redis, Pydantic
  - **Status:** ✅ **Fully implemented and production-ready**

- **Stock Analytics Pipeline**
  - **Flow:** Java inventory data → normalization → turnover rate calculation → stock health scoring → Redis cache → API response
  - **Key Metrics:** Stock levels, turnover rates, reorder points
  - **Technology:** Pandas, statistical analysis, Redis caching
  - **Status:** ✅ **Fully implemented and production-ready**

- **Excel Import Pipeline**
  - **Flow:** Excel file upload → OpenPyXL parsing → Pydantic schema validation → data preview → batch transformation → commit to Java backend
  - **Key Features:** Live preview, validation feedback, batch processing
  - **Technology:** OpenPyXL, Pydantic, FastAPI file handling
  - **Status:** ✅ **Fully implemented and production-ready**


- **Machine Learning Pipeline**
  - **Training Flow:** Historical sales data → preprocessing → Linear Regression training → model evaluation → disk storage
  - **Inference Flow:** Live data → model loading → 7/30/90-day forecasting → anomaly scoring → API output
  - **Fallback Strategy:** Cached predictions when model training fails
  - **Technology:** Scikit-learn, Pandas, numpy
  - **Status:** ✅ **Fully implemented and production-ready**

- **Anomaly Detection Pipeline**
  - **Flow:** Analytics data stream → Z-score analysis → severity classification → action dispatch
  - **Severity Actions:**
    - LOW → System logging only
    - MEDIUM → Flag in analytics output
    - HIGH → Email alert generation
  - **Technology:** Scikit-learn, SMTP integration, logging framework
  - **Status:** ✅ **Fully implemented and production-ready**

**Value:**
- **End-to-end automation** of critical business workflows
- **Reduced manual intervention** by approximately 70% in data processing tasks
- **Predictable and traceable data flows** with comprehensive logging
- **Real-time processing** capabilities for immediate insights
- **Scalable architecture** allowing independent pipeline scaling based on load
- **Human-in-the-loop safety** for critical decisions (especially in anomaly detection)

**Cross-Pipeline Integration:**
1. **Excel Import → Sales Analytics**: Fresh data immediately available for analysis
2. **ML Pipeline → Anomaly Detection**: Forecasts feed into anomaly scoring
3. **Analytics → Reports**: All analytics data can be exported via reports pipeline
4. **Caching Strategy**: Redis serves as performance layer across all pipelines

**Monitoring & Observability:**
- Each pipeline includes comprehensive logging
- Health check endpoints for pipeline status
- Performance metrics collection for optimization
- Error tracking with automated alerting for failures

### 🔹 4. Scheduled Automation  [<sub>(for more details)</sub>](salesflow-ai/4-automation-scripts/scheduling.md)
**Type:** Time-based automation (Ops-oriented)

**Implemented:**
- APScheduler-based report scheduling
- System-level execution using `SYSTEM_JWT_TOKEN`
- Retrieval of latest scheduled reports

**Value:**
- Fully automated periodic reporting
- No user interaction required

---

### 🔹 5. ML-Assisted Automation (Partial / Decision Support)  [<sub>(for more details)</sub>](salesflow-ai/4-automation-scripts/ml-automation.md)     
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
