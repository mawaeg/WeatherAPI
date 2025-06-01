from datetime import datetime

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Column, Enum, Field, SQLModel

from api.models.enum_models import SensorTypeModel

# ToDo Do we want / need relationships?
# Then: https://stackoverflow.com/questions/74252768/missinggreenlet-greenlet-spawn-has-not-been-called


class DatabaseModelBase(SQLModel):
    """
    Base class for all database models.

    This adds an id as primary key to the tables.
    """

    id: int | None = Field(default=None, primary_key=True)


class SensorPermissionCreate(SQLModel):
    """
    Model used to create a new `SensorPermission`.
    """

    __table_args__ = (UniqueConstraint("user_id", "sensor_id"),)
    user_id: int = Field(foreign_key="dbuser.id")
    sensor_id: int = Field(foreign_key="sensor.id")
    read: bool = Field(default=False)
    write: bool = Field(default=False)


class SensorPermission(SensorPermissionCreate, DatabaseModelBase, table=True):
    """
    Represents a SensorPermission from the database.
    """

    pass


class SensorCreate(SQLModel):
    """
    Model used to create a new `Sensor`.
    """

    name: str
    type: SensorTypeModel = Field(sa_column=Column(Enum(SensorTypeModel)))


class Sensor(SensorCreate, DatabaseModelBase, table=True):
    """
    Represents a Sensor from the database.
    """

    pass
    # data: list["SensorData"] = Relationship(back_populates="sensor")
    # users: list["DBUser"] = Relationship(back_populates="sensors", link_model=SensorPermission)


class SensorDataCreate(SQLModel):
    """
    Model used to create new a `SensorData`.
    """

    temperature: float
    humidity: float
    pressure: float
    voltage: float | None


class SensorData(SensorDataCreate, DatabaseModelBase, table=True):
    """
    Represents a SensorData from the database.
    """

    timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False), default_factory=datetime.now)
    sensor_id: int = Field(foreign_key="sensor.id")
    # sensor: Sensor = Relationship(back_populates="data")


class SensorStateCreate(SQLModel):
    """
    Model used to create a new "SensorState".
    """

    state: bool
    voltage: float | None


class SensorState(SensorStateCreate, DatabaseModelBase, table=True):
    """
    Represents a SensorState from the database.
    """

    timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False), default_factory=datetime.now)
    sensor_id: int = Field(foreign_key="sensor.id")


class User(SQLModel):
    """
    Model representing a User.
    """

    username: str = Field(unique=True)
    superuser: bool = False


class UserCreate(SQLModel):
    """
    Model used to create a new `DBUser`
    """

    username: str
    password: str


class DBUser(User, DatabaseModelBase, table=True):
    """
    Represents a User from the database.
    """

    hashed_password: str
    # sensors: list[Sensor] = Relationship(back_populates="users", link_model=SensorPermission)
