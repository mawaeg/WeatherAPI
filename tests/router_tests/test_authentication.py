import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import delete

from api.main import app
from api.models.database_models import DBUser
from api.utils.database import get_engine
from api.utils.security import get_current_user, get_password_hash
from tests.utils.fake_db import async_fake_session_maker, initialize_fake_database, override_get_engine

app.dependency_overrides[get_engine] = override_get_engine
client: TestClient = TestClient(app)


async def create_db_user() -> tuple[str, str, str]:
    username = "test_token_user"
    password = "test_password"
    hashed_password = get_password_hash(password)
    await initialize_fake_database()
    async with async_fake_session_maker() as session:
        await session.execute(delete(DBUser))
        await session.commit()

        user: DBUser = DBUser(username=username, hashed_password=hashed_password)
        session.add(user)
        await session.commit()

    return username, password, hashed_password


def test_fetch_access_token_no_user():
    response: httpx.Response = client.post("/token")
    assert response.status_code == 422


@pytest.mark.parametrize("add_to_username,add_to_password", [("invalid", ""), ("", "invalid")])
@pytest.mark.asyncio
async def test_fetch_access_token_wrong_credentials(add_to_username: str, add_to_password: str):
    username, password, _ = await create_db_user()

    response: httpx.Response = client.post(
        "/token", data={"username": username + add_to_username, "password": password + add_to_password}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_fetch_access_token():
    username, password, hashed_password = await create_db_user()

    response: httpx.Response = client.post("/token", data={"username": username, "password": password})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    async with async_fake_session_maker() as session:
        user: DBUser = await get_current_user(response.json()["access_token"], session)
    assert user.username == username
    assert user.hashed_password == hashed_password
