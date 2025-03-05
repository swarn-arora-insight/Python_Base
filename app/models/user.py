# app/models/user.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, BigInteger, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from models.base import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime


class User(Base):
    __tablename__ = "users"
    
    # id = Column(Integer,primary_key= True , index= True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    address = Column(String(255), nullable=False)
    token = Column(String(255), nullable=True)  # Optional field
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1) # 1 = Active, 0 = Inactive
    last_logged_in = Column(DateTime, nullable=True)  # Optional field
    created_on = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)  # Auto-set timestamp
    auth_key=Column(String(255), nullable=True)
    is_auth = Column(Integer, default=0)

    
    posts = relationship("Post", back_populates="author")

