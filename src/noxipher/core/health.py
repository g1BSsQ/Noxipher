from enum import Enum
from pydantic import BaseModel
from typing import Dict, Any

class HealthStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"

class ServiceHealth(BaseModel):
    status: HealthStatus
    node_connected: bool
    indexer_connected: bool
    proof_server_connected: bool
    details: Dict[str, Any]
