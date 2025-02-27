# app/schemas/comment.py
from pydantic import BaseModel
from typing import Optional

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    # content: str | None = None
    content: Optional[str] = None

class CommentOut(CommentBase):
    id: int
    post_id: int

    class Config:
        from_attributes=True
        # orm_mode = True
