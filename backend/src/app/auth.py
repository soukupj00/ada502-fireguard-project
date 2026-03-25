import os
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt

# 1. ALLOW HTTP FOR LOCAL DEV
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Configuration Variables
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080/auth")
REALM = os.getenv("KEYCLOAK_REALM", "FireGuard")
KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", "http://keycloak:8080/auth")

# --- NEW CONFIGURATION ---
# The Backend now has its own identity and secret
BACKEND_CLIENT_ID = os.getenv("BACKEND_CLIENT_ID", "backend-client")
BACKEND_CLIENT_SECRET = os.getenv("BACKEND_CLIENT_SECRET", "YOUR_SECRET_FROM_KEYCLOAK")
# -------------------------

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth",
    tokenUrl=f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
)

JWKS_URL = f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/certs"


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # FETCH PUBLIC KEYS (Consider caching this globally to
        # avoid per-request network calls)
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            response.raise_for_status()
            jwks = response.json()

        # DECODE AND VERIFY
        # We now verify the audience to ensure the token
        # was intended for the backend-client
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=BACKEND_CLIENT_ID,  # Verify that 'aud' claim
            # matches 'backend-client'
            options={
                "verify_aud": True,  # Turned this ON for better security
                "verify_at_hash": False,
            },
        )
        return payload

    except JWTError as e:
        # If this fails with "Invalid audience", check your Keycloak Audience Mapper
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not connect to Keycloak: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )


async def get_current_user_ws_or_sse(token: str = Query(...)):
    """
    Alternative dependency for WebSockets or Server-Sent Events (SSE) where
    the token cannot be easily sent in the Authorization header.
    Expects the token as a query parameter `?token=...`
    """
    return await get_current_user(token)


async def get_current_user_optional(request: Request) -> Optional[dict]:
    # Try to extract token from Authorization header manually
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        return await get_current_user(token)
    except Exception:
        return None
