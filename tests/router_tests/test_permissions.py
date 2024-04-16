import httpx
import pytest
from sqlmodel import delete, select

from api.models.database_models import DBUser, Sensor, SensorPermission
from api.utils.security import get_current_user
from tests.utils.assertions import assert_missing_privileges
from tests.utils.authentication_tests import _TestDeleteAuthentication, _TestGetAuthentication, _TestPutAuthentication
from tests.utils.fake_db import async_fake_session_maker
from tests.utils.fixtures import superuser_token, token


async def create_sensor_and_extract_user(token: str) -> tuple[Sensor, DBUser]:
    """
    Creates a new sensor and extracts the user from the given token
    Args:
        token (str): The token of the current user.

    Returns:
        The created `Sensor` and the `DBUser`
    """
    async with async_fake_session_maker() as session:
        # Delete all sensors to avoid error because of duplicated
        await session.execute(delete(Sensor))
        await session.commit()

        # Get current user and add new sensor
        user: DBUser = await get_current_user(token, session)
        sensor: Sensor = Sensor(name="test_put_user_sensor")
        session.add(sensor)
        await session.commit()
        await session.refresh(sensor)

    return sensor, user


class TestPutSensorPermission(_TestPutAuthentication):

    @property
    def _get_path(self) -> str:
        return "/permissions/sensor"

    @pytest.mark.asyncio
    async def test_put_sensor_permission_normal_user(self, token: str):
        """
        Asserts the api is returning an error when the route is called with a non superuser.
        """
        sensor_permission = {"user_id": 1, "sensor_id": 1, "read": True, "write": False}
        response: httpx.Response = self.client.put(
            self._get_path, headers={"Authorization": f"Bearer {token}"}, json=sensor_permission
        )
        assert_missing_privileges(response)

    @staticmethod
    async def assert_created_correctly(response: httpx.Response, sensor_permission_json: dict) -> None:
        """
        Assert that a `SensorPermission` was created correctly
        Args:
            response (httpx.Response): The response from the request made to the api.
            sensor_permission_json (dict): The json used to create the new `SensorPermission`.
        """
        assert response.status_code == 201

        async with async_fake_session_maker() as session:
            result = await session.execute(
                select(SensorPermission).where(
                    SensorPermission.user_id == sensor_permission_json["user_id"],
                    SensorPermission.sensor_id == sensor_permission_json["sensor_id"],
                    SensorPermission.read == sensor_permission_json["read"],
                    SensorPermission.write == sensor_permission_json["write"],
                )
            )
            sensor_permission: SensorPermission = result.scalars().first()

        assert response.json() == sensor_permission.model_dump(mode="json")

    @pytest.mark.asyncio
    async def test_put_sensor_permission(self, superuser_token: str):
        """
        Assert the api creates a new `SensorPermission` in the database and returns the created object.
        """
        sensor, user = await create_sensor_and_extract_user(superuser_token)

        sensor_permission_json = {"user_id": user.id, "sensor_id": sensor.id, "read": True, "write": False}
        response: httpx.Response = self.client.put(
            self._get_path, headers={"Authorization": f"Bearer {superuser_token}"}, json=sensor_permission_json
        )
        await self.assert_created_correctly(response, sensor_permission_json)

        # Modify the data and ensure the existing `SensorPermission` gets modified
        sensor_permission_json["read"] = False
        sensor_permission_json["write"] = True
        response: httpx.Response = self.client.put(
            self._get_path, headers={"Authorization": f"Bearer {superuser_token}"}, json=sensor_permission_json
        )
        await self.assert_created_correctly(response, sensor_permission_json)


class TestGetSensorPermission(_TestGetAuthentication):

    @property
    def _get_path(self) -> str:
        return "/permissions/sensor"

    @pytest.mark.asyncio
    async def test_get_sensor_permission_normal_user(self, token: str):
        """
        Assert an error is raised when a non superuser requests the endpoint.
        """
        response: httpx.Response = self.client.get(
            f"{self._get_path}?user_id=1&sensor_id=1", headers={"Authorization": f"Bearer {token}"}
        )
        assert_missing_privileges(response)

    @pytest.mark.asyncio
    async def test_get_sensor_permission_no_permission(self, superuser_token: str):
        """
        Asserts the api raises an error when the requested sensor permission is not existing.
        """
        async with async_fake_session_maker() as session:
            await session.execute(delete(SensorPermission))
            await session.commit()
        response: httpx.Response = self.client.get(
            f"{self._get_path}?user_id=1&sensor_id=1", headers={"Authorization": f"Bearer {superuser_token}"}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "This permission does not exist yet."}

    @pytest.mark.asyncio
    async def test_get_sensor(self, superuser_token: str):
        """
        Asserts the requested `SensorPermission` is returned by the api.
        """
        sensor, user = await create_sensor_and_extract_user(superuser_token)
        async with async_fake_session_maker() as session:
            await session.execute(delete(SensorPermission))
            await session.commit()

            sensor_permission: SensorPermission = SensorPermission(
                user_id=user.id, sensor_id=sensor.id, read=True, write=False
            )
            session.add(sensor_permission)
            await session.commit()
            await session.refresh(sensor_permission)

        response: httpx.Response = self.client.get(
            f"{self._get_path}?user_id={user.id}&sensor_id={sensor.id}",
            headers={"Authorization": f"Bearer {superuser_token}"},
        )
        assert response.status_code == 200
        assert response.json() == sensor_permission.model_dump(mode="json")


# ToDO Improve the duplicated code
class TestDeleteSensorPermission(_TestDeleteAuthentication):

    @property
    def _get_path(self) -> str:
        return "/permissions/sensor"

    @pytest.mark.asyncio
    async def test_delete_sensor_permission_normal_user(self, token: str):
        """
        Assert an error is raised when a non superuser requests the endpoint.
        """
        response: httpx.Response = self.client.delete(
            f"{self._get_path}?user_id=1&sensor_id=1", headers={"Authorization": f"Bearer {token}"}
        )
        assert_missing_privileges(response)

    @pytest.mark.asyncio
    async def test_delete_sensor_permission_no_permission(self, superuser_token: str):
        """
        Asserts the api raises an error when the requested sensor permission is not existing.
        """
        async with async_fake_session_maker() as session:
            await session.execute(delete(SensorPermission))
            await session.commit()
        response: httpx.Response = self.client.delete(
            f"{self._get_path}?user_id=1&sensor_id=1", headers={"Authorization": f"Bearer {superuser_token}"}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "This permission does not exist."}

    @pytest.mark.asyncio
    async def test_delete_sensor(self, superuser_token: str):
        """
        Asserts the requested `SensorPermission` is deleted by the api.
        """
        sensor, user = await create_sensor_and_extract_user(superuser_token)
        async with async_fake_session_maker() as session:
            await session.execute(delete(SensorPermission))
            await session.commit()

            sensor_permission: SensorPermission = SensorPermission(
                user_id=user.id, sensor_id=sensor.id, read=True, write=False
            )
            session.add(sensor_permission)
            await session.commit()
            await session.refresh(sensor_permission)

        response: httpx.Response = self.client.delete(
            f"{self._get_path}?user_id={user.id}&sensor_id={sensor.id}",
            headers={"Authorization": f"Bearer {superuser_token}"},
        )
        assert response.status_code == 204

        async with async_fake_session_maker() as session:
            result = await session.execute(select(SensorPermission).where(SensorPermission.id == sensor_permission.id))
            new_sensor_permission: SensorPermission | None = result.scalars().first()
        assert new_sensor_permission is None
