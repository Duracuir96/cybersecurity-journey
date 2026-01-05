# src/api/routes/health.py

from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1/health",
    tags=["Health"]
)

@router.get("")
async def health_check():
    return {
        "status": "ok",
        "service": "FastAPI Analytics",
        "message": "Service is running"
    }
