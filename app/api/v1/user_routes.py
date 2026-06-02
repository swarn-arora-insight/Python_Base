
import datetime
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Union,Optional
import httpx
import jwt
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config import settings
from core.db import get_db
from core.logging import logger
from core.security import RequiresFeature
from models.constants import UserMessages
from models.user import User
from repositories.uam_repo import UAMRepository
from repositories.user_repo import UserRepository
from schemas.user import *
from services.user_service import UserService
from utils.init_db import hash_password, verify_password

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
# ROUTER & SECURITY
# =============================================================================

router = APIRouter()
SECURITY = HTTPBearer(auto_error=False)


class CheckPayload(BaseModel):
    token: Optional[str] = None


# =============================================================================
# AUTH DEPENDENCY
# =============================================================================

async def get_current_user2(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Unified auth dependency. Accepts:
      1. SSO tokens (RS256 JWT) via session cookie
      2. Standalone tokens (random string) via request body field "token"
    """
    # ─── Step 1: Try SSO cookie first ───
    sso_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if sso_cookie:
        try:
            unverified_header = jwt.get_unverified_header(sso_cookie)
            algorithm = unverified_header.get("alg")

            if algorithm == "RS256":
                unverified = jwt.decode(sso_cookie, options={"verify_signature": False})
                issuer = unverified.get("iss")
                public_key = ISSUER_KEYS.get(issuer)

                if public_key:
                    payload = jwt.decode(
                        sso_cookie,
                        public_key,
                        algorithms=["RS256"],
                        options={"require": ["exp", "iss", "user_id"]},
                    )
                    return {
                        "user_id": payload["user_id"],
                        "auth_provider": "sso",
                        "iss": payload["iss"],
                        "token_id": payload.get("token_id"),
                    }
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            pass  # fall through to body token check

    # ─── Step 2: Try standalone token from request body ───
    try:
        body = await request.json()
        token = body.get("token") if isinstance(body, dict) else None
    except Exception:
        token = None

    if not token:
        raise HTTPException(status_code=401, detail="No authentication token provided")

    try:
        service = UserRepository(db)
        token_data = await service.get_token_data(token)

        if not token_data or len(token_data) == 0:
            raise HTTPException(status_code=401, detail="Session expired")

        user_id = token_data[0].get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing user_id")

        return {
            "user_id": str(user_id),
            "auth_provider": "local",
            "iss": None,
            "token_id": token,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")


# =============================================================================
# ROUTES
# =============================================================================

@router.post("/login")
async def login_user_with_credentials(
    response: Response, payload: LoginRequest, db: AsyncSession = Depends(get_db)
):
    """
    User wants to login through their credentials
    Example payload in encrypted format in cryptography:
    {
    "email": "asx3h2/ihewtJTPRFtcrhHZtXrhZDK4ET3R9svLjVmT5M27MWbWn0ZFKP7zmlHG7",
    "password": "Z4wOzc3FTBdq44spBVTZrA=="
    }
    """
    user_service = UserService(UserRepository(db))
    try:
        access_token, token, first_name, last_name = (
            await user_service.authenticate_user(
                UserRepository.aes_decrypt(payload.email),
                UserRepository.aes_decrypt(payload.password),
            )
        )
        if access_token is not None and token is not None:
            # response.delete_cookie(
            #     key=settings.SESSION_COOKIE_NAME,
            #     path="/",          # must match the path the cookie was set with
            #     # domain=SSO_settings.COOKIE_DOMAIN,  # uncomment if the cookie was set with a domain
            # )
            response.delete_cookie(
            key=settings.SESSION_COOKIE_NAME,
            path="/",
            samesite=settings.COOKIE_SAMESITE,
            secure=settings.COOKIE_SECURE,
            httponly=settings.COOKIE_HTTPONLY,
            domain=settings.COOKIE_DOMAIN,
        )
            response.headers["Authorization"] = access_token
            return {
                "header": {
                    "code": 200,
                    "message": UserMessages.SUCCESS,
                },
                "response": {
                    "token": token,
                    "firstName": first_name,
                    "lastName": last_name,
                },
            }
        return {
            "header": {
                "code": 401,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    except HTTPException as e:
        logger.warning(f"HTTPException: {e.detail}")
        return {
            "header": {
                "code": e.status_code,
                "message": e.detail,
            },
            "response": {},
        }
    except Exception as e:
        logger.error(f"Error in login_user_with_credentials: {str(e)}")
        return {
            "header": {
                "code": 500,
                "message": UserMessages.INTERNAL_SERVER_ERROR,
            },
            "response": {},
        }


@router.post("/getusers")
async def user_list(
    payload: UserList,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Fetch all organizations accessible to an authenticated user."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 401,
                "message": UserMessages.SESSION_EXPIRED,
            },
            "response": {},
        }

    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 401,
                "message": UserMessages.SESSION_EXPIRED,
            },
            "response": {},
        }

    # Feature-Based Permission Check
    # Required: Feature="Users", Level=READ
    actor_user_id = token_data[0]["user_id"]
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
        return {
            "header": {
                "code": 403,
                "message": "Actor user not found.",
            },
            "response": {},
        }

    actor_role_id = actor_user_details.get("role_id")
    uam_repo = UAMRepository(db)

    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Users",
        "required_level": 2,
    })

    if not has_permission:
        logger.info(
            f"Insufficient permissions: User {actor_user_id} lacks READ access to 'Users'"
        )
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need READ access to 'Users' feature.",
            },
            "response": {},
        }

    user_details = await service.get_all_users()

    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": user_details,
    }


@router.post("/createuser")
async def create_user(
    payload: CreateUser,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 401,
                "message": UserMessages.SESSION_EXPIRED,
            },
            "response": {},
        }

    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 401,
                "message": UserMessages.SESSION_EXPIRED,
            },
            "response": {},
        }

    first_name = payload.first_name
    last_name = payload.last_name
    email_address = payload.email_address
    password = payload.password
    org_id = payload.org_id
    role_id = payload.role_id

    email_data = await service.get_user_by_detail({"email": payload.email_address})
    if len(email_data) != 0:
        return {
            "header": {
                "code": 400,
                "message": "Email already exists",
            },
            "response": {},
        }

    user_service = UserService(db)
    valid, message = await user_service.validate_user_details(
        {"first_name": first_name, "last_name": last_name}
    )
    if valid != 200:
        return {
            "header": {
                "code": valid,
                "message": message,
            },
            "response": {},
        }
    valid, message = await user_service.validate_password({"password": password})
    if valid != 200:
        return {
            "header": {
                "code": valid,
                "message": message,
            },
            "response": {},
        }

    uam_repo = UAMRepository(db)
    org_details = await uam_repo.get_org_by_key({"org_id": org_id})
    if len(org_details) == 0:
        return {
            "header": {
                "code": 400,
                "message": "Invalid Organization",
            },
            "response": {},
        }

    role_details = await uam_repo.get_role_by_key({"role_id": role_id})
    if len(role_details) == 0:
        return {
            "header": {
                "code": 400,
                "message": "Invalid Role",
            },
            "response": {},
        }

    password = hash_password(password)
    user_details = await service.add_user(
        {
            "first_name": first_name,
            "last_name": last_name,
            "email": email_address,
            "password": password,
            "org_id": org_id,
            "role_id": role_id,
            "user_id": str(uuid.uuid4()),
            "auth_key": str(uuid.uuid4()),
        }
    )
    if not user_details:
        return {
            "header": {
                "code": 400,
                "message": "User not created",
            },
            "response": {},
        }

    UserService.update_uam_log(token_data[0]["user_id"], "createuser", payload)
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/deleteuser")
async def delete_user(
    payload: DeleteUser,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 401,
                "message": UserMessages.SESSION_EXPIRED,
            },
            "response": {},
        }

    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 401,
                "message": UserMessages.SESSION_EXPIRED,
            },
            "response": {},
        }

    user_id = payload.user_id

    user_data = await service.get_user_by_detail({"user_id": payload.user_id})
    if len(user_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": "User not found",
            },
            "response": {},
        }

    code, message = await service.delete_user({"user_id": user_id})
    if code != 200:
        return {
            "header": {
                "code": code,
                "message": message,
            },
            "response": {},
        }
    UserService.update_uam_log(token_data[0]["user_id"], "deleteuser", payload)
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/logout")
async def logout_user(
    payload: LogoutUser,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Logout a user."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 401,
                "message": UserMessages.SESSION_EXPIRED,
            },
            "response": {},
        }

    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 401,
                "message": UserMessages.SESSION_EXPIRED,
            },
            "response": {},
        }
    delete_token = await service.delete_token(payload.token)
    if not delete_token:
        return {
            "header": {
                "code": 400,
                "message": "Something went wrong",
            },
            "response": {},
        }

    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.get("/sso/start")
async def sso_start(response: Response):
    """Frontend calls this. Backend generates state, sets cookie, redirects to SSO."""
    state = secrets.token_urlsafe(settings.OAUTH_STATE_TOKEN_BYTES)
  
    redirect_url = (
        f"{settings.ORCHESTRATOR_SSO_URL}"
        f"?client_id={settings.CLIENT_ID}"
        f"&redirect_uri={settings.CALLBACK_URL}"
        f"&state={state}"
    )
  
    redirect_response = RedirectResponse(
        url=redirect_url,
        status_code=settings.SSO_REDIRECT_STATUS_CODE,
    )
  
    redirect_response.set_cookie(
        key=settings.OAUTH_STATE_COOKIE_NAME,
        value=state,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.OAUTH_STATE_TTL_SECONDS,
        domain=settings.COOKIE_DOMAIN,
    )
    return redirect_response



@router.post("/check")
async def check_auth(
    request: Request,
    payload: CheckPayload,
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(SECURITY),
    db: AsyncSession = Depends(get_db),
):
    service = UserRepository(db)

    # ─── PATH 1: SSO cookie wins if present, valid, AND user exists ───
    sso_cookie = request.cookies.get(settings.SESSION_COOKIE_NAME)

    if sso_cookie:
        try:
            sso_payload = jwt.decode(
                sso_cookie,
                ORCHESTRATOR_PUBLIC_KEY,
                algorithms=["RS256"],
                options={"require": ["exp", "iss", "user_id"]},
            )

            if sso_payload.get("iss") != settings.SSO_ISSUER:
                # Wrong issuer = hostile cookie, not a missing one. Reject hard.
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token issuer",
                )

            sso_user_id = str(sso_payload["user_id"])
            user_detail = await service._find_user_by_id(sso_user_id)
            if user_detail:
                token_data = await service.issue_token_for_user(user_detail)
                logger.info(f"SSO auth success for user_id={sso_user_id}")
                return {
                    "user_id": token_data["user_id"],
                    "auth_provider": "sso",
                    "role": token_data["role"],
                    "access_token": token_data["access_token"],
                    "token": token_data["token"],
                }

            # User not in template DB — fall through to standalone auth.
            logger.info(
                f"SSO user_id={sso_user_id} not in template DB; "
                f"falling through to standalone auth"
            )

        except jwt.ExpiredSignatureError:
            logger.info("SSO cookie expired; falling through to standalone auth")
        except jwt.InvalidTokenError:
            logger.info("SSO cookie malformed; falling through to standalone auth")
        except HTTPException:
            raise

    # ─── PATH 2: Standalone auth (AES blob + body token, both required) ───
    if authorization and payload.token:
        try:
            auth_token = authorization.credentials
            decrypted = UserRepository.aes_decrypt(json.dumps(auth_token))
            blob_payload = json.loads(decrypted)

            user_id_from_blob = blob_payload.get("user_id")
            if not user_id_from_blob:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid AES blob",
                )

            token_data = await service.get_token_data(payload.token)
            if not token_data:
                raise HTTPException(
                    status_code=401,
                    detail="Session expired",
                )

            user_id_from_token = token_data[0].get("user_id")
            if str(user_id_from_blob) != str(user_id_from_token):
                raise HTTPException(
                    status_code=401,
                    detail="Token mismatch",
                )

            user_detail = await service.get_user_details(user_id_from_blob)

            return {
                "user_id": str(user_id_from_blob),
                "auth_provider": "local",
                "role": user_detail.get("role_id") if user_detail else settings.DEFAULT_ROLE_LOCAL,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Standalone auth failed: {e}")

    raise HTTPException(
        status_code=401,
        detail="Not authenticated",
    )

@router.post("/logout/sso")
def clear_sso_cookie(response: Response):
    """Clears the SSO cookie. Called by frontend when user logs in standalone
    to prevent SSO from overriding their standalone session."""
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path=settings.COOKIE_PATH,
    )
    return {"ok": True}

# =============================================================================
# Add this to your user_routes.py CONFIGURATION block (if not already there)
# =============================================================================

# Used by /logout/all to clear cookies. These should match what you set elsewhere.
# (settings.SESSION_COOKIE_NAME and settings.OAUTH_STATE_COOKIE_NAME are already in your config.)



# =============================================================================
# Add this schema near your other Pydantic models (e.g., next to CheckPayload)
# =============================================================================

class LogoutAllPayload(BaseModel):
    """
    Optional body. If the user has a standalone token, send it so we can
    invalidate it server-side. If they only had SSO, no body is fine.
    """
    token: Optional[str] = None


# =============================================================================
# Add this route (place it near the existing /logout and /logout/sso routes)
# =============================================================================

@router.post("/logout/all")
async def logout_all(
    request: Request,
    response: Response,
    # payload: LogoutAllPayload | None = None,
    payload: Optional[LogoutAllPayload] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Universal logout. Safe to call regardless of auth state.

      1. If a standalone token is provided in body, delete it from DB.
      2. Clear the SSO session cookie.
      3. Clear the oauth_state cookie (in case a flow was interrupted).

    Always returns 200. Frontend should ALSO clear its own localStorage /
    sessionStorage after calling this — the backend can't touch those.
    """
    # ── 1. Invalidate standalone DB token (if any) ──
    token_to_revoke = payload.token if payload else None
    if token_to_revoke:
        try:
            service = UserRepository(db)
            await service.delete_token(token_to_revoke)
        except Exception as e:
            logger.error("Error revoking token:", exc_info=True)
            #  return {
            #     "header": {
            #         "code": 200,
            #         "message": UserMessages.SUCCESS,
            #     },
            #     "response": {},
            # }

            # Don't fail logout just because token cleanup failed.
            # User experience matters more here than DB consistency.

    # ── 2. Clear the SSO session cookie ──
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        httponly=settings.COOKIE_HTTPONLY,
        domain=settings.COOKIE_DOMAIN,
    )

    # ── 3. Clear lingering oauth_state cookie ──
    response.delete_cookie(
        key=settings.OAUTH_STATE_COOKIE_NAME,
        path="/",
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        httponly=settings.COOKIE_HTTPONLY,
        domain=settings.COOKIE_DOMAIN,
    )

    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }














