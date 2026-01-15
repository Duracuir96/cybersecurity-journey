

# ⏰ Scheduled Automation & Cron Pipelines

The SalesFlow Lite backend includes **time-based automation** using an asynchronous scheduler.
This layer is responsible for executing **periodic reports** and **automated anomaly checks** without any user interaction.

The scheduling system reuses **existing pipelines** (reports, ML, anomalies) instead of duplicating business logic.

---

## 📌 Scheduling Scope

* Automated report generation
* Periodic anomaly detection
* System-level execution (no user context)
* Ops-oriented automation

---

## 🧠 Scheduler Initialization

📍 **File:** `src/scheduler/tasks.py`

The scheduler is initialized lazily and shared as a singleton.

```python
scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        scheduler.start()
        logging.info("⏰ Scheduler started")
    return scheduler
```

✔ Async-compatible
✔ Centralized scheduler lifecycle
✔ Explicit timezone configuration

---

## 📊 Scheduled Report Pipeline

This job automatically generates reports at predefined times using the existing **Reports Pipeline**.

📍 **File:** `src/scheduler/tasks.py`

### Job Definition

```python
def schedule_report_job(
    report_type: str,
    fmt: str,
    hour: int,
    minute: int,
    system_token: str,
):
```

### Job Execution Logic

```python
async def job():
    logging.warning(
        f"🕒 SCHEDULED REPORT EXECUTING | {report_type} {fmt}"
    )
    await generate_report(
        report_type=report_type,
        fmt=fmt,
        period=AnalyticsPeriod.daily,
        token=system_token,
        save_to_disk=True,
    )
```

### Cron Registration

```python
scheduler.add_job(
    job_wrapper,
    trigger="cron",
    hour=hour,
    minute=minute,
    id=job_id,
    replace_existing=True,
)
```

✔ Uses cron-style scheduling
✔ Reuses the report generation pipeline
✔ Ensures idempotency via `replace_existing=True`

---

## 🔐 System-Level Execution (No User Dependency)

Scheduled jobs use a **system token**, not a user token.

```python
await generate_report(
    ...
    token=system_token,
    save_to_disk=True,
)
```

### Why this matters

* Jobs remain functional without active users
* No privilege escalation
* Clear separation between **user actions** and **system automation**

---

## 🚨 Scheduled Anomaly Detection Pipeline

The scheduler can also trigger **periodic anomaly detection** independently of API calls.

📍 **File:** `src/scheduler/tasks.py`

```python
async def scheduled_anomaly_check():
    await detect_anomalies(
        scope=ForecastScope.GLOBAL,
        period=AnalyticsPeriod.daily,
    )
```

✔ Fully automated ML-assisted monitoring
✔ Reuses the ML & anomaly pipelines
✔ Compatible with alerting (email notifications)

---

## 🔁 Async Execution Strategy

Because APScheduler executes jobs in a synchronous context, asynchronous pipelines are wrapped explicitly.

```python
def job_wrapper():
    asyncio.run(job())
```

✔ Prevents event loop conflicts
✔ Ensures compatibility with async services
✔ Keeps scheduling logic isolated from business logic

---

## 🧪 Manual Trigger (Ops Testing)

```python
if __name__ == "__main__":
    import asyncio
    asyncio.run(scheduled_anomaly_check())
```

✔ Safe manual execution
✔ Useful for operational validation
✔ No API exposure required

---

## 🎯 Automation Characteristics

| Feature         | Implementation             |
| --------------- | -------------------------- |
| Scheduler       | APScheduler (AsyncIO)      |
| Trigger type    | Cron-based                 |
| Context         | System-level               |
| Logic           | Pipeline reuse             |
| User dependency | ❌ None                    |
| Safety          | Explicit execution control |

---

## 🧠 Why This Is Real Scheduling Automation

This scheduling layer demonstrates:

* Production-ready cron automation
* Clear separation of concerns
* Secure, non-interactive system execution
* Reuse of analytics, ML, and reporting pipelines
* Ops-focused backend design

It avoids common anti-patterns such as embedding business logic directly in cron jobs.

---

## 🏁 Classification

**Automation Level:**
✅ Time-based automation (Ops-oriented)
🔁 Pipeline-driven execution
🛡️ Safe by design (no user tokens, no auto-remediation)



