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
from core.logging import logger
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.uam import Organization, Role, Feature, FeatureGroup, RoleFeature
from models.user import User
from typing import List, Optional



router = APIRouter()

def get_uam_service(db: AsyncSession = Depends(get_db)) -> UAMService:
    return UAMService(UAMRepository(db))

@router.post("/tabslist")
async def user_permission_tabs(
    payload: TabsList,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Return the list of accessible UI tabs for an authenticated user."""
    logger.info("Fetching user permission tabs")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
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
            "icon": "Building2",
        },
        {"tab_name": "Roles", "access": 1, "add_button": "Role", "icon": "Shield"},
        {"tab_name": "Users", "access": 1, "add_button": "User", "icon": "Users"},
    ]

    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": tab_data,
    }


@router.post("/getorgs")
async def list_of_organizations(
    payload: OrgDetails,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Fetch all organizations accessible to an authenticated user."""
    logger.info(f"Fetching list of organizations with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    # Feature-Based Permission Check
    # Required: Feature="Organizations", Level=READ (2)
    actor_user_id = token_data[0]["user_id"]
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
         return {
            "header": {
                "code": 403,
                "message": "Actor user not found.",
            },
            "response": {},
        }
    
    actor_role_id = actor_user_details.get("role_id")
    uam_repo = UAMRepository(db)
    
    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Users",
        "required_level": 3 # WRITE
    })

    if not has_permission:
        logger.info(f"Insufficient permissions: User {actor_user_id} lacks WRITE access to 'Users'")
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need WRITE access to 'Users' feature.",
            },
            "response": {},
        }

    uam_service = UAMRepository(db)
    payload = {"action": "info"}
    org_details = await uam_service.get_all_orgs(payload)

    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": org_details,
    }


@router.post("/createorg")
async def create_organizations(
    payload: CreateOrg,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Create a new organization."""
    logger.info(f"Creating organization with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
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
        logger.info("Invalid organization name")
        return {
            "header": {
                "code": code,
                "message": message,
            },
            "response": {},
        }

    uam_repo = UAMRepository(db)

    # Feature-Based Permission Check
    # Required: Feature="Organizations", Level=WRITE (3)
    actor_user_id = token_data[0]["user_id"]
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
         return {
            "header": {
                "code": 403,
                "message": "Actor user not found.",
            },
            "response": {},
        }
    
    actor_role_id = actor_user_details.get("role_id")
    
    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Organizations",
        "required_level": 3 # WRITE
    })

    if not has_permission:
        logger.info(f"Insufficient permissions: User {actor_user_id} lacks WRITE access to 'Organizations'")
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need WRITE access to 'Organizations' feature.",
            },
            "response": {},
        }

    fetch_org = await uam_repo.get_org_by_key({"org_name": org_name})
    if len(fetch_org) > 0:
        logger.info("Organization name already exists")
        return {
            "header": {
                "code": 400,
                "message": "Organization name already exists.",
            },
            "response": {},
        }
    payload = {"action": "create"}
    orgs = await uam_repo.get_all_orgs(payload)
    if not orgs:
        logger.info("No organizations found")
        next_org_id = "ORG00001"
    else:
        last_number = max(int(org["org_id"][3:]) for org in orgs)
        next_org_id = f"ORG{last_number + 1:04d}"

    payload = {
        "org_name": org_name,
        "org_id": next_org_id,
        "updated_by": token_data[0]["user_id"],
        "action": "create",
    }

    code, org_entry_message = await uam_repo.org_entry(payload)
    if code != 200:
        logger.info("Organization entry failed")
        return {
            "header": {
                "code": code,
                "message": org_entry_message,
            },
            "response": {},
        }
    UserService.update_uam_log(token_data[0]["user_id"], "createorg", payload)
    # logger.info(f"Organization created successfully: {org_name}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/editorg")
async def edit_organizations(
    payload: EditOrg,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Edit organization detail."""
    logger.info(f"Editing organization with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
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

    # Feature-Based Permission Check
    # Required: Feature="Organizations", Level=WRITE (3)
    actor_user_id = token_data[0]["user_id"]
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
         return {
            "header": {
                "code": 403,
                "message": "Actor user not found.",
            },
            "response": {},
        }
    
    actor_role_id = actor_user_details.get("role_id")
    
    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Organizations",
        "required_level": 3 # WRITE
    })

    if not has_permission:
        logger.info(f"Insufficient permissions: User {actor_user_id} lacks WRITE access to 'Organizations'")
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need WRITE access to 'Organizations' feature.",
            },
            "response": {},
        }

    orgs = await uam_repo.get_org_by_key({"org_id": org_id})
    if len(orgs) == 0:
        logger.info("Invalid organization details")
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
        "action": "edit",
    }

    code, org_entry_message = await uam_repo.org_entry(payload)
    if code != 200:
        logger.info("Organization entry failed")
        return {
            "header": {
                "code": code,
                "message": org_entry_message,
            },
            "response": {},
        }
    UserService.update_uam_log(token_data[0]["user_id"], "editorg", payload)
    # logger.info(f"Organization edited successfully: {org_name}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/deleteorg")
