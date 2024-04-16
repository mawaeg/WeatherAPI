import asyncio
import copy
from datetime import datetime, timedelta

import pytest

from api.models.forecast_models import Forecast
from api.utils.forecast_buffer import ForecastBuffer, ForecastBufferObject
from tests.utils.forecast_dump import forecast_json_dump

lat, lon = "10", "10"
forecast: Forecast = Forecast(**forecast_json_dump)


@pytest.mark.asyncio
async def test_forecast_buffer_object():
    """
    Asserts the forecast buffer object works as expected
    """
    buffer_object1: ForecastBufferObject = ForecastBufferObject(lat, lon, forecast, timedelta(minutes=10))
    buffer_object2: ForecastBufferObject = copy.deepcopy(buffer_object1)

    # Assert equal works as expected
    assert buffer_object1 == buffer_object2
    buffer_object2.lat = "20"
    assert buffer_object1 != buffer_object2

    # Assert latlon is correctly returned
    assert buffer_object1.latlon == f"{lat};{lon}"

    # Assert is_expired works as expected
    assert not buffer_object1.is_expired
    buffer_object1.valid_until = datetime.utcnow()
    await asyncio.sleep(0.1)
    assert buffer_object1.is_expired


@pytest.mark.asyncio
async def test_forecast_buffer():
    """
    Assert that the `ForecastBuffer` is working as expected.
    """
    buffer: ForecastBuffer = ForecastBuffer()

    # Assert the correct forecast is returned if requested
    buffer.add(lat, lon, forecast)
    assert buffer.get(lat, lon) == forecast

    # Assert that expired entries get ignored
    buffer.cache[0].valid_until = datetime.utcnow()
    await asyncio.sleep(0.1)
    assert buffer.get(lat, lon) is None
    assert len(buffer) == 0

    # Assert that the buffer does not get larger than the defined max_size
    for _ in range(buffer.max_size + 1):
        buffer.add(lat, lon, forecast)
    assert len(buffer) == buffer.max_size
