# app/services/comment_service.py
from repositories.comment_repo import CommentRepository
from schemas.comment import CommentCreate, CommentUpdate, CommentOut
from models.comment import Comment
from typing import Optional

class CommentService:
    def __init__(self, comment_repo: CommentRepository):
        self.comment_repo = comment_repo

    async def create_comment(self, comment_data: CommentCreate, post_id: int) -> CommentOut:
        comment = Comment(content=comment_data.content, post_id=post_id)
        new_comment = await self.comment_repo.create_comment(comment)
        return CommentOut.from_orm(new_comment)

    async def get_comment(self, comment_id: int) -> Optional[CommentOut]:  # CommentOut | None:
        comment = await self.comment_repo.get_comment_by_id(comment_id)
        return CommentOut.from_orm(comment) if comment else None

    async def update_comment(self, comment_id: int, comment_data: CommentUpdate) -> Optional[CommentOut]:
        comment = await self.comment_repo.get_comment_by_id(comment_id)
        if comment:
            updated_comment = await self.comment_repo.update_comment(comment, comment_data.dict(exclude_unset=True))
            return CommentOut.from_orm(updated_comment)
        return None

    async def delete_comment(self, comment_id: int) -> bool:
        comment = await self.comment_repo.get_comment_by_id(comment_id)
        if comment:
            await self.comment_repo.delete_comment(comment)
            return True
        return False
