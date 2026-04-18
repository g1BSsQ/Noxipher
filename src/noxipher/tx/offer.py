"""ZSwap offer types."""

from pydantic import BaseModel


class ZswapInput(BaseModel):
    """Input for ZSwap offer — spend a shielded coin."""

    coin_info: dict
    merkle_path: list[str]


class ZswapOutput(BaseModel):
    """Output for ZSwap offer — create a shielded coin."""

    coin_commitment: str  # hex-encoded 32 bytes
    value: int
    token_type: str  # hex-encoded 32 bytes
    encrypted_coin: str  # hex-encoded encrypted note


class ZswapOffer(BaseModel):
    """Complete ZSwap offer."""

    inputs: list[ZswapInput] = []
    outputs: list[ZswapOutput] = []
    commitments: list[str] = []
    nullifiers: list[str] = []
