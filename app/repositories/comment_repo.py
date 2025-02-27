# app/repositories/comment_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.comment import Comment

class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_comment_by_id(self, comment_id: int) -> Comment:
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        return result.scalars().first()

    async def get_all_comments(self):
        result = await self.db.execute(select(Comment))
        return result.scalars().all()

    async def create_comment(self, comment: Comment) -> Comment:
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def update_comment(self, comment: Comment, updates: dict) -> Comment:
        for field, value in updates.items():
            setattr(comment, field, value)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def delete_comment(self, comment: Comment):
        await self.db.delete(comment)
        await self.db.commit()
