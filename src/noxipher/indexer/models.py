"""
Indexer data models — Pydantic models for Midnight Indexer v4 responses.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


class Block(BaseModel):
    """Block data from Indexer."""

    height: int
    hash: str
    parent_hash: str | None = None
    timestamp: str | None = None


class TransactionResult(BaseModel):
    """Transaction execution result."""

    status: str  # "success", "PARTIAL_SUCCESS", "failure"
    segments: list[dict[str, Any]] = []

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        """Normalize status string — Indexer returns mixed case."""
        return v.upper() if isinstance(v, str) else v


class TokenBalance(BaseModel):
    """Token balance from Indexer."""

    token_type: str  # hex-encoded RawTokenType
    value: str  # Bigint as string (Specks)


class Transaction(BaseModel):
    """Transaction data from Indexer."""

    hash: str
    block: Block | None = None
    transaction_result: TransactionResult | None = None
    fees: dict[str, Any] | None = None
    raw: str | None = None  # HexEncoded raw bytes
    unshielded_created_outputs: list[dict[str, Any]] = []
    unshielded_spent_outputs: list[dict[str, Any]] = []


class DustGenerationStatus(BaseModel):
    """DUST generation status for a Cardano stake key."""

    cardano_stake_key: str
    is_registered: bool
    available_dust: str  # Bigint as string (Specks)
    registered_utxos: list[dict[str, Any]] = []
