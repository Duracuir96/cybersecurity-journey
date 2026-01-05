from __future__ import annotations

import os
import logging
from typing import Any, List, Optional

import httpx
from fastapi import HTTPException

from src.api.settings import DEV_MODE
from src.models.dto.java_raw_dto import JavaProductDto
from src.mock.mock_products import MOCK_PRODUCTS

JAVA_API_URL = os.getenv(
    "JAVA_API_URL",
    "http://localhost:8080/api/v1"
).rstrip("/")

logger = logging.getLogger(__name__)


class JavaProductsClient:
    """
    Client STRICTEMENT aligné sur ProductController Java.

    Endpoints exposés :
    - GET /products
    - GET /products/{id}
    - GET /products/by-sku/{sku}
    - GET /products/by-name/{name}
    - GET /products/low-stock

    ⚠️ Aucune logique métier ici.
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.client = httpx.AsyncClient(timeout=10.0)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _normalize(self, raw: Any) -> List[dict]:
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict):
            for key in ("data", "content", "items", "result"):
                if key in raw and isinstance(raw[key], list):
                    return raw[key]
            return [raw]
        return []

    async def _get(self, endpoint: str):
        url = f"{JAVA_API_URL}{endpoint}"
        logger.info(f"[JavaProductsClient] GET {url} (DEV_MODE={DEV_MODE})")

        if DEV_MODE:
            return MOCK_PRODUCTS

        try:
            resp = await self.client.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.exception("Java Product API error")
            raise HTTPException(
                status_code=502,
                detail=f"Java Product API error: {str(e)}",
            )

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    async def get_all_products(self) -> List[JavaProductDto]:
        raw = await self._get("/products")
        return [
            JavaProductDto.model_validate(p)
            for p in self._normalize(raw)
        ]

    async def get_product_by_id(self, product_id: int) -> JavaProductDto:
        if DEV_MODE:
            for p in MOCK_PRODUCTS:
                if p["id"] == product_id:
                    return JavaProductDto.model_validate(p)
            raise HTTPException(404, f"Product with id={product_id} not found")

        raw = await self._get(f"/products/by-id/{id}")
        return JavaProductDto.model_validate(raw)

    async def get_product_by_sku(self, sku: str) -> JavaProductDto:
        if DEV_MODE:
            for p in MOCK_PRODUCTS:
                if p["sku"] == sku:
                    return JavaProductDto.model_validate(p)
            raise HTTPException(404, f"Product with sku={sku} not found")

        raw = await self._get(f"/products/by-sku/{sku}")
        return JavaProductDto.model_validate(raw)

    async def get_product_by_name(self, name: str) -> JavaProductDto:
        if DEV_MODE:
            for p in MOCK_PRODUCTS:
                if p["name"].lower() == name.lower():
                    return JavaProductDto.model_validate(p)
            raise HTTPException(404, f"Product with name={name} not found")

        raw = await self._get(f"/products/by-name/{name}")
        return JavaProductDto.model_validate(raw)

    async def get_low_stock_products(self) -> List[JavaProductDto]:
        if DEV_MODE:
            return [
                JavaProductDto.model_validate(p)
                for p in MOCK_PRODUCTS
                if p.get("stockQuantity", 0) <= p.get("lowStockThreshold", 0)
            ]

        raw = await self._get("/products/low-stock")
        return [
            JavaProductDto.model_validate(p)
            for p in self._normalize(raw)
        ]

    async def close(self):
        await self.client.aclose()
