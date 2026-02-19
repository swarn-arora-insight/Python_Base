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

@router.get("/body")
async def get_body_types(
    # auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """
    Get unique body types from vauto inventory.
    """
    logger.info("Fetching vauto body details")
    
    dashboard_repo = DashboardRepository(db)
    data = await dashboard_repo.get_body_types()
    
    return {
        "header": {
            "code": 200,
            "message": "Success",
        },
        "response": {
            "bodies": data
        },
    }

@router.get("/store")
async def get_stores(
    # auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """
    Get unique store types from vauto inventory.
    """
    logger.info("Fetching vauto store details")
    
    dashboard_repo = DashboardRepository(db)
    data = await dashboard_repo.get_stores()
    
    return {
        "header": {
            "code": 200,
            "message": "Success",
        },
        "response": {
            "stores": data
        },
    }

@router.get("/vin")
async def get_vins(
    # auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """
    Get unique VINs from vauto inventory.
    """
    logger.info("Fetching vauto vin details")
    
    dashboard_repo = DashboardRepository(db)
    data = await dashboard_repo.get_vins()
    
    return {
        "header": {
            "code": 200,
            "message": "Success",
        },
        "response": {
            "vins": data
        },
    }

@router.post("/filter")
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
    
    result = await dashboard_repo.get_filtered_data(filters)
    data = result.get("data", [])
    metrics = result.get("metrics", {})
    # graph_data = result.get("graph_data", [])
    
    return {
        "header": {
            "code": 200,
            "message": "Success",
        },
        "response": {
            # "data": data,
            # "count": len(data),
            # "total_leads": metrics.get("total_leads", 0),
            # "avg_leads_per_day": metrics.get("avg_leads", 0),
            "metrics": metrics,
            # "graph_data": graph_data
        },
    }

@router.post("/leadperformance")
async def get_lead_performance_data(
    payload: FilterDashboardRequest,
    # auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """
    Get lead performance graph data.
    """
    logger.info(f"Fetching lead performance data with payload: {payload}")

    dashboard_repo = DashboardRepository(db)
    
    filters = payload.dict(exclude_none=True)
    
    result = await dashboard_repo.get_lead_performance_data(filters)
    graph_data = result.get("graph_data", [])
    
    return {
        "header": {
            "code": 200,
            "message": "Success",
        },
        "response": {
            "graph_data": graph_data
        },
    }
