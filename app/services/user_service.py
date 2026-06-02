# app/services/user_service.py
from repositories.user_repo import UserRepository
from schemas.user import UserCreate, UserUpdate, UserOut
from models.user import User
from core.logging import logger
from typing import Optional
from models.constants import UserMessages
import uuid
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from services.email_verification import send_email_verification_mail
from typing import Union, List
import bcrypt
import os, json, re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Request, HTTPException, Depends
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
secret_key = os.getenv("USER_AUTH_SECRET_KEY")
ORCHESTRATOR_PUBLIC_KEY = open("/home/ubuntu/template/app/keys/orchestrator_public.pem").read()

ALGORITHM = "HS256"
SECURITY = HTTPBearer()


def get_service(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Factory method to create a UserRepository instance.

    Args:
        db (AsyncSession): Database session dependency.

    Returns:
        UserRepository: Instance of the repository.
    """
    return UserRepository(db)


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    @staticmethod
    async def authenticate_token(
        credentials: HTTPAuthorizationCredentials = Depends(SECURITY),
        user_repo: UserRepository = Depends(get_service),
    ):
        """
        Authenticate the token supplied for each API.

        Args:
            credentials: Contains the bearer token.
            user_repo: UserRepository instance injected.

        Returns:
            Tuple: A tuple indicating the validity of the token and payload.

        Raises:
            HTTPException: If the token is invalid.
        """
        try:
            incoming_token = credentials.credentials
            payload = jwt.decode(incoming_token, secret_key, algorithms=["HS256"])
            user_id = payload["user_id"]
            user = await user_repo._find_user_by_user_id(
                user_id
            )  # Use the injected UserRepository
            if user and user.get("token") == incoming_token:
                return (True, payload)
            raise HTTPException(status_code=401, detail="Invalid token")
        except (
            jwt.exceptions.DecodeError,
            jwt.exceptions.InvalidSignatureError,
        ) as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc

    # @staticmethod
    # async def require_authorization(
    #     authorization: HTTPAuthorizationCredentials = Depends(SECURITY),
    #     db: AsyncSession = Depends(get_db),
    # ) -> dict:
    #     if not authorization:
    #         raise HTTPException(
    #             status_code=401, detail="Authorization header is required"
    #         )

    #     try:
    #         auth_token = authorization.credentials
    #         decrypted = UserRepository.aes_decrypt(json.dumps(auth_token))
    #         payload = json.loads(decrypted)

    #         user_id = payload.get("user_id")
    #         if not user_id:
    #             raise HTTPException(status_code=401, detail="Invalid token")

    #         repo = UserRepository(db)
    #         user_detail = await repo.get_user_details(user_id)
    #         return user_detail

    #     except Exception as e:
    #         logger.error(f"Authorization error: {str(e)}")
    #         raise HTTPException(status_code=401, detail="Invalid Authorization token")


    @staticmethod
    async def require_authorization(
        request: Request,
        # authorization: HTTPAuthorizationCredentials | None = Depends(
        #     HTTPBearer(auto_error=False)
        # ),
        authorization: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer(auto_error=False)
        ),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        # ─── Try SSO cookie first ───
        sso_cookie = request.cookies.get("project_template_session")
        if sso_cookie:
            try:
                payload = jwt.decode(
                    sso_cookie,
                    ORCHESTRATOR_PUBLIC_KEY,
                    algorithms=["RS256"],
                    options={"require": ["exp", "iss", "user_id"]},
                )
                if payload.get("iss") == "orchestrator":
                    sso_user_id = str(payload["user_id"])
                    repo = UserRepository(db)
                    user_detail = await repo.get_user_details(sso_user_id)
                    if user_detail:
                        return user_detail
                    # SSO user has no local row — return minimal info
                    return {
                        "user_id": sso_user_id,
                        "role_id": "R0001",
                        "auth_provider": "sso",
                    }
            except jwt.InvalidTokenError:
                pass  # fall through to header check

        # ─── Standalone AES blob check (existing logic) ───
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header is required")

        try:
            auth_token = authorization.credentials
            decrypted = UserRepository.aes_decrypt(json.dumps(auth_token))
            payload = json.loads(decrypted)

            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")

            repo = UserRepository(db)
            user_detail = await repo.get_user_details(user_id)
            return user_detail
        except Exception as e:
            logger.error(f"Authorization error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid Authorization token")

    async def authenticate_user(self, email: str, password: str):
        """
        Authenticates a user based on the provided email and password.
        """
        user = await self.user_repo._find_user_by_email(email)
        try:
            if user and bcrypt.checkpw(
                password.encode("utf-8"), user["password"].encode("utf-8")
            ):
                access_token = {
                    "email": email,
                    "org_id": user["org_id"],
                    "role_id": user["role_id"],
                    "user_id": user["user_id"],
                    "exp": (datetime.utcnow() + timedelta(hours=8)).isoformat(),
                }
                access_token = await self.user_repo.aes_encrypt(
                    json.dumps(access_token)
                )
                token = uuid.uuid4().hex[:32]

                first_name = user.get("first_name", "")
                last_name = user.get("last_name", "")
                is_auth = user.get("is_auth", 0)
                user_id = user.get("user_id", "")

                user["token"] = token
                user["last_logged_in"] = datetime.utcnow().isoformat()
                await self.user_repo.upsert_item(user)  # Update the user document
                confirmation_key = uuid.uuid4()
                if is_auth == 0:
                    await self.user_repo.store_auth_key(user_id, confirmation_key)
                    authenticate_link = (
                        f"{BASE_URL}authentication?key={confirmation_key}"
                    )
                    send_email_verification_mail(email, first_name, authenticate_link)
                return access_token, token, first_name, last_name
            else:
                return None, None, "", ""

        except Exception as e:
            logger.error(f"Error fetching user profile: {str(e)}")
            raise HTTPException(
                status_code=500, detail=UserMessages.INTERNAL_SERVER_ERROR
            )

    async def validate_user_details(self, payload: dict) -> tuple:
        for key, value in payload.items():
            if not value:
                return 400, f"{key} cannot be empty"
            if len(value) < 2:
                return 400, f"{key} must be at least 2 characters long"
            if not re.match(r"^[A-Za-z0-9 _-]+$", value):
                return 400, f"{key} contains invalid characters"

        return 200, "User details are valid"

    async def validate_password(self, payload: dict):
        password = payload.get("password")
        if not isinstance(password, str):
            return 400, "Password must be a string"

        if not password:
            return 400, "Password cannot be empty"

        if len(password) < 8 or len(password) > 100:
            return 400, "Password must be between 8 and 100 characters"

        if not re.search(r"[A-Za-z]", password):
            return 400, "Password must contain at least one alphabet"

        if not re.search(r"[0-9]", password):
            return 400, "Password must contain at least one number"

        return 200, "Password is valid"

    @staticmethod    
    def update_uam_log(user_id,route_name, message):
        import os
        import logging
        from logging.handlers import RotatingFileHandler
        import datetime
        """Keeping logs of uam requests"""
        # Full log file path
        log_path = os.path.join("uam_access_log", f"uam_{user_id}.log")

        # Create folder if not exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        # Create/get logger
        logger = logging.getLogger("uam_access_log")
        logger.setLevel(logging.INFO)

        # Avoid adding multiple handlers on repeated calls
        if not logger.handlers:
            handler = RotatingFileHandler(
                log_path, maxBytes=10 * 1024 * 1024, backupCount=5
            )
            formatter = logging.Formatter(
                "%(message)s"
            )  # We’ll build the timestamp ourselves
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        # Current timestamp with milliseconds
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

        # Write log message
        logger.info(f"{timestamp} | request_id= {user_id} | route_name= {route_name} | payload= {message}")
