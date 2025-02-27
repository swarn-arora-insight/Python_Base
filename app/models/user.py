# app/models/user.py
from sqlalchemy import Column, Integer, String,DateTime
from sqlalchemy.orm import relationship
from models.base import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime

# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(50), index=True)
#     email = Column(String(100), unique=True, index=True)

#     # Relationships
#     posts = relationship("Post", back_populates="author")




### alok in ####

class User(Base):
    __tablename__ = "users"
    
    # id = Column(Integer,primary_key= True , index= True)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    firstname = Column(String(50),nullable=False )
    lastname= Column(String(50))
    age = Column(Integer, nullable=False)
    address = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    isactive = Column(Integer, default=1, nullable=False)  # 1 = Active, 0 = Inactive
    created_on = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)  # Auto-set timestamp
    posts = relationship("Post", back_populates="author")

    


#### alok out ####