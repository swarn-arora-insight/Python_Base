# app/main.py
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
from api.v1 import scrape_routes
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # A list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods like GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Allows all headers
)


app.include_router(scrape_routes.router, prefix="/v1/scrape", tags=["Scraping"])




