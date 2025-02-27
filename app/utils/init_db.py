# app/utils/init_db.py
from sqlalchemy.ext.asyncio import AsyncSession
from models.base import Base
from core.db import engine
#### a ####
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
####


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


#### alok in ###




pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme =OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

#### alok out ###