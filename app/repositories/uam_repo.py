# app/repositories/uam_repo.py
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.uam import Organization, Role, Feature
from models.user import User
from typing import List, Optional

class UAMRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Organization
    async def get_all_orgs(self) -> list:
        result = await self.db.execute(select(Organization.org_id, Organization.org_name).where(Organization.is_active == 1).order_by(Organization.id.asc()))
        return [{"org_id": row.org_id, "org_name": row.org_name} for row in result.all()]

    async def get_org_by_key(self, payload: dict) -> Optional[Organization]:
        if "org_name" in payload:
            result = await self.db.execute(select(Organization.org_id, Organization.org_name).where(Organization.org_name == payload["org_name"], Organization.is_active == 1).order_by(Organization.id.asc()))
            return [{"org_id": row.org_id, "org_name": row.org_name} for row in result.all()]
        elif "org_id" in payload:
            result = await self.db.execute(select(Organization.org_id, Organization.org_name).where(Organization.org_id == payload["org_id"], Organization.is_active == 1).order_by(Organization.id.asc()))
            return [{"org_id": row.org_id, "org_name": row.org_name} for row in result.all()]

    async def org_entry(self, payload: dict) -> tuple:
        try:
            if payload["action"] == "create":
                org = Organization(org_name=payload["org_name"], org_id=payload["org_id"], updated_by=payload["updated_by"])
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
                
                result = await self.db.execute(select(Organization.org_id, Organization.org_name).where(Organization.org_name == payload["org_name"], Organization.org_id != payload["org_id"] ,Organization.is_active == 1))
                check_org = [{"org_id": row.org_id, "org_name": row.org_name} for row in result.all()]
                if len(check_org) > 0:
                    return 400, "Organization name already exists."

                org.org_name = payload["org_name"]
                org.updated_by = payload["updated_by"]

                await self.db.commit()
                return 200, "Success"
        except Exception as e:
            return 500, str(e)

    async def org_delete(self, payload: dict) -> tuple:
        try:
            org = await self.db.scalar(
                select(Organization).where(Organization.org_id == payload["org_id"])
            )
            
            if not org:
                return 404, "Organization not found"
            
            org_users = await self.db.execute(
                select(User).where(User.org_id == payload["org_id"], User.is_active == 1)
            )
            if org_users.scalars().first():
                return 400, "Deletion failed: users are currently assigned to this organization."
            
            org.is_active = 0
            org.updated_by = payload["updated_by"]
            await self.db.commit()
            return 200, "Success"
        except Exception as e:
            return 500, str(e)

    # Role
    async def get_all_roles(self) -> list:
        result = await self.db.execute(
            select(Role.role_id, Role.role_name)
            .where(Role.is_active == 1)
            .order_by(Role.id.asc())
        )

        role_details = []

        for row in result.all():
            users_result = await self.db.execute(
                select(User.first_name, User.last_name)
                .where(User.role_id == row.role_id, User.is_active == 1)
            )

            users = users_result.all()  # list of Row objects

            role_details.append({
                "role_id": row.role_id,
                "role_name": row.role_name,
                "user_count": len(users),
                "user_names": [f"{u.first_name} {u.last_name}" for u in users]
            })

        return role_details
    
    async def get_role_by_key(self, payload: dict) -> Optional[Role]:
        if "role_name" in payload:
            result = await self.db.execute(select(Role.role_id, Role.role_name).where(Role.role_name == payload["role_name"], Role.is_active == 1).order_by(Role.id.asc()))
            return [{"role_id": row.role_id, "role_name": row.role_name} for row in result.all()]
        elif "role_id" in payload:
            result = await self.db.execute(select(Role.role_id, Role.role_name).where(Role.role_id == payload["role_id"], Role.is_active == 1).order_by(Role.id.asc()))
            return [{"role_id": row.role_id, "role_name": row.role_name} for row in result.all()]

    async def role_entry(self, payload: dict) -> tuple:
        try:
            if payload["action"] == "create":
                role = Role(role_name=payload["role_name"], role_id=payload["role_id"], updated_by=payload["updated_by"])
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
                
                result = await self.db.execute(select(Role.role_id, Role.role_name).where(Role.role_name == payload["role_name"], Role.role_id != payload["role_id"] ,Role.is_active == 1))
                check_role = [{"role_id": row.role_id, "role_name": row.role_name} for row in result.all()]
                if len(check_role) > 0:
                    return 400, "Role name already exists."
                
                role.role_name = payload["role_name"]
                role.updated_by = payload["updated_by"]

                await self.db.commit()
                return 200, "Success"
        except Exception as e:
            return 500, str(e)
    
    # async def create_org(self, name: str, code: str) -> Organization:
    #     org = Organization(name=name, code=code)
    #     self.db.add(org)
    #     await self.db.commit()
    #     await self.db.refresh(org)
    #     return org


    # async def get_all_roles(self) -> List[Role]:
    #     result = await self.db.execute(select(Role))
    #     return result.scalars().unique().all()
    
    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        result = await self.db.execute(
            select(Role).options(joinedload(Role.features)).where(Role.id == role_id)
        )
        return result.scalars().first()

    # Feature
    async def create_feature(self, name: str, key: str, description: str = None) -> Feature:
        feature = Feature(name=name, key=key, description=description)
        self.db.add(feature)
        await self.db.commit()
        await self.db.refresh(feature)
        return feature

    async def get_all_features(self) -> List[Feature]:
        result = await self.db.execute(select(Feature))
        return result.scalars().all()

    async def assign_features_to_role(self, role_id: int, feature_ids: List[int]) -> Role:
        role = await self.get_role_by_id(role_id)
        if not role:
            return None
        
        # Clear existing features (simple strategy) or Add new ones. 
        # Here we fetch features and replace.
        result = await self.db.execute(select(Feature).where(Feature.id.in_(feature_ids)))
        features = result.scalars().all()
        
        role.features = features
        await self.db.commit()
        await self.db.refresh(role)
        return role
