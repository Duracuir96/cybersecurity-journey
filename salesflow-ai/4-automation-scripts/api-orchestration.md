# 🔗 API Orchestration & Service-to-Service Automation

This module documents how the SalesFlow Lite Python backend orchestrates **secure, automated communication** with the Java microservices layer.

The orchestration layer is deliberately **thin**:

* no business logic
* no data transformation
* strict contract enforcement

Its role is to **reliably fetch and push data** between services while enforcing security, resilience, and consistency.

---

## 📌 Orchestration Scope

* Python ↔ Java microservice communication
* Secure JWT forwarding
* Timeout and error handling
* DEV / PROD behavior separation
* Bulk operations for pipelines (Excel import)

---

## 🧠 Design Principles

✔ Single responsibility per client
✔ No business logic in clients
✔ Schema-validated payloads
✔ Fail-fast error handling
✔ DEV_MODE isolation

---

## 🧱 JavaSalesClient — Orchestration Entry Point

📍 **File:** `src/clients/java_sales_client.py`

```python
class JavaSalesClient:
    """
    Client STRICTEMENT aligné sur les endpoints Java Sales.
    Aucune logique métier ici.
    """
```

This class acts as a **dedicated API adapter** for the Java Sales service.

---

## 🔐 Authentication & JWT Forwarding

The orchestration layer forwards the **exact JWT** issued by the Java backend.

```python
def _headers(self) -> dict:
    return {"Authorization": f"Bearer {self.token}"} if self.token else {}
```

✔ No token rewriting
✔ No privilege escalation
✔ Clear trust boundary

---

## 🌍 Centralized API Configuration

```python
JAVA_API_URL = os.getenv(
    "JAVA_API_URL",
    "http://localhost:8080/api/v1"
).rstrip("/")
```

✔ Environment-driven configuration
✔ Docker & Cloud friendly
✔ No hard-coded endpoints

---

## 🔁 Unified HTTP GET Automation

All read operations go through a **single internal `_get()` method**.

```python
async def _get(self, endpoint: str) -> Any:
    url = f"{JAVA_API_URL}{endpoint}"
    logger.info(f"[JavaSalesClient] GET {url} (DEV_MODE={DEV_MODE})")
```

### DEV / PROD Behavior

```python
if DEV_MODE:
    if endpoint == "/sales/recent":
        return MOCK_RECENT_SALES
    if endpoint == "/sales/history":
        return MOCK_SALES_HISTORY
```

✔ Deterministic local development
✔ Zero dependency on Java service in DEV
✔ Identical interface in PROD

---

## 🧹 Payload Normalization Layer

Java responses may differ slightly depending on endpoints.
The client normalizes all responses **before DTO validation**.

```python
def _normalize(self, raw: Any) -> List[dict]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("data", "sales", "content", "items", "result"):
            if key in raw and isinstance(raw[key], list):
                return raw[key]
        return [raw]
    return []
```

✔ Defensive programming
✔ Resilient to API shape variations
✔ Prevents downstream crashes

---

## 📦 Schema-Enforced DTO Mapping

All Java responses are validated using **Pydantic DTOs**.

```python
return [JavaSaleDto.model_validate(s) for s in self._normalize(raw)]
```

✔ Strong typing
✔ Contract enforcement
✔ Anti-injection boundary

---

## 📊 Read Operations (Automated Data Ingestion)

Examples of orchestrated read calls:

```python
async def get_sales_history(self) -> List[JavaSaleDto]:
    raw = await self._get("/sales/history")
    return [JavaSaleDto.model_validate(s) for s in self._normalize(raw)]
```

```python
async def get_sales_history_by_sku(self, sku: str):
    raw = await self._get(f"/sales/history/by-sku/{sku}")
```

✔ Used by analytics pipelines
✔ Used by ML pipelines
✔ Used by scheduled jobs

---

## 📥 Bulk Write Automation (Excel Import Pipeline)

📍 **File:** `src/clients/java_sales_client.py`

The orchestration layer also supports **batch write operations** for Excel / CSV imports.

```python
async def create_bulk_sales(self, rows: List[dict]) -> dict:
```

### Swagger-Aligned Payload Construction

```python
payload = [
    JavaCreateSaleRequestDto(
        items=[JavaSaleItemCreateDto(**row)]
    ).model_dump()
    for row in rows
]
```

✔ Strict contract alignment
✔ No free-form JSON
✔ Schema-first communication

---

## 🚨 Error Handling & Resilience

All failures are caught and translated into **explicit upstream errors**.

```python
except Exception as e:
    logger.exception("Java Sales API error")
    raise HTTPException(
        status_code=502,
        detail=f"Java Sales API error: {str(e)}",
    )
```

✔ Fail-fast behavior
✔ Clear error propagation
✔ No silent corruption

---

## 🧪 DEV_MODE Isolation

```python
if DEV_MODE:
    return {
        "imported": len(payload),
        "failed": 0,
        "items": payload,
    }
```

✔ Safe local testing
✔ No accidental production writes
✔ Same code paths

---

## 🔄 Resource Lifecycle Management

```python
async def close(self):
    await self.client.aclose()
```

✔ Explicit connection cleanup
✔ Async-safe resource handling

---

## 🎯 Why This Is Real API Orchestration

This orchestration layer demonstrates:

* Secure service-to-service communication
* Strict API contract enforcement
* Pipeline-friendly design
* DEV / PROD parity
* Defensive and observable HTTP automation

It avoids common anti-patterns such as embedding business logic or transformation inside API clients.

---

## 🏁 Classification

**Automation Level:**
✅ Tool & API automation
✅ Service-to-service orchestration
🛡️ Security-aware design

---

