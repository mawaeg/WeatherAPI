import httpx
import pytest
from pytest_httpx import HTTPXMock

from tests.utils.authentication_tests import _TestGetAuthentication
from tests.utils.fixtures import token
from tests.utils.forecast_dump import forecast_json_dump


class TestForecast(_TestGetAuthentication):

    @property
    def _get_path(self) -> str:
        return "/forecast?lat=10&lon=10"

    @pytest.mark.asyncio
    async def test_get_forecast_owm_error(self, token: str, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=503)

        response: httpx.Response = self.client.get(self._get_path, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 502
        assert response.json()["detail"] == "Could not retrieve current forecast data."

    @pytest.mark.asyncio
    async def test_get_forecast(self, token: str, httpx_mock: HTTPXMock):
        httpx_mock.add_response(json=forecast_json_dump)

        response: httpx.Response = self.client.get(self._get_path, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # ToDo Efficient way to compare both dicts?
        data = response.json()
        # Simple check to make sure the data makes sense.
        assert data["current"]
        assert data["hourly"]
        assert data["daily"]
