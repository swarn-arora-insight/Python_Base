# app/repositories/post_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.post import Post

class PostRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_post_by_id(self, post_id: int) -> Post:
        result = await self.db.execute(select(Post).where(Post.id == post_id))
        return result.scalars().first()

    async def get_all_posts(self):
        result = await self.db.execute(select(Post))
        return result.scalars().all()

    async def create_post(self, post: Post) -> Post:
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def update_post(self, post: Post, updates: dict) -> Post:
        for field, value in updates.items():
            setattr(post, field, value)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def delete_post(self, post: Post):
        await self.db.delete(post)
        await self.db.commit()
