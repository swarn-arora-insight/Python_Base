# app/api/v1/user_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.db import get_db
from repositories.user_repo import UserRepository
from repositories.uam_repo import UAMRepository
from services.user_service import UserService
from schemas.user import *
from utils.init_db import hash_password
from models.user import User
from core.security import RequiresFeature
from core.logging import logger
from models.constants import UserMessages
from utils.init_db import verify_password
import uuid
import datetime

router = APIRouter()

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
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,  # Provide the failure reason as the message
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
                "message": UserMessages.INTERNAL_SERVER_ERROR,  # Use predefined user message for errors
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
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
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
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
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
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
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
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
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
