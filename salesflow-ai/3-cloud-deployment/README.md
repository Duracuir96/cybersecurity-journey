# ☁️ SalesFlow Lite — Docker Deployment (Local Production MVP)

Docker packaging and service orchestration for the **SalesFlow Lite** multi-service application.  
This setup is designed as a **local-production MVP**, with a cloud-ready architecture mindset.

---

## 🧱 Architecture Overview

SalesFlow Lite is deployed as **isolated Docker services**, each handling a dedicated responsibility:

- **Java API (Spring Boot)** — core business logic, authentication, main database access  
- **Python API (FastAPI)** — analytics, machine learning, reporting, automation pipelines  
- **PostgreSQL** — primary relational database  
- **Redis** — caching layer for analytics and reports  
- **Frontend (React + Nginx)** — user interface

All services communicate over a Docker network using explicit ports and environment variables.

---

## 🐳 Docker Files

- `Dockerfile`  
  Builds the **Python FastAPI backend image**, optimized for backend analytics, ML, and automation workloads.

- `docker-compose.yml`  
  Orchestrates the full SalesFlow Lite stack:
  - Java API
  - Python API
  - PostgreSQL
  - Redis
  - Frontend
 

<img width="812" height="571" alt="image" src="https://github.com/user-attachments/assets/41eaea8b-3f36-46b9-ac6e-265d69feca57" />


- `docs/`  
  Architecture diagrams and technical documentation (microservices, pipelines, data flows).

---

## 🔐 Environment Configuration

Environment-specific values are injected via `.env` files and **are not committed**.

Typical variables include:
- JWT secrets
- Database credentials
- SMTP credentials
- Internal service URLs

This separation between **code and configuration** follows production security best practices.

---

## 🚀 Deployment (Local Production)

Build and start the full stack:

```bash
docker-compose up --build

