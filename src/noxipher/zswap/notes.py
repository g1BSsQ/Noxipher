"""
ZSwap coin notes — shielded coin tracking.

Midnight ZSwap (based on Zerocash):
  - Shielded coins stored as cryptographic COMMITMENTS in Merkle tree
  - Spend = reveal NULLIFIER (prevents double-spend, doesn't reveal coin)
  - Coins encrypted to recipient's encryption public key
"""
from __future__ import annotations

from pydantic import BaseModel


class ShieldedCoinNote(BaseModel):
    """A shielded coin (decrypted from on-chain data)."""

    token_type: bytes  # RawTokenType (32 bytes)
    value: int  # Amount in Specks
    nonce: bytes  # Random nonce (32 bytes)
    merkle_tree_index: int  # Position in global Merkle tree
    tx_hash: str | None = None  # Transaction hash when coin was created

    def compute_nullifier(self, secret_scalar: int) -> bytes:
        """
        Compute nullifier to spend coin.

        ⚠️ NOT implemented: Needs verification from compact-runtime source.
        """
        raise NotImplementedError("compute_nullifier needs verification from compact-runtime")

    def compute_nullifier_safe(self) -> bytes | None:
        """Attempt to compute nullifier, return None on failure."""
        return None

    class Config:
        arbitrary_types_allowed = True


class NullifierSet:
    """Track spent nullifiers to prevent double-spend."""

    def __init__(self) -> None:
        self._nullifiers: set[bytes] = set()

    def add(self, nullifier: bytes) -> None:
        """Add a spent nullifier."""
        self._nullifiers.add(nullifier)

    def contains(self, nullifier: bytes) -> bool:
        """Check if nullifier has been spent."""
        return nullifier in self._nullifiers

    def is_spent(self, note: ShieldedCoinNote, secret_scalar: int) -> bool:
        """Check if a coin note has been spent."""
        try:
            nullifier = note.compute_nullifier(secret_scalar)
            return self.contains(nullifier)
        except NotImplementedError:
            return False
