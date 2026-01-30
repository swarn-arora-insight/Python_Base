# app/repositories/uam_repo.py
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.uam import Organization, Role, Feature, FeatureGroup, RoleFeature
from models.user import User
from typing import List, Optional


class UAMRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Organization
    async def get_all_orgs(self) -> list:
        """Retrieves a list of all active organizations with their IDs and names."""
        result = await self.db.execute(
            select(Organization.org_id, Organization.org_name)
            .where(Organization.is_active == 1)
            .order_by(Organization.id.asc())
        )
        return [
            {"org_id": row.org_id, "org_name": row.org_name} for row in result.all()
        ]

    async def get_org_by_key(self, payload: dict) -> Optional[Organization]:
        """Fetches an organization based on the provided organization name or ID."""
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
            if payload["action"] == "create":
                org = Organization(
                    org_name=payload["org_name"],
                    org_id=payload["org_id"],
                    updated_by=payload["updated_by"],
                )
                self.db.add(org)
                await self.db.commit()
                await self.db.refresh(org)
                return 200, "Success"
            elif payload["action"] == "edit":
                org = await self.db.scalar(
                    select(Organization).where(Organization.org_id == payload["org_id"])
                )
                if not org:
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
                    return 400, "Organization name already exists."

                org.org_name = payload["org_name"]
                org.updated_by = payload["updated_by"]

                await self.db.commit()
                return 200, "Success"
        except Exception as e:
            return 500, str(e)

    async def org_delete(self, payload: dict) -> tuple:
        """Soft deletes an organization if no users are currently assigned to it."""
        try:
            org = await self.db.scalar(
                select(Organization).where(Organization.org_id == payload["org_id"])
            )

            if not org:
                return 404, "Organization not found"

            org_users = await self.db.execute(
                select(User).where(
                    User.org_id == payload["org_id"], User.is_active == 1
                )
            )
            if org_users.scalars().first():
                return (
                    400,
                    "Deletion failed: users are currently assigned to this organization.",
                )

            org.is_active = 0
            org.updated_by = payload["updated_by"]
            await self.db.commit()
            return 200, "Success"
        except Exception as e:
            return 500, str(e)

    # Role
    async def get_all_roles(self) -> list:
        """Retrieves all active roles along with the count and names of assigned users."""
        result = await self.db.execute(
            select(Role.role_id, Role.role_name)
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
                    "user_count": len(users),
                    "user_names": [f"{u.first_name} {u.last_name}" for u in users],
                }
            )

        return role_details

    async def get_role_by_key(self, payload: dict) -> Optional[Role]:
        """Fetches a role based on the provided role name or ID."""
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
            if payload["action"] == "create":
                role = Role(
                    role_name=payload["role_name"],
                    role_id=payload["role_id"],
                    updated_by=payload["updated_by"],
                )
                self.db.add(role)
                await self.db.commit()
                await self.db.refresh(role)
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
                role.updated_by = payload["updated_by"]

                await self.db.commit()
                return 200, "Success"
        except Exception as e:
            return 500, str(e)

    # Feature
    async def feature_list(self):
        """Retrieves all features ordered by their ID."""
        result = await self.db.execute(
            select(FeatureGroup.feature_grp_id, FeatureGroup.feature_grp_name).order_by(FeatureGroup.id.asc())
        )
        feature_grp_list = []
        for row in result.all():
            get_feature = await self.db.execute(
                select(Feature.feature_id, Feature.feature_name).where(Feature.feature_grp_id == row.feature_grp_id)
            )
            feature_grp_list.append({"feature_grp_id": row.feature_grp_id, "feature_grp_name": row.feature_grp_name, "feature_list": [{"feature_id": f.feature_id, "feature_name": f.feature_name} for f in get_feature.all()]})
        return feature_grp_list

    async def get_feature_group_by_key(self, payload: dict) -> Optional[FeatureGroup]:
        """Fetches a feature group based on the provided name or ID."""
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
            if payload["action"] == "create":
                feature_group = FeatureGroup(
                    feature_grp_name=payload["feature_grp_name"],
                    feature_grp_id=payload["feature_grp_id"],
                    updated_by=payload["updated_by"],
                )
                self.db.add(feature_group)
                await self.db.commit()
                await self.db.refresh(feature_group)
                return 200, "Success"
            elif payload["action"] == "edit":
                feature_group = await self.db.scalar(
                    select(FeatureGroup).where(
                        FeatureGroup.feature_grp_id == payload["feature_grp_id"]
                    )
                )
                if not feature_group:
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
                    return 400, "Feature group name already exists."

                feature_group.feature_grp_name = payload["feature_grp_name"]
                feature_group.updated_by = payload["updated_by"]

                await self.db.commit()
                return 200, "Success"
            elif payload["action"] == "delete":
                feature = await self.db.scalar(
                    select(Feature).where(
                        Feature.feature_id == payload["feature_id"],
                    )
                )
                if not feature:
                    return 404, "Feature not found"
                await self.db.delete(feature)
                await self.db.commit()
                return 200, "Success"
        except Exception as e:
            return 500, str(e)

    async def get_feature_by_key(self, payload: dict) -> Optional[Feature]:
        """Fetches a feature based on the provided feature name or ID."""
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
                return 200, "Success"
            elif payload["action"] == "edit":
                feature = await self.db.scalar(
                    select(Feature).where(Feature.feature_id == payload["feature_id"])
                )
                if not feature:
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
                    return 400, "Feature group name already exists."

                feature_group.feature_grp_name = payload["feature_grp_name"]
                feature_group.updated_by = payload["updated_by"]

                await self.db.commit()
                return 200, "Success"
        except Exception as e:
            return 500, str(e)

    # Role Feature Mapping
    async def get_role_feature_mapping(self, role_id: str) -> Optional[RoleFeature]:
        """Retrieves feature permissions associated with a specific role ID."""
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
        result = await self.db.execute(
            select(RoleFeature.role_id, RoleFeature.feature_id).where(
                RoleFeature.role_id == role_id, RoleFeature.feature_id == feature_id
            )
        )
        role_feature = result.all()
        return role_feature

    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """Fetches role details using the role ID."""
        result = await self.db.execute(
            select(Role.role_id, Role.role_name).where(Role.role_id == role_id)
        )
        role = result.all()
        return role

    async def create_feature_role_mapping(self, payload) -> tuple:
        """Assigns or updates permission levels for a feature mapped to a role."""
        try:
            if payload["action"] == "create":
                role_feature = RoleFeature(
                    role_id=payload["role_id"],
                    feature_id=payload["feature_id"],
                    permission_level=payload["permission_level"],
                    updated_by=payload["updated_by"],
                )
                self.db.add(role_feature)
                await self.db.commit()
                await self.db.refresh(role_feature)
                return 200, "Success"
            elif payload["action"] == "edit":
                role_feature = await self.db.scalar(
                    select(RoleFeature).where(
                        RoleFeature.role_id == payload["role_id"],
                        RoleFeature.feature_id == payload["feature_id"],
                    )
                )
                if not role_feature:
                    return 404, "Role feature not found"
                role_feature.permission_level = payload["permission_level"]
                role_feature.updated_by = payload["updated_by"]
                await self.db.commit()
                return 200, "Success"
            elif payload["action"] == "delete":
                role_feature = await self.db.scalar(
                    select(RoleFeature).where(
                        RoleFeature.role_id == payload["role_id"],
                        RoleFeature.feature_id == payload["feature_id"],
                    )
                )
                if not role_feature:
                    return 404, "Role feature not found"
                await self.db.delete(role_feature)
                await self.db.commit()
                return 200, "Success"
        except Exception as e:
            return 500, str(e)
