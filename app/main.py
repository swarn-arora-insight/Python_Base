# app/main.py
from fastapi import FastAPI
from api.v1 import user_routes, post_routes, comment_routes
from utils.init_db import init_db
import asyncio

app = FastAPI()

# Include routers for the User, Post, and Comment resources
app.include_router(user_routes.router, prefix="/v1/users", tags=["Users"])
app.include_router(post_routes.router, prefix="/v1/posts", tags=["Posts"])
app.include_router(comment_routes.router, prefix="/v1/comments", tags=["Comments"])

# Initialize the database
@app.on_event("startup")
async def on_startup():
    await init_db()

