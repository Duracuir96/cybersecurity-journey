# 🐍 SalesFlow AI Engine – Data & Machine Learning Microservice

A secure Python microservice for sales analytics, demand forecasting, and business intelligence.

## 🔧 Technology Stack
- **Backend Framework:** FastAPI, Pydantic
- **Data Processing:** Pandas, NumPy
- **Machine Learning:** Scikit-learn

## 🛡️ Built-in Security
- **Input Validation:** Pydantic models for request/response validation
- **Authentication:** JWT-based authentication (integrated with Java auth service)
- **Audit Trail:** Structured logging for security monitoring and compliance

## 📈 Key Features
- **Real-time Analytics:** Live sales data processing and insights
- **ML Forecasting:** Linear regression models for demand prediction
- **RESTful API:** Fully documented endpoints with Swagger/OpenAPI integration
- **Excel Integration:** Automated data import/export functionality
- **Report Generation:** Asynchronous report creation and management

## 🚀 API Endpoints

### 4.1.1 Analytics
- `GET /api/v1/analytics/sales-trend` – Retrieve sales trend metrics
- `GET /api/v1/analytics/health` – Service health check

### 4.1.2 Stock
- `GET /api/v1/stock/alerts` – Get stock level alerts

### 4.1.3 Machine Learning
- `GET /api/v1/ml/forecast` – Generate sales forecasts
- `GET /api/v1/ml/anomalies` – Detect anomalies in sales data

### 4.1.4 Reports
- `POST /api/v1/reports/generate` – Initiate report generation
- `GET /api/v1/reports/status/{job_id}` – Check report generation status
- `GET /api/v1/reports/download` – Download generated reports

### 4.1.5 Excel Integration
- `POST /api/v1/excel/upload` – Upload Excel data for processing
- `POST /api/v1/excel/commit` – Commit processed Excel data to database

---
*This service demonstrates secure, production-ready Python development with a focus on data science integration and comprehensive API design.*
