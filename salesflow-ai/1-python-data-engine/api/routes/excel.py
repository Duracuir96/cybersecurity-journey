from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, UploadFile, Depends, HTTPException

from src.api.dependencies import get_current_user, swagger_auth
from src.data.file_processor import process_sales_upload_to_canonical
from src.clients.java_sales_client import JavaSalesClient


router = APIRouter(
    prefix="/api/v1/excel",
    tags=["Excel Import"],
    dependencies=[Depends(swagger_auth)],
)


# -----------------------------------------------------------
# TOKEN EXTRACTOR — EXACTEMENT COMME ml.py
# -----------------------------------------------------------
def _extract_token(current_user: Any) -> Optional[str]:
    if isinstance(current_user, dict):
        return (
            current_user.get("token")
            or current_user.get("access_token")
            or current_user.get("raw_token")
            or current_user.get("jwt")
        )
    return None


# -----------------------------------------------------------
# IMPORT SALES — EXCEL / CSV → CANONICAL → JAVA
# -----------------------------------------------------------
@router.post("/import-sales")
async def import_sales(
    file: UploadFile,
    current_user=Depends(get_current_user),
):
    """
    Import sales from Excel / CSV.

    Pipeline:
    Excel → validate + canonicalize → Java /sales/bulk
    """

    # --------------------------------------------------
    # 1. Extract token (AUTH)
    # --------------------------------------------------
    token = _extract_token(current_user)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token",
        )

    # --------------------------------------------------
    # 2. Parse + validate + canonicalize Excel
    # --------------------------------------------------
    result = await process_sales_upload_to_canonical(
        file=file,
        token=token,
    )

    if result["errors"]:
        return {
            "status": "failed",
            "errors": result["errors"],
            "total_rows": result["total_rows"],
            "valid_rows": result["valid_rows"],
        }

    if not result["items"]:
        raise HTTPException(
            status_code=400,
            detail="No valid sales found in uploaded file",
        )

    # --------------------------------------------------
    # 3. Send canonical payload to Java (/sales/bulk)
    # --------------------------------------------------
    sales_client = JavaSalesClient(token)

    try:
        # ✅ FIX ICI : appel POSITIONNEL (pas items=)
        java_response = await sales_client.create_bulk_sales(
            result["items"]
        )
    finally:
        await sales_client.close()

    # --------------------------------------------------
    # 4. Final response
    # --------------------------------------------------
    return {
        "status": "success",
        "total_rows": result["total_rows"],
        "valid_rows": result["valid_rows"],
        "imported": len(result["items"]),
        "java_response": java_response,
    }
