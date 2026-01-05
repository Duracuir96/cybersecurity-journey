# src/mock/mock_inventory_stock.py

from src.mock.mock_products import MOCK_PRODUCTS

MOCK_INVENTORY = [
    {
        "id": p["id"],                     # productId
        "sku": p["sku"],
        "name": p["name"],
        "description": p.get("description"),
        "quantity": (
            25 if p["id"] == 1 else
            8 if p["id"] == 2 else
            0
        ),
        "price": p["price"],
        "cost": round(p["price"] * 0.6, 2),
        "category": None,
        "createdAt": "2025-01-01T00:00:00",
        "updatedAt": "2025-12-13T12:00:00",
    }
    for p in MOCK_PRODUCTS
]
