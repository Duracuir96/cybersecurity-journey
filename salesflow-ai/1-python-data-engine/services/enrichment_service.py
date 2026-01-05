from __future__ import annotations

"""
Enrichment layer:
- Joins raw Java data (sales, products, inventory)
- Produces analytics-ready dicts
- Used by analytics_service & report_service
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime

from src.models.dto.analytics_dto import ProductStockStatus


# ------------------------------------------------------------------ #
# Helper ultra-défensif – marche avec dict, Pydantic, objets Java...
# ------------------------------------------------------------------ #
def _to_dict(item: Any) -> Dict[str, Any]:
    """Convertit n'importe quoi en dict pur"""
    if item is None:
        return {}
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):  # Pydantic v2
        return item.model_dump(by_alias=True)
    if hasattr(item, "__dict__"):
        return item.__dict__
    try:
        return dict(item)
    except Exception:
        return {}


def _parse_date(value: Any) -> Optional[date]:
    """Parse dates venant de Java, mocks ou JSON (ultra robuste)"""
    if value is None:
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()

    cleaned: Optional[str] = None
    try:
        cleaned = str(value).replace("Z", "+00:00").split("+")[0].split(".")[0]
        return datetime.fromisoformat(cleaned).date()
    except Exception:
        try:
            if cleaned:
                return datetime.strptime(cleaned, "%Y-%m-%d").date()
        except Exception:
            return None
    return None


def _compute_stock_status(
    current_stock: float,
    min_stock: float,
    last_sale_dt: Optional[date],
    today: Optional[date] = None,
) -> ProductStockStatus:
    """Détermine le statut stock selon règles métier"""
    if today is None:
        today = date.today()

    if current_stock <= 0:
        return ProductStockStatus.out
    if current_stock < max(min_stock, 1):
        return ProductStockStatus.low
    if last_sale_dt and (today - last_sale_dt).days >= 90:
        return ProductStockStatus.dead
    return ProductStockStatus.ok


# ------------------------------------------------------------------ #
# 1. ENRICHISSEMENT DES VENTES (frontend, rapports, etc.)
# ------------------------------------------------------------------ #
def enrich_sales_items_with_products(
    sale_items: List[Any],
    products: List[Any],
) -> List[Dict[str, Any]]:

    product_map = {
        p.get("id"): p
        for p in (_to_dict(p) for p in products)
        if p.get("id") is not None
    }

    enriched: List[Dict[str, Any]] = []

    for item in sale_items:
        it = _to_dict(item)
        pid = it.get("productId")
        qty = float(it.get("quantity", 0))
        price = it.get("price")

        prod = product_map.get(pid, {})
        unit_price = float(price) if price is not None else float(prod.get("price", 0.0))

        enriched.append({
            "productId": pid,
            "productName": prod.get("name", "Unknown"),
            "sku": prod.get("sku"),
            "unitPrice": unit_price,
            "quantity": qty,
            "subtotal": round(qty * unit_price, 2),
        })

    return enriched


def enrich_today_sales(
    today_sales: Any,
    products: List[Any],
) -> Dict[str, Any]:

    data = _to_dict(today_sales)
    items = data.get("items", [])

    enriched_items = enrich_sales_items_with_products(items, products)

    return {
        "saleDate": _parse_date(data.get("saleDate") or data.get("date")),
        "totalAmount": round(float(data.get("totalAmount") or data.get("total", 0.0)), 2),
        "totalTransactions": int(data.get("count", 0)),
        "items": enriched_items,
    }


# ------------------------------------------------------------------ #
# 2. CONSTRUCTION DE LA DERNIÈRE DATE DE VENTE PAR PRODUIT
# ------------------------------------------------------------------ #
def build_last_sale_map(
    sales_history_by_product: Dict[int, List[Any]]
) -> Dict[int, Optional[date]]:

    last_map: Dict[int, Optional[date]] = {}

    for pid, hist in sales_history_by_product.items():
        last_dt: Optional[date] = None
        for row in hist:
            r = _to_dict(row)
            d = _parse_date(r.get("date"))
            if d and (last_dt is None or d > last_dt):
                last_dt = d
        last_map[pid] = last_dt

    return last_map


# ------------------------------------------------------------------ #
# 3. ENRICHISSEMENT INVENTAIRE + INDICATEURS STOCK
# ------------------------------------------------------------------ #
def enrich_inventory_with_products_and_sales(
    inventory_rows: List[Any],
    products: List[Any],
    last_sale_by_product: Optional[Dict[int, Optional[date]]] = None,
    avg_daily_sales_by_product: Optional[Dict[int, float]] = None,
) -> List[Dict[str, Any]]:

    inventory = [_to_dict(inv) for inv in inventory_rows]
    products = [_to_dict(p) for p in products]

    product_map = {p.get("id"): p for p in products if p.get("id") is not None}
    last_map = last_sale_by_product or {}
    avg_map = avg_daily_sales_by_product or {}

    today = date.today()
    enriched: List[Dict[str, Any]] = []

    for inv in inventory:
        pid = inv.get("productId") or inv.get("id")
        if pid is None:
            continue

        current_stock = float(
            inv.get("currentStock") or inv.get("quantity") or 0
        )
        min_stock = float(
            inv.get("minStock") or inv.get("lowStockThreshold") or 0
        )

        prod = product_map.get(pid, {})
        price = float(prod.get("price", 0.0))
        last_sale_date = last_map.get(pid)

        avg_daily = float(avg_map.get(pid, 0.0))
        coverage_days: Optional[float] = None
        if avg_daily > 0 and current_stock > 0:
            coverage_days = current_stock / avg_daily

        status = _compute_stock_status(
            current_stock=current_stock,
            min_stock=min_stock,
            last_sale_dt=last_sale_date,
            today=today,
        )

        enriched.append({
            "product_id": pid,
            "name": prod.get("name", "Inconnu"),
            "current_stock": current_stock,
            "min_stock": min_stock,
            "unit_price": price,
            "stock_value": round(current_stock * price, 2),
            "last_sale_date": last_sale_date,
            "coverage_days": round(coverage_days, 1) if coverage_days is not None else None,
            "status": status.value,
        })

    return enriched
