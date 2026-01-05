# src/models/report.py

from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import date


# ============================================================
# REPORT REQUEST DTO
# ============================================================
class ReportRequest(BaseModel):
    report_type: Literal["sales", "financial", "stock"]
    format: Literal["pdf", "excel"]
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_charts: bool = True


# ============================================================
# SALES REPORT MODELS
# ============================================================
class ProductSummary(BaseModel):
    product_id: int
    name: str
    total_sold: float
    revenue: float


class SalesAnalytics(BaseModel):
    total_sales_amount: float
    total_transactions: int
    average_ticket: float
    top_products: List[ProductSummary]
    date: str  # Keep string for PDF compatibility


# ============================================================
# FINANCIAL REPORT MODELS
# ============================================================
class FinancialAnalytics(BaseModel):
    total_revenue: float
    total_cost: float
    profit: float
    profit_margin: float
    date: str


# ============================================================
# STOCK REPORT MODELS
# ============================================================
class StockReportItem(BaseModel):
    product_id: int
    name: str
    current_stock: float
    stock_value: float
    status: str


class StockReport(BaseModel):
    total_stock_value: float
    out_of_stock_count: int
    low_stock_count: int
    dead_stock_count: int
    items: List[StockReportItem]
    date: str


# ============================================================
# GENERATED REPORT RESPONSE
# ============================================================
class GeneratedReportResponse(BaseModel):
    report_id: str
    filename: str
    filepath: str
    status: Literal["ready", "failed"]
    email_sent: bool = False

    mode: str
    user: dict

    download_url: str
