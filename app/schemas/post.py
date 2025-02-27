# app/schemas/post.py
from pydantic import BaseModel
from typing import Optional

class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    # title: str | None = None
    title: Optional[str] = None
    content: Optional[str] = None
    # content: str | None = None

class PostOut(PostBase):
    id: int
    author_id: int

    class Config:
        from_attributes=True
        # orm_mode = True
