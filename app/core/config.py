# app/core/config.py
import os
from pydantic_settings import BaseSettings  # Update the import here

class Settings(BaseSettings):
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+asyncmy://root:root@host:3306/baseproject")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+asyncmy://root:root@localhost:3306/baseproject")
settings = Settings()
