import datetime

import pytest
from fastapi import HTTPException, WebSocketException
from pytest_mock import MockerFixture
from sqlmodel import delete

from api.models.database_models import DBUser
from api.utils.http_exceptions import INVALID_CREDENTIALS
from api.utils.security import create_access_token, get_current_user, get_current_user_ws
from tests.utils.fake_db import async_fake_session_maker, initialize_fake_database


@pytest.mark.parametrize("token_data", [{}, {"sub": "fake_username"}])
@pytest.mark.asyncio
async def test_get_current_user_invalid_token(token_data: dict):
    await initialize_fake_database()
    async with async_fake_session_maker() as session:
        await session.execute(delete(DBUser))
        await session.commit()

        access_token = create_access_token(data=token_data, expires_delta=datetime.timedelta(minutes=1))

        with pytest.raises(HTTPException) as exception:
            await get_current_user(access_token, session)

        assert exception.value == INVALID_CREDENTIALS


@pytest.mark.parametrize("token_data", [{}, {"sub": "fake_username"}])
@pytest.mark.asyncio
async def test_get_current_user_ws_invalid_token(token_data: dict, mocker: MockerFixture):
    await initialize_fake_database()
    async with async_fake_session_maker() as session:
        await session.execute(delete(DBUser))
        await session.commit()

        access_token = create_access_token(data=token_data, expires_delta=datetime.timedelta(minutes=1))

        jwt_decode_mock = mocker.patch("api.utils.security.jwt.decode")
        jwt_decode_mock.return_value = token_data

        with pytest.raises(WebSocketException) as exception:
            await get_current_user_ws(session, f"Bearer {access_token}")

        # assert jwt_decode_mock.assert_called_once()
        assert exception.value.code == 1008
