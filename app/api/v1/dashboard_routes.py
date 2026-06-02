
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx
import jwt
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.db import get_db
from core.logging import logger
from models.constants import UserMessages
from repositories.user_repo import UserRepository

# =============================================================================
# KEY LOADING  —  done once at import time.
# =============================================================================

with open(settings.PRIVATE_KEY_PATH) as _f:
    PRIVATE_KEY = _f.read()

with open(settings.ORCHESTRATOR_PUBLIC_KEY_PATH) as _f:
    ORCHESTRATOR_PUBLIC_KEY = _f.read()

ISSUER_KEYS = {
    settings.SSO_ISSUER: ORCHESTRATOR_PUBLIC_KEY,
    settings.LOCAL_ISSUER: PRIVATE_KEY,
}

# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter()


# =============================================================================
# AUTH DEPENDENCY
# =============================================================================

async def get_current_user2(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Unified auth dependency. Accepts THREE token types:
      1. SSO tokens (RS256, signed by Orchestrator) via cookie
      2. Project self-signed tokens (RS256) via cookie or header
      3. Standalone tokens (HS256) via Authorization header
    Returns a dict with user info.
    """
    # ─── Step 1: Extract token from cookie OR Authorization header ───
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)

    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(status_code=401, detail="No authentication token provided")

    # ─── Step 2: Peek at the token without verifying signature ───
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
        unverified_header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Malformed token")

    algorithm = unverified_header.get("alg")
    issuer = unverified.get("iss")

    # ─── Step 3a: HS256 path (standalone tokens) ───
    if algorithm == "HS256":
        try:
            service = UserRepository(db)
            token_data = await service.get_token_data(token)
            if len(token_data) == 0:
                return {
                    "header": {
                        "code": 401,
                        "message": UserMessages.SESSION_EXPIRED,
                    },
                    "response": {},
                }
            user_id = token_data[0]["user_id"]
            if not user_id:
                raise HTTPException(status_code=401, detail="Token missing user_id")

            return {
                "user_id": str(user_id),
                "auth_provider": "local",
                "iss": unverified.get("iss"),
                "token_id": unverified.get("token_id"),
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    # ─── Step 3b: RS256 path (SSO / self-signed) ───
    if algorithm == "RS256":
        public_key = ISSUER_KEYS.get(issuer)
        if not public_key:
            raise HTTPException(status_code=401, detail=f"Unknown token issuer: {issuer}")

        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"require": ["exp", "iss", "user_id"]},
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        return {
            "user_id": payload["user_id"],
            "auth_provider": payload.get("auth_provider", "sso"),
            "iss": payload["iss"],
            "token_id": payload.get("token_id"),
        }

    # ─── Unsupported algorithm ───
    raise HTTPException(status_code=401, detail=f"Unsupported algorithm: {algorithm}")


# =============================================================================
# ROUTES
# =============================================================================

@router.get("/callback")
async def sso_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    saved_state = request.cookies.get(settings.OAUTH_STATE_COOKIE_NAME)
    if not state or state != saved_state:
        raise HTTPException(status_code=400, detail="CSRF state mismatch")

    # Build client_assertion JWT
    now = datetime.now(timezone.utc)
    client_assertion_payload = {
        "iss": settings.CLIENT_ID,
        "sub": settings.CLIENT_ID,
        "aud": settings.SSO_ISSUER,
        "iat": now,
        "exp": now + timedelta(minutes=settings.CLIENT_ASSERTION_TTL_MINUTES),
        "jti": secrets.token_hex(settings.CLIENT_ASSERTION_JTI_BYTES),
    }
    client_assertion = jwt.encode(
        client_assertion_payload,
        PRIVATE_KEY,
        algorithm="RS256",
    )

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.ORCHESTRATOR_URL}{settings.ORCHESTRATOR_TOKEN_PATH}",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.CALLBACK_URL,
                "client_id": settings.CLIENT_ID,
                "client_assertion_type": settings.CLIENT_ASSERTION_TYPE,
                "client_assertion": client_assertion,
            },
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail=f"Token exchange failed: {resp.text}",
        )

    sso_access_token = resp.json()["access_token"]

    # Set the SSO cookie and redirect to frontend
    redirect = RedirectResponse(
        url=f"{settings.FRONTEND_URL}{settings.FRONTEND_DASHBOARD_PATH}",
        status_code=settings.SSO_REDIRECT_STATUS_CODE,
    )
    redirect.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=sso_access_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_COOKIE_MAX_AGE_SECONDS,
        domain=settings.COOKIE_DOMAIN,
    )
    redirect.delete_cookie(settings.OAUTH_STATE_COOKIE_NAME, path=settings.COOKIE_PATH)
    return redirect


@router.get("/api/dashboard-data")
def get_dashboard(user: dict = Depends(get_current_user2)):
    user_id = user["user_id"]
    return {
        "msg": "Secure data fetched successfully",
        "user_id": user_id,
        "active_services": 4,
        "uptime": "99.9%",
    }
