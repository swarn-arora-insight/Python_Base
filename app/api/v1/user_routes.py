# app/api/v1/user_routes.py
from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.db import get_db
from repositories.user_repo import UserRepository
from services.user_service import UserService
from schemas.user import UserCreate, UserUpdate, UserOut
from schemas.user import LoginCreate, LoginResponse
from utils.init_db import hash_password
from models.user import User
from schemas.user import LoginRequest
from utils.init_db import verify_password
import uuid
import datetime

router = APIRouter()

###alok####



@router.post("/create-user/", response_model=LoginResponse)
async def create_User(details: LoginCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = hash_password(details.password)
    db_user = User(
        id=uuid.uuid4(),
        firstname=details.firstname,
        lastname=details.lastname,
        age=details.age,
        address=details.address,
        email=details.email,
        password=hashed_password,
        isactive=1,  # Default active
        created_on=datetime.datetime.utcnow(), 
    )
    # db_user = User(**details.dict())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/login/")
async def login(form_data: LoginRequest , db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email == form_data.email)
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return {"message": "Login successful", "user": user.email}    



### alok out ####


@router.post("/", response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    user_service = UserService(UserRepository(db))
    return await user_service.create_user(user)

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user_service = UserService(UserRepository(db))
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_data: UserUpdate, db: AsyncSession = Depends(get_db)):
    user_service = UserService(UserRepository(db))
    user = await user_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", response_model=dict)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user_service = UserService(UserRepository(db))
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
