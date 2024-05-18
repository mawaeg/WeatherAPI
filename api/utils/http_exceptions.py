from fastapi import HTTPException, status

MISSING_PRIVILEGES = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="The user doesn't have enough privileges",
)

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

INCORRECT_PASSWORD = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)

NO_FORECAST_DATA = HTTPException(
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail="Could not retrieve current forecast data.",
)

NO_SERVERSTATS_DATA = HTTPException(
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail="Could not retrieve current forecast data.",
)

PERMISSION_NOT_EXISTING = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "This permission does not exist.",
)

NO_SENSOR_WITH_THIS_ID = HTTPException(
    status.HTTP_404_NOT_FOUND,
    "No sensor with this id.",
)

USER_ALREADY_EXISTS = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="A user with that name already exists.",
)
