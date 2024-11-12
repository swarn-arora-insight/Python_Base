# app/tests/test_user.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_user():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/v1/users/", json={"name": "John", "email": "john@example.com", "password": "secret"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John"
    assert "id" in data
