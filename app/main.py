# app/main.py
from fastapi import FastAPI
from api.v1 import user_routes, post_routes, comment_routes
from utils.init_db import init_db
from core.logging import logger
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # A list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods like GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Allows all headers
)

# Include routers for the User, Post, and Comment resources
app.include_router(user_routes.router, prefix="/v1/users", tags=["Users"])
app.include_router(post_routes.router, prefix="/v1/posts", tags=["Posts"])
app.include_router(comment_routes.router, prefix="/v1/comments", tags=["Comments"])

# Initialize the database
@app.on_event("startup")
async def on_startup():
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Internal server error occurred: {str(e)}")



