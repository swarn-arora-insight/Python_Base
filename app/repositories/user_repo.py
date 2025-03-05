# app/repositories/user_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from core.logging import logger
from typing import Any, Dict, Optional, List
from sqlalchemy import update


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_all_users(self):
        result = await self.db.execute(select(User))
        return result.scalars().all()

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, user: User, updates: dict) -> User:
        for field, value in updates.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user: User):
        await self.db.delete(user)
        await self.db.commit()

    async def _find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Helper method to find a user by user ID.

        Args:
            email (str): The unique identifier for the user.

        Returns:
            Optional[Dict[str, Any]]: The user document if found, None otherwise.
        """
        try:
            logger.info(f"Searching for user with email: {email}")
            result = await self.db.execute(
                select(User).where(User.email == email , User.is_active == 1)
            )
            user_data = result.scalars().one_or_none()
            if user_data is None:
                logger.info(f"No active user found with email: {email}")
                return None
            return {
                "user_id": user_data.user_id,
                "email": user_data.email,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "password": user_data.password,
                "last_logged_in": user_data.last_logged_in,
                "id":user_data.id,
                "is_auth":user_data.is_auth,
                # Include other fields as necessary
            }

        except Exception as e:
            logger.error(f"Error fetching user by email: {str(e)}")
            return None

    async def upsert_item(self, user_details: Dict[str, Any]):
        """
        Insert or update a user in the database based on the provided details.

        :param user_details: A dictionary containing the user details, including `user_id`.
        :raises Exception: If an error occurs during the operation.
        """
        try:
            logger.info("Updating user details.")
            existing_user = await self.db.execute(
                select(User).where(User.user_id == user_details['user_id'])
            )
            user_instance = existing_user.scalar()
            if user_instance:
                # Update the existing user instance with new details
                for key, value in user_details.items():
                    setattr(user_instance, key, value)  # Update only the fields present in user_details
            else:
                # If the user does not exist, create a new user instance
                user_instance = User(**user_details)  # Ensure user_details contains datetime objects
                self.db.add(user_instance)
 
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error in upserting item: {str(e)}")
            raise

    async def _find_user_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Finds a user by their user_id in the Cosmos DB container.

        Args:
            email (str): The user_id to search for.

        Returns:
            Optional[Dict[str, Any]]: The user data as a dictionary if found, otherwise None.
        """
        try:
            logger.info(f"Searching for user with user ID: {user_id}")
            # Construct and execute the query using SQLAlchemy
            result = await self.db.execute(
                select(User).where(User.user_id == user_id, User.is_active == 1)
            )

            user_data = result.scalars().one_or_none()
            if user_data is None:
                logger.info(f"No active user found with user ID: {user_id}")
                return None

            return {
                "user_id": user_data.user_id,
                "email": user_data.email,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "password": user_data.password,
                "last_logged_in": user_data.last_logged_in,
                "token":user_data.token,
                "is_auth":user_data.is_auth,
                "auth_key":user_data.auth_key,
                # Include other fields as necessary
            }

        except Exception as e:
            logger.error(f"Error fetching user by user ID: {str(e)}")
            return None


    async def store_auth_key(self, user_id: int, auth_key: str) -> None:
        """
        Store or update the authentication key for a user.

        Args:
            user_id (int): The unique ID of the user.
            auth_key (str): The authentication key to be stored.

        Raises:
            Exception: If an error occurs while storing the authentication key.
        """
        try:
            logger.info(f"stoing auth_key for user_id: {user_id}")
            # Update the status field in the database
            query = (
                update(User)
                .where(
                    User.user_id == user_id
                )
                .values(auth_key=auth_key)
            )
            await self.db.execute(query)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error storing auth_key: {str(e)}")
            raise