async def delete_organizations(
    payload: DeleteOrg,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Delete organization detail."""
    logger.info(f"Deleting organization with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    org_id = payload.org_id
    uam_repo = UAMRepository(db)
    
    # Feature-Based Permission Check
    # Required: Feature="Organizations", Level=DELETE (4)
    actor_user_id = token_data[0]["user_id"]
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
         return {
            "header": {
                "code": 403,
                "message": "Actor user not found.",
            },
            "response": {},
        }
    
    actor_role_id = actor_user_details.get("role_id")
    
    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Organizations",
        "required_level": 4 # DELETE
    })

    if not has_permission:
        logger.info(f"Insufficient permissions: User {actor_user_id} lacks DELETE access to 'Organizations'")
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need DELETE access to 'Organizations' feature.",
            },
            "response": {},
        }

    orgs = await uam_repo.get_org_by_key({"org_id": org_id})
    if len(orgs) == 0:
        logger.info("Invalid organization details")
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
        logger.info("Organization delete failed")
        return {
            "header": {
                "code": code,
                "message": org_delete_message,
            },
            "response": {},
        }

    UserService.update_uam_log(token_data[0]["user_id"], "deleteorg", payload)
    # logger.info(f"Organization deleted successfully: {org_id}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/getroles")
async def get_roles(
    payload: RoleDetails,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Fetch all roles."""
    logger.info(f"Fetching all roles with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    # Feature-Based Permission Check
    # Required: Feature="Roles", Level=READ (2)
    actor_user_id = token_data[0]["user_id"]
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
         return {
            "header": {
                "code": 403,
                "message": "Actor user not found.",
            },
            "response": {},
        }
    
    actor_role_id = actor_user_details.get("role_id")
    uam_repo = UAMRepository(db)
    
    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Users",
        "required_level": 3 # WRITE
    })

    if not has_permission:
        logger.info(f"Insufficient permissions: User {actor_user_id} lacks WRITE access to 'Users'")
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need WRITE access to 'Users' feature.",
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
        "response": role_details,
    }


