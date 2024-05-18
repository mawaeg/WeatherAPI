from pydantic import BaseModel, ConfigDict, Field


class WindType(BaseModel):
    direction: int
    speed: float


class PrecipitationType(BaseModel):
    type: str | None = Field(default=None)
    precip: float = Field(default=0.0)
    probability: float = Field(default=0.0)


class SunType(BaseModel):
    sunrise: int
    sunset: int


class MoonType(BaseModel):
    moonrise: int
    moonset: int
    moon_phase: float


class WeatherBase(BaseModel):
    """
    The base model for all forecast objects.
    """

    model_config = ConfigDict(populate_by_name=True)

    def __init__(self, **data):

        custom_data: dict = {
            "weatherText": data.get("weather")[0].get("description"),
            "weatherIcon": data.get("weather")[0].get("icon"),
            "wind": {"direction": data.get("wind_deg"), "speed": data.get("wind_speed")},
        }
        if not data.get("precipitation"):
            # Add default dict to avoid error when no precipitation information is provided by OpenWeatherMap
            custom_data["precipitation"] = {}

        super().__init__(**data, **custom_data)

    epochTime: int = Field(alias="dt")
    weatherText: str
    weatherIcon: str
    wind: WindType
    cloudCover: int = Field(alias="clouds")
    precipitation: PrecipitationType


class WeatherObject(WeatherBase):
    """
    This represents a forecast weather object.
    """

    def __init__(self, **data):
        custom_data: dict = {}
        if data.get("rain"):
            custom_data["precipitation"] = {
                "type": "rain",
                "precip": data.get("rain").get("1h", 0.0),
                "probability": data.get("pop", 0) * 100,
            }
        if data.get("snow"):
            custom_data["precipitation"] = {
                "type": "snow",
                "precip": data.get("snow").get("1h", 0.0),
                "probability": data.get("pop", 0) * 100,
            }
        super().__init__(**data, **custom_data)

    temperature: float = Field(alias="temp")


class DailyObject(WeatherBase):
    """
    This represents an entry for the daily forecast.
    """

    def __init__(self, **data):
        custom_data: dict = {
            "minTemperature": data.get("temp").get("min"),
            "maxTemperature": data.get("temp").get("max"),
            "sun": {"sunrise": data.get("sunrise"), "sunset": data.get("sunset")},
            "moon": {
                "moonrise": data.get("moonrise"),
                "moonset": data.get("moonset"),
                "moon_phase": data.get("moon_phase", 0.0),
            },
        }
        if data.get("rain"):
            custom_data["precipitation"] = {
                "type": "rain",
                "precip": data.get("rain", 0.0),
                "probability": data.get("pop", 0) * 100,
            }
        if data.get("snow"):
            custom_data["precipitation"] = {
                "type": "snow",
                "precip": data.get("snow", 0.0),
                "probability": data.get("pop", 0) * 100,
            }
        super().__init__(**data, **custom_data)

    minTemperature: float
    maxTemperature: float
    sun: SunType
    moon: MoonType


class Forecast(BaseModel):
    """
    Represents a Forecast with all information to be transmitted.
    This hold the current forecast, the hourly forecast and the daily forecast.
    """

    current: WeatherObject
    hourly: list[WeatherObject]
    daily: list[DailyObject]
