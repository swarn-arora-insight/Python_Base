# app/services/user_service.py
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.models.user import User
from app.core.logging import logger

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, user_data: UserCreate) -> UserOut:
        user = User(name=user_data.name, email=user_data.email)
        new_user = await self.user_repo.create_user(user)
        return UserOut.from_orm(new_user)

    async def get_user(self, user_id: int) -> UserOut | None:
        logger.debug("Get_user function initiated")
        user = await self.user_repo.get_user_by_id(user_id)
        logger.debug("Get_user function Completed")
        return UserOut.from_orm(user) if user else None

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserOut | None:
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