@router.post("/createrole")
async def create_role(
    payload: CreateRole,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Create a new role."""
    logger.info(f"Creating role with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
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
        logger.info("Invalid role name")
        return {
            "header": {
                "code": code,
                "message": message,
            },
            "response": {},
        }

    # Feature-Based Permission Check
    # Required: Feature="Roles", Level=WRITE (3)
    actor_user_id = token_data[0]["user_id"]
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
         return {
            "header": {
                "code": 403,
                "message": "Actor user not found.",
            },
            "response": {},
        }
    
    actor_role_id = actor_user_details.get("role_id")
    uam_repo = UAMRepository(db)

    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Roles",
        "required_level": 3 # WRITE
    })

    if not has_permission:
        logger.info(f"Insufficient permissions: User {actor_user_id} lacks WRITE access to 'Roles'")
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need WRITE access to 'Roles' feature.",
            },
            "response": {},
        }

    fetch_role = await uam_repo.get_role_by_key({"role_name": role_name})
    if len(fetch_role) > 0:
        logger.info("Role name already exists")
        return {
            "header": {
                "code": 400,
                "message": "Role name already exists.",
            },
            "response": {},
        }
    # if str(payload.permission_level) not in ["1", "2", "3", "4"]:
    #     logger.info("Invalid permission level.")
    #     return {
    #         "header": {
    #             "code": 400,
    #             "message": "Invalid permission level.",
    #         },
    #         "response": {},
    #     }    

    roles = await uam_repo.get_all_roles()
    if not roles:
        next_role_id = "R00001"
    else:
        last_number = max(int(role["role_id"][1:]) for role in roles)
        next_role_id = f"R{last_number + 1:04d}"

    payload = {
        "role_name": role_name,
        "role_id": next_role_id,
        # "permission_level": payload.permission_level,
        "updated_by": token_data[0]["user_id"],
        "action": "create",
    }

    code, role_entry_message = await uam_repo.role_entry(payload)
    if code != 200:
        logger.info("Role entry failed")
        return {
            "header": {
                "code": code,
                "message": role_entry_message,
            },
            "response": {},
        }
    UserService.update_uam_log(token_data[0]["user_id"], "createrole", payload)
    # logger.info(f"Role created successfully: {role_name}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/editrole")
async def edit_role(
    payload: EditRole,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Edit a role."""
    logger.info(f"Editing role with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
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
        logger.info("Invalid role name")
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
        logger.info("Role not found")
        return {
            "header": {
                "code": 400,
                "message": "Role not found.",
            },
            "response": {},
        }

    # if str(payload.permission_level) not in ["1", "2", "3", "4"]:
    #     logger.info("Invalid permission level.")
    #     return {
    #         "header": {
    #             "code": 400,
    #             "message": "Invalid permission level.",
    #         },
    #         "response": {},
    #     }

    # Actor Permission Check
    actor_user_id = token_data[0]["user_id"]
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
         return {
            "header": {
                "code": 403,
                "message": "Actor user not found.",
            },
            "response": {},
        }
    
    # Feature-Based Permission Check
    # Required: Feature="Roles", Level=WRITE (3)
    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Roles",
        "required_level": 3 # WRITE
    })

    if not has_permission:
        logger.info(f"Insufficient permissions: User {actor_user_id} lacks WRITE access to 'Roles'")
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need WRITE access to 'Roles' feature.",
            },
            "response": {},
        }
    
    # Self-Sabotage Check (Legacy Logic on Permission Level)
    # Fetch global permission level for self-check
    # actor_permission_level = await uam_repo.get_role_permission_level(actor_role_id)

    # Self-Sabotage Check: Actor cannot lower their own permission level
    # If the target role is the same as the actor's role
    if payload.role_id == actor_role_id:
        # if actor_permission_level is not None and payload.permission_level < actor_permission_level:
        logger.info(f"User {actor_user_id} attempted to lower their own permission level.")
        return {
            "header": {
                "code": 400,
                "message": "You cannot lower your own permission level.",
            },
            "response": {},
        }

    payload = {
        "role_name": role_name,
        "role_id": payload.role_id,
        # "permission_level": payload.permission_level,
        "updated_by": token_data[0]["user_id"],
        "action": "edit",
    }

    code, role_entry_message = await uam_repo.role_entry(payload)
    if code != 200:
        logger.info("Role entry failed")
        return {
            "header": {
                "code": code,
                "message": role_entry_message,
            },
            "response": {},
        }
    UserService.update_uam_log(token_data[0]["user_id"], "editrole", payload)
    # logger.info(f"Role edited successfully: {role_name}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/deleterole")
