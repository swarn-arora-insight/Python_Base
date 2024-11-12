# app/schemas/user.py
from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes=True
        # orm_mode = True
