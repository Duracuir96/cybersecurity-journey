# src/mock/mock_products.py

MOCK_PRODUCTS = [
    # --------------------------------------------------
    # ✅ STOCK OK (VERT)
    # --------------------------------------------------
    {
        "id": 1,
        "name": "Milk",
        "sku": "MILK-001",
        "price": 2.50,
        "stockQuantity": 25,          # >> largement au-dessus du seuil
        "lowStockThreshold": 10,
        "description": "Fresh whole milk",
        "imageUrl": "",
    },

    # --------------------------------------------------
    # ⚠️ LOW STOCK (ORANGE)
    # --------------------------------------------------
    {
        "id": 2,
        "name": "Bread",
        "sku": "BREAD-002",
        "price": 1.80,
        "stockQuantity": 4,           # < lowStockThreshold → LOW_STOCK
        "lowStockThreshold": 5,
        "description": "Whole grain bread",
        "imageUrl": "",
    },

    # --------------------------------------------------
    # ❌ OUT OF STOCK (ROUGE)
    # --------------------------------------------------
    {
        "id": 3,
        "name": "Sugar",
        "sku": "SUGAR-003",
        "price": 3.00,
        "stockQuantity": 0,           # = 0 → OUT_OF_STOCK
        "lowStockThreshold": 10,
        "description": "White sugar 1kg",
        "imageUrl": "",
    },
]
