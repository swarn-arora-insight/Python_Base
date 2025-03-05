# app/core/config.py
import os
from pydantic_settings import BaseSettings  # Update the import here

class Settings(BaseSettings):
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+asyncmy://root:root@host:3306/baseproject")
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+asyncmy://root:root@localhost:3306/baseproject")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+asyncmy://root:@localhost:3306/template")  ##--local
    # DATABASE_URL: str = "mysql+asyncmy://dbuser1:$parr0w0re0@localhost:3306/template"  ###--dev
settings = Settings()
