# src/mock/mock_sales.py
from datetime import datetime

# ------------------------------------------------
# RECENT SALES (dashboard)
# ------------------------------------------------
MOCK_RECENT_SALES = [
    {
        "id": 101,
        "saleDate": datetime(2025, 12, 13, 14, 30),
        "totalAmount": 55.0,
        "items": [
            {
                "productId": 1,
                "productName": "Milk",
                "sku": "MILK-001",
                "quantity": 2,
                "unitPrice": 2.50,
                "subtotal": 5.00,
            },
            {
                "productId": 2,
                "productName": "Bread",
                "sku": "BREAD-002",
                "quantity": 1,
                "unitPrice": 1.80,
                "subtotal": 1.80,
            },
        ],
    }
]

# ------------------------------------------------
# SALES HISTORY (GLOBAL) — /sales/history
# ------------------------------------------------
MOCK_SALES_HISTORY = [
    {
        "id": 201,
        "saleDate": datetime(2025, 12, 10),
        "totalAmount": 15.0,
        "items": [
            {
                "productId": 1,
                "productName": "Milk",
                "sku": "MILK-001",
                "quantity": 6,
                "unitPrice": 2.50,
                "subtotal": 15.00,
            }
        ],
    },
    {
        "id": 202,
        "saleDate": datetime(2025, 12, 5),
        "totalAmount": 7.20,
        "items": [
            {
                "productId": 2,
                "productName": "Bread",
                "sku": "BREAD-002",
                "quantity": 4,
                "unitPrice": 1.80,
                "subtotal": 7.20,
            }
        ],
    },
    {
        "id": 203,
        "saleDate": datetime(2025, 11, 20),
        "totalAmount": 3.00,
        "items": [
            {
                "productId": 3,
                "productName": "Sugar",
                "sku": "SUGAR-003",
                "quantity": 1,
                "unitPrice": 3.00,
                "subtotal": 3.00,
            }
        ],
    },
    {
  "id": 999,
  "saleDate": datetime.today(),
  "totalAmount": 20.0,
  "items": [
    {
      "productId": 1,
      "productName": "Milk",
      "sku": "MILK-001",
      "quantity": 8,
      "unitPrice": 2.5,
      "subtotal": 20.0
    }
  ]
}
]
