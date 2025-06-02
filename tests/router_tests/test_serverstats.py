import httpx
import pytest
from pytest_httpx import HTTPXMock

from api.utils.http_exceptions import MISSING_PRIVILEGES, NO_SERVERSTATS_DATA
from tests.utils.assertions import assert_HTTPException_EQ
from tests.utils.authentication_tests import _TestGetAuthentication
from tests.utils.fixtures import superuser_token, token
from tests.utils.serverstats_dump import (
    serverstats_history_dump,
    serverstats_history_expected_result,
    serverstats_live_dump,
)


class TestGetServerStatsLive(_TestGetAuthentication):

    async def _get_path(self) -> str:
        return "/server/stats/live"

    @pytest.mark.asyncio
    async def test_normal_user(self, token: str):
        """
        Asserts the api is returning an error when the route is called with wrong authentication.
        """

        response: httpx.Response = self.client.get(await self._get_path(), headers={"Authorization": f"Bearer {token}"})
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)

    @pytest.mark.asyncio
    async def test_get_live_serverstats_pph_error(self, superuser_token: str, httpx_mock: HTTPXMock):
        """
        Assert the api is returning an error, when the pph api returned anything other than 200.
        """
        httpx_mock.add_response(status_code=503)

        response: httpx.Response = self.client.get(
            await self._get_path(), headers={"Authorization": f"Bearer {superuser_token}"}
        )
        assert_HTTPException_EQ(response, NO_SERVERSTATS_DATA)

    @pytest.mark.asyncio
    async def test_get_live_serverstats(self, superuser_token: str, httpx_mock: HTTPXMock):
        """
        Assert the api is correctly returning data when the pph api returns correct data and 200.
        """
        httpx_mock.add_response(json=serverstats_live_dump)

        response: httpx.Response = self.client.get(
            await self._get_path(), headers={"Authorization": f"Bearer {superuser_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == len(serverstats_live_dump["data"])


class TestGetServerStatsHistory(_TestGetAuthentication):

    async def _get_path(self) -> str:
        return "/server/stats/history"

    @pytest.mark.asyncio
    async def test_normal_user(self, token: str):
        """
        Asserts the api is returning an error when the route is called with wrong authentication.
        """

        response: httpx.Response = self.client.get(await self._get_path(), headers={"Authorization": f"Bearer {token}"})
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)

    @pytest.mark.asyncio
    async def test_get_history_serverstats_pph_error(self, superuser_token: str, httpx_mock: HTTPXMock):
        """
        Assert the api is returning an error, when the pph api returned anything other than 200.
        """
        httpx_mock.add_response(status_code=503)

        response: httpx.Response = self.client.get(
            await self._get_path(), headers={"Authorization": f"Bearer {superuser_token}"}
        )
        assert_HTTPException_EQ(response, NO_SERVERSTATS_DATA)

    @pytest.mark.asyncio
    async def test_get_history_serverstats(self, superuser_token: str, httpx_mock: HTTPXMock):
        """
        Assert the api is correctly returning data when the pph api returns correct data and 200.
        """
        httpx_mock.add_response(json=serverstats_history_dump)

        max_amount: int = len(serverstats_history_dump["data"]["chart"]["full_cpu_usage"]["labels"])
        response: httpx.Response = self.client.get(
            await self._get_path(), params={"entries": max_amount}, headers={"Authorization": f"Bearer {superuser_token}"}
        )
        assert response.status_code == 200
        assert response.json() == serverstats_history_expected_result

    @pytest.mark.asyncio
    async def test_get_history_serverstats_not_enough_entries(self, superuser_token: str, httpx_mock: HTTPXMock):
        """
        Assert the api is returning an error when the number of requested entries is bigger than the available amount of entries..
        """
        httpx_mock.add_response(json=serverstats_history_dump)

        max_amount: int = len(serverstats_history_dump["data"]["chart"]["full_cpu_usage"]["labels"]) + 1
        response: httpx.Response = self.client.get(
            await self._get_path(), params={"entries": max_amount}, headers={"Authorization": f"Bearer {superuser_token}"}
        )

        assert_HTTPException_EQ(response, NO_SERVERSTATS_DATA)
