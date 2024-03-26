from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.models.database_models import DBUser, User, UserCreate
from api.models.response_models import BadRequest
from api.utils.database import get_session
from api.utils.security import get_current_superuser, get_current_user, get_password_hash

users_router = APIRouter(tags=["Users"], prefix="/users")


@users_router.get("", response_model=list[User])
async def get_users(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_superuser: Annotated[User, Depends(get_current_superuser)],
):
    """
    Returns a list of all users.
    Args:
        session (AsyncSession): A database session.
        current_superuser (User): The currently logged in superuser.

    Returns:
        A list of `User`s.
    """
    result = await session.execute(select(DBUser))
    users = result.scalars().all()
    return users


@users_router.get("/me", response_model=User)
async def get_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Returns information about the currently logged-in user.
    Args:
        current_user (User): The user that is currently logged in.

    Returns:
        Information about the current user.
    """
    return current_user


@users_router.post(
    "",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_400_BAD_REQUEST: {"description": "BadRequest", "model": BadRequest}},
)
async def create_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_superuser: Annotated[User, Depends(get_current_superuser)],
    user: UserCreate,
):
    """
    Creates a new user.
    Args:
        session (AsyncSession): A database session.
        current_superuser (User): The currently logged in superuser.
        user (UserCreate): The user that should be created.
    Returns:
        The created `User`.
    """
    try:
        hashed_password: str = get_password_hash(user.password)
        session.add(DBUser(username=user.username, hashed_password=hashed_password))
        await session.commit()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with that name already exists.")
    return User(username=user.username)
