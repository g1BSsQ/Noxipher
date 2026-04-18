from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class ServiceHealth(BaseModel):
    status: HealthStatus
    node_connected: bool
    indexer_connected: bool
    proof_server_connected: bool
    details: dict[str, Any]
