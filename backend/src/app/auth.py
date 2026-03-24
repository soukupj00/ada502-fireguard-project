import os

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt

# 1. ALLOW HTTP FOR LOCAL DEV
# This prevents the "OAuth2 requires HTTPS" error in the Swagger UI
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Configuration Variables
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
REALM = os.getenv("KEYCLOAK_REALM", "FireGuard")
# Use this for internal container-to-container calls if using Docker
KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", "http://keycloak:8080")

# 2. Updated OAuth2 Scheme
# The frontend uses KEYCLOAK_URL,
# but the backend must verify against KEYCLOAK_INTERNAL_URL
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth",
    tokenUrl=f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
)

# URL for Keycloak Public Keys (JWKS)
# Use internal URL so the backend can reach Keycloak within the docker network
JWKS_URL = f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/certs"


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # 3. FETCH PUBLIC KEYS (In a real app, cache this result!)
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            response.raise_for_status()
            jwks = response.json()

        # 4. DECODE AND VERIFY
        # We specify the audience (your client_id) to ensure the token was meant
        # for THIS app
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={
                "verify_aud": False
            },  # Set to True and add audience="your-client-id" for prod
        )
        return payload

    except JWTError as e:
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
