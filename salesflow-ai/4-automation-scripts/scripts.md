# 📜 Automation Scripts – Report Generation

This document describes **script-based automation** implemented in the SalesFlow Lite backend.

Unlike pipelines or schedulers, these scripts are **callable execution units** designed to:

* generate business reports,
* format outputs (PDF / Excel),
* persist artifacts to disk,
* and be reused by APIs, schedulers, or manual executions.

They represent **controlled backend automation**, not ad-hoc scripts.

---

## 🧭 Scope of Script Automation

These scripts automate:

* Executive PDF report generation
* Excel analytics export
* File naming & versioning
* Safe persistence to disk
* Reusability across API & scheduled contexts

They are **idempotent, deterministic, and auditable**.

---

## 📂 Main Script Location

```
src/services/report_service.py
```

This file acts as a **scripted automation module**, not a simple helper.

---

## 🧩 Script Architecture

```
generate_report()
 ├─ load analytics (sales / stock)
 ├─ format decision (PDF | Excel)
 ├─ generate content
 │    ├─ charts
 │    ├─ tables
 │    ├─ executive summary
 ├─ filename versioning
 ├─ output routing
 │    ├─ API response
 │    └─ disk persistence
```

---

## 🚀 Entry Point – Script Execution

### Core Automation Function

```python
async def generate_report(
    report_type: ReportType,
    fmt: ReportFormat,
    period: AnalyticsPeriod,
    token: Optional[str],
    save_to_disk: bool = False,
)
```

This single function is reused by:

* REST API endpoints
* Scheduled cron jobs
* Manual execution (CLI / dev)

✔ Single source of truth
✔ No duplicated logic

---

## 📊 Automated Data Loading

```python
sales = await compute_sales_analytics(period=period, token=token)
stock = await compute_stock_analytics(period=period, token=token)
```

Automation guarantees:

* Consistent analytics logic
* Same computation as dashboard
* Auditability (same KPIs everywhere)

---

## 🧠 Smart Automation Logic

```python
include_stock = report_type in ("combined", "stock")
```

The script automatically adapts:

* sales-only report
* stock-only report
* combined executive report

No manual branching required externally.

---

## 📄 PDF Report Automation

📍 **Function:** `_generate_sales_pdf()`

```python
content = _generate_sales_pdf(
    sales=sales,
    stock=stock if include_stock else None,
)
```

Automated responsibilities:

* cover page generation
* executive summary synthesis
* KPI tables
* charts (line & bar)
* pagination & layout

This is **document-generation automation**, not templating.

---

## 📈 Chart Automation

```python
lp = LinePlot()
lp.data = [data]
lp.joinedLines = True
```

```python
bc = VerticalBarChart()
bc.data = [values]
```

Charts are:

* computed dynamically
* scaled automatically
* embedded programmatically

No static assets involved.

---

## 📊 Excel Export Automation

📍 **Function:** `_generate_sales_excel()`

```python
wb = Workbook()
ws_overview = wb.active
ws_overview.title = "Overview"
```

Automated Excel features:

* multi-sheet workbook
* charts
* KPI sections
* stock snapshots
* safe column auto-sizing

```python
_auto_adjust_column_width(ws)
```

---

## 🧾 Versioned File Naming Automation

```python
filename = f"analytics_{report_type}_{period.value}_{_now_label()}.pdf"
```

Guarantees:

* no overwrite
* timestamp traceability
* deterministic naming convention

---

## 💾 Disk Persistence Automation

```python
def _save_report_to_disk(content: bytes, filename: str) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = REPORTS_DIR / filename
    file_path.write_bytes(content)
```

This enables:

* scheduled batch jobs
* offline access
* audit retention

---

## 🔁 Dual-Mode Automation (API vs Scheduler)

```python
if save_to_disk:
    return {
        "status": "success",
        "file_path": file_path,
        "filename": filename,
        "generated_at": datetime.utcnow().isoformat(),
    }
```

| Mode      | Usage                  |
| --------- | ---------------------- |
| API       | Download response      |
| Scheduler | Silent disk generation |

Same script. Different execution context.

---

## 🧠 Script Automation Characteristics

| Property         | Status |
| ---------------- | ------ |
| Deterministic    | ✅      |
| Idempotent       | ✅      |
| Stateless        | ✅      |
| Reusable         | ✅      |
| Environment-safe | ✅      |

---

## 🎯 Why This Is Real Automation

This is not:

* a CLI toy script
* a notebook export
* a one-off batch

This **is backend automation**, designed to be:

* triggered by pipelines
* scheduled via cron
* audited by ops
* reused by APIs

---

## 🏁 Automation Classification

**Type:** Script-based backend automation
**Level:** Deterministic operational automation
**Risk:** Low (read-only analytics, controlled writes)

---

## ✅ Key Takeaway

> SalesFlow Lite uses scripts as automation building blocks — not as isolated utilities.

---


