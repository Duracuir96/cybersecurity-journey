# 🧠 ML-Assisted Automation (Decision Support)

This module documents how **Machine Learning is used as an automation enabler** in SalesFlow Lite — not as an isolated data science experiment.

The ML layer is integrated into backend workflows to:

* automate forecasting,
* detect abnormal behavior,
* trigger operational alerts,
  while **preserving human control**.

---

## 📌 Scope of ML Automation

* Sales forecasting
* Anomaly detection
* Severity-based alerting
* Context-aware enrichment
* Performance optimization via caching

🚫 No autonomous remediation
✅ Human-in-the-loop by design

---

## 🧩 Automation Philosophy

SalesFlow ML automation follows three core principles:

1. **ML augments workflows**, it does not replace decisions
2. **All ML outputs are explainable**
3. **Automation stops at notification**, not execution

This makes the system safe for real business usage.

---

## 🔄 ML Automation Architecture

```
Data ingestion (Java APIs)
   ↓
ML preprocessing
   ↓
Model training / inference
   ↓
Forecast & anomaly signals
   ↓
Severity classification
   ↓
Automation policy
   ↓
Notification (email / logs)
```

---

## 📈 Forecast Automation

📍 **File:** `src/services/ml_service.py`

Forecasting is fully automated and executed on demand via API calls or reused by other pipelines.

```python
model = LinearRegression().fit(X, y)
preds = model.predict(future_idx).clip(0).round(2).tolist()
```

Automated outputs include:

* future dates
* predicted quantities
* trend classification

```python
trend = (
    "upward" if preds[-1] > preds[0]
    else "downward" if preds[-1] < preds[0]
    else "stable"
)
```

### Automation Value

* Eliminates manual forecasting
* Provides immediate business insights
* Deterministic and reproducible results

---

## 🚨 Anomaly Detection Automation

📍 **File:** `src/services/ml_service.py`

Anomalies are detected automatically using Z-score analysis.

```python
z = (values - mean) / std

if abs(score) >= 3:
    anomalies.append({...})
```

Each anomaly contains:

* severity level
* statistical score
* business explanation

✔ Transparent
✔ Explainable
✔ Audit-friendly

---

## 🔔 Severity-Based Alert Automation

📍 **File:** `src/services/anomaly_alert_service.py`

ML outputs are passed through a **policy gate** before triggering alerts.

```python
if severity not in ("high", "medium"):
    return
```

```python
send_anomaly_email(payload)
```

Automation behavior:

* LOW → ignored
* MEDIUM → flagged
* HIGH → email alert

🚫 No auto-remediation
✅ Notification-only automation

---

## 📧 Email Notification Automation

📍 **File:** `src/services/email_service.py`

```python
with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.send_message(msg)
```

✔ Fully automated delivery
✔ Environment-driven configuration
✔ Safe operational alerting

---

## 🎨 Context-Aware Automation (Result Enrichment)

📍 **File:** `src/services/ml_enrichment_service.py`

ML results are automatically enriched with product metadata.

```python
if product:
    base["product"] = {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
    }
```

✔ ML logic unchanged
✔ UI-ready output
✔ Separation of concerns preserved

---

## ⚡ Performance Automation (Caching)

📍 **File:** `src/data/cache_manager.py`

```python
cached = get_cache(cache_key)
if cached:
    return json.loads(cached)
```

✔ Avoids recomputation
✔ Reduces latency
✔ Protects upstream services

---

## 🛡️ Safety & Governance Controls

| Control            | Implementation        |
| ------------------ | --------------------- |
| DEV isolation      | `DEV_MODE` bypass     |
| Explainability     | Z-score + explanation |
| Scope control      | GLOBAL / PRODUCT      |
| No remediation     | Alert-only automation |
| Schema enforcement | Pydantic DTOs         |

---

## 🎯 Why This Is ML Automation (Not Just ML)

This module demonstrates:

* ML embedded in backend automation
* Operationally safe ML usage
* Decision support, not blind execution
* Clear boundaries between ML, business logic, and Ops

It reflects **production ML engineering**, not experimental data science.

---

## 🏁 Automation Classification

**Automation Level:**
⚠️ Intelligent automation (decision support)
✅ Human-in-the-loop
❌ Autonomous remediation (intentionally excluded)

---

## ✅ Key Takeaway

> In SalesFlow Lite, ML is not a feature — it is an automation accelerator.

---

