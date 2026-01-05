# src/models/dto/forecast_dto.py
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from src.models.dto.analytics_dto import AnalyticsPeriod


# ============================================================
# FORECAST / ANOMALY SCOPE
# ============================================================
class ForecastScope(str, Enum):
    GLOBAL = "GLOBAL"
    PRODUCT = "PRODUCT"


# ============================================================
# FORECAST REQUEST
# ============================================================
class ForecastRequest(BaseModel):
    """
    Forecast request.

    Rules:
    - scope=GLOBAL  → sku, name, product_id must be None
    - scope=PRODUCT → at least one of sku or name is REQUIRED
                      → product_id is optional
    """

    scope: ForecastScope = Field(..., description="GLOBAL or PRODUCT")

    sku: Optional[str] = Field(
        None, description="SKU of the product (alternative to name)"
    )
    name: Optional[str] = Field(
        None, description="Name of the product (alternative to sku)"
    )
    product_id: Optional[int] = Field(
        None, description="Optional product ID (for caching / tracking)"
    )

    forecast_days: int = Field(
        7, ge=1, le=365, description="Number of days to forecast"
    )
    period: AnalyticsPeriod = AnalyticsPeriod.daily

    @model_validator(mode="after")
    def validate_product_identifier(self):
        if self.scope == ForecastScope.PRODUCT:
            if not self.sku and not self.name:
                raise ValueError(
                    "At least one of 'sku' or 'name' is required when scope=PRODUCT"
                )
            # Nettoyage optionnel
            if self.sku:
                self.sku = self.sku.strip()
            if self.name:
                self.name = self.name.strip()
        else:  # GLOBAL
            self.sku = None
            self.name = None
            self.product_id = None
        return self


# ============================================================
# FORECAST SUMMARY
# ============================================================
class ForecastSummary(BaseModel):
    total: float
    daily_average: float
    peak_value: float
    peak_day: str
    trend: str
    period_label: str


# ============================================================
# PRODUCT INFO (for UI enrichment)
# ============================================================
class ProductInfo(BaseModel):
    id: Optional[int] = None
    sku: Optional[str] = None
    name: Optional[str] = None
    # Ajoute d'autres champs si besoin (price, category, etc.)


# ============================================================
# FORECAST RESULT
# ============================================================
class ForecastResult(BaseModel):
    """
    Response returned by /ml/forecast
    """

    scope: ForecastScope
    product_id: Optional[int] = None

    dates: List[str]
    predictions: List[float]

    summary: ForecastSummary

    product: Optional[ProductInfo] = None


# ============================================================
# ANOMALY REQUEST
# ============================================================
class AnomalyRequest(BaseModel):
    """
    Anomaly detection request.

    Rules:
    - scope=GLOBAL  → sku, name, product_id must be None
    - scope=PRODUCT → at least one of sku or name is REQUIRED
    """

    scope: ForecastScope = Field(..., description="GLOBAL or PRODUCT")

    sku: Optional[str] = Field(None, description="SKU (alternative to name)")
    name: Optional[str] = Field(None, description="Name (alternative to sku)")
    product_id: Optional[int] = Field(None, description="Optional product ID")

    period: AnalyticsPeriod = AnalyticsPeriod.daily

    @model_validator(mode="after")
    def validate_product_identifier(self):
        if self.scope == ForecastScope.PRODUCT:
            if not self.sku and not self.name:
                raise ValueError(
                    "At least one of 'sku' or 'name' is required when scope=PRODUCT"
                )
            if self.sku:
                self.sku = self.sku.strip()
            if self.name:
                self.name = self.name.strip()
        else:
            self.sku = None
            self.name = None
            self.product_id = None
        return self


# ============================================================
# ANOMALY RESULT
# ============================================================
class AnomalyResult(BaseModel):
    date: str
    value: float
    score: float
    severity: str
    type: str
    explanation: str


# ============================================================
# ANOMALY RESPONSE
# ============================================================
class AnomalyResponse(BaseModel):
    """
    Response returned by /ml/anomalies
    """

    scope: ForecastScope
    product_id: Optional[int] = None

    period: AnalyticsPeriod
    count: int
    anomalies: List[AnomalyResult]

    product: Optional[ProductInfo] = None