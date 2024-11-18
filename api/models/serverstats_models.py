import datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Uptime(BaseModel):
    seconds: int
    date: datetime.datetime
    human: str


class MemoryUsage(BaseModel):
    mem_total: float = Field(validation_alias="mem-total")
    mem_free: float = Field(validation_alias="mem-free")
    mem_available: float = Field(validation_alias="mem-available")
    swap_total: float = Field(validation_alias="swap-total")
    swap_free: float = Field(validation_alias="swap-free")
    mem_used: float = Field(validation_alias="mem-used")


class DiskSpace(BaseModel):
    size: float
    used: float
    available: float
    use: int


class LiveStats(BaseModel):
    cpu_usage: float = Field(validation_alias="cpu-usage")
    uptime: Uptime
    load_average: list[str] = Field(validation_alias="load-average")
    memory_usage: MemoryUsage = Field(validation_alias="memory-usage")
    disk_space: DiskSpace = Field(validation_alias="disk-space")


class HistoryData(BaseModel, Generic[T]):
    date: str
    full_cpu_usage: float
    load_per_core: float
    memory_usage: float
    memory_used: float
    disk_usage: float
    disk_used: float
    updates_available: float
    uptime: int
    traffic_total: float
