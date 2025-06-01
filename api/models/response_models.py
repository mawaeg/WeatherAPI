from datetime import date

from pydantic import BaseModel

from api.models.enum_models import SensorTypeModel


class Token(BaseModel):
    """
    Model representing a token used by the `/token` endpoint.
    """

    access_token: str
    token_type: str


class Error(BaseModel):
    """
    Model describing the structure of an Error.
    """

    detail: str


class NotFoundError(Error):
    """
    Model describing the structure of a "NotFound" Error.
    """

    pass


class BadRequest(Error):
    """
    Model describing the structure of a "BadRequest" Error.
    """

    pass


class BadGateway(Error):
    """
    Model describing the structure of a "BadRequest" Error.
    """

    pass


class DailySensorData(BaseModel):
    """
    Model representing the average `temperature` for a single day.
    """

    timestamp: date
    temperature: float


class UserSensor(BaseModel):
    """
    Represents a `Sensor` with the connected `SensorPermission` for a given `DBUser`.
    """

    id: int
    user_id: int
    name: str
    type: SensorTypeModel
    read: bool | None = True
    write: bool | None = True
