# app/repositories/uam_repo.py
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models.uam import Organization, Role, Feature, FeatureGroup, RoleFeature
from models.user import User
from typing import List, Optional
from core.logging import logger


class UAMRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Organization
    async def get_all_orgs(self, payload: dict) -> list:
        """Retrieves a list of all active organizations with their IDs and names."""
        logger.info("Fetching all active organizations")
        action = payload.get("action", "info")
        if action == "info":
            result = await self.db.execute(
                select(Organization.org_id, Organization.org_name)
                .where(Organization.is_active == 1)
                .order_by(Organization.id.asc())
            )
            return [
                {"org_id": row.org_id, "org_name": row.org_name} for row in result.all()
            ]
        elif action == "create":    
            result = await self.db.execute(
                select(Organization.org_id, Organization.org_name)
                .order_by(Organization.id.asc())
            )
            return [
                {"org_id": row.org_id, "org_name": row.org_name} for row in result.all()
            ]

    async def get_org_by_key(self, payload: dict) -> Optional[Organization]:
        """Fetches an organization based on the provided organization name or ID."""
        logger.info(f"Fetching organization with payload: {payload}")
        if "org_name" in payload:
            result = await self.db.execute(
                select(Organization.org_id, Organization.org_name)
                .where(
                    Organization.org_name == payload["org_name"],
                    Organization.is_active == 1,
                )
                .order_by(Organization.id.asc())
            )
            return [
                {"org_id": row.org_id, "org_name": row.org_name} for row in result.all()
            ]
        elif "org_id" in payload:
            result = await self.db.execute(
                select(Organization.org_id, Organization.org_name)
                .where(
                    Organization.org_id == payload["org_id"],
                    Organization.is_active == 1,
                )
                .order_by(Organization.id.asc())
            )
            return [
                {"org_id": row.org_id, "org_name": row.org_name} for row in result.all()
            ]

    async def org_entry(self, payload: dict) -> tuple:
        """Creates or updates an organization record based on the action specified in the payload."""
        try:
            logger.info(f"Processing org_entry with payload: {payload}")
            if payload["action"] == "create":
                org = Organization(
                    org_name=payload["org_name"],
                    org_id=payload["org_id"],
                    updated_by=payload["updated_by"],
                )
                self.db.add(org)
                await self.db.commit()
                await self.db.refresh(org)
                logger.info(f"Organization created successfully: {payload['org_name']},created_by: {payload['updated_by']}")
                return 200, "Success"
            elif payload["action"] == "edit":
                org = await self.db.scalar(
                    select(Organization).where(Organization.org_id == payload["org_id"])
                )
                if not org:
                    logger.info(f"Organization not found: {payload['org_id']},attempted_by: {payload['updated_by']}")
                    return 404, "Organization not found"

                result = await self.db.execute(
                    select(Organization.org_id, Organization.org_name).where(
                        Organization.org_name == payload["org_name"],
                        Organization.org_id != payload["org_id"],
                        Organization.is_active == 1,
                    )
                )
                check_org = [
                    {"org_id": row.org_id, "org_name": row.org_name}
                    for row in result.all()
                ]
                if len(check_org) > 0:
                    logger.info(f"Organization name already exists: {payload['org_name']},attempted_by: {payload['updated_by']}")
                    return 400, "Organization name already exists."

                org.org_name = payload["org_name"]
                org.updated_by = payload["updated_by"]

                await self.db.commit()
                logger.info(f"Organization updated successfully: {payload['org_name']},updated_by: {payload['updated_by']}")
                return 200, "Success"
        except Exception as e:
            logger.error(f"Error in org_entry: {str(e)}", exc_info=True)
            return 500, str(e)

    async def org_delete(self, payload: dict) -> tuple:
        """Soft deletes an organization if no users are currently assigned to it."""
        try:
            logger.info(f"Attempting to delete organization with payload: {payload}")
            org = await self.db.scalar(
                select(Organization).where(Organization.org_id == payload["org_id"])
            )

            if not org:
                logger.info(f"Organization not found: org_id: {payload['org_id']},attempted_by: {payload['updated_by']}")
                return 404, "Organization not found"

            org_users = await self.db.execute(
                select(User).where(
                    User.org_id == payload["org_id"], User.is_active == 1
                )
            )
            if org_users.scalars().first():
                logger.info(f"Deletion failed: users are currently assigned to this organization. ,attempted_by: {payload['updated_by']}")
                return (
                    400,
                    "Deletion failed: users are currently assigned to this organization.",
                )

            org.is_active = 0
            org.updated_by = payload["updated_by"]
            await self.db.commit()
            logger.info(f"Organization deleted successfully: org_id: {payload['org_id']},updated_by: {payload['updated_by']}")
            return 200, "Success"
        except Exception as e:
            logger.error(f"Error in org_delete: {str(e)}", exc_info=True)
            return 500, str(e)

    # Role
    async def get_all_roles(self) -> list:
        """Retrieves all active roles along with the count and names of assigned users."""
        logger.info("Fetching all active roles")
        result = await self.db.execute(
            select(Role.role_id, Role.role_name,Role.permission_level)
            .where(Role.is_active == 1)
            .order_by(Role.id.asc())
        )

        role_details = []

        for row in result.all():
            users_result = await self.db.execute(
                select(User.first_name, User.last_name).where(
                    User.role_id == row.role_id, User.is_active == 1
                )
            )

            users = users_result.all()  # list of Row objects

            role_details.append(
                {
                    "role_id": row.role_id,
                    "role_name": row.role_name,
                    "permission_level": row.permission_level,
                    "user_count": len(users),
                    "user_names": [f"{u.first_name} {u.last_name}" for u in users],
                }
            )

        return role_details

    async def get_role_by_key(self, payload: dict) -> Optional[Role]:
        """Fetches a role based on the provided role name or ID."""
        logger.info(f"Fetching role with payload: {payload}")
        if "role_name" in payload:
            result = await self.db.execute(
                select(Role.role_id, Role.role_name)
                .where(Role.role_name == payload["role_name"], Role.is_active == 1)
                .order_by(Role.id.asc())
            )
            return [
                {"role_id": row.role_id, "role_name": row.role_name}
                for row in result.all()
            ]
        elif "role_id" in payload:
            result = await self.db.execute(
                select(Role.role_id, Role.role_name)
                .where(Role.role_id == payload["role_id"], Role.is_active == 1)
                .order_by(Role.id.asc())
            )
            return [
                {"role_id": row.role_id, "role_name": row.role_name}
                for row in result.all()
            ]

    async def role_entry(self, payload: dict) -> tuple:
        """Creates or updates a role record based on the action specified in the payload."""
        try:
            logger.info(f"Processing role_entry with payload: {payload}")
            if payload["action"] == "create":
                role = Role(
                    role_name=payload["role_name"],
                    role_id=payload["role_id"],
                    # permission_level=payload.get("permission_level", 1),
                    updated_by=payload["updated_by"],
                )
                self.db.add(role)
                await self.db.commit()
                await self.db.refresh(role)
                logger.info(f"Role created successfully: role_id:{payload['role_id']},role_name:{payload['role_name']},updated_by: {payload['updated_by']}")
                return 200, "Success"
            elif payload["action"] == "edit":
                role = await self.db.scalar(
                    select(Role).where(Role.role_id == payload["role_id"])
                )
                if not role:
                    return 404, "Role not found"

                result = await self.db.execute(
                    select(Role.role_id, Role.role_name).where(
                        Role.role_name == payload["role_name"],
                        Role.role_id != payload["role_id"],
                        Role.is_active == 1,
                    )
                )
                check_role = [
                    {"role_id": row.role_id, "role_name": row.role_name}
                    for row in result.all()
                ]
                if len(check_role) > 0:
                    return 400, "Role name already exists."

                role.role_name = payload["role_name"]
                # role.permission_level = payload["permission_level"]
                role.updated_by = payload["updated_by"]

                await self.db.commit()
                logger.info(f"Role updated successfully: role_id:{payload['role_id']},role_name:{payload['role_name']},updated_by: {payload['updated_by']}")
                return 200, "Success"
        except Exception as e:
            logger.error(f"Error in role_entry: {str(e)}", exc_info=True)
            return 500, str(e)

    async def role_delete(self, payload: dict) -> tuple:
        """Soft deletes a role if no users are currently assigned to it."""
        try:
            logger.info(f"Attempting to delete role with payload: {payload}")
            role = await self.db.scalar(
                select(Role).where(Role.role_id == payload["role_id"])
            )

            if not role:
                logger.info(f"Role not found: role_id:{payload['role_id']},attempted_by: {payload['updated_by']}")
                return 404, "Role not found"

            role_users = await self.db.execute(
                select(User).where(
                    User.role_id == payload["role_id"], User.is_active == 1
                )
            )
            if role_users.scalars().first():
                logger.info(f"Deletion failed: users are currently assigned to this role. ,attempted_by: {payload['updated_by']}")
                return (
                    400,
                    "Deletion failed: users are currently assigned to this role.",
                )

            role.is_active = 0
            role.updated_by = payload["updated_by"]
            await self.db.commit()
            logger.info(f"Role deleted successfully: role_id:{payload['role_id']},updated_by: {payload['updated_by']}")
            return 200, "Success"
        except Exception as e:
            logger.error(f"Error in role_delete: {str(e)}", exc_info=True)
            return 500, str(e)

    # Feature
    async def feature_list(self, role_id: str):
        """Retrieves all features grouped by their feature group name, including permission levels for the specified role."""

        role = await self.db.scalar(
            select(Role).where(Role.role_id == role_id)
        )

        if not role:
            logger.info(f"Role not found: role_id:{role_id}")
            # handle in router or raise HTTPException
            return []

        result = await self.db.execute(
            select(
                FeatureGroup.feature_grp_id,
                FeatureGroup.feature_grp_name
            ).order_by(FeatureGroup.id.asc())
        )

        groups = result.all()
        feature_grp_list = []

        for row in groups:
            get_feature = await self.db.execute(
                select(
                    Feature.feature_id,
                    Feature.feature_name,
                    RoleFeature.permission_level,
                )
                .outerjoin(
                    RoleFeature,
                    (RoleFeature.feature_id == Feature.feature_id) &
                    (RoleFeature.role_id == role_id)   
                )
                .where(Feature.feature_grp_id == row.feature_grp_id)
            )

            feature_grp_list.append(
                {
                    "feature_grp_id": row.feature_grp_id,
                    "feature_grp_name": row.feature_grp_name,
                    "feature_list": [
                        {
                            "feature_id": f.feature_id,
                            "feature_name": f.feature_name,
                            "permission_level": f.permission_level or 1,  
                        }
                        for f in get_feature.all()
                    ],
                }
            )

        return feature_grp_list

    # async def feature_list(self,role_id:str):
    #     """Retrieves all features ordered by their ID."""
    #     logger.info("Fetching feature list")
    #     result = await self.db.execute(
    #         select(FeatureGroup.feature_grp_id, FeatureGroup.feature_grp_name).order_by(FeatureGroup.id.asc())
    #     )
    #     feature_grp_list = []
    #     for row in result.all():
    #         get_feature = await self.db.execute(
    #             select(Feature.feature_id, Feature.feature_name).where(Feature.feature_grp_id == row.feature_grp_id)
    #         )
    #         feature_grp_list.append({"feature_grp_id": row.feature_grp_id, "feature_grp_name": row.feature_grp_name, "feature_list": [{"feature_id": f.feature_id, "feature_name": f.feature_name} for f in get_feature.all()]})
    #     return feature_grp_list
     

    async def get_feature_group_by_key(self, payload: dict) -> Optional[FeatureGroup]:
        """Fetches a feature group based on the provided name or ID."""
        logger.info(f"Fetching feature group with payload: {payload}")
        if "feature_grp_name" in payload:
            result = await self.db.execute(
                select(FeatureGroup.feature_grp_id, FeatureGroup.feature_grp_name)
                .where(FeatureGroup.feature_grp_name == payload["feature_grp_name"])
                .order_by(FeatureGroup.id.asc())
            )
            data = [
                {
                    "feature_grp_id": row.feature_grp_id,
                    "feature_grp_name": row.feature_grp_name,
                }
                for row in result.all()
            ]
            return data
        elif "feature_grp_id" in payload:
            result = await self.db.execute(
                select(FeatureGroup.feature_grp_id, FeatureGroup.feature_grp_name)
                .where(FeatureGroup.feature_grp_id == payload["feature_grp_id"])
                .order_by(FeatureGroup.id.asc())
            )
            return [
                {
                    "feature_grp_id": row.feature_grp_id,
                    "feature_grp_name": row.feature_grp_name,
                }
                for row in result.all()
            ]

    async def get_feature_assigned_to_role(self, feature_id: str) -> Optional[Feature]:
        """Fetches a feature based on the provided feature ID."""
        logger.info(f"Checking if feature {feature_id} is assigned to any role")
        result = await self.db.execute(
            select(RoleFeature.role_id)
            .where(RoleFeature.feature_id == feature_id)
        )
        return [
            {
                "role_id": row.role_id,
            }
            for row in result.all()
        ]

    async def get_all_feature_groups(self):
        """Retrieves all feature groups ordered by their ID."""
        logger.info("Fetching all feature groups")
        result = await self.db.execute(
            select(FeatureGroup.feature_grp_id, FeatureGroup.feature_grp_name).order_by(
                FeatureGroup.id.asc()
            )
        )
        return [
            {
                "feature_grp_id": row.feature_grp_id,
                "feature_grp_name": row.feature_grp_name,
            }
            for row in result.all()
        ]

    async def feature_group_entry(self, payload: dict) -> tuple:
        """Creates or updates a feature group record based on the action specified in the payload."""
        try:
            logger.info(f"Processing feature_group_entry with payload: {payload}")
            if payload["action"] == "create":
                feature_group = FeatureGroup(
                    feature_grp_name=payload["feature_grp_name"],
                    feature_grp_id=payload["feature_grp_id"],
                    updated_by=payload["updated_by"],
                )
                self.db.add(feature_group)
                await self.db.commit()
                await self.db.refresh(feature_group)
                logger.info(f"Feature group created successfully: feature_grp_id:{payload['feature_grp_id']},feature_grp_name:{payload['feature_grp_name']},created_by: {payload['updated_by']}")
                return 200, "Success"
            elif payload["action"] == "edit":
                feature_group = await self.db.scalar(
                    select(FeatureGroup).where(
                        FeatureGroup.feature_grp_id == payload["feature_grp_id"]
                    )
                )
                if not feature_group:
                    logger.info(f"Feature group not found: feature_grp_id:{payload['feature_grp_id']},attempted_by: {payload['updated_by']}")
                    return 404, "Feature group not found"

                result = await self.db.execute(
                    select(
                        FeatureGroup.feature_grp_id, FeatureGroup.feature_grp_name
                    ).where(
                        FeatureGroup.feature_grp_name == payload["feature_grp_name"],
                        FeatureGroup.feature_grp_id != payload["feature_grp_id"],
                        FeatureGroup.is_active == 1,
                    )
                )
                check_feature_group = [
                    {
                        "feature_grp_id": row.feature_grp_id,
                        "feature_grp_name": row.feature_grp_name,
                    }
                    for row in result.all()
                ]
                if len(check_feature_group) > 0:
                    logger.info(f"Feature group name already exists: feature_grp_id:{payload['feature_grp_id']},feature_grp_name:{payload['feature_grp_name']},attempted_by: {payload['updated_by']}")
                    return 400, "Feature group name already exists."

                feature_group.feature_grp_name = payload["feature_grp_name"]
                feature_group.updated_by = payload["updated_by"]

                await self.db.commit()
                logger.info(f"Feature group updated successfully: feature_grp_id:{payload['feature_grp_id']},feature_grp_name:{payload['feature_grp_name']},updated_by: {payload['updated_by']}")
                return 200, "Success"
            elif payload["action"] == "delete":
                feature = await self.db.scalar(
                    select(Feature).where(
                        Feature.feature_id == payload["feature_id"],
                    )
                )
                if not feature:
                    logger.info(f"Feature not found: feature_id:{payload['feature_id']},attempted_by: {payload['updated_by']}")
                    return 404, "Feature not found"
                await self.db.delete(feature)
                await self.db.commit()
                logger.info(f"Feature deleted successfully: feature_id:{payload['feature_id']},deleted_by: {payload['updated_by']}")
                return 200, "Success"
        except Exception as e:
            logger.error(f"Error in feature_group_entry: {str(e)}", exc_info=True)
            return 500, str(e)

    async def get_feature_by_key(self, payload: dict) -> Optional[Feature]:
        """Fetches a feature based on the provided feature name or ID."""
        logger.info(f"Fetching feature with payload: {payload}")
        if "feature_name" in payload:
            result = await self.db.execute(
                select(Feature.feature_id, Feature.feature_name)
                .where(Feature.feature_name == payload["feature_name"])
                .order_by(Feature.id.asc())
            )
            data = [
                {"feature_id": row.feature_id, "feature_name": row.feature_name}
                for row in result.all()
            ]
            return data
        elif "feature_id" in payload:
            result = await self.db.execute(
                select(Feature.feature_id, Feature.feature_name)
                .where(Feature.feature_id == payload["feature_id"])
                .order_by(Feature.id.asc())
            )
            return [
                {"feature_id": row.feature_id, "feature_name": row.feature_name}
                for row in result.all()
            ]

    async def get_all_feature(self):
        """Retrieves all features ordered by their ID."""
        logger.info("Fetching all features")
        result = await self.db.execute(
            select(Feature.feature_id, Feature.feature_name).order_by(Feature.id.asc())
        )
        return [
            {"feature_id": row.feature_id, "feature_name": row.feature_name}
            for row in result.all()
        ]

    async def feature_entry(self, payload: dict) -> tuple:
        """Creates or updates a feature record, including its group association."""
        try:
            logger.info(f"Processing feature_entry with payload: {payload}")
            if payload["action"] == "create":
                feature = Feature(
                    feature_name=payload["feature_name"],
                    feature_id=payload["feature_id"],
                    feature_grp_id=payload["feature_grp_id"],
                    updated_by=payload["updated_by"],
                )
                self.db.add(feature)
                await self.db.commit()
                await self.db.refresh(feature)
                logger.info(f"Feature created successfully: feature_id:{payload['feature_id']},feature_name:{payload['feature_name']},feature_grp_id:{payload['feature_grp_id']},created_by: {payload['updated_by']}")
                return 200, "Success"
            elif payload["action"] == "edit":
                feature = await self.db.scalar(
                    select(Feature).where(Feature.feature_id == payload["feature_id"])
                )
                if not feature:
                    logger.info(f"Feature not found: feature_id:{payload['feature_id']},attempted_by: {payload['updated_by']}")
                    return 404, "Feature not found"

                result = await self.db.execute(
                    select(
                        FeatureGroup.feature_grp_id, FeatureGroup.feature_grp_name
                    ).where(
                        FeatureGroup.feature_grp_name == payload["feature_grp_name"],
                        FeatureGroup.feature_grp_id != payload["feature_grp_id"],
                        FeatureGroup.is_active == 1,
                    )
                )
                check_feature_group = [
                    {
                        "feature_grp_id": row.feature_grp_id,
                        "feature_grp_name": row.feature_grp_name,
                    }
                    for row in result.all()
                ]
                if len(check_feature_group) > 0:
                    logger.info(f"Feature group name already exists: feature_grp_id:{payload['feature_grp_id']},feature_grp_name:{payload['feature_grp_name']},attempted_by: {payload['updated_by']}")
                    return 400, "Feature group name already exists."

                feature_group.feature_grp_name = payload["feature_grp_name"]
                feature_group.updated_by = payload["updated_by"]

                await self.db.commit()
                logger.info(f"Feature updated successfully: feature_id:{payload['feature_id']},feature_grp_id:{payload['feature_grp_id']},updated_by: {payload['updated_by']}")
                return 200, "Success"
        except Exception as e:
            logger.error(f"Error in feature_entry: {str(e)}", exc_info=True)
            return 500, str(e)

    # Role Feature Mapping
    async def get_role_feature_mapping(self, role_id: str) -> Optional[RoleFeature]:
        """Retrieves feature permissions associated with a specific role ID."""
        logger.info(f"Fetching role feature mapping for role_id: {role_id}")
        result = await self.db.execute(
            select(RoleFeature.feature_id, RoleFeature.permission_level)
            .where(RoleFeature.role_id == role_id)
            .order_by(RoleFeature.id.asc())
        )
        role_feature = []
        for row in result.all():
            feature_name, feature_grp_id, feature_grp_name = "", "", ""

            feature_data = await self.db.execute(
                select(Feature.feature_name, Feature.feature_grp_id).where(
                    Feature.feature_id == row.feature_id
                )
            )
            feature_data = feature_data.all()
            if feature_data:
                feature_name = feature_data[0].feature_name
                feature_grp_id = feature_data[0].feature_grp_id
                feature_grp_name = await self.db.scalar(
                    select(FeatureGroup.feature_grp_name).where(
                        FeatureGroup.feature_grp_id == feature_grp_id
                    )
                )

            role_feature.append(
                {
                    "feature_id": row.feature_id,
                    "feature_name": feature_name,
                    "access": row.permission_level,
                    "feature_grp_id": feature_grp_id,
                    "feature_grp_name": feature_grp_name,
                }
            )
        return role_feature

    async def feature_role_mapping(
        self, role_id: str, feature_id: str
    ) -> Optional[RoleFeature]:
        """Checks if a specific feature is mapped to a given role."""
        logger.info(f"Checking feature role mapping for role_id: {role_id}, feature_id: {feature_id}")
        result = await self.db.execute(
            select(RoleFeature.role_id, RoleFeature.feature_id).where(
                RoleFeature.role_id == role_id, RoleFeature.feature_id == feature_id
            )
        )
        role_feature = result.all()
        return role_feature

    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """Fetches role details using the role ID."""
        logger.info(f"Fetching role by ID: {role_id}")
        result = await self.db.execute(
            select(Role.role_id, Role.role_name).where(Role.role_id == role_id)
        )
        role = result.all()
        return role

    async def create_feature_role_mapping(self, payload) -> tuple:
        """Assigns or updates permission levels for a feature mapped to a role."""
        try:
            logger.info(f"Processing create_feature_role_mapping with payload: {payload}")
            
            if payload["action"] == "edit":
                role_feature = await self.db.scalar(
                    select(RoleFeature).where(
                        RoleFeature.role_id == payload["role_id"],
                        RoleFeature.feature_id == payload["feature_id"],
                    )
                )
                if not role_feature:
                    logger.info(f"Role feature not found: role_id: {payload['role_id']}, feature_id: {payload['feature_id']},attempted_by: {payload['updated_by']}")
                    return 404, "Role feature not found"
                role_feature.permission_level = payload["permission_level"]
                role_feature.updated_by = payload["updated_by"]
                await self.db.commit()
                logger.info(f"Feature role mapping updated successfully: role_id: {payload['role_id']}, feature_id: {payload['feature_id']},updated_by: {payload['updated_by']}")
                return 200, "Success"
            elif payload["action"] == "delete":
                role_feature = await self.db.scalar(
                    select(RoleFeature).where(
                        RoleFeature.role_id == payload["role_id"],
                        RoleFeature.feature_id == payload["feature_id"],
                    )
                )
                if not role_feature:
                    logger.info(f"Role feature not found: role_id: {payload['role_id']}, feature_id: {payload['feature_id']},attempted_by: {payload['updated_by']}")
                    return 404, "Role feature not found"
                await self.db.delete(role_feature)
                await self.db.commit()
                logger.info(f"Feature role mapping deleted successfully: role_id: {payload['role_id']}, feature_id: {payload['feature_id']},deleted_by: {payload['updated_by']}")
                return 200, "Success"
        except Exception as e:
            logger.error(f"Error in create_feature_role_mapping: {str(e)}", exc_info=True)
            return 500, str(e)

    async def bulk_assign_features(self, payload: dict) -> tuple:
        """Assigns or updates permission levels for multiple features mapped to roles."""
        try:
            logger.info(f"Processing bulk_assign_features with payload: {payload}")
            features = payload["features"]
            updated_by = payload["updated_by"]

            for item in features:
                role_id = item.role_id
                feature_id = item.feature_id
                permission_level = item.permission_level
                if str(permission_level) not in ["1", "2", "3", "4"]:
                    logger.warning(f"Invalid permission level: {permission_level} for feature: {feature_id}")
                    continue

                feature_exists = await self.db.scalar(
                    select(Feature.feature_id).where(Feature.feature_id == feature_id)
                )
                if not feature_exists:
                    logger.warning(f"Feature ID not found: feature_id:{feature_id},attempted_by: {updated_by}")
                    continue

                # Check if mapping exists
                role_feature = await self.db.scalar(
                    select(RoleFeature).where(
                        RoleFeature.role_id == role_id,
                        RoleFeature.feature_id == feature_id,
                    )
                )

                if role_feature:
                    # Update existing mapping
                    role_feature.permission_level = permission_level
                    role_feature.updated_by = updated_by
                else:
                    # Create new mapping
                    new_role_feature = RoleFeature(
                        role_id=role_id,
                        feature_id=feature_id,
                        permission_level=permission_level,
                        updated_by=updated_by,
                    )
                    self.db.add(new_role_feature)
                logger.info(f"Feature assigned successfully: role_id:{role_id},feature_id:{feature_id},permission_level:{permission_level},updated_by: {updated_by}")
            await self.db.commit()
            logger.info(f"Bulk feature assignment completed successfully by: {updated_by}")
            return 200, "Success"

        except Exception as e:
            logger.error(f"Error in bulk_assign_features: {str(e)}", exc_info=True)
            return 500, str(e)

    async def edit_user_details(self, payload: dict) -> tuple:
        """Edits user details like first name, last name, role, and organization."""
        try:
            logger.info(f"Processing edit_user_details with payload: {payload}")
            user_id = payload["user_id"]
            
            user = await self.db.scalar(select(User).where(User.user_id == user_id, User.is_active == 1))
            if not user:
                logger.info(f"User not found: user_id:{user_id},attempted_by: {payload['updated_by']}")
                return 404, "User not found"

            # Update fields
            user.first_name = payload.get("first_name", user.first_name)
            user.last_name = payload.get("last_name", user.last_name)
            user.org_id = payload.get("org_id", user.org_id)
            user.role_id = payload.get("role_id", user.role_id)
            # user.updated_by = payload["updated_by"]
            
            await self.db.commit()
            logger.info(f"User details updated successfully: user_id:{user_id},updated_by: {payload['updated_by']}")
            return 200, "Success"
        except Exception as e:
            logger.error(f"Error in edit_user_details: {str(e)}", exc_info=True)
            return 500, str(e)

    async def get_role_permission_level(self, role_id: str) -> Optional[int]:
        """Fetches the permission level of a role."""
        try:
            result = await self.db.scalar(select(Role.permission_level).where(Role.role_id == role_id))
            return result
        except Exception as e:
            logger.error(f"Error fetching permission level for role {role_id}: {str(e)}")
            return None

    async def check_org_exists(self, org_id: str) -> bool:
        """Checks if an organization exists."""
        try:
            result = await self.db.scalar(select(Organization.id).where(Organization.org_id == org_id))
            return result is not None
        except Exception as e:
            logger.error(f"Error checking org check_org_exists {org_id}: {str(e)}")
            return False

    async def check_role_exists(self, role_id: str) -> bool:
        """Checks if a role exists."""
        try:
            result = await self.db.scalar(select(Role.id).where(Role.role_id == role_id))
            return result is not None
        except Exception as e:
            logger.error(f"Error checking role check_role_exists {role_id}: {str(e)}")
            return False

    async def check_feature_permission(self, payload: dict) -> bool:
        """
        Checks if a role has the required permission level for a specific feature.
        Payload: {
            "role_id": str,
            "feature_name": str,
            "required_level": int
        }
        """
        try:
            role_id = payload.get("role_id")
            feature_name = payload.get("feature_name")
            required_level = payload.get("required_level")

            # 1. Get Feature ID
            feature_id = await self.db.scalar(
                select(Feature.feature_id).where(Feature.feature_name == feature_name)
            )
            if not feature_id:
                logger.warning(f"Feature not found: {feature_name}")
                return False

            # 2. Get Permission Level for Role + Feature
            current_level = await self.db.scalar(
                select(RoleFeature.permission_level).where(
                    RoleFeature.role_id == role_id,
                    RoleFeature.feature_id == feature_id
                )
            )

            if current_level is None:
                logger.info(f"No permission mapping found for role {role_id} on feature {feature_name}")
                return False
            
            # 3. Check Level (1=None, 2=Read, 3=Write, 4=Delete)
            # Logic: Has permission if current_level >= required_level
            # AND current_level > 1 (Since 1 is NONE, usually implies no access, but strict check is >= required)
            # If required is 1 (None), then 1 is enough? 
            # Enum: NONE=1, READ=2...
            # If I require READ (2), current must be >= 2.
            # If current is 1 (None), 1 >= 2 is False. Correct.
            
            has_permission = current_level >= required_level
            logger.info(f"Permission Check: Role={role_id}, Feat={feature_name}, Cur={current_level}, Req={required_level} -> {has_permission}")
            return has_permission

        except Exception as e:
            logger.error(f"Error checking feature permission: {str(e)}", exc_info=True)
            return False
