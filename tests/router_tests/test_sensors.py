import asyncio
import random

import httpx
import pytest
from pytest_lazy_fixtures import lf
from sqlmodel import delete, select

from api.models.database_models import DBUser, Sensor, SensorData, SensorPermission
from api.models.enum_models import SensorTypeModel
from api.utils.http_exceptions import INVALID_SENSOR_TYPE, MISSING_PRIVILEGES, NO_SENSOR_WITH_THIS_ID
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


async def create_sensor(
    *, name: str = "Sensor1", sensor_type: SensorTypeModel = SensorTypeModel.ENVIRONMENTAL
) -> Sensor:
    """
    Creates a new `Sensor` in the testing database.
    Args:
        name (str): The name of the Sensor
        sensor_type (SensorTypeModel): The type of the Sensor

    Returns:
        The created `Sensor`.
    """
    await clear_sensors()

    sensor: str = Sensor(name=name, type=sensor_type)
    async with async_fake_session_maker() as session:
        session.add(sensor)
        await session.commit()
        await session.refresh(sensor)

    return sensor


async def create_sensors(sensor_type: SensorTypeModel = SensorTypeModel.ENVIRONMENTAL) -> list[Sensor]:
    """
    Creates two `Sensor`s in the testing database.
    Args:
        sensor_type (SensorTypeModel): The type of the Sensor

    Returns:
        The created `Sensor`s.
    """
    sensors = [Sensor(name="Sensor1", type=sensor_type), Sensor(name="Sensor2", type=sensor_type)]
    async with async_fake_session_maker() as session:
        await clear_sensors()
        for sensor in sensors:
            session.add(sensor)
            await session.commit()
            await session.refresh(sensor)
    return sensors


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
            await self._get_path, headers={"Authorization": f"Bearer {superuser_token}"}
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

        response: httpx.Response = self.client.get(await self._get_path, headers={"Authorization": f"Bearer {token}"})
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

        response: httpx.Response = self.client.get(await self._get_path, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestGetSensor(_TestGetAuthentication):

    @property
    async def _get_path(self) -> str:
        return "/sensor/0"

    @pytest.mark.asyncio
    async def test_no_sensor(self, token: str):
        """
        Asserts a HTTPException is raised when no sensor with the given id was found
        """

        await clear_sensors()
        response: httpx.Response = self.client.get(await self._get_path, headers={"Authorization": f"Bearer {token}"})

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
            await self._get_path, headers={"Authorization": f"Bearer {token}"}, json=data
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
            await self._get_path, headers={"Authorization": f"Bearer {superuser_token}"}, json=data
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


class TestCreateSensorData(_TestPostAuthentication):

    @property
    async def _get_path(self) -> str:
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


class _TestGetSensorBase(_TestGetAuthentication):
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

    @property
    async def _get_path(self) -> str:
        return f"sensor/{(await self._get_sensor).id}/{self._get_sensor_endpoint}"

    @property
    async def _get_sensor(self) -> Sensor:
        if self.sensor:
            return self.sensor

        self.sensor = await create_sensor(sensor_type=self._get_sensor_type)
        return self.sensor

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

        response: httpx.Response = self.client.get(await self._get_path, headers={"Authorization": f"Bearer {token}"})
        assert_HTTPException_EQ(response, MISSING_PRIVILEGES)


class TestGetSensorData(_TestGetSensorBase):

    @property
    def _get_sensor_endpoint(self) -> str:
        return "data"

    @property
    def _get_sensor_type(self) -> SensorTypeModel:
        return SensorTypeModel.ENVIRONMENTAL

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


class TestGetSensorDataDaily(_TestGetSensorBase):

    @property
    def _get_sensor_endpoint(self) -> str:
        return "data/daily"

    @property
    def _get_sensor_type(self) -> SensorTypeModel:
        return SensorTypeModel.ENVIRONMENTAL

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
