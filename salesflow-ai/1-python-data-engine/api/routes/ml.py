# src/api/routes/ml.py
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_current_user, swagger_auth
from src.clients.java_products_client import JavaProductsClient

from src.services.ml_service import forecast_sales, detect_anomalies
from src.services.ml_enrichment_service import enrich_ml_result

from src.models.dto.forecast_dto import (
    ForecastRequest,
    ForecastResult,
    ForecastScope,
    AnomalyRequest,
    AnomalyResponse,
)


router = APIRouter(
    prefix="/api/v1/ml",
    tags=["Machine Learning"],
    dependencies=[Depends(swagger_auth)],
)


# -----------------------------------------------------------
# TOKEN EXTRACTOR — unifié
# -----------------------------------------------------------
def _extract_token(current_user: Any) -> Optional[str]:
    if isinstance(current_user, dict):
        return (
            current_user.get("token")
            or current_user.get("access_token")
            or current_user.get("raw_token")
            or current_user.get("jwt")
        )
    return None


# -----------------------------------------------------------
# FORECAST ENDPOINT — Support SKU ou NAME
# -----------------------------------------------------------
@router.post("/forecast", response_model=ForecastResult)
async def forecast_endpoint(
    payload: ForecastRequest,
    current_user=Depends(get_current_user),
):
    token = _extract_token(current_user)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    product = None
    resolved_sku: Optional[str] = None

    if payload.scope == ForecastScope.PRODUCT:
        # Cas 1 : SKU fourni directement
        if payload.sku:
            resolved_sku = payload.sku.strip()

        # Cas 2 : NAME fourni → résolution via API Products
        elif payload.name:
            prod_client = JavaProductsClient(token)
            try:
                product = await prod_client.get_product_by_name(payload.name.strip())
                resolved_sku = product.sku
            finally:
                await prod_client.close()

        # Si ni l'un ni l'autre → déjà bloqué par DTO validator

        # Enrichissement UI avec le produit récupéré (si via name)
        if product is None and payload.product_id:
            # Optionnel : fallback sur ID si fourni
            prod_client = JavaProductsClient(token)
            try:
                product = await prod_client.get_product_by_id(payload.product_id)
                resolved_sku = product.sku
            except Exception:
                pass  # On garde le SKU déjà résolu
            finally:
                await prod_client.close()

    # Appel au service ML avec le SKU résolu
    ml_result = await forecast_sales(
        scope=payload.scope,
        product_sku=resolved_sku,
        product_name=payload.name if not payload.sku else None,  # pour cache si besoin
        forecast_days=payload.forecast_days,
        period=payload.period,
        token=token,
    )

    # Conservation de l'ID si fourni
    ml_result["product_id"] = payload.product_id

    # Enrichissement final pour le frontend (nom, sku, etc.)
    return enrich_ml_result(
        result=ml_result,
        product=product,
    )


# -----------------------------------------------------------
# ANOMALIES ENDPOINT — Support SKU ou NAME
# -----------------------------------------------------------
@router.post("/anomalies", response_model=AnomalyResponse)
async def anomalies_endpoint(
    payload: AnomalyRequest,
    current_user=Depends(get_current_user),
):
    token = _extract_token(current_user)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    product = None
    resolved_sku: Optional[str] = None

    if payload.scope == ForecastScope.PRODUCT:
        if payload.sku:
            resolved_sku = payload.sku.strip()

        elif payload.name:
            prod_client = JavaProductsClient(token)
            try:
                product = await prod_client.get_product_by_name(payload.name.strip())
                resolved_sku = product.sku
            finally:
                await prod_client.close()

        if payload.product_id and product is None:
            prod_client = JavaProductsClient(token)
            try:
                product = await prod_client.get_product_by_id(payload.product_id)
                resolved_sku = product.sku
            except Exception:
                pass
            finally:
                await prod_client.close()

    result = await detect_anomalies(
        scope=payload.scope,
        product_sku=resolved_sku,
        product_name=payload.name if not payload.sku else None,
        period=payload.period,
        token=token,
    )

    result["product_id"] = payload.product_id

    # Enrichissement UI
    enriched = enrich_ml_result(
        result=result,
        product=product,
    )

    return enriched