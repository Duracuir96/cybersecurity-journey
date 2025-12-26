# 🔐 SalesFlow Security Modules – Practical DevSecOps for Python APIs

Reusable, production-oriented **security components** implemented in the **SalesFlow-Lite Python backend**.  
This module reflects **real backend security engineering**, aligned with a **Java ↔ Python microservice architecture**.

The focus is on **authentication, input validation, contract enforcement, and operational resilience**, rather than theoretical security features.

---

## 🛠️ Implemented Security Components

### 🔑 `jwt_validator.py` – Unified JWT Validation (Java ↔ Python)

Implements **strict JWT validation** for FastAPI endpoints using tokens **issued by a Java Spring Boot backend**.

**Features:**
- HS256 signature verification (shared secret)
- Issuer validation (`iss = "salesflow-app"`)
- Expiration check (`exp`)
- Secure extraction of user identity and role
- Compatibility with Java-generated JWT payloads

**Security value:**
- Prevents token forgery and replay
- Enforces trust boundaries between services
- Enables secure service-to-service communication

---

### 🔐 `dependencies.py` – Authentication & Authorization Layer

Centralized security dependency injected into protected FastAPI routes.

**Implemented logic:**
- `get_current_user()` security dependency
- Environment-based behavior:
  - `DEV_MODE=true` → controlled authentication bypass
  - `DEV_MODE=false` → strict JWT enforcement
- Role normalization (`role` → `roles[]`)
- Foundation for Role-Based Access Control (RBAC)

**Security principles applied:**
- Single enforcement point
- Explicit trust model
- Environment-aware security posture

---

### 🧱 `schemas.py` / `excel_schemas.py` – Strong Input Validation (Anti-Injection)

All incoming API payloads are validated using **Pydantic schemas**.

**Guarantees:**
- Strict typing (dates, numbers, enums)
- Required field enforcement
- Business rule validation (positive quantities, valid dates)
- Controlled payload structure (prevents over-posting)
- Excel schema validation before processing or persistence

**Threats mitigated:**
- Injection via malformed JSON
- Mass assignment attacks
- Corrupted or malicious Excel uploads

---

### 📦 Payload Contract Enforcement (422 Handling)

A key security aspect of the project is **strict API contract enforcement**.

**Implemented protections:**
- Detection of malformed or unexpected payloads
- Explicit `422 Unprocessable Entity` responses
- Dedicated schemas for:
  - Machine Learning requests
  - Report generation payloads
  - Excel commit payloads

**Prevents:**
- Silent data corruption
- Unauthorized field injection
- Ambiguous backend behavior

---

### 🗂️ Cache Safety & Resilience (`cache_manager.py`)

While primarily performance-oriented, the cache layer also contributes to **operational security**.

**Implemented safeguards:**
- Redis availability checks
- Automatic in-memory fallback when Redis is unavailable
- TTL-based cache expiration
- Controlled cache key naming

**Security impact:**
- Prevents denial-of-service caused by Redis outages
- Avoids uncontrolled or stale data exposure

---

## 📡 Operational Security Practices

### 🔍 Fail-Fast Error Handling
- Explicit handling of:
  - Invalid or expired JWTs
  - Java backend timeouts
  - Redis connection failures
- No silent degradation or hidden failures

---

### 🧪 Controlled Development Mode

Authentication bypass in development is:
- Explicit
- Environment-bound
- Disabled by default in production

This avoids the common “forgotten auth bypass” vulnerability.

---

## 🎯 Demonstrated Security Skills

- API authentication & JWT validation
- Secure inter-service communication
- Input validation as a primary security boundary
- Anti-injection through strict schema enforcement
- Environment-aware security configuration
- Resilient backend design (fail-safe, not fail-open)






