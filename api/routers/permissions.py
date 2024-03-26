from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.models.database_models import SensorPermission, SensorPermissionCreate, User
from api.models.response_models import NotFoundError
from api.utils.database import get_session
from api.utils.security import get_current_superuser

permissions_router = APIRouter(tags=["Permissions"], prefix="/permissions")


@permissions_router.put(
    "/sensor",
    response_model=SensorPermission,
    status_code=status.HTTP_201_CREATED,
)
async def put_sensor_permission(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_superuser: Annotated[User, Depends(get_current_superuser)],
    sensor_permission: SensorPermissionCreate,
):
    """
    Create a new / Update an exising SensorPermission.

    Args:
        session (AsyncSession): A database session.
        current_superuser (User): The currently logged in superuser.
        sensor_permission (SensorPermissionCreate): The permission that should be created / updated.

    Returns:
        The created / updated `SensorPermission` model.
    """
    sensor_permission: SensorPermission = SensorPermission(**dict(sensor_permission))

    result = await session.execute(
        select(SensorPermission).where(
            SensorPermission.user_id == sensor_permission.user_id,
            SensorPermission.sensor_id == sensor_permission.sensor_id,
        )
    )
    existing_permissions: SensorPermission | None = result.scalars().first()
    if existing_permissions:
        existing_permissions.read = sensor_permission.read
        existing_permissions.write = sensor_permission.write
        sensor_permission = existing_permissions

    session.add(sensor_permission)
    await session.commit()
    await session.refresh(sensor_permission)
    return sensor_permission


async def select_sensor_permission(session: AsyncSession, user_id: int, sensor_id: int) -> SensorPermission | None:
    """
    SELECT the SensorPermission with the given `user_id` and `sensor_id` from the database.
    Args:
        session (AsyncSession): A database session.
        user_id (int): The user_id related to the `SensorPermission`.
        sensor_id (int): The sensor_id related to the `SensorPermission`.

    Returns:
        The requested `SensorPermission` if existing.
    """
    result = await session.execute(
        select(SensorPermission).where(
            SensorPermission.user_id == user_id,
            SensorPermission.sensor_id == sensor_id,
        )
    )
    sensor_permission: SensorPermission | None = result.scalars().first()
    return sensor_permission


@permissions_router.get(
    "/sensor",
    response_model=SensorPermission,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found", "model": NotFoundError}},
)
async def get_sensor_permission(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_superuser: Annotated[User, Depends(get_current_superuser)],
    user_id: int,
    sensor_id: int,
):
    """
    Gets the SensorPermission with the given `user_id` and `sensor_id`.

    Args:
        session (AsyncSession): A database session.
        current_superuser (User): The currently logged in superuser.
        user_id (int): The user_id related to the `SensorPermission`.
        sensor_id (int): The sensor_id related to the `SensorPermission`.

    Returns:
        The requested `SensorPermission` if existing.
    """
    sensor_permission: SensorPermission | None = await select_sensor_permission(session, user_id, sensor_id)
    if not sensor_permission:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This permission does not exist yet.")
    return sensor_permission


@permissions_router.delete(
    "/sensor",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found", "model": NotFoundError}},
)
async def delete_sensor_permission(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_superuser: Annotated[User, Depends(get_current_superuser)],
    user_id: int,
    sensor_id: int,
) -> None:
    """
    Delete the SensorPermission with the given `user_id` and `sensor_id`.

    Args:
        session (AsyncSession): A database session.
        current_superuser (User): The currently logged in superuser.
        user_id (int): The user_id related to the `SensorPermission`.
        sensor_id (int): The sensor_id related to the `SensorPermission`.
    """
    sensor_permission: SensorPermission | None = await select_sensor_permission(session, user_id, sensor_id)
    if not sensor_permission:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This permission does not exist.")
    await session.delete(sensor_permission)
    await session.commit()
    return None
