from enum import Enum

import httpx
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.utils.database import get_engine
from api.utils.http_exceptions import INVALID_CREDENTIALS
from tests.utils.assertions import NOT_AUTHENTICATED_EXCEPTION, assert_HTTPException_EQ
from tests.utils.fake_db import override_get_engine
from tests.utils.fixtures import token


class MethodType(Enum):
    GET = 1
    POST = 2
    PUT = 3
    DELETE = 4


class TestBase:
    """
    Used to inject a TestClient in the test class without a __init__ function

    This is needed as pytest detects no test classes with a constructor.
    """

    app.dependency_overrides[get_engine] = override_get_engine
    _client: TestClient = TestClient(app)

    @property
    def client(self) -> TestClient:
        return self._client

    async def _get_path(self) -> str:
        """
        This returns the path that is currently tested.

        This should be implemented by the class that implements the tests for the path
        """
        raise NotImplementedError

    @property
    def _get_method(self) -> MethodType:
        """
        The method that should be used in the test.

        This should be implemented by the child class.
        """
        raise NotImplementedError

    @pytest.mark.asyncio
    async def test_no_authentication(self):
        """
        Asserts the api is returning and error when the route is called with no authentication.
        """
        path = await self._get_path()
        match self._get_method:
            case MethodType.GET:
                response: httpx.Response = self.client.get(path)
            case MethodType.POST:
                response: httpx.Response = self.client.post(path)
            case MethodType.PUT:
                response: httpx.Response = self.client.put(path)
            case MethodType.DELETE:
                response: httpx.Response = self.client.delete(path)
            case _:
                raise NotImplementedError

        assert_HTTPException_EQ(response, NOT_AUTHENTICATED_EXCEPTION)

    @pytest.mark.asyncio
    async def test_wrong_authentication(self, token: str):
        """
        Asserts the api is returning and error when the route is called with wrong authentication.
        """
        # Invalidate token
        token += "_wrong"

        path = await self._get_path()
        match self._get_method:
            case MethodType.GET:
                response: httpx.Response = self.client.get(path, headers={"Authorization": f"Bearer {token}"})
            case MethodType.POST:
                response: httpx.Response = self.client.post(path, headers={"Authorization": f"Bearer {token}"})
            case MethodType.PUT:
                response: httpx.Response = self.client.put(path, headers={"Authorization": f"Bearer {token}"})
            case MethodType.DELETE:
                response: httpx.Response = self.client.delete(path, headers={"Authorization": f"Bearer {token}"})
            case _:
                raise NotImplementedError

        assert_HTTPException_EQ(response, INVALID_CREDENTIALS)


class _TestGetAuthentication(TestBase):

    @property
    def _get_method(self) -> MethodType:
        return MethodType.GET


class _TestPostAuthentication(TestBase):

    @property
    def _get_method(self) -> MethodType:
        return MethodType.POST


class _TestPutAuthentication(TestBase):

    @property
    def _get_method(self) -> MethodType:
        return MethodType.PUT


class _TestDeleteAuthentication(TestBase):

    @property
    def _get_method(self) -> MethodType:
        return MethodType.DELETE
