from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.models.database_models import DBUser, SensorPermission
from api.utils.http_exceptions import MISSING_PRIVILEGES


class PermissionType(Enum):
    """
    Describes the type of Permission that should be requested in `get_user_with_permission`.
    """

    WRITE = 0
    READ = 1


async def get_user_with_permission(
    session: AsyncSession, user: DBUser, sensor_id: int, permission: PermissionType
) -> bool:
    """
    Check whether a user has the given permissions for a specific sensor.

    Args:
        session (AsyncSession): A database session.
        user (DBUser): The user that is currently logged in.
        sensor_id (int): The id of the sensor that is trying to be accessed
        permission (PermissionType): The type of permission that should be checked.

    Raises:
        HTTPException - The user is missing privileges to access the sensor.

    Returns:
        True when the user is a superuser or has the given permissions.
    """
    if user.superuser:
        return True
    # ToDo Cleaner way to do this?
    if permission == PermissionType.READ:
        result = await session.execute(
            select(SensorPermission).where(
                SensorPermission.user_id == user.id,
                SensorPermission.sensor_id == sensor_id,
                SensorPermission.read == True,
            )
        )
    else:
        result = await session.execute(
            select(SensorPermission).where(
                SensorPermission.user_id == user.id,
                SensorPermission.sensor_id == sensor_id,
                SensorPermission.write == True,
            )
        )
    sensor_permission: SensorPermission | None = result.scalars().first()
    if not sensor_permission:
        raise MISSING_PRIVILEGES
    return True


async def get_user_write_permissions(session: AsyncSession, user: DBUser, sensor_id: int) -> bool:
    """
    Check whether a user has write permissions for a specific sensor.

    Args:
        session (AsyncSession): A database session.
        user (DBUser): The user that is currently logged in.
        sensor_id (int): The id of the sensor that is trying to be accessed

    Raises:
        HTTPException - The user is missing privileges to write new data to the sensor.

    Returns:
        True when the user is a superuser or has write permissions.
    """
    return await get_user_with_permission(session, user, sensor_id, PermissionType.WRITE)


async def get_user_read_permissions(session: AsyncSession, user: DBUser, sensor_id: int) -> bool:
    """
    Check whether a user has read permissions for a specific sensor.

    Args:
        session (AsyncSession): A database session.
        user (DBUser): The user that is currently logged in.
        sensor_id (int): The id of the sensor that is trying to be accessed

    Raises:
        HTTPException - The user is missing privileges to read data from sensor.

    Returns:
        True when the user is a superuser or has read permissions.
    """
    return await get_user_with_permission(session, user, sensor_id, PermissionType.READ)
