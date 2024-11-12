# app/tests/test_comment.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_comment():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/v1/comments/", json={"content": "This is a test comment", "post_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "This is a test comment"
    assert "id" in data
