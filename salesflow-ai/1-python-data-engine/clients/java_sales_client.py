from __future__ import annotations

import os
import logging
from typing import Any, List, Optional

import httpx
from fastapi import HTTPException

from src.models.dto.java_raw_dto import (
    JavaSaleDto,
    JavaSalesHistoryFlatDto,
    JavaCreateSaleRequestDto,
    JavaSaleItemCreateDto,
)

from src.mock.mock_sales import (
    MOCK_RECENT_SALES,
    MOCK_SALES_HISTORY,
)
from src.api.settings import DEV_MODE

JAVA_API_URL = os.getenv(
    "JAVA_API_URL",
    "http://localhost:8080/api/v1"
).rstrip("/")

logger = logging.getLogger(__name__)


class JavaSalesClient:
    """
    Client STRICTEMENT aligné sur les endpoints Java Sales.
    Aucune logique métier ici.
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.client = httpx.AsyncClient(timeout=15.0)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _normalize(self, raw: Any) -> List[dict]:
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict):
            for key in ("data", "sales", "content", "items", "result"):
                if key in raw and isinstance(raw[key], list):
                    return raw[key]
            return [raw]
        return []

    async def _get(self, endpoint: str) -> Any:
        url = f"{JAVA_API_URL}{endpoint}"
        logger.info(f"[JavaSalesClient] GET {url} (DEV_MODE={DEV_MODE})")

        if DEV_MODE:
            if endpoint == "/sales/recent":
                return MOCK_RECENT_SALES
            if endpoint == "/sales/history":
                return MOCK_SALES_HISTORY
            return []

        try:
            resp = await self.client.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.exception("Java Sales API error")
            raise HTTPException(
                status_code=502,
                detail=f"Java Sales API error: {str(e)}",
            )

    # --------------------------------------------------
    # SALES — READ
    # --------------------------------------------------
    async def get_recent_sales(self) -> List[JavaSaleDto]:
        raw = await self._get("/sales/recent")
        return [JavaSaleDto.model_validate(s) for s in self._normalize(raw)]

    async def get_sales_history(self) -> List[JavaSaleDto]:
        raw = await self._get("/sales/history")
        return [JavaSaleDto.model_validate(s) for s in self._normalize(raw)]

    async def get_sales_history_by_sku(
        self,
        sku: str,
    ) -> List[JavaSalesHistoryFlatDto]:
        raw = await self._get(f"/sales/history/by-sku/{sku}")
        return [
            JavaSalesHistoryFlatDto.model_validate(p)
            for p in self._normalize(raw)
        ]

    async def get_sales_history_by_name(
        self,
        name: str,
    ) -> List[JavaSalesHistoryFlatDto]:
        raw = await self._get(f"/sales/history/by-name/{name}")
        return [
            JavaSalesHistoryFlatDto.model_validate(p)
            for p in self._normalize(raw)
        ]

    # --------------------------------------------------
    # SALES — BULK CREATE (Excel / CSV Import)
    # --------------------------------------------------
    async def create_bulk_sales(
        self,
        rows: List[dict],
    ) -> dict:
        """
        POST /sales/bulk

        Swagger expects:
        [
          { "items": [ { productId, sku, quantity } ] }
        ]
        """

        url = f"{JAVA_API_URL}/sales/bulk"

        # 🔒 Swagger-aligned payload
        payload = [
            JavaCreateSaleRequestDto(
                items=[JavaSaleItemCreateDto(**row)]
            ).model_dump()
            for row in rows
        ]

        logger.debug("JAVA BULK PAYLOAD SENT: %s", payload)

        if DEV_MODE:
            return {
                "imported": len(payload),
                "failed": 0,
                "items": payload,
            }

        try:
            resp = await self.client.post(
                url,
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            logger.exception("Java Sales BULK API error")
            raise HTTPException(
                status_code=502,
                detail=f"Java Sales BULK API error: {str(e)}",
            )

    async def close(self):
        await self.client.aclose()
