# app/services/uam_service.py
from repositories.uam_repo import UAMRepository
from schemas.uam import OrganizationCreate, RoleCreate, FeatureAssign
from typing import List
from fastapi import HTTPException, status
import re
from core.logging import logger


class UAMService:
    def __init__(self, uam_repo: UAMRepository):
        self.uam_repo = uam_repo

    async def check_org_name(self, org_name: str):
        logger.info(f"Validating organization name: {org_name}")
        if not isinstance(org_name, str):
            return 400, "Organization name must be a string"

        if not org_name:
            return 400, "Organization name cannot be empty"

        if len(org_name) < 2 or len(org_name) > 100:
            return 400, "Organization name must be between 2 and 100 characters"

        if not re.match(r"^[A-Za-z0-9 _-]+$", org_name):
            return 400, "Organization name contains invalid characters"

        if not re.search(r"[A-Za-z]", org_name):
            logger.warning(f"Organization name validation failed: {org_name} (No alphabet)")
            return 400, "Organization name must contain at least one alphabet"


        return 200, "Organization name is valid"

    async def check_role_name(self, role_name: str):
        logger.info(f"Validating role name: {role_name}")
        if not isinstance(role_name, str):
            return 400, "Role name must be a string"

        if not role_name:
            return 400, "Role name cannot be empty"

        if len(role_name) < 2 or len(role_name) > 100:
            return 400, "Role name must be between 2 and 100 characters"

        if not re.match(r"^[A-Za-z0-9 _-]+$", role_name):
            return 400, "Role name contains invalid characters"

        if not re.search(r"[A-Za-z]", role_name):
            logger.warning(f"Role name validation failed: {role_name} (No alphabet)")
            return 400, "Role name must contain at least one alphabet"

        return 200, "Role name is valid"

    async def validate_feature_name(self, feature_grp_name: str):
        logger.info(f"Validating feature group name: {feature_grp_name}")
        if not isinstance(feature_grp_name, str):
            return 400, "Feature group name must be a string"

        if not feature_grp_name:
            return 400, "Feature group name cannot be empty"

        if len(feature_grp_name) < 2 or len(feature_grp_name) > 100:
            return 400, "Feature group name must be between 2 and 100 characters"

        return 200, "Feature group name is valid"
