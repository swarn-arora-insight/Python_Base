# app/utils/uam_seeder.py
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.uam import Role, Feature, Organization
from core.logging import logger

DEFAULT_FEATURES = [
    {"name": "View Dashboard", "key": "view_dashboard", "description": "Can view the main dashboard"},
    {"name": "Manage Users", "key": "manage_users", "description": "Can create/edit/delete users"},
    {"name": "Manage Roles", "key": "manage_roles", "description": "Can create/edit roles"},
    {"name": "View Reports", "key": "view_reports", "description": "Can view analytics reports"},
]

DEFAULT_ROLES = ["Admin", "User", "Manager"]
DEFAULT_ORG = {"name": "Default Org", "code": "DEFAULT"}

async def seed_uam(db: AsyncSession):
    try:
        # Seed Org
        res_org = await db.execute(select(Organization).where(Organization.code == DEFAULT_ORG["code"]))
        if not res_org.scalars().first():
            db.add(Organization(**DEFAULT_ORG))
            logger.info("Seeding Default Organization")

        # Seed Features
        feature_map = {}
        for feat in DEFAULT_FEATURES:
            res = await db.execute(select(Feature).where(Feature.key == feat["key"]))
            existing = res.scalars().first()
            if not existing:
                new_feat = Feature(**feat)
                db.add(new_feat)
                await db.flush() # flush to get ID
                feature_map[feat["key"]] = new_feat
                logger.info(f"Seeding Feature: {feat['key']}")
            else:
                feature_map[feat["key"]] = existing

        # Seed Roles with feature assignment
        for role_name in DEFAULT_ROLES:
            res = await db.execute(select(Role).where(Role.name == role_name))
            role = res.scalars().first()
            if not role:
                role = Role(name=role_name, description=f"{role_name} Role")
                db.add(role)
                await db.flush()
                logger.info(f"Seeding Role: {role_name}")
            
            # Auto-Assign features for Admin
            if role_name == "Admin":
                role.features = list(feature_map.values()) # All features
            elif role_name == "User":
                # Give specific features
                user_feats = [feature_map.get("view_dashboard")]
                role.features = [f for f in user_feats if f]

        await db.commit()
    except Exception as e:
        logger.error(f"Error seeding UAM data: {e}")
        await db.rollback()
