from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers import authentication, forecast, permissions, sensors, serverstats, users
from api.utils.database import dispose_database, get_session
from api.utils.security import get_current_user

app: FastAPI = FastAPI(root_path="/weatherapi")

app.include_router(authentication.auth_router)
app.include_router(sensors.sensors_router)
app.include_router(users.users_router)
app.include_router(forecast.forecast_router)
app.include_router(permissions.permissions_router)
app.include_router(serverstats.serverstats_router)


@app.on_event("shutdown")
async def dispose_db():
    await dispose_database()


@app.get("/")
async def root():
    """
    Default route.
    """
    return {"message": "Hello World!"}


@app.get("/fire/{token}")
async def fire_notification(
    session: Annotated[AsyncSession, Depends(get_session)], token: str
) -> bool:  # pragma no cover: This is only a test route
    """
    Report a fire detected by a smoke detector.
    Args:
        session (AsyncSession): A database session.
        token (str): A valid user token.

    Returns:
        A bool indicating whether the reporting was successful.
    """
    await get_current_user(token, session)  # Authenticate User.
    print("Fire!")
    return True
