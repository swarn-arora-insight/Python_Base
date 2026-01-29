# app/api/v1/uam_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from repositories.uam_repo import UAMRepository
from services.uam_service import UAMService
from schemas.uam import *
from typing import List
from models.constants import UserMessages
from services.user_service import UserService
from repositories.user_repo import UserRepository

router = APIRouter()

def get_uam_service(db: AsyncSession = Depends(get_db)) -> UAMService:
    return UAMService(UAMRepository(db))


@router.post("/tabslist")
async def tabslist(payload: TabsList, auth_payload: dict = Depends(UserService.require_authorization), db: AsyncSession = Depends(get_db)):
    """Return the list of accessible UI tabs for an authenticated user."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    tab_data = [
        {
            "tab_name": "Organizations",
            "access": 1,
            "add_button": "Organization",
            "icon": "Building2"
        },
        {
            "tab_name": "Roles",
            "access": 1,
            "add_button": "Role",
            "icon": "Shield"
        },
        {
            "tab_name": "Users",
            "access": 1,
            "add_button": "User",
            "icon": "Users"
        }
    ]

    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": tab_data
    }


@router.post("/getorgs")
async def org_details(payload: OrgDetails, auth_payload: dict = Depends(UserService.require_authorization), db: AsyncSession = Depends(get_db) ):
    """Fetch all organizations accessible to an authenticated user."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    uam_service = UAMRepository(db)
    org_details = await uam_service.get_all_orgs()

    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": org_details
    }


@router.post("/createorg")
async def create_org(payload: CreateOrg, auth_payload: dict = Depends(UserService.require_authorization), db: AsyncSession = Depends(get_db) ):
    """Create a new organization."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    uam_service = UAMService(db)
    org_name = payload.org_name.strip()
    code, message = await uam_service.check_org_name(org_name)
    
    if code != 200:
        return {
            "header": {
                "code": code,
                "message": message,
            },
            "response": {},
        }
    
    uam_repo = UAMRepository(db)
    
    fetch_org = await uam_repo.get_org_by_key({"org_name": org_name})
    if len(fetch_org) > 0:
        return {
            "header": {
                "code": 400,
                "message": "Organization name already exists.",
            },
            "response": {},
        }
    
    orgs = await uam_repo.get_all_orgs()    
    if not orgs:
        next_org_id = "ORG00001"
    else:
        last_number = max(int(org["org_id"][3:]) for org in orgs)
        next_org_id = f"ORG{last_number + 1:04d}"

    payload = {
        "org_name": org_name,
        "org_id": next_org_id,
        "updated_by": token_data[0]["user_id"],
        "action": "create"
    }
 
    code, org_entry_message = await uam_repo.org_entry(payload)
    if code != 200:
        return {
            "header": {
                "code": code,
                "message": org_entry_message,
            },
            "response": {},
        }

    return {
            "header": {
                "code": 200,
                "message": UserMessages.SUCCESS,
            },
            "response": {},
        }


@router.post("/editorg")
async def edit_org(payload: EditOrg, auth_payload: dict = Depends(UserService.require_authorization), db: AsyncSession = Depends(get_db) ):
    """Edit organization detail."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    org_id = payload.org_id
    org_name = payload.org_name.strip()

    uam_repo = UAMRepository(db)
    orgs = await uam_repo.get_org_by_key({"org_id": org_id})
    if len(orgs) == 0:
        return {
            "header": {
                "code": 400,
                "message": "Invalid organization details.",
            },
            "response": {},
        }

    payload = {
        "org_name": org_name,
        "org_id": org_id,
        "updated_by": token_data[0]["user_id"],
        "action": "edit"
    }
 
    code, org_entry_message = await uam_repo.org_entry(payload)
    if code != 200:
        return {
            "header": {
                "code": code,
                "message": org_entry_message,
            },
            "response": {},
        }

    return {
            "header": {
                "code": 200,
                "message": UserMessages.SUCCESS,
            },
            "response": {},
        }


@router.post("/deleteorg")
async def delete_org(payload: DeleteOrg, auth_payload: dict = Depends(UserService.require_authorization), db: AsyncSession = Depends(get_db) ):
    """Delete organization detail."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    org_id = payload.org_id
    uam_repo = UAMRepository(db)
    orgs = await uam_repo.get_org_by_key({"org_id": org_id})
    if len(orgs) == 0:
        return {
            "header": {
                "code": 400,
                "message": "Organization ID does not exists.",
            },
            "response": {},
        }
    
    payload = {
        "org_id": org_id,
        "updated_by": token_data[0]["user_id"],
    }
    code, org_delete_message = await uam_repo.org_delete(payload)
    if code != 200:
        return {
            "header": {
                "code": code,
                "message": org_delete_message,
            },
            "response": {},
        }
    
    return {
            "header": {
                "code": 200,
                "message": UserMessages.SUCCESS,
            },
            "response": {},
        }


@router.post("/getroles")
async def get_roles(payload: RoleDetails, auth_payload: dict = Depends(UserService.require_authorization), db: AsyncSession = Depends(get_db) ):
    """Fetch all roles."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    uam_service = UAMRepository(db)
    role_details = await uam_service.get_all_roles()

    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": role_details
    }