async def delete_role(
    payload: DeleteRole,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Delete a role."""
    logger.info(f"Deleting role with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    uam_repo = UAMRepository(db)
    
    # Feature-Based Permission Check
    # Required: Feature="Roles", Level=DELETE (4)
    actor_user_id = token_data[0]["user_id"]
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
         return {
            "header": {
                "code": 403,
                "message": "Actor user not found.",
            },
            "response": {},
        }
    
    actor_role_id = actor_user_details.get("role_id")
    
    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Roles",
        "required_level": 4 # DELETE
    })

    if not has_permission:
        logger.info(f"Insufficient permissions: User {actor_user_id} lacks DELETE access to 'Roles'")
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need DELETE access to 'Roles' feature.",
            },
            "response": {},
        }

    fetch_role = await uam_repo.get_role_by_key({"role_id": payload.role_id})
    if len(fetch_role) == 0:
        logger.info("Role not found")
        return {
            "header": {
                "code": 400,
                "message": "Role not found.",
            },
            "response": {},
        }

    payload = {
        "role_id": payload.role_id,
        "updated_by": token_data[0]["user_id"],
    }

    code, role_delete_message = await uam_repo.role_delete(payload)
    if code != 200:
        logger.info("Role delete failed")
        return {
            "header": {
                "code": code,
                "message": role_delete_message,
            },
            "response": {},
        }
    UserService.update_uam_log(token_data[0]["user_id"], "deleterole", payload)
    # logger.info(f"Role deleted successfully: {payload['role_id']}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }



@router.post("/getfeatures")
async def get_list_of_features_in_feature_group(
    payload: GetFeatures,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Return all features."""
    logger.info(f"Fetching features with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    role_id = payload.role_id
    uam_repo = UAMRepository(db)
    features = await uam_repo.feature_list(role_id)
    if len(features) == 0:
        logger.info("No features found")
        return {
            "header": {
                "code": 400,
                "message": "No features found.",
            },
            "response": {},
        }

    
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": features,
    }


@router.post("/featureassign")
async def bulk_feature_assign(
    payload: FeatureAssignRequest,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Assign multiple features to roles."""
    logger.info(f"Assigning features with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    uam_repo = UAMRepository(db)
    # 1. Check Actor's Permission Level
    # Fetch actor's role to get permission level
    actor_user_id = token_data[0]["user_id"]
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
         return {
            "header": {
                "code": 400,
                "message": "Actor user not found.",
            },
            "response": {},
        }
    
    actor_role_id = actor_user_details.get("role_id")

    # Feature-Based Permission Check
    # Required: Feature="Roles", Level=WRITE (3)
    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Roles",
        "required_level": 3 # WRITE
    })
    
    if not has_permission:
        logger.info(f"Insufficient permissions. User {actor_user_id} lacks WRITE access to 'Roles'")
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need WRITE access to 'Roles' feature.",
            },
            "response": {},
        }

    
    
    # Prepare payload for repository
    repo_payload = {
        "features": payload.features,
        "updated_by": token_data[0]["user_id"]
    }

    code, message = await uam_repo.bulk_assign_features(repo_payload)
    
    if code != 200:
        logger.info(f"Feature assignment failed: {message}")
        return {
            "header": {
                "code": code,
                "message": message,
            },
            "response": {},
        }

    UserService.update_uam_log(token_data[0]["user_id"], "featureassign", repo_payload)
    # logger.info("Features assigned successfully")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/createfeaturegrp")
async def create_feature_group(
    payload: CreateFeatureGroup,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Create a new feature group."""
    logger.info(f"Creating feature group with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    uam_service = UAMService(db)
    feature_grp_name = payload.feature_grp_name.strip()
    code, message = await uam_service.validate_feature_name(feature_grp_name)

    if code != 200:
        logger.info("Invalid feature group name")
        return {
            "header": {
                "code": code,
                "message": message,
            },
            "response": {},
        }

    uam_repo = UAMRepository(db)

    fetch_feature_group = await uam_repo.get_feature_group_by_key(
        {"feature_grp_name": feature_grp_name}
    )
    if len(fetch_feature_group) > 0:
        logger.info("Feature group name already exists")
        return {
            "header": {
                "code": 400,
                "message": "Feature group name already exists.",
            },
            "response": {},
        }

    feature_groups = await uam_repo.get_all_feature_groups()
    if not feature_groups:
        next_feature_grp_id = "FGR00001"
    else:
        last_number = max(
            int(feature_group["feature_grp_id"][3:]) for feature_group in feature_groups
        )
        next_feature_grp_id = f"FGR{last_number + 1:04d}"

    payload = {
        "feature_grp_name": feature_grp_name,
        "feature_grp_id": next_feature_grp_id,
        "updated_by": token_data[0]["user_id"],
        "action": "create",
    }

    code, feature_group_entry_message = await uam_repo.feature_group_entry(payload)
    if code != 200:
        logger.info("Feature group entry failed")
        return {
            "header": {
                "code": code,
                "message": feature_group_entry_message,
            },
            "response": {},
        }
    UserService.update_uam_log(token_data[0]["user_id"], "createfeaturegroup", payload)
    # logger.info(f"Feature group created successfully: {feature_grp_name}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/createfeature")
async def create_feature(
    payload: CreateFeature,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Create a new feature."""
    logger.info(f"Creating feature with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    uam_service = UAMService(db)
    feature_name = payload.feature_name.strip()
    feature_grp_id = payload.feature_grp_id.strip()
    code, message = await uam_service.validate_feature_name(feature_name)

    if code != 200:
        logger.info("Invalid feature name")
        return {
            "header": {
                "code": code,
                "message": message,
            },
            "response": {},
        }

    uam_repo = UAMRepository(db)

    fetch_feature_group = await uam_repo.get_feature_group_by_key(
        {"feature_grp_id": feature_grp_id}
    )
    if len(fetch_feature_group) == 0:
        logger.info("Feature group not found")
        return {
            "header": {
                "code": 400,
                "message": "Feature group not found.",
            },
            "response": {},
        }

    get_feature_by_key = await uam_repo.get_feature_by_key(
        {"feature_name": feature_name}
    )
    if len(get_feature_by_key) > 0:
        logger.info("Feature name already exists")
        return {
            "header": {
                "code": 400,
                "message": "Feature name already exists.",
            },
            "response": {},
        }

    get_feature = await uam_repo.get_all_feature()
    if not get_feature:
        next_feature_id = "F00001"
    else:
        last_number = max(int(feature["feature_id"][1:]) for feature in get_feature)
        next_feature_id = f"F{last_number + 1:04d}"

    payload = {
        "feature_name": feature_name,
        "feature_id": next_feature_id,
        "feature_grp_id": feature_grp_id,
        "updated_by": token_data[0]["user_id"],
        "action": "create",
    }

    code, feature_entry_message = await uam_repo.feature_entry(payload)
    if code != 200:
        logger.info("Feature entry failed")
        return {
            "header": {
                "code": code,
                "message": feature_entry_message,
            },
            "response": {},
        }

    UserService.update_uam_log(token_data[0]["user_id"], "createfeature", payload)
    # logger.info(f"Feature created successfully: {feature_name}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/deletefeature")
async def delete_feature(
    payload: DeleteFeature,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Delete a feature."""
    logger.info(f"Deleting feature with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    uam_repo = UAMRepository(db)
    feature_id = payload.feature_id.strip()

    feature_assigned_to_role = await uam_repo.get_feature_assigned_to_role(feature_id)
    if len(feature_assigned_to_role) > 0:
        logger.info("Feature can't be deleted as it is assigned to role.")
        return {
            "header": {
                "code": 400,
                "message": "Feature can't be deleted as it is assigned to role.",
            },
            "response": {},
        }

    payload = {
        "feature_id": feature_id,
        "action": "delete",
    }
    code, feature_delete_message = await uam_repo.feature_group_entry(payload)
    if code != 200:
        logger.info("Feature delete failed")
        return {
            "header": {
                "code": code,
                "message": feature_delete_message,
            },
            "response": {},
        }

    UserService.update_uam_log(token_data[0]["user_id"], "deletefeature", payload)
    # logger.info(f"Feature deleted successfully: {feature_id}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/featurerolelist")
async def feature_role_list(
    payload: FeatureRoleList,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Fetch all features accessible to an authenticated user."""
    logger.info(f"Fetching feature role list with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    uam_service = UAMRepository(db)
    role_feature_mapping = await uam_service.get_role_feature_mapping(
        role_id=payload.role_id
    )

    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": role_feature_mapping,
    }


@router.post("/edituser")
async def edit_user(
    payload: EditUserRequest,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Edit user details with permission checks."""
    logger.info(f"Editing user with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }
    
    actor_user_id = token_data[0]["user_id"]
    uam_repo = UAMRepository(db)

    # 1. Check Actor's Permission Level
    # Fetch actor's role to get permission level
    actor_user_details = await service.get_user_details(actor_user_id)
    if not actor_user_details:
         return {
            "header": {
                "code": 400,
                "message": "Actor user not found.",
            },
            "response": {},
        }
    
    actor_role_id = actor_user_details.get("role_id")
    actor_role = await uam_repo.get_role_by_key({"role_id": actor_role_id})
    
    # Feature-Based Permission Check
    # Required: Feature="Users", Level=WRITE (3)
    has_permission = await uam_repo.check_feature_permission({
        "role_id": actor_role_id,
        "feature_name": "Users",
        "required_level": 3 # WRITE
    })
    
    if not has_permission:
        logger.info(f"Insufficient permissions. User {actor_user_id} lacks WRITE access to 'Users'")
        return {
            "header": {
                "code": 403,
                "message": "Insufficient permissions. You need WRITE access to 'Users' feature.",
            },
            "response": {},
        }

    # 2. Self-Edit Check
    target_user_id = payload.user_id
    if actor_user_id == target_user_id:
        # Check if trying to change Role or Org
        # We need current user's role and org. We already have `actor_user_details`.
        # current_role_id = actor_user_details.get("role_id")
        # current_org_id = actor_user_details.get("org_id")
        
        # if payload.role_id != current_role_id or payload.org_id != current_org_id:
        logger.info(f"User {actor_user_id} attempted to change their own role/org.")
        return {
            "header": {
                "code": 400,
                "message": "You cannot update your own Role or Organization.",
            },
            "response": {},
        }

    # 3. Validate Existence of New Role/Org
    # Check Org
    if not await uam_repo.check_org_exists(payload.org_id):
         return {
            "header": {
                "code": 400,
                "message": "Invalid Organization ID.",
            },
            "response": {},
        }
        
    # Check Role
    if not await uam_repo.check_role_exists(payload.role_id):
         return {
            "header": {
                "code": 400,
                "message": "Invalid Role ID.",
            },
            "response": {},
        }

    # 4. Perform Update
    # We call uam_repo.edit_user_details
    repo_payload = payload.dict() 
    repo_payload["updated_by"] = actor_user_id
    code, message = await uam_repo.edit_user_details(repo_payload)

    if code != 200:
        return {
            "header": {
                "code": code,
                "message": message,
            },
            "response": {},
        }

    UserService.update_uam_log(actor_user_id, "edituser", repo_payload)
    logger.info(f"User {target_user_id} edited successfully by {actor_user_id}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/editrolefeature")
async def edit_access_level_of_feature_which_is_assigned_to_role(
    payload: EditFeatureRole,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Edit features to a role."""
    logger.info(f"Editing feature role assignment with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    role_id = payload.role_id
    feature_id = payload.feature_id
    permission_level = payload.permission_level

    uam_service = UAMRepository(db)
    role_feature_mapping = await uam_service.feature_role_mapping(role_id, feature_id)
    if len(role_feature_mapping) != 1:
        logger.info("Invalid detail found.")
        return {
            "header": {
                "code": 400,
                "message": "Invalid detail found.",
            },
            "response": {},
        }

    if str(permission_level) not in ["1", "2", "3", "4"]:
        logger.info("Invalid permission level.")
        return {
            "header": {
                "code": 400,
                "message": "Invalid permission level.",
            },
            "response": {},
        }

    payload = {
        "role_id": role_id,
        "feature_id": feature_id,
        "permission_level": permission_level,
        "updated_by": token_data[0]["user_id"],
        "action": "edit",
    }

    code, role_feature_mapping = await uam_service.create_feature_role_mapping(payload)
    if code != 200:
        logger.info("Feature role assignment edited failed.")
        return {
            "header": {
                "code": code,
                "message": role_feature_mapping,
            },
            "response": {},
        }
    UserService.update_uam_log(token_data[0]["user_id"], "editfeaturerole", payload)
    logger.info(f"Feature role assignment edited successfully. Role: {role_id}, Feature: {feature_id},updated_by: {token_data[0]['user_id']}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }


@router.post("/deletefeaturerole")
async def delete_feature_from_role(
    payload: DeleteFeatureRole,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Delete features of a role."""
    logger.info(f"Deleting feature from role with payload: {payload}")
    if len(auth_payload) == 0:
        logger.info("auth_payload is empty Invalid credentials")
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
        logger.info("token not found Invalid credentials")
        return {
            "header": {
                "code": 400,
                "message": UserMessages.INVALID_CREDENTIALS,
            },
            "response": {},
        }

    role_id = payload.role_id
    feature_id = payload.feature_id

    uam_service = UAMRepository(db)
    role_feature_mapping = await uam_service.feature_role_mapping(role_id, feature_id)
    if len(role_feature_mapping) != 1:
        logger.info("Invalid detail found.")
        return {
            "header": {
                "code": 400,
                "message": "Invalid detail found.",
            },
            "response": {},
        }

    payload = {
        "role_id": role_id,
        "feature_id": feature_id,
        "updated_by": token_data[0]["user_id"],
        "action": "delete",
    }

    code, role_feature_mapping = await uam_service.create_feature_role_mapping(payload)
    if code != 200:
        logger.info("Feature role assignment deleted failed.")
        return {
            "header": {
                "code": code,
                "message": role_feature_mapping,
            },
            "response": {},
        }

    UserService.update_uam_log(token_data[0]["user_id"], "deletefeaturerole", payload)
    # logger.info(f"Feature deleted from role successfully. Role: {role_id}, Feature: {feature_id},updated_by: {token_data[0]['user_id']}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }

