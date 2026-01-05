# src/api/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import logging
import os

from dotenv import load_dotenv

# Routers
from src.api.routes.health import router as health_router
from src.api.routes.analytics import router as analytics_router
from src.api.routes.excel import router as excel_router
from src.api.routes.ml import router as ml_router
from src.api.routes.reports import router as reports_router

# Scheduler
from src.scheduler.tasks import get_scheduler

# Exception handlers
from src.utils.exceptions import (
    http_exception_handler,
    generic_exception_handler,
)

# Load .env
load_dotenv()


# ---------------------------------------------------------
# FASTAPI CONFIG
# ---------------------------------------------------------
app = FastAPI(
    title="SalesFlow API",
    version="0.2.0",
    description=(
        "Analytics / ML / Reports microservice for SalesFlow "
        "with unified Java JWT validation."
    ),
)


# ---------------------------------------------------------
# CORS (React + Java + FastAPI)
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5174",   # React Vite Dev
        "http://127.0.0.1:4173",   # React Vite Preview
        "http://localhost:8080",   # Spring Boot
        "http://localhost:8081",   # FastAPI
        "http://localhost:5174",
        "http://localhost:4173",
        "http://10.131.221.179:8080/api/v1" # Spring boot network url 

    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# STARTUP EVENT
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logging.basicConfig(level=logging.INFO)

    logging.info("🚀 FastAPI (Analytics / ML / Reports) started")
    logging.info(
        "JAVA_JWT_SECRET loaded: %s",
        bool(os.getenv("JAVA_JWT_SECRET")),
    )

    # Start scheduler (optional)
    if os.getenv("ENABLE_SCHEDULER", "true").lower() == "true":
        logging.info("⏰ Scheduler enabled: starting background jobs…")
        get_scheduler()
    else:
        logging.info("⏹ Scheduler disabled")


# ---------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------
app.include_router(health_router)
app.include_router(analytics_router)
app.include_router(excel_router)
app.include_router(ml_router)
app.include_router(reports_router)


# ---------------------------------------------------------
# EXCEPTION HANDLERS
# ---------------------------------------------------------
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ---------------------------------------------------------
# CUSTOM OPENAPI SCHEMA — ADD JWT LOCK 🔒
# ---------------------------------------------------------
def custom_openapi():
    """
    Customize Swagger Documentation:
    - Add BearerAuth (JWT)
    - Lock all endpoints except /health
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="SalesFlow API",
        version="0.2.0",
        description="Unified Analytics / ML / Reports API with Java JWT validation",
        routes=app.routes,
    )

    # 🔐 BearerAuth
    openapi_schema.setdefault("components", {}).setdefault(
        "securitySchemes",
        {}
    )["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    # 🔐 Apply security to all endpoints except /health
    for path, methods in openapi_schema.get("paths", {}).items():
        if "/health" in path:
            continue
        for _, details in methods.items():
            details.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
