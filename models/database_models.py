from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

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

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sensor_id: int = Field(foreign_key="sensor.id")
    # sensor: Sensor = Relationship(back_populates="data")


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
