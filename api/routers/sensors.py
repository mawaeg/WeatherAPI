from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.sql import func
from sqlmodel import NUMERIC, cast, select

from api.models.database_models import DBUser, Sensor, SensorCreate, SensorData, SensorDataCreate, User
from api.models.response_models import DailySensorData, NotFoundError
from api.utils.database import get_session
from api.utils.permissions import get_user_read_permissions, get_user_write_permissions
from api.utils.security import get_current_superuser, get_current_user

sensors_router = APIRouter(tags=["Sensors"], prefix="/sensor")


@sensors_router.get("/list", response_model=list[Sensor])
async def get_sensors(
    session: Annotated[AsyncSession, Depends(get_session)], current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Returns a list of all available sensors.
    Args:
        session (AsyncSession): A database session.
        current_user (User): The user that is currently logged in.

    Returns:
        A list of `Sensor`s.
    """
    result = await session.execute(select(Sensor))
    sensors = result.scalars().all()
    return sensors


@sensors_router.get(
    "/{sensor_id}",
    response_model=Sensor,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found", "model": NotFoundError}},
)
async def get_sensor(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    sensor_id: int,
):
    """
    Returns the information for a specific sensor
    Args:
        session (AsyncSession): A database session.
        current_user (User): The user that is currently logged in.
        sensor_id (int): The id of the sensor that should be returned.

    Returns:
        The requested `Sensor`.
    """
    sensor: Sensor | None = await session.get(Sensor, sensor_id)
    if not sensor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No sensor with this id.")
    return sensor


@sensors_router.post("", response_model=Sensor, status_code=status.HTTP_201_CREATED)
async def create_sensor(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_superuser: Annotated[User, Depends(get_current_superuser)],
    sensor: SensorCreate,
):
    """
    Creates a new sensor.
    Args:
        session (AsyncSession): A database session.
        current_superuser (User): The currently logged in superuser.
        sensor (SensorCreate): The sensor that should be created.

    Returns:
        The created `Sensor`.
    """
    sensor: Sensor = Sensor(**dict(sensor))
    session.add(sensor)
    await session.commit()
    await session.refresh(sensor)
    return sensor


@sensors_router.post("/{sensor_id}/data", response_model=SensorData, status_code=status.HTTP_201_CREATED)
async def create_sensor_data(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[DBUser, Depends(get_current_user)],
    sensor_id: int,
    data: SensorDataCreate,
):
    """
    Creates a new `SensorData`.
    Args:
        session (AsyncSession): A database session.
        current_user (DBUser): The user that is currently logged in.
        sensor_id (int): The id of the sensor creating the data.
        data (SensorDataCreate): The sensordata that should be created

    Returns:
        The created `SensorData`
    """
    await get_user_write_permissions(session, current_user, sensor_id)

    data: SensorData = SensorData(**dict(data), sensor_id=sensor_id)
    session.add(data)
    await session.commit()
    await session.refresh(data)
    return data


@sensors_router.get("/{sensor_id}/data", response_model=list[SensorData])
async def get_sensor_data(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    sensor_id: int,
    amount: int = 1,
):
    """
    Retrieves the last n `SensorData` objects from the database for a given sensor.
    Args:
        session (AsyncSession): A database session.
        current_user (User): The user that is currently logged in.
        sensor_id (int): The id of the sensor whose data should be retrieved.
        amount (int): The number of measurements that should be retrieved.

    Returns:
        A list of `SensorData` objects.
    """
    await get_user_read_permissions(session, current_user, sensor_id)

    result = await session.execute(
        select(SensorData).where(SensorData.sensor_id == sensor_id).order_by(SensorData.id.desc()).limit(amount)
    )
    sensors = result.scalars().all()
    return sensors[::-1]


@sensors_router.get("/{sensor_id}/data/daily", response_model=list[DailySensorData])
async def get_sensor_data_daily(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    sensor_id: int,
    amount: int = 1,
):
    """
    Returns the average temperature for the last n days for a given sensor.
    Args:
        session (AsyncSession): A database session.
        current_user (User): The user that is currently logged in.
        sensor_id (int): The id of the sensor whose data should be retrieved.
        amount (int): The number of days that should be retrieved.

    Returns:
        A list of `DailySensorData`.
    """
    await get_user_read_permissions(session, current_user, sensor_id)

    result = await session.execute(
        select(
            func.date(SensorData.timestamp),
            func.round(cast(func.AVG(SensorData.temperature), NUMERIC), 2),
        )
        .where(SensorData.sensor_id == sensor_id)
        .group_by(func.date(SensorData.timestamp))
        .order_by(func.date(SensorData.timestamp).desc())
        .limit(amount)
    )
    return [DailySensorData(timestamp=data[0], temperature=data[1]) for data in result][::-1]
