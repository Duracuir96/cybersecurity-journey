# src/mock/mock_ml_sales.py
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional, List, Dict, Any

# -----------------------------------------------
# GLOBAL SERIES (flattened)
# -----------------------------------------------
MOCK_GLOBAL_SERIES = [
    {"date": "2025-01-01", "quantity": 12},
    {"date": "2025-01-02", "quantity": 15},
    {"date": "2025-01-03", "quantity": 14},
    {"date": "2025-01-04", "quantity": 16},
    {"date": "2025-01-05", "quantity": 18},
    {"date": "2025-01-06", "quantity": 17},
    {"date": "2025-01-07", "quantity": 20},
]

# -----------------------------------------------
# PRODUCT SERIES (by SKU)
# -----------------------------------------------
MOCK_PRODUCT_SERIES = {
    "MILK-001": [
        {"date": "2025-01-01", "quantity": 5},
        {"date": "2025-01-02", "quantity": 7},
        {"date": "2025-01-03", "quantity": 6},
        {"date": "2025-01-04", "quantity": 9},
    ],
    "BREAD-002": [
        {"date": "2025-01-01", "quantity": 14},
        {"date": "2025-01-02", "quantity": 12},
        {"date": "2025-01-03", "quantity": 13},
        {"date": "2025-01-04", "quantity": 15},
    ],
}


def _df(data):
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)

def load_mock_ml_sales(scope: str, sku: Optional[str] = None) -> pd.DataFrame:
    if scope == "GLOBAL":
        return _df(MOCK_GLOBAL_SERIES)

    if scope == "PRODUCT" and sku in MOCK_PRODUCT_SERIES:
        return _df(MOCK_PRODUCT_SERIES[sku])

    # fallback synthetic
    today = datetime.today().date()
    data = [
        {"date": (today - timedelta(days=i)).isoformat(), "quantity": 10 + i % 4}
        for i in range(14)
    ]
    return _df(data)
