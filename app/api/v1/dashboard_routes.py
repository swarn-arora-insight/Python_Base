from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from services.user_service import UserService
from repositories.dashboard_repo import DashboardRepository
from schemas.dashboard import FilterDashboardRequest
from core.logging import logger

router = APIRouter()

@router.get("/info")
async def get_dashboard_info(
    # auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard information.
    """
    logger.info("Fetching dashboard info")
    
    # dashboard_repo = DashboardRepository(db)
    # data = await dashboard_repo.get_data()
    
    return {
        "header": {
            "code": 200,
            "message": "Success",
        },
        "response": {
            "message": "Dashboard module initialized"
        },
    }

@router.get("/vauto/body")
async def get_vauto_body(
    # auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """
    Get unique body types from vauto inventory.
    """
    logger.info("Fetching vauto body details")
    
    dashboard_repo = DashboardRepository(db)
    data = await dashboard_repo.get_vauto_body_details()
    
    return {
        "header": {
            "code": 200,
            "message": "Success",
        },
        "response": {
            "bodies": data
        },
    }

@router.get("/vauto/store")
async def get_vauto_store(
    # auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """
    Get unique store types from vauto inventory.
    """
    logger.info("Fetching vauto store details")
    
    dashboard_repo = DashboardRepository(db)
    data = await dashboard_repo.get_vauto_store_details()
    
    return {
        "header": {
            "code": 200,
            "message": "Success",
        },
        "response": {
            "stores": data
        },
    }

@router.post("/vauto/filter")
async def get_filtered_dashboard_data(
    payload: FilterDashboardRequest,
    # auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """
    Get filtered vauto inventory data.
    """
    logger.info(f"Fetching filtered data with payload: {payload}")
    
    dashboard_repo = DashboardRepository(db)
    
    # Convert payload to dict, excluding None values if needed, or handle in repo
    filters = payload.dict(exclude_none=True)
    
    data = await dashboard_repo.get_filtered_data(filters)
    
    return {
        "header": {
            "code": 200,
            "message": "Success",
        },
        "response": {
            "data": data,
            "count": len(data)
        },
    }
