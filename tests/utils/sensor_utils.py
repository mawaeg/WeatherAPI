from sqlmodel import delete

from api.models.database_models import DBUser, Sensor, SensorPermission
from api.models.enum_models import SensorTypeModel
from api.utils.security import get_current_user
from tests.utils.fake_db import async_fake_session_maker
from tests.utils.fixtures import token


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
