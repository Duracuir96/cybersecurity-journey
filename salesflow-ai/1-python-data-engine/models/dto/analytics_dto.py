# src/models/dto/analytics_dto.py

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# ENUMS
# ============================================================
class AnalyticsPeriod(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"


class ProductStockStatus(str, Enum):
    ok = "OK"
    low = "LOW_STOCK"
    out = "OUT_OF_STOCK"
    dead = "DEAD_STOCK"


# ============================================================
# STOCK ANALYTICS
# ============================================================
class ProductStockSnapshot(BaseModel):
    product_id: int
    name: str
    current_stock: float
    min_stock: float
    unit_price: float
    stock_value: float

    last_sale_date: Optional[date] = None
    coverage_days: Optional[float] = None
    status: ProductStockStatus = ProductStockStatus.ok


class StockKPI(BaseModel):
    total_stock_value: float
    out_of_stock_count: int
    low_stock_count: int
    low_stock_ratio: float

    urgent_reorder_count: int
    dead_stock_count: int

    rotation_per_year: Optional[float] = None
    avg_coverage_days: Optional[float] = None


class StockAnalyticsResponse(BaseModel):
    period: AnalyticsPeriod
    period_label: str = Field(..., description="Human readable period label")
    as_of: date
    kpis: StockKPI
    critical_products: List[ProductStockSnapshot]

    # LE FIX CRITIQUE QUI FAISAIT TOUT RENTRER EN null
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# SALES ANALYTICS
# ============================================================
class DailySalesPoint(BaseModel):
    date: date
    total_revenue: float
    total_quantity: float
    total_transactions: int


class TopProductSales(BaseModel):
    product_id: int
    name: str
    total_quantity: float
    revenue: float
    share_of_revenue: float


class SalesKPI(BaseModel):
    total_revenue: float
    total_quantity: float
    total_transactions: int
    average_ticket: float
    top_products: List[TopProductSales]
    seasonal_hint: Optional[str] = None


class SalesAnalyticsResponse(BaseModel):
    period: AnalyticsPeriod
    start_date: date
    end_date: date
    period_label: str = Field(..., description="Human readable label")
    kpis: SalesKPI
    daily: List[DailySalesPoint]

    # Même fix ici
    model_config = ConfigDict(from_attributes=True)