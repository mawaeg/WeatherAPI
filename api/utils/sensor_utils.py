from sqlalchemy.ext.asyncio.session import AsyncSession

from api.models.database_models import Sensor, SensorTypeModel
from api.utils.http_exceptions import INVALID_SENSOR_TYPE, NO_SENSOR_WITH_THIS_ID


async def get_sensor_from_db(session: AsyncSession, sensor_id: int) -> Sensor:
    sensor: Sensor | None = await session.get(Sensor, sensor_id)
    if not sensor:
        raise NO_SENSOR_WITH_THIS_ID
    return sensor


async def get_is_valid_sensor_type(requested_type: SensorTypeModel, sensor: Sensor) -> bool:
    if sensor.type is not requested_type:
        raise INVALID_SENSOR_TYPE

    return True
