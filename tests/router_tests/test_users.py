import httpx
import pytest
from sqlmodel import delete, select

from api.models.database_models import DBUser
from api.utils.http_exceptions import MISSING_PRIVILEGES, USER_ALREADY_EXISTS
from api.utils.security import get_current_user
from tests.utils.assertions import assert_HTTPException_EQ
from tests.utils.authentication_tests import _TestGetAuthentication, _TestPostAuthentication
from tests.utils.fake_db import async_fake_session_maker
from tests.utils.fixtures import superuser_token, token


class TestGetUsers(_TestGetAuthentication):

    @property
    def _get_path(self) -> str:
        return "/users"

    @pytest.mark.asyncio
    async def test_get_users_normal_user(self, token: str):
        """
        Asserts the api is returning an error when the route is called with a non superuser.
        """
        response: httpx.Response = self.client.get(self._get_path, headers={"Authorization": f"Bearer {token}"})
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)

    @pytest.mark.asyncio
    async def test_get_users(self, superuser_token: str):
        """
        Assert that get users returns all users from the database.

        Currently, this only check for the len as list comparisons are way more complex
        Probably they are too much overkill for such a simple route?
        As still this test mostly just copies the route implementation itself
        """
        # ToDo Does this make sense here, as it is just the code copied from the actual route.
        async with async_fake_session_maker() as session:
            result = await session.execute(select(DBUser))
            users = result.scalars().all()

        response: httpx.Response = self.client.get(
            self._get_path, headers={"Authorization": f"Bearer {superuser_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == len(users)


class TestGetUsersMe(_TestGetAuthentication):

    @property
    def _get_path(self) -> str:
        return "/users/me"

    @pytest.mark.asyncio
    async def test_get_users_me(self, token: str):
        """
        Assert the /users/me endpoint returns the correct user.
        """
        async with async_fake_session_maker() as session:
            current_user: DBUser = await get_current_user(token, session)

        response: httpx.Response = self.client.get(self._get_path, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["username"] == current_user.username
        assert response.json()["superuser"] == current_user.superuser


class TestCreateUser(_TestPostAuthentication):

    @property
    def _get_path(self):
        return "/users"

    @property
    def test_user(self) -> dict[str, str]:
        """
        Returns the test user that is used for the tests.
        """
        return {"username": "test_create_user", "password": "test_password", "superuser": False}

    async def clear_test_user(self) -> None:
        async with async_fake_session_maker() as session:
            await session.execute(delete(DBUser).where(DBUser.username == self.test_user["username"]))
            await session.commit()

    @pytest.mark.asyncio
    async def test_create_user_normal_user(self, token: str):
        """
        Asserts the api is returning an error when the route is called with a non superuser.
        """
        response: httpx.Response = self.client.post(
            self._get_path, headers={"Authorization": f"Bearer {token}"}, json=self.test_user
        )
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)

    @pytest.mark.asyncio
    async def test_create_user(self, superuser_token: str):
        """
        Assert a new user gets created correctly.
        """
        await self.clear_test_user()
        response: httpx.Response = self.client.post(
            self._get_path, headers={"Authorization": f"Bearer {superuser_token}"}, json=self.test_user
        )

        assert response.status_code == 201
        assert response.json()["username"] == self.test_user["username"]
        assert response.json()["superuser"] == self.test_user["superuser"]

        async with async_fake_session_maker() as session:
            result = await session.execute(select(DBUser).where(DBUser.username == self.test_user["username"]))
            user: DBUser | None = result.scalars().first()
        assert user

    @pytest.mark.asyncio
    async def test_create_user_multiple_times(self, superuser_token: str):
        """
        Assert that trying to create a user multiple times results in the expected error.
        """
        await self.clear_test_user()

        response: httpx.Response = self.client.post(
            self._get_path, headers={"Authorization": f"Bearer {superuser_token}"}, json=self.test_user
        )
        assert response.status_code == 201

        response: httpx.Response = self.client.post(
            self._get_path, headers={"Authorization": f"Bearer {superuser_token}"}, json=self.test_user
        )
        assert_HTTPException_EQ(response, USER_ALREADY_EXISTS)
