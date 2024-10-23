from fastapi import APIRouter, Depends, HTTPException
from src.Business.UserBusiness import UserBusiness
from src.Model.UserModel import users, User
router = APIRouter()

@router.post("/register")
async def register(user: User, userBusiness: UserBusiness = Depends()):
    result = await UserBusiness.register_user(user.username, user.email)
    if not result.success:
        raise HTTPException(status_code=result.status_code, detail=result.message)
    return result.to_dict()

@router.get("/users/{username}")
async def user(username: str=None, userBusiness: UserBusiness = Depends()):
    result = await userBusiness.get_user(username)
    if not result.success:
        raise HTTPException(status_code=result.status_code, detail=result.message)
    return result.to_dict()