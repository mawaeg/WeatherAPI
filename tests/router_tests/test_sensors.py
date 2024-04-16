import random

import httpx
import pytest
from pytest_lazy_fixtures import lf
from sqlmodel import delete, select

from api.models.database_models import DBUser, Sensor, SensorData, SensorPermission
from api.utils.http_exceptions import MISSING_PRIVILEGES, NO_SENSOR_WITH_THIS_ID
from api.utils.security import get_current_user
from tests.utils.assertions import assert_HTTPException_EQ
from tests.utils.authentication_tests import _TestGetAuthentication, _TestPostAuthentication
from tests.utils.fake_db import async_fake_session_maker
from tests.utils.fixtures import superuser_token, token


async def clear_sensors():
    """
    Clears all `Sensor`s from the testing database
    """
    async with async_fake_session_maker() as session:
        await session.execute(delete(Sensor))
        await session.commit()


async def create_sensor(name: str = "Sensor1") -> Sensor:
    """
    Creates a new `Sensor` in the testing database.
    Args:
        name (str): The name of the Sensor

    Returns:
        The created `Sensor`.
    """
    await clear_sensors()

    sensor: str = Sensor(name=name)
    async with async_fake_session_maker() as session:
        session.add(sensor)
        await session.commit()
        await session.refresh(sensor)

    return sensor


async def create_sensor_permission(token: str, sensor: Sensor, *, write: bool = False, read: bool = False) -> None:
    """
    Creates a `SensorPermission` for the given user (via the token) and `Sensor`.
    Args:
        token (str): The authentication token to identify the user.
        sensor (Sensor): The sensor for which the permissions should be applied.
        write (bool): The write permission that should be set.
        read (bool): The read permission that should be set.
    """
    async with async_fake_session_maker() as session:
        await session.execute(delete(SensorPermission))
        await session.commit()
        # We need to user from the token to create the correct sensor permission.
        user: DBUser = await get_current_user(token, session)

        sensor_permission: SensorPermission = SensorPermission(
            user_id=user.id, sensor_id=sensor.id, write=write, read=read
        )
        session.add(sensor_permission)
        await session.commit()


# ToDo Create Test: Check response with created data and the database result or only one of both?


class TestGetSensors(_TestGetAuthentication):

    @property
    def _get_path(self) -> str:
        return "/sensor/list"

    @pytest.mark.asyncio
    async def test_get_sensors(self, token: str):
        """
        Asserts the api is returning the expected data when authenticated.
        """

        # Insert fake sensors
        sensors = [Sensor(name="Sensor1"), Sensor(name="Sensor2")]
        async with async_fake_session_maker() as session:
            await clear_sensors()
            for sensor in sensors:
                session.add(sensor)
                await session.commit()
                await session.refresh(sensor)

        response: httpx.Response = self.client.get(self._get_path, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == [sensor.model_dump() for sensor in sensors]


class TestGetSensor(_TestGetAuthentication):

    @property
    def _get_path(self) -> str:
        return "/sensor/0"

    @pytest.mark.asyncio
    async def test_no_sensor(self, token: str):
        """
        Asserts a HTTPException is raised when no sensor with the given id was found
        """

        await clear_sensors()
        response: httpx.Response = self.client.get(self._get_path, headers={"Authorization": f"Bearer {token}"})

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
    @property
    def _get_path(self) -> str:
        return "/sensor"

    @pytest.mark.asyncio
    async def test_normal_user(self, token: str):
        """
        Asserts the api is returning an error when the route is called with wrong authentication.
        """
        await clear_sensors()
        data = {"name": "TestSensor1"}

        response: httpx.Response = self.client.post(
            self._get_path, headers={"Authorization": f"Bearer {token}"}, json=data
        )
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)

    @pytest.mark.asyncio
    async def test_create_sensor(self, superuser_token: str):
        """
        Assert that creating a new sensor returns the sensor and that the sensor is created in the database.
        """
        await clear_sensors()
        data = {"name": "TestSensor1"}
        response: httpx.Response = self.client.post(
            self._get_path, headers={"Authorization": f"Bearer {superuser_token}"}, json=data
        )

        # Assert the request was successful.
        assert response.json().get("id") is not None
        assert response.status_code == 201
        assert response.json().get("name") == data["name"]

        # Assert the sensor was added to the database.
        async with async_fake_session_maker() as session:
            result = await session.execute(select(Sensor).where(Sensor.id == response.json().get("id")))
            sensor: Sensor | None = result.scalars().first()
        assert sensor is not None
        assert response.json() == sensor.model_dump()


