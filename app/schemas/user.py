# app/schemas/user.py
from typing import Union,Optional
from pydantic import BaseModel, EmailStr

###alok in ##

class LoginResponse(BaseModel):
    id: int
    firstname: str
    lastname: str
    age: int
    address: Union[str, int]
    email: str 

    class Config:
        from_attributes=True
        # orm_mode = True

class UserRegistration(BaseModel):
    """user registration pydantic model"""

    first_name: str
    last_name: str
    age: int
    email_address: EmailStr
    address: Union[str, int]
    password: str

class LoginCreate(BaseModel):
    firstname: str
    lastname: str
    age: int
    address: Union[str, int]
    email: str
    password: str 

class LoginRequest(BaseModel):
    email: str
    password: str

### alok out ####

class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name :Optional[str] = None
    email :Optional[str] = None
    # name: str | None = None
    # email: str | None = None

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes=True
        # orm_mode = True
