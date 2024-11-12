# app/services/post_service.py
from app.repositories.post_repo import PostRepository
from app.schemas.post import PostCreate, PostUpdate, PostOut
from app.models.post import Post

class PostService:
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo

    async def create_post(self, post_data: PostCreate, author_id: int) -> PostOut:
        post = Post(title=post_data.title, content=post_data.content, author_id=author_id)
        new_post = await self.post_repo.create_post(post)
        return PostOut.from_orm(new_post)

    async def get_post(self, post_id: int) -> PostOut | None:
        post = await self.post_repo.get_post_by_id(post_id)
        return PostOut.from_orm(post) if post else None

    async def update_post(self, post_id: int, post_data: PostUpdate) -> PostOut | None:
        post = await self.post_repo.get_post_by_id(post_id)
        if post:
            updated_post = await self.post_repo.update_post(post, post_data.dict(exclude_unset=True))
            return PostOut.from_orm(updated_post)
        return None

    async def delete_post(self, post_id: int) -> bool:
        post = await self.post_repo.get_post_by_id(post_id)
        if post:
            await self.post_repo.delete_post(post)
            return True
        return False
