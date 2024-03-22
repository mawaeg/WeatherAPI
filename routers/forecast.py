from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from models.database_models import User
from models.forecast_models import Forecast
from models.response_models import BadGateway
from SECRETS import OPENWEATHERMAP_KEY
from utils.forecast_buffer import ForecastBuffer
from utils.security import get_current_user

forecast_router = APIRouter(tags=["Forecast"])
buffer: ForecastBuffer = ForecastBuffer()

BASE_URL = "https://api.openweathermap.org/data/3.0/onecall"


async def get_forecast_data(*, lat: str, lon: str) -> Forecast | None:
    forecast: Forecast | None = buffer.get(lat, lon)
    if not forecast:
        url = BASE_URL + f"?lat={lat}&lon={lon}&units=metric&lang=de&appid={OPENWEATHERMAP_KEY}"
        async with httpx.AsyncClient() as client:
            response: httpx.Response = await client.get(url)
            print(response.json())
            forecast = Forecast(**response.json())
            buffer.add(lat, lon, forecast)

    return forecast


@forecast_router.get(
    "/forecast",
    responses={status.HTTP_502_BAD_GATEWAY: {"description": "Bad gateway", "model": BadGateway}},
    response_model=Forecast,
)
async def get_forecast(current_user: Annotated[User, Depends(get_current_user)], lat: str, lon: str):
    forecast: Forecast | None = await get_forecast_data(lat=lat, lon=lon)
    if not forecast:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not retrieve current forecast data.")
    return forecast
