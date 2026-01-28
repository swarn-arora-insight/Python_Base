# app/repositories/uam_repo.py
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.uam import Organization, Role, Feature
from typing import List, Optional

class UAMRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Organization
    async def create_org(self, name: str, code: str) -> Organization:
        org = Organization(name=name, code=code)
        self.db.add(org)
        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def org_entry(self, payload: dict) -> tuple:
        try:
            org = Organization(org_name=payload["org_name"], org_id=payload["org_id"], updated_by=payload["updated_by"])
            self.db.add(org)
            await self.db.commit()
            await self.db.refresh(org)
            return 200, "Success"
        except Exception as e:
            return 500, str(e)

    async def get_all_orgs(self) -> list:
        result = await self.db.execute(select(Organization.org_id, Organization.org_name).where(Organization.is_active == 1).order_by(Organization.id.asc()))
        return [{"org_id": row.org_id, "org_name": row.org_name} for row in result.all()]


    # Role
    async def create_role(self, name: str, description: str = None) -> Role:
        role = Role(name=name, description=description)
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def get_all_roles(self) -> List[Role]:
        result = await self.db.execute(select(Role))
        return result.scalars().unique().all()
    
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
