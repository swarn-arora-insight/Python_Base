# app/utils/init_db.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base
from app.core.db import engine

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
