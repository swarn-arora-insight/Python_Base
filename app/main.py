# app/main.py
from fastapi import FastAPI
from api.v1 import user_routes, post_routes, comment_routes
from utils.init_db import init_db
from core.logging import logger
from fastapi.middleware.cors import CORSMiddleware
from models.base import Base
from core.db import engine
import asyncio

# app = FastAPI()
app = FastAPI(
    root_path="/template",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)
origins = [
    "http://localhost:3000",
    "https://dev.viewcurry.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization"],
)

# Include routers for the User, Post, and Comment resources
app.include_router(user_routes.router, prefix="/v1/users", tags=["Users"])
app.include_router(post_routes.router, prefix="/v1/posts", tags=["Posts"])
app.include_router(comment_routes.router, prefix="/v1/comments", tags=["Comments"])
from api.v1 import uam_routes
app.include_router(uam_routes.router, prefix="/v1/uam", tags=["UAM"])

# Initialize the database
@app.on_event("startup")
async def on_startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.error(f"Internal server error occurred: {str(e)}")
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Internal server error occurred: {str(e)}")



