# src/api/routes/reports.py
from __future__ import annotations

import io
import os
import asyncio
import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.api.dependencies import get_current_user, swagger_auth
from src.models.dto.analytics_dto import AnalyticsPeriod
from src.services.report_service import generate_report,get_latest_report, find_last_report_on_disk
from src.scheduler.tasks import get_scheduler

logger = logging.getLogger(__name__)

# -----------------------------------------------------------
# ROUTER CONFIG
# -----------------------------------------------------------
router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"],
    dependencies=[Depends(swagger_auth)],
)

# -----------------------------------------------------------
# TYPES & PAYLOADS
# -----------------------------------------------------------
ReportFormat = Literal["pdf", "excel"]
ReportType = Literal["sales", "stock", "combined"]


class ReportRequestPayload(BaseModel):
    report_type: ReportType
    format: ReportFormat
    period: AnalyticsPeriod = AnalyticsPeriod.monthly


class ScheduleReportPayload(BaseModel):

    # requis pour schedule
    report_type: Optional[ReportType] = None
    format: Optional[ReportFormat] = None
    hour: Optional[int] = None
    minute: Optional[int] = None


# -----------------------------------------------------------
# TOKEN EXTRACTOR
# -----------------------------------------------------------
def _extract_token(current_user: dict) -> Optional[str]:
    if not isinstance(current_user, dict):
        return None

    return (
        current_user.get("token")
        or current_user.get("access_token")
        or current_user.get("raw_token")
        or current_user.get("jwt")
    )


# -----------------------------------------------------------
# GENERATE REPORT (MANUAL — inchangé)
# -----------------------------------------------------------
@router.post("/generate")
async def generate_report_endpoint(
    payload: ReportRequestPayload,
    current_user=Depends(get_current_user),
):
    token = _extract_token(current_user)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token for report generation",
        )

    try:
        content, filename, media_type = await generate_report(
            report_type=payload.report_type,
            fmt=payload.format,
            period=payload.period,
            token=token,
        )

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    except Exception as e:
        logger.exception("Report generation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}",
        )


# -----------------------------------------------------------
# SCHEDULE REPORT (AUTOMATIC + SAVE TO DISK)
# -----------------------------------------------------------

@router.post("/schedule")
async def schedule_report(
    payload: ScheduleReportPayload,
    current_user=Depends(get_current_user),
):
    user_token = _extract_token(current_user)
    if not user_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    scheduler = get_scheduler()

    system_token = os.getenv("SYSTEM_JWT_TOKEN")
    if not system_token:
        raise HTTPException(
            status_code=500,
            detail="SYSTEM_JWT_TOKEN not configured",
        )

    job_id = f"scheduled-{payload.report_type}-{payload.format}"

    async def run_job():
        logger.warning(
            "🕒 SCHEDULED REPORT EXECUTING | %s %s",
            payload.report_type,
            payload.format,
        )

        await generate_report(
            report_type=payload.report_type,
            fmt=payload.format,
            period=AnalyticsPeriod.daily,
            token=system_token,
            save_to_disk=True,
        )

    def job_wrapper():
        asyncio.run(run_job())

    scheduler.add_job(
        job_wrapper,
        trigger="cron",
        hour=payload.hour,
        minute=payload.minute,
        id=job_id,
        replace_existing=True,
    )

    return {
        "status": "scheduled",
        "job_id": job_id,
        "hour": payload.hour,
        "minute": payload.minute,
        "storage": "disk",
    }


@router.get("/scheduled/latest")
async def download_last_scheduled_report(
    report_type: ReportType,
    format: ReportFormat,
    current_user=Depends(get_current_user),
):
    # 🔐 Auth unifiée
    token = _extract_token(current_user)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    file_path = find_last_report_on_disk(
        report_type=report_type,
        fmt=format,
    )

    if not file_path:
        raise HTTPException(
            status_code=404,
            detail="No scheduled report available yet",
        )

    media_type = (
        "application/pdf"
        if format == "pdf"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return StreamingResponse(
        open(file_path, "rb"),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_path.name}"'
        },
    )