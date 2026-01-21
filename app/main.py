# app/main.py
from fastapi import FastAPI
from api.v1 import user_routes, scrape_routes
from utils.init_db import init_db
from core.logging import logger
from models.base import Base
from core.db import engine
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager 
import asyncio




@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== Startup =====
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logger.error(f"Internal server error occurred: {str(e)}")

    try:
        await init_db()
    except Exception as e:
        logger.error(f"Internal server error occurred: {str(e)}")

    yield  # ---- App runs here ----

    # ===== Shutdown (optional) =====
    # e.g. close connections if needed
    # await engine.dispose()



app = FastAPI(lifespan=lifespan)
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
# app.include_router(post_routes.router, prefix="/v1/posts", tags=["Posts"])
# app.include_router(comment_routes.router, prefix="/v1/comments", tags=["Comments"])
app.include_router(scrape_routes.router, prefix="/v1/scrape", tags=["Scraping"])