@router.post("/createrole")
async def create_role(payload: CreateRole, auth_payload: dict = Depends(UserService.require_authorization), db: AsyncSession = Depends(get_db) ):
    """Create a new role."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    uam_service = UAMService(db)
    role_name = payload.role_name.strip()
    code, message = await uam_service.check_role_name(role_name)
    
    if code != 200:
        return {
            "header": {
                "code": code,
                "message": message,
            },
            "response": {},
        }
    
    uam_repo = UAMRepository(db)
    
    fetch_role = await uam_repo.get_role_by_key({"role_name": role_name})
    if len(fetch_role) > 0:
        return {
            "header": {
                "code": 400,
                "message": "Role name already exists.",
            },
            "response": {},
        }
    
    roles = await uam_repo.get_all_roles()    
    if not roles:
        next_role_id = "R00001"
    else:
        last_number = max(int(role["role_id"][1:]) for role in roles)
        next_role_id = f"R{last_number + 1:04d}"

    payload = {
        "role_name": role_name,
        "role_id": next_role_id,
        "updated_by": token_data[0]["user_id"],
        "action": "create"
    }
 
    code, role_entry_message = await uam_repo.role_entry(payload)
    if code != 200:
        return {
            "header": {
                "code": code,
                "message": role_entry_message,
            },
            "response": {},
        }

    return {
            "header": {
                "code": 200,
                "message": UserMessages.SUCCESS,
            },
            "response": {},
        }


@router.post("/editrole")
async def edit_role(payload: EditRole, auth_payload: dict = Depends(UserService.require_authorization), db: AsyncSession = Depends(get_db) ):
    """Edit a role."""
    if len(auth_payload) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    service = UserRepository(db)
    token_data = await service.get_token_data(payload.token)
    if len(token_data) == 0:
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    uam_service = UAMService(db)
    role_name = payload.role_name.strip()
    code, message = await uam_service.check_role_name(role_name)
    
    if code != 200:
        return {
            "header": {
                "code": code,
                "message": message,
            },
            "response": {},
        }
    
    uam_repo = UAMRepository(db)
    
    fetch_role = await uam_repo.get_role_by_key({"role_id": payload.role_id})
    if len(fetch_role) == 0:
        return {
            "header": {
                "code": 400,
                "message": "Role not found.",
            },
            "response": {},
        }

    payload = {
        "role_name": role_name,
        "role_id": payload.role_id,
        "updated_by": token_data[0]["user_id"],
        "action": "edit"
    }
 
    code, role_entry_message = await uam_repo.role_entry(payload)
    if code != 200:
        return {
            "header": {
                "code": code,
                "message": role_entry_message,
            },
            "response": {},
        }

    return {
            "header": {
                "code": 200,
                "message": UserMessages.SUCCESS,
            },
            "response": {},
        }


# @router.post("/orgs", response_model=OrganizationOut)
# async def add_org(org: OrganizationCreate, service: UAMService = Depends(get_uam_service)):
#     return await service.create_organization(org)

# @router.get("/orgs", response_model=List[OrganizationOut])
# async def list_orgs(service: UAMService = Depends(get_uam_service)):
#     return await service.get_organizations()

# Roles
# @router.post("/roles", response_model=RoleOut)
# async def add_role(role: RoleCreate, service: UAMService = Depends(get_uam_service)):
#     return await service.create_role(role)

# @router.get("/roles", response_model=List[RoleOut])
# async def list_roles(service: UAMService = Depends(get_uam_service)):
#     return await service.get_roles()

# @router.post("/roles/{role_id}/features", response_model=RoleOut)
# async def assign_role_features(role_id: int, features: FeatureAssign, service: UAMService = Depends(get_uam_service)):
#     role = await service.assign_features(role_id, features)
#     if not role:
#         raise HTTPException(status_code=404, detail="Role not found")
#     return role

# # Features
# @router.get("/features", response_model=List[FeatureOut])
# async def list_features(service: UAMService = Depends(get_uam_service)):
#     return await service.get_features()
