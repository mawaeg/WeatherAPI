import pytest_asyncio
from sqlmodel import select

from api.models.database_models import DBUser
from api.utils.security import create_access_token, get_password_hash
from tests.utils.fake_db import async_fake_session_maker, initialize_fake_database


@pytest_asyncio.fixture
async def token() -> str:
    """
    Creates a fake user in the testing database and creates a token for that user.

    Returns:
        Returns the token fo the created user
    """
    await initialize_fake_database()
    test_username: str = "test_user"
    async with async_fake_session_maker() as session:
        # Only create the user if not already existing.
        result = await session.execute(select(DBUser).where(DBUser.username == test_username))
        user = result.scalars().first()
        if not user:
            hashed_password: str = get_password_hash("test_password")
            session.add(DBUser(username=test_username, hashed_password=hashed_password))
            await session.commit()

    token = create_access_token(data={"sub": test_username})
    return token


@pytest_asyncio.fixture
async def superuser_token() -> str:
    """
    Creates a fake superuser in the testing database and creates a token for that user.

    Returns:
        Returns the token fo the created superuser
    """
    await initialize_fake_database()
    test_username: str = "test_superuser"
    async with async_fake_session_maker() as session:
        # Only create the user if not already existing.
        result = await session.execute(select(DBUser).where(DBUser.username == test_username))
        user = result.scalars().first()
        if not user:
            hashed_password: str = get_password_hash("test_password")
            session.add(DBUser(username=test_username, hashed_password=hashed_password, superuser=True))
            await session.commit()

    superuser_token = create_access_token(data={"sub": test_username})
    return superuser_token
