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

    uam_service = UAMRepository(db)
    org_details = await uam_service.get_all_orgs()

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

    orgs = await uam_repo.get_all_orgs()
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
    logger.info(f"Organization created successfully: {org_name}")
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
    logger.info(f"Organization edited successfully: {org_name}")
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
    logger.info(f"Organization deleted successfully: {org_id}")
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

    uam_repo = UAMRepository(db)

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
    logger.info(f"Role created successfully: {role_name}")
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

    payload = {
        "role_name": role_name,
        "role_id": payload.role_id,
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
    logger.info(f"Role edited successfully: {role_name}")
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

    uam_repo = UAMRepository(db)
    features = await uam_repo.feature_list()
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
    logger.info(f"Feature group created successfully: {feature_grp_name}")
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
    logger.info(f"Feature created successfully: {feature_name}")
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
    logger.info(f"Feature deleted successfully: {feature_id}")
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


@router.post("/featureassign")
async def assign_feature_to_role(
    payload: AssignFeatureToRole,
    auth_payload: dict = Depends(UserService.require_authorization),
    db: AsyncSession = Depends(get_db),
):
    """Assign features to a role."""
    logger.info(f"Assigning feature to role with payload: {payload}")
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
    if len(role_feature_mapping) > 0:
        logger.info("Feature already assigned to role.")
        return {
            "header": {
                "code": 400,
                "message": "Feature already assigned to role.",
            },
            "response": {},
        }

    role_id_list = await uam_service.get_role_feature_mapping(role_id)
    if len(role_id_list) == 0:
        logger.info("Role not found.")
        return {
            "header": {
                "code": 400,
                "message": "Role not found.",
            },
            "response": {},
        }

    role_id_list = await uam_service.get_feature_by_key({"feature_id": feature_id})
    if len(role_id_list) == 0:
        logger.info("Feature not found.")
        return {
            "header": {
                "code": 400,
                "message": "Feature not found.",
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
        "action": "create",
    }

    code, role_feature_mapping = await uam_service.create_feature_role_mapping(payload)
    if code != 200:
        logger.info("Feature assignment failed")
        return {
            "header": {
                "code": code,
                "message": role_feature_mapping,
            },
            "response": {},
        }
    
    UserService.update_uam_log(token_data[0]["user_id"], "assignfeaturetorole", payload)
    logger.info(f"Feature assigned to role successfully. Role: {role_id}, Feature: {feature_id} ,updated_by: {token_data[0]["user_id"]}")
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
    logger.info(f"Feature role assignment edited successfully. Role: {role_id}, Feature: {feature_id},updated_by: {token_data[0]["user_id"]}")
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
    logger.info(f"Feature deleted from role successfully. Role: {role_id}, Feature: {feature_id},updated_by: {token_data[0]["user_id"]}")
    return {
        "header": {
            "code": 200,
            "message": UserMessages.SUCCESS,
        },
        "response": {},
    }

