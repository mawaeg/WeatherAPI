from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select

from api.models.database_models import DBUser
from api.utils.database import get_session
from SECRETS import SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies whether a password is correct.
    Args:
        plain_password (str): The password that should be verified
        hashed_password (str): The (correct) hashed password for the user.

    Returns:
        Whether the given plain_password is correct or not.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Returns the hash of a given password
    Args:
        password (str): The password that should be hashed.

    Returns:
        The hashed password.
    """
    return pwd_context.hash(password)


async def get_user(username: str, session: AsyncSession) -> DBUser | None:
    """
    Fetches the user associated to the username from the database.
    Args:
        username (str): The username of the user that should be retrieved
        session (AsyncSession): A database session.

    Returns:
        The user associated to the username if existing.
    """
    result = await session.execute(select(DBUser).where(DBUser.username == username))
    user: DBUser | None = result.scalars().first()
    return user


async def authenticate_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: Annotated[AsyncSession, Depends(get_session)]
) -> DBUser | None:
    """
    Authenticates a given user by the `OAuth2PasswordRequestForm`.
    Args:
        form_data (OAuth2PasswordRequestForm): The request form which is provided by the request through FastAPI.
        session (AsyncSession): A database session.

    Returns:
        The user if username and password is matching or None.
    """
    user: DBUser | None = await get_user(form_data.username, session)
    if not user:
        return None
    if not verify_password(form_data.password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: Annotated[AsyncSession, Depends(get_session)]
) -> DBUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user(username, session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_superuser(user: Annotated[DBUser, Depends(get_current_user)]):
    if not user.superuser:
        raise HTTPException(status_code=400, detail="The user doesn't have enough privileges")
    return user
