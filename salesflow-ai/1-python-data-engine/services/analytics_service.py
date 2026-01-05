# src/services/analytics_service.py
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from collections import defaultdict

from src.models.dto.analytics_dto import (
    AnalyticsPeriod,
    StockAnalyticsResponse,
    StockKPI,
    ProductStockSnapshot,
    ProductStockStatus,
    SalesAnalyticsResponse,
    SalesKPI,
    DailySalesPoint,
    TopProductSales,
)

from src.clients.java_products_client import JavaProductsClient
from src.clients.java_sales_client import JavaSalesClient

from src.services.enrichment_service import (
    enrich_inventory_with_products_and_sales,
)

from src.data.cache_manager import get_cache, cache_analytics


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def to_dict(obj) -> dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(by_alias=True)
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return {}


def parse_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(str(value).split("Z")[0]).date()
    except Exception:
        return None


def compute_period_dates(period: AnalyticsPeriod) -> Tuple[date, date]:
    today = date.today()
    if period == AnalyticsPeriod.daily:
        return today, today
    if period == AnalyticsPeriod.weekly:
        return today - timedelta(days=6), today
    if period == AnalyticsPeriod.monthly:
        return today.replace(day=1), today
    if period == AnalyticsPeriod.quarterly:
        return today - timedelta(days=89), today
    return today, today


def _period_label_fr(period: AnalyticsPeriod) -> str:
    return {
        AnalyticsPeriod.daily: "Aujourd’hui",
        AnalyticsPeriod.weekly: "7 derniers jours",
        AnalyticsPeriod.monthly: "Mois en cours",
        AnalyticsPeriod.quarterly: "90 derniers jours",
    }.get(period, "")


# ------------------------------------------------------------
# STOCK ANALYTICS (GLOBAL)
# ------------------------------------------------------------
async def compute_stock_analytics(
    period: AnalyticsPeriod,
    token: Optional[str],
) -> StockAnalyticsResponse:

    today = date.today()
    cache_key = f"analytics:stock:{period.value}"

    cached = get_cache(cache_key)
    if cached:
        try:
            return StockAnalyticsResponse(**cached)
        except Exception:
            pass

    prod = JavaProductsClient(token)
    sales = JavaSalesClient(token)

    try:
        products = [to_dict(p) for p in await prod.get_all_products()]
        sales_history = [to_dict(s) for s in await sales.get_sales_history()]
    finally:
        await prod.close()
        await sales.close()

    cutoff = today - timedelta(days=89)

    qty_by_day = defaultdict(lambda: defaultdict(float))
    last_sale: Dict[int, date] = {}

    for sale in sales_history:
        d = parse_date(sale.get("saleDate"))
        if not d or d < cutoff:
            continue

        for item in sale.get("items", []) or []:
            it = to_dict(item)
            pid = it.get("productId")
            if pid is None:
                continue

            pid = int(pid)
            qty = float(it.get("quantity", 0))
            if qty <= 0:
                continue

            qty_by_day[pid][d] += qty
            last_sale[pid] = max(d, last_sale.get(pid, d))

    avg_daily = {}
    for pid, days in qty_by_day.items():
        span = (max(days) - min(days)).days + 1
        avg_daily[pid] = sum(days.values()) / max(span, 1)

    inventory_rows = [
        {
            "productId": p["id"],
            "currentStock": p.get("stockQuantity", 0),
            "minStock": p.get("lowStockThreshold", 0),
        }
        for p in products
    ]

    enriched = enrich_inventory_with_products_and_sales(
        inventory_rows,
        products,
        last_sale,
        avg_daily,
    )

    snapshots = [ProductStockSnapshot(**e) for e in enriched]

    kpis = StockKPI(
        total_stock_value=round(sum(s.stock_value for s in snapshots), 2),
        out_of_stock_count=sum(1 for s in snapshots if s.current_stock <= 0),
        low_stock_count=sum(
            1 for s in snapshots if s.status == ProductStockStatus.low.value
        ),
        low_stock_ratio=round(
            sum(1 for s in snapshots if s.status == ProductStockStatus.low.value)
            / max(len(snapshots), 1)
            * 100,
            1,
        ),
        urgent_reorder_count=sum(
            1 for s in snapshots if s.coverage_days and s.coverage_days < 7
        ),
        dead_stock_count=sum(
            1 for s in snapshots if s.status == ProductStockStatus.dead.value
        ),
        rotation_per_year=None,
        avg_coverage_days=None,
    )

    response = StockAnalyticsResponse(
        period=period,
        period_label=_period_label_fr(period),
        as_of=today,
        kpis=kpis,
        critical_products=[
            s for s in snapshots if s.status != ProductStockStatus.ok.value
        ],
    )

    cache_analytics(cache_key, response)
    return response


