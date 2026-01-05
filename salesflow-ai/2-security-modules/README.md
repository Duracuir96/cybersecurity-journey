# 🔐 SalesFlow Security Modules – Practical DevSecOps for Python APIs

Reusable, production-oriented **security components** implemented in the **SalesFlow-Lite Python backend**.  
This module reflects **real backend security engineering**, aligned with a **Java ↔ Python microservice architecture**.

The focus is on **authentication, input validation, contract enforcement, and operational resilience**, rather than theoretical security features.


---

## 🔐 Unified Authentication Architecture (Design Decision)

### 🎯 Problem Statement

SalesFlow-Lite is built on a **Java ↔ Python microservice architecture**, which introduces a critical security challenge:

> **How to authenticate users and services consistently across multiple backends without duplicating identity logic or creating trust ambiguities?**

Common anti-patterns avoided:

* Each service issuing its own JWT
* Python acting as an identity provider
* Token re-signing between services
* Shared database access for authentication

These patterns typically lead to:

* Broken trust boundaries
* Token confusion attacks
* Over-privileged services
* Hard-to-audit security flows

---

### 🧠 Architectural Decision

SalesFlow-Lite adopts a **Single Authority Authentication Model**.

### Key Decision

> **The Java API is the sole authentication authority.
> The Python API is a strictly downstream, trust-based consumer.**

This results in:

* One identity source
* One JWT format
* One signing secret
* One issuer (`iss = "salesflow-app"`)

---

### 🏗️ Authentication Flow (High-Level)
<p align="center">
  <img src="https://github.com/user-attachments/assets/4e382d10-b585-4a77-a171-2f3c5b844516" width="45%" />
  <img src="https://github.com/user-attachments/assets/a1647f50-8d17-432f-87f0-793321aa0189" width="45%" />
</p>

                    


There is **no lateral trust** between services — only **vertical trust**.

---

### 🔒 Security Boundaries Enforced

| Component  | Responsibility             | Trust Level         |
| ---------- | -------------------------- | ------------------- |
| Frontend   | Token storage & forwarding | Untrusted           |
| Java API   | Identity & authorization   | Trusted authority   |
| Python API | Validation & execution     | Restricted          |
| Database   | Persistence                | Private (Java-only) |

Python **cannot authenticate users**, **cannot escalate privileges**, and **cannot access persistence directly**.

---

### 🧩 Implementation Mapping (Design → Code)

| Architectural Rule      | Enforced By               |
| ----------------------- | ------------------------- |
| Single JWT issuer       | `jwt_validator.py`        |
| No token mutation       | FastAPI dependency design |
| Strict validation       | HS256 + `iss` + `exp`     |
| Least privilege         | Service-to-service JWT    |
| No identity duplication | No auth logic in Python   |
| Environment safety      | `DEV_MODE` guards         |

---

## 🚨 What This Architecture Prevents

* Token forgery between services
* Identity desynchronization
* Accidental privilege escalation
* Authentication logic drift
* “Shadow auth” implementations

---

### 🧪 Why This Matters (Engineering Perspective)

This unified authentication architecture:

* Scales cleanly with new microservices
* Is auditable and testable
* Matches real-world enterprise patterns
* Separates **identity** from **computation**

> Python focuses on **analytics, ML, and automation**, not identity.

---

### 🏁 Takeaway

This is **not** just JWT validation.

It is a **deliberate security architecture** designed to:

* Centralize trust
* Minimize attack surface
* Enforce least privilege
* Keep services loosely coupled but securely integrated

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






