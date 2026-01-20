# app/core/security.py
from fastapi import Depends, HTTPException, status
from services.user_service import UserService
from core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.uam_repo import UAMRepository
from typing import List

class RequiresFeature:
    def __init__(self, feature_key: str):
        self.feature_key = feature_key

    async def __call__(self, user_info: tuple = Depends(UserService.authenticate_token), db: AsyncSession = Depends(get_db)):
        valid, payload = user_info
        if not valid:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user_id = payload.get("user_id")
        
        # Optimize: Ideally payload has everything, but since features can change dynamically,
        # we often need to fetch fresh permissions from DB.
        # Let's fetch the user's role and features.
        
        # We need a Repo that can fetch User + Role + Features
        # For simplicity, we can use uam_repo if extended or user_repo
        
        # Let's verify via UAMRepo/UserRepo strategy
        # NOTE: Circular dependency is a risk if we import UserService/Repo casually.
        # Let's assume user_info came from UserService, and we use UAM logic here.
        
        from models.user import User
        from sqlalchemy.future import select
        from sqlalchemy.orm import joinedload
        
        result = await db.execute(
            select(User)
            .options(joinedload(User.role).joinedload("features"))
            .where(User.user_id == user_id)
        )
        user = result.scalars().first()
        
        if not user or not user.role:
             raise HTTPException(status_code=403, detail="User has no role assigned")
             
        # Check features
        feature_keys = [f.key for f in user.role.features]
        
        if self.feature_key not in feature_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Missing required feature: {self.feature_key}"
            )
        
        return user
