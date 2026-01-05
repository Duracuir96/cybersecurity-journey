from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Optional
import logging
import asyncio

from src.services.report_service import generate_report
from src.models.dto.analytics_dto import AnalyticsPeriod

from src.services.ml_service import detect_anomalies
from src.models.dto.forecast_dto import ForecastScope
from src.models.dto.analytics_dto import AnalyticsPeriod


scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        scheduler.start()
        logging.info("⏰ Scheduler started")
    return scheduler


def schedule_report_job(
    report_type: str,
    fmt: str,
    hour: int,
    minute: int,
    system_token: str,
):
    scheduler = get_scheduler()

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

    def job_wrapper():
        asyncio.run(job())

    job_id = f"scheduled-{report_type}-{fmt}"

    scheduler.add_job(
        job_wrapper,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id,
        replace_existing=True,
    )

    return job_id
async def scheduled_anomaly_check():
    await detect_anomalies(
        scope=ForecastScope.GLOBAL,
        period=AnalyticsPeriod.daily,
    )
    if __name__ == "__main__":
        import asyncio
        asyncio.run(scheduled_anomaly_check())
