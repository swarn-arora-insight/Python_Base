# app/models/uam.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, DateTime, func
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from models.base import Base

# Association Table for Role <-> Feature
# role_feature_association = Table(
#     "role_features",
#     Base.metadata,
#     Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
#     Column("feature_id", Integer, ForeignKey("features.id"), primary_key=True),
# )

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String(150), unique=True, index=True, nullable=False)
    org_name = Column(String(150), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    updated_by = Column(String(200), nullable=True)

    users = relationship("User", back_populates="organization")

class FeatureGroup(Base):
    __tablename__ = "feature_grp"

    id = Column(Integer, primary_key=True, index=True)
    feature_grp_id = Column(String(200), unique=True, index=True, nullable=False)
    feature_grp_name = Column(String(100), unique=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    updated_by = Column(String(200), nullable=True)

class Feature(Base):
    __tablename__ = "feature"

    id = Column(Integer, primary_key=True, index=True)
    feature_id = Column(String(200), unique=True, index=True, nullable=False)
    feature_name = Column(String(100), unique=True, nullable=False)
    feature_grp_id = Column(String(200), unique=True, index=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    updated_by = Column(String(200), nullable=True)

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(String(200), unique=True, index=True, nullable=False)
    role_name = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    updated_by = Column(String(200), nullable=True)
    
    # One-to-Many with Users
    users = relationship("User", back_populates="role")


class RoleFeature(Base):
    __tablename__ = "role_feature_mapping"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(String(200), index=True, nullable=False)
    feature_id = Column(String(200), index=True, nullable=False)
    permission_level = Column(TINYINT(4), nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    updated_by = Column(String(200), nullable=True)
