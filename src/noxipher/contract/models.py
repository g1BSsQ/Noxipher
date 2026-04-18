"""Contract-related models."""

from pydantic import BaseModel


class ContractDeployResult(BaseModel):
    """Result of contract deployment."""

    address: str
    tx_hash: str
    block_height: int | None = None
