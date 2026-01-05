# src/integration/jwt_validator.py

from fastapi import HTTPException, Header
from jose import jwt, JWTError
from jose.constants import ALGORITHMS
from typing import Dict, Any
from src.api.settings import JAVA_JWT_SECRET


class JavaJWTValidator:
    """
    Validates JWT tokens issued by the Java Spring Boot backend.
    Uses HS256 shared secret and forces issuer = 'salesflow-app'.
    """

    def __init__(self):
        self.secret_key = JAVA_JWT_SECRET
        self.algorithm = ALGORITHMS.HS256
        self.expected_issuer = "salesflow-app"

        if not self.secret_key:
            raise RuntimeError("JAVA_JWT_SECRET missing in environment variables.")

    # --------------------------------------------------------------
    # INTERNAL: Validate JWT payload structure
    # --------------------------------------------------------------
    def validate(self, token: str) -> Dict[str, Any]:
        if not token:
            raise HTTPException(401, "Missing token")

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.expected_issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iss": True,
                }
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expired")

        except jwt.JWTClaimsError as e:
            raise HTTPException(401, f"Invalid claims: {str(e)}")

        except JWTError:
            raise HTTPException(401, "Malformed JWT token")

        except Exception as e:
            raise HTTPException(500, f"Unexpected JWT validation error: {str(e)}")

    # --------------------------------------------------------------
    # FASTAPI DEPENDENCY → Accepts Authorization: Bearer <token>
    # --------------------------------------------------------------
    async def validate_token(
        self,
        authorization: str = Header(None)
    ) -> str:

        if not authorization:
            raise HTTPException(401, "Missing Authorization header")

        if not authorization.startswith("Bearer "):
            raise HTTPException(401, "Invalid Authorization header format")

        token = authorization.replace("Bearer ", "").strip()

        # Validate payload integrity
        self.validate(token)

        # Return raw token — required for Java forwarding
        return token


# Global instance
jwt_validator = JavaJWTValidator()
