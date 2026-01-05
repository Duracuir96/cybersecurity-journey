# src/services/ml_service.py
from __future__ import annotations

import json
from datetime import timedelta
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sklearn.linear_model import LinearRegression

from src.api.settings import DEV_MODE
from src.data.cache_manager import get_cache, set_cache, TTL_ANALYTICS
from src.clients.java_sales_client import JavaSalesClient
from src.clients.java_products_client import JavaProductsClient  # ← Ajout nécessaire
from src.mock.mock_ml_sales import load_mock_ml_sales

from src.data.ml_preprocessor import (
    clean_numeric,
    fill_missing_values,
    prepare_regression_features,
)

from src.models.dto.analytics_dto import AnalyticsPeriod
from src.models.dto.forecast_dto import ForecastScope

from src.services.anomaly_alert_service import handle_anomaly_alert



DEFAULT_HISTORY_DAYS = 90


# ------------------------------------------------------------
# LOAD SALES HISTORY — Support SKU ou NAME
# ------------------------------------------------------------
async def _load_sales_history(
    scope: ForecastScope,
    product_sku: Optional[str],
    product_name: Optional[str],
    token: Optional[str],
) -> pd.DataFrame:
    """
    Charge l'historique des ventes.
    - GLOBAL : toutes les ventes
    - PRODUCT : soit par SKU, soit par NAME (résolution automatique)
    """

    if DEV_MODE:
        # En dev, on mocke avec le SKU si disponible, sinon global
        return load_mock_ml_sales(scope.value, product_sku)

    client = JavaSalesClient(token)
    rows: List[Dict[str, Any]] = []

    try:
        if scope == ForecastScope.GLOBAL:
            sales = await client.get_sales_history()
            for s in sales:
                d = s.saleDate.date() if hasattr(s.saleDate, "date") else s.saleDate
                for it in s.items:
                    rows.append({
                        "date": str(d),
                        "quantity": it.quantity,
                    })

        else:  # PRODUCT
            # Cas 1 : SKU fourni → direct
            if product_sku:
                flat = await client.get_sales_history_by_sku(product_sku)

            # Cas 2 : seul NAME fourni → résolution via Products API
            elif product_name:
                prod_client = JavaProductsClient(token)
                try:
                    product = await prod_client.get_product_by_name(product_name)
                    flat = await client.get_sales_history_by_sku(product.sku)
                finally:
                    await prod_client.close()
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Either product_sku or product_name is required for PRODUCT scope"
                )

            rows = [
                {"date": r.date, "quantity": r.quantity}
                for r in flat
            ]

    finally:
        await client.close()

    if not rows:
        raise HTTPException(404, "No sales history found")

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "quantity"])
    df = df.sort_values("date").reset_index(drop=True)

    df = clean_numeric(df, "quantity")
    df = fill_missing_values(df)

    cutoff = df["date"].max() - timedelta(days=DEFAULT_HISTORY_DAYS)
    return df[df["date"] >= cutoff].reset_index(drop=True)


# ------------------------------------------------------------
# FORECAST — Maintenant accepte SKU ou NAME
# ------------------------------------------------------------
async def forecast_sales(
    scope: ForecastScope,
    product_sku: Optional[str] = None,
    product_name: Optional[str] = None,
    forecast_days: int = 7,
    period: AnalyticsPeriod = AnalyticsPeriod.daily,
    token: Optional[str] = None,
) -> Dict[str, Any]:

    if forecast_days <= 0:
        raise HTTPException(400, "forecast_days must be > 0")

    identifier = product_sku or product_name or "global"
    cache_key = f"ml:forecast:{scope.value}:{identifier}:{forecast_days}:{period.value}"
    cached = get_cache(cache_key)
    if cached:
        return json.loads(cached)

    df = await _load_sales_history(scope, product_sku, product_name, token)
    if len(df) < 2:
        raise HTTPException(400, "Not enough historical data")

    X, y, dfp = prepare_regression_features(df)
    model = LinearRegression().fit(X, y)

    last_idx = int(dfp["day_index"].iloc[-1])
    future_idx = np.arange(last_idx + 1, last_idx + 1 + forecast_days).reshape(-1, 1)

    preds = model.predict(future_idx).clip(0).round(2).tolist()

    last_date = dfp["date"].iloc[-1]
    dates = [
        (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(1, forecast_days + 1)
    ]

    trend = (
        "upward" if preds[-1] > preds[0]
        else "downward" if preds[-1] < preds[0]
        else "stable"
    )

    result = {
        "scope": scope.value,
        "product_id": None,
        "product_sku": product_sku,
        "dates": dates,
        "predictions": preds,
        "summary": {
            "total": float(sum(preds)),
            "daily_average": float(np.mean(preds)),
            "peak_value": float(max(preds)),
            "peak_day": dates[int(np.argmax(preds))],
            "trend": trend,
            "period_label": period.value,
        },
    }

    set_cache(cache_key, json.dumps(result), TTL_ANALYTICS)
    return result


# ------------------------------------------------------------
# ANOMALIES — Support SKU ou NAME
# ------------------------------------------------------------
async def detect_anomalies(
    scope: ForecastScope,
    product_sku: Optional[str] = None,
    product_name: Optional[str] = None,
    period: AnalyticsPeriod = AnalyticsPeriod.daily,
    token: Optional[str] = None,
) -> Dict[str, Any]:

    identifier = product_sku or product_name or "global"
    cache_key = f"ml:anomalies:{scope.value}:{identifier}:{period.value}"
    cached = get_cache(cache_key)
    if cached:
        return json.loads(cached)

    df = await _load_sales_history(scope, product_sku, product_name, token)

    values = df["quantity"].astype(float)
    mean, std = values.mean(), values.std()

    anomalies = []
    if std and not np.isnan(std):
        z = (values - mean) / std
        for i, score in z.items():
            if abs(score) >= 3:
                anomalies.append({
                    "date": df["date"].iloc[i].strftime("%Y-%m-%d"),
                    "value": float(values.iloc[i]),
                    "score": round(float(score), 3),
                    "severity": "high" if abs(score) >= 4 else "medium",
                    "type": "HIGH_SPIKE" if score > 0 else "DROP",
                    "explanation": "Z-score anomaly detected",
                })

    result = {
        "scope": scope.value,
        "product_id": None,
        "product_sku": product_sku,
        "period": period.value,
        "count": len(anomalies),
        "anomalies": anomalies,
    }

    for anomaly in anomalies:
        handle_anomaly_alert(
            anomaly=anomaly,
            scope=scope.value,
            product_sku=product_sku,
            product_name=product_name,
            period=period.value,
        )

    set_cache(cache_key, json.dumps(result), TTL_ANALYTICS)
    return result