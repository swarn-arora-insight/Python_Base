# app/main.py
from fastapi import FastAPI, Request
from api.v1 import user_routes, post_routes, comment_routes, uam_routes
from utils.init_db import init_db
from core.logging import logger
from fastapi.middleware.cors import CORSMiddleware
from models.base import Base
from core.db import engine
import asyncio

from fastapi.responses import JSONResponse
import traceback
import logging

logging.basicConfig(
    level=logging.DEBUG,
)

# app = FastAPI()
app = FastAPI(
    root_path="/template",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

# ADDED — global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    logger.error("Unhandled exception occurred", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

origins = [
    "http://localhost:3000",
    "https://dev.viewcurry.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization"],
)

# Include routers for the User, Post, and Comment resources
# app.include_router(post_routes.router, prefix="/v1/posts", tags=["Posts"]) # Currently commented out and will be used based on future requirements.
# app.include_router(comment_routes.router, prefix="/v1/comments", tags=["Comments"]) # Currently commented out and will be used based on future requirements.
app.include_router(user_routes.router, prefix="/v1/users", tags=["Users"])
app.include_router(uam_routes.router, prefix="/v1/uam", tags=["UAM"])

# Initialize the database
@app.on_event("startup")
async def on_startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Internal server error occurred: {str(e)}")
        raise 
    try:
        await init_db()
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Internal server error occurred: {str(e)}")
        raise
