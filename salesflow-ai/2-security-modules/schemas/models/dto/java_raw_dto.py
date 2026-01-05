from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ====================================================
# PRODUCT – ProductDto (Java)
# ====================================================
class JavaProductDto(BaseModel):
    id: int
    name: str
    sku: str
    price: float
    stockQuantity: int
    lowStockThreshold: int
    description: Optional[str] = None
    imageUrl: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


# ====================================================
# INVENTORY – InventoryResponse (Java)
# ====================================================
class JavaInventoryItemDto(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    quantity: int
    price: float
    cost: float
    category: Optional[str]
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(extra="ignore")


# ====================================================
# SALE ITEM – SaleItemResponse (Java)
# ====================================================
class JavaSaleItemDto(BaseModel):
    productId: int
    productName: str
    sku: str
    quantity: int
    unitPrice: float
    subtotal: float

    model_config = ConfigDict(extra="ignore")


# ====================================================
# SALE – SaleResponse (Java)
# ====================================================
class JavaSaleDto(BaseModel):
    id: int
    saleDate: datetime
    totalAmount: float
    items: List[JavaSaleItemDto]

    model_config = ConfigDict(extra="ignore")


# ====================================================
# SALES HISTORY FLAT – ML / Analytics
# ====================================================
class JavaSalesHistoryFlatDto(BaseModel):
    date: str
    quantity: int

    model_config = ConfigDict(extra="ignore")


# ====================================================
# SALES — BULK CREATE (Swagger-aligned)
# ====================================================

class JavaSaleItemCreateDto(BaseModel):
    productId: int
    sku: str
    quantity: int

    model_config = ConfigDict(extra="ignore")


class JavaCreateSaleRequestDto(BaseModel):
    """
    Correspond EXACTEMENT à CreateSaleRequest côté Java (Swagger)
    """
    items: List[JavaSaleItemCreateDto]

    model_config = ConfigDict(extra="ignore")
