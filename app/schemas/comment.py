# app/schemas/comment.py
from pydantic import BaseModel

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    content: str | None = None

class CommentOut(CommentBase):
    id: int
    post_id: int

    class Config:
        from_attributes=True
        # orm_mode = True
