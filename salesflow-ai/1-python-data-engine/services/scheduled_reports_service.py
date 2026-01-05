import logging
from datetime import datetime

from src.models.report import ReportRequest
from src.services.report_service import generate_report_internal

logger = logging.getLogger(__name__)


async def generate_daily_sales_report():
    """
    Job APScheduler
    Génère automatiquement le rapport SALES PDF
    """

    logger.info("🕛 Starting scheduled daily sales report")

    req = ReportRequest(
        report_type="sales",
        format="pdf",
        period="daily"
    )

    # ⚠️ fonction métier, PAS endpoint FastAPI
    result = await generate_report_internal(req)

    logger.info(
        "✅ Daily sales report generated: %s",
        result.get("file_path")
    )

    return result
