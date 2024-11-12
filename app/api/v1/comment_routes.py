# app/api/v1/comment_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.repositories.comment_repo import CommentRepository
from app.services.comment_service import CommentService
from app.schemas.comment import CommentCreate, CommentUpdate, CommentOut

router = APIRouter()

@router.post("/", response_model=CommentOut)
async def create_comment(comment: CommentCreate, post_id: int, db: AsyncSession = Depends(get_db)):
    comment_service = CommentService(CommentRepository(db))
    return await comment_service.create_comment(comment, post_id)

@router.get("/{comment_id}", response_model=CommentOut)
async def get_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    comment_service = CommentService(CommentRepository(db))
    comment = await comment_service.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment

@router.put("/{comment_id}", response_model=CommentOut)
async def update_comment(comment_id: int, comment_data: CommentUpdate, db: AsyncSession = Depends(get_db)):
    comment_service = CommentService(CommentRepository(db))
    comment = await comment_service.update_comment(comment_id, comment_data)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment

@router.delete("/{comment_id}", response_model=dict)
async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    comment_service = CommentService(CommentRepository(db))
    success = await comment_service.delete_comment(comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"message": "Comment deleted successfully"}
