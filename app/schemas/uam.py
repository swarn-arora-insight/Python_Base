# app/schemas/uam.py
from pydantic import BaseModel
from typing import List, Optional

class FeatureBase(BaseModel):
    name: str
    key: str
    description: Optional[str] = None

class FeatureOut(FeatureBase):
    id: int
    class Config:
        orm_mode = True

class FeatureAssign(BaseModel):
    feature_ids: List[int]

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleOut(RoleBase):
    id: int
    features: List[FeatureOut] = []
    class Config:
        orm_mode = True

class OrganizationBase(BaseModel):
    name: str
    code: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationOut(OrganizationBase):
    id: int
    is_active: bool
    class Config:
        orm_mode = True

class TabsList(BaseModel):
    token:str

class OrgDetails(BaseModel):
    token:str