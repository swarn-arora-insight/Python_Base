# app/models/uam.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, DateTime, func
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

class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # Display Name
    key = Column(String(100), unique=True, index=True, nullable=False) # strict key e.g. 'user_create'
    description = Column(String(255), nullable=True)

    # roles = relationship("Role", secondary=role_feature_association, back_populates="features")

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
