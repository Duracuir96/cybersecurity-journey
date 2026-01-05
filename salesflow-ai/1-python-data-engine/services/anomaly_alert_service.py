from src.api.settings import DEV_MODE
from src.services.email_service import send_anomaly_email
from typing import Optional
def handle_anomaly_alert(
    anomaly: dict,
    scope: str,
    product_sku: Optional[str],
    product_name: Optional[str],
    period: str,
):
    if DEV_MODE:
        return

    severity = anomaly.get("severity")

    # 🔒 Politique d’alerte
    if severity not in ("high", "medium"):
        return

    payload = {
        "scope": scope,
        "sku": product_sku,
        "name": product_name,
        "period": period,
        **anomaly,
    }

    send_anomaly_email(payload)
