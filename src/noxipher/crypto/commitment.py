"""
Shielded coin commitment models.

Mapping from Ledger API v8 types.
"""
from pydantic import BaseModel


class ShieldedCoinInfo(BaseModel):
    """Mapping from Ledger API v8 ShieldedCoinInfo."""

    token_type: bytes  # RawTokenType (32 bytes)
    value: int  # Amount in Specks (uint64)
    nonce: bytes  # Random nonce (32 bytes)

    class Config:
        arbitrary_types_allowed = True


class QualifiedShieldedCoinInfo(ShieldedCoinInfo):
    """ShieldedCoinInfo + Merkle tree index."""

    merkle_tree_index: int


class RawTokenType:
    """Token type identifiers."""

    # NIGHT native token — all zeros (32 bytes)
    # Verify: ledger.unshieldedToken().raw → "0000...00"
    NATIVE_NIGHT: bytes = bytes(32)

    # DUST token — prefix 01 00 01 (verify from ledger-v8)
    # TypeScript: unshieldedToken().raw = "0000...00"
    # Preprod example from NPM docs: "010001000000..."
