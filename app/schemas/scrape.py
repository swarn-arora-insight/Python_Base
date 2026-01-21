# app/schemas/scrape.py
from pydantic import BaseModel
from typing import Optional

class StartScrapeRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    report_name: Optional[str] = None

class OtpRequest(BaseModel):
    session_id: str
    otp: str
