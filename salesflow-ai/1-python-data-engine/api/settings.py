# src/api/settings.py

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def str_to_bool(value: str) -> bool:
    """
    Convert environment string to boolean safely.
    Accepts: true, false, yes, no, 1, 0, y, n.
    """
    if value is None:
        return False
    return value.lower() in ("true", "1", "yes", "y")

# ---------------------------------------------------------
# 🔐 AUTH / SECURITY SETTINGS
# ---------------------------------------------------------

# DEV_MODE:
# - Used by Analytics service
# - Determines whether to use mock FAKE_PRODUCTS / FAKE_SALES
DEV_MODE = str_to_bool(os.getenv("DEV_MODE", "false"))

# Secret used for verifying Java JWT tokens
JAVA_JWT_SECRET = os.getenv("JAVA_JWT_SECRET")


# ---------------------------------------------------------
# 🧠 MACHINE LEARNING SETTINGS
# ---------------------------------------------------------

# ML_ENV:
# - "dev"  → ML uses mock sales dataset
# - "prod" → ML calls Java Sales API for real dataset
ML_ENV = os.getenv("ML_ENV", "dev").lower()


# ---------------------------------------------------------
# 🔌 JAVA API SETTINGS
# ---------------------------------------------------------

# Base URL for calling Java backend
JAVA_API_URL = os.getenv("JAVA_API_URL", "http://localhost:8080/api/v1")


# ---------------------------------------------------------
# 🚨 VALIDATION & DEBUG
# ---------------------------------------------------------

if not JAVA_JWT_SECRET:
    print("⚠ WARNING: JAVA_JWT_SECRET is not set. Java JWT validation may fail.")

print(f"🔧 SETTINGS LOADED:")
print(f"   DEV_MODE      = {DEV_MODE}")
print(f"   ML_ENV        = {ML_ENV}")
print(f"   JAVA_API_URL  = {JAVA_API_URL}")
# ============================================================
# EMAIL / ALERTING SETTINGS
# ============================================================

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")