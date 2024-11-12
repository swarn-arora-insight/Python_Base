# app/api/v1/post_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.repositories.post_repo import PostRepository
from app.services.post_service import PostService
from app.schemas.post import PostCreate, PostUpdate, PostOut

router = APIRouter()

@router.post("/", response_model=PostOut)
async def create_post(post: PostCreate, author_id: int, db: AsyncSession = Depends(get_db)):
    post_service = PostService(PostRepository(db))
    return await post_service.create_post(post, author_id)

@router.get("/{post_id}", response_model=PostOut)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post_service = PostService(PostRepository(db))
    post = await post_service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.put("/{post_id}", response_model=PostOut)
async def update_post(post_id: int, post_data: PostUpdate, db: AsyncSession = Depends(get_db)):
    post_service = PostService(PostRepository(db))
    post = await post_service.update_post(post_id, post_data)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.delete("/{post_id}", response_model=dict)
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post_service = PostService(PostRepository(db))
    success = await post_service.delete_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}
