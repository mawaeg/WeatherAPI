from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends

from api.models.database_models import DBUser
from api.models.serverstats_models import HistoryData, LiveStats
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


async def fetch_serverstats_history(entries: int) -> list[HistoryData] | None:
    endpoint: str = "/actions/read/stats_history"
    url: str = BASE_URL + SERVERSTATS_SETTINGS["hosting_id"] + endpoint
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {SERVERSTATS_SETTINGS['token']}"}) as client:
        response: httpx.Response = await client.get(url)
        if response.status_code != 200:
            return None

    # Convert data to have a list of dicts with all the data for a specific label
    json_response = response.json()

    if entries > len(json_response["data"]["chart"]["full_cpu_usage"]["labels"]):
        return None

    history_stats: list[HistoryData] = []
    for index, date in enumerate(json_response["data"]["chart"]["full_cpu_usage"]["labels"][-entries:]):
        names = [
            "full_cpu_usage",
            "load_per_core",
            "memory_usage",
            "memory_used",
            "disk_usage",
            "disk_used",
            "updates_available",
            "uptime",
            "traffic_total",
        ]
        data: dict[str, Any] = {}
        for name in names:
            data[name] = json_response["data"]["chart"][name]["data"][-entries:][index]
        current_data = HistoryData(date=date, **data)
        history_stats.append(current_data)
    return history_stats


@serverstats_router.get("/live", response_model=LiveStats)
async def get_serverstats_live(current_superuser: Annotated[DBUser, Depends(get_current_superuser)]):
    live_stats: LiveStats | None = await fetch_serverstats_live()
    if not live_stats:
        raise NO_SERVERSTATS_DATA
    return live_stats


@serverstats_router.get("/history", response_model=list[HistoryData])
async def get_serverstats_history(
    current_superuser: Annotated[DBUser, Depends(get_current_superuser)], entries: int = 32
):
    history_stats: list[HistoryData] | None = await fetch_serverstats_history(entries)
    if not history_stats:
        raise NO_SERVERSTATS_DATA
    return history_stats
