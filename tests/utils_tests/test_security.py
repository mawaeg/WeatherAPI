import datetime

import pytest
from fastapi import HTTPException
from sqlmodel import delete

from api.models.database_models import DBUser
from api.utils.security import create_access_token, get_current_user
from tests.utils.fake_db import async_fake_session_maker, initialize_fake_database


@pytest.mark.parametrize("token_data", [{}, {"sub": "fake_username"}])
@pytest.mark.asyncio
async def test_get_current_user_invalid_token(token_data: str):
    await initialize_fake_database()
    async with async_fake_session_maker() as session:
        await session.execute(delete(DBUser))
        await session.commit()

        access_token = create_access_token(data=token_data, expires_delta=datetime.timedelta(minutes=1))

        with pytest.raises(HTTPException) as exception:
            await get_current_user(access_token, session)

        assert exception.value.status_code == 401
        assert exception.value.detail == "Could not validate credentials"
