# app/core/db.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Create the database engine
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Create a session factory bound to the engine
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Dependency to provide an async database session
async def get_db():
    async with SessionLocal() as session:
        yield session
