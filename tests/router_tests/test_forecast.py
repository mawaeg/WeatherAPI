import httpx
import pytest
from pytest_httpx import HTTPXMock

from api.utils.http_exceptions import NO_FORECAST_DATA
from tests.utils.assertions import assert_HTTPException_EQ
from tests.utils.authentication_tests import _TestGetAuthentication
from tests.utils.fixtures import token
from tests.utils.forecast_dump import forecast_json_dump


class TestForecast(_TestGetAuthentication):

    async def _get_path(self) -> str:
        return "/forecast?lat=10&lon=10"

    @pytest.mark.asyncio
    async def test_get_forecast_owm_error(self, token: str, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=503)

        response: httpx.Response = self.client.get(await self._get_path(), headers={"Authorization": f"Bearer {token}"})
        assert_HTTPException_EQ(response, NO_FORECAST_DATA)

    @pytest.mark.asyncio
    async def test_get_forecast(self, token: str, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=forecast_json_dump)

        response: httpx.Response = self.client.get(await self._get_path(), headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # ToDo Efficient way to compare both dicts?
        data = response.json()
        # Simple check to make sure the data makes sense.
        assert data["current"]
        assert data["hourly"]
        assert data["daily"]
