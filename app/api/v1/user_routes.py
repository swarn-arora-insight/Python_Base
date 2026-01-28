# app/api/v1/user_routes.py
from fastapi import APIRouter, Depends, HTTPException,status,Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.db import get_db
from repositories.user_repo import UserRepository
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

###alok####



# @router.post("/create-user/", response_model=LoginResponse)
# async def create_User(details: LoginCreate, db: AsyncSession = Depends(get_db)):
#     hashed_password = hash_password(details.password)
#     db_user = User(
#         id=uuid.uuid4(),
#         firstname=details.firstname,
#         lastname=details.lastname,
#         age=details.age,
#         address=details.address,
#         email=details.email,
#         password=hashed_password,
#         isactive=1,  # Default active
#         created_on=datetime.datetime.utcnow(), 
#     )
#     # db_user = User(**details.dict())
#     db.add(db_user)
#     await db.commit()
#     await db.refresh(db_user)
#     return db_user

# @router.post("/login/")
# async def login(form_data: LoginRequest , db: AsyncSession = Depends(get_db)):
#     query = select(User).where(User.email == form_data.email)
#     result = await db.execute(query)
#     user = result.scalars().first()
    
#     if not user or not verify_password(form_data.password, user.password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
        
#     return {"message": "Login successful", "user": user.email}    



# ### alok out ####


# @router.post("/", response_model=UserOut)
# async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
#     user_service = UserService(UserRepository(db))
#     return await user_service.create_user(user)

# @router.get("/{user_id}", response_model=UserOut)
# async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
#     user_service = UserService(UserRepository(db))
#     user = await user_service.get_user(user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user

# @router.put("/{user_id}", response_model=UserOut)
# async def update_user(user_id: int, user_data: UserUpdate, db: AsyncSession = Depends(get_db)):
#     user_service = UserService(UserRepository(db))
#     user = await user_service.update_user(user_id, user_data)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user

# @router.delete("/{user_id}", dependencies=[Depends(RequiresFeature("user_delete"))])
# async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
#     user_service = UserService(UserRepository(db))
#     success = await user_service.delete_user(user_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="User not found")
#     return {"message": "User deleted successfully"}





@router.post("/signup")
async def user_signup(
    request: UserRegistration,
    db: AsyncSession = Depends(get_db),
    ):
    """
    API for user registration.

    Args:
        request (UserRegistration): The payload containing user registration details.

    Returns:
        dict: Success or failure message after processing the registration.
    """
    user_service = UserService(UserRepository(db))
    try:
        # Call the service to add the user
        result = await user_service.add_user(
            first_name=request.first_name,
            last_name=request.last_name,
            age=request.age,
            address=request.address,
            email=request.email_address,
            password=request.password,
            org_id=request.org_id,
            role_id=request.role_id,
        )
        # Check the result and respond accordingly
        if result == "Success":
            return {
                "header": {
                    "code": 200,
                    "message": UserMessages.SUCCESS,
                },
                "response": {},
            }

        return {
            "header": {
                "code": 400,
                "message": result,  # Provide the failure reason as the message
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
        logger.error(f"Error in user_signup: {str(e)}")
        return {
            "header": {
                "code": 500,
                "message": UserMessages.INTERNAL_SERVER_ERROR,
            },
            "response": {},
        }


@router.post("/login")
async def login_user_with_credentials(response: Response, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
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
        access_token, token, first_name, last_name = await user_service.authenticate_user( UserRepository.aes_decrypt(payload.email), UserRepository.aes_decrypt(payload.password))
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
                    }
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
async def user_list(payload: UserList, auth_payload: dict = Depends(UserService.require_authorization), db: AsyncSession = Depends(get_db) ):
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
        "response": user_details
    }



@router.post("/logout")
async def logout_user(user_info: dict = Depends(UserService.authenticate_token), db: AsyncSession = Depends(get_db)):
    """Ensures user logout

    Args:
        user_info (str, optional):
        _description_. Defaults to Depends(USER_LOGIN.authenticate_token).
    Returns:
        _type_: _description_
    """
    try:
        user_service = UserService(UserRepository(db))
        valid, user_info = user_info
        if valid and  await user_service.logout_user(user_info["user_id"]):
            return {
                    "header": {
                        "code": 200,
                        "message": UserMessages.LOGOUT_SUCCESS,
                    },
                    "response": {}
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
        return HTTPResponse().failed(response_code=401)
