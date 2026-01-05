from __future__ import annotations

import os
import logging
from typing import Any, List, Optional

import httpx
from fastapi import HTTPException

from src.api.settings import DEV_MODE
from src.models.dto.java_raw_dto import JavaInventoryItemDto
from src.mock.mock_inventory_stock import MOCK_INVENTORY

JAVA_API_URL = os.getenv(
    "JAVA_API_URL",
    "http://localhost:8080/api/v1"
).rstrip("/")

logger = logging.getLogger(__name__)


class JavaInventoryClient:
    """
    Client aligné sur InventoryController Java.

    Endpoints exposés :
    - GET /inventory
    - GET /inventory/by-sku/{sku}
    - GET /inventory/by-name/{name}
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
        logger.info(f"[JavaInventoryClient] GET {url} (DEV_MODE={DEV_MODE})")

        if DEV_MODE:
            return MOCK_INVENTORY

        try:
            resp = await self.client.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.exception("Java Inventory API error")
            raise HTTPException(
                status_code=502,
                detail=f"Java Inventory API error: {str(e)}",
            )

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    async def get_inventory(self) -> List[JavaInventoryItemDto]:
        raw = await self._get("/inventory")
        return [
            JavaInventoryItemDto.model_validate(i)
            for i in self._normalize(raw)
        ]

    async def get_inventory_by_sku(self, sku: str) -> JavaInventoryItemDto:
        if DEV_MODE:
            for i in MOCK_INVENTORY:
                if i["sku"] == sku:
                    return JavaInventoryItemDto.model_validate(i)
            raise HTTPException(404, f"Inventory with sku={sku} not found")

        raw = await self._get(f"/inventory/by-sku/{sku}")
        return JavaInventoryItemDto.model_validate(raw)

    async def get_inventory_by_name(self, name: str) -> JavaInventoryItemDto:
        if DEV_MODE:
            for i in MOCK_INVENTORY:
                if i["name"].lower() == name.lower():
                    return JavaInventoryItemDto.model_validate(i)
            raise HTTPException(404, f"Inventory with name={name} not found")

        raw = await self._get(f"/inventory/by-name/{name}")
        return JavaInventoryItemDto.model_validate(raw)

    async def close(self):
        await self.client.aclose()
