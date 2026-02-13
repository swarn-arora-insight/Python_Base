from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from services.user_service import UserService
from repositories.dashboard_repo import DashboardRepository
from core.logging import logger

router = APIRouter()

@router.get("/info")
async def get_dashboard_info(
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard information.
    """
    logger.info("Fetching dashboard info")
    
    # Example usage of repo
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
