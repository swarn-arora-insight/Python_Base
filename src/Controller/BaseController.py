from fastapi import APIRouter, HTTPException
from src.Controller.UserController import router as user_controller 

router = APIRouter()

# Include user API router
router.include_router(user_controller, prefix="/user")
