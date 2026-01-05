import asyncio

from src.services.ml_service import detect_anomalies
from src.models.dto.forecast_dto import ForecastScope
from src.models.dto.analytics_dto import AnalyticsPeriod

async def main():
    print("🚀 START MANUAL SCHEDULER TEST")

    result = await detect_anomalies(
        scope=ForecastScope.GLOBAL,
        period=AnalyticsPeriod.daily,
    )

    print(f"📊 anomalies detected: {result['count']}")
    print("✅ END MANUAL SCHEDULER TEST")

if __name__ == "__main__":
    asyncio.run(main())
