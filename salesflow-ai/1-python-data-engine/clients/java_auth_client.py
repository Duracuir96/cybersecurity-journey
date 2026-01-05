import httpx
import asyncio
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class JavaAPIClient:
    """
    Async HTTP client to communicate with the Java Spring Boot API.
    Automatically forwards Java-issued JWT token.
    Includes retry logic, error handling, timeout, and JSON processing.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080/api/v1",
        timeout: float = 10.0,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    # --------------------------------------------------------
    # INTERNAL HTTP REQUEST WITH RETRY LOGIC
    # --------------------------------------------------------
    async def _request(
        self,
        method: str,
        endpoint: str,
        token: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json,
                        params=params,
                    )

                # Success
                if response.status_code < 400:
                    return response.json()

                # Unauthorized
                if response.status_code == 401:
                    raise HTTPException(
                        status_code=401,
                        detail="Unauthorized — Java API rejected the token"
                    )

                # Forbidden
                if response.status_code == 403:
                    raise HTTPException(
                        status_code=403,
                        detail="Forbidden — insufficient permissions"
                    )

                # Other client/server errors
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Java API error: {response.text}"
                )

            except (httpx.ConnectError, httpx.NetworkError, httpx.ReadTimeout) as e:
                last_exception = e

                if attempt == self.max_retries:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Java API unreachable after retries: {str(e)}"
                    )

                # Backoff delay
                await asyncio.sleep(0.5 * attempt)

            except Exception as e:
                last_exception = e

                if attempt == self.max_retries:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Unexpected error contacting Java API: {str(e)}"
                    )

        raise last_exception or HTTPException(500, "Unknown client error")

    # --------------------------------------------------------
    # PUBLIC GET and POST METHODS
    # --------------------------------------------------------

    async def get(self, endpoint: str, token: str, params: Dict[str, Any] = None):
        return await self._request("GET", endpoint, token, params=params)

    async def post(self, endpoint: str, token: str, data: Dict[str, Any]):
        return await self._request("POST", endpoint, token, json=data)

    # Example specialized method:
    async def fetch_sales_data(self, token: str, start_date: str, end_date: str):
        """
        GET /sales?start_date=...&end_date=...
        """
        return await self.get(
            "sales",
            token,
            params={"start_date": start_date, "end_date": end_date}
        )

    async def batch_insert_sales(self, token: str, sales_payload: Dict[str, Any]):
        """
        POST /sales/batch
        """
        return await self.post("sales/batch", token, data=sales_payload)


# Global client
java_api_client = JavaAPIClient()
