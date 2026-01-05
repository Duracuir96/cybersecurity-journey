# ============================
# BASE IMAGE (PYTHON 3.9.13)
# ============================
FROM python:3.9.13-slim

# ============================
# PYTHON CONFIG
# ============================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ============================
# DEPENDENCIES
# ============================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================
# APPLICATION CODE
# ============================
COPY src ./src

# ============================
# PORT
# ============================
EXPOSE 8081

# ============================
# START FASTAPI
# ============================
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8081", "--reload"]
