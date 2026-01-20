# app/api/v1/uam_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from repositories.uam_repo import UAMRepository
from services.uam_service import UAMService
from schemas.uam import OrganizationCreate, OrganizationOut, RoleCreate, RoleOut, FeatureOut, FeatureAssign
from typing import List

router = APIRouter()

def get_uam_service(db: AsyncSession = Depends(get_db)) -> UAMService:
    return UAMService(UAMRepository(db))

# Organizations
@router.post("/orgs", response_model=OrganizationOut)
async def add_org(org: OrganizationCreate, service: UAMService = Depends(get_uam_service)):
    return await service.create_organization(org)

@router.get("/orgs", response_model=List[OrganizationOut])
async def list_orgs(service: UAMService = Depends(get_uam_service)):
    return await service.get_organizations()

# Roles
@router.post("/roles", response_model=RoleOut)
async def add_role(role: RoleCreate, service: UAMService = Depends(get_uam_service)):
    return await service.create_role(role)

@router.get("/roles", response_model=List[RoleOut])
async def list_roles(service: UAMService = Depends(get_uam_service)):
    return await service.get_roles()

@router.post("/roles/{role_id}/features", response_model=RoleOut)
async def assign_role_features(role_id: int, features: FeatureAssign, service: UAMService = Depends(get_uam_service)):
    role = await service.assign_features(role_id, features)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

# Features
@router.get("/features", response_model=List[FeatureOut])
async def list_features(service: UAMService = Depends(get_uam_service)):
    return await service.get_features()
