from datetime import datetime, timedelta

from models.forecast_models import Forecast


class ForecastBufferObject:
    """
    An object that is stored in the `ForecastBuffer` to indentify the data.

    Args:
        lat (str): The latitude of the forecast location.
        lon (str): The longitude of the forecast location.
        data: (Forecast): The `Forecast` model that is getting cached.
        time_until_expired (timedelta) The time the data will expire.
    """

    def __init__(self, lat: str, lon: str, data: Forecast, time_until_expired: timedelta) -> None:
        self.lat: str = lat
        self.lon: str = lon
        self.data: Forecast = data
        self.valid_until: datetime = datetime.utcnow() + time_until_expired

    def __eq__(self, other) -> bool:
        return isinstance(other, ForecastBufferObject) and self.latlon == other.latlon or self.latlon == other

    @property
    def latlon(self) -> str:
        """
        Returns the latitude and the longitude as a `;` seperated string.

        Returns:
            The combined string.
        """
        return self.lat + ";" + self.lon

    @property
    def is_expired(self) -> bool:
        """
        Indicates whether the object is expired.
        """
        return self.valid_until < datetime.utcnow()


class ForecastBuffer:
    """
    A ring buffer, that holds different `Forecast`s and caches them for a given time.

    Args:
        size (int): The size of the ring buffer.
        time_until_expired (timedelta): The time after which an object should be discarded.
    """

    def __init__(self, size: int = 5, time_until_expired: timedelta = timedelta(minutes=5)) -> None:
        self.max_size: int = size
        self.time_until_expired: timedelta = time_until_expired
        self.cache: list[ForecastBufferObject] = []

    def __len__(self) -> int:
        return len(self.cache)

    def get(self, lat: str, lon: str) -> Forecast | None:
        """
        Searches for a matching entry by the given lat and long values in the buffer and returns it if existing.

        Args:
            lat (str): The latitude of the forecast location that should be fetched.
            lon (str): The longitude of the forecast location that should be fetched.

        Returns:
            A matching `Forecast` object if existing.
        """
        for item in self.cache:
            if item == lat + ";" + lon:
                if item.is_expired:
                    self.cache.remove(item)
                else:
                    return item.data

    def add(self, lat: str, lon: str, data: Forecast) -> None:
        """
        Adds a new `Forecast` object to the buffer.

        Args:
            lat (str): The latitude of the forecast location that should be cached.
            lon (str): The longitude of the forecast location that should be cached.
            data: (Forecast): The data that should be cached.
        """
        if len(self) >= self.max_size:
            self.cache.pop(0)
        new_object: ForecastBufferObject = ForecastBufferObject(lat, lon, data, self.time_until_expired)
        self.cache.append(new_object)
