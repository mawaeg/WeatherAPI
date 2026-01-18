import random
from typing import Any, Type

import httpx
import pytest
from sqlmodel import delete, select

from api.models.database_models import DatabaseModelBase, Sensor, SensorData, SensorState
from api.models.enum_models import SensorTypeModel
from api.utils.http_exceptions import MISSING_PRIVILEGES, NO_SENSOR_WITH_THIS_ID
from tests.utils.assertions import assert_HTTPException_EQ
from tests.utils.authentication_tests import _TestGetAuthentication, _TestPostAuthentication
from tests.utils.fake_db import async_fake_session_maker
from tests.utils.fixtures import superuser_token, token
from tests.utils.sensor_base_tests import _TestCreateSensorBase, _TestGetSensorBase
from tests.utils.sensor_utils import clear_sensors, create_sensor, create_sensor_permission, create_sensors

# ToDo Create Test: Check response with created data and the database result or only one of both?


class TestGetSensors(_TestGetAuthentication):

    async def _get_path(self) -> str:
        return "/sensor/list"

    @pytest.mark.asyncio
    async def test_get_sensors_superuser(self, superuser_token: str):
        """
        Asserts the api is returning all existing sensors when authenticated as superuser.
        """

        # Insert fake sensors
        sensors: list[Sensor] = await create_sensors()

        response: httpx.Response = self.client.get(
            await self._get_path(), headers={"Authorization": f"Bearer {superuser_token}"}
        )
        assert response.status_code == 200

        # We only check for the len, as the created model is not the same as the returned one.
        # ToDo Should there be a check whether it actually returns a `UserSensor`?
        assert len(response.json()) == len(sensors)

    @pytest.mark.asyncio
    async def test_get_sensors(self, token: str):
        """
        Asserts the api is returning all sensors with permissions for the current authenticated user.
        """

        # Insert fake sensors
        sensors: list[Sensor] = await create_sensors()

        await create_sensor_permission(token, sensors[0], read=True)

        response: httpx.Response = self.client.get(await self._get_path(), headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_get_sensors_false_permission(self, token: str):
        """
        Asserts the api is not returning `Sensor`s where both of the `SensorPermission`s are False.

        This test does not actually cover python code, but covers the logic of the rather complicated sql query.
        """

        # Insert fake sensors
        sensors: list[Sensor] = await create_sensors()

        await create_sensor_permission(token, sensors[0])

        response: httpx.Response = self.client.get(await self._get_path(), headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestGetSensor(_TestGetAuthentication):

    async def _get_path(self) -> str:
        return "/sensor/0"

    @pytest.mark.asyncio
    async def test_no_sensor(self, token: str):
        """
        Asserts a HTTPException is raised when no sensor with the given id was found
        """

        await clear_sensors()
        response: httpx.Response = self.client.get(await self._get_path(), headers={"Authorization": f"Bearer {token}"})

        assert_HTTPException_EQ(response, NO_SENSOR_WITH_THIS_ID)

    @pytest.mark.asyncio
    async def test_get_sensor(self, token: str):
        """
        Asserts the given sensor is returned if it is existing.
        """

        sensor: Sensor = await create_sensor()

        # We need to use the custom id here to make sure the sensor we are requesting is the created sensor
        response: httpx.Response = self.client.get(f"/sensor/{sensor.id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == sensor.model_dump()


class TestCreateSensor(_TestPostAuthentication):

    async def _get_path(self) -> str:
        return "/sensor"

    @pytest.mark.asyncio
    async def test_normal_user(self, token: str):
        """
        Asserts the api is returning an error when the route is called with wrong authentication.
        """
        await clear_sensors()
        data = {"name": "TestSensor1", "type": "environmental"}

        response: httpx.Response = self.client.post(
            await self._get_path(), headers={"Authorization": f"Bearer {token}"}, json=data
        )
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)

    @pytest.mark.asyncio
    async def test_create_sensor(self, superuser_token: str):
        """
        Assert that creating a new sensor returns the sensor and that the sensor is created in the database.
        """
        await clear_sensors()
        data = {"name": "TestSensor1", "type": "environmental"}
        response: httpx.Response = self.client.post(
            await self._get_path(), headers={"Authorization": f"Bearer {superuser_token}"}, json=data
        )

        # Assert the request was successful.
        assert response.json().get("id") is not None
        assert response.status_code == 201
        assert response.json().get("name") == data["name"]
        assert response.json().get("type") == data["type"]

        # Assert the sensor was added to the database.
        async with async_fake_session_maker() as session:
            result = await session.execute(select(Sensor).where(Sensor.id == response.json().get("id")))
            sensor: Sensor | None = result.scalars().first()
        assert sensor is not None
        assert response.json() == sensor.model_dump()


class TestCreateSensorData(_TestCreateSensorBase):

    @property
    def _get_sensor_type(self) -> SensorTypeModel:
        return SensorTypeModel.ENVIRONMENTAL

    @property
    def _get_sensor_endpoint(self) -> str:
        return "data"

    @property
    def _get_data(self) -> dict[str, Any]:
        return {"temperature": 32.1, "humidity": 56.78, "pressure": 123.45, "voltage": 3.45}

    @property
    def _get_sql_model(self) -> Type[DatabaseModelBase]:
        return SensorData


class TestGetSensorData(_TestGetSensorBase):

    @property
    def _get_sensor_endpoint(self) -> str:
        return "data"

    @property
    def _get_sensor_type(self) -> SensorTypeModel:
        return SensorTypeModel.ENVIRONMENTAL

    async def _get_data(self) -> list[DatabaseModelBase]:
        return [
            SensorData(
                sensor_id=(await self._get_sensor()).id, temperature=1.23, humidity=54.32, pressure=1234, voltage=3.21
            ),
        ]


class TestGetSensorDataDaily(_TestGetSensorBase):

    @property
    def _get_sensor_endpoint(self) -> str:
        return "data/daily"

    @property
    def _get_sensor_type(self) -> SensorTypeModel:
        return SensorTypeModel.ENVIRONMENTAL

    @property
    def _run_get(self) -> bool:
        # We have a custom get command here
        return False

    @pytest.mark.asyncio
    async def test_get_sensor_data_daily(self, token: str):
        """
        Asserts the api is returning the expected daily data when authenticated.
        """
        async with async_fake_session_maker() as session:
            await session.execute(delete(SensorData))
            await session.commit()

        # Create a sensor and permissions
        sensor: Sensor = await create_sensor()
        await create_sensor_permission(token, sensor, read=True)

        # Insert random temperatures in the database
        temps = random.sample(range(100), 2)

        async with async_fake_session_maker() as session:
            for temp in temps:
                data: SensorData = SensorData(
                    sensor_id=sensor.id, temperature=temp, humidity=54.32, pressure=1234, voltage=3.21
                )
                session.add(data)
                await session.commit()

        response: httpx.Response = self.client.get(
            f"/sensor/{sensor.id}/data/daily?amount=1", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()[0]["temperature"] == round(sum(temps) / len(temps), 2)


class TestCreateSensorState(_TestCreateSensorBase):

    @property
    def _get_sensor_type(self) -> SensorTypeModel:
        return SensorTypeModel.STATE

    @property
    def _get_sensor_endpoint(self) -> str:
        return "state"

    @property
    def _get_data(self) -> dict[str, Any]:
        return {"state": True, "voltage": 3.45}

    @property
    def _get_sql_model(self) -> Type[DatabaseModelBase]:
        return SensorState


class TestGetSensorState(_TestGetSensorBase):

    @property
    def _get_sensor_endpoint(self) -> str:
        return "state"

    @property
    def _get_sensor_type(self) -> SensorTypeModel:
        return SensorTypeModel.STATE

    async def _get_data(self):
        return [SensorState(sensor_id=(await self._get_sensor()).id, state=True, voltage=3.21)]
