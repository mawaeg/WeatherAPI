from typing import Annotated

import httpx
from fastapi import APIRouter, Depends

from api.models.database_models import DBUser
from api.models.serverstats_models import HistoryStats, LiveStats
from api.utils.http_exceptions import NO_SERVERSTATS_DATA
from api.utils.security import get_current_superuser, get_current_user
from SECRETS import SERVERSTATS_SETTINGS

serverstats_router = APIRouter(tags=["Serverstats"], prefix="/server/stats")

BASE_URL: str = "https://api.pph.sh/client/hostings/"


async def fetch_serverstats_live() -> LiveStats | None:
    endpoint: str = "/actions/read/live?methods=cpu-usage,uptime,load-average,memory-usage,disk-space"
    url: str = BASE_URL + SERVERSTATS_SETTINGS["hosting_id"] + endpoint
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {SERVERSTATS_SETTINGS['token']}"}) as client:
        response: httpx.Response = await client.get(url)
        if response.status_code != 200:
            return None
    live_stats: LiveStats = LiveStats(**response.json()["data"])
    return live_stats


async def fetch_serverstats_history() -> HistoryStats | None:
    endpoint: str = "/actions/read/stats_history"
    url: str = BASE_URL + SERVERSTATS_SETTINGS["hosting_id"] + endpoint
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {SERVERSTATS_SETTINGS['token']}"}) as client:
        response: httpx.Response = await client.get(url)
        if response.status_code != 200:
            return None
    history_stats: HistoryStats = HistoryStats(**response.json()["data"]["chart"])
    return history_stats


@serverstats_router.get("/live", response_model=LiveStats)
async def get_serverstats_live(current_superuser: Annotated[DBUser, Depends(get_current_superuser)]):
    live_stats: LiveStats | None = await fetch_serverstats_live()
    if not live_stats:
        raise NO_SERVERSTATS_DATA
    return live_stats


@serverstats_router.get("/history", response_model=HistoryStats)
async def get_serverstats_history(
    current_superuser: Annotated[DBUser, Depends(get_current_superuser)],
):
    history_stats: HistoryStats = await fetch_serverstats_history()
    if not history_stats:
        raise NO_SERVERSTATS_DATA
    return history_stats
