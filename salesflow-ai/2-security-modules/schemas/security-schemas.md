# 🔐 Security Schemas — Pydantic as a Security Boundary

This document explains how **Pydantic schemas** are used in SalesFlow Lite as a
**primary security control**, not just a validation convenience.

Schemas act as a **hard contract** between external inputs and internal pipelines,
protecting the backend from malformed, malicious, or ambiguous data.

---

## 🧱 Why Pydantic Schemas Are a Security Mechanism

In SalesFlow Lite, **no external payload is trusted by default**.

All inputs entering the Python backend must:
- Match an explicit schema
- Respect strict data types
- Satisfy business-level constraints

Any violation results in an **immediate rejection (HTTP 422)**.

This makes Pydantic schemas a **first line of defense** against:
- Injection attacks
- Mass assignment
- Contract abuse
- Corrupted data propagation across pipelines

---

## 🔍 Core Validation Rules Implemented

### 1️⃣ Strict Typing

Schemas enforce exact data types:
- Numbers (`int`, `float`) for quantities and prices
- Dates and timestamps for temporal fields
- Enums for constrained values (status, categories)

**Security impact**
- Prevents payload confusion (e.g. string instead of number)
- Blocks type-juggling attacks
- Eliminates implicit type coercion

---

### 2️⃣ Required Field Enforcement

Critical fields are marked as **mandatory**:
- Identifiers
- Quantities
- Dates
- References to upstream Java entities

**Security impact**
- Prevents partial or ambiguous payloads
- Ensures pipelines always operate on complete data
- Eliminates hidden defaults injected by attackers

---

### 3️⃣ Business Rule Validation

Schemas enforce domain constraints, for example:
- Quantities must be positive
- Dates must be valid and ordered
- Forecast ranges must be realistic

**Security impact**
- Blocks logically invalid but syntactically correct payloads
- Prevents downstream pipeline corruption
- Reduces attack surface beyond simple syntax checks

---

### 4️⃣ Controlled Payload Shape (Anti Over-Posting)

Schemas explicitly define **allowed fields only**.

Any extra or unexpected field:
- Is rejected
- Never reaches service or data layers

**Security impact**
- Prevents mass assignment attacks
- Blocks hidden field injection
- Ensures backend behavior remains deterministic

---

## 📦 API Contract Enforcement (422 as a Security Signal)

When schema validation fails:
- The request is rejected with **HTTP 422 Unprocessable Entity**
- The pipeline execution is **never started**

Schemas are defined for:
- Analytics requests
- Machine Learning prediction inputs
- Report generation payloads
- Excel commit operations

**Security principle**
> *Fail fast at the boundary, never deep in the pipeline.*

---

## 📊 Excel Pipeline — Secure Data Ingestion

### Validation Flow
```

Excel upload
→ schema validation (excel_schemas.py)
→ preview generation
→ explicit commit
→ persistence via Java API

```

### Security Guarantees
- Excel structure is validated before processing
- Column types and required fields are enforced
- Invalid rows never reach the persistence layer

**Threats mitigated**
- Malicious Excel uploads
- Formula or structure abuse
- Corrupted bulk data injection

---

## 🤖 ML Pipeline — Secure Model Inputs

### Validation Flow
```

ML request
→ schema validation (ML request schemas)
→ preprocessing
→ model execution
→ forecast / anomaly output

```

### Security Guarantees
- Model inputs are strictly constrained
- Feature sets are explicitly defined
- Unexpected parameters are rejected

**Security impact**
- Prevents model abuse via crafted payloads
- Protects ML logic from undefined behavior
- Ensures reproducible and explainable outputs

---

## 🔗 Schema Validation Across Pipelines

| Pipeline | Role of Schemas |
|--------|-----------------|
| Sales Analytics | Enforce metric input integrity |
| Stock Analytics | Prevent malformed inventory data |
| Excel Import | Secure bulk ingestion |
| ML Pipeline | Protect model inputs |
| Reports | Guarantee consistent generation payloads |

Schemas ensure **security consistency across all automation pipelines**.

---

## 🧠 Security Design Philosophy

Schemas in SalesFlow Lite follow three rules:

1. **Explicit** — every accepted field is documented  
2. **Strict** — invalid data is rejected immediately  
3. **Composable** — schemas evolve with pipelines without weakening security  

> **If data is not valid, it does not exist.**

---

## 🎯 Key Security Skills Demonstrated

- Input validation as a security boundary
- Anti-injection via strict schema enforcement
- Contract-driven API design
- Secure data ingestion pipelines
- ML input hardening

---

> **In SalesFlow Lite, Pydantic schemas are not optional validation helpers —
> they are a core security control.**
```

