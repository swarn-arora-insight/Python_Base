# app/api/v1/scrape_routes.py
import os
from fastapi import APIRouter, HTTPException, Depends
from schemas.scrape import StartScrapeRequest, OtpRequest
from services.scrape_service import ScrapeService
from services.user_service import UserService
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

def get_scrape_service():
    return ScrapeService()

@router.post("/vauto/start")
async def start_scrape(
    request: StartScrapeRequest, 
    service: ScrapeService = Depends(get_scrape_service),
    user_info: dict = Depends(UserService.authenticate_token)
):
    username = request.username or os.getenv("VAUTO_USERNAME")
    password = request.password or os.getenv("VAUTO_PASSWORD")
    report_name = request.report_name or os.getenv("VAUTO_REPORT_NAME", "Taverna Inventory IRECON PHOTOS3")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and Password required")

    try:
        result = await service.start_login_flow(username, password, report_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cargurus/start")
async def start_cargurus_scrape(
    request: StartScrapeRequest,
    service: ScrapeService = Depends(get_scrape_service)
    user_info: dict = Depends(UserService.authenticate_token)
):
    username = request.username or os.getenv("CARGURUS_USERNAME")
    password = request.password or os.getenv("CARGURUS_PASSWORD")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and Password required for CarGurus")

    try:
        result = await service.start_cargurus_login_flow(username, password)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vauto/otp")
async def submit_otp(
    request: OtpRequest, 
    service: ScrapeService = Depends(get_scrape_service),
    user_info: dict = Depends(UserService.authenticate_token)
):
    report_name = os.getenv("VAUTO_REPORT_NAME", "Taverna Inventory IRECON PHOTOS4")
    try:
        result = await service.submit_otp_flow(request.session_id, request.otp, report_name)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
