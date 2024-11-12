# app/tests/test_post.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_post():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/v1/posts/", json={"title": "Sample Post", "content": "This is a test post", "author_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Sample Post"
    assert "id" in data