# ------------------------------------------------------------
# SALES ANALYTICS (GLOBAL)
# ------------------------------------------------------------
async def compute_sales_analytics(
    period: AnalyticsPeriod,
    token: Optional[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> SalesAnalyticsResponse:

    if not start_date or not end_date:
        start_date, end_date = compute_period_dates(period)

    cache_key = f"analytics:sales:{period.value}:{start_date}:{end_date}"

    cached = get_cache(cache_key)
    if cached:
        try:
            return SalesAnalyticsResponse(**cached)
        except Exception:
            pass

    prod = JavaProductsClient(token)
    sales = JavaSalesClient(token)

    try:
        products = [to_dict(p) for p in await prod.get_all_products()]
        sales_history = [to_dict(s) for s in await sales.get_sales_history()]
    finally:
        await prod.close()
        await sales.close()

    product_map = {p["id"]: p for p in products}

    daily = defaultdict(lambda: {"rev": 0.0, "qty": 0.0, "tx": 0})
    agg = defaultdict(lambda: {"rev": 0.0, "qty": 0.0})

    for sale in sales_history:
        d = parse_date(sale.get("saleDate"))
        if not d or d < start_date or d > end_date:
            continue

        total_amount = float(sale.get("totalAmount", 0))
        daily[d]["rev"] += total_amount
        daily[d]["tx"] += 1

        for item in sale.get("items", []) or []:
            it = to_dict(item)
            pid = it.get("productId")
            if pid is None:
                continue

            pid = int(pid)
            qty = float(it.get("quantity", 0))
            price = float(
                it.get("unitPrice")
                or product_map.get(pid, {}).get("price", 0)
            )

            agg[pid]["qty"] += qty
            agg[pid]["rev"] += qty * price
            daily[d]["qty"] += qty

    daily_points: List[DailySalesPoint] = []
    total_rev = total_qty = total_tx = 0.0

    for d in sorted(daily):
        p = daily[d]

        daily_points.append(
            DailySalesPoint(
                date=d,
                total_revenue=round(p["rev"], 2),
                total_quantity=round(p["qty"], 2),
                total_transactions=int(p["tx"]),
            )
        )

        total_rev += p["rev"]
        total_qty += p["qty"]
        total_tx += p["tx"]

    top_products: List[TopProductSales] = sorted(
        [
            TopProductSales(
                product_id=pid,
                name=product_map[pid]["name"],
                total_quantity=round(v["qty"], 2),
                revenue=round(v["rev"], 2),
                share_of_revenue=(
                    v["rev"] / total_rev * 100 if total_rev else 0.0
                ),
            )
            for pid, v in agg.items()
            if pid in product_map
        ],
        key=lambda x: x.revenue,
        reverse=True,
    )[:5]

    kpis = SalesKPI(
        total_revenue=round(total_rev, 2),
        total_quantity=round(total_qty, 2),
        total_transactions=int(total_tx),
        average_ticket=round(total_rev / total_tx, 2) if total_tx else 0.0,
        top_products=top_products,
        seasonal_hint=None,
    )

    response = SalesAnalyticsResponse(
        period=period,
        start_date=start_date,
        end_date=end_date,
        period_label=_period_label_fr(period),
        kpis=kpis,
        daily=daily_points,
    )

    cache_analytics(cache_key, response)
    return response
