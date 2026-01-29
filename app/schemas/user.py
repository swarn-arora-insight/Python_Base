# app/schemas/user.py
from typing import Union,Optional
from pydantic import BaseModel, EmailStr, field_validator
from disposable_email_domains import blocklist

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
    org_id: Optional[str]
    role_id: Optional[str]
    @field_validator("email_address")
    @classmethod
    def reject_disposable_email_address(cls, v):
        domain = v.split("@")[1].lower()
        if domain in blocklist:
            raise ValueError("Disposable email addresses are not allowed")
        return v

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


class UserList(BaseModel):
    token: str

class CreateUser(BaseModel):
    token: str
    first_name: str
    last_name: str
    org_id: Optional[str]
    role_id: Optional[str]
    email_address: EmailStr
    password: str