class TestCreateSensorData(_TestPostAuthentication):

    @property
    def _get_path(self) -> str:
        return "/sensor/0/data"

    @pytest.mark.asyncio
    async def test_create_sensor_data_no_permissions(self, token: str):
        """
        Asserts that the creation fails if the user has no write permissions for the sensor.
        """
        async with async_fake_session_maker() as session:
            await session.execute(delete(SensorPermission))
            await session.commit()

        sensor: Sensor = await create_sensor()

        data = {"temperature": 32.1, "humidity": 56.78, "pressure": 123.45, "voltage": 3.45}

        response: httpx.Response = self.client.post(
            f"sensor/{sensor.id}/data", headers={"Authorization": f"Bearer {token}"}, json=data
        )
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)

    @pytest.mark.asyncio
    async def test_create_sensor_data(self, token: str):
        """
        Assert that creating a new sensor data returns the sensor data and that the sensor data is created in the database.
        """
        sensor: Sensor = await create_sensor()
        await create_sensor_permission(token, sensor, write=True)

        data = {"temperature": 32.1, "humidity": 56.78, "pressure": 123.45, "voltage": 3.45}

        response: httpx.Response = self.client.post(
            f"sensor/{sensor.id}/data", headers={"Authorization": f"Bearer {token}"}, json=data
        )

        # Assert the request was successful.
        assert response.status_code == 201

        # Assert the sensor data was added to the database.
        async with async_fake_session_maker() as session:
            result = await session.execute(select(SensorData).where(SensorData.id == response.json().get("id")))
            sensor_data: SensorData | None = result.scalars().first()
        assert sensor_data is not None

        assert response.json() == sensor_data.model_dump(mode="json")


class _TestGetSensorDataBase(_TestGetAuthentication):
    @pytest.mark.asyncio
    async def test_get_sensor_data_no_permissions(self, token: str):
        """
        Asserts the request fails when the user does not have permissions to read the data.
        """
        async with async_fake_session_maker() as session:
            await session.execute(delete(SensorPermission))
            await session.commit()

        response: httpx.Response = self.client.get(self._get_path, headers={"Authorization": f"Bearer {token}"})
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)


class TestGetSensorData(_TestGetSensorDataBase):

    @property
    def _get_path(self) -> str:

        return "/sensor/0/data"

    @pytest.mark.parametrize("user_token", [lf("token"), lf("superuser_token")])
    @pytest.mark.asyncio
    async def test_get_sensor_data(self, user_token: str):
        """
        Asserts the api is returning the expected data when authenticated.
        """
        sensor: Sensor = await create_sensor()
        await create_sensor_permission(user_token, sensor, read=True)

        # ToDo Inserting and comparing multiple sometimes fails because of wrong order.
        # Is there and easy way to test it with multiple data=

        # Insert fake sensor data
        sensor_data = [
            SensorData(sensor_id=sensor.id, temperature=1.23, humidity=54.32, pressure=1234, voltage=3.21),
            # SensorData(sensor_id=sensor.id, temperature=32.1, humidity=23.45, pressure=4321, voltage=1.23),
        ]
        async with async_fake_session_maker() as session:
            for data in sensor_data:
                session.add(data)
                await session.commit()
                await session.refresh(data)

        response: httpx.Response = self.client.get(
            f"/sensor/{sensor.id}/data", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert response.json() == [data.model_dump(mode="json") for data in sensor_data]


class TestGetSensorDataDaily(_TestGetSensorDataBase):

    @property
    def _get_path(self) -> str:
        return "/sensor/0/data/daily"

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
