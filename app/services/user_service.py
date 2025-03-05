# app/services/user_service.py
from repositories.user_repo import UserRepository
from schemas.user import UserCreate, UserUpdate, UserOut
from models.user import User
from core.logging import logger
from typing import Optional
from models.constants import UserMessages
import uuid
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from services.email_verification import send_email_verification_mail
from typing import Union
import bcrypt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()

BASE_URL=os.getenv("BASE_URL")
secret_key = os.getenv("USER_AUTH_SECRET_KEY")


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

    async def create_user(self, user_data: UserCreate) -> UserOut:
        user = User(name=user_data.name, email=user_data.email)
        new_user = await self.user_repo.create_user(user)
        return UserOut.from_orm(new_user)

    async def get_user(self, user_id: int) -> Optional[UserOut]:
        logger.debug("Get_user function initiated")
        user = await self.user_repo.get_user_by_id(user_id)
        logger.debug("Get_user function Completed")
        return UserOut.from_orm(user) if user else None

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserOut]:
        user = await self.user_repo.get_user_by_id(user_id)
        if user:
            updated_user = await self.user_repo.update_user(user, user_data.dict(exclude_unset=True))
            return UserOut.from_orm(updated_user)
        return None

    async def delete_user(self, user_id: int) -> bool:
        user = await self.user_repo.get_user_by_id(user_id)
        if user:
            await self.user_repo.delete_user(user)
            return True
        return False

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
            user = await user_repo._find_user_by_user_id(user_id)  # Use the injected UserRepository
            if user and user.get("token") == incoming_token:
                return (True, payload)
            raise HTTPException(status_code=401, detail="Invalid token")
        except (
            jwt.exceptions.DecodeError,
            jwt.exceptions.InvalidSignatureError,
        ) as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc

    async def authenticate_user(self, email: str, password: str):
        """
        Authenticates a user based on the provided email and password.
        """
        user = await self.user_repo._find_user_by_email(email)
        try:
            if user and bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
                token = jwt.encode(
                    {
                        "email": email,
                        "user_id": user["user_id"],
                        "id":user["id"],
                        "exp": datetime.utcnow() + timedelta(hours=8),
                    },
                    secret_key,
                    algorithm="HS256",
                )
                user["token"] = token 
                first_name = user.get("first_name", "")
                is_auth = user.get("is_auth", 0)
                user_id=user.get("user_id", "")
                user["last_logged_in"] = datetime.utcnow().isoformat()
                await self.user_repo.upsert_item(user)  # Update the user document
                confirmation_key=uuid.uuid4()
                if is_auth == 0:
                    await self.user_repo.store_auth_key(user_id,confirmation_key)
                    authenticate_link=f"{BASE_URL}authentication?key={confirmation_key}"
                    send_email_verification_mail(email, first_name, authenticate_link)
                return token, user.get("first_name", ""), user.get("last_name", ""),is_auth
            else:
                return None, "", "",0

        except Exception as e:
            logger.error(f"Error fetching user profile: {str(e)}")
            raise HTTPException(status_code=500, detail=UserMessages.INTERNAL_SERVER_ERROR)


    async def add_user(
        self,
        first_name: str,
        last_name: str,
        age:int,
        address:Union[str, int],
        email: str,
        password: str,
        ) -> str:
        """
        Adds a new user to the system.

        Args:
            first_name (str): The first name of the user.
            last_name (str): The last name of the user.
            email (str): The email address of the user.
            password (str): The password for the user.
            phone_number (str): The phone number of the user.
            business_type (str): The business type or interest of the user.
            state (str): The state of the user.
            company_name (str): The name of the company.
            referral_code (int): The referral code used during signup.

        Returns:
            str: "Success" if the user was added successfully, 
                otherwise an appropriate error message.

        Raises:
            HTTPException: If an unexpected error occurs.
        """
        try:
            user = await self.user_repo._find_user_by_email(email)
            if user:
                return f"Email '{email}' is already registered."
            
            hashed_password = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            user_id = str(uuid.uuid4())
            user_details = {
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email.strip().lower(),
                "password": hashed_password,
                "age":age,
                "address":address,
                "token": "",
                "last_logged_in": datetime.utcnow(),
                "created_on": datetime.utcnow(), 
            }
            # Update into the database
            await self.user_repo.upsert_item(user_details)
        
            return UserMessages.SUCCESS
        except Exception as e:
            logger.error(f"Error adding user: {str(e)}")
            raise HTTPException(
                status_code=500, detail=UserMessages.INTERNAL_SERVER_ERROR  
            )
    
    async def decode_jwt_token(self, token: str) -> tuple:
        """
        Args:
            token (str): The JWT token to decode.

        Returns:
            tuple: A tuple indicating if the token is valid and the payload of the token.

        Raises:
            HTTPException: If the token is invalid or cannot be decoded.
        """
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            return (True, payload)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def logout_user(self, user_id: str) -> bool:
        """
        Logs out a user by clearing their token.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            bool: True if the user was successfully logged out, False otherwise.
        """
        try:
            user = await self.user_repo._find_user_by_user_id(user_id)
            if user:
                user["token"] = ""
                await self.user_repo.upsert_item(user)
                return True

            return False
        except Exception as e:
            logger.error(f"Error logout user: {str(e)}")
            raise HTTPException(
                status_code=500, detail=UserMessages.INTERNAL_SERVER_ERROR  
            )
            


    
    
