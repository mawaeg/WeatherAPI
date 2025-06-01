import enum


class SensorTypeModel(str, enum.Enum):
    """
    Enum for representing the sensor type.
    """

    ENVIRONMENTAL = "environmental"
    STATE = "state"
