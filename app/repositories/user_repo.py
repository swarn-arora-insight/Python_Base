# app/repositories/user_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User

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
