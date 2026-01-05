# src/api/dependencies.py

from __future__ import annotations

from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional

from src.api.settings import DEV_MODE

# Import du validateur Java JWT uniquement en PROD
if not DEV_MODE:
    from src.integration.jwt_validator import jwt_validator


# =========================================================
# 🔐 DÉPENDANCE SWAGGER (VISUELLE UNIQUEMENT)
# =========================================================
# Sert à afficher le cadenas 🔒 et le bouton "Authorize"
# NE FAIT AUCUNE VALIDATION
swagger_bearer = HTTPBearer(auto_error=False)


async def swagger_auth(
    credentials: HTTPAuthorizationCredentials = Depends(swagger_bearer),
):
    """
    Dépendance utilisée UNIQUEMENT par Swagger / OpenAPI.

    - Permet l'affichage du 🔒
    - Active le bouton Authorize
    - N'effectue aucune validation
    """
    return credentials


# =========================================================
# 🔐 AUTH RÉELLE — JWT JAVA UNIFIÉ
# =========================================================
def get_current_user(
    authorization: Optional[str] = Header(None),
    required_roles: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    DEV_MODE = True:
        - Aucun token requis
        - Retourne toujours un utilisateur factice
        - Permet le dev frontend sans backend Java

    DEV_MODE = False:
        - Header Authorization requis (Bearer <token>)
        - Validation du JWT Java
        - Forward du token vers les clients Java
        - Vérification des rôles
    """

    # ---------------------------------------------------------
    # DEV MODE → BYPASS JWT
    # ---------------------------------------------------------
    if DEV_MODE:
        return {
            "user_id": "dev-user",
            "username": "dev",
            "roles": ["admin"],
            "token": "dev-token",
            "mode": "DEV",
        }

    # ---------------------------------------------------------
    # PROD MODE → JWT REQUIS
    # ---------------------------------------------------------
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format (expected Bearer token)",
        )

    # Extraction du token brut
    token = authorization.replace("Bearer ", "").strip()

    # Validation via Java JWT Validator
    payload = jwt_validator.validate(token)

    user: Dict[str, Any] = {
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "roles": payload.get("roles", []),
        "token": token,
        "mode": "PROD",
    }

    # ---------------------------------------------------------
    # Vérification des rôles (si requis)
    # ---------------------------------------------------------
    if required_roles:
        if not any(role in user["roles"] for role in required_roles):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )

    return user
