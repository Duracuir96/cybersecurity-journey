from __future__ import annotations

from typing import Any, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_current_user, swagger_auth
from src.models.dto.analytics_dto import (
    AnalyticsPeriod,
    StockAnalyticsResponse,
    SalesAnalyticsResponse,
)
from src.services.analytics_service import (
    compute_stock_analytics,
    compute_sales_analytics,
)


router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"],
    dependencies=[Depends(swagger_auth)],  # 🔒 Swagger lock
)


# -----------------------------------------------------------
# TOKEN EXTRACTOR — version unifiée
# -----------------------------------------------------------
def _extract_token(current_user: Any) -> Optional[str]:
    """
    Robust extractor compatible with:
    {
        "token": "...",
        "access_token": "...",
        "raw_token": "...",
        "jwt": "..."
    }
    """
    if isinstance(current_user, dict):
        return (
            current_user.get("token")
            or current_user.get("access_token")
            or current_user.get("raw_token")
            or current_user.get("jwt")
        )
    return None


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format (expected YYYY-MM-DD): {value}",
        )


# -----------------------------------------------------------
# STOCK ANALYTICS (GLOBAL)
# -----------------------------------------------------------
@router.get(
    "/stock",
    response_model=StockAnalyticsResponse,
)
async def stock_analytics(
    period: AnalyticsPeriod = AnalyticsPeriod.daily,
    current_user=Depends(get_current_user),
):
    token = _extract_token(current_user)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    return await compute_stock_analytics(
        period=period,
        token=token,
    )


# -----------------------------------------------------------
# SALES ANALYTICS (GLOBAL)
# -----------------------------------------------------------
@router.get(
    "/sales",
    response_model=SalesAnalyticsResponse,
)
async def sales_analytics(
    period: AnalyticsPeriod = AnalyticsPeriod.daily,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    token = _extract_token(current_user)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    start = _parse_date(start_date)
    end = _parse_date(end_date)

    return await compute_sales_analytics(
        period=period,
        start_date=start,
        end_date=end,
        token=token,
    )
