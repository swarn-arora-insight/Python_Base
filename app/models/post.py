# app/models/post.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), index=True)
    content = Column(String(500))

    # Foreign key to link to User
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")

    # Relationships
    comments = relationship("Comment", back_populates="post")
