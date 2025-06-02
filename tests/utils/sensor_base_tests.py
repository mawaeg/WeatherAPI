from typing import Any, Type

import httpx
import pytest
from pytest_lazy_fixtures import lf
from sqlmodel import delete, select

from api.models.database_models import DatabaseModelBase, Sensor, SensorPermission
from api.models.enum_models import SensorTypeModel
from api.utils.http_exceptions import INVALID_SENSOR_TYPE, MISSING_PRIVILEGES
from tests.utils.assertions import assert_HTTPException_EQ
from tests.utils.authentication_tests import _TestGetAuthentication, _TestPostAuthentication
from tests.utils.fake_db import async_fake_session_maker
from tests.utils.fixtures import token
from tests.utils.sensor_utils import create_sensor, create_sensor_permission


class _TestSensorMixin:
    sensor: Sensor | None = None

    @property
    def _get_sensor_endpoint(self) -> str:
        """
        The sensor endpoint that should be used in the test.

        Because of the check if a sensor exists we always need a valid sensor id.
        Therefore, we dynamically build the path.
        The first part is always the same, but the endpoint path should be what this function returns.
        sensor/<sensor_id>/<endpoint>

        This should be implemented by the child class.
        """
        return NotImplemented

    @property
    def _get_sensor_type(self) -> SensorTypeModel:
        """
        The type of sensor that should be used in the test.

        This should be implemented by the child class.
        """
        raise NotImplemented

    async def _base_get_path(self) -> str:
        return f"sensor/{(await self._get_sensor()).id}/{self._get_sensor_endpoint}"

    async def _get_sensor(self) -> Sensor:
        if self.sensor:
            return self.sensor

        self.sensor = await create_sensor(sensor_type=self._get_sensor_type)
        return self.sensor


class _TestCreateSensorBase(_TestPostAuthentication, _TestSensorMixin):
    async def _get_path(self) -> str:
        return await self._base_get_path()

    @property
    def _get_data(self) -> dict[str, Any]:
        """
        The data that should be sent in the test request.

        This should be implemented by the child class.
        """
        raise NotImplemented

    @property
    def _get_sql_model(self) -> Type[DatabaseModelBase]:
        """
        The model that should be inserted in the database.

        This should be implemented by the child class.
        """
        raise NotImplemented

    @pytest.mark.asyncio
    async def test_create_sensor_base_no_permissions(self, token: str):
        """
        Asserts that the creation fails if the user has no write permissions for the sensor.
        """
        async with async_fake_session_maker() as session:
            await session.execute(delete(SensorPermission))
            await session.commit()

        response: httpx.Response = self.client.post(
            await self._get_path(), headers={"Authorization": f"Bearer {token}"}, json=self._get_data
        )
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)

    @pytest.mark.asyncio
    async def test_create_sensor_base(self, token: str):
        """
        Assert that creating a new sensor data returns the sensor data and that the sensor data is created in the database.
        """
        await create_sensor_permission(token, await self._get_sensor(), write=True)

        response: httpx.Response = self.client.post(
            await self._get_path(), headers={"Authorization": f"Bearer {token}"}, json=self._get_data
        )

        # Assert the request was successful.
        assert response.status_code == 201

        # Assert the sensor data was added to the database.
        async with async_fake_session_maker() as session:
            result = await session.execute(
                select(self._get_sql_model).where(self._get_sql_model.id == response.json().get("id"))
            )
            sensor_data: DatabaseModelBase | None = result.scalars().first()
        assert sensor_data is not None

        assert response.json() == sensor_data.model_dump(mode="json")


class _TestGetSensorBase(_TestGetAuthentication, _TestSensorMixin):
    # ToDo Add test to check error when sensor is not existing

    async def _get_path(self) -> str:
        return await self._base_get_path()

    @property
    def _run_get(self) -> bool:
        """
        Whether the "normal" (successful test) get request should be executed.
        """
        return True

    async def _get_data(self) -> list[DatabaseModelBase]:
        """
        The data that should be inserted into the database.

        This should be implemented by the child class.
        """
        raise NotImplemented

    @pytest.mark.asyncio
    async def test_get_sensor_data_wrong_type(self, token: str):
        """
        Asserts the request fails when the user does not have permissions to read the data.
        """
        sensor: Sensor = await create_sensor(
            sensor_type=next(st for st in SensorTypeModel if st != self._get_sensor_type)
        )
        await create_sensor_permission(token, sensor, read=True)

        response: httpx.Response = self.client.get(
            f"sensor/{sensor.id}/{self._get_sensor_endpoint}", headers={"Authorization": f"Bearer {token}"}
        )
        assert_HTTPException_EQ(response, INVALID_SENSOR_TYPE)

    @pytest.mark.asyncio
    async def test_get_sensor_data_no_permissions(self, token: str):
        """
        Asserts the request fails when the user does not have permissions to read the data.
        """
        async with async_fake_session_maker() as session:
            await session.execute(delete(SensorPermission))
            await session.commit()

        response: httpx.Response = self.client.get(await self._get_path(), headers={"Authorization": f"Bearer {token}"})
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)

    @pytest.mark.parametrize("user_token", [lf("token"), lf("superuser_token")])
    @pytest.mark.asyncio
    async def test_get_sensor_base(self, user_token: str):
        """
        Asserts the api is returning the expected data when authenticated.
        """
        if not self._run_get:
            pytest.skip("Test should not be executed.")

        await create_sensor_permission(user_token, await self._get_sensor(), read=True)

        # ToDo Inserting and comparing multiple sometimes fails because of wrong order.
        # Is there and easy way to test it with multiple data?

        # Insert fake sensor data
        fake_data = await self._get_data()

        async with async_fake_session_maker() as session:
            for data in fake_data:
                session.add(data)
                await session.commit()
                await session.refresh(data)

        response: httpx.Response = self.client.get(
            await self._get_path(), headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        print([data.model_dump(mode="json") for data in fake_data])
        assert response.json() == [data.model_dump(mode="json") for data in fake_data]
