# app/services/uam_service.py
from repositories.uam_repo import UAMRepository
from schemas.uam import OrganizationCreate, RoleCreate, FeatureAssign
from typing import List
from fastapi import HTTPException, status
import re

class UAMService:
    def __init__(self, uam_repo: UAMRepository):
        self.uam_repo = uam_repo

    async def create_organization(self, org_data: OrganizationCreate):
        return await self.uam_repo.create_org(org_data.name, org_data.code)

    async def get_organizations(self):
        return await self.uam_repo.get_all_orgs()

    async def create_role(self, role_data: RoleCreate):
        return await self.uam_repo.create_role(role_data.name, role_data.description)

    async def get_roles(self):
        return await self.uam_repo.get_all_roles()

    async def get_features(self):
        return await self.uam_repo.get_all_features()
    
    async def assign_features(self, role_id: int, feature_data: FeatureAssign):
        return await self.uam_repo.assign_features_to_role(role_id, feature_data.feature_ids)
    
    async def check_org_name(self, org_name: str):
        if not isinstance(org_name, str):
            return 400, "Organization name must be a string"

        if not org_name:
            return 400, "Organization name cannot be empty"

        if len(org_name) < 2 or len(org_name) > 100:
            return 400, "Organization name must be between 2 and 100 characters"

        if not re.match(r"^[A-Za-z0-9 _-]+$", org_name):
            return 400, "Organization name contains invalid characters"
        
        if not re.search(r"[A-Za-z]", org_name):
            return 400, "Organization name must contain at least one alphabet"
        
        return 200, "Organization name is valid"

    async def check_role_name(self, role_name: str):
        if not isinstance(role_name, str):
            return 400, "Role name must be a string"

        if not role_name:
            return 400, "Role name cannot be empty"

        if len(role_name) < 2 or len(role_name) > 100:
            return 400, "Role name must be between 2 and 100 characters"

        if not re.match(r"^[A-Za-z0-9 _-]+$", role_name):
            return 400, "Role name contains invalid characters"
        
        if not re.search(r"[A-Za-z]", role_name):
            return 400, "Role name must contain at least one alphabet"
        
        return 200, "Role name is valid"

    
    async def validate_feature_name(self, feature_grp_name: str):
        if not isinstance(feature_grp_name, str):
            return 400, "Feature group name must be a string"

        if not feature_grp_name:
            return 400, "Feature group name cannot be empty"

        if len(feature_grp_name) < 2 or len(feature_grp_name) > 100:
            return 400, "Feature group name must be between 2 and 100 characters"
        
        return 200, "Feature group name is valid"